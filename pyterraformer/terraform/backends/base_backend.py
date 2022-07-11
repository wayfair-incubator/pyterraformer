from dataclasses import dataclass
from typing import Dict, ClassVar

from pyterraformer.core.generics import Backend


@dataclass
class BaseBackend:
    SECRET_FIELDS: ClassVar = []

    def generate_environment(self) -> Dict:
        return {}

    def as_object(self) -> Backend:
        return Backend("undefined")
