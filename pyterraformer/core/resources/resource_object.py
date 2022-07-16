from dataclasses import dataclass
from typing import List, Optional

from pyterraformer.core.objects import TerraformObject, ObjectMetadata


@dataclass
class StateResponse:
    resource_name: str
    remote_address: str


class ResourceObject(TerraformObject):
    REQUIRED_ATTRIBUTES: List[str] = []
    PRIORITY_ATTRIBUTES: List[str] = []
    BLOCK_ATTRIBUTES: List[str] = []
    _type = "generic_resource_object"

    def __init__(
        self, tf_id: str, _metadata: Optional[ObjectMetadata] = None, **kwargs
    ):
        TerraformObject.__init__(self, self._type, tf_id, _metadata=_metadata, **kwargs)

    def render_attribute(self, item):
        return f"${{{self._type}.{self.id}.{item}}}"

    @property
    def import_address(self) -> str:
        raise NotImplementedError
