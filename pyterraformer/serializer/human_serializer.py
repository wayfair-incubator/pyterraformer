from pyterraformer.core import TerraformWorkspace, TerraformObject, TerraformFile
from pyterraformer.serializer.base_serializer import BaseSerializer
import jinja2

template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_PATH)
env = jinja2.Environment(loader=template_loader, autoescape=True, keep_trailing_newline=True)

def render_object(object:TerraformObject, variables:dict=None):
    from pyterraformer.utility import clean_render_dictionary

    variables = variables or {}
    variables["id"] = object.id
    variables["type"] = object._type
    final = {}
    for key in sorted(object.render_variables.keys()):
        if key not in final:
            final[key] = object.render_variables[key]

    # this is compatibility for TF 12
    final = clean_render_dictionary(final, object.BLOCK_ATTRIBUTES)

    output = process_attribute(final)
    return template.render(render_attributes=output, **variables)


class HumanSerializer(object):
    def __init__(self, format:bool=True):
        self.format = format
        pass

    def write_file(self, file:TerraformFile):
        for object in file.objects

    def render_workspace(self, workspace:TerraformWorkspace):
        for file in workspace.files:
            self.write_file(file)
