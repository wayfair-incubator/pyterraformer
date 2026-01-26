from dataclasses import dataclass
from typing import ClassVar

from pyterraformer.core.generics import Backend


@dataclass
class BaseBackend:
    SECRET_FIELDS: ClassVar[list[str]] = []

    def generate_environment(self) -> dict:
        return {}

    def as_object(self) -> Backend:
        return Backend("undefined")
