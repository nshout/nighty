from __future__ import annotations
import asyncio
import datetime
import re
import io
from os import PathLike
from typing import (
    AsyncIterator,
    Dict,
    Collection,
    TYPE_CHECKING,
    Sequence,
    Union,
    List,
    Optional,
    Any,
    Callable,
    Tuple,
    ClassVar,
    Type,
    overload,
)
from . import utils
from .reaction import Reaction
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .calls import CallMessage
from .enums import MessageType, ChannelType, ApplicationCommandType, try_enum
from .errors import HTTPException
from .components import _component_factory
from .embeds import Embed
from .member import Member
from .flags import MessageFlags, AttachmentFlags
from .file import File
from .utils import escape_mentions, MISSING
from .http import handle_message_parameters
from .guild import Guild
from .mixins import Hashable
from .sticker import StickerItem, GuildSticker
from .threads import Thread
from .channel import PartialMessageable
from .interactions import Interaction
from .commands import MessageCommand
from .abc import _handle_commands
from .application import IntegrationApplication
if TYPE_CHECKING:
    from typing_extensions import Self
    from .types.message import (
        Message as MessagePayload,
        Attachment as AttachmentPayload,
        BaseApplication as MessageApplicationPayload,
        Call as CallPayload,
        MessageReference as MessageReferencePayload,
        MessageActivity as MessageActivityPayload,
        RoleSubscriptionData as RoleSubscriptionDataPayload,
        MessageSearchResult as MessageSearchResultPayload,
    )
    from .types.interactions import MessageInteraction as MessageInteractionPayload
    from .types.components import MessageActionRow as ComponentPayload
    from .types.threads import ThreadArchiveDuration
    from .types.member import (
        Member as MemberPayload,
        UserWithMember as UserWithMemberPayload,
    )
    from .types.user import User as UserPayload
    from .types.embed import Embed as EmbedPayload
    from .types.gateway import MessageReactionRemoveEvent, MessageUpdateEvent
    from .abc import Snowflake
    from .abc import GuildChannel, MessageableChannel
    from .components import ActionRow
    from .file import _FileBase
    from .state import ConnectionState
    from .mentions import AllowedMentions
    from .sticker import GuildSticker
    from .user import User
    from .role import Role
    EmojiInputType = Union[Emoji, PartialEmoji, str]
__all__ = (
    'Attachment',
    'Message',
    'PartialMessage',
    'MessageReference',
    'DeletedReferencedMessage',
    'RoleSubscriptionInfo',
)
def convert_emoji_reaction(emoji: Union[EmojiInputType, Reaction]) -> str:
    if isinstance(emoji, Reaction):
        emoji = emoji.emoji
    if isinstance(emoji, Emoji):
        return f'{emoji.name}:{emoji.id}'
    if isinstance(emoji, PartialEmoji):
        return emoji._as_reaction()
    if isinstance(emoji, str):
        return emoji.strip('<>')
    raise TypeError(f'emoji argument must be str, Emoji, or Reaction not {emoji.__class__.__name__}.')
class Attachment(Hashable):
    __slots__ = (
        'id',
        'size',
        'height',
        'width',
        'filename',
        'url',
        'proxy_url',
        '_http',
        'content_type',
        'description',
        'ephemeral',
        'duration',
        'waveform',
        '_flags',
    )
    def __init__(self, *, data: AttachmentPayload, state: ConnectionState):
        self.id: int = int(data['id'])
        self.size: int = data['size']
        self.height: Optional[int] = data.get('height')
        self.width: Optional[int] = data.get('width')
        self.filename: str = data['filename']
        self.url: str = data['url']
        self.proxy_url: str = data['proxy_url']
        self._http = state.http
        self.content_type: Optional[str] = data.get('content_type')
        self.description: Optional[str] = data.get('description')
        self.ephemeral: bool = data.get('ephemeral', False)
        self.duration: Optional[float] = data.get('duration_secs')
        waveform = data.get('waveform')
        self.waveform: Optional[bytes] = utils._base64_to_bytes(waveform) if waveform is not None else None
        self._flags: int = data.get('flags', 0)
    @property
    def flags(self) -> AttachmentFlags:
        return AttachmentFlags._from_value(self._flags)
    def is_spoiler(self) -> bool:
        return self.filename.startswith('SPOILER_')
    def is_voice_message(self) -> bool:
        return self.waveform is not None
    def __repr__(self) -> str:
        return f'<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>'
    def __str__(self) -> str:
        return self.url or ''
    async def save(
        self,
        fp: Union[io.BufferedIOBase, PathLike[Any]],
        *,
        seek_begin: bool = True,
        use_cached: bool = False,
    ) -> int:
        data = await self.read(use_cached=use_cached)
        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)
    async def read(self, *, use_cached: bool = False) -> bytes:
        url = self.proxy_url if use_cached else self.url
        data = await self._http.get_from_cdn(url)
        return data
    async def to_file(
        self,
        *,
        filename: Optional[str] = MISSING,
        description: Optional[str] = MISSING,
        use_cached: bool = False,
        spoiler: bool = False,
    ) -> File:
        data = await self.read(use_cached=use_cached)
        file_filename = filename if filename is not MISSING else self.filename
        file_description = description if description is not MISSING else self.description
        return File(io.BytesIO(data), filename=file_filename, description=file_description, spoiler=spoiler)
    def to_dict(self) -> AttachmentPayload:
        result: AttachmentPayload = {
            'filename': self.filename,
            'id': self.id,
            'proxy_url': self.proxy_url,
            'size': self.size,
            'url': self.url,
            'spoiler': self.is_spoiler(),
        }
        if self.height:
            result['height'] = self.height
        if self.width:
            result['width'] = self.width
        if self.content_type:
            result['content_type'] = self.content_type
        if self.description is not None:
            result['description'] = self.description
        return result
