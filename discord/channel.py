from __future__ import annotations
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    TYPE_CHECKING,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)
import datetime
from operator import attrgetter
import discord.abc
from .scheduled_event import ScheduledEvent
from .permissions import PermissionOverwrite, Permissions
from .enums import (
    ChannelType,
    EntityType,
    ForumLayoutType,
    ForumOrderType,
    PrivacyLevel,
    try_enum,
    VideoQualityMode,
    DirectoryCategory,
    DirectoryEntryType,
)
from .calls import PrivateCall, GroupCall
from .mixins import Hashable
from . import utils
from .utils import MISSING
from .asset import Asset
from .errors import ClientException, DiscordException
from .stage_instance import StageInstance
from .threads import Thread
from .partial_emoji import _EmojiTag, PartialEmoji
from .flags import ChannelFlags, MessageFlags
from .http import handle_message_parameters
from .invite import Invite
from .voice_client import VoiceClient
from .directory import DirectoryEntry
__all__ = (
    'TextChannel',
    'VoiceChannel',
    'StageChannel',
    'CategoryChannel',
    'ForumTag',
    'ForumChannel',
    'DirectoryChannel',
    'DMChannel',
    'GroupChannel',
    'PartialMessageable',
)
if TYPE_CHECKING:
    from typing_extensions import Self
    from .types.threads import ThreadArchiveDuration
    from .client import Client
    from .role import Role
    from .object import Object
    from .member import Member, VoiceState
    from .abc import Snowflake, SnowflakeTime, T
    from .message import Message, PartialMessage, EmojiInputType
    from .mentions import AllowedMentions
    from .webhook import Webhook
    from .state import ConnectionState
    from .sticker import GuildSticker, StickerItem
    from .file import File
    from .user import BaseUser, ClientUser, User
    from .guild import Guild, GuildChannel as GuildChannelType
    from .settings import ChannelSettings
    from .read_state import ReadState
    from .types.channel import (
        TextChannel as TextChannelPayload,
        NewsChannel as NewsChannelPayload,
        VoiceChannel as VoiceChannelPayload,
        StageChannel as StageChannelPayload,
        DirectoryChannel as DirectoryChannelPayload,
        DMChannel as DMChannelPayload,
        CategoryChannel as CategoryChannelPayload,
        GroupDMChannel as GroupChannelPayload,
        ForumChannel as ForumChannelPayload,
        ForumTag as ForumTagPayload,
    )
    from .types.oauth2 import WebhookChannel as WebhookChannelPayload
    from .types.snowflake import SnowflakeList
    OverwriteKeyT = TypeVar('OverwriteKeyT', Role, BaseUser, Object, Union[Role, Member, Object])
class ThreadWithMessage(NamedTuple):
    thread: Thread
    message: Message
