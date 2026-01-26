from pyterraformer.core.objects import ObjectMetadata, TerraformObject


class TerraformConfig(TerraformObject):
    def __init__(self, _metadata: ObjectMetadata | None = None, **kwargs):
        TerraformObject.__init__(self, "terraform", _metadata=_metadata, **kwargs)
