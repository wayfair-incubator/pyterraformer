import os
from logging import DEBUG
from logging import StreamHandler
from typing import Optional, List

from pyterraformer import HumanSerializer
from pyterraformer.constants import logger
from pyterraformer.core import TerraformWorkspace
from pyterraformer.core.generics import Block
from pyterraformer.terraform import Terraform
from pyterraformer.terraform.backends.local_backend import LocalBackend

logger.addHandler(StreamHandler())
logger.setLevel(DEBUG)
import json
from jinja2 import Template

TEMPLATE = Template('''
from pyterraform.core import ResourceObject
from dataclass import dataclass

{% for key, block in blocks.items() %}
@dataclass 
class {{block.camel_case}}():{% for item in block.attributes %}
        {{item.name}}: {{item.python_type}}{% endfor %}
{% endfor %}

class {{resource.camel_case}}(ResourceObject):
    """    
    {{resource.description}}
    """
    _type = '{{resource.snake_case}}'
    
    def __init__(self,{% for item in resource.attributes %}
        {{item.name}}: {% if item.optional %}Optional[{{item.python_type}}]{% else %}{{ item.python_type }}{% endif %}{% if item.optional %}=None{% endif %},{% endfor %}
        {% for key, item  in blocks.items() %}
        {{item.snake_case}}: {% if item.optional %}Optional[{{item.camel_case}}]{% else %}{{item.camel_case}}{% endif %}{% if item.optional %}=None{% endif %}{% endfor %}
        ):
        {% for item in resource.attributes %}self.{{item.name}} = {{item.name}}
        {% endfor %}
        ):
        {% for item in resource.attributes %}self.{{item.name}} = {{item.name}}
        {% endfor %}#begin block assignments{% for key, item in blocks.items() %}
        self.{{item.snake_case}} = {{item.snake_case}}{% endfor %}
        
        
        

''')
from dataclasses import dataclass


def python_type(tf_type: str) -> str:
    if tf_type == 'string':
        return 'str'
    elif 'map' in tf_type:
        type = python_type([v for v in tf_type if v != 'map'][0])
        return f'Dict[str, {type}]'
    elif 'list' in tf_type:
        type = python_type([v for v in tf_type if v != 'list'][0])
        return f'List[{type}]'
    elif 'set' in tf_type:
        type = python_type([v for v in tf_type if v != 'set'][0])
        return f'Set[{type}]'
    elif 'object' in tf_type:
        components = python_type([v for v in tf_type if v != 'object'][0])
        return 'Dict[str,Any]'
    return tf_type


@dataclass
class Attribute:
    name: str
    type: str
    optional: bool
    computed: bool
    description: Optional[str] = None

    @property
    def python_type(self) -> str:
        return python_type(self.type)


@dataclass
class Resource:
    snake_case: str
    description: Optional[str]
    attributes: List[Attribute]

    @property
    def camel_case(self):
        return ''.join([v.capitalize() for v in self.snake_case.split('_')])

    @classmethod
    def parse_from_resource_info(cls, key: str, info: dict):
        print(info['block']['attributes'])
        attributes = [Attribute(name=key, type=v.get('type'),
                                optional=v.get('optional'),
                                computed=v.get('computed'),
                                description=v.get('description', '')) for key, v in info['block']['attributes'].items()]
        # move optional attributes to the end
        attributes = sorted(attributes, key = lambda x: 'zzz'+x.name if x.optional else x.name)
        return Resource(key, description=info.get('description'), attributes=attributes)


@dataclass
class Block:
    snake_case: str
    optional: bool
    attributes: List[Attribute]
    description: Optional[str]
    nesting_mode: str
    max_items:int = -1

    @property
    def camel_case(self):
        return ''.join([v.capitalize() for v in self.snake_case.split('_')])


def build_resource_class(key: str, schema: dict):
    print(key)
    print(schema)
    print(schema['block'].keys())
    print(schema['block'].get('block_types', ''))
    blocks = {key: Block(snake_case=key,
                         nesting_mode = value.get('nesting_mode'),
                         description= value.get('description', ''),
                         max_items = value.get('max_items'),
                         optional=value.get('optional', False), attributes=[Attribute(name=key, type=v.get('type'),
                                                                                      optional=v.get('optional'),
                                                                                      computed=v.get('computed'),
                                                                                      description=v.get(
                                                                                          'description', '')) for
                                                                            key, v in
                                                                            value['block'].get('attributes', {}).items()]
                         )
              for key, value in schema['block'].get('block_types', {}).items()}
    class_text = TEMPLATE.render(resource=Resource.parse_from_resource_info(key, schema), blocks=blocks)
    print(class_text)
    pass


if __name__ == "__main__":

    tf = Terraform(terraform_exec_path=r'c:/tech/terraform.exe',
                   backend=LocalBackend(path=os.getcwd()), )
    workspace = TerraformWorkspace(terraform=tf, path=os.getcwd(), serializer=HumanSerializer(terraform=tf))
    workspace.add_provider(name='google', source="hashicorp/google")
    workspace.save_all()
    tf.run('init', path=os.getcwd())
    provider_info = tf.run(['providers', 'schema', '-json'], path=os.getcwd())
    loaded = json.loads(provider_info)
    print(loaded.keys())
    schemas = loaded['provider_schemas']
    print(schemas.keys())
    google = schemas['registry.terraform.io/hashicorp/google']
    resources = google['resource_schemas']
    print(resources.keys())
    for key, value in resources.items():
        build_resource_class(key, value)
