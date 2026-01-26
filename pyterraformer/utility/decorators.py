from types import MethodType


class lazy_property:
    """used for lazy evaluation of an object attribute. property should represent non-mutable data, as it replaces itself."""

    def __init__(self, fget):
        self.fget = fget
        self.func_name = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj, self.func_name, value)

        setattr(obj, f"_method_{self.func_name}", MethodType(self.fget, obj))
        return value
