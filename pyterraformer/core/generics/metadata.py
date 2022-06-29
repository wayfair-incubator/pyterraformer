from pyterraformer.core.objects import TerraformObject


class Metadata(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "metadata", text, attributes)
