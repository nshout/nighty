from __future__ import annotations
import copy
from datetime import datetime
from operator import attrgetter
import unicodedata
from typing import (
    Any,
    AsyncIterator,
    ClassVar,
    Collection,
    Coroutine,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Sequence,
    Set,
    Literal,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Union,
    overload,
)
import warnings
from . import utils, abc
from .role import Role
from .member import Member, VoiceState
from .emoji import Emoji
from .errors import ClientException, InvalidData
from .permissions import PermissionOverwrite
from .colour import Colour
from .errors import ClientException
from .channel import *
from .channel import _guild_channel_factory, _threaded_guild_channel_factory
from .enums import (
    AuditLogAction,
    VideoQualityMode,
    ChannelType,
    EntityType,
    HubType,
    PrivacyLevel,
    try_enum,
    VerificationLevel,
    ContentFilter,
    NotificationLevel,
    NSFWLevel,
    MFALevel,
    Locale,
    AutoModRuleEventType,
    ForumOrderType,
    ForumLayoutType,
    ReadStateType,
)
from .mixins import Hashable
from .user import User
from .invite import Invite
from .widget import Widget
from .asset import Asset
from .flags import SystemChannelFlags
from .integrations import Integration, _integration_factory
from .scheduled_event import ScheduledEvent
from .stage_instance import StageInstance
from .threads import Thread
from .sticker import GuildSticker
from .file import File
from .audit_logs import AuditLogEntry
from .object import OLDEST_OBJECT, Object
from .profile import MemberProfile
from .partial_emoji import PartialEmoji
from .welcome_screen import *
from .application import PartialApplication
from .guild_premium import PremiumGuildSubscription
from .entitlements import Entitlement
from .automod import AutoModRule, AutoModTrigger, AutoModRuleAction
from .partial_emoji import _EmojiTag, PartialEmoji
from .commands import _command_factory
if TYPE_CHECKING:
    from .abc import Snowflake, SnowflakeTime
    from .types.guild import (
        BaseGuild as BaseGuildPayload,
        Guild as GuildPayload,
        RolePositionUpdate as RolePositionUpdatePayload,
        UserGuild as UserGuildPayload,
    )
    from .types.threads import (
        Thread as ThreadPayload,
    )
    from .types.voice import BaseVoiceState as VoiceStatePayload
    from .permissions import Permissions
    from .channel import VoiceChannel, StageChannel, TextChannel, ForumChannel, CategoryChannel
    from .template import Template
    from .webhook import Webhook
    from .state import ConnectionState
    from .voice_client import VoiceProtocol
    from .settings import GuildSettings
    from .enums import ApplicationType
    from .types.channel import (
        GuildChannel as GuildChannelPayload,
        TextChannel as TextChannelPayload,
        NewsChannel as NewsChannelPayload,
        VoiceChannel as VoiceChannelPayload,
        CategoryChannel as CategoryChannelPayload,
        StageChannel as StageChannelPayload,
        ForumChannel as ForumChannelPayload,
        DirectoryChannel as DirectoryChannelPayload,
    )
    from .types.embed import EmbedType
    from .types.integration import IntegrationType
    from .types.message import MessageSearchAuthorType, MessageSearchHasType
    from .types.snowflake import SnowflakeList
    from .types.widget import EditWidgetSettings
    from .types.audit_log import AuditLogEvent
    from .types.oauth2 import OAuth2Guild as OAuth2GuildPayload
    from .message import EmojiInputType, Message
    from .read_state import ReadState
    from .commands import UserCommand, MessageCommand, SlashCommand
    VocalGuildChannel = Union[VoiceChannel, StageChannel]
    NonCategoryChannel = Union[VocalGuildChannel, ForumChannel, TextChannel, DirectoryChannel]
    GuildChannel = Union[NonCategoryChannel, CategoryChannel]
    ByCategoryItem = Tuple[Optional[CategoryChannel], List[NonCategoryChannel]]
MISSING = utils.MISSING
__all__ = (
    'Guild',
    'UserGuild',
    'BanEntry',
)
class BanEntry(NamedTuple):
    reason: Optional[str]
    user: User
class _GuildLimit(NamedTuple):
    emoji: int
    stickers: int
    bitrate: float
    filesize: int
class UserGuild(Hashable):
    __slots__ = (
        'id',
        'name',
        '_icon',
        'owner',
        '_permissions',
        'mfa_level',
        'features',
        'approximate_member_count',
        'approximate_presence_count',
        'state',
    )
    def __init__(self, *, state: ConnectionState, data: Union[UserGuildPayload, OAuth2GuildPayload]):
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data.get('icon')
        self.owner: bool = data.get('owner', False)
        self._permissions: int = int(data.get('permissions', 0))
        self.mfa_level: MFALevel = try_enum(MFALevel, data.get('mfa_level', 0))
        self.features: List[str] = data.get('features', [])
        self.approximate_member_count: Optional[int] = data.get('approximate_member_count')
        self.approximate_presence_count: Optional[int] = data.get('approximate_presence_count')
    def __str__(self) -> str:
        return self.name or ''
    def __repr__(self) -> str:
        return f'<UserGuild id={self.id} name={self.name!r}>'
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self.state, self.id, self._icon)
    @property
    def permissions(self) -> Permissions:
        return Permissions(self._permissions)
    def is_joined(self) -> bool:
        return True
    async def leave(self) -> None:
        await self.state.http.leave_guild(self.id, lurking=False)
    async def delete(self) -> None:
        await self.state.http.delete_guild(self.id)
