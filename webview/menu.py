from __future__ import annotations
from collections.abc import Callable
class Menu:
    def __init__(self, title: str, items: list[str] = []) -> None:
        self.title = title
        self.items = items
class MenuAction:
    def __init__(self, title: str, function: Callable[[], None]) -> None:
        self.title = title
        self.function = function
class MenuSeparator:
    pass