from pyterraformer.core.objects import TerraformObject


class Local(TerraformObject):
    def __init__(self, text, attributes: dict):
        pass_on = []
        for key, value in attributes.items():
            pass_on.append([key, value])

        TerraformObject.__init__(self, _type="local", original_text=text, attributes=pass_on)
