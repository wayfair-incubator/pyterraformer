import os
import re
import tempfile
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path
from subprocess import CalledProcessError, run as sub_run
from typing import Dict, List, Union, Iterator, Any
from pyterraformer.terraform import Terraform

import jinja2
#
# from analytics_terraformer_core.constants import (
#     TERRAFORM_PATH,
#     BASE_TERRAFORM_VERSION,
#     BASE_CI_TERRAFORM_VERSION,
#     BASE_GOOGLE_VERSION,
#     BASE_NULL_VERSION,
#     TEMPLATE_PATH,
#     TERRAFORM_BIN_PATH,
#     STATE_BUCKET,
#     TERRAFORM_SA_DEV,
#     TERRAFORM_SA
# )
from pyterraformer.exceptions import ValidationError, TerraformApplicationError
from pyterraformer.core.generics import Literal, Block

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyterraformer.core.workspace import TerraformWorkspace
    from pyterraformer.core import TerraformObject

def get_root(path: str, breaker: Union[str, List[str]] = None):
    if isinstance(breaker, str):
        breaker = [breaker]
    elif not breaker:
        breaker = ["terraform", "terraform-local-cache"]
    else:
        breaker = breaker
    parts = splitall(path)
    base = []
    for item in parts:
        base.append(item)
        if item.lower() in breaker:
            break
    joined = os.path.join(*base)
    return str(Path(os.path.relpath(path, joined)).as_posix())


class TerraformNamespace(object):
    def __init__(self, name:str, workspace:"TerraformWorkspace"):
        self.workspace:"TerraformWorkspace" = workspace
        self.name = name
        self.objects: List = []

    def resolve(self):
        if not self.workspace.parser:
            raise ValueError('No parser provided to look at files in this workspace')
        return self.workspace.parser.parse_file(self.name, self.workspace)
        # from analytics_terraformer_core.parser import parse_file
        #
        # return parse_file(self.file, self.parent)

class LazyFile(TerraformNamespace):
    def __init__(self, file:str, parent:"TerraformWorkspace"):
        super().__init__(name=os.path.basename(file).replace('.tf', ''), parent=parent)
        self.file = file

    def resolve(self):
        if not self.parent.parser:
            raise ValueError('No parser provided to look at files in this workspace')
        return self.parent.parser.parse_file(self.file)

class TerraformFile(TerraformNamespace):
    def __init__(
            self,
            workspace: "TerraformWorkspace",
            text: str,
            location: Union[str, Path],
    ):
        self._text = text
        name = os.path.basename(location)
        super().__init__( name=name, workspace=workspace)
        self.location = location
        self.locals: Dict = {}
        if self not in self.workspace.files:
            self.workspace.add_file(self)

    def relative_path(self, path: str):
        return get_root(str(self.location), path)

    def get_object(self, **kwargs):
        for object in self.objects:
            if all([value_match(getattr(object, key, None), val) for key, val in kwargs.items()]):
                return object
        raise ValueError(
            f"No object matching filter criteria {kwargs} found in file {self.location}"
        )

    def delete_object(self, object):
        orig = self.objects
        self.objects = [obj for obj in self.objects if obj != object]
        self.changed = orig != self.objects

    def find(self, object_type, invert=False):
        output = []
        for object in self.objects:
            if isinstance(object, object_type):
                output.append(object)
        if invert:
            return reversed(output)
        return output

    def add_object(
            self,
            object: "TerraformObject",
            position="default",
            exists_okay=False,
            replace=False,
            initial_parse_flag=False,
    ):

        from pyterraformer.core.resources import ResourceObject
        from pyterraformer.core.modules import ModuleObject
        from pyterraformer.core.generics import Variable, Data

        object._file = self
        duplicates = None
        if isinstance(object, (Variable, Data)):
            duplicates = [
                idx
                for idx, obj in enumerate(self.objects)
                if isinstance(object, (Variable, Data)) and object.name == getattr(obj, "name", "")
            ]
        elif isinstance(object, ResourceObject):

            duplicates = [
                idx
                for idx, obj in enumerate(self.objects)
                if isinstance(object, ResourceObject)
                   and object.id + (object._type or "")
                   == getattr(obj, "id", "") + getattr(obj, "_type", "")
            ]
        elif isinstance(object, ModuleObject):

            duplicates = [
                idx
                for idx, obj in enumerate(self.objects)
                if isinstance(object, ModuleObject)
                   and object.id + (object._type or "")
                   == getattr(obj, "id", "") + getattr(obj, "_type", "")
            ]
        if duplicates:
            if replace:
                self.objects = [
                    obj for idx, obj in enumerate(self.objects) if idx not in (duplicates)
                ]
            elif exists_okay:
                return
            else:
                raise ValueError(
                    f"Duplicate resource name or ID detected {[obj for idx, obj in enumerate(self.objects) if idx in (duplicates)]} in file {self.name}! Cannot add unless the 'replace' or 'exists_okay' flags are set."
                )

        # only flag if changed as not already present
        if not initial_parse_flag:
            self.changed = True
        if position == "first":
            self.objects.insert(0, object)
        elif position == "last":
            self.objects.append(object)
        elif position == "default":
            indexes = [idx for idx, val in enumerate(self.objects) if val._type == object._type]
            if indexes:
                self.objects.insert(indexes[-1] + 1, object)
            else:
                self.objects.append(object)

        elif isinstance(position, int):
            self.objects.insert(position, object)
        else:
            raise ValueError(f"Invalid Position Argument {position}")

    def render(self, **variables):
        text = []
        for object in self.objects:
            text.append(object.text)
        return "\n".join(text)

    @property
    def text(self):
        from analytics_terraformer_core.generics import Comment

        out = []
        for idx, object in enumerate(self.objects):
            if isinstance(object, Comment):
                out.append(object.text)
            elif idx == len(self.objects) - 1:
                out.append(object.text + "\n")
            else:
                out.append(object.text + "\n\n")
        return "".join(out)

    @property
    def changed_flag(self):
        return self.changed or any([object._changed for object in self.objects])

    def save(self):
        if self.changed_flag:
            print(self.text)
            try:
                with open(self.location, "r") as file:
                    orig_text = file.read()
            except FileNotFoundError as e:
                orig_text = None
            # the rewrite flags aren't perfect, check if there are actual changes
            try:
                with open(self.location, "w") as file:
                    file.write(self.text)
            except FileNotFoundError:
                import os

                os.makedirs(os.path.dirname(self.location))
                with open(self.location, "w") as file:
                    file.write(self.text)
            # pass out the original text, so we can make a judgement on committing after formatting
            return orig_text
        return False

    def __iter__(self):
        self._idx = 0
        return self

    def __next__(self):
        try:
            out = self.objects[self._idx]
            self._idx += 1
            return out

        except IndexError:
            self._idx = 0
            raise StopIteration  # Done iterating.