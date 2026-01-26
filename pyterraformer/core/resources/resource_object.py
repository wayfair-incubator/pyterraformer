from dataclasses import dataclass
from typing import List, Optional

from pyterraformer.core.objects import ObjectMetadata, TerraformObject


@dataclass
class StateResponse:
    resource_name: str
    remote_address: str


class ResourceObject(TerraformObject):
    REQUIRED_ATTRIBUTES: list[str] = []
    PRIORITY_ATTRIBUTES: list[str] = []
    BLOCK_ATTRIBUTES: list[str] = []
    _type = "generic_resource_object"

    def __init__(self, tf_id: str, _metadata: ObjectMetadata | None = None, **kwargs):
        TerraformObject.__init__(self, self._type, tf_id, _metadata=_metadata, **kwargs)

    def render_attribute(self, item):
        return f"${{{self._type}.{self.tf_id}.{item}}}"

    @property
    def import_address(self) -> str:
        raise NotImplementedError
