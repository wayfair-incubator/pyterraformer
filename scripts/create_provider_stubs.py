import os
from logging import DEBUG
from logging import StreamHandler
from typing import Optional, List, Dict, Set

from pyterraformer import HumanSerializer
from pyterraformer.constants import logger
from pyterraformer.core import TerraformWorkspace
from pyterraformer.core.generics import BlockList
from pyterraformer.terraform import Terraform
from pyterraformer.terraform.backends.local_backend import LocalBackend

logger.addHandler(StreamHandler())
logger.setLevel(DEBUG)
import json
from jinja2 import Template

TEMPLATE = Template('''
from typing import List, Optional, Dict, Set
from pyterraformer.core.resources import ResourceObject
from pyterraformer.core.generics import BlockList, BlockSet
from pyterraformer.core.objects import ObjectMetadata
from dataclasses import dataclass

{% for key, block in blocks.items()  %}
{% if block.nesting_mode == 'single' %}
# this block accepts only a single value, set the class directly
@dataclass 
class {{block.camel_case}}():
        {%- for item in block.attributes %}{% if not item.optional and not item.computed %}
        {{item.name}}:{{ item.python_type }}{% endif %}{% endfor %}
        # non-optional-blocks
        
        {%- for key, item in block.blocks.items() %}{% if not item.optional and not item.computed %}
        {{item.snake_case}}:{{item.camel_case}}{% endif %}{% endfor %}
        
        {%- for item in block.attributes %}{% if item.optional %}
        {{item.name}}: {{item.python_type}} = None{% endif %}{% endfor %}
        
        {%- for key, item  in block.blocks.items() %}{% if item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]=None,{% endif %}{% endfor %}
{% endif %}
{%- if block.nesting_mode == 'list' %}
# this block can contain multiple items, items in a list are required
@dataclass 
class {{block.camel_case}}Item():
        {%- for item in block.attributes %}{% if not item.optional and not item.computed %}
        {{item.name}}:{{ item.python_type }}{% endif %}{% endfor %}
        # non-optional-blocks
        
        {%- for key, item in block.blocks.items() %}{% if not item.optional and not item.computed %}
        {{item.snake_case}}:{{item.camel_case}}{% endif %}{% endfor %}
        
        {%- for item in block.attributes %}{% if item.optional %}
        {{item.name}}: {{item.python_type}} = None{% endif %}{% endfor %}
        
        {%- for key, item  in block.blocks.items() %}{% if item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]=None,{% endif %}{% endfor %}
        
# wrapper list class
class {{block.camel_case}}(BlockList):
        items: List[{{block.camel_case}}Item]
{% endif %}
{% if block.nesting_mode == 'set' %}
# this block can contain multiple items, items in a list are required
@dataclass 
class {{block.camel_case}}Item():
        {%- for item in block.attributes %}{% if not item.optional and not item.computed %}
        {{item.name}}:{{ item.python_type }}{% endif %}{% endfor %}
        # non-optional-blocks
        
        {%- for key, item in block.blocks.items() %}{% if not item.optional and not item.computed %}
        {{item.snake_case}}:{{item.camel_case}}{% endif %}{% endfor %}
        
        {%- for item in block.attributes %}{% if item.optional %}
        {{item.name}}: {{item.python_type}} = None{% endif %}{% endfor %}
        
        {%- for key, item  in block.blocks.items() %}{% if item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]=None,{% endif %}{% endfor %}
        
# wrapper list class
class {{block.camel_case}}(BlockSet):
        items: Set[{{block.camel_case}}Item]
{% endif %}
{% endfor %}

class {{resource.camel_case}}(ResourceObject):
    """    
    Args:
    {%- for item in resource.attributes %}{% if not item.computed and not item.optional %}
        {{item.name}} ({{ item.python_type }}): {% filter indent(width=20) %}{{item.description}}{% endfilter %}{% endif %}{% endfor %}
        {%- for key, item  in blocks.items() %}{% if  not item.computed and not item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]{% endif %}{% endfor %}
    """
    _type = '{{resource.snake_case}}'
    
    def __init__(self,
        tf_id: str,
        
        {%- for item in resource.attributes %}{% if not item.optional and not item.computed %}
        {{item.name}}:{{ item.python_type }},{% endif %}{% endfor %}
        # non-optional-blocks
        
        {%- for key, item  in blocks.items() %}{% if not item.optional and not item.computed %}
        {{item.snake_case}}:{{item.camel_case}},{% endif %}{% endfor %}
        #optional
        metadata: Optional[ObjectMetadata] = None,
        
        {%- for item in resource.attributes %}{% if item.optional %}
        {{item.name}}: {{item.python_type}} = None,{% endif %}{% endfor %}
        
        {%- for key, item  in blocks.items() %}{% if item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]=None,{% endif %}{% endfor %}
        ):
            kwargs = {}
            {% for item in resource.attributes if not item.computed or item.optional %}if {{item.name}} is not None:
                kwargs['{{item.name}}'] = {{ item.name }}
            {% endfor %}
            {%- for key, item in blocks.items() if not item.computed or item.optional %}if {{item.snake_case}} is not None:
                kwargs['{{item.snake_case}}'] = {{ item.snake_case }}
            {% endfor %}
            super().__init__(tf_id=tf_id, metadata=metadata, **kwargs)
            
        
        

''')
from dataclasses import dataclass, field


