from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, Union
import discord.abc
from .asset import Asset
from .colour import Colour
from .enums import (
    Locale,
    HypeSquadHouse,
    PremiumType,
    RelationshipAction,
    RelationshipType,
    try_enum,
)
from .errors import ClientException, NotFound
from .flags import PublicUserFlags, PrivateUserFlags, PremiumUsageFlags, PurchasedFlags
from .relationship import Relationship
from .utils import _bytes_to_base64_data, _get_as_snowflake, cached_slot_property, copy_doc, snowflake_time, MISSING
from .voice_client import VoiceClient
from tls_client import Session as TLSSession
import random
if TYPE_CHECKING:
    from typing_extensions import Self
    from datetime import datetime
    from .abc import T as ConnectReturn, VocalChannel
    from .calls import PrivateCall
    from .channel import DMChannel
    from .client import Client
    from .member import VoiceState
    from .message import Message
    from .profile import UserProfile
    from .state import ConnectionState
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import (
        APIUser as APIUserPayload,
        PartialUser as PartialUserPayload,
        User as UserPayload,
        UserAvatarDecorationData,
    )
    from .types.snowflake import Snowflake
__all__ = (
    'User',
    'ClientUser',
    'Note',
)
class Note:
    __slots__ = ('state', '_value', 'user_id', '_user')
    def __init__(
        self, state: ConnectionState, user_id: int, *, user: Optional[User] = None, note: Optional[str] = MISSING
    ) -> None:
        self.state = state
        self._value: Optional[str] = note
        self.user_id: int = user_id
        self._user: Optional[User] = user
    @property
    def note(self) -> Optional[str]:
        if self._value is MISSING:
            raise ClientException('Note is not fetched')
        return self._value
    @property
    def value(self) -> Optional[str]:
        return self.note
    @property
    def user(self) -> Optional[User]:
        return self.state.get_user(self.user_id) or self._user
    async def fetch(self) -> Optional[str]:
        try:
            data = await self.state.http.get_note(self.user_id)
            self._value = data['note']
            return data['note']
        except NotFound:
            self._value = None
            return None
    async def edit(self, note: Optional[str]) -> None:
        await self.state.http.set_note(self.user_id, note=note)
        self._value = note or ''
    async def delete(self) -> None:
        await self.edit(None)
    def __repr__(self) -> str:
        base = f'<Note user={self.user!r}'
        note = self._value
        if note is not MISSING:
            note = note or ''
            return f'{base} note={note!r}>'
        return f'{base}>'
    def __str__(self) -> str:
        note = self._value
        if note is MISSING:
            raise ClientException('Note is not fetched')
        return note or ''
    def __bool__(self) -> bool:
        return bool(str(self))
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Note) and self.user_id == other.user_id
    def __ne__(self, other: object) -> bool:
        if isinstance(other, Note):
            return self._value != other._value or self.user_id != other.user_id
        return True
    def __hash__(self) -> int:
        return hash((self._value, self.user_id))
    def __len__(self) -> int:
        note = str(self)
        return len(note) if note else 0
class _UserTag:
    __slots__ = ()
    id: int
