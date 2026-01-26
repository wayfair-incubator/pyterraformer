from importlib.metadata import PackageNotFoundError, version

from .config import Config
from .core.workspace import TerraformWorkspace
from .serializer import HumanSerializer
from .terraform.backends import LocalBackend
from .terraform.terraform import Terraform

try:
    __version__ = version("pyterraformer")
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = [
    "HumanSerializer",
    "Config",
    "Terraform",
    "LocalBackend",
    "TerraformWorkspace",
]