class TextChannel(discord.abc.Messageable, discord.abc.GuildChannel, Hashable):
    __slots__ = (
        'name',
        'id',
        'guild',
        'topic',
        'state',
        'nsfw',
        'category_id',
        'position',
        'slowmode_delay',
        '_overwrites',
        '_type',
        'last_message_id',
        'last_pin_timestamp',
        'default_auto_archive_duration',
        'default_thread_slowmode_delay',
    )
    def __init__(self, *, state: ConnectionState, guild: Guild, data: Union[TextChannelPayload, NewsChannelPayload]):
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self._type: Literal[0, 5] = data['type']
        self._update(guild, data)
    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('nsfw', self.nsfw),
            ('news', self.is_news()),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'
    def _update(self, guild: Guild, data: Union[TextChannelPayload, NewsChannelPayload]) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.topic: Optional[str] = data.get('topic')
        self.position: int = data['position']
        self.nsfw: bool = data.get('nsfw', False)
        self.slowmode_delay: int = data.get('rate_limit_per_user', 0)
        self.default_auto_archive_duration: ThreadArchiveDuration = data.get('default_auto_archive_duration', 1440)
        self.default_thread_slowmode_delay: int = data.get('default_thread_rate_limit_per_user', 0)
        self._type: Literal[0, 5] = data.get('type', self._type)
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('last_pin_timestamp'))
        self._fill_overwrites(data)
    async def _get_channel(self) -> Self:
        return self
    @property
    def type(self) -> ChannelType:
        return try_enum(ChannelType, self._type)
    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.text.value
    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return None
    @utils.copy_doc(discord.abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)
        self._apply_implicit_permissions(base)
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base
    @property
    def members(self) -> List[Member]:
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]
    @property
    def threads(self) -> List[Thread]:
        return [thread for thread in self.guild._threads.values() if thread.parent_id == self.id]
    def is_nsfw(self) -> bool:
        return self.nsfw
    def is_news(self) -> bool:
        return self._type == ChannelType.news.value
    @property
    def read_state(self) -> ReadState:
        return self.state.get_read_state(self.id)
    @property
    def last_message(self) -> Optional[Message]:
        return self.state._get_message(self.last_message_id) if self.last_message_id else None
    @property
    def acked_message_id(self) -> int:
        return self.read_state.last_acked_id
    @property
    def acked_message(self) -> Optional[Message]:
        acked_message_id = self.acked_message_id
        if acked_message_id is None:
            return
        message = self.state._get_message(acked_message_id)
        if message and message.channel.id == self.id:
            return message
    @property
    def acked_pin_timestamp(self) -> Optional[datetime.datetime]:
        return self.read_state.last_pin_timestamp
    @property
    def mention_count(self) -> int:
        return self.read_state.badge_count
    @property
    def last_viewed_timestamp(self) -> datetime.date:
        return self.read_state.last_viewed
    @overload
    async def edit(self) -> Optional[TextChannel]:
        ...
    @overload
    async def edit(self, *, position: int, reason: Optional[str] = ...) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        topic: str = ...,
        position: int = ...,
        nsfw: bool = ...,
        sync_permissions: bool = ...,
        category: Optional[CategoryChannel] = ...,
        slowmode_delay: int = ...,
        default_auto_archive_duration: ThreadArchiveDuration = ...,
        default_thread_slowmode_delay: int = ...,
        type: ChannelType = ...,
        overwrites: Mapping[OverwriteKeyT, PermissionOverwrite] = ...,
    ) -> TextChannel:
        ...
    async def edit(self, *, reason: Optional[str] = None, **options: Any) -> Optional[TextChannel]:
        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return self.__class__(state=self.state, guild=self.guild, data=payload)
    @utils.copy_doc(discord.abc.GuildChannel.clone)
    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> TextChannel:
        return await self._clone_impl(
            {'topic': self.topic, 'nsfw': self.nsfw, 'rate_limit_per_user': self.slowmode_delay}, name=name, reason=reason
        )
    async def delete_messages(self, messages: Iterable[Snowflake], /, *, reason: Optional[str] = None) -> None:
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)
        if len(messages) == 0:
            return
        await self.state._delete_messages(self.id, messages, reason=reason)
    async def purge(
        self,
        *,
        limit: Optional[int] = 100,
        check: Callable[[Message], bool] = MISSING,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
        reason: Optional[str] = None,
    ) -> List[Message]:
        return await discord.abc._purge_helper(
            self,
            limit=limit,
            check=check,
            before=before,
            after=after,
            around=around,
            oldest_first=oldest_first,
            reason=reason,
        )
    async def webhooks(self) -> List[Webhook]:
        from .webhook import Webhook
        data = await self.state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self.state) for d in data]
    async def create_webhook(self, *, name: str, avatar: Optional[bytes] = None, reason: Optional[str] = None) -> Webhook:
        from .webhook import Webhook
        if avatar is not None:
            avatar = utils._bytes_to_base64_data(avatar)
        data = await self.state.http.create_webhook(self.id, name=str(name), avatar=avatar, reason=reason)
        return Webhook.from_state(data, state=self.state)
    async def follow(self, *, destination: TextChannel, reason: Optional[str] = None) -> Webhook:
        if not self.is_news():
            raise ClientException('The channel must be a news channel.')
        if not isinstance(destination, TextChannel):
            raise TypeError(f'Expected TextChannel received {destination.__class__.__name__}')
        from .webhook import Webhook
        data = await self.state.http.follow_webhook(self.id, webhook_channel_id=destination.id, reason=reason)
        return Webhook._as_follower(data, channel=destination, user=self.state.user)
    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        from .message import PartialMessage
        return PartialMessage(channel=self, id=message_id)
    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        return self.guild.get_thread(thread_id)
    async def create_thread(
        self,
        *,
        name: str,
        message: Optional[Snowflake] = None,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        type: Optional[ChannelType] = None,
        reason: Optional[str] = None,
        invitable: bool = True,
        slowmode_delay: Optional[int] = None,
    ) -> Thread:
        if type is None:
            type = ChannelType.private_thread
        if message is None:
            data = await self.state.http.start_thread_without_message(
                self.id,
                name=name,
                auto_archive_duration=auto_archive_duration or self.default_auto_archive_duration,
                type=type.value,
                reason=reason,
                invitable=invitable,
                rate_limit_per_user=slowmode_delay,
            )
        else:
            data = await self.state.http.start_thread_with_message(
                self.id,
                message.id,
                name=name,
                auto_archive_duration=auto_archive_duration or self.default_auto_archive_duration,
                reason=reason,
                rate_limit_per_user=slowmode_delay,
            )
        return Thread(guild=self.guild, state=self.state, data=data)
    async def archived_threads(
        self,
        *,
        private: bool = False,
        joined: bool = False,
        limit: Optional[int] = 100,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
    ) -> AsyncIterator[Thread]:
        if joined and not private:
            raise ValueError('Cannot retrieve joined public archived threads')
        before_timestamp = None
        if isinstance(before, datetime.datetime):
            if joined:
                before_timestamp = str(utils.time_snowflake(before, high=False))
            else:
                before_timestamp = before.isoformat()
        elif before is not None:
            if joined:
                before_timestamp = str(before.id)
            else:
                before_timestamp = utils.snowflake_time(before.id).isoformat()
        update_before = lambda data: data['thread_metadata']['archive_timestamp']
        endpoint = self.guild.state.http.get_public_archived_threads
        if joined:
            update_before = lambda data: data['id']
            endpoint = self.guild.state.http.get_joined_private_archived_threads
        elif private:
            endpoint = self.guild.state.http.get_private_archived_threads
        while True:
            retrieve = 100
            if limit is not None:
                if limit <= 0:
                    return
                retrieve = max(2, min(retrieve, limit))
            data = await endpoint(self.id, before=before_timestamp, limit=retrieve)
            threads = data.get('threads', [])
            for raw_thread in threads:
                yield Thread(guild=self.guild, state=self.guild.state, data=raw_thread)
                if limit is not None:
                    limit -= 1
                    if limit <= 0:
                        return
            if not data.get('has_more', False):
                return
            before_timestamp = update_before(threads[-1])
class VocalGuildChannel(discord.abc.Messageable, discord.abc.Connectable, discord.abc.GuildChannel, Hashable):
    __slots__ = (
        'name',
        'id',
        'guild',
        'nsfw',
        'bitrate',
        'user_limit',
        'state',
        'position',
        'slowmode_delay',
        '_overwrites',
        'category_id',
        'rtc_region',
        'video_quality_mode',
        'last_message_id',
        'last_pin_timestamp',
    )
    def __init__(self, *, state: ConnectionState, guild: Guild, data: Union[VoiceChannelPayload, StageChannelPayload]):
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(guild, data)
    async def _get_channel(self) -> Self:
        return self
    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.guild.id, 'guild_id'
    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.guild.id, self.id
    def _update(self, guild: Guild, data: Union[VoiceChannelPayload, StageChannelPayload]) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.nsfw: bool = data.get('nsfw', False)
        self.rtc_region: Optional[str] = data.get('rtc_region')
        self.video_quality_mode: VideoQualityMode = try_enum(VideoQualityMode, data.get('video_quality_mode', 1))
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('last_pin_timestamp'))
        self.position: int = data['position']
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self.bitrate: int = data['bitrate']
        self.user_limit: int = data['user_limit']
        self._fill_overwrites(data)
    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.voice.value
    def is_nsfw(self) -> bool:
        return self.nsfw
    @property
    def members(self) -> List[Member]:
        ret = []
        for user_id, state in self.guild._voice_states.items():
            if state.channel and state.channel.id == self.id:
                member = self.guild.get_member(user_id)
                if member is not None:
                    ret.append(member)
        return ret
    @property
    def voice_states(self) -> Dict[int, VoiceState]:
        return {
            key: value
            for key, value in self.guild._voice_states.items()
            if value.channel and value.channel.id == self.id
        }
    @property
    def scheduled_events(self) -> List[ScheduledEvent]:
        return [event for event in self.guild.scheduled_events if event.channel_id == self.id]
    @utils.copy_doc(discord.abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)
        self._apply_implicit_permissions(base)
        if not base.connect:
            denied = Permissions.voice()
            denied.update(manage_channels=True, manage_roles=True)
            base.value &= ~denied.value
        return base
    @property
    def read_state(self) -> ReadState:
        return self.state.get_read_state(self.id)
    @property
    def last_message(self) -> Optional[Message]:
        return self.state._get_message(self.last_message_id) if self.last_message_id else None
    @property
    def acked_message_id(self) -> int:
        return self.read_state.last_acked_id
    @property
    def acked_message(self) -> Optional[Message]:
        acked_message_id = self.acked_message_id
        if acked_message_id is None:
            return
        message = self.state._get_message(acked_message_id)
        if message and message.channel.id == self.id:
            return message
    @property
    def acked_pin_timestamp(self) -> Optional[datetime.datetime]:
        return self.read_state.last_pin_timestamp
    @property
    def mention_count(self) -> int:
        return self.read_state.badge_count
    @property
    def last_viewed_timestamp(self) -> datetime.date:
        return self.read_state.last_viewed
    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        from .message import PartialMessage
        return PartialMessage(channel=self, id=message_id)
    async def delete_messages(self, messages: Iterable[Snowflake], /, *, reason: Optional[str] = None) -> None:
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)
        if len(messages) == 0:
            return
        await self.state._delete_messages(self.id, messages, reason=reason)
    async def purge(
        self,
        *,
        limit: Optional[int] = 100,
        check: Callable[[Message], bool] = MISSING,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
        reason: Optional[str] = None,
    ) -> List[Message]:
        return await discord.abc._purge_helper(
            self,
            limit=limit,
            check=check,
            before=before,
            after=after,
            around=around,
            oldest_first=oldest_first,
            reason=reason,
        )
    async def webhooks(self) -> List[Webhook]:
        from .webhook import Webhook
        data = await self.state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self.state) for d in data]
    async def create_webhook(self, *, name: str, avatar: Optional[bytes] = None, reason: Optional[str] = None) -> Webhook:
        from .webhook import Webhook
        if avatar is not None:
            avatar = utils._bytes_to_base64_data(avatar)
        data = await self.state.http.create_webhook(self.id, name=str(name), avatar=avatar, reason=reason)
        return Webhook.from_state(data, state=self.state)
