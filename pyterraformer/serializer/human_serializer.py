from os.path import join, dirname
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Dict, Union, TYPE_CHECKING, Any, List

import jinja2


from pyterraformer.core.modules import ModuleObject
from pyterraformer.core.resources import ResourceObject
from pyterraformer.serializer.base_serializer import BaseSerializer
from pyterraformer.serializer.human_resources.engine import parse_text

if TYPE_CHECKING:
    from pyterraformer.terraform import Terraform
    from pyterraformer.core import (
        TerraformWorkspace,
        TerraformObject,
        TerraformNamespace,
        TerraformFile,
    )
TEMPLATE_PATH = join(dirname(__file__), "templates")

template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_PATH)
env = jinja2.Environment(
    loader=template_loader, autoescape=True, keep_trailing_newline=True
)


def process_attribute(input: Any):
    from pyterraformer.core.generics import Variable, Literal, Block

    if not isinstance(input, dict):
        return input
    output = {}
    for key, item in input.items():
        if isinstance(item, Variable):
            output[key] = item.render_basic()
        elif isinstance(item, Literal):
            output[key] = item
        elif isinstance(item, Block):
            for idx, sub_item in enumerate(item):  # type: ignore
                output[f"{key}~~block_{idx}"] = process_attribute(sub_item)
        elif isinstance(item, dict):
            output[key] = process_attribute(item)
        elif isinstance(item, List):
            output[key] = [process_attribute(sub_item) for sub_item in item]
        else:
            output[key] = item
    return output


class HumanSerializer(BaseSerializer):
    def __init__(self, terraform: Optional[Union[str, "Terraform"]] = None):
        from pyterraformer.terraform import Terraform

        self.terraform: Optional[Terraform] = None
        if isinstance(terraform, Terraform):
            self.terraform = terraform
        elif terraform:
            self.terraform = Terraform(terraform_exec_path=terraform)

    #
    # def _format_path(self):
    #     self.terraform.

    @property
    def can_format(self) -> bool:
        return self.terraform is not None

    def parse_string(self, string: str):
        return parse_text(string)

    def parse_file(self, path: Union[str, Path], workspace: "TerraformWorkspace"):
        with open(path, "r") as f:
            text = f.read()
            objects = self.parse_string(string=text)
        return TerraformFile(
            location=path, workspace=workspace, objects=objects, text=text
        )

    def _format_string(self, string: str) -> str:
        if not self.terraform:
            return string
        with TemporaryDirectory() as td:
            temp_dir = Path(td)
            file_name = temp_dir / "to_format.tf"
            file_name.write_text(string)
            self.terraform.run("fmt", path=td)
            return file_name.open().read()

    def render_object(
        self, object: "TerraformObject", format: Optional[bool] = None
    ) -> str:
        if format and not self.can_format:
            raise ValueError("No terraform executable configured, cannot format.")
        format = format if format is not None else self.can_format
        variables = {}
        variables["id"] = object.id
        variables["type"] = object._type
        final = {}
        for key in sorted(object.render_variables.keys()):
            if key not in final:
                final[key] = object.render_variables[key]

        if isinstance(object, ResourceObject):
            template_name = "resource.tf"
        elif isinstance(object, ModuleObject):
            template_name = "module.tf"
        else:
            template_name = "generic.tf"
        template = env.get_template(template_name)
        string = template.render(
            render_attributes=process_attribute(final), **variables
        )
        if format:
            string = self._format_string(string)
        return string

    def render_namespace(self, namespace: "TerraformNamespace") -> str:
        from pyterraformer.core.generics import Comment

        out = []
        for idx, object in enumerate(namespace.objects):
            # comments should have no trailing whitespace
            if isinstance(object, Comment):
                out.append(self.render_object(object))
            # EOF one
            elif idx == len(namespace.objects) - 1:
                out.append(self.render_object(object) + "\n")
            # all others two
            else:
                out.append(self.render_object(object) + "\n\n")
        return "".join(out)

    def render_workspace(self, workspace: "TerraformWorkspace") -> Dict[str, str]:
        output = {}
        for name, file in workspace.files.items():
            output[name] = self.render_namespace(file)
        return output
