from __future__ import annotations
from typing import List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired, Required
from .snowflake import Snowflake, SnowflakeList
from .member import Member, UserWithMember
from .user import User
from .emoji import PartialEmoji
from .embed import Embed
from .channel import ChannelType
from .components import MessageActionRow
from .interactions import MessageInteraction
from .application import BaseApplication
from .sticker import StickerItem
from .threads import Thread, ThreadMember
class PartialMessage(TypedDict):
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]
class ChannelMention(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    type: ChannelType
    name: str
class Reaction(TypedDict):
    count: int
    me: bool
    emoji: PartialEmoji
class Attachment(TypedDict):
    id: Snowflake
    filename: str
    size: int
    url: str
    proxy_url: str
    height: NotRequired[Optional[int]]
    width: NotRequired[Optional[int]]
    description: NotRequired[str]
    content_type: NotRequired[str]
    spoiler: NotRequired[bool]
    ephemeral: NotRequired[bool]
    duration_secs: NotRequired[float]
    waveform: NotRequired[str]
    flags: NotRequired[int]
MessageActivityType = Literal[1, 2, 3, 5]
class MessageActivity(TypedDict):
    type: MessageActivityType
    party_id: str
class MessageReference(TypedDict, total=False):
    message_id: Snowflake
    channel_id: Required[Snowflake]
    guild_id: Snowflake
    fail_if_not_exists: bool
class Call(TypedDict):
    participants: List[Snowflake]
    ended_timestamp: Optional[str]
class RoleSubscriptionData(TypedDict):
    role_subscription_listing_id: Snowflake
    tier_name: str
    total_months_subscribed: int
    is_renewal: bool
MessageType = Literal[
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32
]
class Message(PartialMessage):
    id: Snowflake
    author: User
    content: str
    timestamp: str
    edited_timestamp: Optional[str]
    tts: bool
    mention_everyone: bool
    mentions: List[UserWithMember]
    mention_roles: SnowflakeList
    attachments: List[Attachment]
    embeds: List[Embed]
    pinned: bool
    type: MessageType
    member: NotRequired[Member]
    mention_channels: NotRequired[List[ChannelMention]]
    reactions: NotRequired[List[Reaction]]
    nonce: NotRequired[Union[int, str]]
    webhook_id: NotRequired[Snowflake]
    activity: NotRequired[MessageActivity]
    application: NotRequired[BaseApplication]
    application_id: NotRequired[Snowflake]
    message_reference: NotRequired[MessageReference]
    flags: NotRequired[int]
    sticker_items: NotRequired[List[StickerItem]]
    referenced_message: NotRequired[Optional[Message]]
    interaction: NotRequired[MessageInteraction]
    components: NotRequired[List[MessageActionRow]]
    position: NotRequired[int]
    call: NotRequired[Call]
    role_subscription_data: NotRequired[RoleSubscriptionData]
    hit: NotRequired[bool]
    thread: NotRequired[Thread]
AllowedMentionType = Literal['roles', 'users', 'everyone']
class AllowedMentions(TypedDict):
    parse: List[AllowedMentionType]
    roles: SnowflakeList
    users: SnowflakeList
    replied_user: bool
class MessageSearchIndexingResult(TypedDict):
    message: str
    code: int
    documents_indexed: int
    retry_after: int
class MessageSearchResult(TypedDict):
    messages: List[List[Message]]
    threads: NotRequired[List[Thread]]
    members: NotRequired[List[ThreadMember]]
    total_results: int
    analytics_id: str
    doing_deep_historical_index: NotRequired[bool]
MessageSearchAuthorType = Literal['user', '-user', 'bot', '-bot', 'webhook', '-webhook']
MessageSearchHasType = Literal[
    'image',
    '-image',
    'sound',
    '-sound',
    'video',
    '-video',
    'file',
    '-file',
    'sticker',
    '-sticker',
    'embed',
    '-embed',
    'link',
    '-link',
]
MessageSearchSortType = Literal['timestamp', 'relevance']
MessageSearchSortOrder = Literal['desc', 'asc']
class PartialAttachment(TypedDict):
    id: NotRequired[Snowflake]
    filename: str
    description: NotRequired[str]
    uploaded_filename: NotRequired[str]
class UploadedAttachment(TypedDict):
    id: NotRequired[Snowflake]
    filename: str
    file_size: int
class CloudAttachment(TypedDict):
    id: NotRequired[Snowflake]
    upload_url: str
    upload_filename: str
class CloudAttachments(TypedDict):
    attachments: List[CloudAttachment]