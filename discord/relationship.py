from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple, Union
from .enums import ConnectionType, FriendSuggestionReasonType, RelationshipAction, RelationshipType, Status, try_enum
from .mixins import Hashable
from .object import Object
from .utils import MISSING, parse_time
if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self
    from .activity import ActivityTypes
    from .state import ConnectionState, Presence
    from .types.gateway import RelationshipEvent
    from .types.user import (
        FriendSuggestion as FriendSuggestionPayload,
        FriendSuggestionReason as FriendSuggestionReasonPayload,
        Relationship as RelationshipPayload,
    )
    from .user import User
__all__ = (
    'Relationship',
    'FriendSuggestionReason',
    'FriendSuggestion',
)
class Relationship(Hashable):
    __slots__ = ('_presence', 'since', 'nick', 'type', 'user', 'state')
    if TYPE_CHECKING:
        user: User
    def __init__(self, *, state: ConnectionState, data: RelationshipPayload) -> None:
        self.state = state
        self._presence: Optional[Presence] = None
        self._update(data)
    def _update(self, data: Union[RelationshipPayload, RelationshipEvent]) -> None:
        self.type: RelationshipType = try_enum(RelationshipType, data['type'])
        self.nick: Optional[str] = data.get('nickname')
        self.since: Optional[datetime] = parse_time(data.get('since'))
        if not getattr(self, 'user', None):
            if 'user' in data:
                self.user = self.state.store_user(data['user'])
            else:
                user_id = int(data['id'])
                self.user = self.state.get_user(user_id) or Object(id=user_id)
    @classmethod
    def _from_implicit(cls, *, state: ConnectionState, user: User) -> Relationship:
        self = cls.__new__(cls)
        self.state = state
        self._presence = None
        self.type = RelationshipType.implicit
        self.nick = None
        self.since = None
        self.user = user
        return self
    @classmethod
    def _copy(cls, relationship: Self, presence: Presence) -> Self:
        self = cls.__new__(cls)
        self.state = relationship.state
        self._presence = presence
        self.type = relationship.type
        self.nick = relationship.nick
        self.since = relationship.since
        self.user = relationship.user
        return self
    def __repr__(self) -> str:
        return f'<Relationship user={self.user!r} type={self.type!r} nick={self.nick!r}>'
    @property
    def id(self) -> int:
        return self.user.id
    @property
    def presence(self) -> Presence:
        state = self.state
        return self._presence or state._presences.get(self.user.id) or state.create_offline_presence()
    @property
    def status(self) -> Status:
        return try_enum(Status, self.presence.client_status.status)
    @property
    def raw_status(self) -> str:
        return self.presence.client_status.status
    @property
    def mobile_status(self) -> Status:
        return try_enum(Status, self.presence.client_status.mobile or 'offline')
    @property
    def desktop_status(self) -> Status:
        return try_enum(Status, self.presence.client_status.desktop or 'offline')
    @property
    def web_status(self) -> Status:
        return try_enum(Status, self.presence.client_status.web or 'offline')
    def is_on_mobile(self) -> bool:
        return self.presence.client_status.mobile is not None
    @property
    def activities(self) -> Tuple[ActivityTypes, ...]:
        return self.presence.activities
    @property
    def activity(self) -> Optional[ActivityTypes]:
        if self.activities:
            return self.activities[0]
    async def delete(self) -> None:
        action = RelationshipAction.deny_request
        if self.type is RelationshipType.friend:
            action = RelationshipAction.unfriend
        elif self.type is RelationshipType.blocked:
            action = RelationshipAction.unblock
        elif self.type is RelationshipType.incoming_request:
            action = RelationshipAction.deny_request
        elif self.type is RelationshipType.outgoing_request:
            action = RelationshipAction.remove_pending_request
        await self.state.http.remove_relationship(self.user.id, action=action)
    async def accept(self) -> None:
        await self.state.http.add_relationship(self.user.id, action=RelationshipAction.accept_request)
    async def edit(self, nick: Optional[str] = MISSING) -> None:
        payload = {}
        if nick is not MISSING:
            payload['nickname'] = nick
        await self.state.http.edit_relationship(self.user.id, **payload)
class FriendSuggestionReason:
    __slots__ = ('type', 'platform', 'name')
    def __init__(self, data: FriendSuggestionReasonPayload):
        self.type: FriendSuggestionReasonType = try_enum(FriendSuggestionReasonType, data.get('type', 0))
        self.platform: ConnectionType = try_enum(ConnectionType, data.get('platform'))
        self.name: str = data.get('name') or ''
    def __repr__(self) -> str:
        return f'<FriendSuggestionReason platform={self.platform!r} name={self.name!r}>'
class FriendSuggestion(Hashable):
    __slots__ = ('user', 'reasons', 'from_user_contacts', 'state')
    def __init__(self, *, state: ConnectionState, data: FriendSuggestionPayload):
        self.state = state
        self.user = state.store_user(data['suggested_user'])
        self.reasons = [FriendSuggestionReason(r) for r in data.get('reasons', [])]
        self.from_user_contacts: bool = data.get('from_suggested_user_contacts', False)
    def __repr__(self) -> str:
        return (
            f'<FriendSuggestion user={self.user!r} reasons={self.reasons!r} from_user_contacts={self.from_user_contacts!r}>'
        )
    async def accept(self) -> None:
        await self.state.http.add_relationship(self.user.id, action=RelationshipAction.friend_suggestion)
    async def delete(self) -> None:
        await self.state.http.delete_friend_suggestion(self.user.id)