#!python

import json
import os
from logging import DEBUG
from logging import StreamHandler
from pathlib import Path
from typing import Optional, List, Dict

from jinja2 import Template

from pyterraformer import HumanSerializer
from pyterraformer.constants import logger
from pyterraformer.core import TerraformWorkspace
from pyterraformer.terraform import Terraform
from pyterraformer.terraform.backends.local_backend import LocalBackend
import click

logger.addHandler(StreamHandler())
logger.setLevel(DEBUG)

TEMPLATE = Template(
    '''# This file is auto-generated. Do not edit manually.
{%- macro render_blocks(blocks, indent) -%}
{%- filter indent(width=indent) %}
{%- for key, block in blocks.items()  %}
{%- if block.nesting_mode == 'single' %}
@dataclass 
class {{block.camel_case}}():
    {{ render_blocks(block.blocks, 4) }}
    {%- for item in block.attributes %}{% if not item.optional and not item.computed %}
    {{item.name}}:{{ item.python_type }}{% endif %}{% endfor %}
    # non-optional-blocks
    
    {%- for key, item in block.blocks.items() %}{% if not item.optional and not item.computed %}
    {{item.snake_case}}:{{item.camel_case}}{% endif %}{% endfor %}
    
    {%- for item in block.attributes %}{% if item.optional %}
    {{item.name}}: {{item.python_type}} = EMPTY_DEFAULT{% endif %}{% endfor %}
    
    {%- for key, item  in block.blocks.items() %}{% if item.optional %}
    {{item.snake_case}}: Optional[{{item.camel_case}}]=EMPTY_DEFAULT{% endif %}{% endfor %}
    pass
{% endif %}
{%- if block.nesting_mode == 'list' %}
# wrapper list class
class {{block.camel_case}}(BlockList):
    @dataclass 
    class {{block.camel_case}}Item():
{{ render_blocks(block.blocks, 8) }}
        {%- for item in block.attributes %}{% if not item.optional and not item.computed %}
        {{item.name}}:{{ item.python_type }}{% endif %}{% endfor %}
        # non-optional-blocks
        
        {%- for key, item in block.blocks.items() %}{% if not item.optional and not item.computed %}
        {{item.snake_case}}:{{item.camel_case}}{% endif %}{% endfor %}
        
        {%- for item in block.attributes %}{% if item.optional %}
        {{item.name}}: Optional[{{item.python_type}}] = EMPTY_DEFAULT{% endif %}{% endfor %}
        
        {%- for key, item  in block.blocks.items() %}{% if item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]=EMPTY_DEFAULT{% endif %}{% endfor %}
        pass
    items: List[{{block.camel_case}}Item]
{% endif %}
{% if block.nesting_mode == 'set' %}      
# wrapper set class
class {{block.camel_case}}(BlockSet):
    @dataclass 
    class {{block.camel_case}}Item():
{{ render_blocks(block.blocks, 8) }}
        {%- for item in block.attributes %}{% if not item.optional and not item.computed %}
        {{item.name}}:{{ item.python_type }}{% endif %}{% endfor %}
        # non-optional-blocks
        
        {%- for key, item in block.blocks.items() %}{% if not item.optional and not item.computed %}
        {{item.snake_case}}:{{item.camel_case}}{% endif %}{% endfor %}
        
        {%- for item in block.attributes %}{% if item.optional %}
        {{item.name}}: Optional[{{item.python_type}}] = EMPTY_DEFAULT{% endif %}{% endfor %}
        
        {%- for key, item  in block.blocks.items() %}{% if item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]=EMPTY_DEFAULT{% endif %}{% endfor %}
        pass
    items: Set[{{block.camel_case}}Item]
{% endif %}
{% endfor %}
{% endfilter %}
{%- endmacro %}

from typing import List, Optional, Dict, Set, Any
from pyterraformer.core.resources import ResourceObject
from pyterraformer.core.generics import BlockList, BlockSet
from pyterraformer.core.objects import ObjectMetadata
from pyterraformer.constants import EMPTY_DEFAULT
from dataclasses import dataclass



class {{resource.camel_case}}(ResourceObject):
    """    
    Args:
    {%- for item in resource.attributes %}{% if not item.computed and not item.optional %}
        {{item.name}} ({{ item.python_type }}): {% filter indent(width=20) %}{{item.description}}{% endfilter %}{% endif %}{% endfor %}
        {%- for key, item  in blocks.items() %}{% if  not item.computed and not item.optional %}
        {{item.snake_case}}: Optional[{{item.camel_case}}]{% endif %}{% endfor %}
    """
    _type = '{{resource.snake_case}}'
    
{{ render_blocks(blocks, 4) }}
    
    def __init__(self,
        tf_id: str,
        
        {%- for item in resource.attributes %}{% if not item.optional and not item.computed %}
        {{item.name}}:{{ item.python_type }},{% endif %}{% endfor %}
        # non-optional-blocks
        
        {%- for key, item  in blocks.items() %}{% if not item.optional and not item.computed %}
        {{item.snake_case}}:{{item.camel_case}},{% endif %}{% endfor %}
        #optional
        _metadata: Optional[ObjectMetadata] = EMPTY_DEFAULT,
        
        {%- for item in resource.attributes %}{% if item.optional %}
        {{item.name}}: {{item.python_type}} = EMPTY_DEFAULT,{% endif %}{% endfor %}
        
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
            super().__init__(tf_id=tf_id, _metadata=_metadata, **kwargs)
            
        
        

'''
)
from dataclasses import dataclass, field


