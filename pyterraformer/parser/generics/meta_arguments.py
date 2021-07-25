from analytics_utility_core.decorators import lazy_property

from analytics_terraformer_core.base_objects import TerraformObject, process_attribute
from analytics_terraformer_core.templates import get_template


class Provider(TerraformObject):
    def __init__(self, ptype, text, attributes):
        self.ptype = str(ptype).replace('"', "")
        TerraformObject.__init__(self, "provider", text, attributes)

    def __repr__(self):
        return (
            f"{self._type}-{self.ptype}("
            + ", ".join([f'{key}="{val}"' for key, val in self.render_variables.items()])
            + ")"
        )

    @lazy_property
    def template(self):
        return get_template("provider")

    def render(self, variables=None):
        from analytics_terraformer_core.utility import clean_render_dictionary

        variables = variables or {}
        variables["type"] = self.ptype

        final = clean_render_dictionary(self.render_variables, [])
        output = process_attribute(final)
        return self.template.render(render_attributes=output, **variables)


class Lifecycle(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "lifecycle", text, attributes)


class Count(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "count", text, attributes)


class DependsOn(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "depends_on", text, attributes)


class ForEach(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "for_each", text, attributes)
