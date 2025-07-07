from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Tuple
from . import utils
from .application import ApplicationInstallParams
from .asset import Asset, AssetMixin
from .colour import Colour
from .connections import PartialConnection
from .enums import PremiumType, try_enum
from .flags import ApplicationFlags
from .member import Member
from .mixins import Hashable
from .partial_emoji import PartialEmoji
from .user import User
if TYPE_CHECKING:
    from datetime import datetime
    from .guild import Guild
    from .state import ConnectionState
    from .types.profile import (
        Profile as ProfilePayload,
        ProfileApplication as ProfileApplicationPayload,
        ProfileBadge as ProfileBadgePayload,
        ProfileMetadata as ProfileMetadataPayload,
        MutualGuild as MutualGuildPayload,
    )
    from .types.user import PartialUser as PartialUserPayload
__all__ = (
    'ProfileMetadata',
    'ApplicationProfile',
    'MutualGuild',
    'ProfileBadge',
    'UserProfile',
    'MemberProfile',
)
class Profile:
    if TYPE_CHECKING:
        id: int
        bot: bool
        state: ConnectionState
    def __init__(self, **kwargs) -> None:
        data: ProfilePayload = kwargs.pop('data')
        user = data['user']
        profile = data.get('user_profile')
        mutual_friends: List[PartialUserPayload] = kwargs.pop('mutual_friends', None)
        member = data.get('guild_member')
        member_profile = data.get('guild_member_profile')
        if member is not None:
            member['user'] = user
            kwargs['data'] = member
        else:
            kwargs['data'] = user
        super().__init__(**kwargs)
        state = self.state
        self.metadata = ProfileMetadata(id=self.id, state=state, data=profile)
        if member is not None:
            self.guild_metadata = ProfileMetadata(id=self.id, state=state, data=member_profile)
        self.legacy_username: Optional[str] = data.get('legacy_username')
        self.bio: Optional[str] = user['bio'] or None
        guild_premium_since = getattr(self, 'premium_since', utils.MISSING)
        if guild_premium_since is not utils.MISSING:
            self.guild_premium_since = guild_premium_since
        self.premium_type: Optional[PremiumType] = try_enum(PremiumType, data.get('premium_type') or 0) if profile else None
        self.premium_since: Optional[datetime] = utils.parse_time(data.get('premium_since'))
        self.premium_guild_since: Optional[datetime] = utils.parse_time(data.get('premium_guild_since'))
        self.connections: List[PartialConnection] = [PartialConnection(d) for d in data['connected_accounts']]
        self.badges: List[ProfileBadge] = [
            ProfileBadge(state=state, data=d) for d in data.get('badges', []) + data.get('guild_badges', [])
        ]
        self.mutual_guilds: Optional[List[MutualGuild]] = (
            [MutualGuild(state=state, data=d) for d in data['mutual_guilds']] if 'mutual_guilds' in data else None
        )
        self.mutual_friends: Optional[List[User]] = self._parse_mutual_friends(mutual_friends)
        self._mutual_friends_count: Optional[int] = data.get('mutual_friends_count')
        application = data.get('application')
        self.application: Optional[ApplicationProfile] = ApplicationProfile(data=application) if application else None
    def _parse_mutual_friends(self, mutual_friends: List[PartialUserPayload]) -> Optional[List[User]]:
        if self.bot:
            return []
        if mutual_friends is None:
            return
        state = self.state
        return [state.store_user(friend) for friend in mutual_friends]
    @property
    def mutual_friends_count(self) -> Optional[int]:
        if self.bot:
            return 0
        if self._mutual_friends_count is not None:
            return self._mutual_friends_count
        if self.mutual_friends is not None:
            return len(self.mutual_friends)
    @property
    def premium(self) -> bool:
        return self.premium_since is not None
class ProfileMetadata:
    __slots__ = (
        '_id',
        'state',
        'bio',
        'pronouns',
        'emoji',
        'popout_animation_particle_type',
        'effect_id',
        '_banner',
        '_accent_colour',
        '_theme_colours',
        '_guild_id',
    )
    def __init__(self, *, id: int, state: ConnectionState, data: Optional[ProfileMetadataPayload]) -> None:
        self._id = id
        self.state = state
        if data is None:
            data = {'pronouns': ''}
        self.bio: Optional[str] = data.get('bio') or None
        self.pronouns: Optional[str] = data.get('pronouns') or None
        self.emoji: Optional[PartialEmoji] = PartialEmoji.from_dict_stateful(data['emoji'], state) if data.get('emoji') else None
        self.popout_animation_particle_type: Optional[int] = utils._get_as_snowflake(data, 'popout_animation_particle_type')
        self.effect_id: Optional[int] = utils._get_as_snowflake(data['profile_effect'], 'id') if data.get('profile_effect') else None
        self._banner: Optional[str] = data.get('banner')
        self._accent_colour: Optional[int] = data.get('accent_color')
        self._theme_colours: Optional[Tuple[int, int]] = tuple(data['theme_colors']) if data.get('theme_colors') else None
        self._guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
    def __repr__(self) -> str:
        return f'<ProfileMetadata bio={self.bio!r} pronouns={self.pronouns!r}>'
    @property
    def banner(self) -> Optional[Asset]:
        if self._banner is None:
            return None
        return Asset._from_user_banner(self.state, self._id, self._banner)
    @property
    def accent_colour(self) -> Optional[Colour]:
        if self._accent_colour is None:
            return None
        return Colour(self._accent_colour)
    @property
    def accent_color(self) -> Optional[Colour]:
        return self.accent_colour
    @property
    def theme_colours(self) -> Optional[Tuple[Colour, Colour]]:
        if self._theme_colours is None:
            return None
        return tuple(Colour(c) for c in self._theme_colours)
    @property
    def theme_colors(self) -> Optional[Tuple[Colour, Colour]]:
        return self.theme_colours
