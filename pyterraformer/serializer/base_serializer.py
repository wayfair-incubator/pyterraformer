from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Union

if TYPE_CHECKING:
    from pyterraformer.core import (
        TerraformNamespace,
        TerraformObject,
        TerraformWorkspace,
    )


class BaseSerializer:
    pass

    @property
    def can_format(self) -> bool:
        return False

    def parse_string(self, string: str):
        raise NotImplementedError

    def parse_file(self, path: str | Path, workspace: "TerraformWorkspace"):
        raise NotImplementedError

    def _format_string(self, string: str):
        raise NotImplementedError

    def render_object(self, object: "TerraformObject", format: bool | None = None) -> str:
        raise NotImplementedError

    def render_namespace(self, namespace: "TerraformNamespace", format: bool | None = None) -> str:
        raise NotImplementedError

    def render_workspace(self, workspace: "TerraformWorkspace") -> dict[str, str]:
        raise NotImplementedError

    #
