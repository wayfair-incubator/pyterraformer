from pyterraformer.core.objects import TerraformObject


class Data(TerraformObject):
    _type = "data"

    def __init__(self, name, type, text, attributes):
        self.name = str(name).replace('"', "")
        self.type = str(type).replace('"', "")
        TerraformObject.__init__(self, self._type, text, attributes)

    def __repr__(self):
        return (
            f"{self._type}({self.name})(" + ", ".join([f'{key}="{val}"' for key, val in self.render_variables.items()]) + ")"
        )
