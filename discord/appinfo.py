from __future__ import annotations
from typing import Collection, List, TYPE_CHECKING, Optional
from . import utils
from .asset import Asset
from .enums import ApplicationType, ApplicationVerificationState, RPCApplicationState, StoreApplicationState, try_enum
from .flags import ApplicationFlags
from .mixins import Hashable
from .permissions import Permissions
from .user import User
if TYPE_CHECKING:
    from .abc import Snowflake, User as abcUser
    from .guild import Guild
    from .types.appinfo import (
        AppInfo as AppInfoPayload,
        PartialAppInfo as PartialAppInfoPayload,
        Team as TeamPayload,
    )
    from .state import ConnectionState
__all__ = (
    'Application',
    'ApplicationBot',
    'PartialApplication',
    'InteractionApplication',
)
MISSING = utils.MISSING
def ClientInfo():
    return True
class ApplicationBot(User):
    __slots__ = ('public', 'require_code_grant')
    def __init__(self, *, data, state: ConnectionState, application: Application):
        super().__init__(state=state, data=data)
        self.application = application
        self.public: bool = data['public']
        self.require_code_grant: bool = data['require_code_grant']
    async def reset_token(self) -> None:
        data = await self.state.http.reset_token(self.application.id)
        return data['token']
    async def edit(
        self,
        *,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
    ) -> None:
        payload = {}
        if public is not MISSING:
            payload['bot_public'] = public
        if require_code_grant is not MISSING:
            payload['bot_require_code_grant'] = require_code_grant
        data = await self.state.http.edit_application(self.application.id, payload=payload)
        self.public = data.get('bot_public', True)
        self.require_code_grant = data.get('bot_require_code_grant', False)
        self.application._update(data)
class PartialApplication(Hashable):
    __slots__ = (
        'state',
        'id',
        'name',
        'description',
        'rpc_origins',
        'verify_key',
        'terms_of_service_url',
        'privacy_policy_url',
        '_icon',
        '_flags',
        '_cover_image',
        'public',
        'require_code_grant',
        'type',
        'hook',
        'premium_tier_level',
        'tags',
        'max_participants',
        'install_url',
    )
    def __init__(self, *, state: ConnectionState, data: PartialAppInfoPayload):
        self.state: ConnectionState = state
        self._update(data)
    def __str__(self) -> str:
        return self.name
    def _update(self, data: PartialAppInfoPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.rpc_origins: Optional[List[str]] = data.get('rpc_origins')
        self.verify_key: str = data['verify_key']
        self._icon: Optional[str] = data.get('icon')
        self._cover_image: Optional[str] = data.get('cover_image')
        self.terms_of_service_url: Optional[str] = data.get(
            'terms_of_service_url')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url')
        self._flags: int = data.get('flags', 0)
        self.type: ApplicationType = try_enum(
            ApplicationType, data.get('type'))
        self.hook: bool = data.get('hook', False)
        self.max_participants: Optional[int] = data.get('max_participants')
        self.premium_tier_level: Optional[int] = data.get(
            'embedded_activity_config', {}).get('activity_premium_tier_level')
        self.tags: List[str] = data.get('tags', [])
        install_params = data.get('install_params', {})
        self.install_url = (
            data.get('custom_install_url')
            if not install_params
            else utils.oauth_url(
                self.id,
                permissions=Permissions(
                    int(install_params.get('permissions', 0))),
                scopes=install_params.get('scopes', utils.MISSING),
            )
        )
        self.public: bool = data.get(
            'integration_public', data.get('bot_public', True)
        )
        self.require_code_grant: bool = data.get(
            'integration_require_code_grant', data.get(
                'bot_require_code_grant', False)
        )
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} description={self.description!r}>'
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='app')
    @property
    def cover_image(self) -> Optional[Asset]:
        if self._cover_image is None:
            return None
        return Asset._from_cover_image(self.state, self.id, self._cover_image)
    @property
    def flags(self) -> ApplicationFlags:
        return ApplicationFlags._from_value(self._flags)
