from __future__ import annotations
import time
import random
from typing import Callable, Generic, Literal, TypeVar, overload, Union
T = TypeVar('T', bool, Literal[True], Literal[False])
__all__ = (
    'ExponentialBackoff',
)
class ExponentialBackoff(Generic[T]):
    def __init__(self, base: int = 1, *, integral: T = False):
        self._base: int = base
        self._exp: int = 0
        self._max: int = 10
        self._reset_time: int = base * 2**11
        self._last_invocation: float = time.monotonic()
        rand = random.Random()
        rand.seed()
        self._randfunc: Callable[..., Union[int, float]] = rand.randrange if integral else rand.uniform
    @overload
    def delay(self: ExponentialBackoff[Literal[False]]) -> float:
        ...
    @overload
    def delay(self: ExponentialBackoff[Literal[True]]) -> int:
        ...
    @overload
    def delay(self: ExponentialBackoff[bool]) -> Union[int, float]:
        ...
    def delay(self) -> Union[int, float]:
        invocation = time.monotonic()
        interval = invocation - self._last_invocation
        self._last_invocation = invocation
        if interval > self._reset_time:
            self._exp = 0
        self._exp = min(self._exp + 1, self._max)
        return self._randfunc(0, self._base * 2**self._exp)