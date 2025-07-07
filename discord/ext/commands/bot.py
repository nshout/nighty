from __future__ import annotations
import asyncio
import collections
import collections.abc
import inspect
import importlib.util
import sys
import logging
import types
from typing import (
    Any,
    Callable,
    Mapping,
    List,
    Dict,
    TYPE_CHECKING,
    Optional,
    TypeVar,
    Type,
    Union,
    Iterable,
    Collection,
    overload,
)
import discord
from discord.utils import MISSING, _is_submodule
from .core import GroupMixin
from .view import StringView
from .context import Context
from . import errors
from .help import HelpCommand, DefaultHelpCommand
from .cog import Cog
if TYPE_CHECKING:
    from typing_extensions import Self
    import importlib.machinery
    from discord.message import Message
    from discord.abc import User
    from ._types import (
        _Bot,
        BotT,
        UserCheck,
        CoroFunc,
        ContextT,
        MaybeAwaitableFunc,
    )
    _Prefix = Union[Iterable[str], str]
    _PrefixCallable = MaybeAwaitableFunc[[BotT, Message], _Prefix]
    PrefixType = Union[_Prefix, _PrefixCallable[BotT]]
__all__ = (
    'when_mentioned',
    'when_mentioned_or',
    'Bot',
)
T = TypeVar('T')
CFT = TypeVar('CFT', bound='CoroFunc')
_log = logging.getLogger(__name__)
def when_mentioned(bot: _Bot, msg: Message, /) -> List[str]:
    return [f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']
def when_mentioned_or(*prefixes: str) -> Callable[[_Bot, Message], List[str]]:
    def inner(bot, msg):
        r = list(prefixes)
        r = when_mentioned(bot, msg) + r
        return r
    return inner
class _DefaultRepr:
    def __repr__(self):
        return '<default-help-command>'
_default: Any = _DefaultRepr()
class BotBase(GroupMixin[None]):
    def __init__(
        self,
        command_prefix: PrefixType[BotT],
        help_command: Optional[HelpCommand] = _default,
        description: Optional[str] = None,
        **options: Any,
    ) -> None:
        super().__init__(**options)
        self.command_prefix: PrefixType[BotT] = command_prefix
        self.extra_events: Dict[str, List[CoroFunc]] = {}
        self.__cogs: Dict[str, Cog] = {}
        self.__extensions: Dict[str, types.ModuleType] = {}
        self._checks: List[UserCheck] = []
        self._check_once: List[UserCheck] = []
        self._before_invoke: Optional[CoroFunc] = None
        self._after_invoke: Optional[CoroFunc] = None
        self._help_command: Optional[HelpCommand] = None
        self.description: str = inspect.cleandoc(description) if description else ''
        self.owner_id: Optional[int] = options.get('owner_id')
        self.owner_ids: Optional[Collection[int]] = options.get('owner_ids', set())
        self.strip_after_prefix: bool = options.get('strip_after_prefix', False)
        if self.owner_id and self.owner_ids:
            raise TypeError('Both owner_id and owner_ids are set')
        if self.owner_ids and not isinstance(self.owner_ids, collections.abc.Collection):
            raise TypeError(f'owner_ids must be a collection not {self.owner_ids.__class__!r}')
        self_bot = options.get('self_bot', False)
        user_bot = options.get('user_bot', False)
        if self_bot and user_bot:
            raise TypeError('Both self_bot and user_bot are set')
        self._skip_check = lambda x, y: x != y
        if help_command is _default:
            self.help_command = DefaultHelpCommand()
        else:
            self.help_command = help_command
    def dispatch(self, event_name: str, /, *args: Any, **kwargs: Any) -> None:
        super().dispatch(event_name, *args, **kwargs)
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            self._schedule_event(event, ev, *args, **kwargs)
    @discord.utils.copy_doc(discord.Client.close)
    async def close(self) -> None:
        for extension in tuple(self.__extensions):
            try:
                await self.unload_extension(extension)
            except Exception:
                pass
        for cog in tuple(self.__cogs):
            try:
                await self.remove_cog(cog)
            except Exception:
                pass
        await super().close()
    async def on_command_error(self, context: Context[BotT], exception: errors.CommandError, /) -> None:
        if self.extra_events.get('on_command_error', None):
            return
        command = context.command
        if command and command.has_error_handler():
            return
        cog = context.cog
        if cog and cog.has_error_handler():
            return
        _log.error('Ignoring exception in command %s', command, exc_info=exception)
    def check(self, func: T, /) -> T:
        r
        self.add_check(func)
        return func
    def add_check(self, func: UserCheck[ContextT], /, *, call_once: bool = False) -> None:
        if call_once:
            self._check_once.append(func)
        else:
            self._checks.append(func)
    def remove_check(self, func: UserCheck[ContextT], /, *, call_once: bool = False) -> None:
        l = self._check_once if call_once else self._checks
        try:
            l.remove(func)
        except ValueError:
            pass
    def check_once(self, func: CFT, /) -> CFT:
        r
        self.add_check(func, call_once=True)
        return func
    async def can_run(self, ctx: Context[BotT], /, *, call_once: bool = False) -> bool:
        data = self._check_once if call_once else self._checks
        if len(data) == 0:
            return True
        return await discord.utils.async_all(f(ctx) for f in data)
    async def is_owner(self, user: User, /) -> bool:
        if self.owner_id:
            return user.id == self.owner_id
        elif self.owner_ids:
            return user.id in self.owner_ids
        else:
            raise AttributeError('Owners aren\'t set.')
    def before_invoke(self, coro: CFT, /) -> CFT:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The pre-invoke hook must be a coroutine.')
        self._before_invoke = coro
        return coro
    def after_invoke(self, coro: CFT, /) -> CFT:
        r
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The post-invoke hook must be a coroutine.')
        self._after_invoke = coro
        return coro
    def add_listener(self, func: CoroFunc, /, name: str = MISSING) -> None:
        name = func.__name__ if name is MISSING else name
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Listeners must be coroutines')
        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]
    def remove_listener(self, func: CoroFunc, /, name: str = MISSING) -> None:
        name = func.__name__ if name is MISSING else name
        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass
    def listen(self, name: str = MISSING) -> Callable[[CFT], CFT]:
        def decorator(func: CFT) -> CFT:
            self.add_listener(func, name)
            return func
        return decorator
    async def add_cog(
        self,
        cog: Cog,
        /,
        *,
        override: bool = False,
    ) -> None:
        if not isinstance(cog, Cog):
            raise TypeError('cogs must derive from Cog')
        cog_name = cog.__cog_name__
        existing = self.__cogs.get(cog_name)
        if existing is not None:
            if not override:
                raise discord.ClientException(f'Cog named {cog_name!r} already loaded')
            await self.remove_cog(cog_name)
        cog = await cog._inject(self, override=override)
        self.__cogs[cog_name] = cog
    def get_cog(self, name: str, /) -> Optional[Cog]:
        return self.__cogs.get(name)
    async def remove_cog(
        self,
        name: str,
        /,
    ) -> Optional[Cog]:
        cog = self.__cogs.pop(name, None)
        if cog is None:
            return
        help_command = self._help_command
        if help_command and help_command.cog is cog:
            help_command.cog = None
        await cog._eject(self)
        return cog
    @property
    def cogs(self) -> Mapping[str, Cog]:
        return types.MappingProxyType(self.__cogs)
    async def _remove_module_references(self, name: str) -> None:
        for cogname, cog in self.__cogs.copy().items():
            if _is_submodule(name, cog.__module__):
                await self.remove_cog(cogname)
        for cmd in self.all_commands.copy().values():
            if cmd.module is not None and _is_submodule(name, cmd.module):
                if isinstance(cmd, GroupMixin):
                    cmd.recursively_remove_all_commands()
                self.remove_command(cmd.name)
        for event_list in self.extra_events.copy().values():
            remove = []
            for index, event in enumerate(event_list):
                if event.__module__ is not None and _is_submodule(name, event.__module__):
                    remove.append(index)
            for index in reversed(remove):
                del event_list[index]
    async def _call_module_finalizers(self, lib: types.ModuleType, key: str) -> None:
        try:
            func = getattr(lib, 'teardown')
        except AttributeError:
            pass
        else:
            try:
                await func(self)
            except Exception:
                pass
        finally:
            self.__extensions.pop(key, None)
            sys.modules.pop(key, None)
            name = lib.__name__
            for module in list(sys.modules.keys()):
                if _is_submodule(name, module):
                    del sys.modules[module]
    async def _load_from_module_spec(self, spec: importlib.machinery.ModuleSpec, key: str) -> None:
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e
        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)
        try:
            await setup(self)
        except Exception as e:
            del sys.modules[key]
            await self._remove_module_references(lib.__name__)
            await self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
        else:
            self.__extensions[key] = lib
    def _resolve_name(self, name: str, package: Optional[str]) -> str:
        try:
            return importlib.util.resolve_name(name, package)
        except ImportError:
            raise errors.ExtensionNotFound(name)
    async def load_extension(self, name: str, *, package: Optional[str] = None) -> None:
        name = self._resolve_name(name, package)
        if name in self.__extensions:
            raise errors.ExtensionAlreadyLoaded(name)
        spec = importlib.util.find_spec(name)
        if spec is None:
            raise errors.ExtensionNotFound(name)
        await self._load_from_module_spec(spec, name)
    async def unload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)
        await self._remove_module_references(lib.__name__)
        await self._call_module_finalizers(lib, name)
    async def reload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)
        modules = {
            name: module
            for name, module in sys.modules.items()
            if _is_submodule(lib.__name__, name)
        }
        try:
            await self._remove_module_references(lib.__name__)
            await self._call_module_finalizers(lib, name)
            await self.load_extension(name)
        except Exception:
            await lib.setup(self)
            self.__extensions[name] = lib
            sys.modules.update(modules)
            raise
    @property
    def extensions(self) -> Mapping[str, types.ModuleType]:
        return types.MappingProxyType(self.__extensions)
    @property
    def help_command(self) -> Optional[HelpCommand]:
        return self._help_command
    @help_command.setter
    def help_command(self, value: Optional[HelpCommand]) -> None:
        if value is not None:
            if not isinstance(value, HelpCommand):
                raise TypeError('help_command must be a subclass of HelpCommand')
            if self._help_command is not None:
                self._help_command._remove_from_bot(self)
            self._help_command = value
            value._add_to_bot(self)
        elif self._help_command is not None:
            self._help_command._remove_from_bot(self)
            self._help_command = None
        else:
            self._help_command = None
    async def get_prefix(self, message: Message, /) -> Union[List[str], str]:
        prefix = ret = self.command_prefix
        if callable(prefix):
            ret = await discord.utils.maybe_coroutine(prefix, self, message)
        if not isinstance(ret, str):
            try:
                ret = list(ret)
            except TypeError:
                if isinstance(ret, collections.abc.Iterable):
                    raise
                raise TypeError(
                    "command_prefix must be plain string, iterable of strings, or callable "
                    f"returning either of these, not {ret.__class__.__name__}"
                )
        return ret
    @overload
    async def get_context(
        self,
        message: Message,
        /,
    ) -> Context[Self]:
        ...
    @overload
    async def get_context(
        self,
        message: Message,
        /,
        *,
        cls: Type[ContextT] = ...,
    ) -> ContextT:
        ...
    async def get_context(
        self,
        message: Message,
        /,
        *,
        cls: Type[ContextT] = MISSING,
    ) -> Any:
        r
        if cls is MISSING:
            cls = Context
        view = StringView(message.content)
        ctx = cls(prefix=None, view=view, bot=self, message=message)
        prefix = await self.get_prefix(message)
        invoked_prefix = prefix
        if isinstance(prefix, str):
            if not view.skip_string(prefix):
                return ctx
        else:
            try:
                if message.content.startswith(tuple(prefix)):
                    invoked_prefix = discord.utils.find(view.skip_string, prefix)
                else:
                    return ctx
            except TypeError:
                if not isinstance(prefix, list):
                    raise TypeError(
                        "get_prefix must return either a string or a list of string, " f"not {prefix.__class__.__name__}"
                    )
                for value in prefix:
                    if not isinstance(value, str):
                        raise TypeError(
                            "Iterable command_prefix or list returned from get_prefix must "
                            f"contain only strings, not {value.__class__.__name__}"
                        )
                raise
        if self.strip_after_prefix:
            view.skip_ws()
        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.prefix = invoked_prefix
        ctx.command = self.all_commands.get(invoker)
        return ctx
    async def invoke(self, ctx: Context[BotT], /) -> None:
        if ctx.command is not None:
            self.dispatch('command', ctx)
            try:
                if await self.can_run(ctx, call_once=True):
                    await ctx.command.invoke(ctx)
                else:
                    raise errors.CheckFailure('The global check once functions failed.')
            except errors.CommandError as exc:
                await ctx.command.dispatch_error(ctx, exc)
            else:
                self.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc = errors.CommandNotFound(f'Command "{ctx.invoked_with}" is not found')
            self.dispatch('command_error', ctx, exc)
    async def process_commands(self, message: Message, /) -> None:
        if message.author.bot:
            return
        ctx = await self.get_context(message)
        await self.invoke(ctx)
    async def on_message(self, message: Message, /) -> None:
        await self.process_commands(message)
class Bot(BotBase, discord.Client):
    pass