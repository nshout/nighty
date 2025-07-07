from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple, Union
from . import utils
from .errors import ClientException
from .utils import cached_slot_property
from .voice_client import VoiceClient
if TYPE_CHECKING:
    from . import abc
    from .abc import T as ConnectReturn
    from .channel import DMChannel, GroupChannel
    from .client import Client
    from .member import VoiceState
    from .message import Message
    from .state import ConnectionState
    from .types.gateway import CallCreateEvent, CallUpdateEvent
    from .user import BaseUser, User
    _PrivateChannel = Union[abc.DMChannel, abc.GroupChannel]
__all__ = (
    'CallMessage',
    'PrivateCall',
    'GroupCall',
)
def _running_only(func: Callable):
    def decorator(self: Call, *args, **kwargs):
        if self._ended:
            raise ClientException('Call is over')
        else:
            return func(self, *args, **kwargs)
    return decorator
class CallMessage:
    __slots__ = ('message', 'ended_timestamp', 'participants')
    def __init__(self, message: Message, *, participants: List[User], ended_timestamp: Optional[str]) -> None:
        self.message = message
        self.ended_timestamp = utils.parse_time(ended_timestamp)
        self.participants = participants
    @property
    def call_ended(self) -> bool:
        return self.ended_timestamp is not None
    @property
    def initiator(self) -> User:
        return self.message.author
    @property
    def channel(self) -> _PrivateChannel:
        return self.message.channel
    @property
    def duration(self) -> datetime.timedelta:
        if self.ended_timestamp is None:
            return utils.utcnow() - self.message.created_at
        else:
            return self.ended_timestamp - self.message.created_at
class PrivateCall:
    __slots__ = ('state', '_ended', 'channel', '_cs_message', '_ringing', '_message_id', 'region', 'unavailable')
    if TYPE_CHECKING:
        channel: DMChannel
    def __init__(
        self,
        *,
        data: Union[CallCreateEvent, CallUpdateEvent],
        state: ConnectionState,
        message: Optional[Message],
        channel: abc.PrivateChannel,
    ) -> None:
        self.state = state
        self._cs_message = message
        self.channel = channel
        self._ended: bool = False
        self._update(data)
    def _delete(self) -> None:
        self._ringing = tuple()
        self._ended = True
    def _get_recipients(self) -> Tuple[BaseUser, ...]:
        channel = self.channel
        return channel.me, channel.recipient
    def _is_participating(self, user: BaseUser) -> bool:
        state = self.voice_state_for(user)
        return bool(state and state.channel and state.channel.id == self.channel.id)
    def _update(self, data: Union[CallCreateEvent, CallUpdateEvent]) -> None:
        self._message_id = int(data['message_id'])
        self.unavailable = data.get('unavailable', False)
        try:
            self.region: str = data['region']
        except KeyError:
            pass
        channel = self.channel
        recipients = self._get_recipients()
        lookup = {u.id: u for u in recipients}
        self._ringing = tuple(filter(None, map(lookup.get, [int(x) for x in data.get('ringing', [])])))
        for vs in data.get('voice_states', []):
            self.state._update_voice_state(vs, channel.id)
    @property
    def ringing(self) -> List[BaseUser]:
        return list(self._ringing)
    @property
    def initiator(self) -> Optional[User]:
        return getattr(self.message, 'author', None)
    @property
    def connected(self) -> bool:
        return self._is_participating(self.channel.me)
    @property
    def members(self) -> List[BaseUser]:
        recipients = self._get_recipients()
        return [u for u in recipients if self._is_participating(u)]
    @property
    def voice_states(self) -> Dict[int, VoiceState]:
        return {
            k: v for k, v in self.state._voice_states.items() if bool(v and v.channel and v.channel.id == self.channel.id)
        }
    @cached_slot_property('_cs_message')
    def message(self) -> Optional[Message]:
        return self.state._get_message(self._message_id)
    async def fetch_message(self) -> Message:
        message = await self.channel.fetch_message(self._message_id)
        state = self.state
        if self.message is None:
            if state._messages is not None:
                state._messages.append(message)
            self._cs_message = message
        return message
    async def change_region(self, region: str) -> None:
        await self.state.http.change_call_voice_region(self.channel.id, region)
    @_running_only
    async def ring(self) -> None:
        channel = self.channel
        await self.state.http.ring(channel.id)
    @_running_only
    async def stop_ringing(self) -> None:
        channel = self.channel
        await self.state.http.stop_ringing(channel.id, channel.recipient.id)
    @_running_only
    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, abc.VocalChannel], ConnectReturn] = VoiceClient,
    ) -> ConnectReturn:
        return await self.channel.connect(timeout=timeout, reconnect=reconnect, cls=cls, ring=False)
    @_running_only
    async def join(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, abc.VocalChannel], ConnectReturn] = VoiceClient,
    ) -> ConnectReturn:
        return await self.connect(timeout=timeout, reconnect=reconnect, cls=cls)
    @_running_only
    async def disconnect(self, force: bool = False) -> None:
        state = self.state
        if not (client := state._get_voice_client(self.channel.me.id)):
            return
        return await client.disconnect(force=force)
    @_running_only
    async def leave(self, force: bool = False) -> None:
        return await self.disconnect(force=force)
    def voice_state_for(self, user: abc.Snowflake) -> Optional[VoiceState]:
        return self.state._voice_state_for(user.id)
class GroupCall(PrivateCall):
    __slots__ = ()
    if TYPE_CHECKING:
        channel: GroupChannel
    def _get_recipients(self) -> Tuple[BaseUser, ...]:
        channel = self.channel
        return *channel.recipients, channel.me
    @_running_only
    async def ring(self, *recipients: abc.Snowflake) -> None:
        r
        await self.state.http.ring(self.channel.id, *{r.id for r in recipients})
    @_running_only
    async def stop_ringing(self, *recipients: abc.Snowflake) -> None:
        r
        channel = self.channel
        await self.state.http.stop_ringing(channel.id, *{r.id for r in recipients or channel.recipients})
Call = Union[PrivateCall, GroupCall]