class ApplicationProfile(Hashable):
    __slots__ = (
        'id',
        'verified',
        'popular_application_command_ids',
        'primary_sku_id',
        '_flags',
        'custom_install_url',
        'install_params',
    )
    def __init__(self, data: ProfileApplicationPayload) -> None:
        self.id: int = int(data['id'])
        self.verified: bool = data.get('verified', False)
        self.popular_application_command_ids: List[int] = [int(id) for id in data.get('popular_application_command_ids', [])]
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self._flags: int = data.get('flags', 0)
        params = data.get('install_params')
        self.custom_install_url: Optional[str] = data.get('custom_install_url')
        self.install_params: Optional[ApplicationInstallParams] = (
            ApplicationInstallParams.from_application(self, params) if params else None
        )
    def __repr__(self) -> str:
        return f'<ApplicationProfile id={self.id} verified={self.verified}>'
    @property
    def created_at(self) -> datetime:
        return utils.snowflake_time(self.id)
    @property
    def flags(self) -> ApplicationFlags:
        return ApplicationFlags._from_value(self._flags)
    @property
    def install_url(self) -> Optional[str]:
        return self.custom_install_url or self.install_params.url if self.install_params else None
    @property
    def primary_sku_url(self) -> Optional[str]:
        if self.primary_sku_id:
            return f'https://discord.com/store/skus/{self.primary_sku_id}/unknown'
class MutualGuild(Hashable):
    __slots__ = ('id', 'nick', 'state')
    def __init__(self, *, state: ConnectionState, data: MutualGuildPayload) -> None:
        self.state = state
        self.id: int = int(data['id'])
        self.nick: Optional[str] = data.get('nick')
    def __repr__(self) -> str:
        return f'<MutualGuild guild={self.guild!r} nick={self.nick!r}>'
    @property
    def guild(self) -> Guild:
        return self.state._get_or_create_unavailable_guild(self.id)
class ProfileBadge(AssetMixin, Hashable):
    __slots__ = ('id', 'description', 'link', '_icon', 'state')
    def __init__(self, *, state: ConnectionState, data: ProfileBadgePayload) -> None:
        self.state = state
        self.id: str = data['id']
        self.description: str = data.get('description', '')
        self.link: Optional[str] = data.get('link')
        self._icon: str = data['icon']
    def __repr__(self) -> str:
        return f'<ProfileBadge id={self.id!r} description={self.description!r}>'
    def __hash__(self) -> int:
        return hash(self.id)
    def __str__(self) -> str:
        return self.description
    @property
    def animated(self) -> bool:
        return False
    @property
    def url(self) -> str:
        return f'{Asset.BASE}/badge-icons/{self._icon}.png'
class UserProfile(Profile, User):
    __slots__ = (
        'bio',
        'premium_type',
        'premium_since',
        'premium_guild_since',
        'connections',
        'badges',
        'mutual_guilds',
        'mutual_friends',
        '_mutual_friends_count',
        'application',
    )
    def __repr__(self) -> str:
        return f'<UserProfile id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot} system={self.system} premium={self.premium}>'
    @property
    def display_bio(self) -> Optional[str]:
        return self.bio
class MemberProfile(Profile, Member):
    __slots__ = (
        'bio',
        'guild_premium_since',
        'premium_type',
        'premium_since',
        'premium_guild_since',
        'connections',
        'badges',
        'mutual_guilds',
        'mutual_friends',
        '_mutual_friends_count',
        'application',
        '_banner',
        'guild_bio',
    )
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        data = kwargs['data']
        member = data['guild_member']
        self._banner: Optional[str] = member.get('banner')
        self.guild_bio: Optional[str] = member.get('bio') or None
    def __repr__(self) -> str:
        return (
            f'<MemberProfile id={self._user.id} name={self._user.name!r} discriminator={self._user.discriminator!r}'
            f' bot={self._user.bot} nick={self.nick!r} premium={self.premium} guild={self.guild!r}>'
        )
    @property
    def display_banner(self) -> Optional[Asset]:
        return self.guild_banner or self._user.banner
    @property
    def guild_banner(self) -> Optional[Asset]:
        if self._banner is None:
            return None
        return Asset._from_guild_banner(self.state, self.guild.id, self.id, self._banner)
    @property
    def display_bio(self) -> Optional[str]:
        return self.guild_bio or self.bio