class VoiceChannel(VocalGuildChannel):
    __slots__ = ()
    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('rtc_region', self.rtc_region),
            ('position', self.position),
            ('bitrate', self.bitrate),
            ('video_quality_mode', self.video_quality_mode),
            ('user_limit', self.user_limit),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'
    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return EntityType.voice
    @property
    def type(self) -> Literal[ChannelType.voice]:
        return ChannelType.voice
    @utils.copy_doc(discord.abc.GuildChannel.clone)
    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> VoiceChannel:
        return await self._clone_impl({'bitrate': self.bitrate, 'user_limit': self.user_limit}, name=name, reason=reason)
    @overload
    async def edit(self) -> None:
        ...
    @overload
    async def edit(self, *, position: int, reason: Optional[str] = ...) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        nsfw: bool = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        position: int = ...,
        sync_permissions: int = ...,
        category: Optional[CategoryChannel] = ...,
        overwrites: Mapping[OverwriteKeyT, PermissionOverwrite] = ...,
        rtc_region: Optional[str] = ...,
        video_quality_mode: VideoQualityMode = ...,
        slowmode_delay: int = ...,
        reason: Optional[str] = ...,
    ) -> VoiceChannel:
        ...
    async def edit(self, *, reason: Optional[str] = None, **options: Any) -> Optional[VoiceChannel]:
        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return self.__class__(state=self.state, guild=self.guild, data=payload)
class StageChannel(VocalGuildChannel):
    __slots__ = ('topic',)
    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('topic', self.topic),
            ('rtc_region', self.rtc_region),
            ('position', self.position),
            ('bitrate', self.bitrate),
            ('video_quality_mode', self.video_quality_mode),
            ('user_limit', self.user_limit),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'
    def _update(self, guild: Guild, data: StageChannelPayload) -> None:
        super()._update(guild, data)
        self.topic: Optional[str] = data.get('topic')
    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return EntityType.stage_instance
    @property
    def requesting_to_speak(self) -> List[Member]:
        return [member for member in self.members if member.voice and member.voice.requested_to_speak_at is not None]
    @property
    def speakers(self) -> List[Member]:
        return [
            member
            for member in self.members
            if member.voice and not member.voice.suppress and member.voice.requested_to_speak_at is None
        ]
    @property
    def listeners(self) -> List[Member]:
        return [member for member in self.members if member.voice and member.voice.suppress]
    @property
    def moderators(self) -> List[Member]:
        required_permissions = Permissions.stage_moderator()
        return [member for member in self.members if self.permissions_for(member) >= required_permissions]
    @property
    def type(self) -> ChannelType:
        return ChannelType.stage_voice
    @utils.copy_doc(discord.abc.GuildChannel.clone)
    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> StageChannel:
        return await self._clone_impl({}, name=name, reason=reason)
    @property
    def instance(self) -> Optional[StageInstance]:
        return utils.get(self.guild.stage_instances, channel_id=self.id)
    async def create_instance(
        self,
        *,
        topic: str,
        privacy_level: PrivacyLevel = MISSING,
        send_start_notification: bool = False,
        reason: Optional[str] = None,
    ) -> StageInstance:
        payload = {'channel_id': self.id, 'topic': topic, 'send_start_notification': send_start_notification}
        if privacy_level is not MISSING:
            if not isinstance(privacy_level, PrivacyLevel):
                raise TypeError('privacy_level field must be of type PrivacyLevel')
            payload['privacy_level'] = privacy_level.value
        data = await self.state.http.create_stage_instance(**payload, reason=reason)
        return StageInstance(guild=self.guild, state=self.state, data=data)
    async def fetch_instance(self) -> StageInstance:
        data = await self.state.http.get_stage_instance(self.id)
        return StageInstance(guild=self.guild, state=self.state, data=data)
    @overload
    async def edit(self) -> None:
        ...
    @overload
    async def edit(self, *, position: int, reason: Optional[str] = ...) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        nsfw: bool = ...,
        user_limit: int = ...,
        position: int = ...,
        sync_permissions: int = ...,
        category: Optional[CategoryChannel] = ...,
        overwrites: Mapping[OverwriteKeyT, PermissionOverwrite] = ...,
        rtc_region: Optional[str] = ...,
        video_quality_mode: VideoQualityMode = ...,
        slowmode_delay: int = ...,
        reason: Optional[str] = ...,
    ) -> StageChannel:
        ...
    async def edit(self, *, reason: Optional[str] = None, **options: Any) -> Optional[StageChannel]:
        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return self.__class__(state=self.state, guild=self.guild, data=payload)
