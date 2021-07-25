from analytics_terraformer_core.base_objects import TerraformObject, process_attribute


class Local(TerraformObject):
    def __init__(self, text, attributes: dict):
        pass_on = []
        for key, value in attributes.items():
            pass_on.append([key, value])

        TerraformObject.__init__(self, "local", text, pass_on)

    def render(self, variables=None):
        from analytics_terraformer_core.utility import clean_render_dictionary

        variables = variables or {}

        final = clean_render_dictionary(self.render_variables, [])
        output = process_attribute(final)
        return self.template.render(render_attributes=output, **variables)
