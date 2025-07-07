from typing import Dict, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired
from .guild import PartialGuild, _GuildCounts
from .scheduled_event import ExternalScheduledEvent, StageInstanceScheduledEvent, VoiceScheduledEvent
from .snowflake import Snowflake
class _DirectoryScheduledEvent(TypedDict):
    guild: PartialGuild
    user_rsvp: bool
    user_count: int
class _DirectoryStageInstanceScheduledEvent(_DirectoryScheduledEvent, StageInstanceScheduledEvent):
    ...
class _DirectoryVoiceScheduledEvent(_DirectoryScheduledEvent, VoiceScheduledEvent):
    ...
class _DirectoryExternalScheduledEvent(_DirectoryScheduledEvent, ExternalScheduledEvent):
    ...
DirectoryScheduledEvent = Union[
    _DirectoryStageInstanceScheduledEvent, _DirectoryVoiceScheduledEvent, _DirectoryExternalScheduledEvent
]
class DirectoryGuild(PartialGuild, _GuildCounts):
    featurable_in_directory: bool
DirectoryEntryType = Literal[0, 1]
DirectoryCategory = Literal[0, 1, 2, 3, 5]
DirectoryCounts = Dict[DirectoryCategory, int]
class PartialDirectoryEntry(TypedDict):
    type: DirectoryEntryType
    primary_category_id: NotRequired[DirectoryCategory]
    directory_channel_id: Snowflake
    author_id: Snowflake
    entity_id: Snowflake
    created_at: str
    description: Optional[str]
class DirectoryEntry(PartialDirectoryEntry):
    guild: NotRequired[DirectoryGuild]
    guild_scheduled_event: NotRequired[DirectoryScheduledEvent]
class DirectoryBroadcast(TypedDict):
    can_broadcast: bool