class CategoryChannel(discord.abc.GuildChannel, Hashable):
    __slots__ = ('name', 'id', 'guild', 'nsfw', 'state', 'position', '_overwrites', 'category_id')
    def __init__(self, *, state: ConnectionState, guild: Guild, data: CategoryChannelPayload):
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(guild, data)
    def __repr__(self) -> str:
        return f'<CategoryChannel id={self.id} name={self.name!r} position={self.position} nsfw={self.nsfw}>'
    def _update(self, guild: Guild, data: CategoryChannelPayload) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.nsfw: bool = data.get('nsfw', False)
        self.position: int = data['position']
        self._fill_overwrites(data)
    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.category.value
    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return None
    @property
    def type(self) -> ChannelType:
        return ChannelType.category
    def is_nsfw(self) -> bool:
        return self.nsfw
    @utils.copy_doc(discord.abc.GuildChannel.clone)
    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> CategoryChannel:
        return await self._clone_impl({'nsfw': self.nsfw}, name=name, reason=reason)
    @overload
    async def edit(self) -> None:
        ...
    @overload
    async def edit(self, *, position: int, reason: Optional[str] = ...) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        position: int = ...,
        nsfw: bool = ...,
        overwrites: Mapping[OverwriteKeyT, PermissionOverwrite] = ...,
        reason: Optional[str] = ...,
    ) -> CategoryChannel:
        ...
    async def edit(self, *, reason: Optional[str] = None, **options: Any) -> Optional[CategoryChannel]:
        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return self.__class__(state=self.state, guild=self.guild, data=payload)
    @utils.copy_doc(discord.abc.GuildChannel.move)
    async def move(self, **kwargs: Any) -> None:
        kwargs.pop('category', None)
        await super().move(**kwargs)
    @property
    def channels(self) -> List[GuildChannelType]:
        def comparator(channel):
            return (not isinstance(channel, TextChannel), channel.position)
        ret = [c for c in self.guild.channels if c.category_id == self.id]
        ret.sort(key=comparator)
        return ret
    @property
    def text_channels(self) -> List[TextChannel]:
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, TextChannel)]
        ret.sort(key=attrgetter('position', 'id'))
        return ret
    @property
    def voice_channels(self) -> List[VoiceChannel]:
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, VoiceChannel)]
        ret.sort(key=attrgetter('position', 'id'))
        return ret
    @property
    def stage_channels(self) -> List[StageChannel]:
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, StageChannel)]
        ret.sort(key=attrgetter('position', 'id'))
        return ret
    @property
    def forums(self) -> List[ForumChannel]:
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, ForumChannel)]
        ret.sort(key=attrgetter('position', 'id'))
        return ret
    @property
    def directory_channels(self) -> List[DirectoryChannel]:
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, DirectoryChannel)]
        ret.sort(key=attrgetter('position', 'id'))
        return ret
    @property
    def directories(self) -> List[DirectoryChannel]:
        return self.directory_channels
    async def create_text_channel(self, name: str, **options: Any) -> TextChannel:
        return await self.guild.create_text_channel(name, category=self, **options)
    async def create_voice_channel(self, name: str, **options: Any) -> VoiceChannel:
        return await self.guild.create_voice_channel(name, category=self, **options)
    async def create_stage_channel(self, name: str, **options: Any) -> StageChannel:
        return await self.guild.create_stage_channel(name, category=self, **options)
    async def create_directory(self, name: str, **options: Any) -> DirectoryChannel:
        return await self.guild.create_directory(name, category=self, **options)
    create_directory_channel = create_directory
    async def create_forum(self, name: str, **options: Any) -> ForumChannel:
        return await self.guild.create_forum(name, category=self, **options)
    create_forum_channel = create_forum
class ForumTag(Hashable):
    __slots__ = ('name', 'id', 'moderated', 'emoji', 'state', '_channel_id')
    def __init__(self, *, name: str, emoji: Optional[EmojiInputType] = None, moderated: bool = False) -> None:
        self.state = None
        self._channel_id: Optional[int] = None
        self.name: str = name
        self.id: int = 0
        self.moderated: bool = moderated
        self.emoji: Optional[PartialEmoji] = None
        if isinstance(emoji, _EmojiTag):
            self.emoji = emoji._to_partial()
            if not self.state and emoji.state:
                self.state = emoji.state
        elif isinstance(emoji, str):
            self.emoji = PartialEmoji.from_str(emoji)
        elif emoji is not None:
            raise TypeError(f'emoji must be a Emoji, PartialEmoji, str or None not {emoji.__class__.__name__}')
    @classmethod
    def from_data(cls, *, state: ConnectionState, data: ForumTagPayload, channel_id: int) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self._channel_id = channel_id
        self.name = data['name']
        self.id = int(data['id'])
        self.moderated = data.get('moderated', False)
        emoji_name = data['emoji_name'] or ''
        emoji_id = utils._get_as_snowflake(data, 'emoji_id') or None
        if not emoji_name and not emoji_id:
            self.emoji = None
        else:
            self.emoji = PartialEmoji.with_state(state=state, name=emoji_name, id=emoji_id)
        return self
    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            'name': self.name,
            'moderated': self.moderated,
        }
        if self.emoji is not None:
            payload.update(self.emoji._to_forum_tag_payload())
        else:
            payload.update(emoji_id=None, emoji_name=None)
        if self.id:
            payload['id'] = self.id
        return payload
    def __repr__(self) -> str:
        return f'<ForumTag id={self.id} name={self.name!r} emoji={self.emoji!r} moderated={self.moderated}>'
    def __str__(self) -> str:
        return self.name
    async def edit(
        self,
        *,
        name: str = MISSING,
        emoji: Optional[PartialEmoji] = MISSING,
        moderated: bool = MISSING,
        reason: Optional[str] = None,
    ) -> ForumTag:
        if not self.state or not self._channel_id:
            raise DiscordException('Invalid state (no ConnectionState provided)')
        result = ForumTag(
            name=name or self.name,
            emoji=emoji if emoji is not MISSING else self.emoji,
            moderated=moderated if moderated is not MISSING else self.moderated,
        )
        result.state = self.state
        result._channel_id = self._channel_id
        await self.state.http.edit_forum_tag(self._channel_id, self.id, **result.to_dict(), reason=reason)
        result.id = self.id
        return result
    async def delete(self) -> None:
        if not self.state or not self._channel_id:
            raise DiscordException('Invalid state (no ConnectionState provided)')
        await self.state.http.delete_forum_tag(self._channel_id, self.id)
