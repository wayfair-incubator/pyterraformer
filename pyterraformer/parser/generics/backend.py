from analytics_terraformer_core.base_objects import TerraformObject, process_attribute


class Backend(TerraformObject):
    def __init__(self, name, attributes):
        TerraformObject.__init__(self, "backend", name, attributes=attributes)
        self.name = str(name).replace('"', "")

    def render(self, variables=None):
        final = {}
        for key in sorted(self.render_variables.keys()):
            if key != "name":
                final[key] = self.render_variables[key]
        final = process_attribute(final)
        return self.template.render(name=self.name, render_attributes=final)
