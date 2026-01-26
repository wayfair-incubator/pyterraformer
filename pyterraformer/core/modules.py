from typing import Optional

from pyterraformer.core.objects import ObjectMetadata, TerraformObject


class ModuleObject(TerraformObject):
    def __init__(self, tf_id, _metadata: ObjectMetadata | None = None, **kwargs):
        TerraformObject.__init__(self, _type="module", tf_id=tf_id, **kwargs)
