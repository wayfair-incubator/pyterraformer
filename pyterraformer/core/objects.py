from typing import Dict, Any, List, Optional

from pyterraformer.exceptions import ValidationError
from pyterraformer.parser.load_templates import env
from pyterraformer.utility.decorators import lazy_property


def process_attribute(input: Any):
    from pyterraformer.parser.generics import Variable, Literal, Block

    if not isinstance(input, dict):
        return input
    output = {}
    for key, item in input.items():
        if isinstance(item, Variable):
            output[key] = item.render_basic()
        elif isinstance(item, Literal):
            output[key] = item
        elif isinstance(item, Block):
            for idx, sub_item in enumerate(item):
                output[f"{key}~~block_{idx}"] = process_attribute(sub_item)
        elif isinstance(item, dict):
            output[key] = process_attribute(item)
        elif isinstance(item, List):
            output[key] = [process_attribute(sub_item) for sub_item in item]
        else:
            output[key] = item
    return output


class TerraformObject(object):
    extractors: Dict[str, str] = {}

    def __init__(
        self, id: str, type, original_text: Optional[str], attributes: Optional[List]
    ):
        from pyterraformer.parser.generics import Block, Block

        self.render_variables: Dict[str, str] = {}
        self.attributes = attributes or []
        for attribute in self.attributes:
            if isinstance(attribute, list):
                # always cast keys to string
                self.render_variables[str(attribute[0])] = attribute[1]
            elif isinstance(attribute, Block):
                base = self.render_variables.get(attribute.name, Block())
                base.append(attribute)
                self.render_variables[attribute.name] = base
        self._type: str = type
        self._original_text: str = original_text
        self._changed = False
        self._workspace = None
        self._file = None
        self._initialized = True

    def __repr__(self):
        return (
            f"{self._type}("
            + ", ".join(
                [f'{key}="{val}"' for key, val in self.render_variables.items()]
            )
            + ")"
        )

    @classmethod
    def create(cls, id, **kwargs):
        kwargs = kwargs or {}

        attributes = [[key, item] for key, item in kwargs.items()]
        if hasattr(cls, "REQUIRED_ATTRIBUTES"):
            for attribute in cls.REQUIRED_ATTRIBUTES:
                if attribute not in kwargs:
                    raise ValidationError(f"Missing required attribute {attribute}")
        ctype = getattr(cls, "type", kwargs.get("type", "Unknown"))
        return cls(id, ctype, original_text=None, attributes=attributes)

    @property
    def tf_attributes(self):
        return self.render_variables.keys()

    def __getattr__(self, name):
        if name == "render_variables":
            return self.__dict__.get("render_variables")
        elif self.render_variables and name in self.render_variables:
            return self.__dict__.get("render_variables").get(name)
        elif (
            self.render_variables
            and "_" in name
            and name.endswith("resolved")
            and name.rsplit("_", 1)[0] in self.render_variables
        ):
            lookup = name.rsplit("_", 1)[0]
            return self.resolved_attributes.get(lookup)
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        """This gets tricky:
        We want any new attribute set on a base class to get rendered...
        Unless it's one of the internal attributes we use for managing objects.
        So skip anything with a private method, or in the disallow list...
        Unless it's also in the list of things that we should render.
        Woof."""
        if name.startswith("_") or (
            name in ("row_num", "template", "name", "id")
            and not (self.render_variables and name in self.render_variables)
        ):
            super().__setattr__(name, value)
        elif (self.render_variables and name in self.render_variables) or getattr(
            self, "_initialized", False
        ):
            self._changed = True
            self.__dict__.get("render_variables")[name] = value
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if self.render_variables and name in self.render_variables:
            self._changed = True
            del self.__dict__.get("render_variables")[name]
        else:
            super().__delattr__(name)

    @property
    def changed(self):
        return self._original_text and not self._changed

    @lazy_property
    def template(self):
        try:
            out = env.get_template(f"{self._type}.tf")
            if not out:
                raise ValueError(f"could not get template {self._type}")
            return env.get_template(f"{self._type}.tf")
        except Exception as e:
            return env.get_template(f"generic.tf")

    @lazy_property
    def variables(self):
        return env.parse(env.get_template(f"{self._type}.tf")[0])

    @property
    def text(self):
        if not self._changed and self._original_text:
            return self._original_text
        else:
            return self.render()

    def render(self, variables=None):
        from pyterraformer.parser.generics import StringLit, Literal

        variables = variables or {}
        final = {}
        for key, item in self.render_variables.items():
            if (
                isinstance(item, StringLit)
                and len(item.contents) == 1
                and str(item).startswith('"${')
                and str(item).endswith('$}"')
            ):
                item = str(item)[3:-3]
                final[key] = Literal(item)
            else:
                final[key] = item
        output = process_attribute(final)
        if not self.template:
            raise ValueError(self._type + self._original_text)
        return self.template.render(**output, render_attributes=output, **variables)

    def resolve_item(self, item):
        from pyterraformer.parser.generics import Variable

        if isinstance(item, list):
            resolved = [self.resolve_item(sub_item) for sub_item in item]
        elif isinstance(item, str):
            resolved = item
        elif isinstance(item, int):
            resolved = item
        elif isinstance(item, dict):
            resolved = {
                self.resolve_item(key): self.resolve_item(value)
                for key, value in item.items()
            }
        else:
            resolved = item.resolve(self._workspace, self._file, None, None)
        if isinstance(resolved, Variable) and hasattr(resolved, "default"):
            resolved = getattr(resolved, "default")
        return resolved

    @property
    def resolved_attributes(self):
        out = {}
        for key, item in self.render_variables.items():
            resolved = self.resolve_item(item)
            out[str(key)] = resolved

        return out
