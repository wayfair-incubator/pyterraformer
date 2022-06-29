from pyterraformer.core.generics import Literal
from pyterraformer.core.objects import TerraformObject


class ModuleObject(TerraformObject):
    def __init__(self, text, name, attributes):
        self._name = str(name).replace('"', "")
        self.id = self._name
        TerraformObject.__init__(self, "module", text, attributes)

    def render_attribute(self, item):
        return f"${{module.{self._name}.{item}}}"

    @property
    def filtered_source(self):
        return str(self.source).replace('"', "")

    @property
    def short_name(self):
        if self.filtered_source.startswith("http"):
            return extract_http_module(str(getattr(self, "source", None)))
        elif self.filtered_source.startswith("git"):
            return extract_git_module(str(getattr(self, "source", None)))
        else:
            raise ValueError(f"Unable to parse source {self.source}")

    @property
    def version(self):
        if self.filterered_source.startswith("http"):
            return extract_http_version(self.filterered_source)
        # elif self.filtered_source.startswith('git'):
        #     return extract_http_version(self.filterered_source)
        else:
            raise ValueError(f"Unable to parse version from source {self.source}")

    @classmethod
    def create(cls, id, **kwargs):
        kwargs = kwargs or {}
        attributes = [[key, item] for key, item in kwargs.items()]
        if hasattr(cls, "REQUIRED_ATTRIBUTES"):
            for attribute in cls.REQUIRED_ATTRIBUTES:
                if attribute not in kwargs:
                    raise ValueError(f"Missing required attribute {attribute}")
        return cls(name=id, text=None, attributes=attributes)

    # def render(self, variables=None):
    #     from analytics_terraformer_core.utility import clean_render_dictionary
    #     from analytics_terraformer_core.generics import Variable
    #
    #     variables = variables or {}
    #     final = {}
    #     priority_attributes = self.REQUIRED_ATTRIBUTES + self.PRIORITY_ATTRIBUTES
    #     for val in priority_attributes:
    #         test = self.render_variables.get(val)
    #         if test:
    #             final[val] = test
    #     for key in sorted(self.render_variables.keys()):
    #         if key in "version":
    #             continue
    #         if key not in final:
    #             final[key] = self.render_variables[key]
    #     for key, item in final.items():
    #         if isinstance(item, Variable):
    #             final[key] = item.render_basic()
    #     final = clean_render_dictionary(final, [])
    #     processed = process_attribute(final)
    #     return self.template.render(
    #         render_attributes=processed, name=self._name, **variables
    #     )

    def interpolation_property(self, property: str):
        from pyterraformer.core.generics import Literal

        return Literal(f"${{module.{self.id}.{property}}}")

    def __getattr__(self, item):
        if item.endswith("_lookup"):
            property = item.split("_lookup")[0]
            return Literal(f"{self._type}.{self.id}.{property}")
        return super().__getattr__(item)


def extract_git_module(input: str):
    return input.split("/")[-1].split(".")[0]


def extract_http_module(input: str):
    return input.split("/")[-1].split("_")[0]


def extract_http_version(input: str):
    return ".".join(input.split("/")[-1].split("_")[1].split(".")[0:3])[1:]
