import os
from pathlib import Path
from typing import Iterator, List, Union
from fnmatch import fnmatch

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

def value_match(item, value) -> bool:
    if isinstance(value, str):
        # first check for string comparison
        if item == value:
            return True
        # then fnmatch with quotes replaced
        return fnmatch(str(item).replace('"', ""), value)
    else:
        return item == value