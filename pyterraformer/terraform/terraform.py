import os
import re
import tempfile
from subprocess import CalledProcessError, run as sub_run
from typing import Optional, List, Union
from pyterraformer.config import TerraformerConfig
from pyterraformer.exceptions import TerraformExecutionError
from pyterraformer.terraform.backends import BaseBackend, LocalBackend
from dataclasses import dataclass, field
from pyterraformer.constants import logger


@dataclass
class Terraform:
    terraform_exec_path: Optional[str] = None
    plugin_cache_directory: Optional[str] = None
    backend: BaseBackend = field(default_factory=LocalBackend(path=os.getcwd()))

    def run(self, arguments: Union[str, List[str]], path: str):
        runtime_env = os.environ.copy()
        if isinstance(arguments, str):
            arguments = [arguments]
        # os.cwd will fail on Null values, which can happen
        runtime_env = {
            key: value
            for key, value in {
                **runtime_env,
                **self.backend.generate_environment(),
            }.items()
            if value
        }
        if self.plugin_cache_directory:
            runtime_env["TF_PLUGIN_CACHE_DIR"] = self.plugin_cache_directory
        cmd_array = [self.terraform_exec_path, *arguments]
        run_cmd = lambda: sub_run(
            cmd_array,
            cwd=path,
            env=runtime_env,
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout
        try:
            return run_cmd()
        except CalledProcessError as e:
            logger.error(e.stderr)
            raise e


def extract_errors(input: str):
    found = re.findall(
        r"(Error:.*)(?:Error:|$)", input, re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    return "\n".join(found).strip()


def apply(path: str, workspace: str, state_provider=None):
    workspace = workspace or TerraformerConfig.DEFAULT_WORKSPACE
    with tempfile.TemporaryDirectory() as tmpdirname:
        my_env = os.environ.copy()
        my_env["TF_PLUGIN_CACHE_DIR"] = TerraformerConfig.TF_PLUGIN_CACHE_DIR

        if TerraformerConfig.GIT_MODULE_PROVIDER_KEY:
            # key_path = os.path.join(tmpdirname, "tmpssh")
            # with open(key_path, "w") as keyfile:
            #     lines = secret_store["ssh_identity"].replace("|", "\n")
            #     keyfile.write(lines)
            os.chmod(key_path, 0o600)
            ssh_cmd = "ssh -i %s -o StrictHostKeyChecking=no" % keyfile.name.replace(
                "\\", "\\\\"
            )
            my_env["GIT_SSH_COMMAND"] = ssh_cmd
        state_provider = state_provider or TerraformerConfig.state_provider
        if state_provider:
            state_provider.hydrate_enviroment(my_env)

        run_cmd = lambda cmd: sub_run(
            cmd, cwd=path, env=my_env, check=True, capture_output=True, encoding="utf-8"
        ).stdout

        try:
            for cmd in [
                [TerraformerConfig.TERRAFORM_EXEC, "init"],
                [TerraformerConfig.TERRAFORM_EXEC, "workspace", "list"],
            ]:
                check = run_cmd(cmd)
            if workspace not in check:
                run_cmd(
                    [TerraformerConfig.TERRAFORM_EXEC, "workspace", "new", workspace]
                )
            for cmd in [
                [TerraformerConfig.TERRAFORM_EXEC, "workspace", "select", workspace],
                [TerraformerConfig.TERRAFORM_EXEC, "apply", "-auto-approve"],
            ]:
                run = run_cmd(cmd)
        except CalledProcessError as e:
            errors = extract_errors(e.stderr)
            raise TerraformExecutionError(errors)
    return str(run)
