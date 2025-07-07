from __future__ import annotations
from datetime import date
from operator import attrgetter
from typing import TYPE_CHECKING, Optional, Union
from .channel import PartialMessageable
from .enums import ReadStateType, try_enum
from .flags import ReadStateFlags
from .threads import Thread
from .utils import DISCORD_EPOCH, MISSING, parse_time
if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self
    from .abc import MessageableChannel
    from .guild import Guild
    from .state import ConnectionState
    from .types.read_state import ReadState as ReadStatePayload
    from .user import ClientUser
__all__ = (
    'ReadState',
)
class ReadState:
    __slots__ = (
        'id',
        'type',
        'last_acked_id',
        'acked_pin_timestamp',
        'badge_count',
        'last_viewed',
        '_flags',
        '_last_entity_id',
        'state',
    )
    def __init__(self, *, state: ConnectionState, data: ReadStatePayload):
        self.state = state
        self.id: int = int(data['id'])
        self.type: ReadStateType = try_enum(ReadStateType, data.get('read_state_type', 0))
        self._last_entity_id: Optional[int] = None
        self._flags: int = 0
        self.last_viewed: Optional[date] = self.unpack_last_viewed(0) if self.type == ReadStateType.channel else None
        self._update(data)
    def _update(self, data: ReadStatePayload):
        self.last_acked_id: int = int(data.get('last_acked_id', data.get('last_message_id', 0)))
        self.acked_pin_timestamp: Optional[datetime] = parse_time(data.get('last_pin_timestamp'))
        self.badge_count: int = int(data.get('badge_count', data.get('mention_count', 0)))
        if 'flags' in data and data['flags'] is not None:
            self._flags = data['flags']
        if 'last_viewed' in data and data['last_viewed']:
            self.last_viewed = self.unpack_last_viewed(data['last_viewed'])
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ReadState):
            return other.id == self.id and other.type == self.type
        return False
    def __ne__(self, other: object) -> bool:
        if isinstance(other, ReadState):
            return other.id != self.id or other.type != self.type
        return True
    def __hash__(self) -> int:
        return (self.id * self.type.value) >> 22
    @classmethod
    def default(cls, id: int, type: ReadStateType, *, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self.id = id
        self.type = type
        self._last_entity_id = None
        self._flags = 0
        self.last_viewed = cls.unpack_last_viewed(0) if type == ReadStateType.channel else None
        self.last_acked_id = 0
        self.acked_pin_timestamp = None
        self.badge_count = 0
        return self
    @staticmethod
    def unpack_last_viewed(last_viewed: int) -> date:
        return date.fromtimestamp(DISCORD_EPOCH / 1000 + last_viewed * 86400)
    @staticmethod
    def pack_last_viewed(last_viewed: date) -> int:
        return int((last_viewed - date.fromtimestamp(DISCORD_EPOCH / 1000)).total_seconds() / 86400 + 0.5)
    @property
    def flags(self) -> ReadStateFlags:
        return ReadStateFlags._from_value(self._flags)
    @property
    def resource(self) -> Union[ClientUser, Guild, MessageableChannel]:
        state = self.state
        if self.type == ReadStateType.channel:
            return state._get_or_create_partial_messageable(self.id)
        elif self.type in (ReadStateType.scheduled_events, ReadStateType.guild_home, ReadStateType.onboarding):
            return state._get_or_create_unavailable_guild(self.id)
        elif self.type == ReadStateType.notification_center and self.id == state.self_id:
            return state.user
        else:
            raise NotImplementedError(f'Unknown read state type {self.type!r}')
    @property
    def last_entity_id(self) -> int:
        if self._last_entity_id is not None:
            return self._last_entity_id
        resource = self.resource
        if not resource:
            return 0
        if self.type == ReadStateType.channel:
            return resource.last_message_id or 0
        elif self.type == ReadStateType.scheduled_events:
            return max(resource.scheduled_events, key=attrgetter('id')).id
        return 0
    @property
    def last_pin_timestamp(self) -> Optional[datetime]:
        if self.resource and hasattr(self.resource, 'last_pin_timestamp'):
            return self.resource.last_pin_timestamp
    async def ack(
        self,
        entity_id: int,
        *,
        manual: bool = False,
        mention_count: Optional[int] = None,
        last_viewed: Optional[date] = MISSING,
    ) -> None:
        state = self.state
        if self.type == ReadStateType.channel:
            flags = None
            channel: MessageableChannel = self.resource
            if not isinstance(channel, PartialMessageable):
                flags = ReadStateFlags()
                if isinstance(channel, Thread):
                    flags.thread = True
                elif channel.guild:
                    flags.guild_channel = True
                if flags == self.flags:
                    flags = None
            if not manual and last_viewed is MISSING:
                last_viewed = date.today()
            await state.http.ack_message(
                self.id,
                entity_id,
                manual=manual,
                mention_count=mention_count,
                flags=flags.value if flags else None,
                last_viewed=self.pack_last_viewed(last_viewed) if last_viewed else None,
            )
            return
        if manual or mention_count is not None or last_viewed:
            raise ValueError('Extended read state parameters are only valid for channel read states')
        if self.type in (ReadStateType.scheduled_events, ReadStateType.guild_home, ReadStateType.onboarding):
            await state.http.ack_guild_feature(self.id, self.type.value, entity_id)
        elif self.type == ReadStateType.notification_center:
            await state.http.ack_user_feature(self.type.value, entity_id)
    async def delete(self):
        state = self.state
        await state.http.delete_read_state(self.id, self.type.value)
        state.remove_read_state(self)