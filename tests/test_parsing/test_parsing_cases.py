from pathlib import Path
import os
from logging import DEBUG
from logging import StreamHandler

from pyterraformer import HumanSerializer
from pyterraformer.constants import logger
from pyterraformer.core import TerraformWorkspace
from pyterraformer.terraform import Terraform
from pyterraformer.terraform.backends.local_backend import LocalBackend

logger.addHandler(StreamHandler())
logger.setLevel(DEBUG)


def test_all_parsing():
    test_cases = Path(__file__).parent / "cases"
    tf = Terraform(terraform_exec_path=None, backend=LocalBackend(path=test_cases))
    workspace = TerraformWorkspace(
        terraform=tf, path=test_cases, serializer=HumanSerializer(terraform=tf)
    )

    all_files = os.listdir(test_cases)
    for file in all_files:
        filepath = Path(file)
        namespace = workspace.get_file_safe(filepath.name)
        assert len(namespace.objects) > 0