class Application(PartialApplication):
    __slots__ = (
        'owner',
        'team',
        'guild_id',
        'primary_sku_id',
        'slug',
        'redirect_uris',
        'bot',
        'verification_state',
        'store_application_state',
        'rpc_application_state',
        'interactions_endpoint_url',
    )
    def _update(self, data: AppInfoPayload) -> None:
        super()._update(data)
        from .team import Team
        self.guild_id: Optional[int] = utils._get_as_snowflake(
            data, 'guild_id')
        self.redirect_uris: List[str] = data.get('redirect_uris', [])
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(
            data, 'primary_sku_id')
        self.slug: Optional[str] = data.get('slug')
        self.interactions_endpoint_url: Optional[str] = data.get(
            'interactions_endpoint_url')
        self.verification_state = try_enum(
            ApplicationVerificationState, data['verification_state'])
        self.store_application_state = try_enum(
            StoreApplicationState, data.get('store_application_state', 1))
        self.rpc_application_state = try_enum(
            RPCApplicationState, data.get('rpc_application_state', 0))
        state = self.state
        team: Optional[TeamPayload] = data.get('team')
        self.team: Optional[Team] = Team(state, team) if team else None
        if bot := data.get('bot'):
            bot['public'] = data.get('bot_public', self.public)
            bot['require_code_grant'] = data.get(
                'bot_require_code_grant', self.require_code_grant)
        self.bot: Optional[ApplicationBot] = ApplicationBot(
            data=bot, state=state, application=self) if bot else None
        owner = data.get('owner')
        if owner is not None:
            self.owner: abcUser = state.create_user(owner)
        else:
            self.owner: abcUser = state.user
    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'description={self.description!r} public={self.public} '
            f'owner={self.owner!r}>'
        )
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
        icon: Optional[bytes] = MISSING,
        cover_image: Optional[bytes] = MISSING,
        tags: Collection[str] = MISSING,
        terms_of_service_url: Optional[str] = MISSING,
        privacy_policy_url: Optional[str] = MISSING,
        interactions_endpoint_url: Optional[str] = MISSING,
        redirect_uris: Collection[str] = MISSING,
        rpc_origins: Collection[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
        flags: ApplicationFlags = MISSING,
        team: Snowflake = MISSING,
    ) -> None:
        payload = {}
        if name is not MISSING:
            payload['name'] = name or ''
        if description is not MISSING:
            payload['description'] = description or ''
        if icon is not MISSING:
            if icon is not None:
                payload['icon'] = utils._bytes_to_base64_data(icon)
            else:
                payload['icon'] = ''
        if cover_image is not MISSING:
            if cover_image is not None:
                payload['cover_image'] = utils._bytes_to_base64_data(
                    cover_image)
            else:
                payload['cover_image'] = ''
        if tags is not MISSING:
            payload['tags'] = tags
        if terms_of_service_url is not MISSING:
            payload['terms_of_service_url'] = terms_of_service_url or ''
        if privacy_policy_url is not MISSING:
            payload['privacy_policy_url'] = privacy_policy_url or ''
        if interactions_endpoint_url is not MISSING:
            payload['interactions_endpoint_url'] = interactions_endpoint_url or ''
        if redirect_uris is not MISSING:
            payload['redirect_uris'] = redirect_uris
        if rpc_origins is not MISSING:
            payload['rpc_origins'] = rpc_origins
        if public is not MISSING:
            payload['integration_public'] = public
        if require_code_grant is not MISSING:
            payload['integration_require_code_grant'] = require_code_grant
        if flags is not MISSING:
            payload['flags'] = flags.value
        data = await self.state.http.edit_application(self.id, payload)
        if team is not MISSING:
            data = await self.state.http.transfer_application(self.id, team.id)
        self._update(data)
    async def reset_secret(self) -> str:
        data = await self.state.http.reset_secret(self.id)
        return data['secret']
    async def create_bot(self) -> ApplicationBot:
        state = self.state
        data = await state.http.botify_app(self.id)
        data['public'] = self.public
        data['require_code_grant'] = self.require_code_grant
        bot = ApplicationBot(data=data, state=state, application=self)
        self.bot = bot
        return bot
class InteractionApplication(Hashable):
    __slots__ = (
        'state',
        'id',
        'name',
        'description',
        '_icon',
        'type',
        'bot',
    )
    def __init__(self, *, state: ConnectionState, data: dict):
        self.state: ConnectionState = state
        self._update(data)
    def __str__(self) -> str:
        return self.name
    def _update(self, data: dict) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: Optional[str] = data.get('description')
        self._icon: Optional[str] = data.get('icon')
        self.type: Optional[ApplicationType] = try_enum(
            ApplicationType, data['type']) if 'type' in data else None
        self.bot: User = None
        user = data.get('bot')
        if user is not None:
            self.bot = User(state=self.state, data=user)
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r}>'
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='app')