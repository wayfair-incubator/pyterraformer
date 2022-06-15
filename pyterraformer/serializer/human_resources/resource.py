from typing import List, Optional

from pyterraformer.utility.decorators import lazy_property

from pyterraformer.base_objects import TerraformObject
from pyterraformer.serializer.load_templates import get_template
from dataclasses import dataclass


@dataclass
class StateResponse:
    resource_name: str
    remote_address: str


class ResourceObject(TerraformObject):
    REQUIRED_ATTRIBUTES: List[str] = []
    PRIORITY_ATTRIBUTES: List[str] = []
    BLOCK_ATTRIBUTES: List[str] = []
    _type = "generic_resource_object"

    def __init__(self, type: str, id: str, text: str, attributes: Optional[List]):
        # self.extractors = {**self.extractors, 'name': f'resource\s+"{type}"\s+"(.*?)"',
        #                    'count': 'count\s+=\s+"(.*?)"\s*?\n',}
        TerraformObject.__init__(self, self._type, text, attributes)
        self.id = str(id).replace('"', "")

    def render_attribute(self, item):
        return f"${{{self._type}.{self.id}.{item}}}"

    @property
    def import_address(self) -> str:
        raise NotImplementedError

    @lazy_property
    def template(self):
        return get_template("resource")
