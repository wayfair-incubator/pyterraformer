from analytics_terraformer_core.base_objects import TerraformObject


class Metadata(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "metadata", text, attributes)
