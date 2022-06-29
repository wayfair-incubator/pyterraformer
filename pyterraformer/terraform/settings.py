from dataclasses import dataclass


@dataclass
class TerraformConfig(object):
    terraform_exec_path: str
