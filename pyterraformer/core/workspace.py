import os
import re
import tempfile
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path
from subprocess import CalledProcessError, run as sub_run
from typing import Dict, List, Union, Iterator, Any
from pyterraformer.terraform import Terraform
from pyterraformer.serializer import

import jinja2
from analytics_utility_core.decorators import lazy_property
from analytics_utility_core.secrets import secret_store

from analytics_terraformer_core.constants import (
    TERRAFORM_PATH,
    BASE_TERRAFORM_VERSION,
    BASE_CI_TERRAFORM_VERSION,
    BASE_GOOGLE_VERSION,
    BASE_NULL_VERSION,
    TEMPLATE_PATH,
    TERRAFORM_BIN_PATH,
    STATE_BUCKET,
    TERRAFORM_SA_DEV,
    TERRAFORM_SA
)
from analytics_terraformer_core.exceptions import ValidationError, TerraformApplicationError
from analytics_terraformer_core.meta_classes import Literal, Block
from analytics_terraformer_core.workflows.enums import ExecutionMode

template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_PATH)
env = jinja2.Environment(loader=template_loader, autoescape=True, keep_trailing_newline=True)

DEFAULT_EXTRACTOR = re.compile('\s+([A-z]+)\s+=\s+"(.*?)(?<!\[)"(?!\])')

DEFAULT_PROVIDER_ACCOUNT = 'file("./credentials/terraform-${terraform.workspace}@wf-gcp-gb-ae-support-prod.iam.gserviceaccount.com.json")'


def process_attribute(input: Any, level=0):
    from analytics_terraformer_core.generics import Variable

    # if isinstance(input, Block):
    #     input = {input.name: input._keys}

    if not isinstance(input, dict):
        return input
    output = {}
    for key, item in input.items():
        if isinstance(item, Variable):
            output[key] = item.render_basic()
        # elif isinstance(item, StringLit):
        #     output[key] = item.__repr__()
        elif isinstance(item, Literal):
            output[key] = item
        elif isinstance(item, Block):
            for idx, sub_item in enumerate(item):
                output[f"{key}~~block_{idx}"] = process_attribute(sub_item)
        elif isinstance(item, dict):
            output[key] = process_attribute(item)
        elif isinstance(item, List):
            output[key] = [process_attribute(sub_item) for sub_item in item]
        else:
            output[key] = item
    return output


def splitall(path: str) -> Iterator[str]:
    out: List[str] = []
    while True:
        base, end = os.path.split(path)
        if base and end:
            out.append(end)
        else:
            out.append(base)
            break
        path = base
    return reversed(out)


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


