import re
from collections import defaultdict
from fnmatch import fnmatch
from os.path import dirname
from pathlib import Path, PurePath
from typing import Dict, List, Union, Any
from typing import Optional, TYPE_CHECKING

from pyterraformer.constants import logger
from pyterraformer.core.generics import Literal, BlockList
from pyterraformer.core.utility import get_root
from pyterraformer.serializer import BaseSerializer
from pyterraformer.terraform import Terraform

if TYPE_CHECKING:
    from pyterraformer.core.namespace import TerraformFile
    from pyterraformer.core.generics.variables import Variable


def process_attribute(input: Any, level=0):
    from pyterraformer.core.generics import Variable

    # if isinstance(input, Block):
    #     input = {input.name: input._keys}

    if not isinstance(input, dict):
        return input
    output: Dict[str, Any] = {}
    for key, item in input.items():
        if isinstance(item, Variable):
            output[key] = item.render_basic()
        # elif isinstance(item, StringLit):
        #     output[key] = item.__repr__()
        elif isinstance(item, Literal):
            output[key] = item
        elif isinstance(item, BlockList):
            for idx, sub_item in enumerate(item):
                output[f"{key}~~block_{idx}"] = process_attribute(sub_item)
        elif isinstance(item, dict):
            output[key] = process_attribute(item)
        elif isinstance(item, List):
            output[key] = [process_attribute(sub_item) for sub_item in item]
        else:
            output[key] = item
    return output


class LazyFileDict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def iter(self):
        from pyterraformer.core.namespace import LazyFile

        for key, value in super().iter():
            if isinstance(value, LazyFile):
                value = value.resolve()
                self[key] = value
            yield key, value

    def items(self, resolve=True):
        from pyterraformer.core.namespace import LazyFile

        for key, value in super().items():
            if isinstance(value, LazyFile) and resolve:
                value = value.resolve()
                self[key] = value
            yield key, value

    def __getitem__(self, key):
        from pyterraformer.core.namespace import LazyFile

        val = dict.__getitem__(self, key)
        if isinstance(val, LazyFile):
            val = val.resolve()
            self[key] = val
        return val

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)