class DeletedReferencedMessage:
    __slots__ = ('_parent',)
    def __init__(self, parent: MessageReference):
        self._parent: MessageReference = parent
    def __repr__(self) -> str:
        return f"<DeletedReferencedMessage id={self.id} channel_id={self.channel_id} guild_id={self.guild_id!r}>"
    @property
    def id(self) -> int:
        return self._parent.message_id
    @property
    def channel_id(self) -> int:
        return self._parent.channel_id
    @property
    def guild_id(self) -> Optional[int]:
        return self._parent.guild_id
class MessageReference:
    __slots__ = ('message_id', 'channel_id', 'guild_id', 'fail_if_not_exists', 'resolved', 'state')
    def __init__(self, *, message_id: int, channel_id: int, guild_id: Optional[int] = None, fail_if_not_exists: bool = True):
        self.state: Optional[ConnectionState] = None
        self.resolved: Optional[Union[Message, DeletedReferencedMessage]] = None
        self.message_id: Optional[int] = message_id
        self.channel_id: int = channel_id
        self.guild_id: Optional[int] = guild_id
        self.fail_if_not_exists: bool = fail_if_not_exists
    @classmethod
    def with_state(cls, state: ConnectionState, data: MessageReferencePayload) -> Self:
        self = cls.__new__(cls)
        self.message_id = utils._get_as_snowflake(data, 'message_id')
        self.channel_id = int(data['channel_id'])
        self.guild_id = utils._get_as_snowflake(data, 'guild_id')
        self.fail_if_not_exists = data.get('fail_if_not_exists', True)
        self.state = state
        self.resolved = None
        return self
    @classmethod
    def from_message(cls, message: PartialMessage, *, fail_if_not_exists: bool = True) -> Self:
        self = cls(
            message_id=message.id,
            channel_id=message.channel.id,
            guild_id=getattr(message.guild, 'id', None),
            fail_if_not_exists=fail_if_not_exists,
        )
        self.state = message.state
        return self
    @property
    def cached_message(self) -> Optional[Message]:
        return self.state and self.state._get_message(self.message_id)
    @property
    def jump_url(self) -> str:
        guild_id = self.guild_id if self.guild_id is not None else '@me'
        return f'https://discord.com/channels/{guild_id}/{self.channel_id}/{self.message_id}'
    def __repr__(self) -> str:
        return f'<MessageReference message_id={self.message_id!r} channel_id={self.channel_id!r} guild_id={self.guild_id!r}>'
    def to_dict(self) -> MessageReferencePayload:
        result: Dict[str, Any] = {'message_id': self.message_id} if self.message_id is not None else {}
        result['channel_id'] = self.channel_id
        if self.guild_id is not None:
            result['guild_id'] = self.guild_id
        if self.fail_if_not_exists is not None:
            result['fail_if_not_exists'] = self.fail_if_not_exists
        return result
    to_message_reference_dict = to_dict
def flatten_handlers(cls: Type[Message]) -> Type[Message]:
    prefix = len('_handle_')
    handlers = [
        (key[prefix:], value)
        for key, value in cls.__dict__.items()
        if key.startswith('_handle_') and key != '_handle_member'
    ]
    handlers.append(('member', cls._handle_member))
    cls._HANDLERS = handlers
    cls._CACHED_SLOTS = [attr for attr in cls.__slots__ if attr.startswith('_cs_')]
    return cls