class ForumChannel(discord.abc.GuildChannel, Hashable):
    __slots__ = (
        'name',
        'id',
        'guild',
        'topic',
        'state',
        '_flags',
        'nsfw',
        'category_id',
        'position',
        'slowmode_delay',
        '_overwrites',
        'last_message_id',
        'default_auto_archive_duration',
        'default_thread_slowmode_delay',
        'default_reaction_emoji',
        'default_layout',
        'default_sort_order',
        '_available_tags',
        '_flags',
    )
    def __init__(self, *, state: ConnectionState, guild: Guild, data: ForumChannelPayload):
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(guild, data)
    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('nsfw', self.nsfw),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'
    def _update(self, guild: Guild, data: ForumChannelPayload) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.topic: Optional[str] = data.get('topic')
        self.position: int = data['position']
        self.nsfw: bool = data.get('nsfw', False)
        self.slowmode_delay: int = data.get('rate_limit_per_user', 0)
        self.default_auto_archive_duration: ThreadArchiveDuration = data.get('default_auto_archive_duration', 1440)
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        tags = [
            ForumTag.from_data(state=self.state, data=tag, channel_id=self.id) for tag in data.get('available_tags', [])
        ]
        self.default_thread_slowmode_delay: int = data.get('default_thread_rate_limit_per_user', 0)
        self.default_layout: ForumLayoutType = try_enum(ForumLayoutType, data.get('default_forum_layout', 0))
        self._available_tags: Dict[int, ForumTag] = {tag.id: tag for tag in tags}
        self.default_reaction_emoji: Optional[PartialEmoji] = None
        default_reaction_emoji = data.get('default_reaction_emoji')
        if default_reaction_emoji:
            self.default_reaction_emoji = PartialEmoji.with_state(
                state=self.state,
                id=utils._get_as_snowflake(default_reaction_emoji, 'emoji_id') or None,
                name=default_reaction_emoji.get('emoji_name') or '',
            )
        self.default_sort_order: Optional[ForumOrderType] = None
        default_sort_order = data.get('default_sort_order')
        if default_sort_order is not None:
            self.default_sort_order = try_enum(ForumOrderType, default_sort_order)
        self._flags: int = data.get('flags', 0)
        self._fill_overwrites(data)
    @property
    def type(self) -> ChannelType:
        return ChannelType.forum
    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.text.value
    @utils.copy_doc(discord.abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)
        self._apply_implicit_permissions(base)
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base
    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        thread = self.guild.get_thread(thread_id)
        if thread is not None and thread.parent_id == self.id:
            return thread
        return None
    @property
    def threads(self) -> List[Thread]:
        return [thread for thread in self.guild._threads.values() if thread.parent_id == self.id]
    @property
    def flags(self) -> ChannelFlags:
        return ChannelFlags._from_value(self._flags)
    @property
    def available_tags(self) -> Sequence[ForumTag]:
        return utils.SequenceProxy(self._available_tags.values())
    def get_tag(self, tag_id: int, /) -> Optional[ForumTag]:
        return self._available_tags.get(tag_id)
    def is_nsfw(self) -> bool:
        return self.nsfw
    @utils.copy_doc(discord.abc.GuildChannel.clone)
    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> ForumChannel:
        return await self._clone_impl(
            {'topic': self.topic, 'nsfw': self.nsfw, 'rate_limit_per_user': self.slowmode_delay}, name=name, reason=reason
        )
    @overload
    async def edit(self) -> None:
        ...
    @overload
    async def edit(self, *, position: int, reason: Optional[str] = ...) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        topic: str = ...,
        position: int = ...,
        nsfw: bool = ...,
        sync_permissions: bool = ...,
        category: Optional[CategoryChannel] = ...,
        slowmode_delay: int = ...,
        default_auto_archive_duration: ThreadArchiveDuration = ...,
        type: ChannelType = ...,
        overwrites: Mapping[OverwriteKeyT, PermissionOverwrite] = ...,
        available_tags: Sequence[ForumTag] = ...,
        default_thread_slowmode_delay: int = ...,
        default_reaction_emoji: Optional[EmojiInputType] = ...,
        default_layout: ForumLayoutType = ...,
        default_sort_order: ForumOrderType = ...,
        require_tag: bool = ...,
    ) -> ForumChannel:
        ...
    async def edit(self, *, reason: Optional[str] = None, **options: Any) -> Optional[ForumChannel]:
        try:
            tags: Sequence[ForumTag] = options.pop('available_tags')
        except KeyError:
            pass
        else:
            options['available_tags'] = [tag.to_dict() for tag in tags]
        try:
            default_reaction_emoji: Optional[EmojiInputType] = options.pop('default_reaction_emoji')
        except KeyError:
            pass
        else:
            if default_reaction_emoji is None:
                options['default_reaction_emoji'] = None
            elif isinstance(default_reaction_emoji, _EmojiTag):
                options['default_reaction_emoji'] = default_reaction_emoji._to_partial()._to_forum_tag_payload()
            elif isinstance(default_reaction_emoji, str):
                options['default_reaction_emoji'] = PartialEmoji.from_str(default_reaction_emoji)._to_forum_tag_payload()
        try:
            require_tag = options.pop('require_tag')
        except KeyError:
            pass
        else:
            flags = self.flags
            flags.require_tag = require_tag
            options['flags'] = flags.value
        try:
            layout = options.pop('default_layout')
        except KeyError:
            pass
        else:
            if not isinstance(layout, ForumLayoutType):
                raise TypeError(f'default_layout parameter must be a ForumLayoutType not {layout.__class__.__name__}')
            options['default_forum_layout'] = layout.value
        try:
            sort_order = options.pop('default_sort_order')
        except KeyError:
            pass
        else:
            if sort_order is None:
                options['default_sort_order'] = None
            else:
                if not isinstance(sort_order, ForumOrderType):
                    raise TypeError(
                        f'default_sort_order parameter must be a ForumOrderType not {sort_order.__class__.__name__}'
                    )
                options['default_sort_order'] = sort_order.value
        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return self.__class__(state=self.state, guild=self.guild, data=payload)
    async def create_tag(
        self,
        *,
        name: str,
        emoji: PartialEmoji,
        moderated: bool = False,
        reason: Optional[str] = None,
    ) -> ForumTag:
        result = ForumTag(name=name, emoji=emoji, moderated=moderated)
        result.state = self.state
        result._channel_id = self.id
        payload = await self.state.http.create_forum_tag(self.id, **result.to_dict(), reason=reason)
        try:
            result.id = int(payload['available_tags'][-1]['id'])
        except (KeyError, IndexError, ValueError):
            pass
        return result
    async def create_thread(
        self,
        *,
        name: str,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        slowmode_delay: Optional[int] = None,
        content: Optional[str] = None,
        tts: bool = False,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        mention_author: bool = MISSING,
        applied_tags: Sequence[ForumTag] = MISSING,
        suppress_embeds: bool = False,
        reason: Optional[str] = None,
    ) -> ThreadWithMessage:
        state = self.state
        previous_allowed_mention = state.allowed_mentions
        if stickers is MISSING:
            sticker_ids = MISSING
        else:
            sticker_ids: SnowflakeList = [s.id for s in stickers]
        if suppress_embeds:
            flags = MessageFlags._from_value(4)
        else:
            flags = MISSING
        content = str(content) if content else MISSING
        channel_payload = {
            'name': name,
            'auto_archive_duration': auto_archive_duration or self.default_auto_archive_duration,
            'rate_limit_per_user': slowmode_delay,
            'type': 11,
        }
        if applied_tags is not MISSING:
            channel_payload['applied_tags'] = [str(tag.id) for tag in applied_tags]
        with handle_message_parameters(
            content=content,
            tts=tts,
            file=file,
            files=files,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=None if mention_author is MISSING else mention_author,
            stickers=sticker_ids,
            flags=flags,
            channel_payload=channel_payload,
        ) as params:
            data = await state.http.start_thread_in_forum(self.id, params=params, reason=reason)
            thread = Thread(guild=self.guild, state=self.state, data=data)
            message = state.create_message(channel=thread, data=data['message'])
            return ThreadWithMessage(thread=thread, message=message)
    async def webhooks(self) -> List[Webhook]:
        from .webhook import Webhook
        data = await self.state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self.state) for d in data]
    async def create_webhook(self, *, name: str, avatar: Optional[bytes] = None, reason: Optional[str] = None) -> Webhook:
        from .webhook import Webhook
        if avatar is not None:
            avatar = utils._bytes_to_base64_data(avatar)
        data = await self.state.http.create_webhook(self.id, name=str(name), avatar=avatar, reason=reason)
        return Webhook.from_state(data, state=self.state)
    async def archived_threads(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
    ) -> AsyncIterator[Thread]:
        before_timestamp = None
        if isinstance(before, datetime.datetime):
            before_timestamp = before.isoformat()
        elif before is not None:
            before_timestamp = utils.snowflake_time(before.id).isoformat()
        update_before = lambda data: data['thread_metadata']['archive_timestamp']
        while True:
            retrieve = 100
            if limit is not None:
                if limit <= 0:
                    return
                retrieve = max(2, min(retrieve, limit))
            data = await self.guild.state.http.get_public_archived_threads(self.id, before=before_timestamp, limit=retrieve)
            threads = data.get('threads', [])
            for raw_thread in threads:
                yield Thread(guild=self.guild, state=self.guild.state, data=raw_thread)
                if limit is not None:
                    limit -= 1
                    if limit <= 0:
                        return
            if not data.get('has_more', False):
                return
            before_timestamp = update_before(threads[-1])
