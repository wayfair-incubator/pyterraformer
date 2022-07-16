from dataclasses import dataclass
from typing import Optional

from pyterraformer.settings import get_default_terraform_location


# tempdir = mkdtemp()
#
# atexit.register(shutil.rmtree, tempdir)


@dataclass
class TerraformerConfig(object):
    terraform_exec: Optional[str] = get_default_terraform_location()
    default_workspace: str = "default"
    tf_plugin_cache_dir: Optional[str] = None
    default_variable_file: str = "variables.tf"
    default_data_file: str = "data.tf"

    #
    # def configure_git_module_provider(self):
    #     pass

    @property
    def state_provider(self):
        return None


Config = TerraformerConfig()