class RoleSubscriptionInfo:
    __slots__ = (
        'role_subscription_listing_id',
        'tier_name',
        'total_months_subscribed',
        'is_renewal',
    )
    def __init__(self, data: RoleSubscriptionDataPayload) -> None:
        self.role_subscription_listing_id: int = int(data['role_subscription_listing_id'])
        self.tier_name: str = data['tier_name']
        self.total_months_subscribed: int = data['total_months_subscribed']
        self.is_renewal: bool = data['is_renewal']
class PartialMessage(Hashable):
    __slots__ = ('channel', 'id', 'state', 'guild_id', 'guild')
    def __init__(self, *, channel: MessageableChannel, id: int) -> None:
        if not isinstance(channel, PartialMessageable) and channel.type not in (
            ChannelType.text,
            ChannelType.voice,
            ChannelType.stage_voice,
            ChannelType.news,
            ChannelType.private,
            ChannelType.news_thread,
            ChannelType.public_thread,
            ChannelType.private_thread,
        ):
            raise TypeError(
                f'expected PartialMessageable, TextChannel, StageChannel, VoiceChannel, DMChannel or Thread not {type(channel)!r}'
            )
        self.channel: MessageableChannel = channel
        self.state: ConnectionState = channel.state
        self.id: int = id
        self.guild: Optional[Guild] = getattr(channel, 'guild', None)
        self.guild_id: Optional[int] = self.guild.id if self.guild else None
        if hasattr(channel, 'guild_id'):
            if self.guild_id is not None:
                channel.guild_id = self.guild_id
            else:
                self.guild_id = channel.guild_id
    def _update(self, data: MessageUpdateEvent) -> None:
        pass
    pinned: Any = property(None, lambda x, y: None)
    def __repr__(self) -> str:
        return f'<PartialMessage id={self.id} channel={self.channel!r}>'
    @property
    def created_at(self) -> datetime.datetime:
        return utils.snowflake_time(self.id)
    @property
    def jump_url(self) -> str:
        guild_id = getattr(self.guild, 'id', '@me')
        return f'https://discord.com/channels/{guild_id}/{self.channel.id}/{self.id}'
    async def fetch(self) -> Message:
        data = await self.state.http.get_message(self.channel.id, self.id)
        return self.state.create_message(channel=self.channel, data=data)
    async def delete(self, *, delay: Optional[float] = None) -> None:
        if delay is not None:
            async def delete(delay: float):
                await asyncio.sleep(delay)
                try:
                    await self.state.http.delete_message(self.channel.id, self.id)
                except HTTPException:
                    pass
            asyncio.create_task(delete(delay))
        else:
            await self.state.http.delete_message(self.channel.id, self.id)
    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        attachments: Sequence[Union[Attachment, _FileBase]] = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
    ) -> Message:
        ...
    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        attachments: Sequence[Union[Attachment, _FileBase]] = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
    ) -> Message:
        ...
    async def edit(
        self,
        content: Optional[str] = MISSING,
        attachments: Sequence[Union[Attachment, _FileBase]] = MISSING,
        delete_after: Optional[float] = None,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
    ) -> Message:
        if content is not MISSING:
            previous_allowed_mentions = self.state.allowed_mentions
        else:
            previous_allowed_mentions = None
        with handle_message_parameters(
            content=content,
            attachments=attachments,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_allowed_mentions,
        ) as params:
            data = await self.state.http.edit_message(self.channel.id, self.id, params=params)
            message = Message(state=self.state, channel=self.channel, data=data)
        if delete_after is not None:
            await self.delete(delay=delete_after)
        return message
    async def publish(self) -> None:
        await self.state.http.publish_message(self.channel.id, self.id)
    async def pin(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.pin_message(self.channel.id, self.id, reason=reason)
        self.pinned = True
    async def unpin(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.unpin_message(self.channel.id, self.id, reason=reason)
        self.pinned = False
    async def add_reaction(self, emoji: Union[EmojiInputType, Reaction], /) -> None:
        emoji = convert_emoji_reaction(emoji)
        await self.state.http.add_reaction(self.channel.id, self.id, emoji)
    async def remove_reaction(self, emoji: Union[EmojiInputType, Reaction], member: Snowflake) -> None:
        emoji = convert_emoji_reaction(emoji)
        if member.id == self.state.self_id:
            await self.state.http.remove_own_reaction(self.channel.id, self.id, emoji)
        else:
            await self.state.http.remove_reaction(self.channel.id, self.id, emoji, member.id)
    async def clear_reaction(self, emoji: Union[EmojiInputType, Reaction]) -> None:
        emoji = convert_emoji_reaction(emoji)
        await self.state.http.clear_single_reaction(self.channel.id, self.id, emoji)
    async def clear_reactions(self) -> None:
        await self.state.http.clear_reactions(self.channel.id, self.id)
    async def create_thread(
        self,
        *,
        name: str,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        slowmode_delay: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Thread:
        if self.guild is None:
            raise ValueError('This message does not have guild info attached')
        default_auto_archive_duration: ThreadArchiveDuration = getattr(self.channel, 'default_auto_archive_duration', 1440)
        data = await self.state.http.start_thread_with_message(
            self.channel.id,
            self.id,
            name=name,
            auto_archive_duration=auto_archive_duration or default_auto_archive_duration,
            rate_limit_per_user=slowmode_delay,
            reason=reason,
            location='Message',
        )
        return Thread(guild=self.guild, state=self.state, data=data)
    async def ack(self, *, manual: bool = False, mention_count: Optional[int] = None) -> None:
        await self.channel.read_state.ack(self.id, manual=manual, mention_count=mention_count)
    async def unack(self, *, mention_count: Optional[int] = None) -> None:
        await self.channel.read_state.ack(self.id - 1, manual=True, mention_count=mention_count)
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
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
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
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
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
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
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
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        return await self.channel.send(content, reference=self, **kwargs)
    @overload
    async def greet(
        self,
        sticker: Union[GuildSticker, StickerItem],
        *,
        allowed_mentions: AllowedMentions = ...,
        mention_author: bool = ...,
    ) -> Message:
        ...
    @overload
    async def greet(self, sticker: Union[GuildSticker, StickerItem]) -> Message:
        ...
    async def greet(self, sticker: Union[GuildSticker, StickerItem], **kwargs: Any) -> Message:
        return await self.channel.greet(sticker, reference=self, **kwargs)
    def to_reference(self, *, fail_if_not_exists: bool = True) -> MessageReference:
        return MessageReference.from_message(self, fail_if_not_exists=fail_if_not_exists)
    def to_message_reference_dict(self) -> MessageReferencePayload:
        data: MessageReferencePayload = {
            'message_id': self.id,
            'channel_id': self.channel.id,
        }
        if self.guild is not None:
            data['guild_id'] = self.guild.id
        return data
@flatten_handlers
class Message(PartialMessage, Hashable):
    r
    __slots__ = (
        '_edited_timestamp',
        '_cs_channel_mentions',
        '_cs_raw_mentions',
        '_cs_clean_content',
        '_cs_raw_channel_mentions',
        '_cs_raw_role_mentions',
        '_cs_system_content',
        'tts',
        'content',
        'webhook_id',
        'mention_everyone',
        'embeds',
        'mentions',
        'author',
        'attachments',
        'nonce',
        'pinned',
        'role_mentions',
        'type',
        'flags',
        'reactions',
        'reference',
        'application',
        'activity',
        'stickers',
        'components',
        'call',
        'interaction',
        'role_subscription',
        'application_id',
        'position',
        'hit',
        'total_results',
        'analytics_id',
        'doing_deep_historical_index',
    )
    if TYPE_CHECKING:
        _HANDLERS: ClassVar[List[Tuple[str, Callable[..., None]]]]
        _CACHED_SLOTS: ClassVar[List[str]]
        reference: Optional[MessageReference]
        mentions: List[Union[User, Member]]
        author: Union[User, Member]
        role_mentions: List[Role]
        components: List[ActionRow]
    def __init__(
        self,
        *,
        state: ConnectionState,
        channel: MessageableChannel,
        data: MessagePayload,
        search_result: Optional[MessageSearchResultPayload] = None,
    ) -> None:
        self.channel: MessageableChannel = channel
        self.id: int = int(data['id'])
        self.state: ConnectionState = state
        self.webhook_id: Optional[int] = utils._get_as_snowflake(data, 'webhook_id')
        self.reactions: List[Reaction] = [Reaction(message=self, data=d) for d in data.get('reactions', [])]
        self.attachments: List[Attachment] = [Attachment(data=a, state=self.state) for a in data['attachments']]
        self.embeds: List[Embed] = [Embed.from_dict(a) for a in data['embeds']]
        self.activity: Optional[MessageActivityPayload] = data.get('activity')
        self._edited_timestamp: Optional[datetime.datetime] = utils.parse_time(data['edited_timestamp'])
        self.type: MessageType = try_enum(MessageType, data['type'])
        self.pinned: bool = data['pinned']
        self.flags: MessageFlags = MessageFlags._from_value(data.get('flags', 0))
        self.mention_everyone: bool = data['mention_everyone']
        self.tts: bool = data['tts']
        self.content: str = data['content']
        self.nonce: Optional[Union[int, str]] = data.get('nonce')
        self.position: Optional[int] = data.get('position')
        self.application_id: Optional[int] = utils._get_as_snowflake(data, 'application_id')
        self.stickers: List[StickerItem] = [StickerItem(data=d, state=state) for d in data.get('sticker_items', [])]
        self.call: Optional[CallMessage] = None
        try:
            self.guild = channel.guild
        except AttributeError:
            guild_id = utils._get_as_snowflake(data, 'guild_id')
            if guild_id is not None:
                channel.guild_id = guild_id
            else:
                guild_id = channel.guild_id
            self.guild_id: Optional[int] = guild_id
            self.guild = state._get_guild(guild_id)
        self.application: Optional[IntegrationApplication] = None
        try:
            application = data['application']
        except KeyError:
            pass
        else:
            self.application = IntegrationApplication(state=self.state, data=application)
        self.interaction: Optional[Interaction] = None
        try:
            interaction = data['interaction']
        except KeyError:
            pass
        else:
            self.interaction = Interaction._from_message(self, **interaction)
        try:
            ref = data['message_reference']
        except KeyError:
            self.reference = None
        else:
            self.reference = ref = MessageReference.with_state(state, ref)
            try:
                resolved = data['referenced_message']
            except KeyError:
                pass
            else:
                if resolved is None:
                    ref.resolved = DeletedReferencedMessage(ref)
                else:
                    if ref.channel_id == channel.id:
                        chan = channel
                    elif isinstance(channel, Thread) and channel.parent_id == ref.channel_id:
                        chan = channel
                    else:
                        chan, _ = state._get_guild_channel(resolved, ref.guild_id)
                    ref.resolved = self.__class__(channel=chan, data=resolved, state=state)
        self.role_subscription: Optional[RoleSubscriptionInfo] = None
        try:
            role_subscription = data['role_subscription_data']
        except KeyError:
            pass
        else:
            self.role_subscription = RoleSubscriptionInfo(role_subscription)
        search_payload = search_result or {}
        self.hit: bool = data.get('hit', False)
        self.total_results: Optional[int] = search_payload.get('total_results')
        self.analytics_id: Optional[str] = search_payload.get('analytics_id')
        self.doing_deep_historical_index: Optional[bool] = search_payload.get('doing_deep_historical_index')
        for handler in ('author', 'member', 'mentions', 'mention_roles', 'call', 'interaction', 'components'):
            try:
                getattr(self, f'_handle_{handler}')(data[handler])
            except KeyError:
                continue
    def __repr__(self) -> str:
        name = self.__class__.__name__
        return (
            f'<{name} id={self.id} channel={self.channel!r} type={self.type!r} author={self.author!r} flags={self.flags!r}>'
        )
    async def _get_channel(self) -> MessageableChannel:
        return self.channel
    def _try_patch(self, data, key, transform=None) -> None:
        try:
            value = data[key]
        except KeyError:
            pass
        else:
            if transform is None:
                setattr(self, key, value)
            else:
                setattr(self, key, transform(value))
    def _add_reaction(self, data, emoji, user_id) -> Reaction:
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)
        is_me = data['me'] = user_id == self.state.self_id
        if reaction is None:
            reaction = Reaction(message=self, data=data, emoji=emoji)
            self.reactions.append(reaction)
        else:
            reaction.count += 1
            if is_me:
                reaction.me = is_me
        return reaction
    def _remove_reaction(self, data: MessageReactionRemoveEvent, emoji: EmojiInputType, user_id: int) -> Reaction:
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)
        if reaction is None:
            raise ValueError('Emoji already removed?')
        reaction.count -= 1
        if user_id == self.state.self_id:
            reaction.me = False
        if reaction.count == 0:
            self.reactions.remove(reaction)
        return reaction
    def _clear_emoji(self, emoji: PartialEmoji) -> Optional[Reaction]:
        to_check = str(emoji)
        for index, reaction in enumerate(self.reactions):
            if str(reaction.emoji) == to_check:
                break
        else:
            return
        del self.reactions[index]
        return reaction
    def _update(self, data: MessageUpdateEvent) -> None:
        for key, handler in self._HANDLERS:
            try:
                value = data[key]
            except KeyError:
                continue
            else:
                handler(self, value)
        for attr in self._CACHED_SLOTS:
            try:
                delattr(self, attr)
            except AttributeError:
                pass
    def _handle_edited_timestamp(self, value: str) -> None:
        self._edited_timestamp = utils.parse_time(value)
    def _handle_pinned(self, value: bool) -> None:
        self.pinned = value
    def _handle_flags(self, value: int) -> None:
        self.flags = MessageFlags._from_value(value)
    def _handle_application(self, value: MessageApplicationPayload) -> None:
        application = IntegrationApplication(state=self.state, data=value)
        self.application = application
    def _handle_activity(self, value: MessageActivityPayload) -> None:
        self.activity = value
    def _handle_mention_everyone(self, value: bool) -> None:
        self.mention_everyone = value
    def _handle_tts(self, value: bool) -> None:
        self.tts = value
    def _handle_type(self, value: int) -> None:
        self.type = try_enum(MessageType, value)
    def _handle_content(self, value: str) -> None:
        self.content = value
    def _handle_attachments(self, value: List[AttachmentPayload]) -> None:
        self.attachments = [Attachment(data=a, state=self.state) for a in value]
    def _handle_embeds(self, value: List[EmbedPayload]) -> None:
        self.embeds = [Embed.from_dict(data) for data in value]
    def _handle_nonce(self, value: Union[str, int]) -> None:
        self.nonce = value
    def _handle_author(self, author: UserPayload) -> None:
        self.author = self.state.store_user(author, cache=self.webhook_id is None)
        if isinstance(self.guild, Guild):
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found
    def _handle_member(self, member: MemberPayload) -> None:
        author = self.author
        try:
            author._update_from_message(member)
        except AttributeError:
            self.author = Member._from_message(message=self, data=member)
    def _handle_mentions(self, mentions: List[UserWithMemberPayload]) -> None:
        self.mentions = r = []
        guild = self.guild
        state = self.state
        if not isinstance(guild, Guild):
            self.mentions = [state.store_user(m) for m in mentions]
            return
        for mention in filter(None, mentions):
            id_search = int(mention['id'])
            member = guild.get_member(id_search)
            if member is not None:
                r.append(member)
            else:
                r.append(Member._try_upgrade(data=mention, guild=guild, state=state))
    def _handle_mention_roles(self, role_mentions: List[int]) -> None:
        self.role_mentions = r = []
        if isinstance(self.guild, Guild):
            for role_id in map(int, role_mentions):
                role = self.guild.get_role(role_id)
                if role is not None:
                    r.append(role)
    def _handle_call(self, call: Optional[CallPayload]) -> None:
        if call is None or self.type is not MessageType.call:
            self.call = None
            return
        participants = []
        for uid in map(int, call.get('participants', [])):
            if uid == self.author.id:
                participants.append(self.author)
            else:
                user = utils.find(lambda u: u.id == uid, self.mentions)
                if user is not None:
                    participants.append(user)
        self.call = CallMessage(message=self, ended_timestamp=call.get('ended_timestamp'), participants=participants)
    def _handle_components(self, data: List[ComponentPayload]) -> None:
        self.components = []
        for component_data in data:
            component = _component_factory(component_data, self)
            if component is not None:
                self.components.append(component)
    def _handle_interaction(self, data: MessageInteractionPayload):
        self.interaction = Interaction._from_message(self, **data)
    def _rebind_cached_references(
        self,
        new_guild: Guild,
        new_channel: Union[GuildChannel, Thread, PartialMessageable],
    ) -> None:
        self.guild = new_guild
        self.channel = new_channel
    def _is_self_mentioned(self) -> bool:
        state = self.state
        guild = self.guild
        channel = self.channel
        settings = guild.notification_settings if guild else state.client.notification_settings
        if channel.type in (ChannelType.private, ChannelType.group) and not settings.muted and not channel.notification_settings.muted:
            return True
        if state.user in self.mentions:
            return True
        if self.mention_everyone and not settings.suppress_everyone:
            return True
        if guild and guild.me and not settings.suppress_roles and guild.me.mentioned_in(self):
            return True
        return False
    @utils.cached_slot_property('_cs_raw_mentions')
    def raw_mentions(self) -> List[int]:
        return [int(x) for x in re.findall(r'<@!?([0-9]{15,20})>', self.content)]
    @utils.cached_slot_property('_cs_raw_channel_mentions')
    def raw_channel_mentions(self) -> List[int]:
        return [int(x) for x in re.findall(r'<
    @utils.cached_slot_property('_cs_raw_role_mentions')
    def raw_role_mentions(self) -> List[int]:
        return [int(x) for x in re.findall(r'<@&([0-9]{15,20})>', self.content)]
    @utils.cached_slot_property('_cs_channel_mentions')
    def channel_mentions(self) -> List[Union[GuildChannel, Thread]]:
        if self.guild is None:
            return []
        it = filter(None, map(self.guild._resolve_channel, self.raw_channel_mentions))
        return utils._unique(it)
    @utils.cached_slot_property('_cs_clean_content')
    def clean_content(self) -> str:
        if self.guild:
            def resolve_member(id: int) -> str:
                m = self.guild.get_member(id) or utils.get(self.mentions, id=id)
                return f'@{m.display_name}' if m else '@deleted-user'
            def resolve_role(id: int) -> str:
                r = self.guild.get_role(id) or utils.get(self.role_mentions, id=id)
                return f'@{r.name}' if r else '@deleted-role'
            def resolve_channel(id: int) -> str:
                c = self.guild._resolve_channel(id)
                return f'
        else:
            def resolve_member(id: int) -> str:
                m = utils.get(self.mentions, id=id)
                return f'@{m.display_name}' if m else '@deleted-user'
            def resolve_role(id: int) -> str:
                return '@deleted-role'
            def resolve_channel(id: int) -> str:
                return '
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
        return escape_mentions(result)
    @property
    def created_at(self) -> datetime.datetime:
        return utils.snowflake_time(self.id)
    @property
    def edited_at(self) -> Optional[datetime.datetime]:
        return self._edited_timestamp
    def is_system(self) -> bool:
        return self.type not in (
            MessageType.default,
            MessageType.reply,
            MessageType.chat_input_command,
            MessageType.context_menu_command,
            MessageType.thread_starter_message,
        )
    def is_acked(self) -> bool:
        read_state = self.state.get_read_state(self.channel.id)
        return read_state.last_acked_id >= self.id if read_state.last_acked_id else False
    @utils.cached_slot_property('_cs_system_content')
    def system_content(self) -> str:
        r
        if self.type is MessageType.recipient_add:
            if self.channel.type is ChannelType.group:
                return f'{self.author.name} added {self.mentions[0].name} to the group.'
            else:
                return f'{self.author.name} added {self.mentions[0].name} to the thread.'
        if self.type is MessageType.recipient_remove:
            if self.channel.type is ChannelType.group:
                return f'{self.author.name} removed {self.mentions[0].name} from the group.'
            else:
                return f'{self.author.name} removed {self.mentions[0].name} from the thread.'
        if self.type is MessageType.channel_name_change:
            if getattr(self.channel, 'parent', self.channel).type is ChannelType.forum:
                return f'{self.author.name} changed the post title: **{self.content}**'
            else:
                return f'{self.author.name} changed the channel name: **{self.content}**'
        if self.type is MessageType.channel_icon_change:
            return f'{self.author.name} changed the group icon.'
        if self.type is MessageType.pins_add:
            return f'{self.author.name} pinned a message to this channel.'
        if self.type is MessageType.new_member:
            formats = [
                "{0} joined the party.",
                "{0} is here.",
                "Welcome, {0}. We hope you brought pizza.",
                "A wild {0} appeared.",
                "{0} just landed.",
                "{0} just slid into the server.",
                "{0} just showed up!",
                "Welcome {0}. Say hi!",
                "{0} hopped into the server.",
                "Everyone welcome {0}!",
                "Glad you're here, {0}.",
                "Good to see you, {0}.",
                "Yay you made it, {0}!",
            ]
            created_at_ms = int(self.created_at.timestamp() * 1000)
            return formats[created_at_ms % len(formats)].format(self.author.name)
        if self.type is MessageType.call:
            call_ended = self.call.ended_timestamp is not None
            if self.channel.me in self.call.participants:
                return f'{self.author.name} started a call.'
            elif call_ended:
                return f'You missed a call from {self.author.name} that lasted {int((utils.utcnow() - self.call.ended_timestamp).total_seconds())} seconds.'
            else:
                return f'{self.author.name} started a call \N{EM DASH} Join the call.'
        if self.type is MessageType.premium_guild_subscription:
            if not self.content:
                return f'{self.author.name} just boosted the server!'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times!'
        if self.type is MessageType.premium_guild_tier_1:
            if not self.content:
                return f'{self.author.name} just boosted the server! {self.guild} has achieved **Level 1!**'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times! {self.guild} has achieved **Level 1!**'
        if self.type is MessageType.premium_guild_tier_2:
            if not self.content:
                return f'{self.author.name} just boosted the server! {self.guild} has achieved **Level 2!**'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times! {self.guild} has achieved **Level 2!**'
        if self.type is MessageType.premium_guild_tier_3:
            if not self.content:
                return f'{self.author.name} just boosted the server! {self.guild} has achieved **Level 3!**'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times! {self.guild} has achieved **Level 3!**'
        if self.type is MessageType.channel_follow_add:
            return (
                f'{self.author.name} has added {self.content} to this channel. Its most important updates will show up here.'
            )
        if self.type is MessageType.guild_discovery_disqualified:
            return 'This server has been removed from Server Discovery because it no longer passes all the requirements. Check Server Settings for more details.'
        if self.type is MessageType.guild_discovery_requalified:
            return 'This server is eligible for Server Discovery again and has been automatically relisted!'
        if self.type is MessageType.guild_discovery_grace_period_initial_warning:
            return 'This server has failed Discovery activity requirements for 1 week. If this server fails for 4 weeks in a row, it will be automatically removed from Discovery.'
        if self.type is MessageType.guild_discovery_grace_period_final_warning:
            return 'This server has failed Discovery activity requirements for 3 weeks in a row. If this server fails for 1 more week, it will be removed from Discovery.'
        if self.type is MessageType.thread_created:
            return f'{self.author.name} started a thread: **{self.content}**. See all threads.'
        if self.type is MessageType.thread_starter_message:
            if self.reference is None or self.reference.resolved is None:
                return 'Sorry, we couldn\'t load the first message in this thread'
            return self.reference.resolved.content
        if self.type is MessageType.guild_invite_reminder:
            return 'Wondering who to invite?\nStart by inviting anyone who can help you build the server!'
        if self.type is MessageType.role_subscription_purchase and self.role_subscription is not None:
            total_months = self.role_subscription.total_months_subscribed
            months = '1 month' if total_months == 1 else f'{total_months} months'
            action = 'renewed' if self.role_subscription.is_renewal else 'subscribed'
            return f'{self.author.name} {action} **{self.role_subscription.tier_name}** and has been a subscriber of {self.guild} for {months}!'
        if self.type is MessageType.stage_start:
            return f'{self.author.name} started **{self.content}**'
        if self.type is MessageType.stage_end:
            return f'{self.author.name} ended **{self.content}**'
        if self.type is MessageType.stage_speaker:
            return f'{self.author.name} is now a speaker.'
        if self.type is MessageType.stage_raise_hand:
            return f'{self.author.name} requested to speak.'
        if self.type is MessageType.stage_topic:
            return f'{self.author.name} changed the Stage topic: **{self.content}**'
        if self.type is MessageType.guild_application_premium_subscription:
            return f'{self.author.name} upgraded {self.application.name if self.application else "a deleted application"} to premium for this server!'
        return self.content
    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        attachments: Sequence[Union[Attachment, _FileBase]] = ...,
        suppress: bool = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
    ) -> Message:
        ...
    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        attachments: Sequence[Union[Attachment, _FileBase]] = ...,
        suppress: bool = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
    ) -> Message:
        ...
    async def edit(
        self,
        content: Optional[str] = MISSING,
        attachments: Sequence[Union[Attachment, _FileBase]] = MISSING,
        suppress: bool = False,
        delete_after: Optional[float] = None,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
    ) -> Message:
        if content is not MISSING:
            previous_allowed_mentions = self.state.allowed_mentions
        else:
            previous_allowed_mentions = None
        if suppress is not MISSING:
            flags = MessageFlags._from_value(self.flags.value)
            flags.suppress_embeds = suppress
        else:
            flags = MISSING
        with handle_message_parameters(
            content=content,
            flags=flags,
            attachments=attachments,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_allowed_mentions,
        ) as params:
            data = await self.state.http.edit_message(self.channel.id, self.id, params=params)
            message = Message(state=self.state, channel=self.channel, data=data)
        if delete_after is not None:
            await self.delete(delay=delete_after)
        return message
    async def add_files(self, *files: _FileBase) -> Message:
        r
        return await self.edit(attachments=[*self.attachments, *files])
    async def remove_attachments(self, *attachments: Attachment) -> Message:
        r
        return await self.edit(attachments=[a for a in self.attachments if a not in attachments])
    @utils.deprecated("Message.channel.application_commands")
    def message_commands(
        self,
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        command_ids: Optional[Collection[int]] = None,
        application: Optional[Snowflake] = None,
        with_applications: bool = True,
    ) -> AsyncIterator[MessageCommand]:
        return _handle_commands(
            self,
            ApplicationCommandType.message,
            query=query,
            limit=limit,
            command_ids=command_ids,
            application=application,
            target=self,
        )