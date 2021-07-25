from analytics_terraformer_core.base_objects import (
    TerraformObject,
    TerraformBlock,
    Literal,
    process_attribute,
)


from analytics_terraformer_core.generics.backend import Backend


class TerraformConfig(TerraformObject):
    def __init__(self, text, attributes):
        attributes = attributes or []
        self.backends = [obj for obj in attributes if isinstance(obj, Backend)]
        TerraformObject.__init__(
            self, "terraform", text, [obj for obj in attributes if not isinstance(obj, Backend)]
        )

    def render(self, variables=None):
        output = {
            "required_version": self.required_version,
            "backend": TerraformBlock([Literal(backend.render()) for backend in self.backends]),
        }
        final = process_attribute(output)
        return self.template.render(render_attributes=final)
