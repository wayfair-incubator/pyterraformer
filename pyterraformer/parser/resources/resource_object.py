from typing import List, Optional

from pyterraformer.utility.decorators import lazy_property

from pyterraformer.base_objects import TerraformObject, process_attribute
from pyterraformer.parser.load_templates import get_template
from dataclasses import dataclass

@dataclass
class StateResponse:
    resource_name:str
    remote_address:str

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
    def import_address(self)->str:
        raise NotImplementedError

    @lazy_property
    def template(self):
        return get_template("resource")

    def render(self, variables=None):
        from analytics_terraformer_core.utility import clean_render_dictionary

        variables = variables or {}
        variables["id"] = self.id
        variables["type"] = self._type
        priority_attributes = (
            ["name", "project", "project_id"] + self.REQUIRED_ATTRIBUTES + self.PRIORITY_ATTRIBUTES
        )

        # sort logic for workflow_utility attributes at top, then alphabetical
        final = {}
        for val in priority_attributes:
            test = self.render_variables.get(val)
            if test:
                final[val] = test
        for key in sorted(self.render_variables.keys()):
            if key not in final:
                final[key] = self.render_variables[key]

        # this is compatibility for TF 12
        final = clean_render_dictionary(final, self.BLOCK_ATTRIBUTES)

        output = process_attribute(final)
        return self.template.render(render_attributes=output, **variables)
