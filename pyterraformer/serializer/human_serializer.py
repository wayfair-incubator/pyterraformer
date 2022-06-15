from os.path import join, dirname
from typing import Optional, Dict

import jinja2

from pyterraformer.core import TerraformWorkspace, TerraformObject, TerraformNamespace
from pyterraformer.core.modules import ModuleObject
from pyterraformer.core.resources import ResourceObject
from pyterraformer.serializer.human_resources.engine import parse_text
TEMPLATE_PATH = join(dirname(__file__, ), 'templates')

template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_PATH)
env = jinja2.Environment(loader=template_loader, autoescape=True, keep_trailing_newline=True)

TEMPLATE_DICT = {}


class HumanSerializer(object):
    def __init__(self, terraform: Optional[str] = None):
        from pyterraformer.terraform import Terraform
        self.terraform: Optional[Terraform] = None
        if isinstance(terraform, Terraform):
            self.terraform = terraform
        elif terraform:
            self.terraform = Terraform(terraform_exec_path=terraform)

    #
    # def _format_path(self):
    #     self.terraform.

    def parse_string(self, string: str):
        return parse_text(string)

    def render_object(self, object: TerraformObject) -> str:
        variables = {}
        variables["id"] = object.id
        variables["type"] = object._type
        final = {}
        for key in sorted(object.render_variables.keys()):
            if key not in final:
                final[key] = object.render_variables[key]

        if isinstance(object, ResourceObject):
            template_name = 'resource.tf'
        elif isinstance(object, ModuleObject):
            template_name = 'module.tf'
        else:
            template_name = 'generic.tf'
        template = env.get_template(template_name)
        return template.render(render_attributes=final, **variables)

    def render_namespace(self, namespace: TerraformNamespace) -> str:
        output = []
        for object in namespace.objects:
            output.append(self.render_object(object))
        return '\n\n'.join(output)

    def render_workspace(self, workspace: TerraformWorkspace) -> Dict[str, str]:
        output = {}
        for name, file in workspace.files.items():
            output[name] = self.render_namespace(file)
        return output

    #
    # def write_object(self, file:TerraformObject):
    #     for object in file.objects:
    #         serialized =
