from typing import List, Optional, TypedDict
from typing_extensions import NotRequired
from .guild import Guild
from .snowflake import Snowflake
class HubWaitlist(TypedDict):
    email: str
    email_domain: str
    school: str
    user_id: Snowflake
class HubGuild(TypedDict):
    id: Snowflake
    name: str
    icon: Optional[str]
class EmailDomainLookup(TypedDict):
    guilds_info: NotRequired[List[HubGuild]]
    has_matching_guild: bool
class EmailDomainVerification(TypedDict):
    guild: Guild
    joined: bool