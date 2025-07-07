from typing import Optional, TypedDict
from .activity import BasePresenceUpdate
from .snowflake import SnowflakeList
from .user import PartialUser
class Nickname(TypedDict):
    nick: str
class PartialMember(TypedDict):
    roles: SnowflakeList
    joined_at: str
    deaf: bool
    mute: bool
    flags: int
class Member(PartialMember, total=False):
    avatar: Optional[str]
    user: PartialUser
    nick: str
    premium_since: Optional[str]
    pending: bool
    communication_disabled_until: str
class _OptionalMemberWithUser(PartialMember, total=False):
    avatar: Optional[str]
    nick: str
    premium_since: Optional[str]
    pending: bool
    communication_disabled_until: str
class MemberWithUser(_OptionalMemberWithUser):
    user: PartialUser
class MemberWithPresence(MemberWithUser):
    presence: BasePresenceUpdate
class PrivateMember(MemberWithUser):
    bio: str
    banner: Optional[str]
class UserWithMember(PartialUser, total=False):
    member: _OptionalMemberWithUser