def python_type(tf_type: str) -> str:
    if tf_type == 'string':
        return 'str'
    elif tf_type == 'number':
        return 'float'
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
        if self.optional:
            return f'Optional[{python_type(self.type)}]'
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
        attributes = [Attribute(name=key, type=v.get('type'),
                                optional=v.get('optional'),
                                computed=v.get('computed', False),
                                description=v.get('description', '')) for key, v in info['block']['attributes'].items()]
        # move optional attributes to the end
        attributes = sorted(attributes, key = lambda x: 'zzz'+x.name if x.optional else x.name)
        return Resource(key, description=info.get('description'), attributes=attributes)


def generate_blocks(schema:dict, depth = 0)->dict:
    extra_blocks = {}
    for key, value in schema['block'].get('block_types', {}).items():
        extra_blocks = {**generate_blocks(value, depth +1), **extra_blocks}
    blocks = {key: Block(snake_case=key,
                         nesting_mode = value.get('nesting_mode'),
                         description= value.get('description', ''),
                         max_items = value.get('max_items'),
                         blocks = generate_blocks(value),
                         optional=value.get('optional', False), attributes=[Attribute(name=key,
                                                                                      type=v.get('type'),
                                                                                      optional=v.get('optional'),
                                                                                      computed=v.get('computed'),
                                                                                      description=v.get(
                                                                                          'description', '')) for
                                                                            key, v in
                                                                            value['block'].get('attributes', {}).items()]
                         )
              for key, value in schema['block'].get('block_types', {}).items()}
    return {**extra_blocks, **blocks}

@dataclass
class Block:
    snake_case: str
    optional: bool
    attributes: List[Attribute]
    description: Optional[str]
    nesting_mode: str
    max_items:int = -1
    blocks: [Optional[Dict[str,"Block"]]] = field(default_factory = dict)

    def __post_init__(self):
        # all lists can be empty
        # single maybe shouldn't be the case
        # but for now
        if self.nesting_mode in ('list', 'set', 'single'):
            self.optional = True

    @property
    def camel_case(self):
        return ''.join([v.capitalize() for v in self.snake_case.split('_')])


def build_resource_class(key: str, schema: dict):
    blocks = generate_blocks(schema)
    # blocks = sorted(blocks, key= lambda x: not x.blocks)
    class_text = TEMPLATE.render(resource=Resource.parse_from_resource_info(key, schema), blocks=blocks)
    print(class_text)
    pass


if __name__ == "__main__":

    tf = Terraform(terraform_exec_path=r'c:/tech/terraform.exe',
                   backend=LocalBackend(path=os.getcwd()), )
    workspace = TerraformWorkspace(terraform=tf, path=os.getcwd(), serializer=HumanSerializer(terraform=tf))
    # workspace.add_provider(name='google', source="hashicorp/google")
    # workspace.save_all()
    tf.run('init', path=os.getcwd())
    provider_info = tf.run(['providers', 'schema', '-json'], path=os.getcwd())
    loaded = json.loads(provider_info)
    schemas = loaded['provider_schemas']
    google = schemas['registry.terraform.io/hashicorp/google']
    resources = google['resource_schemas']
    for key, value in resources.items():
        if 'google_storage_bucket'==key:
            build_resource_class(key, value)
