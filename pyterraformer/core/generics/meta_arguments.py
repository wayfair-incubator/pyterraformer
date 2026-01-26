from pyterraformer.core.objects import ObjectMetadata, TerraformObject


class Provider(TerraformObject):
    def __init__(self, type: str, _metadata: ObjectMetadata | None = None, **kwargs):
        self.ptype = str(type).replace('"', "")
        TerraformObject.__init__(self, _type="provider", _metadata=_metadata)

    def __repr__(self):
        return (
            f"{self._type}-{self.ptype}(" + ", ".join([f'{key}="{val}"' for key, val in self.render_variables.items()]) + ")"
        )


class Lifecycle(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "lifecycle", text, attributes)


class Count(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "count", text, attributes)


class DependsOn(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "depends_on", text, attributes)


class ForEach(TerraformObject):
    def __init__(self, text, attributes):
        TerraformObject.__init__(self, "for_each", text, attributes)
