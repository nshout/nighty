from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from .application import PartialApplication
from .guild import UserGuild
from .mixins import Hashable
from .utils import MISSING
if TYPE_CHECKING:
    from .abc import Snowflake
    from .permissions import Permissions
    from .state import ConnectionState
    from .user import User
    from .types.oauth2 import OAuth2Authorization as OAuth2AuthorizationPayload, OAuth2Token as OAuth2TokenPayload
__all__ = (
    'OAuth2Token',
    'OAuth2Authorization',
)
class OAuth2Token(Hashable):
    __slots__ = ('id', 'application', 'scopes', '_state')
    def __init__(self, *, state: ConnectionState, data: OAuth2TokenPayload):
        self._state = state
        self.id: int = int(data['id'])
        self.application: PartialApplication = PartialApplication(state=state, data=data['application'])
        self.scopes: List[str] = data['scopes']
    def __repr__(self):
        return f'<OAuth2Token id={self.id} application={self.application!r} scopes={self.scopes!r}>'
    def __str__(self):
        return self.application.name
    @property
    def authorized(self) -> bool:
        return True
    async def revoke(self):
        await self._state.http.revoke_oauth2_token(self.id)
class OAuth2Authorization:
    __slots__ = (
        'authorized',
        'application',
        'bot',
        'approximate_guild_count',
        'guilds',
        'redirect_uri',
        'scopes',
        'response_type',
        'code_challenge_method',
        'code_challenge',
        'state',
        '_state',
    )
    def __init__(
        self,
        *,
        _state: ConnectionState,
        data: OAuth2AuthorizationPayload,
        scopes: List[str],
        response_type: Optional[str],
        code_challenge_method: Optional[str] = None,
        code_challenge: Optional[str] = None,
        state: Optional[str],
    ):
        self._state = _state
        self.scopes: List[str] = scopes
        self.response_type: Optional[str] = response_type
        self.code_challenge_method: Optional[str] = code_challenge_method
        self.code_challenge: Optional[str] = code_challenge
        self.state: Optional[str] = state
        self.authorized: bool = data['authorized']
        self.application: PartialApplication = PartialApplication(state=_state, data=data['application'])
        self.bot: Optional[User] = _state.store_user(data['bot']) if 'bot' in data else None
        self.approximate_guild_count: Optional[int] = (
            data['bot'].get('approximate_guild_count', 0) if 'bot' in data else None
        )
        self.guilds: List[UserGuild] = [UserGuild(state=_state, data=g) for g in data.get('guilds', [])]
        self.redirect_uri: Optional[str] = data.get('redirect_uri')
    def __repr__(self):
        return f'<OAuth2Authorization authorized={self.authorized} application={self.application!r} scopes={self.scopes!r} response_type={self.response_type!r} redirect_uri={self.redirect_uri}>'
    async def authorize(
        self, *, guild: Snowflake = MISSING, channel: Snowflake = MISSING, permissions: Permissions = MISSING
    ) -> str:
        data = await self._state.http.authorize_oauth2(
            self.application.id,
            self.scopes,
            self.response_type,
            self.redirect_uri,
            self.code_challenge_method,
            self.code_challenge,
            self.state,
            guild_id=guild.id if guild else None,
            webhook_channel_id=channel.id if channel else None,
            permissions=permissions.value if permissions else None,
        )
        return data['location']