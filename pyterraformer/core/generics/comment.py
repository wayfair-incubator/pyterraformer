from pyterraformer.core.objects import ObjectMetadata, TerraformObject


class Comment(TerraformObject):
    def __init__(
        self,
        text: str,
        multiline: bool = False,
        _metadata: ObjectMetadata | None = None,
    ):
        self.multiline = multiline
        text = f"/*{text}*/" if self.multiline else text.strip()
        TerraformObject.__init__(self, "comment", tf_id=None, text=text, _metadata=_metadata)

    @property
    def has_content(self):
        return bool(self.text.strip())