class Guild(Hashable):
    __slots__ = (
        'afk_timeout',
        'name',
        'id',
        'unavailable',
        'owner_id',
        'emojis',
        'stickers',
        'features',
        'verification_level',
        'explicit_content_filter',
        'default_notifications',
        'description',
        'max_presences',
        'max_members',
        'max_video_channel_users',
        '_premium_tier',
        'premium_subscription_count',
        'preferred_locale',
        'nsfw_level',
        'mfa_level',
        'vanity_url_code',
        'application_id',
        'widget_enabled',
        '_widget_channel_id',
        '_members',
        '_channels',
        '_icon',
        '_banner',
        'state',
        '_roles',
        '_member_count',
        '_large',
        '_splash',
        '_voice_states',
        '_afk_channel_id',
        '_system_channel_id',
        '_system_channel_flags',
        '_discovery_splash',
        '_rules_channel_id',
        '_public_updates_channel_id',
        '_stage_instances',
        '_scheduled_events',
        '_threads',
        'approximate_member_count',
        'approximate_presence_count',
        'premium_progress_bar_enabled',
        '_presence_count',
        '_true_online_count',
        '_member_list',
        'keywords',
        'primary_category_id',
        'hub_type',
        '_joined_at',
        '_cs_joined',
    )
    _PREMIUM_GUILD_LIMITS: ClassVar[Dict[Optional[int], _GuildLimit]] = {
        None: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=utils.DEFAULT_FILE_SIZE_LIMIT_BYTES),
        0: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=utils.DEFAULT_FILE_SIZE_LIMIT_BYTES),
        1: _GuildLimit(emoji=100, stickers=15, bitrate=128e3, filesize=utils.DEFAULT_FILE_SIZE_LIMIT_BYTES),
        2: _GuildLimit(emoji=150, stickers=30, bitrate=256e3, filesize=52428800),
        3: _GuildLimit(emoji=250, stickers=60, bitrate=384e3, filesize=104857600),
    }
    def __init__(self, *, data: Union[BaseGuildPayload, GuildPayload], state: ConnectionState) -> None:
        self._cs_joined: Optional[bool] = None
        self._roles: Dict[int, Role] = {}
        self._channels: Dict[int, GuildChannel] = {}
        self._members: Dict[int, Member] = {}
        self._member_list: List[Optional[Member]] = []
        self._voice_states: Dict[int, VoiceState] = {}
        self._threads: Dict[int, Thread] = {}
        self._stage_instances: Dict[int, StageInstance] = {}
        self._scheduled_events: Dict[int, ScheduledEvent] = {}
        self.state: ConnectionState = state
        self._member_count: Optional[int] = None
        self._presence_count: Optional[int] = None
        self._large: Optional[bool] = None
        self._from_data(data)
    def _add_channel(self, channel: GuildChannel, /) -> None:
        self._channels[channel.id] = channel
    def _remove_channel(self, channel: Snowflake, /) -> None:
        self._channels.pop(channel.id, None)
    def _voice_state_for(self, user_id: int, /) -> Optional[VoiceState]:
        return self._voice_states.get(user_id)
    def _add_member(self, member: Member, /) -> None:
        self._members[member.id] = member
        if member._presence:
            self.state.store_presence(member.id, member._presence, self.id)
            member._presence = None
    def _store_thread(self, payload: ThreadPayload, /) -> Thread:
        thread = Thread(guild=self, state=self.state, data=payload)
        self._threads[thread.id] = thread
        return thread
    def _remove_member(self, member: Snowflake, /) -> None:
        self._members.pop(member.id, None)
        self.state.remove_presence(member.id, self.id)
    def _add_thread(self, thread: Thread, /) -> None:
        self._threads[thread.id] = thread
    def _remove_thread(self, thread: Snowflake, /) -> None:
        self._threads.pop(thread.id, None)
    def _remove_threads_by_channel(self, channel_id: int) -> None:
        to_remove = [k for k, t in self._threads.items() if t.parent_id == channel_id]
        for k in to_remove:
            del self._threads[k]
    def _filter_threads(self, channel_ids: Set[int]) -> Dict[int, Thread]:
        return {k: t for k, t in self._threads.items() if t.parent_id in channel_ids}
    def __str__(self) -> str:
        return self.name or ''
    def __repr__(self) -> str:
        attrs = (
            ('id', self.id),
            ('name', self.name),
            ('chunked', self.chunked),
            ('member_count', self.member_count),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<Guild {inner}>'
    def _update_voice_state(
        self, data: VoiceStatePayload, channel_id: Optional[int]
    ) -> Tuple[Optional[Member], VoiceState, VoiceState]:
        cache_flags = self.state.member_cache_flags
        user_id = int(data['user_id'])
        channel: Optional[VocalGuildChannel] = self.get_channel(channel_id)
        try:
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]
            before = copy.copy(after)
            after._update(data, channel)
        except KeyError:
            after = VoiceState(data=data, channel=channel)
            before = VoiceState(data=data, channel=None)
            self._voice_states[user_id] = after
        member = self.get_member(user_id)
        if member is None:
            try:
                member = Member(data=data['member'], state=self.state, guild=self)
            except KeyError:
                member = None
            if member is not None and cache_flags.voice:
                self._add_member(member)
        return member, before, after
    def _add_role(self, role: Role, /) -> None:
        for r in self._roles.values():
            r.position += not r.is_default()
        self._roles[role.id] = role
    def _remove_role(self, role_id: int, /) -> Role:
        role = self._roles.pop(role_id)
        for r in self._roles.values():
            r.position -= r.position > role.position
        return role
    @classmethod
    def _create_unavailable(cls, *, state: ConnectionState, guild_id: int) -> Guild:
        return cls(state=state, data={'id': guild_id, 'unavailable': True})
    def _from_data(self, guild: Union[BaseGuildPayload, GuildPayload]) -> None:
        try:
            self._member_count: Optional[int] = guild['member_count']
        except KeyError:
            pass
        self.id: int = int(guild['id'])
        self.name: str = guild.get('name', '')
        self.verification_level: VerificationLevel = try_enum(VerificationLevel, guild.get('verification_level'))
        self.default_notifications: NotificationLevel = try_enum(
            NotificationLevel, guild.get('default_message_notifications')
        )
        self.explicit_content_filter: ContentFilter = try_enum(ContentFilter, guild.get('explicit_content_filter', 0))
        self.afk_timeout: int = guild.get('afk_timeout', 0)
        self.hub_type: Optional[HubType] = (
            try_enum(HubType, guild.get('hub_type')) if guild.get('hub_type') is not None else None
        )
        self.unavailable: bool = guild.get('unavailable', False)
        if self.unavailable:
            self._member_count = 0
        state = self.state
        for r in guild.get('roles', []):
            role = Role(guild=self, data=r, state=state)
            self._roles[role.id] = role
        for c in guild.get('channels', []):
            factory, _ = _guild_channel_factory(c['type'])
            if factory:
                self._add_channel(factory(guild=self, data=c, state=state))
        for t in guild.get('threads', []):
            self._add_thread(Thread(guild=self, state=self.state, data=t))
        for s in guild.get('stage_instances', []):
            stage_instance = StageInstance(guild=self, data=s, state=state)
            self._stage_instances[stage_instance.id] = stage_instance
        for s in guild.get('guild_scheduled_events', []):
            scheduled_event = ScheduledEvent(data=s, state=state)
            self._scheduled_events[scheduled_event.id] = scheduled_event
        self.emojis: Tuple[Emoji, ...] = tuple(map(lambda d: state.store_emoji(self, d), guild.get('emojis', [])))
        self.stickers: Tuple[GuildSticker, ...] = tuple(
            map(lambda d: state.store_sticker(self, d), guild.get('stickers', []))
        )
        self.features: List[str] = guild.get('features', [])
        self._icon: Optional[str] = guild.get('icon')
        self._banner: Optional[str] = guild.get('banner')
        self._splash: Optional[str] = guild.get('splash')
        self._system_channel_id: Optional[int] = utils._get_as_snowflake(guild, 'system_channel_id')
        self.description: Optional[str] = guild.get('description')
        self.max_presences: Optional[int] = guild.get('max_presences')
        self.max_members: Optional[int] = guild.get('max_members')
        self.max_video_channel_users: Optional[int] = guild.get('max_video_channel_users')
        self._premium_tier = guild.get('premium_tier')
        self.premium_subscription_count: int = guild.get('premium_subscription_count') or 0
        self.vanity_url_code: Optional[str] = guild.get('vanity_url_code')
        self.widget_enabled: bool = guild.get('widget_enabled', False)
        self._widget_channel_id: Optional[int] = utils._get_as_snowflake(guild, 'widget_channel_id')
        self._system_channel_flags: int = guild.get('system_channel_flags', 0)
        self.preferred_locale: Locale = try_enum(Locale, guild.get('preferred_locale', 'en-US'))
        self._discovery_splash: Optional[str] = guild.get('discovery_splash')
        self._rules_channel_id: Optional[int] = utils._get_as_snowflake(guild, 'rules_channel_id')
        self._public_updates_channel_id: Optional[int] = utils._get_as_snowflake(guild, 'public_updates_channel_id')
        self._afk_channel_id: Optional[int] = utils._get_as_snowflake(guild, 'afk_channel_id')
        self.nsfw_level: NSFWLevel = try_enum(NSFWLevel, guild.get('nsfw_level', 0))
        self.mfa_level: MFALevel = try_enum(MFALevel, guild.get('mfa_level', 0))
        self.approximate_presence_count: Optional[int] = guild.get('approximate_presence_count')
        self.approximate_member_count: Optional[int] = guild.get('approximate_member_count')
        self.owner_id: Optional[int] = utils._get_as_snowflake(guild, 'owner_id')
        self.application_id: Optional[int] = utils._get_as_snowflake(guild, 'application_id')
        self.premium_progress_bar_enabled: bool = guild.get('premium_progress_bar_enabled', False)
        self._joined_at = guild.get('joined_at')
        try:
            self._large = guild['large']
        except KeyError:
            pass
        for vs in guild.get('voice_states', []):
            self._update_voice_state(vs, int(vs['channel_id']))
        cache_flags = state.member_cache_flags
        for mdata in guild.get('members', []):
            member = Member(data=mdata, guild=self, state=state)
            if cache_flags.joined or member.id == state.self_id or (cache_flags.voice and member.id in self._voice_states):
                self._add_member(member)
        for presence in guild.get('presences', []):
            user_id = int(presence['user']['id'])
            presence = state.create_presence(presence)
            state.store_presence(user_id, presence, self.id)
    @property
    def channels(self) -> Sequence[GuildChannel]:
        return utils.SequenceProxy(self._channels.values())
    @property
    def threads(self) -> Sequence[Thread]:
        return utils.SequenceProxy(self._threads.values())
    @property
    def large(self) -> bool:
        if self._large is None:
            if self._member_count is not None:
                return self._member_count >= 250
            return len(self._members) >= 250
        return self._large
    @property
    def _offline_members_hidden(self) -> bool:
        return (self._member_count or 0) + len([role for role in self.roles if role.hoist]) + 2 >= 1000
    @property
    def _extra_large(self) -> bool:
        return self._member_count is not None and self._member_count >= 75000
    def is_hub(self) -> bool:
        return 'HUB' in self.features
    @property
    def voice_channels(self) -> List[VoiceChannel]:
        r = [ch for ch in self._channels.values() if isinstance(ch, VoiceChannel)]
        r.sort(key=attrgetter('position', 'id'))
        return r
    @property
    def stage_channels(self) -> List[StageChannel]:
        r = [ch for ch in self._channels.values() if isinstance(ch, StageChannel)]
        r.sort(key=attrgetter('position', 'id'))
        return r
    @property
    def me(self) -> Optional[Member]:
        self_id = self.state.self_id
        return self.get_member(self_id)
    def is_joined(self) -> bool:
        if self._cs_joined is not None:
            return self._cs_joined
        if (self.me and self.me.joined_at) or self.joined_at:
            return True
        return self.state.is_guild_evicted(self)
    @property
    def joined_at(self) -> Optional[datetime]:
        return utils.parse_time(self._joined_at)
    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        return self.state._get_voice_client(self.id)
    @property
    def notification_settings(self) -> GuildSettings:
        state = self.state
        return state.guild_settings.get(self.id, state.default_guild_settings(self.id))
    @property
    def text_channels(self) -> List[TextChannel]:
        r = [ch for ch in self._channels.values() if isinstance(ch, TextChannel)]
        r.sort(key=attrgetter('position', 'id'))
        return r
    @property
    def categories(self) -> List[CategoryChannel]:
        r = [ch for ch in self._channels.values() if isinstance(ch, CategoryChannel)]
        r.sort(key=attrgetter('position', 'id'))
        return r
    @property
    def forums(self) -> List[ForumChannel]:
        r = [ch for ch in self._channels.values() if isinstance(ch, ForumChannel)]
        r.sort(key=attrgetter('position', 'id'))
        return r
    @property
    def directory_channels(self) -> List[DirectoryChannel]:
        r = [ch for ch in self._channels.values() if isinstance(ch, DirectoryChannel)]
        r.sort(key=attrgetter('position', 'id'))
        return r
    @property
    def directories(self) -> List[DirectoryChannel]:
        return self.directory_channels
    def by_category(self) -> List[ByCategoryItem]:
        grouped: Dict[Optional[int], List[NonCategoryChannel]] = {}
        for channel in self._channels.values():
            if isinstance(channel, CategoryChannel):
                grouped.setdefault(channel.id, [])
                continue
            try:
                grouped[channel.category_id].append(channel)
            except KeyError:
                grouped[channel.category_id] = [channel]
        def key(t: ByCategoryItem) -> Tuple[Tuple[int, int], List[NonCategoryChannel]]:
            k, v = t
            return ((k.position, k.id) if k else (-1, -1), v)
        _get = self._channels.get
        as_list: List[ByCategoryItem] = [(_get(k), v) for k, v in grouped.items()]
        as_list.sort(key=key)
        for _, channels in as_list:
            channels.sort(key=attrgetter('_sorting_bucket', 'position', 'id'))
        return as_list
    def _resolve_channel(self, id: Optional[int], /) -> Optional[Union[GuildChannel, Thread]]:
        if id is None:
            return
        return self._channels.get(id) or self._threads.get(id)
    def get_channel_or_thread(self, channel_id: int, /) -> Optional[Union[Thread, GuildChannel]]:
        return self._channels.get(channel_id) or self._threads.get(channel_id)
    def get_channel(self, channel_id: int, /) -> Optional[GuildChannel]:
        return self._channels.get(channel_id)
    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        return self._threads.get(thread_id)
    def get_emoji(self, emoji_id: int, /) -> Optional[Emoji]:
        emoji = self.state.get_emoji(emoji_id)
        if emoji and emoji.guild == self:
            return emoji
        return None
    @property
    def system_channel(self) -> Optional[TextChannel]:
        channel_id = self._system_channel_id
        return channel_id and self._channels.get(channel_id)
    @property
    def system_channel_flags(self) -> SystemChannelFlags:
        return SystemChannelFlags._from_value(self._system_channel_flags)
    @property
    def rules_channel(self) -> Optional[TextChannel]:
        channel_id = self._rules_channel_id
        return channel_id and self._channels.get(channel_id)
    @property
    def public_updates_channel(self) -> Optional[TextChannel]:
        channel_id = self._public_updates_channel_id
        return channel_id and self._channels.get(channel_id)
    @property
    def afk_channel(self) -> Optional[VocalGuildChannel]:
        channel_id = self._afk_channel_id
        return channel_id and self._channels.get(channel_id)
    @property
    def widget_channel(self) -> Optional[Union[TextChannel, ForumChannel, VoiceChannel, StageChannel]]:
        channel_id = self._widget_channel_id
        return channel_id and self._channels.get(channel_id)
    @property
    def emoji_limit(self) -> int:
        more_emoji = 200 if 'MORE_EMOJI' in self.features else 50
        return max(more_emoji, self._PREMIUM_GUILD_LIMITS[self.premium_tier].emoji)
    @property
    def sticker_limit(self) -> int:
        more_stickers = 60 if 'MORE_STICKERS' in self.features else 0
        return max(more_stickers, self._PREMIUM_GUILD_LIMITS[self.premium_tier].stickers)
    @property
    def bitrate_limit(self) -> float:
        vip_guild = self._PREMIUM_GUILD_LIMITS[1].bitrate if 'VIP_REGIONS' in self.features else 96e3
        return max(vip_guild, self._PREMIUM_GUILD_LIMITS[self.premium_tier].bitrate)
    @property
    def filesize_limit(self) -> int:
        return self._PREMIUM_GUILD_LIMITS[self.premium_tier].filesize
    @property
    def members(self) -> Sequence[Member]:
        return utils.SequenceProxy(self._members.values())
    def get_member(self, user_id: int, /) -> Optional[Member]:
        return self._members.get(user_id)
    @property
    def premium_tier(self) -> int:
        tier = self._premium_tier
        if tier is not None:
            return tier
        if 'PREMIUM_TIER_3_OVERRIDE' in self.features:
            return 3
        count = self.premium_subscription_count
        if count < 2:
            return 0
        elif count < 7:
            return 1
        elif count < 14:
            return 2
        else:
            return 3
    @property
    def premium_subscribers(self) -> List[Member]:
        return [member for member in self.members if member.premium_since is not None]
    @property
    def roles(self) -> Sequence[Role]:
        return utils.SequenceProxy(self._roles.values(), sorted=True)
    def get_role(self, role_id: int, /) -> Optional[Role]:
        return self._roles.get(role_id)
    @property
    def default_role(self) -> Role:
        return self.get_role(self.id)
    @property
    def premium_subscriber_role(self) -> Optional[Role]:
        for role in self._roles.values():
            if role.is_premium_subscriber():
                return role
        return None
    @property
    def stage_instances(self) -> Sequence[StageInstance]:
        return utils.SequenceProxy(self._stage_instances.values())
    def get_stage_instance(self, stage_instance_id: int, /) -> Optional[StageInstance]:
        return self._stage_instances.get(stage_instance_id)
    @property
    def scheduled_events(self) -> Sequence[ScheduledEvent]:
        return utils.SequenceProxy(self._scheduled_events.values())
    @property
    def scheduled_events_read_state(self) -> ReadState:
        return self.state.get_read_state(self.id, ReadStateType.scheduled_events)
    @property
    def acked_scheduled_event(self) -> Optional[ScheduledEvent]:
        return self._scheduled_events.get(self.scheduled_events_read_state.last_acked_id)
    def get_scheduled_event(self, scheduled_event_id: int, /) -> Optional[ScheduledEvent]:
        return self._scheduled_events.get(scheduled_event_id)
    @property
    def owner(self) -> Optional[Member]:
        return self.get_member(self.owner_id)
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self.state, self.id, self._icon)
    @property
    def banner(self) -> Optional[Asset]:
        if self._banner is None:
            return None
        return Asset._from_guild_image(self.state, self.id, self._banner, path='banners')
    @property
    def splash(self) -> Optional[Asset]:
        if self._splash is None:
            return None
        return Asset._from_guild_image(self.state, self.id, self._splash, path='splashes')
    @property
    def discovery_splash(self) -> Optional[Asset]:
        if self._discovery_splash is None:
            return None
        return Asset._from_guild_image(self.state, self.id, self._discovery_splash, path='discovery-splashes')
    @property
    def member_count(self) -> Optional[int]:
        return self._member_count if self._member_count is not None else self.approximate_member_count
    @property
    def online_count(self) -> Optional[int]:
        return self._presence_count
    @property
    def application_command_count(self) -> Optional[int]:
        counts = self.application_command_counts
        if counts:
            sum(counts)
    @property
    def chunked(self) -> bool:
        count = self._member_count
        if count is None:
            return False
        return count == len(self._members) and self.state.subscriptions.has_feature(self, 'member_updates')
    @property
    def created_at(self) -> datetime:
        return utils.snowflake_time(self.id)
    def get_member_named(self, name: str, /) -> Optional[Member]:
        members = self.members
        username, _, discriminator = name.rpartition('
        if not username:
            discriminator, username = username, discriminator
        if discriminator == '0' or (len(discriminator) == 4 and discriminator.isdigit()):
            return utils.find(lambda m: m.name == username and m.discriminator == discriminator, members)
        def pred(m: Member) -> bool:
            return m.nick == name or m.global_name == name or m.name == name
        return utils.find(pred, members)
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.text],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, TextChannelPayload]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.voice],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, VoiceChannelPayload]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.stage_voice],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, StageChannelPayload]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.category],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, CategoryChannelPayload]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.news],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, NewsChannelPayload]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.news, ChannelType.text],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, Union[TextChannelPayload, NewsChannelPayload]]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.forum],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, ForumChannelPayload]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: Literal[ChannelType.directory],
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, DirectoryChannelPayload]:
        ...
    @overload
    def _create_channel(
        self,
        name: str,
        channel_type: ChannelType,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        category: Optional[Snowflake] = ...,
        **options: Any,
    ) -> Coroutine[Any, Any, GuildChannelPayload]:
        ...
    def _create_channel(
        self,
        name: str,
        channel_type: ChannelType,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = MISSING,
        category: Optional[Snowflake] = None,
        **options: Any,
    ) -> Coroutine[Any, Any, GuildChannelPayload]:
        if overwrites is MISSING:
            overwrites = {}
        elif not isinstance(overwrites, Mapping):
            raise TypeError('overwrites parameter expects a dict')
        perms = []
        for target, perm in overwrites.items():
            if not isinstance(perm, PermissionOverwrite):
                raise TypeError(f'Expected PermissionOverwrite received {perm.__class__.__name__}')
            allow, deny = perm.pair()
            payload = {'allow': allow.value, 'deny': deny.value, 'id': target.id}
            if isinstance(target, Role):
                payload['type'] = abc._Overwrites.ROLE
            else:
                payload['type'] = abc._Overwrites.MEMBER
            perms.append(payload)
        parent_id = category.id if category else None
        return self.state.http.create_channel(
            self.id, channel_type.value, name=name, parent_id=parent_id, permission_overwrites=perms, **options
        )
    async def create_text_channel(
        self,
        name: str,
        *,
        reason: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        news: bool = False,
        position: int = MISSING,
        topic: str = MISSING,
        slowmode_delay: int = MISSING,
        nsfw: bool = MISSING,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = MISSING,
        default_auto_archive_duration: int = MISSING,
        default_thread_slowmode_delay: int = MISSING,
    ) -> TextChannel:
        options = {}
        if position is not MISSING:
            options['position'] = position
        if topic is not MISSING:
            options['topic'] = topic
        if slowmode_delay is not MISSING:
            options['rate_limit_per_user'] = slowmode_delay
        if nsfw is not MISSING:
            options['nsfw'] = nsfw
        if default_auto_archive_duration is not MISSING:
            options['default_auto_archive_duration'] = default_auto_archive_duration
        if default_thread_slowmode_delay is not MISSING:
            options['default_thread_rate_limit_per_user'] = default_thread_slowmode_delay
        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.news if news else ChannelType.text,
            category=category,
            reason=reason,
            **options,
        )
        channel = TextChannel(state=self.state, guild=self, data=data)
        self._channels[channel.id] = channel
        return channel
    async def create_voice_channel(
        self,
        name: str,
        *,
        reason: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        position: int = MISSING,
        bitrate: int = MISSING,
        user_limit: int = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality_mode: VideoQualityMode = MISSING,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = MISSING,
    ) -> VoiceChannel:
        options = {}
        if position is not MISSING:
            options['position'] = position
        if bitrate is not MISSING:
            options['bitrate'] = bitrate
        if user_limit is not MISSING:
            options['user_limit'] = user_limit
        if rtc_region is not MISSING:
            options['rtc_region'] = None if rtc_region is None else rtc_region
        if video_quality_mode is not MISSING:
            if not isinstance(video_quality_mode, VideoQualityMode):
                raise TypeError('video_quality_mode must be of type VideoQualityMode')
            options['video_quality_mode'] = video_quality_mode.value
        data = await self._create_channel(
            name, overwrites=overwrites, channel_type=ChannelType.voice, category=category, reason=reason, **options
        )
        channel = VoiceChannel(state=self.state, guild=self, data=data)
        self._channels[channel.id] = channel
        return channel
    async def create_stage_channel(
        self,
        name: str,
        *,
        reason: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        position: int = MISSING,
        bitrate: int = MISSING,
        user_limit: int = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality_mode: VideoQualityMode = MISSING,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = MISSING,
    ) -> StageChannel:
        options = {}
        if position is not MISSING:
            options['position'] = position
        if bitrate is not MISSING:
            options['bitrate'] = bitrate
        if user_limit is not MISSING:
            options['user_limit'] = user_limit
        if rtc_region is not MISSING:
            options['rtc_region'] = None if rtc_region is None else rtc_region
        if video_quality_mode is not MISSING:
            if not isinstance(video_quality_mode, VideoQualityMode):
                raise TypeError('video_quality_mode must be of type VideoQualityMode')
            options['video_quality_mode'] = video_quality_mode.value
        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.stage_voice,
            category=category,
            reason=reason,
            **options,
        )
        channel = StageChannel(state=self.state, guild=self, data=data)
        self._channels[channel.id] = channel
        return channel
    async def create_category(
        self,
        name: str,
        *,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = MISSING,
        reason: Optional[str] = None,
        position: int = MISSING,
    ) -> CategoryChannel:
        options: Dict[str, Any] = {}
        if position is not MISSING:
            options['position'] = position
        data = await self._create_channel(
            name, overwrites=overwrites, channel_type=ChannelType.category, reason=reason, **options
        )
        channel = CategoryChannel(state=self.state, guild=self, data=data)
        self._channels[channel.id] = channel
        return channel
    create_category_channel = create_category
    async def create_directory(
        self,
        name: str,
        *,
        reason: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        position: int = MISSING,
        topic: str = MISSING,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = MISSING,
    ) -> DirectoryChannel:
        options = {}
        if position is not MISSING:
            options['position'] = position
        if topic is not MISSING:
            options['topic'] = topic
        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.directory,
            category=category,
            reason=reason,
            **options,
        )
        channel = DirectoryChannel(state=self.state, guild=self, data=data)
        self._channels[channel.id] = channel
        return channel
    create_directory_channel = create_directory
    async def create_forum(
        self,
        name: str,
        *,
        topic: str = MISSING,
        position: int = MISSING,
        category: Optional[CategoryChannel] = None,
        slowmode_delay: int = MISSING,
        nsfw: bool = MISSING,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = MISSING,
        reason: Optional[str] = None,
        default_auto_archive_duration: int = MISSING,
        default_thread_slowmode_delay: int = MISSING,
        default_sort_order: ForumOrderType = MISSING,
        default_reaction_emoji: EmojiInputType = MISSING,
        default_layout: ForumLayoutType = MISSING,
        available_tags: Sequence[ForumTag] = MISSING,
    ) -> ForumChannel:
        options = {}
        if position is not MISSING:
            options['position'] = position
        if topic is not MISSING:
            options['topic'] = topic
        if slowmode_delay is not MISSING:
            options['rate_limit_per_user'] = slowmode_delay
        if nsfw is not MISSING:
            options['nsfw'] = nsfw
        if default_auto_archive_duration is not MISSING:
            options['default_auto_archive_duration'] = default_auto_archive_duration
        if default_thread_slowmode_delay is not MISSING:
            options['default_thread_rate_limit_per_user'] = default_thread_slowmode_delay
        if default_sort_order is not MISSING:
            if not isinstance(default_sort_order, ForumOrderType):
                raise TypeError(
                    f'default_sort_order parameter must be a ForumOrderType not {default_sort_order.__class__.__name__}'
                )
            options['default_sort_order'] = default_sort_order.value
        if default_reaction_emoji is not MISSING:
            if isinstance(default_reaction_emoji, _EmojiTag):
                options['default_reaction_emoji'] = default_reaction_emoji._to_partial()._to_forum_tag_payload()
            elif isinstance(default_reaction_emoji, str):
                options['default_reaction_emoji'] = PartialEmoji.from_str(default_reaction_emoji)._to_forum_tag_payload()
            else:
                raise ValueError(f'default_reaction_emoji parameter must be either Emoji, PartialEmoji, or str')
        if default_layout is not MISSING:
            if not isinstance(default_layout, ForumLayoutType):
                raise TypeError(
                    f'default_layout parameter must be a ForumLayoutType not {default_layout.__class__.__name__}'
                )
            options['default_forum_layout'] = default_layout.value
        if available_tags is not MISSING:
            options['available_tags'] = [t.to_dict() for t in available_tags]
        data = await self._create_channel(
            name=name,
            overwrites=overwrites,
            channel_type=ChannelType.forum,
            category=category,
            reason=reason,
            **options,
        )
        channel = ForumChannel(state=self.state, guild=self, data=data)
        self._channels[channel.id] = channel
        return channel
    create_forum_channel = create_forum
    async def leave(self) -> None:
        await self.state.http.leave_guild(self.id, lurking=not self.is_joined())
    async def delete(self) -> None:
        await self.state.http.delete_guild(self.id)
    async def edit(
        self,
        *,
        reason: Optional[str] = MISSING,
        name: str = MISSING,
        description: Optional[str] = MISSING,
        icon: Optional[bytes] = MISSING,
        banner: Optional[bytes] = MISSING,
        splash: Optional[bytes] = MISSING,
        discovery_splash: Optional[bytes] = MISSING,
        community: bool = MISSING,
        afk_channel: Optional[VoiceChannel] = MISSING,
        owner: Snowflake = MISSING,
        afk_timeout: int = MISSING,
        default_notifications: NotificationLevel = MISSING,
        verification_level: VerificationLevel = MISSING,
        explicit_content_filter: ContentFilter = MISSING,
        vanity_code: str = MISSING,
        system_channel: Optional[TextChannel] = MISSING,
        system_channel_flags: SystemChannelFlags = MISSING,
        preferred_locale: Locale = MISSING,
        rules_channel: Optional[TextChannel] = MISSING,
        public_updates_channel: Optional[TextChannel] = MISSING,
        premium_progress_bar_enabled: bool = MISSING,
        discoverable: bool = MISSING,
        invites_disabled: bool = MISSING,
        widget_enabled: bool = MISSING,
        widget_channel: Optional[Snowflake] = MISSING,
        mfa_level: MFALevel = MISSING,
    ) -> Guild:
        r
        http = self.state.http
        if vanity_code is not MISSING:
            await http.change_vanity_code(self.id, vanity_code, reason=reason)
        fields: Dict[str, Any] = {}
        if name is not MISSING:
            fields['name'] = name
        if description is not MISSING:
            fields['description'] = description
        if preferred_locale is not MISSING:
            fields['preferred_locale'] = str(preferred_locale)
        if afk_timeout is not MISSING:
            fields['afk_timeout'] = afk_timeout
        if icon is not MISSING:
            if icon is None:
                fields['icon'] = icon
            else:
                fields['icon'] = utils._bytes_to_base64_data(icon)
        if banner is not MISSING:
            if banner is None:
                fields['banner'] = banner
            else:
                fields['banner'] = utils._bytes_to_base64_data(banner)
        if splash is not MISSING:
            if splash is None:
                fields['splash'] = splash
            else:
                fields['splash'] = utils._bytes_to_base64_data(splash)
        if discovery_splash is not MISSING:
            if discovery_splash is None:
                fields['discovery_splash'] = discovery_splash
            else:
                fields['discovery_splash'] = utils._bytes_to_base64_data(discovery_splash)
        if default_notifications is not MISSING:
            if not isinstance(default_notifications, NotificationLevel):
                raise TypeError('default_notifications field must be of type NotificationLevel')
            fields['default_message_notifications'] = default_notifications.value
        if afk_channel is not MISSING:
            if afk_channel is None:
                fields['afk_channel_id'] = afk_channel
            else:
                fields['afk_channel_id'] = afk_channel.id
        if system_channel is not MISSING:
            if system_channel is None:
                fields['system_channel_id'] = system_channel
            else:
                fields['system_channel_id'] = system_channel.id
        if rules_channel is not MISSING:
            if rules_channel is None:
                fields['rules_channel_id'] = rules_channel
            else:
                fields['rules_channel_id'] = rules_channel.id
        if public_updates_channel is not MISSING:
            if public_updates_channel is None:
                fields['public_updates_channel_id'] = public_updates_channel
            else:
                fields['public_updates_channel_id'] = public_updates_channel.id
        if owner is not MISSING:
            if self.owner_id != self.state.self_id:
                raise ValueError('To transfer ownership you must be the owner of the guild')
            fields['owner_id'] = owner.id
        if verification_level is not MISSING:
            if not isinstance(verification_level, VerificationLevel):
                raise TypeError('verification_level field must be of type VerificationLevel')
            fields['verification_level'] = verification_level.value
        if explicit_content_filter is not MISSING:
            if not isinstance(explicit_content_filter, ContentFilter):
                raise TypeError('explicit_content_filter field must be of type ContentFilter')
            fields['explicit_content_filter'] = explicit_content_filter.value
        if system_channel_flags is not MISSING:
            if not isinstance(system_channel_flags, SystemChannelFlags):
                raise TypeError('system_channel_flags field must be of type SystemChannelFlags')
            fields['system_channel_flags'] = system_channel_flags.value
        if any(feat is not MISSING for feat in (community, discoverable, invites_disabled)):
            features = set(self.features)
            if community is not MISSING:
                if community:
                    if 'rules_channel_id' in fields and 'public_updates_channel_id' in fields:
                        features.add('COMMUNITY')
                    else:
                        raise ValueError(
                            'community field requires both rules_channel and public_updates_channel fields to be provided'
                        )
                else:
                    features.discard('COMMUNITY')
            if discoverable is not MISSING:
                if discoverable:
                    features.add('DISCOVERABLE')
                else:
                    features.discard('DISCOVERABLE')
            if invites_disabled is not MISSING:
                if invites_disabled:
                    features.add('INVITES_DISABLED')
                else:
                    features.discard('INVITES_DISABLED')
            fields['features'] = list(features)
        if premium_progress_bar_enabled is not MISSING:
            fields['premium_progress_bar_enabled'] = premium_progress_bar_enabled
        widget_payload: EditWidgetSettings = {}
        if widget_channel is not MISSING:
            widget_payload['channel_id'] = None if widget_channel is None else widget_channel.id
        if widget_enabled is not MISSING:
            widget_payload['enabled'] = widget_enabled
        if widget_payload:
            await self.state.http.edit_widget(self.id, payload=widget_payload, reason=reason)
        if mfa_level is not MISSING:
            if not isinstance(mfa_level, MFALevel):
                raise TypeError('mfa_level must be of type MFALevel')
            await http.edit_guild_mfa_level(self.id, mfa_level=mfa_level.value)
        data = await http.edit_guild(self.id, reason=reason, **fields)
        return Guild(data=data, state=self.state)
    async def top_channels(self) -> List[Union[TextChannel, VoiceChannel, StageChannel, PartialMessageable]]:
        state = self.state
        data = await state.http.get_top_guild_channels(self.id)
        return [self.get_channel(int(c)) or PartialMessageable(id=int(c), state=state, guild_id=self.id) for c in data]
    async def webhook_channels(self) -> List[Union[TextChannel, VoiceChannel, StageChannel, PartialMessageable]]:
        state = self.state
        data = await state.http.get_guild_webhook_channels(self.id)
        return [self.get_channel(int(c['id'])) or PartialMessageable._from_webhook_channel(self, c) for c in data]
    async def fetch_channels(self) -> Sequence[GuildChannel]:
        data = await self.state.http.get_all_guild_channels(self.id)
        def convert(d):
            factory, ch_type = _guild_channel_factory(d['type'])
            if factory is None:
                raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(d))
            channel = factory(guild=self, state=self.state, data=d)
            return channel
        return [convert(d) for d in data]
    async def fetch_member(self, member_id: int, /) -> Member:
        data = await self.state.http.get_member(self.id, member_id)
        return Member(data=data, state=self.state, guild=self)
    async def fetch_member_profile(
        self,
        member_id: int,
        /,
        *,
        with_mutual_guilds: bool = True,
        with_mutual_friends_count: bool = False,
        with_mutual_friends: bool = True,
    ) -> MemberProfile:
        state = self.state
        data = await state.http.get_user_profile(
            member_id,
            self.id,
            with_mutual_guilds=with_mutual_guilds,
            with_mutual_friends_count=with_mutual_friends_count,
        )
        if 'guild_member_profile' not in data:
            raise InvalidData('Member is not in this guild')
        if 'guild_member' not in data:
            raise InvalidData('Member has blocked you')
        mutual_friends = None
        if with_mutual_friends and not data['user'].get('bot', False):
            mutual_friends = await state.http.get_mutual_friends(member_id)
        return MemberProfile(state=state, data=data, mutual_friends=mutual_friends, guild=self)
    async def fetch_ban(self, user: Snowflake) -> BanEntry:
        data = await self.state.http.get_ban(user.id, self.id)
        return BanEntry(user=User(state=self.state, data=data['user']), reason=data['reason'])
    async def fetch_channel(self, channel_id: int, /) -> Union[GuildChannel, Thread]:
        data = await self.state.http.get_channel(channel_id)
        factory, ch_type = _threaded_guild_channel_factory(data['type'])
        if factory is None:
            raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(data))
        if ch_type in (ChannelType.group, ChannelType.private):
            raise InvalidData('Channel ID resolved to a private channel')
        guild_id = int(data['guild_id'])
        if self.id != guild_id:
            raise InvalidData('Guild ID resolved to a different guild')
        channel: GuildChannel = factory(guild=self, state=self.state, data=data)
        return channel
    async def bans(
        self,
        *,
        limit: Optional[int] = 1000,
        before: Snowflake = MISSING,
        after: Snowflake = MISSING,
        paginate: bool = True,
    ) -> AsyncIterator[BanEntry]:
        if before is not MISSING and after is not MISSING:
            raise TypeError('bans pagination does not support both before and after')
        state = self.state
        endpoint = state.http.get_bans
        if not paginate:
            data = await endpoint(self.id)
            for entry in data:
                yield BanEntry(user=User(state=state, data=entry['user']), reason=entry['reason'])
            return
        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await endpoint(self.id, limit=retrieve, before=before_id)
            if data:
                if limit is not None:
                    limit -= len(data)
                before = Object(id=int(data[0]['user']['id']))
            return data, before, limit
        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await endpoint(self.id, limit=retrieve, after=after_id)
            if data:
                if limit is not None:
                    limit -= len(data)
                after = Object(id=int(data[-1]['user']['id']))
            return data, after, limit
        if before:
            strategy, state = _before_strategy, before
        else:
            strategy, state = _after_strategy, after
        while True:
            retrieve = 1000 if limit is None else min(limit, 1000)
            if retrieve < 1:
                return
            data, state, limit = await strategy(retrieve, state, limit)
            if len(data) < 1000:
                limit = 0
            for e in data:
                yield BanEntry(user=User(state=state, data=e['user']), reason=e['reason'])
    def search(
        self,
        content: str = MISSING,
        *,
        limit: Optional[int] = 25,
        offset: int = 0,
        before: SnowflakeTime = MISSING,
        after: SnowflakeTime = MISSING,
        include_nsfw: bool = MISSING,
        channels: Collection[Snowflake] = MISSING,
        authors: Collection[Snowflake] = MISSING,
        author_types: Collection[MessageSearchAuthorType] = MISSING,
        mentions: Collection[Snowflake] = MISSING,
        mention_everyone: bool = MISSING,
        pinned: bool = MISSING,
        has: Collection[MessageSearchHasType] = MISSING,
        embed_types: Collection[EmbedType] = MISSING,
        embed_providers: Collection[str] = MISSING,
        link_hostnames: Collection[str] = MISSING,
        attachment_filenames: Collection[str] = MISSING,
        attachment_extensions: Collection[str] = MISSING,
        application_commands: Collection[Snowflake] = MISSING,
        oldest_first: bool = False,
        most_relevant: bool = False,
    ) -> AsyncIterator[Message]:
        return abc._handle_message_search(
            self,
            limit=limit,
            offset=offset,
            before=before,
            after=after,
            content=content,
            include_nsfw=include_nsfw,
            channels=channels,
            authors=authors,
            author_types=author_types,
            mentions=mentions,
            mention_everyone=mention_everyone,
            pinned=pinned,
            has=has,
            embed_types=embed_types,
            embed_providers=embed_providers,
            link_hostnames=link_hostnames,
            attachment_filenames=attachment_filenames,
            attachment_extensions=attachment_extensions,
            application_commands=application_commands,
            oldest_first=oldest_first,
            most_relevant=most_relevant,
        )
    async def prune_members(
        self,
        *,
        days: int,
        compute_prune_count: bool = True,
        roles: Collection[Snowflake] = MISSING,
        reason: Optional[str] = None,
    ) -> Optional[int]:
        r
        if not isinstance(days, int):
            raise TypeError(f'Expected int for ``days``, received {days.__class__.__name__} instead')
        if roles:
            role_ids = [str(role.id) for role in roles]
        else:
            role_ids = []
        data = await self.state.http.prune_members(
            self.id, days, compute_prune_count=compute_prune_count, roles=role_ids, reason=reason
        )
        return data['pruned']
    async def templates(self) -> List[Template]:
        from .template import Template
        data = await self.state.http.guild_templates(self.id)
        return [Template(data=d, state=self.state) for d in data]
    async def webhooks(self) -> List[Webhook]:
        from .webhook import Webhook
        data = await self.state.http.guild_webhooks(self.id)
        return [Webhook.from_state(d, state=self.state) for d in data]
    async def estimate_pruned_members(self, *, days: int, roles: Collection[Snowflake] = MISSING) -> Optional[int]:
        if not isinstance(days, int):
            raise TypeError(f'Expected int for ``days``, received {days.__class__.__name__} instead')
        if roles:
            role_ids = [str(role.id) for role in roles]
        else:
            role_ids = []
        data = await self.state.http.estimate_pruned_members(self.id, days, role_ids)
        return data['pruned']
    async def invites(self) -> List[Invite]:
        data = await self.state.http.invites_from(self.id)
        result = []
        for invite in data:
            channel = self.get_channel(int(invite['channel']['id']))
            result.append(Invite(state=self.state, data=invite, guild=self, channel=channel))
        return result
    async def create_template(self, *, name: str, description: str = MISSING) -> Template:
        from .template import Template
        payload = {'name': name}
        if description:
            payload['description'] = description
        data = await self.state.http.create_template(self.id, payload)
        return Template(state=self.state, data=data)
    async def create_integration(self, *, type: IntegrationType, id: int, reason: Optional[str] = None) -> None:
        await self.state.http.create_integration(self.id, type, id, reason=reason)
    async def integrations(self, *, has_commands: bool = False) -> List[Integration]:
        data = await self.state.http.get_all_integrations(self.id, has_commands=has_commands)
        def convert(d):
            factory, _ = _integration_factory(d['type'])
            return factory(guild=self, data=d)
        return [convert(d) for d in data]
    async def application_commands(self) -> List[Union[SlashCommand, UserCommand, MessageCommand]]:
        state = self.state
        data = await state.http.guild_application_command_index(self.id)
        cmds = data['application_commands']
        apps = {int(app['id']): state.create_integration_application(app) for app in data.get('applications') or []}
        result = []
        for cmd in cmds:
            _, cls = _command_factory(cmd['type'])
            application = apps.get(int(cmd['application_id']))
            result.append(cls(state=state, data=cmd, application=application))
        return result
    async def fetch_stickers(self) -> List[GuildSticker]:
        r
        data = await self.state.http.get_all_guild_stickers(self.id)
        return [GuildSticker(state=self.state, data=d) for d in data]
    async def fetch_sticker(self, sticker_id: int, /) -> GuildSticker:
        data = await self.state.http.get_guild_sticker(self.id, sticker_id)
        return GuildSticker(state=self.state, data=data)
    async def create_sticker(
        self,
        *,
        name: str,
        description: str,
        emoji: str,
        file: File,
        reason: Optional[str] = None,
    ) -> GuildSticker:
        payload = {
            'name': name,
            'description': description or '',
        }
        try:
            emoji = unicodedata.name(emoji)
        except TypeError:
            pass
        else:
            emoji = emoji.replace(' ', '_')
        payload['tags'] = emoji
        data = await self.state.http.create_guild_sticker(self.id, payload, file, reason)
        return self.state.store_sticker(self, data)
    async def delete_sticker(self, sticker: Snowflake, /, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_guild_sticker(self.id, sticker.id, reason)
    async def subscribed_scheduled_events(self) -> List[Union[ScheduledEvent, Object]]:
        data = await self.state.http.get_subscribed_scheduled_events(self.id)
        return [
            self.get_scheduled_event(int(d['guild_scheduled_event_id'])) or Object(id=int(d['guild_scheduled_event_id']))
            for d in data
        ]
    async def fetch_scheduled_events(self, *, with_counts: bool = True) -> List[ScheduledEvent]:
        data = await self.state.http.get_scheduled_events(self.id, with_counts)
        return [ScheduledEvent(state=self.state, data=d) for d in data]
    async def fetch_scheduled_event(self, scheduled_event_id: int, /, *, with_counts: bool = True) -> ScheduledEvent:
        data = await self.state.http.get_scheduled_event(self.id, scheduled_event_id, with_counts)
        return ScheduledEvent(state=self.state, data=data)
    @overload
    async def create_scheduled_event(
        self,
        *,
        name: str,
        start_time: datetime,
        entity_type: Literal[EntityType.external] = ...,
        privacy_level: PrivacyLevel = ...,
        location: str = ...,
        end_time: datetime = ...,
        description: str = ...,
        image: bytes = ...,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    @overload
    async def create_scheduled_event(
        self,
        *,
        name: str,
        start_time: datetime,
        entity_type: Literal[EntityType.stage_instance, EntityType.voice] = ...,
        privacy_level: PrivacyLevel = ...,
        channel: Snowflake = ...,
        end_time: datetime = ...,
        description: str = ...,
        image: bytes = ...,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    @overload
    async def create_scheduled_event(
        self,
        *,
        name: str,
        start_time: datetime,
        privacy_level: PrivacyLevel = ...,
        location: str = ...,
        end_time: datetime = ...,
        description: str = ...,
        image: bytes = ...,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    @overload
    async def create_scheduled_event(
        self,
        *,
        name: str,
        start_time: datetime,
        privacy_level: PrivacyLevel = ...,
        channel: Union[VoiceChannel, StageChannel] = ...,
        end_time: datetime = ...,
        description: str = ...,
        image: bytes = ...,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    async def create_scheduled_event(
        self,
        *,
        name: str,
        start_time: datetime,
        entity_type: EntityType = MISSING,
        privacy_level: PrivacyLevel = PrivacyLevel.guild_only,
        channel: Optional[Snowflake] = MISSING,
        location: str = MISSING,
        end_time: datetime = MISSING,
        description: str = MISSING,
        image: bytes = MISSING,
        directory_broadcast: bool = False,
        reason: Optional[str] = None,
    ) -> ScheduledEvent:
        r
        payload: Dict[str, Any] = {
            'name': name,
            'privacy_level': int(privacy_level or PrivacyLevel.guild_only.value),
            'broadcast_to_directory_channels': directory_broadcast,
        }
        metadata = {}
        if start_time.tzinfo is None:
            raise ValueError(
                'start_time must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
            )
        payload['scheduled_start_time'] = start_time.isoformat()
        if privacy_level:
            if not isinstance(privacy_level, PrivacyLevel):
                raise TypeError('privacy_level must be of type PrivacyLevel')
        payload['privacy_level'] = (privacy_level or PrivacyLevel.guild_only).value
        entity_type = entity_type or getattr(channel, '_scheduled_event_entity_type', MISSING)
        if entity_type is MISSING:
            if channel and isinstance(channel, Object):
                if channel.type is VoiceChannel:
                    entity_type = EntityType.voice
                elif channel.type is StageChannel:
                    entity_type = EntityType.stage_instance
            elif location not in (MISSING, None):
                entity_type = EntityType.external
        else:
            if not isinstance(entity_type, EntityType):
                raise TypeError('entity_type must be of type EntityType')
            payload['entity_type'] = entity_type.value
        if entity_type is None:
            raise TypeError(
                f'invalid GuildChannel type passed; must be VoiceChannel or StageChannel not {channel.__class__.__name__}'
            )
        if description is not MISSING:
            payload['description'] = description
        if image is not MISSING:
            image_as_str: str = utils._bytes_to_base64_data(image)
            payload['image'] = image_as_str
        if entity_type in (EntityType.stage_instance, EntityType.voice):
            if channel in (MISSING, None):
                raise TypeError('channel must be set when entity_type is voice or stage_instance')
            payload['channel_id'] = channel.id
            if location is not MISSING:
                raise TypeError('location cannot be set when entity_type is voice or stage_instance')
        else:
            if channel is not MISSING:
                raise TypeError('channel cannot be set when entity_type is external')
            if location is MISSING or location is None:
                raise TypeError('location must be set when entity_type is external')
            metadata['location'] = location
            if not end_time:
                raise TypeError('end_time must be set when entity_type is external')
        if end_time:
            if end_time.tzinfo is None:
                raise ValueError(
                    'end_time must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                )
            payload['scheduled_end_time'] = end_time.isoformat()
        if metadata:
            payload['entity_metadata'] = metadata
        data = await self.state.http.create_guild_scheduled_event(self.id, **payload, reason=reason)
        return ScheduledEvent(state=self.state, data=data)
    async def top_emojis(self) -> List[Union[Emoji, PartialEmoji]]:
        state = self.state
        data = await state.http.get_top_emojis(self.id)
        return [
            self.state.get_emoji(int(e['emoji_id'])) or PartialEmoji.with_state(state, name='', id=int(e['emoji_id']))
            for e in data['items']
        ]
    async def fetch_emojis(self) -> List[Emoji]:
        r
        data = await self.state.http.get_all_custom_emojis(self.id)
        return [Emoji(guild=self, state=self.state, data=d) for d in data]
    async def fetch_emoji(self, emoji_id: int, /) -> Emoji:
        data = await self.state.http.get_custom_emoji(self.id, emoji_id)
        return Emoji(guild=self, state=self.state, data=data)
    async def create_custom_emoji(
        self,
        *,
        name: str,
        image: bytes,
        roles: Collection[Role] = MISSING,
        reason: Optional[str] = None,
    ) -> Emoji:
        r
        img = utils._bytes_to_base64_data(image)
        if roles:
            role_ids: SnowflakeList = [role.id for role in roles]
        else:
            role_ids = []
        data = await self.state.http.create_custom_emoji(self.id, name, img, roles=role_ids, reason=reason)
        return self.state.store_emoji(self, data)
    async def delete_emoji(self, emoji: Snowflake, /, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_custom_emoji(self.id, emoji.id, reason=reason)
    async def fetch_roles(self) -> List[Role]:
        data = await self.state.http.get_roles(self.id)
        return [Role(guild=self, state=self.state, data=d) for d in data]
    @overload
    async def create_role(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        permissions: Permissions = ...,
        colour: Union[Colour, int] = ...,
        hoist: bool = ...,
        display_icon: Union[bytes, str] = MISSING,
        mentionable: bool = ...,
        icon: Optional[bytes] = ...,
        emoji: Optional[PartialEmoji] = ...,
    ) -> Role:
        ...
    @overload
    async def create_role(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        permissions: Permissions = ...,
        color: Union[Colour, int] = ...,
        hoist: bool = ...,
        display_icon: Union[bytes, str] = MISSING,
        mentionable: bool = ...,
    ) -> Role:
        ...
    async def create_role(
        self,
        *,
        name: str = MISSING,
        permissions: Permissions = MISSING,
        color: Union[Colour, int] = MISSING,
        colour: Union[Colour, int] = MISSING,
        hoist: bool = MISSING,
        display_icon: Union[bytes, str] = MISSING,
        mentionable: bool = MISSING,
        icon: Optional[bytes] = MISSING,
        emoji: Optional[PartialEmoji] = MISSING,
        reason: Optional[str] = None,
    ) -> Role:
        fields: Dict[str, Any] = {}
        if permissions is not MISSING:
            fields['permissions'] = str(permissions.value)
        else:
            fields['permissions'] = '0'
        actual_colour = colour or color or Colour.default()
        if isinstance(actual_colour, int):
            fields['color'] = actual_colour
        else:
            fields['color'] = actual_colour.value
        if hoist is not MISSING:
            fields['hoist'] = hoist
        if display_icon is not MISSING:
            if isinstance(display_icon, bytes):
                fields['icon'] = utils._bytes_to_base64_data(display_icon)
            else:
                fields['unicode_emoji'] = display_icon
        if mentionable is not MISSING:
            fields['mentionable'] = mentionable
        if name is not MISSING:
            fields['name'] = name
        if icon is not MISSING:
            if icon is None:
                fields['icon'] = icon
            else:
                fields['icon'] = utils._bytes_to_base64_data(icon)
        if emoji is not MISSING:
            if emoji is None:
                fields['unicode_emoji'] = None
            elif emoji.id is not None:
                raise ValueError('emoji only supports unicode emojis')
            else:
                fields['unicode_emoji'] = emoji.name
        data = await self.state.http.create_role(self.id, reason=reason, **fields)
        role = Role(guild=self, data=data, state=self.state)
        return role
    async def edit_role_positions(self, positions: Mapping[Snowflake, int], *, reason: Optional[str] = None) -> List[Role]:
        if not isinstance(positions, Mapping):
            raise TypeError('positions parameter expects a dict')
        role_positions = []
        for role, position in positions.items():
            payload: RolePositionUpdatePayload = {'id': role.id, 'position': position}
            role_positions.append(payload)
        data = await self.state.http.move_role_position(self.id, role_positions, reason=reason)
        roles: List[Role] = []
        for d in data:
            role = Role(guild=self, data=d, state=self.state)
            roles.append(role)
            self._roles[role.id] = role
        return roles
    async def role_member_counts(self) -> Dict[Role, int]:
        data = await self.state.http.get_role_member_counts(self.id)
        ret: Dict[Role, int] = {}
        for k, v in data.items():
            role = self.get_role(int(k))
            if role is not None:
                ret[role] = v
        return ret
    async def kick(self, user: Snowflake, *, reason: Optional[str] = None) -> None:
        await self.state.http.kick(user.id, self.id, reason=reason)
    async def ban(
        self,
        user: Snowflake,
        *,
        reason: Optional[str] = None,
        delete_message_days: int = MISSING,
        delete_message_seconds: int = MISSING,
    ) -> None:
        if delete_message_days is not MISSING and delete_message_seconds is not MISSING:
            raise TypeError('Cannot mix delete_message_days and delete_message_seconds keyword arguments.')
        if delete_message_days is not MISSING:
            msg = 'delete_message_days is deprecated, use delete_message_seconds instead'
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            delete_message_seconds = delete_message_days * 86400
        if delete_message_seconds is MISSING:
            delete_message_seconds = 86400
        await self.state.http.ban(user.id, self.id, delete_message_seconds, reason=reason)
    async def unban(self, user: Snowflake, *, reason: Optional[str] = None) -> None:
        await self.state.http.unban(user.id, self.id, reason=reason)
    @property
    def vanity_url(self) -> Optional[str]:
        if self.vanity_url_code is None:
            return None
        return f'{Invite.BASE}/{self.vanity_url_code}'
    async def vanity_invite(self) -> Optional[Invite]:
        payload = await self.state.http.get_vanity_code(self.id)
        if not payload['code']:
            return
        data = await self.state.http.get_invite(payload['code'])
        channel = self.get_channel(int(data['channel']['id']))
        data.update({'temporary': False, 'max_uses': 0, 'max_age': 0, 'uses': payload.get('uses', 0)})
        return Invite(state=self.state, data=payload, guild=self, channel=channel)
    async def audit_logs(
        self,
        *,
        limit: Optional[int] = 100,
        before: SnowflakeTime = MISSING,
        after: SnowflakeTime = MISSING,
        oldest_first: bool = MISSING,
        user: Snowflake = MISSING,
        action: AuditLogAction = MISSING,
    ) -> AsyncIterator[AuditLogEntry]:
        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await self.state.http.get_audit_logs(
                self.id, limit=retrieve, user_id=user_id, action_type=action_type, before=before_id
            )
            entries = data.get('audit_log_entries', [])
            if data and entries:
                if limit is not None:
                    limit -= len(data)
                before = Object(id=int(entries[-1]['id']))
            return data, entries, before, limit
        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await self.state.http.get_audit_logs(
                self.id, limit=retrieve, user_id=user_id, action_type=action_type, after=after_id
            )
            entries = data.get('audit_log_entries', [])
            if data and entries:
                if limit is not None:
                    limit -= len(data)
                after = Object(id=int(entries[-1]['id']))
            return data, entries, after, limit
        if user is not MISSING:
            user_id = user.id
        else:
            user_id = None
        if action is not MISSING:
            action_type: Optional[AuditLogEvent] = action.value
        else:
            action_type = None
        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))
        if oldest_first:
            if after is MISSING:
                after = OLDEST_OBJECT
        predicate = None
        if oldest_first:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda m: int(m['id']) < before.id
        else:
            strategy, state = _before_strategy, before
            if after:
                predicate = lambda m: int(m['id']) > after.id
        from .webhook import Webhook
        while True:
            retrieve = 100 if limit is None else min(limit, 100)
            if retrieve < 1:
                return
            data, raw_entries, state, limit = await strategy(retrieve, state, limit)
            if predicate:
                raw_entries = filter(predicate, raw_entries)
            users = (User(data=raw_user, state=self.state) for raw_user in data.get('users', []))
            user_map = {user.id: user for user in users}
            automod_rules = (
                AutoModRule(data=raw_rule, guild=self, state=self.state)
                for raw_rule in data.get('auto_moderation_rules', [])
            )
            automod_rule_map = {rule.id: rule for rule in automod_rules}
            webhooks = (Webhook.from_state(data=raw_webhook, state=self.state) for raw_webhook in data.get('webhooks', []))
            webhook_map = {webhook.id: webhook for webhook in webhooks}
            count = 0
            for count, raw_entry in enumerate(raw_entries, 1):
                if raw_entry['action_type'] is None:
                    continue
                yield AuditLogEntry(
                    data=raw_entry,
                    users=user_map,
                    automod_rules=automod_rule_map,
                    webhooks=webhook_map,
                    guild=self,
                )
            if count < 100:
                break
    async def ack(self) -> None:
        return await self.state.http.ack_guild(self.id)
    async def widget(self) -> Widget:
        data = await self.state.http.get_widget(self.id)
        return Widget(state=self.state, data=data)
    async def edit_widget(
        self,
        *,
        enabled: bool = MISSING,
        channel: Optional[Snowflake] = MISSING,
        reason: Optional[str] = None,
    ) -> None:
        payload: EditWidgetSettings = {}
        if channel is not MISSING:
            payload['channel_id'] = None if channel is None else channel.id
        if enabled is not MISSING:
            payload['enabled'] = enabled
        if payload:
            await self.state.http.edit_widget(self.id, payload=payload, reason=reason)
    async def welcome_screen(self) -> WelcomeScreen:
        data = await self.state.http.get_welcome_screen(self.id)
        return WelcomeScreen(data=data, guild=self)
    async def edit_welcome_screen(
        self,
        *,
        description: str = MISSING,
        welcome_channels: Sequence[WelcomeChannel] = MISSING,
        enabled: bool = MISSING,
        reason: Optional[str] = None,
    ):
        payload = {}
        if enabled is not MISSING:
            payload['enabled'] = enabled
        if description is not MISSING:
            payload['description'] = description
        if welcome_channels is not MISSING:
            channels = [channel._to_dict() for channel in welcome_channels] if welcome_channels else []
            payload['welcome_channels'] = channels
        if payload:
            await self.state.http.edit_welcome_screen(self.id, payload, reason=reason)
    async def applications(
        self, *, with_team: bool = False, type: Optional[ApplicationType] = None, channel: Optional[Snowflake] = None
    ) -> List[PartialApplication]:
        data = await self.state.http.get_guild_applications(
            self.id,
            include_team=with_team,
            type=int(type) if type else None,
            channel_id=channel.id if channel else None,
        )
        return [PartialApplication(state=self.state, data=app) for app in data]
    async def premium_subscriptions(self) -> List[PremiumGuildSubscription]:
        data = await self.state.http.get_guild_subscriptions(self.id)
        return [PremiumGuildSubscription(state=self.state, data=sub) for sub in data]
    async def apply_premium_subscription_slots(self, *subscription_slots: Snowflake) -> List[PremiumGuildSubscription]:
        r
        if not subscription_slots:
            return []
        state = self.state
        data = await state.http.apply_guild_subscription_slots(self.id, [slot.id for slot in subscription_slots])
        return [PremiumGuildSubscription(state=state, data=sub) for sub in data]
    async def entitlements(
        self, *, with_sku: bool = True, with_application: bool = True, exclude_deleted: bool = False
    ) -> List[Entitlement]:
        state = self.state
        data = await state.http.get_guild_entitlements(
            self.id, with_sku=with_sku, with_application=with_application, exclude_deleted=exclude_deleted
        )
        return [Entitlement(state=state, data=d) for d in data]
    async def price_tiers(self) -> List[int]:
        return await self.state.http.get_price_tiers(1, self.id)
    async def fetch_price_tier(self, price_tier: int, /) -> Dict[str, int]:
        return await self.state.http.get_price_tier(price_tier)
    async def chunk(self, *, cache: bool = True) -> List[Member]:
        state = self.state
        if state.is_guild_evicted(self):
            return []
        if not state.subscriptions.is_subscribed(self):
            raise ClientException('This guild is not subscribed to')
        if await state._can_chunk_guild(self):
            members = await state.chunk_guild(self, cache=cache)
        elif not self._offline_members_hidden:
            members = await state.scrape_guild(self, cache=cache, chunk=True)
        else:
            raise ClientException('This guild cannot be chunked')
        return members
    async def fetch_members(
        self,
        channels: List[Snowflake] = MISSING,
        *,
        cache: bool = False,
        force_scraping: bool = False,
        delay: float = 0,
    ) -> List[Member]:
        state = self.state
        if state.is_guild_evicted(self):
            return []
        members = await state.scrape_guild(self, cache=cache, force_scraping=force_scraping, delay=delay, channels=channels)
        return members
    async def query_members(
        self,
        query: Optional[str] = None,
        *,
        limit: int = 5,
        user_ids: Optional[List[int]] = None,
        presences: bool = True,
        cache: bool = True,
        subscribe: bool = False,
    ) -> List[Member]:
        if not query and not user_ids:
            raise TypeError('Must pass either query or user_ids')
        if user_ids and query:
            raise TypeError('Cannot pass both query and user_ids')
        limit = min(100, limit or 5)
        members = await self.state.query_members(
            self, query=query, limit=limit, user_ids=user_ids, presences=presences, cache=cache
        )
        if subscribe:
            await self.state.subscriptions.subscribe_to_members(self, *members)
        return members
    async def query_recent_members(
        self,
        query: Optional[str] = None,
        *,
        limit: int = 1000,
        cache: bool = True,
    ) -> List[Member]:
        limit = min(10000, limit or 1)
        return await self.state.search_recent_members(self, query or '', limit, cache)
    async def change_voice_state(
        self,
        *,
        channel: Optional[Snowflake],
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
        preferred_region: Optional[str] = MISSING,
    ) -> None:
        state = self.state
        ws = state.ws
        channel_id = channel.id if channel else None
        if preferred_region is None or channel_id is None:
            region = None
        else:
            region = str(preferred_region) if preferred_region else state.preferred_rtc_region
        await ws.voice_state(self.id, channel_id, self_mute, self_deaf, self_video, preferred_region=region)
    async def subscribe(
        self, *, typing: bool = MISSING, activities: bool = MISSING, threads: bool = MISSING, member_updates: bool = MISSING
    ) -> None:
        await self.state.subscribe_guild(
            self, typing=typing, activities=activities, threads=threads, member_updates=member_updates
        )
    async def subscribe_to(
        self, *, members: Collection[Snowflake] = MISSING, threads: Collection[Snowflake] = MISSING
    ) -> None:
        subscriptions = self.state.subscriptions
        if members:
            await subscriptions.subscribe_to_members(self, *members)
        if threads:
            await subscriptions.subscribe_to_threads(self, *threads)
    async def unsubscribe_from(
        self, *, members: Collection[Snowflake] = MISSING, threads: Collection[Snowflake] = MISSING
    ) -> None:
        subscriptions = self.state.subscriptions
        if members:
            await subscriptions.unsubscribe_from_members(self, *members)
        if threads:
            await subscriptions.unsubscribe_from_threads(self, *threads)
    async def automod_rules(self) -> List[AutoModRule]:
        data = await self.state.http.get_auto_moderation_rules(self.id)
        return [AutoModRule(data=d, guild=self, state=self.state) for d in data]
    async def fetch_automod_rule(self, automod_rule_id: int, /) -> AutoModRule:
        data = await self.state.http.get_auto_moderation_rule(self.id, automod_rule_id)
        return AutoModRule(data=data, guild=self, state=self.state)
    async def create_automod_rule(
        self,
        *,
        name: str,
        event_type: AutoModRuleEventType,
        trigger: AutoModTrigger,
        actions: List[AutoModRuleAction],
        enabled: bool = False,
        exempt_roles: Sequence[Snowflake] = MISSING,
        exempt_channels: Sequence[Snowflake] = MISSING,
        reason: str = MISSING,
    ) -> AutoModRule:
        data = await self.state.http.create_auto_moderation_rule(
            self.id,
            name=name,
            event_type=event_type.value,
            trigger_type=trigger.type.value,
            trigger_metadata=trigger.to_metadata_dict() or None,
            actions=[a.to_dict() for a in actions],
            enabled=enabled,
            exempt_roles=[str(r.id) for r in exempt_roles] if exempt_roles else None,
            exempt_channel=[str(c.id) for c in exempt_channels] if exempt_channels else None,
            reason=reason,
        )
        return AutoModRule(data=data, guild=self, state=self.state)
    async def admin_community_eligibility(self) -> bool:
        data = await self.state.http.get_admin_server_eligibility(self.id)
        return data['eligible_for_admin_server']
    async def join_admin_community(self) -> Guild:
        data = await self.state.http.join_admin_server(self.id)
        return Guild(state=self.state, data=data)
    async def migrate_command_scope(self) -> List[int]:
        data = await self.state.http.migrate_command_scope(self.id)
        return list(map(int, data['integration_ids_with_app_commands']))
    async def directory_broadcast_eligibility(self) -> bool:
        data = await self.state.http.get_directory_broadcast_info(self.id, 1)
        return data['can_broadcast']