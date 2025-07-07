from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Union
from .asset import Asset
from .enums import ChannelType, InviteTarget, InviteType, NSFWLevel, VerificationLevel, try_enum
from .flags import InviteFlags
from .mixins import Hashable
from .object import Object
from .scheduled_event import ScheduledEvent
from .stage_instance import StageInstance
from .utils import MISSING, _generate_session_id, _get_as_snowflake, parse_time, snowflake_time
from .welcome_screen import WelcomeScreen
__all__ = (
    'PartialInviteChannel',
    'PartialInviteGuild',
    'Invite',
)
if TYPE_CHECKING:
    import datetime
    from typing_extensions import Self
    from .abc import GuildChannel, Snowflake
    from .application import PartialApplication
    from .channel import DMChannel, GroupChannel
    from .guild import Guild
    from .message import Message
    from .state import ConnectionState
    from .types.channel import PartialChannel as InviteChannelPayload
    from .types.invite import (
        GatewayInvite as GatewayInvitePayload,
        Invite as InvitePayload,
        InviteGuild as InviteGuildPayload,
    )
    from .types.channel import (
        PartialChannel as InviteChannelPayload,
    )
    from .state import ConnectionState
    from .abc import GuildChannel
    from .user import User
    InviteGuildType = Union[Guild, 'PartialInviteGuild', Object]
    InviteChannelType = Union[GuildChannel, 'PartialInviteChannel', Object, DMChannel, GroupChannel]
class PartialInviteChannel:
    __slots__ = ('state', 'id', 'name', 'type', 'recipients', '_icon')
    def __new__(cls, data: Optional[InviteChannelPayload], *args, **kwargs):
        if data is None:
            return
        return super().__new__(cls)
    def __init__(self, data: Optional[InviteChannelPayload], state: ConnectionState):
        if data is None:
            return
        self.state = state
        self.id: int = int(data['id'])
        self.name: Optional[str] = data.get('name')
        self.type: ChannelType = try_enum(ChannelType, data['type'])
        self.recipients: Optional[List[str]] = (
            [user['username'] for user in data.get('recipients', [])]
            if self.type in (ChannelType.private, ChannelType.group)
            else None
        )
        self._icon: Optional[str] = data.get('icon')
    def __str__(self) -> str:
        if self.name:
            return self.name
        recipients = self.recipients or []
        if self.type == ChannelType.group:
            return ', '.join(recipients) if recipients else 'Unnamed'
        return f'Direct Message with {recipients[0] if recipients else "Unknown User"}'
    def __repr__(self) -> str:
        return f'<PartialInviteChannel id={self.id} name={self.name} type={self.type!r}>'
    @property
    def mention(self) -> str:
        return f'<
    @property
    def created_at(self) -> datetime.datetime:
        return snowflake_time(self.id)
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='channel')
class PartialInviteGuild:
    __slots__ = (
        'state',
        '_icon',
        '_banner',
        '_splash',
        'features',
        'id',
        'name',
        'verification_level',
        'description',
        'vanity_url_code',
        'nsfw_level',
        'premium_subscription_count',
    )
    def __init__(self, state: ConnectionState, data: InviteGuildPayload, id: int):
        self.state: ConnectionState = state
        self.id: int = id
        self.name: str = data['name']
        self.features: List[str] = data.get('features', [])
        self._icon: Optional[str] = data.get('icon')
        self._banner: Optional[str] = data.get('banner')
        self._splash: Optional[str] = data.get('splash')
        self.verification_level: VerificationLevel = try_enum(VerificationLevel, data.get('verification_level'))
        self.description: Optional[str] = data.get('description')
        self.vanity_url_code: Optional[str] = data.get('vanity_url_code')
        self.nsfw_level: NSFWLevel = try_enum(NSFWLevel, data.get('nsfw_level', 0))
        self.premium_subscription_count: int = data.get('premium_subscription_count') or 0
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} features={self.features} '
            f'description={self.description!r}>'
        )
    @property
    def created_at(self) -> datetime.datetime:
        return snowflake_time(self.id)
    @property
    def vanity_url(self) -> Optional[str]:
        if self.vanity_url_code is None:
            return None
        return f'{Invite.BASE}/{self.vanity_url_code}'
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
    def _resolve_channel(self, channel_id: Optional[int], /):
        return
