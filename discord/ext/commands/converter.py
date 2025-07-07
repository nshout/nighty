from __future__ import annotations
import inspect
import re
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    overload,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
)
import types
import discord
from .errors import *
if TYPE_CHECKING:
    from discord.state import Channel
    from discord.threads import Thread
    from .parameters import Parameter
    from ._types import BotT, _Bot
    from .context import Context
__all__ = (
    'Converter',
    'ObjectConverter',
    'MemberConverter',
    'UserConverter',
    'MessageConverter',
    'PartialMessageConverter',
    'TextChannelConverter',
    'InviteConverter',
    'GuildConverter',
    'RoleConverter',
    'GameConverter',
    'ColourConverter',
    'ColorConverter',
    'VoiceChannelConverter',
    'StageChannelConverter',
    'EmojiConverter',
    'PartialEmojiConverter',
    'CategoryChannelConverter',
    'ForumChannelConverter',
    'IDConverter',
    'ThreadConverter',
    'GuildChannelConverter',
    'GuildStickerConverter',
    'ScheduledEventConverter',
    'clean_content',
    'Greedy',
    'Range',
    'run_converters',
)
def _get_from_guilds(bot: _Bot, getter: str, argument: Any) -> Any:
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result
_utils_get = discord.utils.get
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
CT = TypeVar('CT', bound=discord.abc.GuildChannel)
TT = TypeVar('TT', bound=discord.Thread)
@runtime_checkable
class Converter(Protocol[T_co]):
    async def convert(self, ctx: Context[BotT], argument: str) -> T_co:
        raise NotImplementedError('Derived classes need to implement this.')
_ID_REGEX = re.compile(r'([0-9]{15,20})$')
class IDConverter(Converter[T_co]):
    @staticmethod
    def _get_id_match(argument):
        return _ID_REGEX.match(argument)
