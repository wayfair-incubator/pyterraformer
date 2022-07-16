from pyterraformer.core.objects import TerraformObject, ObjectMetadata
from typing import Optional

# from pyterraformer.core.resources import


class Backend(TerraformObject):
    def __init__(self, name: str, _metadata: Optional[ObjectMetadata] = None, **kwargs):
        TerraformObject.__init__(self, "backend", _metadata=_metadata, **kwargs)
        self.name = str(name).replace('"', "")

    # def render(self, variables=None):
    #     final = {}
    #     for key in sorted(self.render_variables.keys()):
    #         if key != "name":
    #             final[key] = self.render_variables[key]
    #     final = process_attribute(final)
    #     return self.template.render(name=self.name, render_attributes=final)
