from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type
from .enums import ExpireBehaviour, try_enum
from .user import User
from .utils import MISSING, _get_as_snowflake, parse_time, utcnow
__all__ = (
    'IntegrationAccount',
    'Integration',
    'StreamIntegration',
    'BotIntegration',
)
if TYPE_CHECKING:
    from datetime import datetime
    from .application import IntegrationApplication
    from .guild import Guild
    from .role import Role
    from .state import ConnectionState
    from .types.integration import (
        BotIntegration as BotIntegrationPayload,
        Integration as IntegrationPayload,
        IntegrationAccount as IntegrationAccountPayload,
        IntegrationType,
        StreamIntegration as StreamIntegrationPayload,
    )
class IntegrationAccount:
    __slots__ = ('id', 'name')
    def __init__(self, data: IntegrationAccountPayload) -> None:
        self.id: str = data['id']
        self.name: str = data['name']
    def __repr__(self) -> str:
        return f'<IntegrationAccount id={self.id} name={self.name!r}>'
class Integration:
    __slots__ = (
        'guild',
        'id',
        'state',
        'type',
        'name',
        'account',
        'user',
        'enabled',
    )
    def __init__(self, *, data: IntegrationPayload, guild: Guild) -> None:
        self.guild: Guild = guild
        self.state: ConnectionState = guild.state
        self._from_data(data)
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} name={self.name!r}>"
    def _from_data(self, data: IntegrationPayload) -> None:
        self.id: int = int(data['id'])
        self.type: IntegrationType = data['type']
        self.name: str = data['name']
        self.account: IntegrationAccount = IntegrationAccount(data['account'])
        user = data.get('user')
        self.user: Optional[User] = User(state=self.state, data=user) if user else None
        self.enabled: bool = data.get('enabled', True)
    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_integration(self.guild.id, self.id, reason=reason)
        self.enabled = False
class StreamIntegration(Integration):
    __slots__ = (
        'revoked',
        'expire_behaviour',
        'expire_grace_period',
        'synced_at',
        '_role_id',
        'syncing',
        'enable_emoticons',
        'subscriber_count',
    )
    def _from_data(self, data: StreamIntegrationPayload) -> None:
        super()._from_data(data)
        self.revoked: bool = data.get('revoked', False)
        self.expire_behaviour: ExpireBehaviour = try_enum(ExpireBehaviour, data.get('expire_behaviour', 0))
        self.expire_grace_period: int = data.get('expire_grace_period', 1)
        self.synced_at: datetime = parse_time(data['synced_at']) if 'synced_at' in data else utcnow()
        self._role_id: Optional[int] = _get_as_snowflake(data, 'role_id')
        self.syncing: bool = data.get('syncing', False)
        self.enable_emoticons: bool = data.get('enable_emoticons', True)
        self.subscriber_count: int = data.get('subscriber_count', 0)
    @property
    def expire_behavior(self) -> ExpireBehaviour:
        return self.expire_behaviour
    @property
    def role(self) -> Optional[Role]:
        return self.guild.get_role(self._role_id)
    async def edit(
        self,
        *,
        expire_behaviour: ExpireBehaviour = MISSING,
        expire_grace_period: int = MISSING,
        enable_emoticons: bool = MISSING,
    ) -> None:
        payload: Dict[str, Any] = {}
        if expire_behaviour is not MISSING:
            payload['expire_behavior'] = int(expire_behaviour)
        if expire_grace_period is not MISSING:
            payload['expire_grace_period'] = expire_grace_period
        if enable_emoticons is not MISSING:
            payload['enable_emoticons'] = enable_emoticons
        await self.state.http.edit_integration(self.guild.id, self.id, **payload)
    async def sync(self) -> None:
        await self.state.http.sync_integration(self.guild.id, self.id)
        self.synced_at = utcnow()
    async def disable(self, *, reason: Optional[str] = None) -> None:
        await self.delete(reason=reason)
    async def enable(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.create_integration(self.guild.id, self.type, self.id, reason=reason)
        self.enabled = True
class BotIntegration(Integration):
    __slots__ = ('application', 'application_id', 'scopes')
    def _from_data(self, data: BotIntegrationPayload) -> None:
        super()._from_data(data)
        self.application: Optional[IntegrationApplication] = (
            self.state.create_integration_application(data['application']) if 'application' in data else None
        )
        self.application_id = self.application.id if self.application else int(data['application_id'])
        self.scopes: List[str] = data.get('scopes', [])
def _integration_factory(value: str) -> Tuple[Type[Integration], str]:
    if value == 'discord':
        return BotIntegration, value
    elif value in ('twitch', 'youtube'):
        return StreamIntegration, value
    else:
        return Integration, value