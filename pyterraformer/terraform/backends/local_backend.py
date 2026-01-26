import atexit
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Dict, Optional

from pyterraformer.core.generics import Backend
from pyterraformer.terraform.backends.base_backend import BaseBackend


@dataclass
class LocalBackend(BaseBackend):
    path: str | None = None
    workspace_dir: str | None = None

    def generate_environment(self) -> dict:
        output: dict = {}
        return output

    def as_object(self) -> Backend:
        return Backend(name="local")


@dataclass
class TemporaryLocalBackend(LocalBackend):
    def __init__(self):
        temp_dir = TemporaryDirectory()
        super().__init__(path=temp_dir)
        atexit.register(lambda: temp_dir.cleanup())
