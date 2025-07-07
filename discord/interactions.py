from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Optional, Union
from .enums import InteractionType, try_enum
from .errors import InvalidData
from .mixins import Hashable
from .utils import MISSING, cached_slot_property, find
if TYPE_CHECKING:
    from .channel import DMChannel, TextChannel, VoiceChannel
    from .guild import Guild
    from .message import Message
    from .modal import Modal
    from .state import ConnectionState
    from .threads import Thread
    from .types.interactions import InteractionData
    from .types.snowflake import Snowflake
    from .types.user import User as UserPayload
    from .user import BaseUser, ClientUser
    MessageableChannel = Union[TextChannel, Thread, DMChannel, VoiceChannel]
__all__ = (
    'Interaction',
)
class Interaction(Hashable):
    __slots__ = ('id', 'type', 'nonce', 'channel', 'user', 'name', 'successful', 'modal', '_cs_message', 'state')
    def __init__(
        self,
        id: int,
        type: int,
        nonce: Optional[Snowflake] = None,
        *,
        channel: MessageableChannel,
        user: BaseUser,
        state: ConnectionState,
        name: Optional[str] = None,
        message: Optional[Message] = None,
    ) -> None:
        self.id = id
        self.type = try_enum(InteractionType, type)
        self.nonce = nonce
        self.channel = channel
        self.user = user
        self.name = name
        self.successful: bool = MISSING
        self.modal: Optional[Modal] = None
        self.state = state
        if message is not None:
            self._cs_message = message
    @classmethod
    def _from_self(
        cls,
        channel: MessageableChannel,
        *,
        id: Snowflake,
        type: int,
        nonce: Optional[Snowflake] = None,
        user: ClientUser,
        name: Optional[str],
    ) -> Interaction:
        return cls(int(id), type, nonce, user=user, name=name, state=user.state, channel=channel)
    @classmethod
    def _from_message(cls, message: Message, *, id: Snowflake, type: int, user: UserPayload, **data) -> Interaction:
        state = message.state
        name = data.get('name')
        user_cls = state.store_user(user)
        self = cls(
            int(id),
            type,
            channel=message.channel,
            user=user_cls,
            name=name,
            message=message,
            state=state,
        )
        self.successful = True
        return self
    def __repr__(self) -> str:
        s = self.successful
        return f'<Interaction id={self.id} type={self.type!r}{f" successful={s}" if s is not MISSING else ""} user={self.user!r}>'
    def __str__(self) -> str:
        if self.name:
            return f'{self.user.name} used **{"/" if self.type == InteractionType.application_command else ""}{self.name}**'
        return ''
    def __bool__(self) -> bool:
        if self.successful is not MISSING:
            return self.successful
        raise TypeError('Interaction has not been resolved yet')
    @cached_slot_property('_cs_message')
    def message(self) -> Optional[Message]:
        def predicate(message: Message) -> bool:
            return message.interaction is not None and message.interaction.id == self.id
        return find(predicate, self.state.client.cached_messages)
    @property
    def guild(self) -> Optional[Guild]:
        return getattr(self.channel, 'guild', None)
async def _wrapped_interaction(
    state: ConnectionState,
    nonce: str,
    type: InteractionType,
    name: Optional[str],
    channel: MessageableChannel,
    data: InteractionData,
    **kwargs,
) -> Interaction:
    state._interaction_cache[nonce] = (type.value, name, channel)
    try:
        await state.http.interact(type, data, channel, nonce=nonce, **kwargs)
        i = await state.client.wait_for(
            'interaction_finish',
            check=lambda d: d.nonce == nonce,
            timeout=12,
        )
    except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
        raise InvalidData('Did not receive a response from Discord') from exc
    finally:
        state._interaction_cache.pop(nonce, None)
    return i