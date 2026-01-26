from pyterraformer.core.objects import ObjectMetadata, TerraformObject


class Backend(TerraformObject):
    def __init__(self, name: str, _metadata: ObjectMetadata | None = None, **kwargs):
        TerraformObject.__init__(self, "backend", _metadata=_metadata, **kwargs)
        self.name = str(name).replace('"', "")
