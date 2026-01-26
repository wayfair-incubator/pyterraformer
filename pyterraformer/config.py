from dataclasses import dataclass
from typing import Optional

from pyterraformer.settings import get_default_terraform_location

# tempdir = mkdtemp()
#
# atexit.register(shutil.rmtree, tempdir)


@dataclass
class TerraformerConfig:
    terraform_exec: str | None = get_default_terraform_location()
    default_workspace: str = "default"
    tf_plugin_cache_dir: str | None = None
    default_variable_file: str = "variables.tf"
    default_data_file: str = "data.tf"

    #
    # def configure_git_module_provider(self):
    #     pass

    @property
    def state_provider(self):
        return None


Config = TerraformerConfig()
