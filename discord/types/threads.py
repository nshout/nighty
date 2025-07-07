from __future__ import annotations
from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired
from .activity import BasePresenceUpdate
from .member import MemberWithUser
from .message import Message
from .snowflake import Snowflake
ThreadType = Literal[10, 11, 12]
ThreadArchiveDuration = Literal[60, 1440, 4320, 10080]
class BaseThreadMember(TypedDict):
    user_id: Snowflake
    member: MemberWithUser
    presence: BasePresenceUpdate
class ThreadMember(TypedDict):
    id: Snowflake
    user_id: Snowflake
    join_timestamp: str
    flags: int
    member: NotRequired[MemberWithUser]
    presence: NotRequired[BasePresenceUpdate]
class ThreadMetadata(TypedDict):
    archived: bool
    auto_archive_duration: ThreadArchiveDuration
    archive_timestamp: str
    archiver_id: NotRequired[Snowflake]
    locked: NotRequired[bool]
    invitable: NotRequired[bool]
    create_timestamp: NotRequired[str]
class Thread(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    parent_id: Snowflake
    owner_id: Snowflake
    name: str
    type: ThreadType
    member_count: int
    message_count: int
    rate_limit_per_user: int
    thread_metadata: ThreadMetadata
    member_ids_preview: List[Snowflake]
    member: NotRequired[ThreadMember]
    last_message_id: NotRequired[Optional[Snowflake]]
    last_pin_timestamp: NotRequired[Optional[str]]
    newly_created: NotRequired[bool]
    flags: NotRequired[int]
    applied_tags: NotRequired[List[Snowflake]]
class ThreadPaginationPayload(TypedDict):
    threads: List[Thread]
    members: List[ThreadMember]
    has_more: bool
class ForumThread(Thread):
    message: Message