class TerraformObject(object):
    extractors: Dict[str, str] = {}

    def __init__(self, type, original_text, attributes):
        from analytics_terraformer_core.generics import Block

        self.render_variables: Dict[str, str] = {}
        self.attributes = attributes or []
        for attribute in self.attributes:
            if isinstance(attribute, list):
                # always cast keys to string
                self.render_variables[str(attribute[0])] = attribute[1]
            elif isinstance(attribute, Block):
                base = self.render_variables.get(attribute.name, Block())
                base.append(attribute)
                self.render_variables[attribute.name] = base
        self._type: str = type
        self._original_text: str = original_text
        self._changed = False
        self._workspace = None
        self._file = None
        # for key, extractor in self.extractors.items():
        #     match = re.findall(extractor, self._original_text, re.DOTALL)
        #     if match:
        #         self.render_variables[key] = match[0]
        # defaults = DEFAULT_EXTRACTOR.findall(self._original_text, re.DOTALL)
        # for val in defaults:
        #     if val[0] not in self.render_variables:
        #         self.render_variables[val[0]] = val[1]
        self._initialized = True

    def __repr__(self):
        return (
            f"{self._type}("
            + ", ".join([f'{key}="{val}"' for key, val in self.render_variables.items()])
            + ")"
        )

    @classmethod
    def create(cls, id, **kwargs):
        kwargs = kwargs or {}

        attributes = [[key, item] for key, item in kwargs.items()]
        if hasattr(cls, "REQUIRED_ATTRIBUTES"):
            for attribute in cls.REQUIRED_ATTRIBUTES:
                if attribute not in kwargs:
                    raise ValidationError(f"Missing required attribute {attribute}")
        ctype = getattr(cls, "type", kwargs.get("type", "Unknown"))
        return cls(id, ctype, text=None, attributes=attributes)

    @property
    def tf_attributes(self):
        return self.render_variables.keys()

    def __getattr__(self, name):
        if name == "render_variables":
            return self.__dict__.get("render_variables")
        elif self.render_variables and name in self.render_variables:
            return self.__dict__.get("render_variables").get(name)
        elif (
            self.render_variables
            and "_" in name
            and name.endswith("resolved")
            and name.rsplit("_", 1)[0] in self.render_variables
        ):
            lookup = name.rsplit("_", 1)[0]
            return self.resolved_attributes.get(lookup)
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        """This gets tricky:
        We want any new attribute set on a base class to get rendered...
        Unless it's one of the internal attributes we use for managing objects.
        So skip anything with a private method, or in the disallow list...
        Unless it's also in the list of things that we should render.
        Woof."""
        if name.startswith("_") or (
            name in ("row_num", "template", "name", "id")
            and not (self.render_variables and name in self.render_variables)
        ):
            super().__setattr__(name, value)
        elif (self.render_variables and name in self.render_variables) or getattr(
            self, "_initialized", False
        ):
            self._changed = True
            self.__dict__.get("render_variables")[name] = value
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if self.render_variables and name in self.render_variables:
            self._changed = True
            del self.__dict__.get("render_variables")[name]
        else:
            super().__delattr__(name)

    @property
    def changed(self):
        return self._original_text and not self._changed

    @lazy_property
    def template(self):
        try:
            out = env.get_template(f"{self._type}.tf")
            if not out:
                raise ValueError(f"could not get template {self._type}")
            return env.get_template(f"{self._type}.tf")
        except Exception as e:
            return env.get_template(f"generic.tf")

    @lazy_property
    def variables(self):
        return env.parse(env.loader.get_source(env, f"{self._type}.tf")[0])

    @property
    def text(self):
        if not self._changed and self._original_text:
            return self._original_text
        else:
            return self.render()

    def render(self, variables=None):
        from analytics_terraformer_core.generics import StringLit

        variables = variables or {}
        final = {}
        for key, item in self.render_variables.items():
            if (
                isinstance(item, StringLit)
                and len(item.contents) == 1
                and str(item).startswith('"${')
                and str(item).endswith('$}"')
            ):
                item = str(item)[3:-3]
                final[key] = Literal(item)
            else:
                final[key] = item
        output = process_attribute(final)
        if not self.template:
            raise ValueError(self._type + self._original_text)
        return self.template.render(**output, render_attributes=output, **variables)

    def resolve_item(self, item):
        from analytics_terraformer_core.generics import Variable

        if isinstance(item, list):
            resolved = [self.resolve_item(sub_item) for sub_item in item]
        elif isinstance(item, str):
            resolved = item
        elif isinstance(item, int):
            resolved = item
        elif isinstance(item, dict):
            resolved = item
        else:
            resolved = item.resolve(self._workspace, self._file, None, None)
        if isinstance(resolved, Variable) and hasattr(resolved, "default"):
            resolved = getattr(resolved, "default")
        return resolved

    @property
    def resolved_attributes(self):
        out = {}
        for key, item in self.render_variables.items():
            resolved = self.resolve_item(item)
            out[str(key)] = resolved

        return out


class LazyFile(object):
    def __init__(self, file, parent):
        self.file = file
        self.parent = parent
        self.name = os.path.basename(file)

    def resolve(self):
        from analytics_terraformer_core.parser import parse_file

        return parse_file(self.file, self.parent)


