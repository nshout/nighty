from __future__ import annotations
from .mixins import Hashable
from .utils import snowflake_time, MISSING
from typing import (
    SupportsInt,
    TYPE_CHECKING,
    Type,
    Union,
)
if TYPE_CHECKING:
    import datetime
    from . import abc
    SupportsIntCast = Union[SupportsInt, str, bytes, bytearray]
__all__ = (
    'Object',
)
class Object(Hashable):
    def __init__(self, id: SupportsIntCast, *, type: Type[abc.Snowflake] = MISSING):
        try:
            id = int(id)
        except ValueError:
            raise TypeError(f'id parameter must be convertible to int not {id.__class__!r}') from None
        self.id: int = id
        self.type: Type[abc.Snowflake] = type or self.__class__
    def __repr__(self) -> str:
        return f'<Object id={self.id!r} type={self.type!r}>'
    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.type):
            return self.id == other.id
        return NotImplemented
    __hash__ = Hashable.__hash__
    @property
    def created_at(self) -> datetime.datetime:
        return snowflake_time(self.id)
OLDEST_OBJECT = Object(id=0)