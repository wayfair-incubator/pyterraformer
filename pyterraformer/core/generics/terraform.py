from pyterraformer.core.generics.backend import Backend
from pyterraformer.core.objects import TerraformObject


class TerraformConfig(TerraformObject):
    def __init__(self, text, attributes):
        attributes = attributes or []
        self.backends = [obj for obj in attributes if isinstance(obj, Backend)]
        TerraformObject.__init__(
            self,
            "terraform",
            text,
            [obj for obj in attributes if not isinstance(obj, Backend)],
        )

    # def render(self, variables=None):
    #     from pyterraformer.core.generics import Block, Literal
    #
    #     output = {
    #         "required_version": self.required_version,
    #         "backend": Block([Literal(backend.render()) for backend in self.backends]),
    #     }
    #     final = process_attribute(output)
    #     return self.template.render(render_attributes=final)