def camel_case(string: str) -> str:
    return "".join([v.capitalize() for v in string.split("_")])


def python_type(tf_type: str) -> str:
    if tf_type == "string":
        return "str"
    elif tf_type == "number":
        return "float"
    elif "map" in tf_type:
        type = python_type([v for v in tf_type if v != "map"][0])
        return f"Dict[str, {type}]"
    elif "list" in tf_type:
        type = python_type([v for v in tf_type if v != "list"][0])
        return f"List[{type}]"
    elif "set" in tf_type:
        type = python_type([v for v in tf_type if v != "set"][0])
        return f"Set[{type}]"
    elif "object" in tf_type:
        components = python_type([v for v in tf_type if v != "object"][0])
        return "Dict[str,Any]"
    return tf_type


@dataclass
class Attribute:
    name: str
    type: str
    optional: bool
    computed: bool
    description: Optional[str] = None
    default: Optional[str] = None

    @property
    def python_type(self) -> str:
        if self.optional:
            return f"Optional[{python_type(self.type)}]"
        return python_type(self.type)


@dataclass
class Resource:
    snake_case: str
    description: Optional[str]
    attributes: List[Attribute]

    @property
    def camel_case(self):
        return "".join([v.capitalize() for v in self.snake_case.split("_")])

    @classmethod
    def parse_from_resource_info(cls, key: str, info: dict):
        attributes = [
            Attribute(
                name=key,
                type=v.get("type"),
                optional=v.get("optional"),
                computed=v.get("computed", False),
                default=v.get("default", None),
                description=v.get("description", ""),
            )
            for key, v in info["block"]["attributes"].items()
        ]
        # move optional attributes to the end
        attributes = sorted(
            attributes, key=lambda x: "zzz" + x.name if x.optional else x.name
        )
        return Resource(key, description=info.get("description"), attributes=attributes)


def generate_blocks(schema: dict, depth=0) -> dict:
    # extra_blocks = {}
    # for key, value in schema['block'].get('block_types', {}).items():
    #
    #     extra_blocks = {**generate_blocks(value, depth + 1), **extra_blocks}
    blocks = {
        key: Block(
            snake_case=key,
            nesting_mode=value.get("nesting_mode"),
            description=value.get("description", ""),
            max_items=value.get("max_items"),
            blocks=generate_blocks(value),
            optional=value.get("optional", False),
            attributes=[
                Attribute(
                    name=key,
                    type=v.get("type"),
                    optional=v.get("optional"),
                    computed=v.get("computed"),
                    default=v.get("default"),
                    description=v.get("description", ""),
                )
                for key, v in value["block"].get("attributes", {}).items()
            ],
        )
        for key, value in schema["block"].get("block_types", {}).items()
    }
    return blocks


