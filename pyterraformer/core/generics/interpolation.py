"""This module contains classes for resolving values out
of a parsed set of Terraform files.

These can have complex and condition resolution orders.

For example, consider the following
project = "${var.bigquery_processing_project["${terraform.workspace}"].test}"

This can be broken into the following

StringLit
    Interpolation
        PropertyLookup -> Resolve Left to Right
            DictLookup -> Resolve Left to Right
                StringLit
                    Interpolation
                        PropertyLookup -> Resolve Left to Right
            PropertyLookup -> Resolve Left to Right
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyterraformer.core.namespace import TerraformFile, TerraformNamespace
    from pyterraformer.core.workspace import TerraformWorkspace


@dataclass
class UnresolvedLookup:
    base: Any
    property: Any


class Resolvable:
    def resolve(self, workspace, file, parent, parent_instance):
        return self


def _resolver_function(arg, workspace, file, parent, parent_instance):
    if isinstance(arg, Resolvable):
        resolved = arg.resolve(workspace, file, parent, parent_instance)
        if resolved is None:
            raise ValueError("Unable to resolve function")
        return resolved
    else:
        if not arg:
            raise ValueError
        return arg


def variable_helper(arg, workspace, file, parent, parent_instance):
    from pyterraformer.core.generics.variables import Variable

    if isinstance(arg, Variable):
        return arg.default.resolve(workspace, file, parent, parent_instance)
    return arg


class FileLookupInstantiator(Resolvable):
    def __init__(self, workspace: "TerraformWorkspace"):
        for key, file in workspace.files.items():
            for object in file.objects:
                if hasattr(object, "id"):
                    setattr(self, object.id, object)
                if hasattr(object, "_name"):
                    setattr(self, object._name, object)


class FileObjectLookupInstantiator(Resolvable):
    def __init__(self, workspace: "TerraformWorkspace"):
        # TODO: 2022-06-05 figure out how to do this bette
        from pyterraformer.core.namespace import LazyFile

        self.workspace = workspace
        objects = []
        for key, file in self.workspace.files.items():
            if isinstance(file, LazyFile):
                file = file.resolve()
                workspace.files[key] = file

            for object in file.objects:
                objects.append(object)
        self.objects = objects

    def __getattr__(self, item):
        return FileObjectSubClassLookupInstantiator(
            [
                obj
                for obj in self.objects
                if hasattr(obj, "_type") and obj._type == str(item)
            ]
        )


class FileObjectSubClassLookupInstantiator(Resolvable):
    def __init__(self, obj_list):
        self.obj_list = obj_list

    def __getattr__(self, item):
        try:
            return [obj for obj in self.obj_list if obj.id == item][0]
        except IndexError:
            return f"<could not compute {item} from file lookup>"


class DataLookupInstantiator(Resolvable):
    def __init__(self, workspace: "TerraformWorkspace"):
        self.workspace = workspace

    def __getattr__(self, item):
        return DataSubClassLookupInstantiator(
            [
                obj
                for obj in self.workspace.data
                if hasattr(obj, "type") and obj.type == str(item)
            ]
        )


class DataSubClassLookupInstantiator(Resolvable):
    def __init__(self, obj_list):
        self.obj_list = obj_list

    def __getattr__(self, item):
        return [obj for obj in self.obj_list if obj.name == item][0]


class VariableLookupInstantiator(Resolvable):
    def __init__(self, workspace: "TerraformWorkspace"):
        for key, value in workspace.variables.items():
            setattr(self, key, value)


class TerraformLookupInstantiator(Resolvable):
    def __init__(self, workspace: "TerraformWorkspace"):
        if workspace.terraform:
            self.workspace = workspace.terraform.workspace
        else:
            self.workspace = "undefined"


class LocalLookupInstantiator(Resolvable):
    def __init__(self, file: "TerraformFile"):
        for key, value in file.locals.items():
            setattr(self, key, value)


class CountLookupInstantiator(Resolvable):
    def __init__(self):
        pass

    @property
    def index(self):
        return 1


class Interpolation(Resolvable):
    def __init__(self, contents):
        self.contents = contents

    def __repr__(self):
        return "${{{}}}".format("".join([f"{val.__repr__()}" for val in self.contents]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        parent = None
        # an interpolation always resets parent_instances
        parent_instance = self
        resolve = deepcopy(self.contents)
        resolved = []
        while resolve:
            next = resolve.pop(0)
            parent = _resolver_function(next, workspace, file, parent, parent_instance)
            resolved.append(parent)
            parent_instance = next
        if parent is None:
            raise ValueError(f"No values for interpolation {resolved}")
        return parent


class DictLookup(Resolvable):
    def __init__(self, base, lookup):
        self.base = base
        # TODO don't return a list here
        self.contents = lookup
        # the lookup will be a nested list
        self.lookup = lookup[0]

    def __repr__(self):
        return f"{self.base.__repr__()}[{self.lookup.__repr__()}]"

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        """ex: bigquery_processing_project["${terraform.workspace}"]
        to resolve a dict lookup
        we will resolve the lookup, then
        """
        parent = parent or self.base
        lookup = deepcopy(self.lookup)
        lookup = lookup.resolve(workspace, file, None, self)
        results = parent[lookup]
        return _resolver_function(results, workspace, file, None, self)


class ArrayLookup(Resolvable):
    def __init__(self, base, lookup):
        self.base = base
        # TODO don't return a list here
        self.contents = lookup
        # the lookup will be a nested list
        self.lookup = lookup[0]

    def __repr__(self):
        return f"{self.base.__repr__()}[{self.lookup.__repr__()}]"

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        """ex: bigquery_processing_project["${terraform.workspace}"]
        to resolve a dict lookup
        we will resolve the lookup, then
        """
        parent = parent or self.base
        lookup = deepcopy(self.lookup)
        lookup = int(lookup.resolve(workspace, file, None, self))
        results = parent[lookup]
        return _resolver_function(results, workspace, file, None, self)


class PropertyLookup(Resolvable):
    def __init__(self, base, attributes: List):
        self.base = base
        self.contents = attributes
        self.property = attributes[0]

    def __repr__(self):
        return "{}.{}".format(self.base.__repr__(), self.property.__repr__())

    def resolve(
        self,
        workspace: "TerraformWorkspace",
        file: "TerraformFile",
        parent: Optional[Resolvable] = None,
        parent_instance: Optional[Resolvable] = None,
    ):

        anchor = parent or self.base
        if self.base == "module":
            anchor = FileLookupInstantiator(workspace)
        elif self.base == "var":
            anchor = VariableLookupInstantiator(workspace)
        elif self.base == "terraform":
            anchor = TerraformLookupInstantiator(workspace)
        elif self.base == "data":
            anchor = DataLookupInstantiator(workspace)
        elif self.base == "locals":
            anchor = LocalLookupInstantiator(file)
        elif self.base == "count":
            anchor = CountLookupInstantiator()
        elif not parent:
            anchor = getattr(FileObjectLookupInstantiator(workspace), str(self.base))
        # the lookup could be another property or a dictionary
        # in either case, pull out the base value and look that up immediately
        # then pass forward

        if isinstance(self.property, (DictLookup, PropertyLookup)):
            local_resolved = getattr(anchor, str(self.property.base))
            return self.property.resolve(
                workspace, file, parent=local_resolved, parent_instance=self
            )
        else:
            try:
                return getattr(anchor, str(self.property))
            except AttributeError:
                return UnresolvedLookup(anchor, self.property)


class StringLit(Resolvable):
    def __init__(self, contents:List):
        self.contents = contents

    @property
    def string(self)->str:
        return ''.join([str(v) for v in self.contents])

    def __add__(self, v):
        return self.string.__add__(v)

    def __hash__(self):
        return hash(str(self))

    def split(self, splitter: str = " "):
        return str(self.contents).split(splitter)

    def __eq__(self, other):
        return str(self).replace('"', "") == str(other) or str(self) == str(other)

    def __repr__(self):
        return '"{}"'.format("".join([val.__repr__() for val in self.contents]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        return "".join(
            [
                str(
                    variable_helper(
                        item.resolve(workspace, file, parent, parent_instance),
                        workspace,
                        file,
                        parent,
                        parent_instance,
                    )
                )
                for item in self.contents
            ]
        )


class String(Resolvable):
    def __init__(self, item):
        self.item = item

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return self.item

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        if isinstance(parent_instance, PropertyLookup):
            resolved = PropertyLookup(self.item).resolve(
                workspace, file, parent, parent_instance
            )
            return resolved
        return self.item


class File(Resolvable):
    def __init__(self, item):
        self.item = item[0] if isinstance(item, list) else item

    def __repr__(self):
        return "file({})".format(self.item.__repr__())

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        if isinstance(parent_instance, PropertyLookup):
            resolved = PropertyLookup(self.item).resolve(
                workspace, file, parent, parent_instance
            )
            out = resolved
        else:
            out = self.item
        return f"file({out})"


class Concat(Resolvable):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return "concat({})".format(",".join([item.__repr__() for item in self.items]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        final = []
        for item in self.items:
            if isinstance(parent_instance, PropertyLookup):
                resolved = PropertyLookup(item).resolve(
                    workspace, file, parent, parent_instance
                )
                out = resolved
            elif isinstance(item, Resolvable):
                out = item.resolve(workspace, file, None, None)
            else:
                out = item
            final.append(out)
        if all([isinstance(item, str) for item in final]):
            concat = "".join(final)
        else:
            concat = []
            for item in final:
                concat += item
        return f"concat({concat})"


class Types(Resolvable):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return "types({})".format(",".join([item.__repr__() for item in self.items]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        # final = []
        # for item in self.items:
        #     if isinstance(parent_instance, PropertyLookup):
        #         resolved = PropertyLookup(item).resolve(workspace, file, parent, parent_instance)
        #         out = resolved
        #     else:
        #         out = item
        #     final.append(out)
        # concat = ",".join(final)
        return "types({})".format(",".join([item.__repr__() for item in self.items]))


class Replace(Resolvable):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return "replace({})".format(",".join([item.__repr__() for item in self.items]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        final = []
        for item in self.items:
            if isinstance(parent_instance, PropertyLookup):
                resolved = PropertyLookup(item).resolve(
                    workspace, file, parent, parent_instance
                )
                out = resolved
            else:
                out = item
            final.append(out)
        concat = ",".join(final)
        return f"replace({concat})"


class GenericFunction(Resolvable):
    def __init__(self, items):
        self.name = str(items[0])
        self.items = items[1:]

    def __repr__(self):
        return "{}({})".format(
            self.name, ",".join([item.__repr__() for item in self.items])
        )

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        final = []
        for item in self.items:
            if isinstance(parent_instance, PropertyLookup):
                resolved = PropertyLookup(item).resolve(
                    workspace, file, parent, parent_instance
                )
                out = resolved
            else:
                out = item
            final.append(out)
        concat = ",".join([item.__repr__() for item in final])
        return f"{self.name}({concat})"


class Merge(Resolvable):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return "merge({})".format(",".join([item.__repr__() for item in self.items]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        final = []
        for item in self.items:
            if isinstance(parent_instance, PropertyLookup):
                resolved = PropertyLookup(item).resolve(
                    workspace, file, parent, parent_instance
                )
                out = resolved
            else:
                out = item
            final.append(out)
        concat = ",".join(final)
        return f"merge({concat})"


class Conditional(Resolvable):
    def __init__(self, args):
        self.bool = args[0]
        self.true = args[1]
        self.false = args[2]

    def __repr__(self):
        return f"{self.bool} ? {self.true} : {self.false}"

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        boolean_eval = self.bool.resolve(workspace, file, parent, parent_instance)
        if boolean_eval:
            return self.true.resolve(workspace, file, parent, parent_instance)
        else:
            return self.false.resolve(workspace, file, parent, parent_instance)


class Parenthetical(Resolvable):
    def __init__(self, args):
        self.contents = args

    def __repr__(self):
        return "({})".format("".join([val.__repr__() for val in self.contents]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        # parent = None
        parent_instance = self
        resolve = deepcopy(self.contents)
        while resolve:
            next = resolve.pop(0)
            parent = _resolver_function(next, workspace, file, parent, parent_instance)
            parent_instance = next
        if parent is None:
            raise ValueError(f"No values for interpolation {self.contents}")
        return parent


class Expression(Resolvable):
    def __init__(self, args):
        self.args = args

    def __repr__(self):
        return "".join([val.__repr__() for val in self.args])

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        output = self.args[0]
        if hasattr(output, "resolve"):
            return self.args[0].resolve(workspace, file, parent, parent_instance)
        else:
            return output


class BinaryOp(Resolvable):
    def __init__(self, args):
        self.args = args

    def __repr__(self):
        return "".join([val.__repr__() for val in self.args])

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        all = [item.resolve(workspace, file, parent) for item in self.args]
        left = all[0]
        operator, right = all[1]
        if isinstance(parent_instance, PropertyLookup):
            left = PropertyLookup(left).resolve(
                workspace, file, parent, parent_instance
            )
        if operator == "==":
            return left == right
        elif operator == ">=":
            return left >= right
        elif operator == "<=":
            return left <= right
        elif operator == "!=":
            return left != right
        elif operator == "%":
            return True
        else:
            raise ValueError(f"Unable to do comparison {left}, {operator}, {right}")


class BinaryOperator(Resolvable):
    def __init__(self, args):
        self.args = args

    def __repr__(self):
        return str(self.args[0].value)

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        return str(self.args[0].value)


class BinaryTerm(Resolvable):
    def __init__(self, args):
        self.args = args

    def __repr__(self):
        return "".join([val.__repr__() for val in self.args])

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        return [
            item.resolve(workspace, file, parent, parent_instance) for item in self.args
        ]


class Boolean(Resolvable):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value.__eq__(other)

    def __repr__(self):
        if self.value:
            return "true"
        return "false"


class Block(Resolvable):
    log_keys = False

    def __init__(self, name, values):
        self._keys = {}
        self.name = str(name)
        self.values = values
        for attribute in self.values:
            if isinstance(attribute, list):
                # always cast keys to string
                key = str(attribute[0])
                val = attribute[1]
                if isinstance(val, Block):
                    base = getattr(self, key, Block)
                    base.append(val)
                    val = base
                setattr(self, key, val)
                self._keys[key] = val
            elif isinstance(attribute, Block):
                key = str(attribute.name)
                base = getattr(self, attribute.name, Block())
                base.append(attribute)
                setattr(self, key, base)
                self._keys[key] = attribute
            self.log_keys = True

    def __setattr__(self, key, value):
        if self.log_keys and key in self._keys:
            self._keys[key] = value
        super().__setattr__(key, value)

    def __repr__(self):
        out = []
        for key, item in self._keys.items():
            if isinstance(item, Block):
                for sub in item:
                    out.append(f"{key} {sub.__repr__()}")
            elif isinstance(item, Block):
                out.append(f"{key} {item.__repr__()}")
            else:
                out.append(f"{key}={item.__repr__()}")
        out = "\n".join(out)
        return f"""{{
        {out}
        }}"""


class Symlink(Resolvable):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value.__eq__(other)

    def __repr__(self):
        return "".join([val.__repr__() for val in self.value])


class LegacySplat(Resolvable):
    def __init__(self, args):
        self.contents = args

    def __repr__(self):
        return "{}".format(*[val.__repr__() for val in self.contents[:1]])

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        # parent = None
        parent_instance = self
        resolve = deepcopy(self.contents)
        while resolve:
            next = resolve.pop(0)
            parent = _resolver_function(next, workspace, file, parent, parent_instance)
            parent_instance = next
        if parent is None:
            raise ValueError(f"No values for interpolation {self.contents}")
        return parent


class ToSet(Resolvable):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return "toset({})".format(",".join([item.__repr__() for item in self.items]))

    def resolve(self, workspace, file, parent=None, parent_instance=None):
        final = []
        for item in self.items:
            if isinstance(parent_instance, PropertyLookup):
                resolved = PropertyLookup(parent_instance, item).resolve(
                    workspace, file, parent, parent_instance
                )
                out = resolved
            else:
                out = item
            final.append(out)
        concat = ",".join(final)
        return f"toset({concat})"
