from typing import List, Optional, Tuple, TypedDict
from typing_extensions import NotRequired, Required
from .application import ApplicationInstallParams, RoleConnection
from .emoji import Emoji
from .member import PrivateMember as ProfileMember
from .snowflake import Snowflake
from .user import APIUser, PartialConnection, PremiumType
class ProfileUser(APIUser):
    bio: str
class ProfileEffect(TypedDict):
    id: Snowflake
class ProfileMetadata(TypedDict, total=False):
    guild_id: int
    bio: str
    banner: Optional[str]
    accent_color: Optional[int]
    theme_colors: Optional[Tuple[int, int]]
    emoji: Optional[Emoji]
    popout_animation_particle_type: Optional[Snowflake]
    profile_effect: Optional[ProfileEffect]
    pronouns: Required[str]
class MutualGuild(TypedDict):
    id: Snowflake
    nick: Optional[str]
class ProfileApplication(TypedDict):
    id: Snowflake
    verified: bool
    popular_application_command_ids: NotRequired[List[Snowflake]]
    primary_sku_id: NotRequired[Snowflake]
    flags: int
    custom_install_url: NotRequired[str]
    install_params: NotRequired[ApplicationInstallParams]
class ProfileBadge(TypedDict):
    id: str
    description: str
    icon: str
    link: NotRequired[str]
class Profile(TypedDict):
    user: ProfileUser
    user_profile: Optional[ProfileMetadata]
    badges: List[ProfileBadge]
    guild_member: NotRequired[ProfileMember]
    guild_member_profile: NotRequired[Optional[ProfileMetadata]]
    guild_badges: List[ProfileBadge]
    mutual_guilds: NotRequired[List[MutualGuild]]
    mutual_friends_count: NotRequired[int]
    connected_accounts: List[PartialConnection]
    application_role_connections: NotRequired[List[RoleConnection]]
    premium_type: Optional[PremiumType]
    premium_since: Optional[str]
    premium_guild_since: Optional[str]
    legacy_username: Optional[str]
    application: NotRequired[ProfileApplication]