from typing import Optional, Dict, TYPE_CHECKING, Union
from pathlib import Path

if TYPE_CHECKING:
    from pyterraformer.core import (
        TerraformWorkspace,
        TerraformObject,
        TerraformNamespace,
    )


class BaseSerializer(object):
    pass

    @property
    def can_format(self) -> bool:
        return False

    def parse_string(self, string: str):
        raise NotImplementedError

    def parse_file(self, path: Union[str, Path], workspace: "TerraformWorkspace"):
        raise NotImplementedError

    def _format_string(self, string: str):
        raise NotImplementedError

    def render_object(
        self, object: "TerraformObject", format: Optional[bool] = None
    ) -> str:
        raise NotImplementedError

    def render_namespace(
        self, namespace: "TerraformNamespace", format: Optional[bool] = None
    ) -> str:
        raise NotImplementedError

    def render_workspace(self, workspace: "TerraformWorkspace") -> Dict[str, str]:
        raise NotImplementedError

    #
