from __future__ import annotations
import re
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Collection,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
    overload,
)
import discord.abc
import discord.utils
from discord.message import Message
from discord.utils import MISSING
from ._types import BotT
if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeGuard
    from discord.abc import MessageableChannel
    from discord.commands import MessageCommand
    from discord.file import _FileBase
    from discord.guild import Guild
    from discord.member import Member
    from discord.mentions import AllowedMentions
    from discord.message import MessageReference, PartialMessage
    from discord.state import ConnectionState
    from discord.sticker import GuildSticker, StickerItem
    from discord.user import ClientUser, User
    from discord.voice_client import VoiceProtocol
    from .cog import Cog
    from .core import Command
    from .parameters import Parameter
    from .view import StringView
__all__ = (
    'Context',
)
T = TypeVar('T')
CogT = TypeVar('CogT', bound="Cog")
if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')
def is_cog(obj: Any) -> TypeGuard[Cog]:
    return hasattr(obj, '__cog_commands__')
class Context(discord.abc.Messageable, Generic[BotT]):
    r
    def __init__(
        self,
        *,
        message: Message,
        bot: BotT,
        view: StringView,
        args: List[Any] = MISSING,
        kwargs: Dict[str, Any] = MISSING,
        prefix: Optional[str] = None,
        command: Optional[Command[Any, ..., Any]] = None,
        invoked_with: Optional[str] = None,
        invoked_parents: List[str] = MISSING,
        invoked_subcommand: Optional[Command[Any, ..., Any]] = None,
        subcommand_passed: Optional[str] = None,
        command_failed: bool = False,
        current_parameter: Optional[Parameter] = None,
        current_argument: Optional[str] = None,
    ):
        self.message: Message = message
        self.bot: BotT = bot
        self.args: List[Any] = args or []
        self.kwargs: Dict[str, Any] = kwargs or {}
        self.prefix: Optional[str] = prefix
        self.command: Optional[Command[Any, ..., Any]] = command
        self.view: StringView = view
        self.invoked_with: Optional[str] = invoked_with
        self.invoked_parents: List[str] = invoked_parents or []
        self.invoked_subcommand: Optional[Command[Any, ..., Any]] = invoked_subcommand
        self.subcommand_passed: Optional[str] = subcommand_passed
        self.command_failed: bool = command_failed
        self.current_parameter: Optional[Parameter] = current_parameter
        self.current_argument: Optional[str] = current_argument
        self.state: ConnectionState = self.message.state
    async def invoke(self, command: Command[CogT, P, T], /, *args: P.args, **kwargs: P.kwargs) -> T:
        r
        return await command(self, *args, **kwargs)
    async def reinvoke(self, *, call_hooks: bool = False, restart: bool = True) -> None:
        cmd = self.command
        view = self.view
        if cmd is None:
            raise ValueError('This context is not valid.')
        index, previous = view.index, view.previous
        invoked_with = self.invoked_with
        invoked_subcommand = self.invoked_subcommand
        invoked_parents = self.invoked_parents
        subcommand_passed = self.subcommand_passed
        if restart:
            to_call = cmd.root_parent or cmd
            view.index = len(self.prefix or '')
            view.previous = 0
            self.invoked_parents = []
            self.invoked_with = view.get_word()
        else:
            to_call = cmd
        try:
            await to_call.reinvoke(self, call_hooks=call_hooks)
        finally:
            self.command = cmd
            view.index = index
            view.previous = previous
            self.invoked_with = invoked_with
            self.invoked_subcommand = invoked_subcommand
            self.invoked_parents = invoked_parents
            self.subcommand_passed = subcommand_passed
    @property
    def valid(self) -> bool:
        return self.prefix is not None and self.command is not None
    async def _get_channel(self) -> discord.abc.Messageable:
        return self.channel
    @property
    def clean_prefix(self) -> str:
        if self.prefix is None:
            return ''
        user = self.me
        pattern = re.compile(r"<@!?%s>" % user.id)
        return pattern.sub("@%s" % user.display_name.replace('\\', r'\\'), self.prefix)
    @property
    def cog(self) -> Optional[Cog]:
        if self.command is None:
            return None
        return self.command.cog
    @property
    def filesize_limit(self) -> int:
        return self.guild.filesize_limit if self.guild is not None else discord.utils.DEFAULT_FILE_SIZE_LIMIT_BYTES
    @discord.utils.cached_property
    def guild(self) -> Optional[Guild]:
        return self.message.guild
    @discord.utils.cached_property
    def channel(self) -> MessageableChannel:
        return self.message.channel
    @discord.utils.cached_property
    def author(self) -> Union[User, Member]:
        return self.message.author
    @discord.utils.cached_property
    def me(self) -> Union[Member, ClientUser]:
        return self.guild.me if self.guild is not None else self.bot.user
    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        r
        g = self.guild
        return g.voice_client if g else None
    async def send_help(self, *args: Any) -> Any:
        from .core import Command, Group, wrap_callback
        from .errors import CommandError
        bot = self.bot
        cmd = bot.help_command
        if cmd is None:
            return None
        cmd = cmd.copy()
        cmd.context = self
        if len(args) == 0:
            await cmd.prepare_help_command(self, None)
            mapping = cmd.get_bot_mapping()
            injected = wrap_callback(cmd.send_bot_help)
            try:
                return await injected(mapping)
            except CommandError as e:
                await cmd.on_help_command_error(self, e)
                return None
        entity = args[0]
        if isinstance(entity, str):
            entity = bot.get_cog(entity) or bot.get_command(entity)
        if entity is None:
            return None
        try:
            entity.qualified_name
        except AttributeError:
            return None
        await cmd.prepare_help_command(self, entity.qualified_name)
        try:
            if is_cog(entity):
                injected = wrap_callback(cmd.send_cog_help)
                return await injected(entity)
            elif isinstance(entity, Group):
                injected = wrap_callback(cmd.send_group_help)
                return await injected(entity)
            elif isinstance(entity, Command):
                injected = wrap_callback(cmd.send_command_help)
                return await injected(entity)
            else:
                return None
        except CommandError as e:
            await cmd.on_help_command_error(self, e)
    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: _FileBase = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[_FileBase] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: _FileBase = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[_FileBase] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    @discord.utils.copy_doc(Message.reply)
    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        return await self.message.reply(content, **kwargs)
    @discord.utils.deprecated("Context.application_commands")
    @discord.utils.copy_doc(Message.message_commands)
    def message_commands(
        self,
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        command_ids: Optional[Collection[int]] = None,
        application: Optional[discord.abc.Snowflake] = None,
        with_applications: bool = True,
    ) -> AsyncIterator[MessageCommand]:
        return self.message.message_commands(
            query, limit=limit, command_ids=command_ids, with_applications=with_applications, application=application
        )