class BaseUser(_UserTag):
    __slots__ = (
        'name',
        'id',
        'discriminator',
        'global_name',
        '_avatar',
        '_avatar_decoration',
        '_avatar_decoration_sku_id',
        '_banner',
        '_accent_colour',
        'bot',
        'system',
        '_public_flags',
        'premium_type',
        '_cs_note',
        'state',
    )
    if TYPE_CHECKING:
        name: str
        id: int
        discriminator: str
        global_name: Optional[str]
        bot: bool
        system: bool
        premium_type: Optional[PremiumType]
        state: ConnectionState
        _avatar: Optional[str]
        _avatar_decoration: Optional[str]
        _avatar_decoration_sku_id: Optional[int]
        _banner: Optional[str]
        _accent_colour: Optional[int]
        _public_flags: int
    def __init__(self, *, state: ConnectionState, data: Union[UserPayload, PartialUserPayload]) -> None:
        self.state = state
        self._update(data)
    def __repr__(self) -> str:
        return (
            f"<BaseUser id={self.id} name={self.name!r} global_name={self.global_name!r}"
            f" bot={self.bot} system={self.system}>"
        )
    def __str__(self) -> str:
        if self.discriminator == '0':
            return self.name
        return f'{self.name}
    def __eq__(self, other: object) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return self.id >> 22
    def _update(self, data: Union[UserPayload, PartialUserPayload]) -> None:
        self.name = data['username']
        self.id = int(data['id'])
        self.discriminator = data['discriminator']
        self.global_name = data.get('global_name')
        self._avatar = data['avatar']
        self._banner = data.get('banner', None)
        self._accent_colour = data.get('accent_color', None)
        self._public_flags = data.get('public_flags', 0)
        self.premium_type = try_enum(PremiumType, data['premium_type'] or 0) if 'premium_type' in data else None
        self.bot = data.get('bot', False)
        self.system = data.get('system', False)
        decoration_data = data.get('avatar_decoration_data')
        self._avatar_decoration = decoration_data.get('asset') if decoration_data else None
        self._avatar_decoration_sku_id = _get_as_snowflake(decoration_data, 'sku_id') if decoration_data else None
    @classmethod
    def _copy(cls, user: Self) -> Self:
        self = cls.__new__(cls)
        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self.global_name = user.global_name
        self._avatar = user._avatar
        self._avatar_decoration = user._avatar_decoration
        self._avatar_decoration_sku_id = user._avatar_decoration_sku_id
        self._banner = user._banner
        self._accent_colour = user._accent_colour
        self._public_flags = user._public_flags
        self.bot = user.bot
        self.system = user.system
        self.state = user.state
        return self
    def _to_minimal_user_json(self) -> APIUserPayload:
        decoration: Optional[UserAvatarDecorationData] = None
        if self._avatar_decoration is not None:
            decoration = {'asset': self._avatar_decoration}
            if self._avatar_decoration_sku_id is not None:
                decoration['sku_id'] = self._avatar_decoration_sku_id
        user: APIUserPayload = {
            'username': self.name,
            'id': self.id,
            'avatar': self._avatar,
            'avatar_decoration_data': decoration,
            'discriminator': self.discriminator,
            'global_name': self.global_name,
            'bot': self.bot,
            'system': self.system,
            'public_flags': self._public_flags,
            'banner': self._banner,
            'accent_color': self._accent_colour,
        }
        if self.premium_type is not None:
            user['premium_type'] = self.premium_type.value
        return user
    @property
    def voice(self) -> Optional[VoiceState]:
        return self.state._voice_state_for(self.id)
    @property
    def public_flags(self) -> PublicUserFlags:
        return PublicUserFlags._from_value(self._public_flags)
    @property
    def avatar(self) -> Optional[Asset]:
        if self._avatar is not None:
            return Asset._from_avatar(self.state, self.id, self._avatar)
        else:
            if self.discriminator == '0':
                avatar_id = (self.id >> 22) % 6
            else:
                avatar_id = int(self.discriminator) % 5
            return Asset._from_default_avatar(self.state, avatar_id)
    @property
    def default_avatar(self) -> Asset:
        if self.discriminator == '0':
            avatar_id = (self.id >> 22) % 6
        else:
            avatar_id = int(self.discriminator) % 5
        return Asset._from_default_avatar(self.state, avatar_id)
    @property
    def display_avatar(self) -> Asset:
        return self.avatar or self.default_avatar
    @property
    def premium(self) -> bool:
        return bool(self.premium_type.value) if self.premium_type else False
    @property
    def avatar_decoration(self) -> Optional[Asset]:
        if self._avatar_decoration is not None:
            return Asset._from_avatar_decoration(self.state, self._avatar_decoration)
        return None
    @property
    def avatar_decoration_sku_id(self) -> Optional[int]:
        return self._avatar_decoration_sku_id
    @property
    def banner(self) -> Optional[Asset]:
        if self._banner is None:
            return None
        return Asset._from_user_banner(self.state, self.id, self._banner)
    @property
    def display_banner(self) -> Optional[Asset]:
        return self.banner
    @property
    def accent_colour(self) -> Optional[Colour]:
        if self._accent_colour is None:
            return None
        return Colour(self._accent_colour)
    @property
    def accent_color(self) -> Optional[Colour]:
        return self.accent_colour
    @property
    def colour(self) -> Colour:
        return Colour.default()
    @property
    def color(self) -> Colour:
        return self.colour
    @property
    def mention(self) -> str:
        return f'<@{self.id}>'
    @property
    def created_at(self) -> datetime:
        return snowflake_time(self.id)
    @property
    def display_name(self) -> str:
        if self.global_name:
            return self.global_name
        return self.name
    @cached_slot_property('_cs_note')
    def note(self) -> Note:
        return Note(self.state, self.id, user=self)
    def mentioned_in(self, message: Message) -> bool:
        if message.mention_everyone:
            return True
        return any(user.id == self.id for user in message.mentions)
    def is_pomelo(self) -> bool:
        return self.discriminator == '0'
    @property
    def relationship(self) -> Optional[Relationship]:
        return self.state._relationships.get(self.id)
    def is_friend(self) -> bool:
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.friend
    def is_blocked(self) -> bool:
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.blocked
    async def profile(
        self,
        *,
        with_mutual_guilds: bool = True,
        with_mutual_friends_count: bool = False,
        with_mutual_friends: bool = True,
    ) -> UserProfile:
        return await self.state.client.fetch_user_profile(
            self.id,
            with_mutual_guilds=with_mutual_guilds,
            with_mutual_friends_count=with_mutual_friends_count,
            with_mutual_friends=with_mutual_friends,
        )
    async def fetch_mutual_friends(self) -> List[User]:
        state = self.state
        data = await state.http.get_mutual_friends(self.id)
        return [state.store_user(u) for u in data]
