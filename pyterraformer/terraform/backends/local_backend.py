import atexit
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Optional, Dict

from pyterraformer.terraform.backends.base_backend import BaseBackend


@dataclass
class LocalBackend(BaseBackend):
    path: Optional[str] = None
    workspace_dir: Optional[str] = None

    def generate_environment(self) -> Dict:
        output: Dict = {}
        return output


@dataclass
class TemporaryLocalBackend(LocalBackend):
    def __init__(self):
        temp_dir = TemporaryDirectory()
        super().__init__(path=temp_dir)
        atexit.register(lambda: temp_dir.cleanup())
