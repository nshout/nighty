from __future__ import annotations
import inspect
from discord.utils import maybe_coroutine, MISSING
from typing import Any, Callable, Dict, Generator, List, Optional, TYPE_CHECKING, Tuple, TypeVar
from ._types import _BaseCommand, BotT
if TYPE_CHECKING:
    from typing_extensions import Self
    from .bot import BotBase
    from .context import Context
    from .core import Command
__all__ = (
    'CogMeta',
    'Cog',
)
FuncT = TypeVar('FuncT', bound=Callable[..., Any])
class CogMeta(type):
    __cog_name__: str
    __cog_settings__: Dict[str, Any]
    __cog_commands__: List[Command[Any, ..., Any]]
    __cog_listeners__: List[Tuple[str, str]]
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        name, bases, attrs = args
        attrs['__cog_name__'] = kwargs.get('name', name)
        attrs['__cog_settings__'] = kwargs.pop('command_attrs', {})
        description = kwargs.get('description', None)
        if description is None:
            description = inspect.cleandoc(attrs.get('__doc__', ''))
        attrs['__cog_description__'] = description
        kwargs.pop('name', None)
        kwargs.pop('description', None)
        commands = {}
        listeners = {}
        no_bot_cog = 'Commands or listeners must not start with cog_ or bot_ (in method {0.__name__}.{1})'
        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in commands:
                    del commands[elem]
                if elem in listeners:
                    del listeners[elem]
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, _BaseCommand):
                    if is_static_method:
                        raise TypeError(f'Command in method {base}.{elem!r} must not be staticmethod.')
                    if elem.startswith(('cog_', 'bot_')):
                        raise TypeError(no_bot_cog.format(base, elem))
                    commands[elem] = value
                elif inspect.iscoroutinefunction(value):
                    try:
                        getattr(value, '__cog_listener__')
                    except AttributeError:
                        continue
                    else:
                        if elem.startswith(('cog_', 'bot_')):
                            raise TypeError(no_bot_cog.format(base, elem))
                        listeners[elem] = value
        new_cls.__cog_commands__ = list(commands.values())
        listeners_as_list = []
        for listener in listeners.values():
            for listener_name in listener.__cog_listener_names__:
                listeners_as_list.append((listener_name, listener.__name__))
        new_cls.__cog_listeners__ = listeners_as_list
        return new_cls
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)
    @classmethod
    def qualified_name(cls) -> str:
        return cls.__cog_name__
def _cog_special_method(func: FuncT) -> FuncT:
    func.__cog_special_method__ = None
    return func
class Cog(metaclass=CogMeta):
    __cog_name__: str
    __cog_settings__: Dict[str, Any]
    __cog_commands__: List[Command[Self, ..., Any]]
    __cog_listeners__: List[Tuple[str, str]]
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        self = super().__new__(cls)
        cmd_attrs = cls.__cog_settings__
        self.__cog_commands__ = tuple(c._update_copy(cmd_attrs) for c in cls.__cog_commands__)
        lookup = {cmd.qualified_name: cmd for cmd in self.__cog_commands__}
        for command in self.__cog_commands__:
            setattr(self, command.callback.__name__, command)
            parent = command.parent
            if parent is not None:
                parent = lookup[parent.qualified_name]
                parent.remove_command(command.name)
                parent.add_command(command)
        return self
    def get_commands(self) -> List[Command[Self, ..., Any]]:
        r
        return [c for c in self.__cog_commands__ if c.parent is None]
    @property
    def qualified_name(self) -> str:
        return self.__cog_name__
    @property
    def description(self) -> str:
        return self.__cog_description__
    @description.setter
    def description(self, description: str) -> None:
        self.__cog_description__ = description
    def walk_commands(self) -> Generator[Command[Self, ..., Any], None, None]:
        from .core import GroupMixin
        for command in self.__cog_commands__:
            if command.parent is None:
                yield command
                if isinstance(command, GroupMixin):
                    yield from command.walk_commands()
    def get_listeners(self) -> List[Tuple[str, Callable[..., Any]]]:
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]
    @classmethod
    def _get_overridden_method(cls, method: FuncT) -> Optional[FuncT]:
        return getattr(method.__func__, '__cog_special_method__', method)
    @classmethod
    def listener(cls, name: str = MISSING) -> Callable[[FuncT], FuncT]:
        if name is not MISSING and not isinstance(name, str):
            raise TypeError(f'Cog.listener expected str but received {name.__class__.__name__!r} instead.')
        def decorator(func: FuncT) -> FuncT:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('Listener function must be a coroutine function.')
            actual.__cog_listener__ = True
            to_assign = name or actual.__name__
            try:
                actual.__cog_listener_names__.append(to_assign)
            except AttributeError:
                actual.__cog_listener_names__ = [to_assign]
            return func
        return decorator
    def has_error_handler(self) -> bool:
        return not hasattr(self.cog_command_error.__func__, '__cog_special_method__')
    @_cog_special_method
    async def cog_load(self) -> None:
        pass
    @_cog_special_method
    async def cog_unload(self) -> None:
        pass
    @_cog_special_method
    def bot_check_once(self, ctx: Context[BotT]) -> bool:
        return True
    @_cog_special_method
    def bot_check(self, ctx: Context[BotT]) -> bool:
        return True
    @_cog_special_method
    def cog_check(self, ctx: Context[BotT]) -> bool:
        return True
    @_cog_special_method
    async def cog_command_error(self, ctx: Context[BotT], error: Exception) -> None:
        pass
    @_cog_special_method
    async def cog_before_invoke(self, ctx: Context[BotT]) -> None:
        pass
    @_cog_special_method
    async def cog_after_invoke(self, ctx: Context[BotT]) -> None:
        pass
    async def _inject(self, bot: BotBase, override: bool) -> Self:
        cls = self.__class__
        await maybe_coroutine(self.cog_load)
        for index, command in enumerate(self.__cog_commands__):
            command.cog = self
            if command.parent is None:
                try:
                    bot.add_command(command)
                except Exception as e:
                    for to_undo in self.__cog_commands__[:index]:
                        if to_undo.parent is None:
                            bot.remove_command(to_undo.name)
                    try:
                        await maybe_coroutine(self.cog_unload)
                    finally:
                        raise e
        if cls.bot_check is not Cog.bot_check:
            bot.add_check(self.bot_check)
        if cls.bot_check_once is not Cog.bot_check_once:
            bot.add_check(self.bot_check_once, call_once=True)
        for name, method_name in self.__cog_listeners__:
            bot.add_listener(getattr(self, method_name), name)
        return self
    async def _eject(self, bot: BotBase) -> None:
        cls = self.__class__
        try:
            for command in self.__cog_commands__:
                if command.parent is None:
                    bot.remove_command(command.name)
            for name, method_name in self.__cog_listeners__:
                bot.remove_listener(getattr(self, method_name), name)
            if cls.bot_check is not Cog.bot_check:
                bot.remove_check(self.bot_check)
            if cls.bot_check_once is not Cog.bot_check_once:
                bot.remove_check(self.bot_check_once, call_once=True)
        finally:
            try:
                await maybe_coroutine(self.cog_unload)
            except Exception:
                pass