@dataclass
class Block:
    snake_case: str
    optional: bool
    attributes: List[Attribute]
    description: Optional[str]
    nesting_mode: str
    max_items: int = -1
    blocks: [Optional[Dict[str, "Block"]]] = field(default_factory=dict)

    def __post_init__(self):
        # all lists can be empty
        # single maybe shouldn't be the case
        # but for now
        if self.nesting_mode in ("list", "set", "single"):
            self.optional = True

    @property
    def camel_case(self):
        return "".join([v.capitalize() for v in self.snake_case.split("_")])


def build_resource_class(key: str, schema: dict):
    blocks = generate_blocks(schema)
    # blocks = sorted(blocks, key= lambda x: not x.blocks)
    class_text = TEMPLATE.render(
        resource=Resource.parse_from_resource_info(key, schema), blocks=blocks
    )
    return class_text


def _create_stubs(provider: str, version: str, output_path: str, terraform_path: str):
    output = {}
    tf = Terraform(
        terraform_exec_path=terraform_path, backend=LocalBackend(path=os.getcwd())
    )
    workspace = TerraformWorkspace(
        terraform=tf, path=os.getcwd(), serializer=HumanSerializer(terraform=tf)
    )
    workspace.add_provider(name="build", source=provider, version=version)
    workspace.save_all()
    tf.run("init", path=os.getcwd())
    provider_info = tf.run(["providers", "schema", "-json"], path=os.getcwd())
    loaded = json.loads(provider_info)
    schemas = loaded["provider_schemas"]
    google = schemas[f"registry.terraform.io/{provider}"]
    resources = google["resource_schemas"]
    for key, value in resources.items():
        if key == "google_bigquery_connection":
            print(key)
            print(value)
        output[key] = build_resource_class(key, value)

    save_stubs(provider, version, output, output_path)


def save_stubs(provider: str, version: str, stubs: dict, path: str):
    base_path = Path(path)
    root = Path(path) / provider / f"v{version.replace('.','_')}"
    os.makedirs(root, exist_ok=True)
    for key, text in stubs.items():
        if not text:
            continue
        with open(root / f"{key}.py", "w", encoding="utf-8") as f:
            f.write(text)
    imports = [f"from .{v} import {camel_case(v)}" for v in stubs.keys()]
    all = ",".join([f'"{camel_case(v)}"' for v in stubs.keys()])
    with open(root / "__init__.py", "w", encoding="utf-8") as f:
        f.write("\n".join(imports))
        f.write(f"\n__all__ = [{all}]")
    parts = root.relative_to(base_path).parts
    for idx in range(1, len(parts)):
        subpath = Path(path)
        for val in parts[0:idx]:
            subpath = subpath / val
        with open(subpath / "__init__.py", "w", encoding="utf-8") as f:
            f.write("\n")


@click.command()
@click.option(
    "--provider", help="The provider name, eg. hashicorp/aws to create stubs for"
)
@click.option("--version", help="The version of the provider to create stubs for. ")
@click.option("--terraform_path", help="The path of the local terraform binary.")
@click.option("--output_path", help="The output path to put the created files in")
def create_stubs(provider: str, version: str, output_path: str, terraform_path: str):
    _create_stubs(
        provider=provider,
        version=version,
        output_path=output_path,
        terraform_path=terraform_path,
    )


if __name__ == "__main__":
    create_stubs()

    # tf = Terraform(terraform_exec_path=r'c:/tech/terraform.exe',
    #                backend=LocalBackend(path=os.getcwd()), )
    # workspace = TerraformWorkspace(terraform=tf, path=os.getcwd(), serializer=HumanSerializer(terraform=tf))
    # workspace.add_provider(name='google', source="hashicorp/google")
    # workspace.save_all()
    # tf.run('init', path=os.getcwd())
    # provider_info = tf.run(['providers', 'schema', '-json'], path=os.getcwd())
    # loaded = json.loads(provider_info)
    # schemas = loaded['provider_schemas']
    # google = schemas['registry.terraform.io/hashicorp/google']
    # resources = google['resource_schemas']
    # for key, value in resources.items():
    #     if 'google_storage_bucket'==key:
    #         build_resource_class(key, value)
