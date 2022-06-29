from pyterraformer.core.objects import TerraformObject


class Comment(TerraformObject):
    def __init__(self, text, multiline=False):
        self.multiline = multiline
        if self.multiline:
            text = f"/*{text}*/"
        TerraformObject.__init__(self, "comment", text, None)

    def __repr__(self):
        return f"{self._type}({self._original_text})"

    @property
    def has_content(self):
        return bool(self.text.strip())

    def render(self, variables=None):
        return self.template.render(multiline=self.multiline, text=self._original_text)
