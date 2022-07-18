import os
from pathlib import Path
from typing import Dict, List, Union, Optional, TYPE_CHECKING

from pyterraformer.enums import InsertPosition
from pyterraformer.serializer import BaseSerializer
from pyterraformer.core.utility import value_match

if TYPE_CHECKING:
    from pyterraformer.core.workspace import TerraformWorkspace
    from pyterraformer.core import TerraformObject


class TerraformNamespace(object):
    def __init__(
        self,
        name: str,
        workspace: "TerraformWorkspace",
        objects: Optional[List["TerraformObject"]] = None,
    ):
        self.workspace: "TerraformWorkspace" = workspace
        self.name = name
        self.objects: List = objects or []
        self.locals: Dict = {}

    def resolve(self):
        """No op for the base file"""
        return self


class LazyFile(TerraformNamespace):
    def __init__(self, file: Union[str, Path], workspace: "TerraformWorkspace"):
        super().__init__(
            name=os.path.basename(file).replace(".tf", ""), workspace=workspace
        )
        self.file = file

    def resolve(self) -> "TerraformFile":
        if not self.workspace.serializer:
            raise ValueError("No parser provided to look at files in this workspace")
        return self.workspace.serializer.parse_file(self.file, workspace=self.workspace)


class TerraformFile(TerraformNamespace):
    def __init__(
        self,
        workspace: "TerraformWorkspace",
        text: str,
        location: Union[str, Path],
        objects: Optional[List["TerraformObject"]] = None,
    ):
        self._text = text
        name = os.path.basename(location)
        super().__init__(name=name, workspace=workspace, objects=objects)
        self.location = location
        if self not in self.workspace.files:
            self.workspace.add_file(self)

    def get_object(self, **kwargs):
        for object in self.objects:
            if all(
                [
                    value_match(getattr(object, key, None), val)
                    for key, val in kwargs.items()
                ]
            ):
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

    def _detect_duplicates(self, object) -> List:
        from pyterraformer.core.resources import ResourceObject
        from pyterraformer.core.modules import ModuleObject
        from pyterraformer.core.generics import Variable, Data

        duplicates = []
        if isinstance(object, (Variable, Data)):
            duplicates = [
                idx
                for idx, obj in enumerate(self.objects)
                if isinstance(object, (Variable, Data))
                and object.name == getattr(obj, "name", "")
            ]
        elif isinstance(object, ResourceObject):

            duplicates = [
                idx
                for idx, obj in enumerate(self.objects)
                if isinstance(object, ResourceObject)
                   and object.tf_id
                   and object.tf_id + (object._type or "")
                   == getattr(obj, "tf_id", "") + getattr(obj, "_type", "")
            ]
        elif isinstance(object, ModuleObject):
            duplicates = [
                idx
                for idx, obj in enumerate(self.objects)
                if isinstance(object, ModuleObject)
                and object.id
                and object.id + (object._type or "")
                == getattr(obj, "tf_id", "") + getattr(obj, "_type", "")
            ]
        return duplicates

    def add_object(
        self,
        object: "TerraformObject",
        position: Union[InsertPosition, int] = InsertPosition.DEFAULT,
        exists_okay: bool = False,
        replace: bool = False,
    ):
        object._file = self
        duplicates = self._detect_duplicates(object)
        if duplicates:
            if replace:
                self.objects = [
                    obj
                    for idx, obj in enumerate(self.objects)
                    if idx not in (duplicates)
                ]
            elif exists_okay:
                return
            else:
                raise ValueError(
                    f"Duplicate resource name or ID detected {[obj for idx, obj in enumerate(self.objects) if idx in (duplicates)]} in file {self.name}! Cannot add unless the 'replace' or 'exists_okay' flags are set."
                )

        if position == InsertPosition.FIRST:
            self.objects.insert(0, object)
        elif position == InsertPosition.LAST:
            self.objects.append(object)
        elif position == InsertPosition.DEFAULT:
            indexes = [
                idx for idx, val in enumerate(self.objects) if val._type == object._type
            ]
            if indexes:
                self.objects.insert(indexes[-1] + 1, object)
            else:
                self.objects.append(object)
        elif isinstance(position, int):
            self.objects.insert(position, object)
        else:
            raise ValueError(f"Invalid Position Argument {position}")

    def render(self, serializer: BaseSerializer):
        return serializer.render_namespace(self)

    def save(self, serializer: BaseSerializer):
        try:
            with open(self.location, "w") as file:
                file.write(self.render(serializer))
        # if directory doesn't exist, create it
        except FileNotFoundError:
            import os

            os.makedirs(os.path.dirname(self.location))
            self.save(serializer=serializer)

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
