from typing import List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired
from .user import PartialUser
from .snowflake import Snowflake
from .guild import MemberWithUser
from .threads import ThreadMetadata, ThreadMember, ThreadArchiveDuration, ThreadType
OverwriteType = Literal[0, 1]
class PermissionOverwrite(TypedDict):
    id: Snowflake
    type: OverwriteType
    allow: str
    deny: str
ChannelTypeWithoutThread = Literal[0, 1, 2, 3, 4, 5, 6, 13, 14, 15]
ChannelType = Union[ChannelTypeWithoutThread, ThreadType]
class _BaseChannel(TypedDict):
    id: Snowflake
class _BaseGuildChannel(_BaseChannel):
    guild_id: Snowflake
    position: int
    permission_overwrites: List[PermissionOverwrite]
    parent_id: Optional[Snowflake]
    name: str
    flags: int
class PartialRecipient(TypedDict):
    username: str
class PartialChannel(_BaseChannel):
    name: Optional[str]
    type: ChannelType
    icon: NotRequired[Optional[str]]
    recipients: NotRequired[List[PartialRecipient]]
class _BaseTextChannel(_BaseGuildChannel, total=False):
    topic: str
    last_message_id: Optional[Snowflake]
    last_pin_timestamp: str
    rate_limit_per_user: int
    default_thread_rate_limit_per_user: int
    default_auto_archive_duration: ThreadArchiveDuration
    nsfw: bool
class TextChannel(_BaseTextChannel):
    type: Literal[0]
class NewsChannel(_BaseTextChannel):
    type: Literal[5]
VideoQualityMode = Literal[1, 2]
class VoiceChannel(_BaseTextChannel):
    type: Literal[2]
    bitrate: int
    user_limit: int
    rtc_region: NotRequired[Optional[str]]
    video_quality_mode: NotRequired[VideoQualityMode]
class CategoryChannel(_BaseGuildChannel):
    type: Literal[4]
class StageChannel(_BaseGuildChannel):
    type: Literal[13]
    bitrate: int
    user_limit: int
    rtc_region: NotRequired[Optional[str]]
    topic: NotRequired[str]
    nsfw: bool
class DirectoryChannel(_BaseGuildChannel):
    type: Literal[14]
    last_message_id: Optional[Snowflake]
    topic: Optional[str]
class ThreadChannel(_BaseChannel):
    type: Literal[10, 11, 12]
    guild_id: Snowflake
    parent_id: Snowflake
    owner_id: Snowflake
    nsfw: bool
    last_message_id: Optional[Snowflake]
    rate_limit_per_user: int
    message_count: int
    member_count: int
    thread_metadata: ThreadMetadata
    member: NotRequired[ThreadMember]
    owner_id: NotRequired[Snowflake]
    rate_limit_per_user: NotRequired[int]
    last_message_id: NotRequired[Optional[Snowflake]]
    last_pin_timestamp: NotRequired[str]
    applied_tags: NotRequired[List[Snowflake]]
    flags: int
class DefaultReaction(TypedDict):
    emoji_id: Optional[Snowflake]
    emoji_name: Optional[str]
class ForumTag(TypedDict):
    id: Snowflake
    name: str
    moderated: bool
    emoji_id: Optional[Snowflake]
    emoji_name: Optional[str]
ForumOrderType = Literal[0, 1]
ForumLayoutType = Literal[0, 1, 2]
class ForumChannel(_BaseTextChannel):
    type: Literal[15]
    available_tags: List[ForumTag]
    default_reaction_emoji: Optional[DefaultReaction]
    default_sort_order: Optional[ForumOrderType]
    default_forum_layout: NotRequired[ForumLayoutType]
GuildChannel = Union[
    TextChannel, NewsChannel, VoiceChannel, CategoryChannel, StageChannel, DirectoryChannel, ThreadChannel, ForumChannel
]
class DMChannel(_BaseChannel):
    type: Literal[1]
    last_message_id: Optional[Snowflake]
    recipients: List[PartialUser]
    is_message_request: NotRequired[bool]
    is_message_request_timestamp: NotRequired[str]
    is_spam: NotRequired[bool]
class GroupDMChannel(_BaseChannel):
    type: Literal[3]
    name: Optional[str]
    icon: Optional[str]
    owner_id: Snowflake
    recipients: List[PartialUser]
Channel = Union[GuildChannel, DMChannel, GroupDMChannel]
PrivacyLevel = Literal[1, 2]
class StageInstance(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Snowflake
    topic: str
    privacy_level: PrivacyLevel
    discoverable_disabled: bool
    invite_code: Optional[str]
    guild_scheduled_event_id: Optional[int]
class InviteStageInstance(TypedDict):
    members: List[MemberWithUser]
    participant_count: int
    speaker_count: int
    topic: str
class CallEligibility(TypedDict):
    ringable: bool