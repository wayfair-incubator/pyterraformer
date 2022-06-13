from dataclasses import dataclass
from typing import Dict, ClassVar


@dataclass
class BaseBackend:
    SECRET_FIELDS: ClassVar = []

    def generate_environment(self) -> Dict:
        return {}
