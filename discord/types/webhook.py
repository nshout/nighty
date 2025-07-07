from __future__ import annotations
from typing import Literal, Optional, TypedDict
from typing_extensions import NotRequired
from .snowflake import Snowflake
from .user import User
from .channel import PartialChannel
class SourceGuild(TypedDict):
    id: int
    name: str
    icon: str
class SourceChannel(TypedDict):
    id: int
    name: str
WebhookType = Literal[1, 2, 3]
class FollowerWebhook(TypedDict):
    channel_id: Snowflake
    webhook_id: Snowflake
    source_channel: NotRequired[PartialChannel]
    source_guild: NotRequired[SourceGuild]
class PartialWebhook(TypedDict):
    id: Snowflake
    type: WebhookType
    guild_id: NotRequired[Snowflake]
    user: NotRequired[User]
    token: NotRequired[str]
class _FullWebhook(TypedDict, total=False):
    name: Optional[str]
    avatar: Optional[str]
    channel_id: Snowflake
    application_id: Optional[Snowflake]
class Webhook(PartialWebhook, _FullWebhook):
    ...