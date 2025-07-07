from __future__ import annotations
from typing import List, Optional, TypedDict
from typing_extensions import NotRequired
from .application import PartialApplication
from .snowflake import Snowflake
from .user import PartialUser
class OAuth2Token(TypedDict):
    id: Snowflake
    application: PartialApplication
    scopes: List[str]
class BotUser(PartialUser):
    approximate_guild_count: int
class OAuth2Guild(TypedDict):
    id: Snowflake
    name: str
    icon: Optional[str]
    permissions: str
    mfa_level: int
class OAuth2Authorization(TypedDict):
    authorized: bool
    user: PartialUser
    application: PartialApplication
    bot: NotRequired[BotUser]
    guilds: NotRequired[List[OAuth2Guild]]
    redirect_uri: NotRequired[Optional[str]]
class OAuth2Location(TypedDict):
    location: str
class WebhookChannel(TypedDict):
    id: Snowflake
    name: str