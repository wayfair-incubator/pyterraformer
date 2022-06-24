from pyterraformer.core.objects import TerraformObject


class Data(TerraformObject):
    _type = "data"

    def __init__(self, name, type, text, attributes):
        self.name = str(name).replace('"', "")
        self.type = str(type).replace('"', "")
        TerraformObject.__init__(self, self._type, text, attributes)

    def __repr__(self):
        return (
            f"{self._type}({self.name})("
            + ", ".join(
                [f'{key}="{val}"' for key, val in self.render_variables.items()]
            )
            + ")"
        )

    #
    # def render(self, variables=None):
    #     variables = variables or {}
    #     final = {}
    #     for key in sorted(self.render_variables.keys()):
    #         if key not in final and key != "type":
    #             final[key] = self.render_variables[key]
    #
    #     for key, item in final.items():
    #         if (
    #             isinstance(item, str)
    #             and item.startswith('"${')
    #             and item.endswith('$}"')
    #         ):
    #             item = item[3:-3]
    #             final[key] = Literal(item)
    #
    #     output = process_attribute(final)
    #     return self.template.render(
    #         name=self.name, type=self.type, render_attributes=output, **variables
    #     )
