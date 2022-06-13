from dataclasses import dataclass
from typing import Optional, Dict

from pyterraformer.terraform.backends.base_backend import BaseBackend


@dataclass
class LocalBackend(BaseBackend):
    path: Optional[str] = None
    workspace_dir: Optional[str] = None

    def generate_environment(self) -> Dict:
        output = {}
        return output