class LazyFileDict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def iter(self):
        for key, value in super().iter():
            if isinstance(value, LazyFile):
                value = value.resolve()
                self[key] = value
            yield key, value

    def items(self, resolve=True):
        for key, value in super().items():
            if isinstance(value, LazyFile) and resolve:
                value = value.resolve()
                self[key] = value
            yield key, value

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        if isinstance(val, LazyFile):
            val = val.resolve()
            self[key] = val
        return val

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)


def extract_errors(input: str):
    found = re.findall(r"(Error:.*)(?:Error:|$)", input, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return "\n".join(found).strip()


class TerraformWorkspace(object):
    def __init__(self, path: str, terraform:Terraform):
        from pyterraformer.parser.generics.variables import Variable
        self.terraform = terraform
        self.path = path
        self._path = Path(self.path)
        self.files: Dict[str, TerraformFile] = LazyFileDict()
        self.children: List[TerraformWorkspace] = []
        self.name = self._path.stem
        self.variables: Dict[str, Variable] = {}
        self.data: List = []

    def init(self):
        from pyterraformer.parser.generics import Provider, TerraformConfig, Backend
        from os import makedirs

        makedirs(self.path, exist_ok=True)
        terraform = TerraformFile(self, "", self._path / "terraform.tf")

        return self
    #
    # def apply(self, workspace: str = None):
    #     # default to the local workspace
    #     workspace = workspace or self.env or "prod"
    #     from analytics_terraformer_core.generics import TerraformConfig
    #
    #     if self._applied:
    #         return None
    #     if workspace == "dev":
    #         creds = secret_store[TERRAFORM_SA_DEV]
    #     else:
    #         creds = secret_store[TERRAFORM_SA]
    #     # temporary override for VPC work
    #     # creds = secret_store["eden-terraform-sa"]
    #     state_config = self.files["terraform.tf"]
    #     for obj in state_config.objects:
    #         # this handling can be cleaned up after all existing paths have been fixed
    #         # but provides backwards compatibility with the initial [incorrect] state sitch
    #         if isinstance(obj, TerraformConfig):
    #             obj.backends[0].prefix = f"terraform/state/{self.terraform_path}"
    #             if "encryption_key" in obj.backends[0].render_variables:
    #                 del obj.backends[0].render_variables["encryption_key"]
    #             obj._changed = True
    #     changed = state_config.save()
    #     if not changed:
    #         raise ValueError
    #     with tempfile.TemporaryDirectory() as tmpdirname:
    #         secrets = os.path.join(tmpdirname, "keyfile.json")
    #         with open(secrets, "w") as f:
    #             f.write(creds)
    #         key_path = os.path.join(tmpdirname, "tmpssh")
    #         with open(key_path, "w") as keyfile:
    #             lines = secret_store["ssh_identity"].replace("|", "\n")
    #             keyfile.write(lines)
    #         os.chmod(key_path, 0o600)
    #         ssh_cmd = "ssh -i %s -o StrictHostKeyChecking=no" % keyfile.name.replace("\\", "\\\\")
    #
    #         my_env = os.environ.copy()
    #         my_env["GOOGLE_APPLICATION_CREDENTIALS"] = secrets
    #         my_env["GOOGLE_ENCRYPTION_KEY"] = secret_store["gcs_terraform_encryption_key"]
    #         my_env["TF_PLUG_CACHE_DIR"] = TERRAFORM_BIN_PATH
    #         my_env["TF_PLUGIN_CACHE_DIR"] = TERRAFORM_BIN_PATH
    #         my_env["GIT_SSH_COMMAND"] = ssh_cmd
    #
    #         run_cmd = lambda cmd: sub_run(
    #             cmd, cwd=self.path, env=my_env, check=True, capture_output=True, encoding="utf-8"
    #         ).stdout
    #
    #         try:
    #             # init, then list workspaces
    #             for cmd in [[TERRAFORM_PATH, "init"], [TERRAFORM_PATH, "workspace", "list"]]:
    #                 check = run_cmd(cmd)
    #             # create workspace if required
    #             if workspace not in check:
    #                 run_cmd([TERRAFORM_PATH, "workspace", "new", workspace])
    #             # then select, plan, and apply
    #             # 4/23 removed [TERRAFORM_PATH, "plan"] step - redundant
    #
    #             for cmd in [
    #                 [TERRAFORM_PATH, "workspace", "select", workspace],
    #                 # [TERRAFORM_PATH, "import", "google_access_context_manager_service_perimeter.eden_dev_perimeter",
    #                 #  'accessPolicies/273592504183/servicePerimeters/eden_dev_service_perimeter'],
    #                 # [TERRAFORM_PATH, "plan"],
    #                 [TERRAFORM_PATH, "apply", "-auto-approve"],
    #             ]:
    #                 run = run_cmd(cmd)
    #             self._applied = True
    #             print(run)
    #         except CalledProcessError as e:
    #             errors = extract_errors(e.stderr)
    #             raise TerraformApplicationError(errors)
    #     return str(run)

    @property
    def terraform_path(self):
        return get_root(self._path)

    def relative_path(self, path: str):
        return get_root(str(self._path), path)

    def get_file_safe(self, name: str) -> "TerraformFile":
        out = self.files.get(name)
        if not out:
            self.files[name] = TerraformFile(self, name, os.path.join(self.path, name))
        return self.files[name]

    def add_file(self, file, new=True):
        from pyterraformer.parser import parse_file

        if isinstance(file, str) and not file.endswith("variables.tf"):
            nfile = LazyFile(file, self)
            self.files[nfile.name] = nfile
            return
        elif isinstance(file, str):
            parsed = parse_file(file, self)
            self.files[parsed.name] = parsed
            return
        if new:
            file.changed = True
        self.files[file.name] = file

    def add_child_workspace(self, path, escalate_failure=True):
        from analytics_terraformer_core.parser import parse_workspace

        child = parse_workspace(path, escalate_failure=escalate_failure)
        self.children.append(child)
        setattr(self, child.name, child)

    def add_variable(self, key: str, values, exists_okay=False, replace=False):
        from analytics_terraformer_core.generics.variables import Variable

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
            self.files["variables.tf"] = TerraformFile(self, "", self._path / "variables.tf")

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

    def add_data(self, type, name, **kwargs):
        if type in self.data:
            raise ValueError(f"Type {type} already exists in data!")
        from analytics_terraformer_core.generics import Data

        datum = Data(None, type, name, [])
        self.data[type] = datum
        # create if not exists
        if "datasources.tf" not in self.files:
            self.files["datasources.tf"] = TerraformFile(self, "", self._path / "datasources.tf")

        self.files["datasources.tf"].add_object(datum)
        return datum

    def save(self, format: bool = True, force_apply: bool = False):

        if self.type_ == ExecutionMode.CI:
            force_apply = True

        changed = []
        for key, file in self.files.items(resolve=False):  # type: ignore
            # skip files we never touched
            if isinstance(file, LazyFile):
                continue
            # and ones we've never changed
            if not file.changed_flag:
                continue
            check = file.save()
            if format:
                from subprocess import check_output

                if str(file.location).endswith(".tf"):
                    cmds = [str(TERRAFORM_PATH), str("fmt"), str(file.location)]
                    try:
                        check_output(cmds)
                    except Exception as e:
                        with open(file.location, "r") as output:
                            comparison = output.read()
                            print(comparison)
                        raise e
            with open(file.location, "r") as output:
                comparison = output.read()
            if check is not False and check != comparison:
                changed.append(file)
            elif force_apply:
                changed.append(file)
            elif check is not False and check == comparison:
                print("skipping, no changes after formatting")
        return changed

    def save_all(self, format=True):
        self.save(format)
        for ws in self.children:
            ws.save_all(format)

    def find(self, object_type, invert=False):
        output = defaultdict(list)
        replace = {}
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


def value_match(item, value) -> bool:
    if isinstance(value, str):
        # first check for string comparison
        if item == value:
            return True
        # then fnmatch with quotes replaced
        return fnmatch(str(item).replace('"', ""), value)
    else:
        return item == value



