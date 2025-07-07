from __future__ import annotations
from typing import TypedDict, List, Optional
from typing_extensions import NotRequired
from .user import User
from .team import Team
from .snowflake import Snowflake
class BaseAppInfo(TypedDict):
    id: Snowflake
    name: str
    verify_key: str
    icon: Optional[str]
    summary: str
    description: str
    cover_image: Optional[str]
    flags: NotRequired[int]
    rpc_origins: List[str]
class AppInfo(BaseAppInfo):
    owner: User
    bot_public: NotRequired[bool]
    bot_require_code_grant: NotRequired[bool]
    integration_public: NotRequired[bool]
    integration_require_code_grant: NotRequired[bool]
    team: NotRequired[Team]
    guild_id: NotRequired[Snowflake]
    primary_sku_id: NotRequired[Snowflake]
    slug: NotRequired[str]
    terms_of_service_url: NotRequired[str]
    privacy_policy_url: NotRequired[str]
    hook: NotRequired[bool]
    max_participants: NotRequired[int]
    interactions_endpoint_url: NotRequired[str]
    verification_state: int
    store_application_state: int
    rpc_application_state: int
    interactions_endpoint_url: str
class PartialAppInfo(BaseAppInfo, total=False):
    hook: bool
    terms_of_service_url: str
    privacy_policy_url: str
    max_participants: int