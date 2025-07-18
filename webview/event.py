from __future__ import annotations
import inspect
import logging
import threading
from typing import Any, Callable
from typing_extensions import Self
logger = logging.getLogger('pywebview')
class Event:
    def __init__(self, should_lock: bool = False) -> None:
        self._items: list[Callable[..., Any]] = []
        self._should_lock = should_lock
        self._event = threading.Event()
    def set(self, *args: Any, **kwargs: Any) -> bool:
        def execute():
            for func in self._items:
                try:
                    try:
                        value = func(*args, **kwargs)
                    except:
                        value = func()
                    return_values.add(value)
                except Exception as e:
                    logger.exception(e)
            if self._should_lock:
                semaphore.release()
        semaphore = threading.Semaphore(0)
        return_values: set[Any] = set()
        if len(self._items):
            t = threading.Thread(target=execute)
            t.start()
            if self._should_lock:
                semaphore.acquire()
        false_values = [v for v in return_values if v is False]
        self._event.set()
        return len(false_values) != 0
    def is_set(self) -> bool:
        return self._event.is_set()
    def wait(self, timeout: float = 0) -> bool:
        return self._event.wait(timeout)
    def clear(self) -> None:
        return self._event.clear()
    def __add__(self, item: Callable[..., Any]) -> Self:
        self._items.append(item)
        return self
    def __sub__(self, item: Callable[..., Any]) -> Self:
        self._items.remove(item)
        return self
    def __iadd__(self, item: Callable[..., Any]) -> Self:
        self._items.append(item)
        return self
    def __isub__(self, item: Callable[..., Any]) -> Self:
        self._items.remove(item)
        return self