class DirectoryChannel(discord.abc.GuildChannel, Hashable):
    __slots__ = (
        'name',
        'id',
        'guild',
        'topic',
        'state',
        'category_id',
        'position',
        '_overwrites',
        'last_message_id',
    )
    def __init__(self, *, state: ConnectionState, guild: Guild, data: DirectoryChannelPayload):
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(guild, data)
    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'
    def _update(self, guild: Guild, data: DirectoryChannelPayload) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.topic: Optional[str] = data.get('topic')
        self.position: int = data['position']
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self._fill_overwrites(data)
    async def _get_channel(self) -> Self:
        return self
    @property
    def type(self) -> ChannelType:
        return ChannelType.directory
    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.directory.value
    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return None
    @utils.copy_doc(discord.abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)
        self._apply_implicit_permissions(base)
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base
    @property
    def members(self) -> List[Member]:
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]
    @property
    def read_state(self) -> ReadState:
        return self.state.get_read_state(self.id)
    @property
    def acked_message_id(self) -> int:
        return self.read_state.last_acked_id
    @property
    def mention_count(self) -> int:
        return self.read_state.badge_count
    @property
    def last_viewed_timestamp(self) -> datetime.date:
        return self.read_state.last_viewed
    @overload
    async def edit(self) -> Optional[DirectoryChannel]:
        ...
    @overload
    async def edit(self, *, position: int, reason: Optional[str] = ...) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        topic: str = ...,
        position: int = ...,
        sync_permissions: bool = ...,
        category: Optional[CategoryChannel] = ...,
        overwrites: Mapping[OverwriteKeyT, PermissionOverwrite] = ...,
    ) -> DirectoryChannel:
        ...
    async def edit(self, *, reason: Optional[str] = None, **options: Any) -> Optional[DirectoryChannel]:
        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return self.__class__(state=self.state, guild=self.guild, data=payload)
    @utils.copy_doc(discord.abc.GuildChannel.clone)
    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> DirectoryChannel:
        return await self._clone_impl({'topic': self.topic}, name=name, reason=reason)
    async def counts(self) -> Dict[DirectoryCategory, int]:
        data = await self.state.http.get_directory_counts(self.id)
        return {try_enum(DirectoryCategory, int(k)): v for k, v in data.items()}
    async def entries(
        self,
        *,
        type: Optional[DirectoryEntryType] = None,
        category: Optional[DirectoryCategory] = None,
    ) -> List[DirectoryEntry]:
        state = self.state
        data = await state.http.get_directory_entries(
            self.id, type=type.value if type else None, category_id=category.value if category else None
        )
        return [DirectoryEntry(state=state, data=e, channel=self) for e in data]
    async def fetch_entries(self, *entity_ids: int) -> List[DirectoryEntry]:
        r
        if not entity_ids:
            return []
        state = self.state
        data = await state.http.get_some_directory_entries(self.id, entity_ids)
        return [DirectoryEntry(state=state, data=e, channel=self) for e in data]
    async def search_entries(
        self,
        query: str,
        /,
        *,
        category: Optional[DirectoryCategory] = None,
    ) -> List[DirectoryEntry]:
        state = self.state
        data = await state.http.search_directory_entries(self.id, query, category_id=category.value if category else None)
        return [DirectoryEntry(state=state, data=e, channel=self) for e in data]
    async def create_entry(
        self,
        guild: Snowflake,
        *,
        category: DirectoryCategory = DirectoryCategory.uncategorized,
        description: Optional[str] = None,
    ) -> DirectoryEntry:
        state = self.state
        data = await state.http.create_directory_entry(
            self.id,
            guild.id,
            primary_category_id=(category or DirectoryCategory.uncategorized).value,
            description=description or '',
        )
        return DirectoryEntry(state=state, data=data, channel=self)
