import atexit
import shutil
from tempfile import mkdtemp
from typing import Optional

from goodconf import GoodConf, Field

tempdir = mkdtemp()

atexit.register(shutil.rmtree, tempdir)


class TerraformerConfig(GoodConf):
    "Configuration for pyterraformer"
    DEBUG: bool = Field(default=False)
    TERRAFORM_EXEC: str = Field(default="")
    DEFAULT_WORKSPACE: str = Field(default="prod")
    GIT_MODULE_PROVIDER_KEY: Optional[str] = Field(default=None)
    TF_PLUGIN_CACHE_DIR: Optional[str] = Field(default=tempdir)

    class Config:
        default_files = []

    def configure_git_module_provider(self):
        pass

    @property
    def state_provider(self):
        return None


terraform_config = TerraformerConfig(load=True)
