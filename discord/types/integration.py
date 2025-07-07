from __future__ import annotations
from typing import List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired
from .application import IntegrationApplication, RoleConnectionMetadata
from .guild import Guild
from .snowflake import Snowflake
from .user import APIUser
class IntegrationAccount(TypedDict):
    id: str
    name: str
IntegrationExpireBehavior = Literal[0, 1]
class PartialIntegration(TypedDict):
    id: Snowflake
    name: str
    type: IntegrationType
    account: IntegrationAccount
    application_id: NotRequired[Snowflake]
IntegrationType = Literal['twitch', 'youtube', 'discord', 'guild_subscription']
class BaseIntegration(PartialIntegration):
    enabled: bool
    user: NotRequired[APIUser]
class StreamIntegration(BaseIntegration):
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    subscriber_count: int
    revoked: bool
    expire_behavior: IntegrationExpireBehavior
    expire_grace_period: int
    syncing: bool
    synced_at: str
class BotIntegration(BaseIntegration):
    application: IntegrationApplication
    scopes: List[str]
    role_connections_metadata: NotRequired[List[RoleConnectionMetadata]]
class ConnectionIntegration(BaseIntegration):
    guild: Guild
Integration = Union[BaseIntegration, StreamIntegration, BotIntegration, ConnectionIntegration]