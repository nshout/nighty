from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterator, Dict, List, Optional, Union, overload, Literal
from .asset import Asset
from .enums import EventStatus, EntityType, PrivacyLevel, ReadStateType, try_enum
from .mixins import Hashable
from .object import Object, OLDEST_OBJECT
from .utils import parse_time, _get_as_snowflake, _bytes_to_base64_data, MISSING
if TYPE_CHECKING:
    from .types.scheduled_event import (
        GuildScheduledEvent as BaseGuildScheduledEventPayload,
        GuildScheduledEventWithUserCount as GuildScheduledEventWithUserCountPayload,
        EntityMetadata,
    )
    from .abc import Snowflake
    from .guild import Guild
    from .channel import VoiceChannel, StageChannel
    from .state import ConnectionState
    from .user import User
    GuildScheduledEventPayload = Union[BaseGuildScheduledEventPayload, GuildScheduledEventWithUserCountPayload]
__all__ = (
    "ScheduledEvent",
)
class ScheduledEvent(Hashable):
    __slots__ = (
        'state',
        '_users',
        'id',
        'guild_id',
        'name',
        'description',
        'entity_type',
        'entity_id',
        'start_time',
        'end_time',
        'privacy_level',
        'status',
        '_cover_image',
        'user_count',
        'creator',
        'channel_id',
        'creator_id',
        'location',
        'sku_ids',
    )
    def __init__(self, *, state: ConnectionState, data: GuildScheduledEventPayload) -> None:
        self.state = state
        self._users: Dict[int, User] = {}
        self._update(data)
    def _update(self, data: GuildScheduledEventPayload) -> None:
        self.id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        self.name: str = data['name']
        self.description: Optional[str] = data.get('description')
        self.entity_type: EntityType = try_enum(EntityType, data['entity_type'])
        self.entity_id: Optional[int] = _get_as_snowflake(data, 'entity_id')
        self.start_time: datetime = parse_time(data['scheduled_start_time'])
        self.privacy_level: PrivacyLevel = try_enum(PrivacyLevel, data['status'])
        self.status: EventStatus = try_enum(EventStatus, data['status'])
        self._cover_image: Optional[str] = data.get('image', None)
        self.user_count: int = data.get('user_count', 0)
        self.creator_id: Optional[int] = _get_as_snowflake(data, 'creator_id')
        creator = data.get('creator')
        self.creator: Optional[User] = self.state.store_user(creator) if creator else None
        if self.creator_id is not None and self.creator is None:
            self.creator = self.state.get_user(self.creator_id)
        self.end_time: Optional[datetime] = parse_time(data.get('scheduled_end_time'))
        self.channel_id: Optional[int] = _get_as_snowflake(data, 'channel_id')
        self.sku_ids: List[int] = [int(sku_id) for sku_id in data.get('sku_ids', [])]
        metadata = data.get('entity_metadata')
        self._unroll_metadata(metadata)
    def _unroll_metadata(self, data: Optional[EntityMetadata]):
        self.location: Optional[str] = data.get('location') if data else None
    def __repr__(self) -> str:
        return f'<GuildScheduledEvent id={self.id} name={self.name!r} guild_id={self.guild_id!r} creator={self.creator!r}>'
    @property
    def cover_image(self) -> Optional[Asset]:
        if self._cover_image is None:
            return None
        return Asset._from_scheduled_event_cover_image(self.state, self.id, self._cover_image)
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    @property
    def channel(self) -> Optional[Union[VoiceChannel, StageChannel]]:
        return self.guild.get_channel(self.channel_id)
    @property
    def url(self) -> str:
        return f'https://discord.com/events/{self.guild_id}/{self.id}'
    def is_acked(self) -> bool:
        read_state = self.state.get_read_state(self.guild_id, ReadStateType.scheduled_events)
        return read_state.last_acked_id >= self.id if read_state.last_acked_id else False
    async def __modify_status(self, status: EventStatus, reason: Optional[str], /) -> ScheduledEvent:
        payload = {'status': status.value}
        data = await self.state.http.edit_scheduled_event(self.guild_id, self.id, **payload, reason=reason)
        s = ScheduledEvent(state=self.state, data=data)
        s._users = self._users
        return s
    async def start(self, *, reason: Optional[str] = None) -> ScheduledEvent:
        if self.status is not EventStatus.scheduled:
            raise ValueError('This scheduled event is already running')
        return await self.__modify_status(EventStatus.active, reason)
    async def end(self, *, reason: Optional[str] = None) -> ScheduledEvent:
        if self.status is not EventStatus.active:
            raise ValueError('This scheduled event is not active')
        return await self.__modify_status(EventStatus.ended, reason)
    async def cancel(self, *, reason: Optional[str] = None) -> ScheduledEvent:
        if self.status is not EventStatus.scheduled:
            raise ValueError('This scheduled event is already running')
        return await self.__modify_status(EventStatus.cancelled, reason)
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        start_time: datetime = ...,
        end_time: Optional[datetime] = ...,
        privacy_level: PrivacyLevel = ...,
        status: EventStatus = ...,
        image: bytes = ...,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        channel: Snowflake,
        start_time: datetime = ...,
        end_time: Optional[datetime] = ...,
        privacy_level: PrivacyLevel = ...,
        entity_type: Literal[EntityType.voice, EntityType.stage_instance],
        status: EventStatus = ...,
        image: bytes = ...,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        start_time: datetime = ...,
        end_time: datetime = ...,
        privacy_level: PrivacyLevel = ...,
        entity_type: Literal[EntityType.external],
        status: EventStatus = ...,
        image: bytes = ...,
        location: str,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        channel: Union[VoiceChannel, StageChannel],
        start_time: datetime = ...,
        end_time: Optional[datetime] = ...,
        privacy_level: PrivacyLevel = ...,
        status: EventStatus = ...,
        image: bytes = ...,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        start_time: datetime = ...,
        end_time: datetime = ...,
        privacy_level: PrivacyLevel = ...,
        status: EventStatus = ...,
        image: bytes = ...,
        location: str,
        directory_broadcast: bool = ...,
        reason: Optional[str] = ...,
    ) -> ScheduledEvent:
        ...
    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        channel: Optional[Snowflake] = MISSING,
        start_time: datetime = MISSING,
        end_time: Optional[datetime] = MISSING,
        privacy_level: PrivacyLevel = MISSING,
        entity_type: EntityType = MISSING,
        status: EventStatus = MISSING,
        image: bytes = MISSING,
        location: str = MISSING,
        directory_broadcast: bool = MISSING,
        reason: Optional[str] = None,
    ) -> ScheduledEvent:
        r
        payload = {}
        metadata = {}
        if name is not MISSING:
            payload['name'] = name
        if start_time is not MISSING:
            if start_time.tzinfo is None:
                raise ValueError(
                    'start_time must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                )
            payload['scheduled_start_time'] = start_time.isoformat()
        if description is not MISSING:
            payload['description'] = description
        if privacy_level is not MISSING:
            if not isinstance(privacy_level, PrivacyLevel):
                raise TypeError('privacy_level must be of type PrivacyLevel')
            payload['privacy_level'] = privacy_level.value
        if status is not MISSING:
            if not isinstance(status, EventStatus):
                raise TypeError('status must be of type EventStatus')
            payload['status'] = status.value
        if image is not MISSING:
            image_as_str: Optional[str] = _bytes_to_base64_data(image) if image is not None else image
            payload['image'] = image_as_str
        entity_type = entity_type or getattr(channel, '_scheduled_event_entity_type', MISSING)
        if entity_type is MISSING:
            if channel and isinstance(channel, Object):
                if channel.type is VoiceChannel:
                    entity_type = EntityType.voice
                elif channel.type is StageChannel:
                    entity_type = EntityType.stage_instance
            elif location not in (MISSING, None):
                entity_type = EntityType.external
        else:
            if not isinstance(entity_type, EntityType):
                raise TypeError('entity_type must be of type EntityType')
            payload['entity_type'] = entity_type.value
        if entity_type is None:
            raise TypeError(
                f'invalid GuildChannel type passed; must be VoiceChannel or StageChannel not {channel.__class__.__name__}'
            )
        _entity_type = entity_type or self.entity_type
        _entity_type_changed = _entity_type is not self.entity_type
        if _entity_type in (EntityType.stage_instance, EntityType.voice):
            if channel is MISSING or channel is None:
                if _entity_type_changed:
                    raise TypeError('channel must be set when entity_type is voice or stage_instance')
            else:
                payload['channel_id'] = channel.id
            if location not in (MISSING, None):
                raise TypeError('location cannot be set when entity_type is voice or stage_instance')
            payload['entity_metadata'] = None
        else:
            if channel not in (MISSING, None):
                raise TypeError('channel cannot be set when entity_type is external')
            payload['channel_id'] = None
            if location is MISSING or location is None:
                if _entity_type_changed:
                    raise TypeError('location must be set when entity_type is external')
            else:
                metadata['location'] = location
            if not self.end_time and (end_time is MISSING or end_time is None):
                raise TypeError('end_time must be set when entity_type is external')
        if end_time is not MISSING:
            if end_time is not None:
                if end_time.tzinfo is None:
                    raise ValueError(
                        'end_time must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                    )
                payload['scheduled_end_time'] = end_time.isoformat()
            else:
                payload['scheduled_end_time'] = end_time
        if directory_broadcast is not MISSING:
            payload['broadcast_to_directory_channels'] = directory_broadcast
        if metadata:
            payload['entity_metadata'] = metadata
        data = await self.state.http.edit_scheduled_event(self.guild_id, self.id, **payload, reason=reason)
        s = ScheduledEvent(state=self.state, data=data)
        s._users = self._users
        return s
    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_scheduled_event(self.guild_id, self.id, reason=reason)
    async def users(
        self,
        *,
        limit: Optional[int] = None,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        oldest_first: bool = MISSING,
    ) -> AsyncIterator[User]:
        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            users = await self.state.http.get_scheduled_event_users(
                self.guild_id, self.id, limit=retrieve, with_member=False, before=before_id
            )
            users = users['users']
            if users:
                if limit is not None:
                    limit -= len(users)
                before = Object(id=users[-1]['id'])
            return users, before, limit
        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            users = await self.state.http.get_scheduled_event_users(
                self.guild_id, self.id, limit=retrieve, with_member=False, after=after_id
            )
            users = users['users']
            if users:
                if limit is not None:
                    limit -= len(users)
                after = Object(id=users[0]['id'])
            return users, after, limit
        if limit is None:
            limit = self.user_count or None
        if oldest_first is MISSING:
            reverse = after is not None
        else:
            reverse = oldest_first
        predicate = None
        if reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda u: u['user']['id'] < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda u: u['user']['id'] > after.id
        while True:
            retrieve = 100 if limit is None else min(limit, 100)
            if retrieve < 1:
                return
            data, state, limit = await strategy(retrieve, state, limit)
            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)
            users = (self.state.store_user(raw_user) for raw_user in data)
            count = 0
            for count, user in enumerate(users, 1):
                if user.id not in self._users:
                    self._add_user(user)
                yield user
            if count < 100:
                break
    async def rsvp(self) -> None:
        await self.state.http.create_scheduled_event_user(self.guild_id, self.id)
    async def unrsvp(self) -> None:
        await self.state.http.delete_scheduled_event_user(self.guild_id, self.id)
    async def ack(self) -> None:
        await self.state.http.ack_guild_feature(self.guild_id, ReadStateType.scheduled_events.value, self.id)
    def _add_user(self, user: User) -> None:
        self._users[user.id] = user
    def _pop_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)