class Invite(Hashable):
    r
    __slots__ = (
        'max_age',
        'code',
        'guild',
        'created_at',
        'uses',
        'temporary',
        'max_uses',
        'inviter',
        'channel',
        'target_user',
        'target_type',
        'state',
        'approximate_member_count',
        'approximate_presence_count',
        'target_application',
        'expires_at',
        'scheduled_event',
        'scheduled_event_id',
        'stage_instance',
        '_message',
        'welcome_screen',
        'type',
        'new_member',
        'show_verification_form',
        '_flags',
    )
    BASE = 'https://discord.gg'
    def __init__(
        self,
        *,
        state: ConnectionState,
        data: InvitePayload,
        guild: Optional[Union[PartialInviteGuild, Guild]] = None,
        channel: Optional[Union[PartialInviteChannel, GuildChannel, GroupChannel]] = None,
        welcome_screen: Optional[WelcomeScreen] = None,
        message: Optional[Message] = None,
    ):
        self.state: ConnectionState = state
        self.type: InviteType = try_enum(InviteType, data.get('type', 0))
        self.max_age: Optional[int] = data.get('max_age')
        self.code: str = data['code']
        self.guild: Optional[InviteGuildType] = self._resolve_guild(data.get('guild'), guild)
        self.created_at: Optional[datetime.datetime] = parse_time(data.get('created_at'))
        self.temporary: Optional[bool] = data.get('temporary')
        self.uses: Optional[int] = data.get('uses')
        self.max_uses: Optional[int] = data.get('max_uses')
        self.approximate_presence_count: Optional[int] = data.get('approximate_presence_count')
        self.approximate_member_count: Optional[int] = data.get('approximate_member_count')
        self._flags: int = data.get('flags', 0)
        self._message: Optional[Message] = message
        if self.type in (InviteType.group_dm, InviteType.friend):
            self.temporary = False
            if self.max_uses is None and self.type is InviteType.group_dm:
                self.max_uses = 0
        expires_at = data.get('expires_at', None)
        self.expires_at: Optional[datetime.datetime] = parse_time(expires_at) if expires_at else None
        inviter_data = data.get('inviter')
        self.inviter: Optional[User] = None if inviter_data is None else self.state.create_user(inviter_data)
        self.channel: Optional[InviteChannelType] = self._resolve_channel(data.get('channel'), channel)
        target_user_data = data.get('target_user')
        self.target_user: Optional[User] = None if target_user_data is None else self.state.create_user(target_user_data)
        self.target_type: InviteTarget = try_enum(InviteTarget, data.get("target_type", 0))
        application = data.get('target_application')
        if application is not None:
            from .application import PartialApplication
            application = PartialApplication(data=application, state=state)
        self.target_application: Optional[PartialApplication] = application
        self.welcome_screen = welcome_screen
        scheduled_event = data.get('guild_scheduled_event')
        self.scheduled_event: Optional[ScheduledEvent] = (
            ScheduledEvent(
                state=self.state,
                data=scheduled_event,
            )
            if scheduled_event
            else None
        )
        self.scheduled_event_id: Optional[int] = self.scheduled_event.id if self.scheduled_event else None
        stage_instance = data.get('stage_instance')
        self.stage_instance: Optional[StageInstance] = (
            StageInstance.from_invite(self, stage_instance) if stage_instance else None
        )
        self.new_member: bool = data.get('new_member', False)
        self.show_verification_form: bool = data.get('show_verification_form', False)
    @classmethod
    def from_incomplete(cls, *, state: ConnectionState, data: InvitePayload, message: Optional[Message] = None) -> Self:
        guild: Optional[Union[Guild, PartialInviteGuild]]
        try:
            guild_data = data['guild']
        except KeyError:
            guild = None
            welcome_screen = None
        else:
            guild_id = int(guild_data['id'])
            guild = state._get_guild(guild_id)
            if guild is None:
                guild = PartialInviteGuild(state, guild_data, guild_id)
            welcome_screen = guild_data.get('welcome_screen')
            if welcome_screen is not None:
                welcome_screen = WelcomeScreen(data=welcome_screen, guild=guild)
        channel_data = data.get('channel')
        if channel_data and channel_data.get('type') == ChannelType.private.value:
            channel_data['recipients'] = [data['inviter']] if 'inviter' in data else []
        channel = PartialInviteChannel(channel_data, state)
        channel = (state.get_channel(channel.id) or channel) if channel else None
        return cls(state=state, data=data, guild=guild, channel=channel, welcome_screen=welcome_screen, message=message)
    @classmethod
    def from_gateway(cls, *, state: ConnectionState, data: GatewayInvitePayload) -> Self:
        guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        guild: Optional[Union[Guild, Object]] = state._get_guild(guild_id)
        channel_id = _get_as_snowflake(data, 'channel_id')
        if guild is not None:
            channel = (guild.get_channel(channel_id) or Object(id=channel_id)) if channel_id is not None else None
        else:
            guild = state._get_or_create_unavailable_guild(guild_id) if guild_id is not None else None
            channel = Object(id=channel_id) if channel_id is not None else None
        return cls(state=state, data=data, guild=guild, channel=channel)
    def _resolve_guild(
        self,
        data: Optional[InviteGuildPayload],
        guild: Optional[Union[Guild, PartialInviteGuild]] = None,
    ) -> Optional[InviteGuildType]:
        if guild is not None:
            return guild
        if data is None:
            return None
        guild_id = int(data['id'])
        return PartialInviteGuild(self.state, data, guild_id)
    def _resolve_channel(
        self,
        data: Optional[InviteChannelPayload],
        channel: Optional[Union[PartialInviteChannel, GuildChannel, GroupChannel]] = None,
    ) -> Optional[InviteChannelType]:
        if channel is not None:
            return channel
        if data is None:
            return None
        return PartialInviteChannel(data, self.state)
    def __str__(self) -> str:
        return self.url
    def __repr__(self) -> str:
        return (
            f'<Invite code={self.code!r} type={self.type!r} '
            f'guild={self.guild!r} '
            f'members={self.approximate_member_count}>'
        )
    def __hash__(self) -> int:
        return hash(self.code)
    @property
    def id(self) -> str:
        return self.code
    @property
    def url(self) -> str:
        url = self.BASE + '/' + self.code
        if self.scheduled_event_id is not None:
            url += '?event=' + str(self.scheduled_event_id)
        return url
    @property
    def flags(self) -> InviteFlags:
        return InviteFlags._from_value(self._flags)
    def set_scheduled_event(self, scheduled_event: Snowflake, /) -> Self:
        self.scheduled_event_id = scheduled_event.id
        try:
            self.scheduled_event = self.guild.get_scheduled_event(scheduled_event.id)
        except AttributeError:
            self.scheduled_event = None
        return self
    async def use(self) -> Invite:
        state = self.state
        type = self.type
        kwargs = {}
        if not self._message:
            kwargs = {
                'guild_id': getattr(self.guild, 'id', MISSING),
                'channel_id': getattr(self.channel, 'id', MISSING),
                'channel_type': getattr(self.channel, 'type', MISSING),
            }
        data = await state.http.accept_invite(
            self.code, type, state.session_id or _generate_session_id(), message=self._message, **kwargs
        )
        return Invite.from_incomplete(state=state, data=data, message=self._message)
    async def accept(self) -> Invite:
        return await self.use()
    async def delete(self, *, reason: Optional[str] = None) -> Invite:
        state = self.state
        data = await state.http.delete_invite(self.code, reason=reason)
        return Invite.from_incomplete(state=state, data=data)