def extract_errors(input: str):
    found = re.findall(
        r"(Error:.*)(?:Error:|$)", input, re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    return "\n".join(found).strip()


class TerraformWorkspace(object):
    def __init__(
        self,
        path: Union[str, PurePath],
        terraform: Optional[Terraform] = None,
        serializer: Optional[BaseSerializer] = None,
        files: Optional[List["TerraformFile"]] = None,
        children: Optional[List["TerraformWorkspace"]] = None,
    ):

        self.terraform = terraform
        self.path = str(path)
        self._path = Path(self.path)
        self.files: Dict[str, TerraformFile] = LazyFileDict()
        if files:
            for file in files:
                self.files[file.name] = files
        self.children: List[TerraformWorkspace] = children or []
        self.name = self._path.stem
        self.variables: Dict[str, "Variable"] = {}
        self.data: List = []
        self.serializer = serializer

    def apply(self):
        return self.terraform.run(["apply", "--auto-approve"], path=self._path)

    @property
    def terraform_path(self):
        return get_root(self._path)

    def relative_path(self, path: str):
        return get_root(str(self._path), path)

    def get_file_safe(self, name: str) -> "TerraformFile":
        from pyterraformer.core.namespace import TerraformFile

        out = self.files.get(name)
        if not out:
            try:
                if not self.serializer:
                    raise FileNotFoundError("No valid serializer found.")
                file = self.serializer.parse_file(self._path / name, self)
            except FileNotFoundError:
                file = TerraformFile(
                    workspace=self, text="", location=self._path / name
                )

            self.files[name] = file

        return self.files[name]

    def get_terraform_config(self):
        from pyterraformer.core.generics import TerraformConfig
        from pyterraformer.core.generics import BlockList

        terraform = self.get_file_safe("terraform.tf")
        existing = [
            obj for obj in terraform.objects if isinstance(obj, TerraformConfig)
        ]
        if existing:
            return existing[0]
        logger.info("creating new terraform config")
        config = TerraformConfig(
            backend=self.terraform.backend.as_object(),
            required_providers=BlockList([{}]),
        )
        terraform.add_object(config)
        return config

    def add_provider(self, name: str, source: str, **kwargs):
        existing = self.get_terraform_config()
        required_providers = getattr(existing, "required_providers", BlockList([{}]))
        required_providers[0][name] = {"source": source, **kwargs}
        existing.required_providers = required_providers

    def add_file(self, file: Union["TerraformFile", PurePath, str]) -> "TerraformFile":
        from pyterraformer.core.namespace import TerraformFile

        if isinstance(file, TerraformFile):
            self.files[file.name] = file
            return file
        elif str(file) in self.files:
            return self.files[str(file)]
        else:
            nfile = TerraformFile(workspace=self, text="", location=self._path / file)
            self.files[nfile.name] = nfile
            return nfile

    def add_child_workspace(self, path: str):
        child = TerraformWorkspace(
            path=path, serializer=self.serializer, terraform=self.terraform
        )
        self.children.append(child)
        setattr(self, child.name, child)

    def add_variable(
        self, key: str, values, exists_okay: bool = False, replace: bool = False
    ):
        from pyterraformer.core.generics.variables import Variable

        if key in self.variables:
            if exists_okay:
                return self.variables[key]
            elif replace:
                pass
            else:
                raise ValueError(f"Key {key} already exists in variables!")

        if isinstance(values, dict):
            vtype = "map"
            variable = Variable(None, key, [["type", vtype], ["default", values]])
        elif isinstance(values, str):
            vtype = "string"
            variable = Variable(None, key, [["type", vtype], ["default", values]])
        elif isinstance(values, Variable):
            variable = values
        else:
            raise ValueError(f"Unable to map {type(values)} to a variable type")

        self.variables[key] = variable
        # create if not exists
        if "variables.tf" not in self.files:
            self.files["variables.tf"] = TerraformFile(
                self, "", self._path / "variables.tf"
            )

        self.files["variables.tf"].add_object(variable, replace=replace)
        return variable

    def delete_variable(self, key: str, safe=False):
        try:
            variable = self.variables[key]
        except KeyError as e:
            if safe:
                return
            raise e
        self.files["variables.tf"].delete_object(variable)

    def save(self, format: bool = True, apply: bool = False):
        from pyterraformer.core.namespace import LazyFile

        if not self.serializer:
            raise ValueError("Cannot save without serializer defined.")
        for key, file in self.files.items(resolve=False):  # type: ignore
            # skip files we never touched
            if isinstance(file, LazyFile):
                logger.info("Skipping lazily unparsed file")
                continue
            file.save(self.serializer)
            if format and self.terraform:
                if str(file.location).endswith(".tf"):
                    try:
                        self.terraform.run(
                            ["fmt", str(file.location)], path=dirname(file.location)
                        )
                    except Exception as e:
                        with open(file.location, "r") as output:
                            comparison = output.read()
                            logger.error(f"Error parsing {comparison}")
                        raise e
        if apply:
            self.apply()

    def save_all(self, format=True):
        self.save(format)
        for ws in self.children:
            ws.save_all(format)

    def find(self, object_type, invert=False):
        from pyterraformer.core.namespace import LazyFile

        output = defaultdict(list)
        replace = {}
        # resolve any files, so we can search them
        for key, file in self.files.items():
            if isinstance(file, LazyFile):
                replace[key] = file.resolve()
        for key, item in replace.items():
            self.files[key] = item
        for key, file in self.files.items():
            for object in file.objects:
                if isinstance(object, object_type):
                    output[key].append(object)
        if invert:
            out_list = {}
            for key, items in output.items():
                for item in items:
                    out_list[item] = key
            return out_list
        return output

    def get_object(self, **kwargs):
        for key, file in self.files.items():
            try:
                return file.get_object(**kwargs)
            except ValueError:
                pass
        raise ValueError(
            f"No object matching filter criteria {kwargs} found in any files in {self.path}"
        )


def value_match(item: Any, value: Any) -> bool:
    if isinstance(value, str):
        # first check for string comparison
        if item == value:
            return True
        # then fnmatch with quotes replaced
        return fnmatch(str(item).replace('"', ""), value)
    else:
        return item == value
