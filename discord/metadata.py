from __future__ import annotations
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Iterator, Tuple
from .utils import parse_time
if TYPE_CHECKING:
    MetadataObject = Mapping[str, Any]
else:
    MetadataObject = Mapping
__all__ = ('Metadata',)
class Metadata(MetadataObject):
    def __init__(self, *args, **kwargs) -> None:
        data = dict(*args, **kwargs)
        for key, value in data.items():
            key, value = self.__parse(key, value)
            self.__dict__[key] = value
    @staticmethod
    def __parse(key: str, value: Any) -> Tuple[str, Any]:
        if isinstance(value, dict):
            value = Metadata(value)
        elif isinstance(value, list):
            if key.endswith('_ids'):
                try:
                    value = [int(x) for x in value]
                except ValueError:
                    pass
            value = [Metadata(x) if isinstance(x, dict) else x for x in value]
        elif key.endswith('_id') and isinstance(value, str) and value.isdigit():
            value = int(value)
        elif (key.endswith('_at') or key.endswith('_date')) and isinstance(value, str):
            try:
                value = parse_time(value)
            except ValueError:
                pass
        return key, value
    def __repr__(self) -> str:
        if not self.__dict__:
            return '<Metadata>'
        return f'<Metadata {" ".join(f"{k}={v!r}" for k, v in self.__dict__.items())}>'
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Metadata):
            return False
        return self.__dict__ == other.__dict__
    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Metadata):
            return True
        return self.__dict__ != other.__dict__
    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield from self.__dict__.items()
    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]
    def __setitem__(self, key: str, value: Any) -> None:
        key, value = self.__parse(key, value)
        self.__dict__[key] = value
    def __getattr__(self, _) -> Any:
        return None
    def __setattr__(self, key: str, value: Any) -> None:
        key, value = self.__parse(key, value)
        self.__dict__[key] = value
    def __contains__(self, key: str) -> bool:
        return key in self.__dict__
    def __len__(self) -> int:
        return len(self.__dict__)
    def keys(self):
        return self.__dict__.keys()
    def values(self):
        return self.__dict__.values()
    def items(self):
        return self.__dict__.items()