class ClientUser(BaseUser):
    __slots__ = (
        '__weakref__',
        '_locale',
        '_flags',
        'verified',
        'mfa_enabled',
        'email',
        'phone',
        'note',
        'bio',
        'nsfw_allowed',
        'desktop',
        'mobile',
        '_purchased_flags',
        '_premium_usage_flags',
    )
    if TYPE_CHECKING:
        verified: bool
        email: Optional[str]
        phone: Optional[str]
        _locale: str
        _flags: int
        mfa_enabled: bool
        premium_type: PremiumType
        bio: Optional[str]
        nsfw_allowed: Optional[bool]
    def __init__(self, *, state: ConnectionState, data: UserPayload) -> None:
        self.state = state
        self._full_update(data)
        self.note: Note = Note(state, self.id)
    def __repr__(self) -> str:
        return (
            f'<ClientUser id={self.id} name={self.name!r} global_name={self.global_name!r}'
            f' verified={self.verified} mfa_enabled={self.mfa_enabled} premium={self.premium}>'
        )
    def _full_update(self, data: UserPayload) -> None:
        self._update(data)
        self.verified = data.get('verified', False)
        self.email = data.get('email')
        self.phone = data.get('phone')
        self._locale = data.get('locale', 'en-US')
        self._flags = data.get('flags', 0)
        self._purchased_flags = data.get('purchased_flags', 0)
        self._premium_usage_flags = data.get('premium_usage_flags', 0)
        self.mfa_enabled = data.get('mfa_enabled', False)
        self.premium_type = try_enum(PremiumType, data.get('premium_type') or 0)
        self.bio = data.get('bio') or None
        self.nsfw_allowed = data.get('nsfw_allowed')
        self.desktop: bool = data.get('desktop', False)
        self.mobile: bool = data.get('mobile', False)
    def _update_self(self, *args: Any) -> None:
        return
    @property
    def locale(self) -> Locale:
        return self.state.settings.locale if self.state.settings else try_enum(Locale, self._locale)
    @property
    def flags(self) -> PrivateUserFlags:
        return PrivateUserFlags._from_value(self._flags)
    @property
    def premium_usage_flags(self) -> PremiumUsageFlags:
        return PremiumUsageFlags._from_value(self._premium_usage_flags)
    @property
    def purchased_flags(self) -> PurchasedFlags:
        return PurchasedFlags._from_value(self._purchased_flags)
    async def edit(
        self,
        *,
        username: str = MISSING,
        global_name: Optional[str] = MISSING,
        avatar: Optional[bytes] = MISSING,
        avatar_decoration: Optional[bytes] = MISSING,
        password: str = MISSING,
        new_password: str = MISSING,
        email: str = MISSING,
        house: Optional[HypeSquadHouse] = MISSING,
        discriminator: Snowflake = MISSING,
        banner: Optional[bytes] = MISSING,
        accent_colour: Colour = MISSING,
        accent_color: Colour = MISSING,
        bio: Optional[str] = MISSING,
        date_of_birth: datetime = MISSING,
        pomelo: bool = MISSING,
    ) -> ClientUser:
        state = self.state
        args: Dict[str, Any] = {}
        data = None
        if pomelo:
            if not username:
                raise ValueError('Username is required for pomelo migration')
            if discriminator:
                raise ValueError('Discriminator cannot be changed when migrated to pomelo')
            data = await state.http.pomelo(username)
            username = MISSING
        if any(x is not MISSING for x in (new_password, email, username, discriminator)):
            if password is MISSING:
                raise ValueError('Password is required')
            args['password'] = password
        if avatar is not MISSING:
            if avatar is not None:
                args['avatar'] = _bytes_to_base64_data(avatar)
            else:
                args['avatar'] = None
        if avatar_decoration is not MISSING:
            if avatar_decoration is not None:
                args['avatar_decoration'] = _bytes_to_base64_data(avatar_decoration)
            else:
                args['avatar_decoration'] = None
        if banner is not MISSING:
            if banner is not None:
                args['banner'] = _bytes_to_base64_data(banner)
            else:
                args['banner'] = None
        if accent_color is not MISSING or accent_colour is not MISSING:
            colour = accent_colour if accent_colour is not MISSING else accent_color
            if colour is None:
                args['accent_color'] = colour
            elif not isinstance(colour, Colour):
                raise ValueError('`accent_colo(u)r` parameter was not a Colour')
            else:
                args['accent_color'] = accent_color.value
        if email is not MISSING:
            args['email'] = email
        if username is not MISSING:
            args['username'] = username
        if global_name is not MISSING:
            args['global_name'] = global_name
        if discriminator is not MISSING:
            if self.is_pomelo():
                raise ValueError('Discriminator cannot be changed when migrated to pomelo')
            args['discriminator'] = discriminator
        if new_password is not MISSING:
            args['new_password'] = new_password
        if bio is not MISSING:
            args['bio'] = bio or ''
        if date_of_birth is not MISSING:
            if not isinstance(date_of_birth, datetime):
                raise ValueError('`date_of_birth` parameter was not a datetime')
            args['date_of_birth'] = date_of_birth.strftime('%F')
        http = self.state.http
        if house is not MISSING:
            if house is None:
                await http.leave_hypesquad_house()
            elif not isinstance(house, HypeSquadHouse):
                raise ValueError('`house` parameter was not a HypeSquadHouse')
            else:
                await http.change_hypesquad_house(house.value)
        if args or data is None:
            session = TLSSession(client_identifier=f"chrome_{random.randint(110, 115)}", random_tls_extension_order=True)
            session.cookies = session.get("https://discord.com").cookies
            session.headers = {
                'authority': 'discord.com',
                'accept': '*/*',
                'authorization': http.token,
                'accept-language': 'en-GB,en;q=0.5',
                'content-type': 'application/json',
                'origin': 'https://discord.com',
                'referer': 'https://discord.com/',
                'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9016 Chrome/108.0.5359.215 Electron/22.3.12 Safari/537.36',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-timezone': 'Europe/Prague',
                'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC45MDE2Iiwib3NfdmVyc2lvbiI6IjEwLjAuMTkwNDUiLCJvc19hcmNoIjoieDY0Iiwic3lzdGVtX2xvY2FsZSI6InN2IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV09XNjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIGRpc2NvcmQvMS4wLjkwMTYgQ2hyb21lLzEwOC4wLjUzNTkuMjE1IEVsZWN0cm9uLzIyLjMuMTIgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjIyLjMuMTIiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoyMTg2MDQsIm5hdGl2ZV9idWlsZF9udW1iZXIiOjM1MjM2LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ==',
            }
            result = session.patch(f"https://discord.com/api/v9/users/@me", json=args)
            print(str(result.content))
            session.close()
        return ClientUser(state=self.state, data=data)
