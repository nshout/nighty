from typing import Any, Awaitable, Callable, Coroutine, TYPE_CHECKING, Protocol, TypeVar, Union, Tuple, Optional
T = TypeVar('T')
if TYPE_CHECKING:
    from typing_extensions import ParamSpec
    from .bot import Bot
    from .context import Context
    from .cog import Cog
    from .errors import CommandError
    _Bot = Bot
    P = ParamSpec('P')
    MaybeAwaitableFunc = Callable[P, 'MaybeAwaitable[T]']
else:
    _Bot = 'Bot'
    P = TypeVar('P')
    MaybeAwaitableFunc = Tuple[P, T]
Coro = Coroutine[Any, Any, T]
CoroFunc = Callable[..., Coro[Any]]
MaybeCoro = Union[T, Coro[T]]
MaybeAwaitable = Union[T, Awaitable[T]]
CogT = TypeVar('CogT', bound='Optional[Cog]')
UserCheck = Callable[["ContextT"], MaybeCoro[bool]]
Hook = Union[Callable[["CogT", "ContextT"], Coro[Any]], Callable[["ContextT"], Coro[Any]]]
Error = Union[Callable[["CogT", "ContextT", "CommandError"], Coro[Any]], Callable[["ContextT", "CommandError"], Coro[Any]]]
ContextT = TypeVar('ContextT', bound='Context[Any]')
BotT = TypeVar('BotT', bound=_Bot, covariant=True)
ContextT_co = TypeVar('ContextT_co', bound='Context[Any]', covariant=True)
class Check(Protocol[ContextT_co]):
    predicate: Callable[[ContextT_co], Coroutine[Any, Any, bool]]
    def __call__(self, coro_or_commands: T) -> T:
        ...
class _BaseCommand:
    __slots__ = ()