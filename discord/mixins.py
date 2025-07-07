__all__ = (
    'EqualityComparable',
    'Hashable',
)
class EqualityComparable:
    __slots__ = ()
    id: int
    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return other.id == self.id
        return NotImplemented
class Hashable(EqualityComparable):
    __slots__ = ()
    def __hash__(self) -> int:
        return self.id >> 22