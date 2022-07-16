from typing import Optional

from pyterraformer.core.objects import TerraformObject, ObjectMetadata


class TerraformConfig(TerraformObject):
    def __init__(self, _metadata: Optional[ObjectMetadata] = None, **kwargs):
        # self.backends = [obj for obj in attributes if isinstance(obj, Backend)]
        TerraformObject.__init__(self, "terraform", _metadata=_metadata, **kwargs)

    # def render(self, variables=None):
    #     from pyterraformer.core.generics import Block, Literal
    #
    #     output = {
    #         "required_version": self.required_version,
    #         "backend": Block([Literal(backend.render()) for backend in self.backends]),
    #     }
    #     final = process_attribute(output)
    #     return self.template.render(render_attributes=final)