class DMChannel(discord.abc.Messageable, discord.abc.Connectable, discord.abc.PrivateChannel, Hashable):
    __slots__ = (
        'id',
        'recipient',
        'me',
        'last_message_id',
        'last_pin_timestamp',
        '_message_request',
        '_requested_at',
        '_spam',
        'state',
    )
    def __init__(self, *, me: ClientUser, state: ConnectionState, data: DMChannelPayload):
        self.state: ConnectionState = state
        self.recipient: User = state.store_user(data['recipients'][0])
        self.me: ClientUser = me
        self.id: int = int(data['id'])
        self._update(data)
    def _update(self, data: DMChannelPayload) -> None:
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('last_pin_timestamp'))
        self._message_request: Optional[bool] = data.get('is_message_request')
        self._requested_at: Optional[datetime.datetime] = utils.parse_time(data.get('is_message_request_timestamp'))
        self._spam: bool = data.get('is_spam', False)
    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.me.id, 'self_id'
    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.me.id, self.id
    def _add_call(self, **kwargs) -> PrivateCall:
        return PrivateCall(**kwargs)
    async def _get_channel(self) -> Self:
        return self
    async def _initial_ring(self) -> None:
        ring = self.recipient.is_friend()
        if not ring:
            data = await self.state.http.get_ringability(self.id)
            ring = data['ringable']
        if ring:
            await self.state.http.ring(self.id)
    def __str__(self) -> str:
        if self.recipient:
            return f'Direct Message with {self.recipient}'
        return 'Direct Message with Unknown User'
    def __repr__(self) -> str:
        return f'<DMChannel id={self.id} recipient={self.recipient!r}>'
    @property
    def notification_settings(self) -> ChannelSettings:
        state = self.state
        return state.client.notification_settings._channel_overrides.get(
            self.id, state.default_channel_settings(None, self.id)
        )
    @property
    def call(self) -> Optional[PrivateCall]:
        return self.state._calls.get(self.id)
    @property
    def type(self) -> ChannelType:
        return ChannelType.private
    @property
    def created_at(self) -> datetime.datetime:
        return utils.snowflake_time(self.id)
    @property
    def guild(self) -> Optional[Guild]:
        return None
    @property
    def jump_url(self) -> str:
        return f'https://discord.com/channels/@me/{self.id}'
    @property
    def read_state(self) -> ReadState:
        return self.state.get_read_state(self.id)
    @property
    def last_message(self) -> Optional[Message]:
        return self.state._get_message(self.last_message_id) if self.last_message_id else None
    @property
    def acked_message_id(self) -> int:
        return self.read_state.last_acked_id
    @property
    def acked_message(self) -> Optional[Message]:
        acked_message_id = self.acked_message_id
        if acked_message_id is None:
            return
        message = self.state._get_message(acked_message_id)
        if message and message.channel.id == self.id:
            return message
    @property
    def acked_pin_timestamp(self) -> Optional[datetime.datetime]:
        return self.read_state.last_pin_timestamp
    @property
    def mention_count(self) -> int:
        return self.read_state.badge_count
    @property
    def last_viewed_timestamp(self) -> datetime.date:
        return self.read_state.last_viewed
    @property
    def requested_at(self) -> Optional[datetime.datetime]:
        return self._requested_at
    def is_message_request(self) -> bool:
        return self._message_request is not None
    def is_accepted(self) -> bool:
        return not self._message_request if self._message_request is not None else True
    def is_spam(self) -> bool:
        return self._spam
    def permissions_for(self, obj: Any = None, /) -> Permissions:
        return Permissions._dm_permissions()
    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        from .message import PartialMessage
        return PartialMessage(channel=self, id=message_id)
    async def close(self):
        await self.state.http.delete_channel(self.id, silent=False)
    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, discord.abc.VocalChannel], T] = VoiceClient,
        ring: bool = True,
    ) -> T:
        await self._get_channel()
        call = self.call
        if call is None and ring:
            await self._initial_ring()
        return await super().connect(timeout=timeout, reconnect=reconnect, cls=cls)
    async def accept(self) -> DMChannel:
        data = await self.state.http.accept_message_request(self.id)
        data['is_message_request'] = False
        if self._requested_at:
            data['is_message_request_timestamp'] = self._requested_at.isoformat()
        data['is_spam'] = self._spam
        return DMChannel(state=self.state, data=data, me=self.me)
    async def decline(self) -> None:
        await self.state.http.decline_message_request(self.id)
