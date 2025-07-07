from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Optional, Set, List, Tuple, Union
from .enums import ChannelType, ReadStateType, try_enum
from .utils import _get_as_snowflake
if TYPE_CHECKING:
    from .guild import Guild
    from .member import Member
    from .message import Message
    from .partial_emoji import PartialEmoji
    from .state import ConnectionState
    from .threads import Thread
    from .types.gateway import (
        GuildMemberRemoveEvent,
        IntegrationDeleteEvent,
        MessageAckEvent,
        MessageDeleteBulkEvent as BulkMessageDeleteEvent,
        MessageDeleteEvent,
        MessageReactionAddEvent,
        MessageReactionRemoveAllEvent as ReactionClearEvent,
        MessageReactionRemoveEmojiEvent as ReactionClearEmojiEvent,
        MessageReactionRemoveEvent,
        MessageUpdateEvent,
        NonChannelAckEvent,
        ThreadDeleteEvent,
        ThreadMembersUpdate,
    )
    from .user import User
    ReactionActionEvent = Union[MessageReactionAddEvent, MessageReactionRemoveEvent]
    ReactionActionType = Literal['REACTION_ADD', 'REACTION_REMOVE']
__all__ = (
    'RawMessageDeleteEvent',
    'RawBulkMessageDeleteEvent',
    'RawMessageUpdateEvent',
    'RawReactionActionEvent',
    'RawReactionClearEvent',
    'RawReactionClearEmojiEvent',
    'RawIntegrationDeleteEvent',
    'RawThreadDeleteEvent',
    'RawThreadMembersUpdate',
    'RawMemberRemoveEvent',
    'RawMessageAckEvent',
    'RawUserFeatureAckEvent',
    'RawGuildFeatureAckEvent',
)
class _RawReprMixin:
    __slots__: Tuple[str, ...] = ()
    def __repr__(self) -> str:
        value = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'<{self.__class__.__name__} {value}>'
class RawMessageDeleteEvent(_RawReprMixin):
    __slots__ = ('message_id', 'channel_id', 'guild_id', 'cached_message')
    def __init__(self, data: MessageDeleteEvent) -> None:
        self.message_id: int = int(data['id'])
        self.channel_id: int = int(data['channel_id'])
        self.cached_message: Optional[Message] = None
        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None
class RawBulkMessageDeleteEvent(_RawReprMixin):
    __slots__ = ('message_ids', 'channel_id', 'guild_id', 'cached_messages')
    def __init__(self, data: BulkMessageDeleteEvent) -> None:
        self.message_ids: Set[int] = {int(x) for x in data.get('ids', [])}
        self.channel_id: int = int(data['channel_id'])
        self.cached_messages: List[Message] = []
        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None
class RawMessageUpdateEvent(_RawReprMixin):
    __slots__ = ('message_id', 'channel_id', 'guild_id', 'data', 'cached_message')
    def __init__(self, data: MessageUpdateEvent) -> None:
        self.message_id: int = int(data['id'])
        self.channel_id: int = int(data['channel_id'])
        self.data: MessageUpdateEvent = data
        self.cached_message: Optional[Message] = None
        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None
class RawReactionActionEvent(_RawReprMixin):
    __slots__ = ('message_id', 'user_id', 'channel_id', 'guild_id', 'emoji', 'event_type', 'member', 'message_author_id')
    def __init__(self, data: ReactionActionEvent, emoji: PartialEmoji, event_type: ReactionActionType) -> None:
        self.message_id: int = int(data['message_id'])
        self.channel_id: int = int(data['channel_id'])
        self.user_id: int = int(data['user_id'])
        self.emoji: PartialEmoji = emoji
        self.event_type: ReactionActionType = event_type
        self.member: Optional[Member] = None
        self.message_author_id: Optional[int] = _get_as_snowflake(data, 'message_author_id')
        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None
class RawReactionClearEvent(_RawReprMixin):
    __slots__ = ('message_id', 'channel_id', 'guild_id')
    def __init__(self, data: ReactionClearEvent) -> None:
        self.message_id: int = int(data['message_id'])
        self.channel_id: int = int(data['channel_id'])
        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None
class RawReactionClearEmojiEvent(_RawReprMixin):
    __slots__ = ('message_id', 'channel_id', 'guild_id', 'emoji')
    def __init__(self, data: ReactionClearEmojiEvent, emoji: PartialEmoji) -> None:
        self.emoji: PartialEmoji = emoji
        self.message_id: int = int(data['message_id'])
        self.channel_id: int = int(data['channel_id'])
        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None
class RawIntegrationDeleteEvent(_RawReprMixin):
    __slots__ = ('integration_id', 'application_id', 'guild_id')
    def __init__(self, data: IntegrationDeleteEvent) -> None:
        self.integration_id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        try:
            self.application_id: Optional[int] = int(data['application_id'])
        except KeyError:
            self.application_id: Optional[int] = None
class RawThreadDeleteEvent(_RawReprMixin):
    __slots__ = ('thread_id', 'thread_type', 'parent_id', 'guild_id', 'thread')
    def __init__(self, data: ThreadDeleteEvent) -> None:
        self.thread_id: int = int(data['id'])
        self.thread_type: ChannelType = try_enum(ChannelType, data['type'])
        self.guild_id: int = int(data['guild_id'])
        self.parent_id: int = int(data['parent_id'])
        self.thread: Optional[Thread] = None
class RawThreadMembersUpdate(_RawReprMixin):
    __slots__ = ('thread_id', 'guild_id', 'member_count', 'data')
    def __init__(self, data: ThreadMembersUpdate) -> None:
        self.thread_id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        self.member_count: int = int(data['member_count'])
        self.data: ThreadMembersUpdate = data
class RawMemberRemoveEvent(_RawReprMixin):
    __slots__ = ('user', 'guild_id')
    def __init__(self, data: GuildMemberRemoveEvent, user: User, /) -> None:
        self.user: Union[User, Member] = user
        self.guild_id: int = int(data['guild_id'])
class RawMessageAckEvent(_RawReprMixin):
    __slots__ = ('message_id', 'channel_id', 'cached_message', 'manual', 'mention_count')
    def __init__(self, data: MessageAckEvent) -> None:
        self.message_id: int = int(data['message_id'])
        self.channel_id: int = int(data['channel_id'])
        self.cached_message: Optional[Message] = None
        self.manual: bool = data.get('manual', False)
        self.mention_count: int = data.get('mention_count', 0)
class RawUserFeatureAckEvent(_RawReprMixin):
    __slots__ = ('type', 'entity_id')
    def __init__(self, data: NonChannelAckEvent) -> None:
        self.type: ReadStateType = try_enum(ReadStateType, data['ack_type'])
        self.entity_id: int = int(data['entity_id'])
class RawGuildFeatureAckEvent(RawUserFeatureAckEvent):
    __slots__ = ('guild_id', 'state')
    def __init__(self, data: NonChannelAckEvent, state: ConnectionState) -> None:
        self.state: ConnectionState = state
        self.guild_id: int = int(data['resource_id'])
        super().__init__(data)
    @property
    def guild(self) -> Guild:
        return self.state._get_or_create_unavailable_guild(self.guild_id)