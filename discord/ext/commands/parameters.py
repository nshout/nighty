from __future__ import annotations
import inspect
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Literal, Optional, OrderedDict, Union, Protocol
from discord.utils import MISSING, maybe_coroutine
from .errors import NoPrivateMessage
from .converter import GuildConverter
from discord import (
    Member,
    User,
    TextChannel,
    VoiceChannel,
    DMChannel,
    Thread,
)
if TYPE_CHECKING:
    from typing_extensions import Self
    from discord import Guild
    from .context import Context
__all__ = (
    'Parameter',
    'parameter',
    'param',
    'Author',
    'CurrentChannel',
    'CurrentGuild',
)
ParamKinds = Union[
    Literal[inspect.Parameter.POSITIONAL_ONLY],
    Literal[inspect.Parameter.POSITIONAL_OR_KEYWORD],
    Literal[inspect.Parameter.VAR_POSITIONAL],
    Literal[inspect.Parameter.KEYWORD_ONLY],
    Literal[inspect.Parameter.VAR_KEYWORD],
]
empty: Any = inspect.Parameter.empty
def _gen_property(name: str) -> property:
    attr = f'_{name}'
    return property(
        attrgetter(attr),
        lambda self, value: setattr(self, attr, value),
        doc=f"The parameter's {name}.",
    )
class Parameter(inspect.Parameter):
    r
    __slots__ = ('_displayed_default', '_description', '_fallback', '_displayed_name')
    def __init__(
        self,
        name: str,
        kind: ParamKinds,
        default: Any = empty,
        annotation: Any = empty,
        description: str = empty,
        displayed_default: str = empty,
        displayed_name: str = empty,
    ) -> None:
        super().__init__(name=name, kind=kind, default=default, annotation=annotation)
        self._name = name
        self._kind = kind
        self._description = description
        self._default = default
        self._annotation = annotation
        self._displayed_default = displayed_default
        self._fallback = False
        self._displayed_name = displayed_name
    def replace(
        self,
        *,
        name: str = MISSING,
        kind: ParamKinds = MISSING,
        default: Any = MISSING,
        annotation: Any = MISSING,
        description: str = MISSING,
        displayed_default: Any = MISSING,
        displayed_name: Any = MISSING,
    ) -> Self:
        if name is MISSING:
            name = self._name
        if kind is MISSING:
            kind = self._kind
        if default is MISSING:
            default = self._default
        if annotation is MISSING:
            annotation = self._annotation
        if description is MISSING:
            description = self._description
        if displayed_default is MISSING:
            displayed_default = self._displayed_default
        if displayed_name is MISSING:
            displayed_name = self._displayed_name
        return self.__class__(
            name=name,
            kind=kind,
            default=default,
            annotation=annotation,
            description=description,
            displayed_default=displayed_default,
            displayed_name=displayed_name,
        )
    if not TYPE_CHECKING:
        name = _gen_property('name')
        kind = _gen_property('kind')
        default = _gen_property('default')
        annotation = _gen_property('annotation')
    @property
    def required(self) -> bool:
        return self.default is empty
    @property
    def converter(self) -> Any:
        if self.annotation is empty:
            return type(self.default) if self.default not in (empty, None) else str
        return self.annotation
    @property
    def description(self) -> Optional[str]:
        return self._description if self._description is not empty else None
    @property
    def displayed_default(self) -> Optional[str]:
        if self._displayed_default is not empty:
            return self._displayed_default
        if self.required:
            return None
        if callable(self.default) or self.default is None:
            return None
        return str(self.default)
    @property
    def displayed_name(self) -> Optional[str]:
        return self._displayed_name if self._displayed_name is not empty else None
    async def get_default(self, ctx: Context[Any]) -> Any:
        if callable(self.default):
            return await maybe_coroutine(self.default, ctx)
        return self.default
def parameter(
    *,
    converter: Any = empty,
    default: Any = empty,
    description: str = empty,
    displayed_default: str = empty,
    displayed_name: str = empty,
) -> Any:
    r
    return Parameter(
        name='empty',
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        annotation=converter,
        default=default,
        description=description,
        displayed_default=displayed_default,
        displayed_name=displayed_name,
    )
class ParameterAlias(Protocol):
    def __call__(
        self,
        *,
        converter: Any = empty,
        default: Any = empty,
        description: str = empty,
        displayed_default: str = empty,
        displayed_name: str = empty,
    ) -> Any:
        ...
param: ParameterAlias = parameter
r
Author = parameter(
    default=attrgetter('author'),
    displayed_default='<you>',
    converter=Union[Member, User],
)
Author._fallback = True
CurrentChannel = parameter(
    default=attrgetter('channel'),
    displayed_default='<this channel>',
    converter=Union[TextChannel, DMChannel, Thread, VoiceChannel],
)
CurrentChannel._fallback = True
def default_guild(ctx: Context[Any]) -> Guild:
    if ctx.guild is not None:
        return ctx.guild
    raise NoPrivateMessage()
CurrentGuild = parameter(
    default=default_guild,
    displayed_default='<this server>',
    converter=GuildConverter,
)
class Signature(inspect.Signature):
    _parameter_cls = Parameter
    parameters: OrderedDict[str, Parameter]