class ObjectConverter(IDConverter[discord.Object]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Object:
        match = self._get_id_match(argument) or re.match(r'<(?:@(?:!|&)?|
        if match is None:
            raise ObjectNotFound(argument)
        result = int(match.group(1))
        return discord.Object(id=result)
class MemberConverter(IDConverter[discord.Member]):
    async def query_member_named(self, guild: discord.Guild, argument: str) -> Optional[discord.Member]:
        cache = guild.state.member_cache_flags.joined
        username, _, discriminator = argument.rpartition('
        if not username:
            discriminator, username = username, discriminator
        if discriminator == '0' or (len(discriminator) == 4 and discriminator.isdigit()):
            lookup = username
            predicate = lambda m: m.name == username and m.discriminator == discriminator
        else:
            lookup = argument
            predicate = lambda m: m.name == argument or m.global_name == argument or m.nick == argument
        members = await guild.query_members(lookup, limit=100, cache=cache)
        return discord.utils.find(predicate, members)
    async def query_member_by_id(self, bot, guild, user_id):
        ws = bot.ws
        cache = guild.state.member_cache_flags.joined
        if ws.is_ratelimited():
            try:
                member = await guild.fetch_member(user_id)
            except discord.HTTPException:
                return None
            if cache:
                guild._add_member(member)
            return member
        members = await guild.query_members(limit=1, user_ids=[user_id], cache=cache)
        if not members:
            return None
        return members[0]
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Member:
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]{15,20})>$', argument)
        guild = ctx.guild
        result = None
        user_id = None
        if match is None:
            if guild:
                result = guild.get_member_named(argument)
            else:
                result = _get_from_guilds(bot, 'get_member_named', argument)
        else:
            user_id = int(match.group(1))
            if guild:
                result = guild.get_member(user_id) or _utils_get(ctx.message.mentions, id=user_id)
            else:
                result = _get_from_guilds(bot, 'get_member', user_id)
        if not isinstance(result, discord.Member):
            if guild is None:
                raise MemberNotFound(argument)
            if user_id is not None:
                result = await self.query_member_by_id(bot, guild, user_id)
            else:
                result = await self.query_member_named(guild, argument)
            if not result:
                raise MemberNotFound(argument)
        return result
class UserConverter(IDConverter[discord.User]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.User:
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]{15,20})>$', argument)
        result = None
        state = ctx.state
        if match is not None:
            user_id = int(match.group(1))
            result = ctx.bot.get_user(user_id) or _utils_get(ctx.message.mentions, id=user_id)
            if result is None:
                try:
                    result = await ctx.bot.fetch_user(user_id)
                except discord.HTTPException:
                    raise UserNotFound(argument) from None
            return result
        username, _, discriminator = argument.rpartition('
        if not username:
            discriminator, username = username, discriminator
        if discriminator == '0' or (len(discriminator) == 4 and discriminator.isdigit()):
            predicate = lambda u: u.name == username and u.discriminator == discriminator
        else:
            predicate = lambda u: u.name == argument or u.global_name == argument
        result = discord.utils.find(predicate, state._users.values())
        if result is None:
            raise UserNotFound(argument)
        return result
class PartialMessageConverter(Converter[discord.PartialMessage]):
    @staticmethod
    def _get_id_matches(ctx: Context[BotT], argument: str) -> Tuple[Optional[int], int, int]:
        id_regex = re.compile(r'(?:(?P<channel_id>[0-9]{15,20})-)?(?P<message_id>[0-9]{15,20})$')
        link_regex = re.compile(
            r'https?://(?:(ptb|canary|www)\.)?discord(?:app)?\.com/channels/'
            r'(?P<guild_id>[0-9]{15,20}|@me)'
            r'/(?P<channel_id>[0-9]{15,20})/(?P<message_id>[0-9]{15,20})/?$'
        )
        match = id_regex.match(argument) or link_regex.match(argument)
        if not match:
            raise MessageNotFound(argument)
        data = match.groupdict()
        channel_id = discord.utils._get_as_snowflake(data, 'channel_id') or ctx.channel.id
        message_id = int(data['message_id'])
        guild_id = data.get('guild_id')
        if guild_id is None:
            guild_id = ctx.guild and ctx.guild.id
        elif guild_id == '@me':
            guild_id = None
        else:
            guild_id = int(guild_id)
        return guild_id, message_id, channel_id
    @staticmethod
    def _resolve_channel(
        ctx: Context[BotT], guild_id: Optional[int], channel_id: Optional[int]
    ) -> Optional[Union[Channel, Thread]]:
        if channel_id is None:
            return ctx.channel
        if guild_id is not None:
            guild = ctx.bot.get_guild(guild_id)
            if guild is None:
                return None
            return guild._resolve_channel(channel_id)
        return ctx.bot.get_channel(channel_id)
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.PartialMessage:
        guild_id, message_id, channel_id = self._get_id_matches(ctx, argument)
        channel = self._resolve_channel(ctx, guild_id, channel_id)
        if not channel or not isinstance(channel, discord.abc.Messageable):
            raise ChannelNotFound(channel_id)
        return discord.PartialMessage(channel=channel, id=message_id)
class MessageConverter(IDConverter[discord.Message]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Message:
        guild_id, message_id, channel_id = PartialMessageConverter._get_id_matches(ctx, argument)
        message = ctx.bot._connection._get_message(message_id)
        if message:
            return message
        channel = PartialMessageConverter._resolve_channel(ctx, guild_id, channel_id)
        if not channel or not isinstance(channel, discord.abc.Messageable):
            raise ChannelNotFound(channel_id)
        try:
            return await channel.fetch_message(message_id)
        except discord.NotFound:
            raise MessageNotFound(argument)
        except discord.Forbidden:
            raise ChannelNotReadable(channel)
class GuildChannelConverter(IDConverter[discord.abc.GuildChannel]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.abc.GuildChannel:
        return self._resolve_channel(ctx, argument, 'channels', discord.abc.GuildChannel)
    @staticmethod
    def _resolve_channel(ctx: Context[BotT], argument: str, attribute: str, type: Type[CT]) -> CT:
        bot = ctx.bot
        match = IDConverter._get_id_match(argument) or re.match(r'<
        result = None
        guild = ctx.guild
        if match is None:
            if guild:
                iterable: Iterable[CT] = getattr(guild, attribute)
                result: Optional[CT] = discord.utils.get(iterable, name=argument)
            else:
                def check(c):
                    return isinstance(c, type) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)
        if not isinstance(result, type):
            raise ChannelNotFound(argument)
        return result
    @staticmethod
    def _resolve_thread(ctx: Context[BotT], argument: str, attribute: str, type: Type[TT]) -> TT:
        match = IDConverter._get_id_match(argument) or re.match(r'<
        result = None
        guild = ctx.guild
        if match is None:
            if guild:
                iterable: Iterable[TT] = getattr(guild, attribute)
                result: Optional[TT] = discord.utils.get(iterable, name=argument)
        else:
            thread_id = int(match.group(1))
            if guild:
                result = guild.get_thread(thread_id)
        if not result or not isinstance(result, type):
            raise ThreadNotFound(argument)
        return result
class TextChannelConverter(IDConverter[discord.TextChannel]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.TextChannel:
        return GuildChannelConverter._resolve_channel(ctx, argument, 'text_channels', discord.TextChannel)
class VoiceChannelConverter(IDConverter[discord.VoiceChannel]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.VoiceChannel:
        return GuildChannelConverter._resolve_channel(ctx, argument, 'voice_channels', discord.VoiceChannel)
class StageChannelConverter(IDConverter[discord.StageChannel]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.StageChannel:
        return GuildChannelConverter._resolve_channel(ctx, argument, 'stage_channels', discord.StageChannel)
class CategoryChannelConverter(IDConverter[discord.CategoryChannel]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.CategoryChannel:
        return GuildChannelConverter._resolve_channel(ctx, argument, 'categories', discord.CategoryChannel)
class ThreadConverter(IDConverter[discord.Thread]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Thread:
        return GuildChannelConverter._resolve_thread(ctx, argument, 'threads', discord.Thread)
class ForumChannelConverter(IDConverter[discord.ForumChannel]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.ForumChannel:
        return GuildChannelConverter._resolve_channel(ctx, argument, 'forums', discord.ForumChannel)
class ColourConverter(Converter[discord.Colour]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Colour:
        try:
            return discord.Colour.from_str(argument)
        except ValueError:
            arg = argument.lower().replace(' ', '_')
            method = getattr(discord.Colour, arg, None)
            if arg.startswith('from_') or method is None or not inspect.ismethod(method):
                raise BadColourArgument(arg)
            return method()
ColorConverter = ColourConverter
class RoleConverter(IDConverter[discord.Role]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Role:
        guild = ctx.guild
        if not guild:
            raise NoPrivateMessage()
        match = self._get_id_match(argument) or re.match(r'<@&([0-9]{15,20})>$', argument)
        if match:
            result = guild.get_role(int(match.group(1)))
        else:
            result = discord.utils.get(guild._roles.values(), name=argument)
        if result is None:
            raise RoleNotFound(argument)
        return result
class GameConverter(Converter[discord.Game]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Game:
        return discord.Game(name=argument)
class InviteConverter(Converter[discord.Invite]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Invite:
        try:
            invite = await ctx.bot.fetch_invite(argument)
            return invite
        except Exception as exc:
            raise BadInviteArgument(argument) from exc
class GuildConverter(IDConverter[discord.Guild]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Guild:
        match = self._get_id_match(argument)
        result = None
        if match is not None:
            guild_id = int(match.group(1))
            result = ctx.bot.get_guild(guild_id)
        if result is None:
            result = discord.utils.get(ctx.bot.guilds, name=argument)
            if result is None:
                raise GuildNotFound(argument)
        return result
class EmojiConverter(IDConverter[discord.Emoji]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.Emoji:
        match = self._get_id_match(argument) or re.match(r'<a?:[a-zA-Z0-9\_]{1,32}:([0-9]{15,20})>$', argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild
        if match is None:
            if guild:
                result = discord.utils.get(guild.emojis, name=argument)
            if result is None:
                result = discord.utils.get(bot.emojis, name=argument)
        else:
            emoji_id = int(match.group(1))
            result = bot.get_emoji(emoji_id)
        if result is None:
            raise EmojiNotFound(argument)
        return result
class PartialEmojiConverter(Converter[discord.PartialEmoji]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.PartialEmoji:
        match = re.match(r'<(a?):([a-zA-Z0-9\_]{1,32}):([0-9]{15,20})>$', argument)
        if match:
            emoji_animated = bool(match.group(1))
            emoji_name = match.group(2)
            emoji_id = int(match.group(3))
            return discord.PartialEmoji.with_state(
                ctx.bot._connection, animated=emoji_animated, name=emoji_name, id=emoji_id
            )
        raise PartialEmojiConversionFailure(argument)
class GuildStickerConverter(IDConverter[discord.GuildSticker]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.GuildSticker:
        match = self._get_id_match(argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild
        if match is None:
            if guild:
                result = discord.utils.get(guild.stickers, name=argument)
            if result is None:
                result = discord.utils.get(bot.stickers, name=argument)
        else:
            sticker_id = int(match.group(1))
            result = bot.get_sticker(sticker_id)
        if result is None:
            raise GuildStickerNotFound(argument)
        return result
class ScheduledEventConverter(IDConverter[discord.ScheduledEvent]):
    async def convert(self, ctx: Context[BotT], argument: str) -> discord.ScheduledEvent:
        guild = ctx.guild
        match = self._get_id_match(argument)
        result = None
        if match:
            event_id = int(match.group(1))
            if guild:
                result = guild.get_scheduled_event(event_id)
            else:
                for guild in ctx.bot.guilds:
                    result = guild.get_scheduled_event(event_id)
                    if result:
                        break
        else:
            pattern = (
                r'https?://(?:(ptb|canary|www)\.)?discord\.com/events/'
                r'(?P<guild_id>[0-9]{15,20})/'
                r'(?P<event_id>[0-9]{15,20})$'
            )
            match = re.match(pattern, argument, flags=re.I)
            if match:
                guild = ctx.bot.get_guild(int(match.group('guild_id')))
                if guild:
                    event_id = int(match.group('event_id'))
                    result = guild.get_scheduled_event(event_id)
            else:
                if guild:
                    result = discord.utils.get(guild.scheduled_events, name=argument)
                else:
                    for guild in ctx.bot.guilds:
                        result = discord.utils.get(guild.scheduled_events, name=argument)
                        if result:
                            break
        if result is None:
            raise ScheduledEventNotFound(argument)
        return result
class clean_content(Converter[str]):
    def __init__(
        self,
        *,
        fix_channel_mentions: bool = False,
        use_nicknames: bool = True,
        escape_markdown: bool = False,
        remove_markdown: bool = False,
    ) -> None:
        self.fix_channel_mentions = fix_channel_mentions
        self.use_nicknames = use_nicknames
        self.escape_markdown = escape_markdown
        self.remove_markdown = remove_markdown
    async def convert(self, ctx: Context[BotT], argument: str) -> str:
        msg = ctx.message
        if ctx.guild:
            def resolve_member(id: int) -> str:
                m = _utils_get(msg.mentions, id=id) or ctx.guild.get_member(id)
                return f'@{m.display_name if self.use_nicknames else m.name}' if m else '@deleted-user'
            def resolve_role(id: int) -> str:
                r = _utils_get(msg.role_mentions, id=id) or ctx.guild.get_role(id)
                return f'@{r.name}' if r else '@deleted-role'
        else:
            def resolve_member(id: int) -> str:
                m = _utils_get(msg.mentions, id=id) or ctx.bot.get_user(id)
                return f'@{m.display_name}' if m else '@deleted-user'
            def resolve_role(id: int) -> str:
                return '@deleted-role'
        if self.fix_channel_mentions and ctx.guild:
            def resolve_channel(id: int) -> str:
                c = ctx.guild._resolve_channel(id)
                return f'
        else:
            def resolve_channel(id: int) -> str:
                return f'<
        transforms = {
            '@': resolve_member,
            '@!': resolve_member,
            '
            '@&': resolve_role,
        }
        def repl(match: re.Match) -> str:
            type = match[1]
            id = int(match[2])
            transformed = transforms[type](id)
            return transformed
        result = re.sub(r'<(@[!&]?|
        if self.escape_markdown:
            result = discord.utils.escape_markdown(result)
        elif self.remove_markdown:
            result = discord.utils.remove_markdown(result)
        return discord.utils.escape_mentions(result)
class Greedy(List[T]):
    r
    __slots__ = ('converter',)
    def __init__(self, *, converter: T) -> None:
        self.converter: T = converter
    def __repr__(self) -> str:
        converter = getattr(self.converter, '__name__', repr(self.converter))
        return f'Greedy[{converter}]'
    def __class_getitem__(cls, params: Union[Tuple[T], T]) -> Greedy[T]:
        if not isinstance(params, tuple):
            params = (params,)
        if len(params) != 1:
            raise TypeError('Greedy[...] only takes a single argument')
        converter = params[0]
        args = getattr(converter, '__args__', ())
        if discord.utils.PY_310 and converter.__class__ is types.UnionType:
            converter = Union[args]
        origin = getattr(converter, '__origin__', None)
        if not (callable(converter) or isinstance(converter, Converter) or origin is not None):
            raise TypeError('Greedy[...] expects a type or a Converter instance.')
        if converter in (str, type(None)) or origin is Greedy:
            raise TypeError(f'Greedy[{converter.__name__}] is invalid.')
        if origin is Union and type(None) in args:
            raise TypeError(f'Greedy[{converter!r}] is invalid.')
        return cls(converter=converter)
    @property
    def constructed_converter(self) -> Any:
        if (
            inspect.isclass(self.converter)
            and issubclass(self.converter, Converter)
            and not inspect.ismethod(self.converter.convert)
        ):
            return self.converter()
        return self.converter
if TYPE_CHECKING:
    from typing_extensions import Annotated as Range
else:
    class Range:
        def __init__(
            self,
            *,
            annotation: Any,
            min: Optional[Union[int, float]] = None,
            max: Optional[Union[int, float]] = None,
        ) -> None:
            self.annotation: Any = annotation
            self.min: Optional[Union[int, float]] = min
            self.max: Optional[Union[int, float]] = max
        async def convert(self, ctx: Context[BotT], value: str) -> Union[int, float]:
            try:
                count = converted = self.annotation(value)
            except ValueError:
                raise BadArgument(
                    f'Converting to "{self.annotation.__name__}" failed for parameter "{ctx.current_parameter.name}".'
                )
            if self.annotation is str:
                count = len(value)
            if (self.min is not None and count < self.min) or (self.max is not None and count > self.max):
                raise RangeError(converted, minimum=self.min, maximum=self.max)
            return converted
        def __call__(self) -> None:
            pass
        def __or__(self, rhs) -> Any:
            return Union[self, rhs]
        def __repr__(self) -> str:
            return f'{self.__class__.__name__}[{self.annotation.__name__}, {self.min}, {self.max}]'
        def __class_getitem__(cls, obj) -> Range:
            if not isinstance(obj, tuple):
                raise TypeError(f'expected tuple for arguments, received {obj.__class__!r} instead')
            if len(obj) == 2:
                obj = (*obj, None)
            elif len(obj) != 3:
                raise TypeError('Range accepts either two or three arguments with the first being the type of range.')
            annotation, min, max = obj
            if min is None and max is None:
                raise TypeError('Range must not be empty')
            if min is not None and max is not None:
                if type(min) != type(max):
                    raise TypeError('Both min and max in Range must be the same type')
            if annotation not in (int, float, str):
                raise TypeError(f'expected int, float, or str as range type, received {annotation!r} instead')
            if annotation in (str, int):
                cast = int
            else:
                cast = float
            return cls(
                annotation=annotation,
                min=cast(min) if min is not None else None,
                max=cast(max) if max is not None else None,
            )
def _convert_to_bool(argument: str) -> bool:
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    else:
        raise BadBoolArgument(lowered)
_GenericAlias = type(List[T])
def is_generic_type(tp: Any, *, _GenericAlias: type = _GenericAlias) -> bool:
    return isinstance(tp, type) and issubclass(tp, Generic) or isinstance(tp, _GenericAlias)
CONVERTER_MAPPING: Dict[type, Any] = {
    discord.Object: ObjectConverter,
    discord.Member: MemberConverter,
    discord.User: UserConverter,
    discord.Message: MessageConverter,
    discord.PartialMessage: PartialMessageConverter,
    discord.TextChannel: TextChannelConverter,
    discord.Invite: InviteConverter,
    discord.Guild: GuildConverter,
    discord.Role: RoleConverter,
    discord.Game: GameConverter,
    discord.Colour: ColourConverter,
    discord.VoiceChannel: VoiceChannelConverter,
    discord.StageChannel: StageChannelConverter,
    discord.Emoji: EmojiConverter,
    discord.PartialEmoji: PartialEmojiConverter,
    discord.CategoryChannel: CategoryChannelConverter,
    discord.Thread: ThreadConverter,
    discord.abc.GuildChannel: GuildChannelConverter,
    discord.GuildSticker: GuildStickerConverter,
    discord.ScheduledEvent: ScheduledEventConverter,
    discord.ForumChannel: ForumChannelConverter,
}
async def _actual_conversion(ctx: Context[BotT], converter: Any, argument: str, param: inspect.Parameter):
    if converter is bool:
        return _convert_to_bool(argument)
    try:
        module = converter.__module__
    except AttributeError:
        pass
    else:
        if module is not None and (module.startswith('discord.') and not module.endswith('converter')):
            converter = CONVERTER_MAPPING.get(converter, converter)
    try:
        if inspect.isclass(converter) and issubclass(converter, Converter):
            if inspect.ismethod(converter.convert):
                return await converter.convert(ctx, argument)
            else:
                return await converter().convert(ctx, argument)
        elif isinstance(converter, Converter):
            return await converter.convert(ctx, argument)
    except CommandError:
        raise
    except Exception as exc:
        raise ConversionError(converter, exc) from exc
    try:
        return converter(argument)
    except CommandError:
        raise
    except Exception as exc:
        try:
            name = converter.__name__
        except AttributeError:
            name = converter.__class__.__name__
        raise BadArgument(f'Converting to "{name}" failed for parameter "{param.name}".') from exc
@overload
async def run_converters(
    ctx: Context[BotT], converter: Union[Type[Converter[T]], Converter[T]], argument: str, param: Parameter
) -> T:
    ...
@overload
async def run_converters(ctx: Context[BotT], converter: Any, argument: str, param: Parameter) -> Any:
    ...
async def run_converters(ctx: Context[BotT], converter: Any, argument: str, param: Parameter) -> Any:
    origin = getattr(converter, '__origin__', None)
    if origin is Union:
        errors = []
        _NoneType = type(None)
        union_args = converter.__args__
        for conv in union_args:
            if conv is _NoneType and param.kind != param.VAR_POSITIONAL:
                ctx.view.undo()
                return None if param.required else await param.get_default(ctx)
            try:
                value = await run_converters(ctx, conv, argument, param)
            except CommandError as exc:
                errors.append(exc)
            else:
                return value
        raise BadUnionArgument(param, union_args, errors)
    if origin is Literal:
        errors = []
        conversions = {}
        literal_args = converter.__args__
        for literal in literal_args:
            literal_type = type(literal)
            try:
                value = conversions[literal_type]
            except KeyError:
                try:
                    value = await _actual_conversion(ctx, literal_type, argument, param)
                except CommandError as exc:
                    errors.append(exc)
                    conversions[literal_type] = object()
                    continue
                else:
                    conversions[literal_type] = value
            if value == literal:
                return value
        raise BadLiteralArgument(param, literal_args, errors, argument)
    if origin is not None and is_generic_type(converter):
        converter = origin
    return await _actual_conversion(ctx, converter, argument, param)