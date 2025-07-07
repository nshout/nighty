from __future__ import annotations
import datetime
import inspect
import itertools
from operator import attrgetter
from typing import Any, Awaitable, Callable, Collection, Dict, List, Optional, TYPE_CHECKING, Tuple, TypeVar, Union
import discord.abc
from . import utils
from .asset import Asset
from .utils import MISSING
from .user import BaseUser, User, _UserTag
from .permissions import Permissions
from .enums import Status, try_enum
from .errors import ClientException
from .colour import Colour
from .object import Object
from .flags import MemberFlags
__all__ = (
    'VoiceState',
    'Member',
)
T = TypeVar('T', bound=type)
if TYPE_CHECKING:
    from typing_extensions import Self
    from .activity import ActivityTypes
    from .asset import Asset
    from .channel import DMChannel, VoiceChannel, StageChannel, GroupChannel
    from .flags import PublicUserFlags
    from .guild import Guild
    from .profile import MemberProfile
    from .types.activity import (
        BasePresenceUpdate,
    )
    from .types.member import (
        MemberWithUser as MemberWithUserPayload,
        Member as MemberPayload,
        UserWithMember as UserWithMemberPayload,
    )
    from .types.gateway import GuildMemberUpdateEvent
    from .types.user import PartialUser as PartialUserPayload
    from .abc import Snowflake
    from .state import ConnectionState, Presence
    from .message import Message
    from .role import Role
    from .types.voice import BaseVoiceState as VoiceStatePayload
    from .user import Note
    from .relationship import Relationship
    from .calls import PrivateCall
    from .enums import PremiumType
    VocalGuildChannel = Union[VoiceChannel, StageChannel]
    ConnectableChannel = Union[VocalGuildChannel, DMChannel, GroupChannel]
