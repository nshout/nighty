from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
from .enums import DirectoryCategory, DirectoryEntryType, try_enum
from .scheduled_event import ScheduledEvent
from .utils import MISSING, parse_time
if TYPE_CHECKING:
    from datetime import datetime
    from .channel import DirectoryChannel
    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .types.directory import (
        DirectoryEntry as DirectoryEntryPayload,
        PartialDirectoryEntry as PartialDirectoryEntryPayload,
    )
__all__ = ('DirectoryEntry',)
class DirectoryEntry:
    def __init__(
        self,
        *,
        data: Union[DirectoryEntryPayload, PartialDirectoryEntryPayload],
        state: ConnectionState,
        channel: DirectoryChannel,
    ):
        self.channel = channel
        self.state = state
        self._update(data)
    def __repr__(self) -> str:
        return f'<DirectoryEntry channel={self.channel!r} type={self.type!r} category={self.category!r} author_id={self.author_id!r} guild={self.guild!r}>'
    def __hash__(self) -> int:
        return hash((self.channel.id, self.entity_id))
    def __eq__(self, other: object) -> bool:
        if isinstance(other, DirectoryEntry):
            return self.channel == other.channel and self.entity_id == other.entity_id
        return NotImplemented
    def _update(self, data: Union[DirectoryEntryPayload, PartialDirectoryEntryPayload]):
        state = self.state
        self.type: DirectoryEntryType = try_enum(DirectoryEntryType, data['type'])
        self.category: DirectoryCategory = try_enum(DirectoryCategory, data.get('primary_category_id', 0))
        self.author_id: int = int(data['author_id'])
        self.created_at: datetime = parse_time(data['created_at'])
        self.description: Optional[str] = data.get('description') or None
        self.entity_id: int = int(data['entity_id'])
        guild_data = data.get('guild', data.get('guild_scheduled_event', {}).get('guild'))
        self.guild: Optional[Guild] = state.create_guild(guild_data) if guild_data is not None else None
        self.featurable: bool = guild_data.get('featurable_in_directory', False) if guild_data is not None else False
        event_data = data.get('guild_scheduled_event')
        self.scheduled_event: Optional[ScheduledEvent] = (
            ScheduledEvent(data=event_data, state=state) if event_data is not None else None
        )
        self.rsvp: bool = event_data.get('user_rsvp', False) if event_data is not None else False
    @property
    def author(self) -> Optional[Member]:
        return self.channel.guild.get_member(self.author_id)
    async def edit(self, *, description: Optional[str] = MISSING, category: DirectoryCategory = MISSING) -> None:
        data = await self.state.http.edit_directory_entry(
            self.channel.id,
            self.entity_id,
            description=description,
            primary_category_id=category.value if category is not MISSING else MISSING,
        )
        self._update(data)
    async def delete(self) -> None:
        await self.state.http.delete_directory_entry(self.channel.id, self.entity_id)