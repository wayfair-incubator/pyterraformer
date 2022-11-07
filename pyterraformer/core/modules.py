from typing import Optional

from pyterraformer.core.objects import TerraformObject, ObjectMetadata


class ModuleObject(TerraformObject):
    def __init__(self, tf_id, _metadata: Optional[ObjectMetadata] = None, **kwargs):
        TerraformObject.__init__(self, _type="module", tf_id=tf_id, **kwargs)
