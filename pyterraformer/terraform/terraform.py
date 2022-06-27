import os
import re
from dataclasses import dataclass, field
from subprocess import CalledProcessError, run as sub_run
from typing import Optional, List, Union

from pyterraformer.constants import logger
from pyterraformer.settings import get_default_terraform_location
from pyterraformer.terraform.backends import BaseBackend, LocalBackend


@dataclass
class Terraform:
    terraform_exec_path: Optional[str] = field(
        default_factory=get_default_terraform_location
    )
    plugin_cache_directory: Optional[str] = None
    backend: BaseBackend = field(default_factory=lambda: LocalBackend(path=os.getcwd()))
    workspace: str = "default"

    def run(self, arguments: Union[str, List[str]], path: str):

        workspace = self._run(["workspace", "show"], path=path).strip()
        logger.info(f"Executing {arguments} in workspace {workspace}.")
        if workspace != self.workspace:
            logger.info(f"swapping to configured workspace {workspace}")
            workspaces = [
                v.replace("*", "").strip()
                for v in self._run(["workspace", "list"], path=path).split("\n")
            ]
            if self.workspace in workspaces:
                logger.info("workspace found, swapping to")
                self._run(["workspace", "select", self.workspace], path=path)
            else:
                logger.info("workspace not found, creating")
                self._run(["workspace", "new", self.workspace], path=path)
        return self._run(arguments=arguments, path=path)

    def _run(self, arguments: Union[str, List[str]], path: str):
        if not self.terraform_exec_path:
            raise ValueError("No terraform executable set, cannot run TF commands.")
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

        cmd_array: List[str] = [self.terraform_exec_path, *arguments]
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