class VoiceState:
    __slots__ = (
        'session_id',
        'deaf',
        'mute',
        'self_mute',
        'self_stream',
        'self_video',
        'self_deaf',
        'afk',
        'channel',
        'requested_to_speak_at',
        'suppress',
    )
    def __init__(self, *, data: VoiceStatePayload, channel: Optional[ConnectableChannel] = None):
        self.session_id: Optional[str] = data.get('session_id')
        self._update(data, channel)
    def _update(self, data: VoiceStatePayload, channel: Optional[ConnectableChannel]):
        self.self_mute: bool = data.get('self_mute', False)
        self.self_deaf: bool = data.get('self_deaf', False)
        self.self_stream: bool = data.get('self_stream', False)
        self.self_video: bool = data.get('self_video', False)
        self.afk: bool = data.get('suppress', False)
        self.mute: bool = data.get('mute', False)
        self.deaf: bool = data.get('deaf', False)
        self.suppress: bool = data.get('suppress', False)
        self.requested_to_speak_at: Optional[datetime.datetime] = utils.parse_time(data.get('request_to_speak_timestamp'))
        self.channel: Optional[ConnectableChannel] = channel
    def __repr__(self) -> str:
        attrs = [
            ('self_mute', self.self_mute),
            ('self_deaf', self.self_deaf),
            ('self_stream', self.self_stream),
            ('suppress', self.suppress),
            ('requested_to_speak_at', self.requested_to_speak_at),
            ('channel', self.channel),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {inner}>'
def flatten_user(cls: T) -> T:
    for attr, value in itertools.chain(BaseUser.__dict__.items(), User.__dict__.items()):
        if attr.startswith('_'):
            continue
        if attr in cls.__dict__:
            continue
        if not hasattr(value, '__annotations__') or isinstance(value, utils.CachedSlotProperty):
            getter = attrgetter('_user.' + attr)
            setattr(cls, attr, property(getter, doc=f'Equivalent to :attr:`User.{attr}`'))
        else:
            def generate_function(x):
                if inspect.iscoroutinefunction(value):
                    async def general(self, *args, **kwargs):
                        return await getattr(self._user, x)(*args, **kwargs)
                else:
                    def general(self, *args, **kwargs):
                        return getattr(self._user, x)(*args, **kwargs)
                general.__name__ = x
                return general
            func = generate_function(attr)
            func = utils.copy_doc(value)(func)
            setattr(cls, attr, func)
    return cls
@flatten_user
class Member(discord.abc.Messageable, discord.abc.Connectable, _UserTag):
    __slots__ = (
        '_roles',
        'joined_at',
        'premium_since',
        'guild',
        'pending',
        'nick',
        'timed_out_until',
        '_presence',
        '_user',
        'state',
        '_avatar',
        '_flags',
    )
    if TYPE_CHECKING:
        name: str
        id: int
        discriminator: str
        global_name: Optional[str]
        bot: bool
        system: bool
        created_at: datetime.datetime
        default_avatar: Asset
        avatar: Optional[Asset]
        avatar_decoration: Optional[Asset]
        avatar_decoration_sku_id: Optional[int]
        note: Note
        relationship: Optional[Relationship]
        is_friend: Callable[[], bool]
        is_blocked: Callable[[], bool]
        dm_channel: Optional[DMChannel]
        call: Optional[PrivateCall]
        create_dm: Callable[[], Awaitable[DMChannel]]
        block: Callable[[], Awaitable[None]]
        unblock: Callable[[], Awaitable[None]]
        remove_friend: Callable[[], Awaitable[None]]
        fetch_mutual_friends: Callable[[], Awaitable[List[User]]]
        public_flags: PublicUserFlags
        premium_type: Optional[PremiumType]
        banner: Optional[Asset]
        accent_color: Optional[Colour]
        accent_colour: Optional[Colour]
    def __init__(self, *, data: MemberWithUserPayload, guild: Guild, state: ConnectionState):
        self.state: ConnectionState = state
        self._user: User = state.store_user(data['user'])
        self.guild: Guild = guild
        self.joined_at: Optional[datetime.datetime] = utils.parse_time(data.get('joined_at'))
        self.premium_since: Optional[datetime.datetime] = utils.parse_time(data.get('premium_since'))
        self._roles: utils.SnowflakeList = utils.SnowflakeList(map(int, data['roles']))
        self._presence: Optional[Presence] = None
        self.nick: Optional[str] = data.get('nick', None)
        self.pending: bool = data.get('pending', False)
        self._avatar: Optional[str] = data.get('avatar')
        self._flags: int = data.get('flags', 0)
        self.timed_out_until: Optional[datetime.datetime] = utils.parse_time(data.get('communication_disabled_until'))
    def __str__(self) -> str:
        return str(self._user)
    def __repr__(self) -> str:
        return (
            f'<Member id={self._user.id} name={self._user.name!r} global_name={self._user.global_name!r}'
            f' bot={self._user.bot} nick={self.nick!r} guild={self.guild!r}>'
        )
    def __eq__(self, other: object) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return hash(self._user)
    @classmethod
    def _from_message(cls, *, message: Message, data: MemberPayload) -> Self:
        author = message.author
        data['user'] = author._to_minimal_user_json()
        return cls(data=data, guild=message.guild, state=message.state)
    def _update_from_message(self, data: MemberPayload) -> None:
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self.premium_since = utils.parse_time(data.get('premium_since'))
        self._roles = utils.SnowflakeList(map(int, data['roles']))
        self.nick = data.get('nick', None)
        self.pending = data.get('pending', False)
        self.timed_out_until = utils.parse_time(data.get('communication_disabled_until'))
        self._flags = data.get('flags', 0)
    @classmethod
    def _try_upgrade(cls, *, data: UserWithMemberPayload, guild: Guild, state: ConnectionState) -> Union[User, Self]:
        try:
            member_data = data.pop('member')
        except KeyError:
            return state.create_user(data)
        else:
            member_data['user'] = data
            return cls(data=member_data, guild=guild, state=state)
    @classmethod
    def _copy(cls, member: Self) -> Self:
        self = cls.__new__(cls)
        self._roles = utils.SnowflakeList(member._roles, is_sorted=True)
        self.joined_at = member.joined_at
        self.premium_since = member.premium_since
        self._presence = member._presence
        self.guild = member.guild
        self.nick = member.nick
        self.pending = member.pending
        self.timed_out_until = member.timed_out_until
        self._flags = member._flags
        self.state = member.state
        self._avatar = member._avatar
        self._user = member._user
        return self
    def _update(self, data: Union[GuildMemberUpdateEvent, MemberWithUserPayload]) -> Optional[Member]:
        old = Member._copy(self)
        try:
            self.nick = data['nick']
        except KeyError:
            pass
        try:
            self.pending = data['pending']
        except KeyError:
            pass
        self.premium_since = utils.parse_time(data.get('premium_since'))
        self.timed_out_until = utils.parse_time(data.get('communication_disabled_until'))
        self._roles = utils.SnowflakeList(map(int, data['roles']))
        self._avatar = data.get('avatar')
        self._flags = data.get('flags', 0)
        attrs = {'joined_at', 'premium_since', '_roles', '_avatar', 'timed_out_until', 'nick', 'pending'}
        if any(getattr(self, attr) != getattr(old, attr) for attr in attrs):
            return old
    def _presence_update(
        self, data: BasePresenceUpdate, user: Union[PartialUserPayload, Tuple[()]]
    ) -> Optional[Tuple[User, User]]:
        self._presence = self.state.create_presence(data)
        return self._user._update_self(user)
    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.state.self_id, 'self_id'
    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.state.self_id, self.dm_channel.id
    async def _get_channel(self) -> DMChannel:
        ch = await self.create_dm()
        return ch
    @property
    def presence(self) -> Presence:
        state = self.state
        return self._presence or state.get_presence(self._user.id, self.guild.id) or state.create_offline_presence()
    @property
    def status(self) -> Status:
        return try_enum(Status, self.presence.client_status.status)
    @property
    def raw_status(self) -> str:
        return self.presence.client_status.status
    @property
    def mobile_status(self) -> Status:
        return try_enum(Status, self.presence.client_status.mobile or 'offline')
    @property
    def desktop_status(self) -> Status:
        return try_enum(Status, self.presence.client_status.desktop or 'offline')
    @property
    def web_status(self) -> Status:
        return try_enum(Status, self.presence.client_status.web or 'offline')
    def is_on_mobile(self) -> bool:
        return self.presence.client_status.mobile is not None
    @property
    def colour(self) -> Colour:
        roles = self.roles[1:]
        for role in reversed(roles):
            if role.colour.value:
                return role.colour
        return Colour.default()
    @property
    def color(self) -> Colour:
        return self.colour
    @property
    def roles(self) -> List[Role]:
        result = []
        g = self.guild
        for role_id in self._roles:
            role = g.get_role(role_id)
            if role:
                result.append(role)
        result.append(g.default_role)
        result.sort()
        return result
    @property
    def display_icon(self) -> Optional[Union[str, Asset]]:
        roles = self.roles[1:]
        for role in reversed(roles):
            icon = role.display_icon
            if icon:
                return icon
        return None
    @property
    def mention(self) -> str:
        return f'<@{self._user.id}>'
    @property
    def display_name(self) -> str:
        return self.nick or self.global_name or self.name
    @property
    def display_avatar(self) -> Asset:
        return self.guild_avatar or self._user.avatar or self._user.default_avatar
    @property
    def guild_avatar(self) -> Optional[Asset]:
        if self._avatar is None:
            return None
        return Asset._from_guild_avatar(self.state, self.guild.id, self.id, self._avatar)
    @property
    def activities(self) -> Tuple[ActivityTypes, ...]:
        return self.presence.activities
    @property
    def activity(self) -> Optional[ActivityTypes]:
        if self.activities:
            return self.activities[0]
    def mentioned_in(self, message: Message) -> bool:
        if message.guild is None or message.guild.id != self.guild.id:
            return False
        if self._user.mentioned_in(message):
            return True
        return any(self._roles.has(role.id) for role in message.role_mentions)
    @property
    def top_role(self) -> Role:
        guild = self.guild
        if len(self._roles) == 0:
            return guild.default_role
        return max(guild.get_role(rid) or guild.default_role for rid in self._roles)
    @property
    def guild_permissions(self) -> Permissions:
        if self.guild.owner_id == self.id:
            return Permissions.all()
        base = Permissions.none()
        for r in self.roles:
            base.value |= r.permissions.value
        if base.administrator:
            return Permissions.all()
        if self.is_timed_out():
            base.value &= Permissions._timeout_mask()
        return base
    @property
    def voice(self) -> Optional[VoiceState]:
        return self.guild._voice_state_for(self._user.id)
    @property
    def flags(self) -> MemberFlags:
        return MemberFlags._from_value(self._flags)
    async def ban(
        self,
        *,
        delete_message_days: int = MISSING,
        delete_message_seconds: int = MISSING,
        reason: Optional[str] = None,
    ) -> None:
        await self.guild.ban(
            self,
            reason=reason,
            delete_message_days=delete_message_days,
            delete_message_seconds=delete_message_seconds,
        )
    async def unban(self, *, reason: Optional[str] = None) -> None:
        await self.guild.unban(self, reason=reason)
    async def kick(self, *, reason: Optional[str] = None) -> None:
        await self.guild.kick(self, reason=reason)
    async def edit(
        self,
        *,
        nick: Optional[str] = MISSING,
        mute: bool = MISSING,
        deafen: bool = MISSING,
        suppress: bool = MISSING,
        roles: Collection[discord.abc.Snowflake] = MISSING,
        voice_channel: Optional[VocalGuildChannel] = MISSING,
        timed_out_until: Optional[datetime.datetime] = MISSING,
        avatar: Optional[bytes] = MISSING,
        banner: Optional[bytes] = MISSING,
        bio: Optional[str] = MISSING,
        bypass_verification: bool = MISSING,
        reason: Optional[str] = None,
    ) -> Optional[Member]:
        http = self.state.http
        guild_id = self.guild.id
        me = self._user.id == self.state.self_id
        payload: Dict[str, Any] = {}
        data = None
        if nick is not MISSING:
            payload['nick'] = nick
        if avatar is not MISSING:
            payload['avatar'] = utils._bytes_to_base64_data(avatar) if avatar is not None else None
        if banner is not MISSING:
            payload['banner'] = utils._bytes_to_base64_data(banner) if banner is not None else None
        if bio is not MISSING:
            payload['bio'] = bio or ''
        if me and payload:
            data = await http.edit_me(self.guild.id, **payload)
            payload = {}
        if deafen is not MISSING:
            payload['deaf'] = deafen
        if mute is not MISSING:
            payload['mute'] = mute
        if suppress is not MISSING:
            voice_state_payload: Dict[str, Any] = {
                'suppress': suppress,
            }
            if self.voice is not None and self.voice.channel is not None:
                voice_state_payload['channel_id'] = self.voice.channel.id
            if suppress or self.bot:
                voice_state_payload['request_to_speak_timestamp'] = None
            if me:
                await http.edit_my_voice_state(guild_id, voice_state_payload)
            else:
                if not suppress:
                    voice_state_payload['request_to_speak_timestamp'] = datetime.datetime.utcnow().isoformat()
                await http.edit_voice_state(guild_id, self.id, voice_state_payload)
        if voice_channel is not MISSING:
            payload['channel_id'] = voice_channel and voice_channel.id
        if roles is not MISSING:
            payload['roles'] = tuple(r.id for r in roles)
        if timed_out_until is not MISSING:
            if timed_out_until is None:
                payload['communication_disabled_until'] = None
            else:
                if timed_out_until.tzinfo is None:
                    raise TypeError(
                        'timed_out_until must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                    )
                payload['communication_disabled_until'] = timed_out_until.isoformat()
        if bypass_verification is not MISSING:
            flags = MemberFlags._from_value(self._flags)
            flags.bypasses_verification = bypass_verification
            payload['flags'] = flags.value
        if payload:
            data = await http.edit_member(guild_id, self.id, reason=reason, **payload)
        if data:
            return Member(data=data, guild=self.guild, state=self.state)
    async def request_to_speak(self) -> None:
        if self.voice is None or self.voice.channel is None:
            raise ClientException('Cannot request to speak while not connected to a voice channel.')
        payload = {
            'channel_id': self.voice.channel.id,
            'request_to_speak_timestamp': datetime.datetime.utcnow().isoformat(),
        }
        if self.state.self_id != self.id:
            payload['suppress'] = False
            await self.state.http.edit_voice_state(self.guild.id, self.id, payload)
        else:
            await self.state.http.edit_my_voice_state(self.guild.id, payload)
    async def move_to(self, channel: Optional[VocalGuildChannel], *, reason: Optional[str] = None) -> None:
        await self.edit(voice_channel=channel, reason=reason)
    async def timeout(
        self, until: Optional[Union[datetime.timedelta, datetime.datetime]], /, *, reason: Optional[str] = None
    ) -> None:
        if until is None:
            timed_out_until = None
        elif isinstance(until, datetime.timedelta):
            timed_out_until = utils.utcnow() + until
        elif isinstance(until, datetime.datetime):
            timed_out_until = until
        else:
            raise TypeError(f'expected None, datetime.datetime, or datetime.timedelta not {until.__class__!r}')
        await self.edit(timed_out_until=timed_out_until, reason=reason)
    async def add_roles(self, *roles: Snowflake, reason: Optional[str] = None, atomic: bool = True) -> None:
        r
        if not atomic:
            new_roles = utils._unique(Object(id=r.id) for s in (self.roles[1:], roles) for r in s)
            await self.edit(roles=new_roles, reason=reason)
        else:
            req = self.state.http.add_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                await req(guild_id, user_id, role.id, reason=reason)
    async def remove_roles(self, *roles: Snowflake, reason: Optional[str] = None, atomic: bool = True) -> None:
        r
        if not atomic:
            new_roles = [Object(id=r.id) for r in self.roles[1:]]
            for role in roles:
                try:
                    new_roles.remove(Object(id=role.id))
                except ValueError:
                    pass
            await self.edit(roles=new_roles, reason=reason)
        else:
            req = self.state.http.remove_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                await req(guild_id, user_id, role.id, reason=reason)
    def get_role(self, role_id: int, /) -> Optional[Role]:
        return self.guild.get_role(role_id) if self._roles.has(role_id) else None
    def is_timed_out(self) -> bool:
        if self.timed_out_until is not None:
            return utils.utcnow() < self.timed_out_until
        return False
    async def profile(
        self,
        *,
        with_mutual_guilds: bool = True,
        with_mutual_friends_count: bool = False,
        with_mutual_friends: bool = True,
    ) -> MemberProfile:
        return await self.guild.fetch_member_profile(
            self._user.id,
            with_mutual_guilds=with_mutual_guilds,
            with_mutual_friends_count=with_mutual_friends_count,
            with_mutual_friends=with_mutual_friends,
        )