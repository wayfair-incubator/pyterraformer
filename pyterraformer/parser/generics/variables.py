from analytics_utility_core.decorators import lazy_property

from analytics_terraformer_core.base_objects import TerraformObject, Literal
from analytics_terraformer_core.generics import StringLit
from analytics_terraformer_core.templates import get_template


class Variable(TerraformObject):
    def __init__(self, text, name, attributes):
        self.name = str(name).replace('"', "")
        TerraformObject.__init__(self, "variable", text, attributes)

    def __repr__(self):
        return (
            f"{self._type}(name={self.name}, "
            + ", ".join([f'{key}="{val}"' for key, val in self.render_variables.items()])
            + ")"
        )

    def __getitem__(self, val):
        for key, item in self.default.items():

            if val == key:
                return item
        raise KeyError(val)

    def render_lookup(self, item):
        return Literal(f'var.{self.name}["{item}"]')

    def render_attribute(self, item):
        return Literal(f"var.{self.name}.{item}")

    def render_basic(self):
        return Literal(f"var.{self.name}")

    def get(self, val, fallback=None):
        for key, item in self.default.items():
            if val == key:
                return item
        return fallback

    @lazy_property
    def template(self):
        return get_template("variables")

    def get_type(self, val):
        from analytics_terraformer_core.generics.interpolation import String

        if isinstance(val, list):
            if not val:
                return Literal(f"list(any)")
            return Literal(f"list({self.get_type(val[0]).value})")
        elif isinstance(val, dict):
            out = set()
            for item in val.values():
                out.add(self.get_type(item).value)
            out = list(out)
            if len(out) == 1:
                return Literal(f"map({out[0]})")
            return Literal(f"map(any)")
        elif isinstance(val, set):
            return Literal(f"set({self.get_type(next(iter(val))).value})")
        elif isinstance(val, str):
            return Literal("string")
        elif isinstance(val, StringLit):
            return Literal("string")
        elif isinstance(val, bool):
            return Literal("bool")
        elif isinstance(val, int) or isinstance(val, float):
            return Literal("number")
        elif isinstance(val, String):
            return Literal("string")
        return Literal("any")

    def render(self, variables=None):
        variables = variables or {}
        variables["id"] = self.name
        type_map = self.get_type(self.render_variables.get("default", None))
        self.render_variables["type"] = type_map

        priority_attributes = ["type"]

        # sort logic for workflow_utility attributes at top, then alphabetical
        final = {}
        for val in priority_attributes:
            test = self.render_variables.get(val)
            if test:
                final[val] = test
        for key, value in self.render_variables.items():
            if key in ("_type",):
                continue
            final[key] = value

        return self.template.render(render_attributes=final, **variables)
