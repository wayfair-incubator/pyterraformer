from pathlib import PurePath
from typing import Union, TYPE_CHECKING
from os import listdir
from os.path import isfile, join

if TYPE_CHECKING:
    from pyterraformer.core import TerraformWorkspace, TerraformFile


class BaseParser():
    def __init__(self):
        pass

    def parse_string(self, input:str)->"TerraformFile":
        raise NotImplementedError

    def parse_file(self, path:Union[str, PurePath])->"TerraformFile":
        if not isinstance(path, PurePath):
            path = PurePath(path)
        with open(path, 'r', encoding='utf-8') as f:
            return self.parse_string(f.read())

    def parse_workspace(self,path:Union[str, PurePath])->"TerraformWorkspace":
        if not isinstance(path, PurePath):
            path = PurePath(path)

        files = [f for f in listdir(path) if isfile(join(path, f))]

        return TerraformWorkspace(path=path)