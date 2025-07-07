from __future__ import annotations
from typing import TYPE_CHECKING
from .mixins import Hashable
if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.user import UserAffinity as UserAffinityPayload, GuildAffinity as GuildAffinityPayload
__all__ = (
    'UserAffinity',
    'GuildAffinity',
)
class UserAffinity(Hashable):
    __slots__ = ('state', 'user_id', 'affinity')
    def __init__(self, *, state: ConnectionState, data: UserAffinityPayload):
        self.state = state
        self.user_id = int(data['user_id'])
        self.affinity = data['affinity']
    def __repr__(self) -> str:
        return f'<UserAffinity user_id={self.user_id} affinity={self.affinity}>'
    @property
    def id(self) -> int:
        return self.user_id
    @property
    def user(self):
        return self.state.get_user(self.user_id)
class GuildAffinity(Hashable):
    __slots__ = ('state', 'guild_id', 'affinity')
    def __init__(self, *, state: ConnectionState, data: GuildAffinityPayload):
        self.state = state
        self.guild_id = int(data['guild_id'])
        self.affinity = data['affinity']
    def __repr__(self) -> str:
        return f'<GuildAffinity guild_id={self.guild_id} affinity={self.affinity}>'
    @property
    def id(self) -> int:
        return self.guild_id
    @property
    def guild(self):
        return self.state._get_guild(self.guild_id)