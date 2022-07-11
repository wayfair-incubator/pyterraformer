from typing import Optional

from pyterraformer.core.objects import TerraformObject, ObjectMetadata


class Comment(TerraformObject):
    def __init__(
        self,
        text: str,
        multiline: bool = False,
        _metadata: Optional[ObjectMetadata] = None,
    ):
        self.multiline = multiline
        if self.multiline:
            text = f"/*{text}*/"
        else:
            text = text.strip()
        TerraformObject.__init__(
            self, "comment", tf_id=None, text=text, _metadata=_metadata
        )

    @property
    def has_content(self):
        return bool(self.text.strip())
