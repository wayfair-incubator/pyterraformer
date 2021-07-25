from analytics_terraformer_core.base_objects import TerraformObject


class Output(TerraformObject):
    def __init__(self, name, attributes):
        TerraformObject.__init__(self, "output", name, attributes)
