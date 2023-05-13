import typing as t

T = t.TypeVar("T")
_MAPPING: t.Mapping[str, "ConVar"] = {}


class _MissingType:
    def __eq__(self, other: t.Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<MISSING>"


MISSING: t.Any = _MissingType()


class ConVar(t.Generic[T]):
    """
    ContextVars were giving me a headache, so I made a workaround with a similar api.
    if name already exists grabs the clone
    """

    # @t.overload # FIXME: typing over load not working
    # def __init__(self, name: str) -> None:
    # ...

    def __init__(self, name: str, *, default: T = MISSING) -> None:
        if o := _MAPPING.get(name):
            self.__dict__ = o.__dict__
        else:
            self._name = name
            self._value = MISSING
            self._default = default
            _MAPPING[name] = self
        pass

    @property
    def name(self):
        return self._name

    def set(self, value: T) -> T:
        old, self._value = self._value, value
        return old

    def get(self, default: T = MISSING) -> T:
        adefault = default or self._default
        if self._value is MISSING and adefault is MISSING:
            raise Exception("Missing default")
        return self._value or adefault

    def reset(self):
        self._value = None

    def __repr__(self) -> str:
        return f"<class {type(self).__name__}  name={self.name} value={type(self._value)} >"