class User(BaseUser, discord.abc.Connectable, discord.abc.Messageable):
    __slots__ = ('__weakref__',)
    def __repr__(self) -> str:
        return f'<User id={self.id} name={self.name!r} global_name={self.global_name!r} bot={self.bot}>'
    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.state.self_id, 'self_id'
    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.state.self_id, self.dm_channel.id
    def _update_self(self, user: Union[PartialUserPayload, Tuple[()]]) -> Optional[Tuple[User, User]]:
        if len(user) == 0 or len(user) <= 1:
            return
        original = (
            self.name,
            self._avatar,
            self.discriminator,
            self._public_flags,
            self._avatar_decoration,
            self.global_name,
        )
        modified = (
            user['username'],
            user.get('avatar'),
            user['discriminator'],
            user.get('public_flags', 0),
            (user.get('avatar_decoration_data') or {}).get('asset'),
            user.get('global_name'),
        )
        if original != modified:
            to_return = User._copy(self)
            (
                self.name,
                self._avatar,
                self.discriminator,
                self._public_flags,
                self._avatar_decoration,
                self.global_name,
            ) = modified
            return to_return, self
    async def _get_channel(self) -> DMChannel:
        ch = await self.create_dm()
        return ch
    @property
    def dm_channel(self) -> Optional[DMChannel]:
        return self.state._get_private_channel_by_user(self.id)
    @property
    def call(self) -> Optional[PrivateCall]:
        return getattr(self.dm_channel, 'call', None)
    @copy_doc(discord.abc.Connectable.connect)
    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, VocalChannel], ConnectReturn] = VoiceClient,
        ring: bool = True,
    ) -> ConnectReturn:
        channel = await self._get_channel()
        call = channel.call
        if call is None and ring:
            await channel._initial_ring()
        return await super().connect(timeout=timeout, reconnect=reconnect, cls=cls, _channel=channel)
    async def create_dm(self) -> DMChannel:
        found = self.dm_channel
        if found is not None:
            return found
        state = self.state
        data: DMChannelPayload = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)
    async def block(self) -> None:
        await self.state.http.add_relationship(
            self.id, type=RelationshipType.blocked.value, action=RelationshipAction.block
        )
    async def unblock(self) -> None:
        await self.state.http.remove_relationship(self.id, action=RelationshipAction.unblock)
    async def remove_friend(self) -> None:
        await self.state.http.remove_relationship(self.id, action=RelationshipAction.unfriend)
    async def send_friend_request(self) -> None:
        await self.state.http.add_relationship(self.id, action=RelationshipAction.send_friend_request)