class GroupChannel(discord.abc.Messageable, discord.abc.Connectable, discord.abc.PrivateChannel, Hashable):
    __slots__ = (
        'last_message_id',
        'last_pin_timestamp',
        'id',
        'recipients',
        'owner_id',
        'managed',
        'application_id',
        'nicks',
        '_icon',
        'name',
        'me',
        'state',
    )
    def __init__(self, *, me: ClientUser, state: ConnectionState, data: GroupChannelPayload):
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self.me: ClientUser = me
        self._update(data)
    def _update(self, data: GroupChannelPayload) -> None:
        self.owner_id: int = int(data['owner_id'])
        self._icon: Optional[str] = data.get('icon')
        self.name: Optional[str] = data.get('name')
        self.recipients: List[User] = [self.state.store_user(u) for u in data.get('recipients', [])]
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('last_pin_timestamp'))
        self.managed: bool = data.get('managed', False)
        self.application_id: Optional[int] = utils._get_as_snowflake(data, 'application_id')
        self.nicks: Dict[User, str] = {utils.get(self.recipients, id=int(k)): v for k, v in data.get('nicks', {}).items()}
    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.me.id, 'self_id'
    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.me.id, self.id
    async def _get_channel(self) -> Self:
        return self
    def _initial_ring(self):
        return self.state.http.ring(self.id)
    def _add_call(self, **kwargs) -> GroupCall:
        return GroupCall(**kwargs)
    def __str__(self) -> str:
        if self.name:
            return self.name
        recipients = [x for x in self.recipients if x.id != self.me.id]
        if len(recipients) == 0:
            return 'Unnamed'
        return ', '.join(map(lambda x: x.name, recipients))
    def __repr__(self) -> str:
        return f'<GroupChannel id={self.id} name={self.name!r}>'
    @property
    def notification_settings(self) -> ChannelSettings:
        state = self.state
        return state.client.notification_settings._channel_overrides.get(
            self.id, state.default_channel_settings(None, self.id)
        )
    @property
    def owner(self) -> Optional[User]:
        return utils.get(self.recipients, id=self.owner_id) or self.state.get_user(self.owner_id)
    @property
    def call(self) -> Optional[PrivateCall]:
        return self.state._calls.get(self.id)
    @property
    def type(self) -> ChannelType:
        return ChannelType.group
    @property
    def guild(self) -> Optional[Guild]:
        return None
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='channel')
    @property
    def created_at(self) -> datetime.datetime:
        return utils.snowflake_time(self.id)
    @property
    def jump_url(self) -> str:
        return f'https://discord.com/channels/@me/{self.id}'
    @property
    def read_state(self) -> ReadState:
        return self.state.get_read_state(self.id)
    @property
    def last_message(self) -> Optional[Message]:
        return self.state._get_message(self.last_message_id) if self.last_message_id else None
    @property
    def acked_message_id(self) -> int:
        return self.read_state.last_acked_id
    @property
    def acked_message(self) -> Optional[Message]:
        acked_message_id = self.acked_message_id
        if acked_message_id is None:
            return
        message = self.state._get_message(acked_message_id)
        if message and message.channel.id == self.id:
            return message
    @property
    def acked_pin_timestamp(self) -> Optional[datetime.datetime]:
        return self.read_state.last_pin_timestamp
    @property
    def mention_count(self) -> int:
        return self.read_state.badge_count
    @property
    def last_viewed_timestamp(self) -> datetime.date:
        return self.read_state.last_viewed
    def permissions_for(self, obj: Snowflake, /) -> Permissions:
        if obj.id in [x.id for x in self.recipients]:
            base = Permissions._dm_permissions()
            base.mention_everyone = True
            if not self.managed:
                base.create_instant_invite = True
        else:
            base = Permissions.none()
        if obj.id == self.owner_id:
            base.kick_members = True
        return base
    async def add_recipients(self, *recipients: Snowflake, nicks: Optional[Dict[Snowflake, str]] = None) -> None:
        r
        nicknames = {k.id: v for k, v in nicks.items()} if nicks else {}
        await self._get_channel()
        req = self.state.http.add_group_recipient
        for recipient in recipients:
            await req(self.id, recipient.id, getattr(recipient, 'nick', (nicknames.get(recipient.id) if nicks else None)))
    async def remove_recipients(self, *recipients: Snowflake) -> None:
        r
        await self._get_channel()
        req = self.state.http.remove_group_recipient
        for recipient in recipients:
            await req(self.id, recipient.id)
    async def edit(
        self,
        *,
        name: Optional[str] = MISSING,
        icon: Optional[bytes] = MISSING,
        owner: Snowflake = MISSING,
    ) -> GroupChannel:
        await self._get_channel()
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if icon is not MISSING:
            if icon is None:
                payload['icon'] = None
            else:
                payload['icon'] = utils._bytes_to_base64_data(icon)
        if owner:
            payload['owner'] = owner.id
        data = await self.state.http.edit_channel(self.id, **payload)
        return self.__class__(me=self.me, state=self.state, data=data)
    async def leave(self, *, silent: bool = False) -> None:
        await self.state.http.delete_channel(self.id, silent=silent)
    async def close(self, *, silent: bool = False) -> None:
        await self.leave(silent=silent)
    async def invites(self) -> List[Invite]:
        state = self.state
        data = await state.http.invites_from_channel(self.id)
        return [Invite(state=state, data=invite, channel=self) for invite in data]
    async def create_invite(self, *, max_age: int = 86400) -> Invite:
        data = await self.state.http.create_group_invite(self.id, max_age=max_age)
        return Invite.from_incomplete(data=data, state=self.state)
    @utils.copy_doc(DMChannel.connect)
    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, discord.abc.VocalChannel], T] = VoiceClient,
        ring: bool = True,
    ) -> T:
        await self._get_channel()
        call = self.call
        if call is None and ring:
            await self._initial_ring()
        return await super().connect(timeout=timeout, reconnect=reconnect, cls=cls)
class PartialMessageable(discord.abc.Messageable, Hashable):
    def __init__(
        self,
        *,
        state: ConnectionState,
        id: int,
        guild_id: Optional[int] = None,
        type: Optional[ChannelType] = None,
        name: Optional[str] = None,
    ):
        self.state: ConnectionState = state
        self.id: int = id
        self.guild_id: Optional[int] = guild_id
        self.type: Optional[ChannelType] = type
        self.name: Optional[str] = name
        self.last_message_id: Optional[int] = None
        self.last_pin_timestamp: Optional[datetime.datetime] = None
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} type={self.type!r}>'
    async def _get_channel(self) -> PartialMessageable:
        return self
    @classmethod
    def _from_webhook_channel(cls, guild: Guild, channel: WebhookChannelPayload) -> Self:
        return cls(
            state=guild.state,
            id=int(channel['id']),
            guild_id=guild.id,
            name=channel['name'],
        )
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    @property
    def jump_url(self) -> str:
        if self.guild_id is None:
            return f'https://discord.com/channels/@me/{self.id}'
        return f'https://discord.com/channels/{self.guild_id}/{self.id}'
    @property
    def created_at(self) -> datetime.datetime:
        return utils.snowflake_time(self.id)
    @property
    def read_state(self) -> ReadState:
        return self.state.get_read_state(self.id)
    def permissions_for(self, obj: Any = None, /) -> Permissions:
        return Permissions.none()
    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        from .message import PartialMessage
        return PartialMessage(channel=self, id=message_id)
def _guild_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.category:
        return CategoryChannel, value
    elif value is ChannelType.news:
        return TextChannel, value
    elif value is ChannelType.stage_voice:
        return StageChannel, value
    elif value is ChannelType.directory:
        return DirectoryChannel, value
    elif value is ChannelType.forum:
        return ForumChannel, value
    else:
        return None, value
def _private_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    else:
        return None, value
def _channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if cls is None:
        cls, value = _private_channel_factory(channel_type)
    return cls, value
def _threaded_channel_factory(channel_type: int):
    cls, value = _channel_factory(channel_type)
    if value in (ChannelType.private_thread, ChannelType.public_thread, ChannelType.news_thread):
        return Thread, value
    return cls, value
def _threaded_guild_channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if value in (ChannelType.private_thread, ChannelType.public_thread, ChannelType.news_thread):
        return Thread, value
    return cls, value