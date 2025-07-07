from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from .enums import ConnectionType, try_enum
from .integrations import Integration
from .metadata import Metadata
from .utils import MISSING
if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.integration import ConnectionIntegration as IntegrationPayload
    from .types.user import Connection as ConnectionPayload, PartialConnection as PartialConnectionPayload
__all__ = (
    'PartialConnection',
    'Connection',
)
class PartialConnection:
    __slots__ = ('id', 'name', 'type', 'verified', 'visible', 'metadata')
    def __init__(self, data: PartialConnectionPayload):
        self._update(data)
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} type={self.type!r} visible={self.visible}>'
    def __hash__(self) -> int:
        return hash((self.type.value, self.id))
    def __eq__(self, other: object) -> bool:
        if isinstance(other, PartialConnection):
            return self.id == other.id and self.name == other.name
        return False
    def __ne__(self, other: object) -> bool:
        if isinstance(other, PartialConnection):
            return self.id != other.id or self.name != other.name
        return True
    def _update(self, data: PartialConnectionPayload):
        self.id: str = data['id']
        self.name: str = data['name']
        self.type: ConnectionType = try_enum(ConnectionType, data['type'])
        self.verified: bool = data['verified']
        self.visible: bool = True
        self.metadata: Optional[Metadata] = Metadata(data['metadata']) if 'metadata' in data else None
    @property
    def url(self) -> Optional[str]:
        if self.type == ConnectionType.twitch:
            return f'https://www.twitch.tv/{self.name}'
        elif self.type == ConnectionType.youtube:
            return f'https://www.youtube.com/channel/{self.id}'
        elif self.type == ConnectionType.skype:
            return f'skype:{self.id}?userinfo'
        elif self.type == ConnectionType.steam:
            return f'https://steamcommunity.com/profiles/{self.id}'
        elif self.type == ConnectionType.reddit:
            return f'https://www.reddit.com/u/{self.name}'
        elif self.type == ConnectionType.twitter:
            return f'https://twitter.com/{self.name}'
        elif self.type == ConnectionType.spotify:
            return f'https://open.spotify.com/user/{self.id}'
        elif self.type == ConnectionType.xbox:
            return f'https://account.xbox.com/en-US/Profile?Gamertag={self.name}'
        elif self.type == ConnectionType.github:
            return f'https://github.com/{self.name}'
        elif self.type == ConnectionType.tiktok:
            return f'https://tiktok.com/@{self.name}'
        elif self.type == ConnectionType.ebay:
            return f'https://www.ebay.com/usr/{self.name}'
        elif self.type == ConnectionType.instagram:
            return f'https://www.instagram.com/{self.name}'
class Connection(PartialConnection):
    __slots__ = (
        'state',
        'revoked',
        'friend_sync',
        'show_activity',
        'two_way_link',
        'metadata_visible',
        'access_token',
        'integrations',
    )
    def __init__(self, *, data: ConnectionPayload, state: ConnectionState):
        self._update(data)
        self.state = state
        self.access_token: Optional[str] = None
    def _update(self, data: ConnectionPayload):
        super()._update(data)
        self.revoked: bool = data.get('revoked', False)
        self.visible: bool = bool(data.get('visibility', False))
        self.friend_sync: bool = data.get('friend_sync', False)
        self.show_activity: bool = data.get('show_activity', True)
        self.two_way_link: bool = data.get('two_way_link', False)
        self.metadata_visible: bool = bool(data.get('metadata_visibility', False))
        try:
            self.access_token: Optional[str] = data['access_token']
        except KeyError:
            pass
        self.integrations: List[Integration] = [
            Integration(data=i, guild=self._resolve_guild(i)) for i in data.get('integrations') or []
        ]
    def _resolve_guild(self, data: IntegrationPayload) -> Guild:
        state = self.state
        guild_data = data.get('guild')
        if not guild_data:
            return None
        guild_id = int(guild_data['id'])
        guild = state._get_guild(guild_id)
        if guild is None:
            guild = state.create_guild(guild_data)
        return guild
    async def edit(
        self,
        *,
        name: str = MISSING,
        visible: bool = MISSING,
        friend_sync: bool = MISSING,
        show_activity: bool = MISSING,
        metadata_visible: bool = MISSING,
    ) -> Connection:
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if visible is not MISSING:
            payload['visibility'] = visible
        if show_activity is not MISSING:
            payload['show_activity'] = show_activity
        if friend_sync is not MISSING:
            payload['friend_sync'] = friend_sync
        if metadata_visible is not MISSING:
            payload['metadata_visibility'] = metadata_visible
        data = await self.state.http.edit_connection(self.type.value, self.id, **payload)
        return Connection(data=data, state=self.state)
    async def refresh(self) -> None:
        await self.state.http.refresh_connection(self.type.value, self.id)
    async def delete(self) -> None:
        await self.state.http.delete_connection(self.type.value, self.id)
    async def fetch_access_token(self) -> str:
        data = await self.state.http.get_connection_token(self.type.value, self.id)
        return data['access_token']