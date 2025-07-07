from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Collection, List, Mapping, Optional, Sequence, Tuple, Union, overload
from urllib.parse import quote
from . import utils
from .asset import Asset, AssetMixin
from .entitlements import Entitlement, GiftBatch
from .enums import (
    ApplicationAssetType,
    ApplicationBuildStatus,
    ApplicationDiscoverabilityState,
    ApplicationMembershipState,
    ApplicationType,
    ApplicationVerificationState,
    Distributor,
    EmbeddedActivityLabelType,
    EmbeddedActivityOrientation,
    EmbeddedActivityPlatform,
    EmbeddedActivityReleasePhase,
    Locale,
    OperatingSystem,
    RPCApplicationState,
    StoreApplicationState,
    UserFlags,
    try_enum,
)
from .flags import ApplicationDiscoveryFlags, ApplicationFlags
from .mixins import Hashable
from .object import OLDEST_OBJECT, Object
from .permissions import Permissions
from .store import SKU, StoreAsset, StoreListing, SystemRequirements
from .team import Team
from .user import User, _UserTag
from .utils import _bytes_to_base64_data, _parse_localizations
if TYPE_CHECKING:
    from datetime import date
    from typing_extensions import Self
    from .abc import Snowflake, SnowflakeTime
    from .enums import SKUAccessLevel, SKUFeature, SKUGenre, SKUType
    from .file import File
    from .guild import Guild
    from .metadata import MetadataObject
    from .state import ConnectionState
    from .store import ContentRating
    from .types.application import (
        EULA as EULAPayload,
        Achievement as AchievementPayload,
        ActivityStatistics as ActivityStatisticsPayload,
        Application as ApplicationPayload,
        ApplicationExecutable as ApplicationExecutablePayload,
        ApplicationInstallParams as ApplicationInstallParamsPayload,
        Asset as AssetPayload,
        BaseApplication as BaseApplicationPayload,
        Branch as BranchPayload,
        Build as BuildPayload,
        Company as CompanyPayload,
        EmbeddedActivityConfig as EmbeddedActivityConfigPayload,
        EmbeddedActivityPlatform as EmbeddedActivityPlatformValues,
        EmbeddedActivityPlatformConfig as EmbeddedActivityPlatformConfigPayload,
        GlobalActivityStatistics as GlobalActivityStatisticsPayload,
        InteractionsVersion,
        Manifest as ManifestPayload,
        ManifestLabel as ManifestLabelPayload,
        PartialApplication as PartialApplicationPayload,
        ThirdPartySKU as ThirdPartySKUPayload,
        UnverifiedApplication as UnverifiedApplicationPayload,
        WhitelistedUser as WhitelistedUserPayload,
    )
    from .types.user import PartialUser as PartialUserPayload
__all__ = (
    'Company',
    'EULA',
    'Achievement',
    'ThirdPartySKU',
    'EmbeddedActivityPlatformConfig',
    'EmbeddedActivityConfig',
    'ApplicationBot',
    'ApplicationExecutable',
    'ApplicationInstallParams',
    'ApplicationAsset',
    'ApplicationActivityStatistics',
    'ManifestLabel',
    'Manifest',
    'ApplicationBuild',
    'ApplicationBranch',
    'ApplicationTester',
    'PartialApplication',
    'Application',
    'IntegrationApplication',
    'UnverifiedApplication',
)
MISSING = utils.MISSING
class Company(Hashable):
    __slots__ = ('id', 'name')
    def __init__(self, data: CompanyPayload):
        self.id: int = int(data['id'])
        self.name: str = data['name']
    def __repr__(self) -> str:
        return f'<Company id={self.id} name={self.name!r}>'
    def __str__(self) -> str:
        return self.name
class EULA(Hashable):
    __slots__ = ('id', 'name', 'content')
    def __init__(self, data: EULAPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.content: str = data['content']
    def __repr__(self) -> str:
        return f'<EULA id={self.id} name={self.name!r}>'
    def __str__(self) -> str:
        return self.name
class Achievement(Hashable):
    __slots__ = (
        'id',
        'name',
        'name_localizations',
        'description',
        'description_localizations',
        'application_id',
        'secure',
        'secret',
        '_icon',
        'state',
    )
    if TYPE_CHECKING:
        name: str
        name_localizations: dict[Locale, str]
        description: str
        description_localizations: dict[Locale, str]
    def __init__(self, *, data: AchievementPayload, state: ConnectionState):
        self.state = state
        self._update(data)
    def _update(self, data: AchievementPayload):
        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self.secure: bool = data.get('secure', False)
        self.secret: bool = data.get('secret', False)
        self._icon = data.get('icon', data.get('icon_hash'))
        self.name, self.name_localizations = _parse_localizations(data, 'name')
        self.description, self.description_localizations = _parse_localizations(data, 'description')
    def __repr__(self) -> str:
        return f'<Achievement id={self.id} name={self.name!r}>'
    def __str__(self) -> str:
        return self.name
    @property
    def icon(self) -> Asset:
        return Asset._from_achievement_icon(self.state, self.application_id, self.id, self._icon)
    async def edit(
        self,
        *,
        name: str = MISSING,
        name_localizations: Mapping[Locale, str] = MISSING,
        description: str = MISSING,
        description_localizations: Mapping[Locale, str] = MISSING,
        icon: bytes = MISSING,
        secure: bool = MISSING,
        secret: bool = MISSING,
    ) -> None:
        payload = {}
        if secure is not MISSING:
            payload['secure'] = secure
        if secret is not MISSING:
            payload['secret'] = secret
        if icon is not MISSING:
            payload['icon'] = utils._bytes_to_base64_data(icon)
        if name is not MISSING or name_localizations is not MISSING:
            localizations = (name_localizations or {}) if name_localizations is not MISSING else self.name_localizations
            payload['name'] = {'default': name or self.name, 'localizations': {str(k): v for k, v in localizations.items()}}
        if description is not MISSING or description_localizations is not MISSING:
            localizations = (
                (name_localizations or {}) if description_localizations is not MISSING else self.description_localizations
            )
            payload['description'] = {
                'default': description or self.description,
                'localizations': {str(k): v for k, v in localizations.items()},
            }
        data = await self.state.http.edit_achievement(self.application_id, self.id, payload)
        self._update(data)
    async def update(self, user: Snowflake, percent_complete: int) -> None:
        await self.state.http.update_user_achievement(self.application_id, self.id, user.id, percent_complete)
    async def delete(self):
        await self.state.http.delete_achievement(self.application_id, self.id)
class ThirdPartySKU:
    __slots__ = ('application', 'distributor', 'id', 'sku_id')
    def __init__(self, *, data: ThirdPartySKUPayload, application: Union[PartialApplication, IntegrationApplication]):
        self.application = application
        self.distributor: Distributor = try_enum(Distributor, data['distributor'])
        self.id: Optional[str] = data.get('id') or None
        self.sku_id: Optional[str] = data.get('sku_id') or None
    def __repr__(self) -> str:
        return f'<ThirdPartySKU distributor={self.distributor!r} id={self.id!r} sku_id={self.sku_id!r}>'
    @property
    def _id(self) -> str:
        return self.id or self.sku_id or ''
    @property
    def url(self) -> Optional[str]:
        if not self._id:
            return
        if self.distributor == Distributor.discord:
            return f'https://discord.com/store/skus/{self._id}'
        elif self.distributor == Distributor.steam:
            return f'https://store.steampowered.com/app/{self._id}'
        elif self.distributor == Distributor.epic_games:
            return f'https://store.epicgames.com/en-US/p/{self.application.name.replace(" ", "-")}'
        elif self.distributor == Distributor.google_play:
            return f'https://play.google.com/store/apps/details?id={self._id}'
class EmbeddedActivityPlatformConfig:
    __slots__ = ('platform', 'label_type', 'label_until', 'release_phase')
    def __init__(
        self,
        platform: EmbeddedActivityPlatform,
        *,
        label_type: EmbeddedActivityLabelType = EmbeddedActivityLabelType.none,
        label_until: Optional[datetime] = None,
        release_phase: EmbeddedActivityReleasePhase = EmbeddedActivityReleasePhase.global_launch,
    ):
        self.platform = platform
        self.label_type = label_type
        self.label_until = label_until
        self.release_phase = release_phase
    @classmethod
    def from_data(cls, *, data: EmbeddedActivityPlatformConfigPayload, platform: EmbeddedActivityPlatformValues) -> Self:
        return cls(
            try_enum(EmbeddedActivityPlatform, platform),
            label_type=try_enum(EmbeddedActivityLabelType, data.get('label_type', 0)),
            label_until=utils.parse_time(data.get('label_until')),
            release_phase=try_enum(EmbeddedActivityReleasePhase, data.get('release_phase', 'global_launch')),
        )
    def __repr__(self) -> str:
        return (
            f'<EmbeddedActivityPlatformConfig platform={self.platform!r} label_type={self.label_type!r} '
            f'label_until={self.label_until!r} release_phase={self.release_phase!r}>'
        )
    def to_dict(self) -> EmbeddedActivityPlatformConfigPayload:
        return {
            'label_type': self.label_type.value,
            'label_until': self.label_until.isoformat() if self.label_until else None,
            'release_phase': self.release_phase.value,
        }
class EmbeddedActivityConfig:
    __slots__ = (
        'application',
        'supported_platforms',
        'platform_configs',
        'orientation_lock_state',
        'tablet_orientation_lock_state',
        'premium_tier_requirement',
        'requires_age_gate',
        'shelf_rank',
        'free_period_starts_at',
        'free_period_ends_at',
        '_preview_video_asset_id',
    )
    def __init__(self, *, data: EmbeddedActivityConfigPayload, application: PartialApplication) -> None:
        self.application: PartialApplication = application
        self._update(data)
    def __repr__(self) -> str:
        return f'<EmbeddedActivityConfig supported_platforms={self.supported_platforms!r} orientation_lock_state={self.orientation_lock_state!r} tablet_orientation_lock_state={self.tablet_orientation_lock_state!r} premium_tier_requirement={self.premium_tier_requirement!r} requires_age_gate={self.requires_age_gate!r}>'
    def _update(self, data: EmbeddedActivityConfigPayload) -> None:
        self.supported_platforms: List[EmbeddedActivityPlatform] = [
            try_enum(EmbeddedActivityPlatform, platform) for platform in data.get('supported_platforms', [])
        ]
        self.platform_configs: List[EmbeddedActivityPlatformConfig] = [
            EmbeddedActivityPlatformConfig.from_data(platform=platform, data=config)
            for platform, config in data.get('client_platform_config', {}).items()
        ]
        self.orientation_lock_state: EmbeddedActivityOrientation = try_enum(
            EmbeddedActivityOrientation, data.get('default_orientation_lock_state', 0)
        )
        self.tablet_orientation_lock_state: EmbeddedActivityOrientation = try_enum(
            EmbeddedActivityOrientation, data.get('tablet_default_orientation_lock_state', 0)
        )
        self.premium_tier_requirement: int = data.get('premium_tier_requirement') or 0
        self.requires_age_gate: bool = data.get('requires_age_gate', False)
        self.shelf_rank: int = data.get('shelf_rank', 0)
        self.free_period_starts_at: Optional[datetime] = utils.parse_time(data.get('free_period_starts_at'))
        self.free_period_ends_at: Optional[datetime] = utils.parse_time(data.get('free_period_ends_at'))
        self._preview_video_asset_id = utils._get_as_snowflake(data, 'preview_video_asset_id')
    @property
    def preview_video_asset(self) -> Optional[ApplicationAsset]:
        if self._preview_video_asset_id is None:
            return None
        return ApplicationAsset._from_embedded_activity_config(self.application, self._preview_video_asset_id)
    async def edit(
        self,
        *,
        supported_platforms: Collection[EmbeddedActivityPlatform] = MISSING,
        platform_configs: Collection[EmbeddedActivityPlatformConfig] = MISSING,
        orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        tablet_orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        requires_age_gate: bool = MISSING,
        shelf_rank: int = MISSING,
        free_period_starts_at: Optional[datetime] = MISSING,
        free_period_ends_at: Optional[datetime] = MISSING,
        preview_video_asset: Optional[Snowflake] = MISSING,
    ) -> None:
        data = await self.application.state.http.edit_embedded_activity_config(
            self.application.id,
            supported_platforms=[str(x) for x in (supported_platforms)] if supported_platforms is not MISSING else None,
            platform_config={c.platform.value: c.to_dict() for c in (platform_configs)}
            if platform_configs is not MISSING
            else None,
            orientation_lock_state=int(orientation_lock_state) if orientation_lock_state is not MISSING else None,
            tablet_orientation_lock_state=int(tablet_orientation_lock_state)
            if tablet_orientation_lock_state is not MISSING
            else None,
            requires_age_gate=requires_age_gate if requires_age_gate is not MISSING else None,
            shelf_rank=shelf_rank if shelf_rank is not MISSING else None,
            free_period_starts_at=free_period_starts_at.isoformat() if free_period_starts_at else None,
            free_period_ends_at=free_period_ends_at.isoformat() if free_period_ends_at else None,
            preview_video_asset_id=(preview_video_asset.id if preview_video_asset else None)
            if preview_video_asset is not MISSING
            else MISSING,
        )
        self._update(data)
class ApplicationBot(User):
    __slots__ = ('application',)
    def __init__(self, *, data: PartialUserPayload, state: ConnectionState, application: Application):
        super().__init__(state=state, data=data)
        self.application = application
    def _update(self, data: PartialUserPayload) -> None:
        super()._update(data)
    def __repr__(self) -> str:
        return f'<ApplicationBot id={self.id} name={self.name!r} discriminator={self.discriminator!r} public={self.public} require_code_grant={self.require_code_grant}>'
    @property
    def public(self) -> bool:
        return self.application.public
    @property
    def require_code_grant(self) -> bool:
        return self.application.require_code_grant
    @property
    def disabled(self) -> bool:
        return self.application.disabled
    @property
    def quarantined(self) -> bool:
        return self.application.quarantined
    @property
    def bio(self) -> Optional[str]:
        return self.application.description or None
    @property
    def mfa_enabled(self) -> bool:
        if self.application.owner.public_flags.team_user:
            return True
        return self.state.user.mfa_enabled
    @property
    def verified(self) -> bool:
        return True
    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[bytes] = MISSING,
        bio: Optional[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
    ) -> None:
        payload = {}
        if username is not MISSING:
            payload['username'] = username
        if avatar is not MISSING:
            if avatar is not None:
                payload['avatar'] = _bytes_to_base64_data(avatar)
            else:
                payload['avatar'] = None
        if payload:
            data = await self.state.http.edit_bot(self.application.id, payload)
            self._update(data)
            payload = {}
        if public is not MISSING:
            payload['bot_public'] = public
        if require_code_grant is not MISSING:
            payload['bot_require_code_grant'] = require_code_grant
        if bio is not MISSING:
            payload['description'] = bio
        if payload:
            data = await self.state.http.edit_application(self.application.id, payload)
            self.application._update(data)
    async def token(self) -> str:
        data = await self.state.http.reset_bot_token(self.application.id)
        return data['token']
class ApplicationExecutable:
    __slots__ = (
        'name',
        'os',
        'launcher',
        'application',
    )
    def __init__(self, *, data: ApplicationExecutablePayload, application: PartialApplication):
        self.name: str = data['name']
        self.os: OperatingSystem = OperatingSystem.from_string(data['os'])
        self.launcher: bool = data['is_launcher']
        self.application = application
    def __repr__(self) -> str:
        return f'<ApplicationExecutable name={self.name!r} os={self.os!r} launcher={self.launcher!r}>'
    def __str__(self) -> str:
        return self.name
class ApplicationInstallParams:
    __slots__ = ('application_id', 'scopes', 'permissions')
    def __init__(
        self, application_id: int, *, scopes: Optional[Collection[str]] = None, permissions: Optional[Permissions] = None
    ):
        self.application_id: int = application_id
        self.scopes: List[str] = [scope for scope in scopes] if scopes else ['bot', 'applications.commands']
        self.permissions: Permissions = permissions or Permissions(0)
    @classmethod
    def from_application(cls, application: Snowflake, data: ApplicationInstallParamsPayload) -> ApplicationInstallParams:
        return cls(
            application.id,
            scopes=data.get('scopes', []),
            permissions=Permissions(int(data.get('permissions', 0))),
        )
    def __repr__(self) -> str:
        return f'<ApplicationInstallParams application_id={self.application_id} scopes={self.scopes!r} permissions={self.permissions!r}>'
    def __str__(self) -> str:
        return self.url
    @property
    def url(self) -> str:
        return utils.oauth_url(self.application_id, permissions=self.permissions, scopes=self.scopes)
    def to_dict(self) -> dict:
        return {
            'scopes': self.scopes,
            'permissions': self.permissions.value,
        }
class ApplicationAsset(AssetMixin, Hashable):
    __slots__ = ('state', 'id', 'name', 'type', 'application')
    def __init__(self, *, data: AssetPayload, application: Union[PartialApplication, IntegrationApplication]) -> None:
        self.state: ConnectionState = application.state
        self.application = application
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.type: ApplicationAssetType = try_enum(ApplicationAssetType, data.get('type', 1))
    def __repr__(self) -> str:
        return f'<ApplicationAsset id={self.id} name={self.name!r}>'
    def __str__(self) -> str:
        return self.name
    @classmethod
    def _from_embedded_activity_config(
        cls, application: Union[PartialApplication, IntegrationApplication], id: int
    ) -> ApplicationAsset:
        return cls(data={'id': id, 'name': '', 'type': 1}, application=application)
    @property
    def animated(self) -> bool:
        return False
    @property
    def url(self) -> str:
        return f'{Asset.BASE}/app-assets/{self.application.id}/{self.id}.png'
    async def delete(self) -> None:
        await self.state.http.delete_asset(self.application.id, self.id)
class ApplicationActivityStatistics:
    __slots__ = ('application_id', 'user_id', 'duration', 'sku_duration', 'updated_at', 'state')
    def __init__(
        self,
        *,
        data: Union[ActivityStatisticsPayload, GlobalActivityStatisticsPayload],
        state: ConnectionState,
        application_id: Optional[int] = None,
    ) -> None:
        self.state = state
        self.application_id = application_id or int(data['application_id'])
        self.user_id: int = int(data['user_id']) if 'user_id' in data else state.self_id
        self.duration: int = data.get('total_duration', data.get('duration', 0))
        self.sku_duration: int = data.get('total_discord_sku_duration', 0)
        self.updated_at: datetime = utils.parse_time(data.get('last_played_at', data.get('updated_at'))) or utils.utcnow()
    def __repr__(self) -> str:
        return f'<ApplicationActivityStatistics user_id={self.user_id} duration={self.duration} last_played_at={self.updated_at!r}>'
    @property
    def user(self) -> Optional[User]:
        return self.state.get_user(self.user_id)
    async def application(self) -> PartialApplication:
        state = self.state
        data = await state.http.get_partial_application(self.application_id)
        return PartialApplication(state=state, data=data)
class ManifestLabel(Hashable):
    __slots__ = ('id', 'application_id', 'name')
    def __new__(cls, *, data: ManifestLabelPayload, application_id: Optional[int] = None) -> Union[ManifestLabel, int]:
        if data.get('name') is None:
            return int(data['id'])
        if application_id is not None:
            data['application_id'] = application_id
        return super().__new__(cls)
    def __init__(self, *, data: ManifestLabelPayload, **kwargs) -> None:
        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self.name: Optional[str] = data.get('name')
    def __repr__(self) -> str:
        return f'<ManifestLabel id={self.id} application_id={self.application_id} name={self.name!r}>'
class Manifest(Hashable):
    __slots__ = ('id', 'application_id', 'label_id', 'label', 'redistributable_label_ids', 'url', 'state')
    if TYPE_CHECKING:
        label_id: int
        label: Optional[ManifestLabel]
    def __init__(self, *, data: ManifestPayload, state: ConnectionState, application_id: int) -> None:
        self.state = state
        self.id: int = int(data['id'])
        self.application_id = application_id
        self.redistributable_label_ids: List[int] = [int(r) for r in data.get('redistributable_label_ids', [])]
        self.url: Optional[str] = data.get('url')
        label = ManifestLabel(data=data['label'], application_id=application_id)
        if isinstance(label, int):
            self.label_id = label
            self.label = None
        else:
            self.label_id = label.id
            self.label = label
    def __repr__(self) -> str:
        return f'<Manifest id={self.id} application_id={self.application_id} label_id={self.label_id}>'
    async def upload(self, manifest: MetadataObject, /) -> None:
        if not self.url:
            raise ValueError('Manifest URL is not set')
        await self.state.http.upload_to_cloud(self.url, utils._to_json(dict(manifest)))
class ApplicationBuild(Hashable):
    def __init__(self, *, data: BuildPayload, state: ConnectionState, branch: ApplicationBranch) -> None:
        self.state = state
        self.branch = branch
        self._update(data)
    def _update(self, data: BuildPayload) -> None:
        state = self.state
        self.id: int = int(data['id'])
        self.application_id: int = self.branch.application_id
        self.created_at: datetime = (
            utils.parse_time(data['created_at']) if 'created_at' in data else utils.snowflake_time(self.id)
        )
        self.status: ApplicationBuildStatus = try_enum(ApplicationBuildStatus, data['status'])
        self.source_build_id: Optional[int] = utils._get_as_snowflake(data, 'source_build_id')
        self.version: Optional[str] = data.get('version')
        self.manifests: List[Manifest] = [
            Manifest(data=m, state=state, application_id=self.application_id) for m in data.get('manifests', [])
        ]
    def __repr__(self) -> str:
        return f'<ApplicationBuild id={self.id} application_id={self.application_id} status={self.status!r}>'
    @staticmethod
    def format_download_url(
        endpoint: str, application_id, branch_id, build_id, manifest_id, user_id, expires: int, signature: str
    ) -> str:
        return f'{endpoint}/apps/{application_id}/builds/{build_id}/manifests/{manifest_id}/metadata/MANIFEST?branch_id={branch_id}&manifest_id={manifest_id}&user_id={user_id}&expires={expires}&signature={quote(signature)}'
    async def size(self, manifests: Collection[Snowflake] = MISSING) -> float:
        data = await self.state.http.get_branch_build_size(
            self.application_id, self.branch.id, self.id, [m.id for m in manifests or self.manifests]
        )
        return float(data['size_kb'])
    async def download_urls(self, manifest_labels: Collection[Snowflake] = MISSING) -> List[str]:
        state = self.state
        app_id, branch_id, build_id, user_id = self.application_id, self.branch.id, self.id, state.self_id
        data = await state.http.get_branch_build_download_signatures(
            app_id,
            branch_id,
            build_id,
            [m.id for m in manifest_labels] if manifest_labels else list({m.label_id for m in self.manifests}),
        )
        return [
            self.format_download_url(v['endpoint'], app_id, branch_id, build_id, k, user_id, v['expires'], v['signature'])
            for k, v in data.items()
        ]
    async def edit(self, status: ApplicationBuildStatus) -> None:
        await self.state.http.edit_build(self.application_id, self.id, str(status))
        self.status = try_enum(ApplicationBuildStatus, str(status))
    async def upload_files(self, *files: File, hash: bool = True) -> None:
        r
        if not files:
            return
        urls = await self.state.http.get_build_upload_urls(self.application_id, self.id, files, hash)
        id_files = {f.filename: f for f in files}
        for url in urls:
            file = id_files.get(url['id'])
            if file:
                await self.state.http.upload_to_cloud(url['url'], file, file.b64_md5 if hash else None)
    async def publish(self) -> None:
        await self.state.http.publish_build(self.application_id, self.branch.id, self.id)
    async def delete(self) -> None:
        await self.state.http.delete_build(self.application_id, self.id)
class ApplicationBranch(Hashable):
    __slots__ = ('id', 'live_build_id', 'name', 'application_id', '_created_at', 'state')
    def __init__(self, *, data: BranchPayload, state: ConnectionState, application_id: int) -> None:
        self.state = state
        self.application_id = application_id
        self.id: int = int(data['id'])
        self.name: str = data['name'] if 'name' in data else ('master' if self.id == self.application_id else 'unknown')
        self.live_build_id: Optional[int] = utils._get_as_snowflake(data, 'live_build_id')
        self._created_at = data.get('created_at')
    def __repr__(self) -> str:
        return f'<ApplicationBranch id={self.id} name={self.name!r} live_build_id={self.live_build_id!r}>'
    def __str__(self) -> str:
        return self.name
    @property
    def created_at(self) -> datetime:
        return utils.parse_time(self._created_at) if self._created_at else utils.snowflake_time(self.id)
    def is_master(self) -> bool:
        return self.id == self.application_id
    async def builds(self) -> List[ApplicationBuild]:
        data = await self.state.http.get_branch_builds(self.application_id, self.id)
        return [ApplicationBuild(data=build, state=self.state, branch=self) for build in data]
    async def fetch_build(self, build_id: int, /) -> ApplicationBuild:
        data = await self.state.http.get_branch_build(self.application_id, self.id, build_id)
        return ApplicationBuild(data=data, state=self.state, branch=self)
    async def fetch_live_build_id(self) -> Optional[int]:
        data = await self.state.http.get_build_ids((self.id,))
        if not data:
            return
        branch = data[0]
        self.live_build_id = build_id = utils._get_as_snowflake(branch, 'live_build_id')
        return build_id
    async def live_build(self, *, locale: Locale = MISSING, platform: str) -> ApplicationBuild:
        state = self.state
        data = await state.http.get_live_branch_build(
            self.application_id, self.id, str(locale) if locale else state.locale, str(platform)
        )
        self.live_build_id = int(data['id'])
        return ApplicationBuild(data=data, state=self.state, branch=self)
    async def latest_build(self) -> ApplicationBuild:
        data = await self.state.http.get_latest_branch_build(self.application_id, self.id)
        return ApplicationBuild(data=data, state=self.state, branch=self)
    async def create_build(
        self,
        *,
        built_with: str = "DISPATCH",
        manifests: Sequence[MetadataObject],
        source_build: Optional[Snowflake] = None,
    ) -> Tuple[ApplicationBuild, List[Manifest]]:
        state = self.state
        app_id = self.application_id
        payload = {'built_with': built_with, 'manifests': [dict(m) for m in manifests]}
        if source_build:
            payload['source_build_id'] = source_build.id
        data = await state.http.create_branch_build(app_id, self.id, payload)
        build = ApplicationBuild(data=data['build'], state=state, branch=self)
        manifest_uploads = [Manifest(data=m, state=state, application_id=app_id) for m in data['manifest_uploads']]
        return build, manifest_uploads
    async def promote(self, branch: Snowflake, /) -> None:
        await self.state.http.promote_build(self.application_id, self.id, branch.id)
    async def delete(self) -> None:
        await self.state.http.delete_app_branch(self.application_id, self.id)
class ApplicationTester(User):
    __slots__ = ('application', 'state')
    def __init__(self, application: Application, state: ConnectionState, data: WhitelistedUserPayload):
        self.application: Application = application
        self.state: ApplicationMembershipState = try_enum(ApplicationMembershipState, data['state'])
        super().__init__(state=state, data=data['user'])
    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'discriminator={self.discriminator!r} state={self.state!r}>'
        )
    async def remove(self) -> None:
        await self.state.http.delete_app_whitelist(self.application.id, self.id)
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
        'deeplink_uri',
        '_icon',
        '_flags',
        '_cover_image',
        '_splash',
        'public',
        'require_code_grant',
        'type',
        'hook',
        'tags',
        'max_participants',
        'overlay',
        'overlay_warn',
        'overlay_compatibility_hook',
        'aliases',
        'developers',
        'publishers',
        'executables',
        'third_party_skus',
        'custom_install_url',
        'install_params',
        'embedded_activity_config',
        'guild_id',
        'primary_sku_id',
        'store_listing_sku_id',
        'slug',
        'eula_id',
        'owner',
        'team',
        '_guild',
        '_has_bot',
    )
    if TYPE_CHECKING:
        owner: Optional[User]
        team: Optional[Team]
    def __init__(self, *, state: ConnectionState, data: PartialApplicationPayload):
        self.state: ConnectionState = state
        self._update(data)
    def __str__(self) -> str:
        return self.name
    def _update(self, data: PartialApplicationPayload) -> None:
        state = self.state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.rpc_origins: Optional[List[str]] = data.get('rpc_origins')
        self.verify_key: str = data['verify_key']
        self.aliases: List[str] = data.get('aliases', [])
        self.developers: List[Company] = [Company(data=d) for d in data.get('developers', [])]
        self.publishers: List[Company] = [Company(data=d) for d in data.get('publishers', [])]
        self.executables: List[ApplicationExecutable] = [
            ApplicationExecutable(data=e, application=self) for e in data.get('executables', [])
        ]
        self.third_party_skus: List[ThirdPartySKU] = [
            ThirdPartySKU(data=t, application=self) for t in data.get('third_party_skus', [])
        ]
        self._icon: Optional[str] = data.get('icon')
        self._cover_image: Optional[str] = data.get('cover_image')
        self._splash: Optional[str] = data.get('splash')
        self.terms_of_service_url: Optional[str] = data.get('terms_of_service_url')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url')
        self.deeplink_uri: Optional[str] = data.get('deeplink_uri')
        self._flags: int = data.get('flags', 0)
        self.type: Optional[ApplicationType] = try_enum(ApplicationType, data['type']) if data.get('type') else None
        self.hook: bool = data.get('hook', False)
        self.max_participants: Optional[int] = data.get('max_participants')
        self.tags: List[str] = data.get('tags', [])
        self.overlay: bool = data.get('overlay', False)
        self.overlay_warn: bool = data.get('overlay_warn', False)
        self.overlay_compatibility_hook: bool = data.get('overlay_compatibility_hook', False)
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self.store_listing_sku_id: Optional[int] = utils._get_as_snowflake(data, 'store_listing_sku_id')
        self.slug: Optional[str] = data.get('slug')
        self.eula_id: Optional[int] = utils._get_as_snowflake(data, 'eula_id')
        params = data.get('install_params')
        self.custom_install_url: Optional[str] = data.get('custom_install_url')
        self.install_params: Optional[ApplicationInstallParams] = (
            ApplicationInstallParams.from_application(self, params) if params else None
        )
        self.embedded_activity_config: Optional[EmbeddedActivityConfig] = (
            EmbeddedActivityConfig(data=data['embedded_activity_config'], application=self)
            if 'embedded_activity_config' in data
            else None
        )
        self.public: bool = data.get('integration_public', data.get('bot_public', True))
        self.require_code_grant: bool = data.get('integration_require_code_grant', data.get('bot_require_code_grant', False))
        self._has_bot: bool = 'bot_public' in data
        self._guild: Optional[Guild] = state.create_guild(data['guild']) if 'guild' in data else None
        existing = getattr(self, 'owner', None)
        owner = data.get('owner')
        self.owner = state.create_user(owner) if owner else existing
        existing = getattr(self, 'team', None)
        team = data.get('team')
        if existing and team:
            existing._update(team)
        else:
            self.team = Team(state=state, data=team) if team else existing
        if self.team and not self.owner:
            team = self.team
            payload: PartialUserPayload = {
                'id': team.id,
                'username': f'team{team.id}',
                'global_name': None,
                'public_flags': UserFlags.team_user.value,
                'discriminator': '0000',
                'avatar': None,
            }
            self.owner = state.create_user(payload)
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} description={self.description!r}>'
    @property
    def created_at(self) -> datetime:
        return utils.snowflake_time(self.id)
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='app')
    @property
    def cover_image(self) -> Optional[Asset]:
        if self._cover_image is None:
            return None
        return Asset._from_icon(self.state, self.id, self._cover_image, path='app')
    @property
    def splash(self) -> Optional[Asset]:
        if self._splash is None:
            return None
        return Asset._from_icon(self.state, self.id, self._splash, path='app')
    @property
    def flags(self) -> ApplicationFlags:
        return ApplicationFlags._from_value(self._flags)
    @property
    def install_url(self) -> Optional[str]:
        return self.custom_install_url or self.install_params.url if self.install_params else None
    @property
    def primary_sku_url(self) -> Optional[str]:
        if self.primary_sku_id:
            return f'https://discord.com/store/skus/{self.primary_sku_id}/{self.slug or "unknown"}'
    @property
    def store_listing_sku_url(self) -> Optional[str]:
        if self.store_listing_sku_id:
            return f'https://discord.com/store/skus/{self.store_listing_sku_id}/{self.slug or "unknown"}'
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id) or self._guild
    def has_bot(self) -> bool:
        return self._has_bot
    def is_rpc_enabled(self) -> bool:
        return self.rpc_origins is not None
    async def assets(self) -> List[ApplicationAsset]:
        data = await self.state.http.get_app_assets(self.id)
        return [ApplicationAsset(data=d, application=self) for d in data]
    async def published_store_listings(self, *, localize: bool = True) -> List[StoreListing]:
        state = self.state
        data = await state.http.get_app_store_listings(self.id, country_code=state.country_code or 'US', localize=localize)
        return [StoreListing(state=state, data=d, application=self) for d in data]
    async def primary_store_listing(self, *, localize: bool = True) -> StoreListing:
        state = self.state
        data = await state.http.get_app_store_listing(self.id, country_code=state.country_code or 'US', localize=localize)
        return StoreListing(state=state, data=data, application=self)
    async def achievements(self, completed: bool = True) -> List[Achievement]:
        state = self.state
        data = (await state.http.get_my_achievements(self.id)) if completed else (await state.http.get_achievements(self.id))
        return [Achievement(data=achievement, state=state) for achievement in data]
    async def entitlements(self, *, exclude_consumed: bool = True) -> List[Entitlement]:
        state = self.state
        data = await state.http.get_user_app_entitlements(self.id, exclude_consumed=exclude_consumed)
        return [Entitlement(data=entitlement, state=state) for entitlement in data]
    async def eula(self) -> Optional[EULA]:
        if self.eula_id is None:
            return None
        state = self.state
        data = await state.http.get_eula(self.eula_id)
        return EULA(data=data)
    async def ticket(self) -> str:
        state = self.state
        data = await state.http.get_app_ticket(self.id)
        return data['ticket']
    async def entitlement_ticket(self) -> str:
        state = self.state
        data = await state.http.get_app_entitlement_ticket(self.id)
        return data['ticket']
    async def activity_statistics(self) -> List[ApplicationActivityStatistics]:
        state = self.state
        app_id = self.id
        data = await state.http.get_app_activity_statistics(app_id)
        return [ApplicationActivityStatistics(data=activity, state=state, application_id=app_id) for activity in data]
class Application(PartialApplication):
    __slots__ = (
        'owner',
        'redirect_uris',
        'interactions_endpoint_url',
        'interactions_version',
        'interactions_event_types',
        'role_connections_verification_url',
        'bot',
        'disabled',
        'quarantined',
        'verification_state',
        'store_application_state',
        'rpc_application_state',
        'discoverability_state',
        '_discovery_eligibility_flags',
        'approximate_guild_count',
    )
    if TYPE_CHECKING:
        owner: User
    def __init__(self, *, state: ConnectionState, data: ApplicationPayload, team: Optional[Team] = None):
        self.team = team
        super().__init__(state=state, data=data)
    def _update(self, data: ApplicationPayload) -> None:
        super()._update(data)
        self.disabled: bool = data.get('bot_disabled', False)
        self.quarantined: bool = data.get('bot_quarantined', False)
        self.redirect_uris: List[str] = data.get('redirect_uris', [])
        self.interactions_endpoint_url: Optional[str] = data.get('interactions_endpoint_url')
        self.interactions_version: InteractionsVersion = data.get('interactions_version', 1)
        self.interactions_event_types: List[str] = data.get('interactions_event_types', [])
        self.role_connections_verification_url: Optional[str] = data.get('role_connections_verification_url')
        self.verification_state = try_enum(ApplicationVerificationState, data['verification_state'])
        self.store_application_state = try_enum(StoreApplicationState, data.get('store_application_state', 1))
        self.rpc_application_state = try_enum(RPCApplicationState, data.get('rpc_application_state', 0))
        self.discoverability_state = try_enum(ApplicationDiscoverabilityState, data.get('discoverability_state', 1))
        self._discovery_eligibility_flags = data.get('discovery_eligibility_flags', 0)
        self.approximate_guild_count: int = data.get('approximate_guild_count', 0)
        state = self.state
        existing = getattr(self, 'bot', None)
        bot = data.get('bot')
        if existing is not None:
            existing._update(bot)
        else:
            self.bot: Optional[ApplicationBot] = ApplicationBot(data=bot, state=state, application=self) if bot else None
        self.owner = self.owner or state.user
    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'description={self.description!r} public={self.public} '
            f'owner={self.owner!r}>'
        )
    @property
    def discovery_eligibility_flags(self) -> ApplicationDiscoveryFlags:
        return ApplicationDiscoveryFlags._from_value(self._discovery_eligibility_flags)
    def has_bot(self) -> bool:
        return self.bot is not None
    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
        icon: Optional[bytes] = MISSING,
        cover_image: Optional[bytes] = MISSING,
        tags: Sequence[str] = MISSING,
        terms_of_service_url: Optional[str] = MISSING,
        privacy_policy_url: Optional[str] = MISSING,
        deeplink_uri: Optional[str] = MISSING,
        interactions_endpoint_url: Optional[str] = MISSING,
        interactions_version: InteractionsVersion = MISSING,
        interactions_event_types: Sequence[str] = MISSING,
        role_connections_verification_url: Optional[str] = MISSING,
        redirect_uris: Sequence[str] = MISSING,
        rpc_origins: Sequence[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
        discoverable: bool = MISSING,
        max_participants: Optional[int] = MISSING,
        flags: ApplicationFlags = MISSING,
        custom_install_url: Optional[str] = MISSING,
        install_params: Optional[ApplicationInstallParams] = MISSING,
        developers: Sequence[Snowflake] = MISSING,
        publishers: Sequence[Snowflake] = MISSING,
        guild: Snowflake = MISSING,
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
                payload['cover_image'] = utils._bytes_to_base64_data(cover_image)
            else:
                payload['cover_image'] = ''
        if tags is not MISSING:
            payload['tags'] = tags or []
        if terms_of_service_url is not MISSING:
            payload['terms_of_service_url'] = terms_of_service_url or ''
        if privacy_policy_url is not MISSING:
            payload['privacy_policy_url'] = privacy_policy_url or ''
        if deeplink_uri is not MISSING:
            payload['deeplink_uri'] = deeplink_uri or ''
        if interactions_endpoint_url is not MISSING:
            payload['interactions_endpoint_url'] = interactions_endpoint_url or ''
        if interactions_version is not MISSING:
            payload['interactions_version'] = interactions_version
        if interactions_event_types is not MISSING:
            payload['interactions_event_types'] = interactions_event_types or []
        if role_connections_verification_url is not MISSING:
            payload['role_connections_verification_url'] = role_connections_verification_url or ''
        if redirect_uris is not MISSING:
            payload['redirect_uris'] = redirect_uris or []
        if rpc_origins is not MISSING:
            payload['rpc_origins'] = rpc_origins or []
        if public is not MISSING:
            if self.bot:
                payload['bot_public'] = public
            else:
                payload['integration_public'] = public
        if require_code_grant is not MISSING:
            if self.bot:
                payload['bot_require_code_grant'] = require_code_grant
            else:
                payload['integration_require_code_grant'] = require_code_grant
        if discoverable is not MISSING:
            payload['discoverability_state'] = (
                ApplicationDiscoverabilityState.discoverable.value
                if discoverable
                else ApplicationDiscoverabilityState.not_discoverable.value
            )
        if max_participants is not MISSING:
            payload['max_participants'] = max_participants
        if flags is not MISSING:
            payload['flags'] = flags.value
        if custom_install_url is not MISSING:
            payload['custom_install_url'] = custom_install_url or ''
        if install_params is not MISSING:
            payload['install_params'] = install_params.to_dict() if install_params else None
        if developers is not MISSING:
            payload['developer_ids'] = [developer.id for developer in developers or []]
        if publishers is not MISSING:
            payload['publisher_ids'] = [publisher.id for publisher in publishers or []]
        if guild:
            payload['guild_id'] = guild.id
        if team:
            await self.state.http.transfer_application(self.id, team.id)
        data = await self.state.http.edit_application(self.id, payload)
        self._update(data)
    async def fetch_bot(self) -> ApplicationBot:
        data = await self.state.http.edit_bot(self.id, {})
        if not self.bot:
            self.bot = ApplicationBot(data=data, state=self.state, application=self)
        else:
            self.bot._update(data)
        return self.bot
    async def create_bot(self) -> Optional[str]:
        state = self.state
        data = await state.http.botify_app(self.id)
        return data.get('token')
    async def edit_bot(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[bytes] = MISSING,
        bio: Optional[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
    ) -> ApplicationBot:
        payload = {}
        if username is not MISSING:
            payload['username'] = username
        if avatar is not MISSING:
            if avatar is not None:
                payload['avatar'] = _bytes_to_base64_data(avatar)
            else:
                payload['avatar'] = None
        if payload or not self.bot:
            data = await self.state.http.edit_bot(self.id, payload)
            if not self.bot:
                self.bot = ApplicationBot(data=data, state=self.state, application=self)
            else:
                self.bot._update(data)
            payload = {}
        if public is not MISSING:
            payload['bot_public'] = public
        if require_code_grant is not MISSING:
            payload['bot_require_code_grant'] = require_code_grant
        if bio is not MISSING:
            payload['description'] = bio
        if payload:
            data = await self.state.http.edit_application(self.id, payload)
            self._update(data)
        return self.bot
    async def whitelisted(self) -> List[ApplicationTester]:
        state = self.state
        data = await state.http.get_app_whitelisted(self.id)
        return [ApplicationTester(self, state, user) for user in data]
    @overload
    async def whitelist(self, user: _UserTag, /) -> ApplicationTester:
        ...
    @overload
    async def whitelist(self, user: str, /) -> ApplicationTester:
        ...
    @overload
    async def whitelist(self, username: str, discriminator: str, /) -> ApplicationTester:
        ...
    async def whitelist(self, *args: Union[_UserTag, str]) -> ApplicationTester:
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, _UserTag):
                user = str(user)
            username, _, discrim = user.partition('
        elif len(args) == 2:
            username, discrim = args
        else:
            raise TypeError(f'whitelist() takes 1 or 2 arguments but {len(args)} were given')
        state = self.state
        data = await state.http.add_app_whitelist(self.id, username, discrim or 0)
        return ApplicationTester(self, state, data)
    async def create_asset(
        self, name: str, image: bytes, *, type: ApplicationAssetType = ApplicationAssetType.one
    ) -> ApplicationAsset:
        data = await self.state.http.create_asset(self.id, name, int(type), utils._bytes_to_base64_data(image))
        return ApplicationAsset(data=data, application=self)
    async def store_assets(self) -> List[StoreAsset]:
        state = self.state
        data = await self.state.http.get_store_assets(self.id)
        return [StoreAsset(data=asset, state=state, parent=self) for asset in data]
    async def create_store_asset(self, file: File, /) -> StoreAsset:
        state = self.state
        data = await state.http.create_store_asset(self.id, file)
        return StoreAsset(state=state, data=data, parent=self)
    async def skus(self, *, with_bundled_skus: bool = True, localize: bool = True) -> List[SKU]:
        state = self.state
        data = await self.state.http.get_app_skus(
            self.id, country_code=state.country_code or 'US', with_bundled_skus=with_bundled_skus, localize=localize
        )
        return [SKU(data=sku, state=state, application=self) for sku in data]
    async def primary_sku(self, *, localize: bool = True) -> Optional[SKU]:
        if not self.primary_sku_id:
            return None
        state = self.state
        data = await self.state.http.get_sku(
            self.primary_sku_id, country_code=state.country_code or 'US', localize=localize
        )
        return SKU(data=data, state=state, application=self)
    async def store_listing_sku(self, *, localize: bool = True) -> Optional[SKU]:
        if not self.store_listing_sku_id:
            return None
        state = self.state
        data = await self.state.http.get_sku(
            self.store_listing_sku_id, country_code=state.country_code or 'US', localize=localize
        )
        return SKU(data=data, state=state, application=self)
    async def create_sku(
        self,
        *,
        name: str,
        name_localizations: Optional[Mapping[Locale, str]] = None,
        legal_notice: Optional[str] = None,
        legal_notice_localizations: Optional[Mapping[Locale, str]] = None,
        type: SKUType,
        price_tier: Optional[int] = None,
        price_overrides: Optional[Mapping[str, int]] = None,
        sale_price_tier: Optional[int] = None,
        sale_price_overrides: Optional[Mapping[str, int]] = None,
        dependent_sku: Optional[Snowflake] = None,
        access_level: Optional[SKUAccessLevel] = None,
        features: Optional[Collection[SKUFeature]] = None,
        locales: Optional[Collection[Locale]] = None,
        genres: Optional[Collection[SKUGenre]] = None,
        content_ratings: Optional[Collection[ContentRating]] = None,
        system_requirements: Optional[Collection[SystemRequirements]] = None,
        release_date: Optional[date] = None,
        bundled_skus: Optional[Sequence[Snowflake]] = None,
        manifest_labels: Optional[Sequence[Snowflake]] = None,
    ):
        payload = {
            'type': int(type),
            'name': {'default': name, 'localizations': {str(k): v for k, v in (name_localizations or {}).items()}},
            'application_id': self.id,
        }
        if legal_notice or legal_notice_localizations:
            payload['legal_notice'] = {
                'default': legal_notice,
                'localizations': {str(k): v for k, v in (legal_notice_localizations or {}).items()},
            }
        if price_tier is not None:
            payload['price_tier'] = price_tier
        if price_overrides:
            payload['price'] = {str(k): v for k, v in price_overrides.items()}
        if sale_price_tier is not None:
            payload['sale_price_tier'] = sale_price_tier
        if sale_price_overrides:
            payload['sale_price'] = {str(k): v for k, v in sale_price_overrides.items()}
        if dependent_sku is not None:
            payload['dependent_sku_id'] = dependent_sku.id
        if access_level is not None:
            payload['access_level'] = int(access_level)
        if locales:
            payload['locales'] = [str(l) for l in locales]
        if features:
            payload['features'] = [int(f) for f in features]
        if genres:
            payload['genres'] = [int(g) for g in genres]
        if content_ratings:
            payload['content_ratings'] = {
                content_rating.agency: content_rating.to_dict() for content_rating in content_ratings
            }
        if system_requirements:
            payload['system_requirements'] = {
                system_requirement.os: system_requirement.to_dict() for system_requirement in system_requirements
            }
        if release_date is not None:
            payload['release_date'] = release_date.isoformat()
        if bundled_skus:
            payload['bundled_skus'] = [s.id for s in bundled_skus]
        if manifest_labels:
            payload['manifest_labels'] = [m.id for m in manifest_labels]
        state = self.state
        data = await state.http.create_sku(payload)
        return SKU(data=data, state=state, application=self)
    async def fetch_achievement(self, achievement_id: int) -> Achievement:
        data = await self.state.http.get_achievement(self.id, achievement_id)
        return Achievement(data=data, state=self.state)
    async def create_achievement(
        self,
        *,
        name: str,
        name_localizations: Optional[Mapping[Locale, str]] = None,
        description: str,
        description_localizations: Optional[Mapping[Locale, str]] = None,
        icon: bytes,
        secure: bool = False,
        secret: bool = False,
    ) -> Achievement:
        state = self.state
        data = await state.http.create_achievement(
            self.id,
            name=name,
            name_localizations={str(k): v for k, v in name_localizations.items()} if name_localizations else None,
            description=description,
            description_localizations={str(k): v for k, v in description_localizations.items()}
            if description_localizations
            else None,
            icon=_bytes_to_base64_data(icon),
            secure=secure,
            secret=secret,
        )
        return Achievement(state=state, data=data)
    async def entitlements(
        self,
        *,
        user: Optional[Snowflake] = None,
        guild: Optional[Snowflake] = None,
        skus: Optional[List[Snowflake]] = None,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        oldest_first: bool = MISSING,
        with_payments: bool = False,
        exclude_ended: bool = False,
    ) -> AsyncIterator[Entitlement]:
        state = self.state
        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await state.http.get_app_entitlements(
                self.id,
                limit=retrieve,
                after=after_id,
                user_id=user.id if user else None,
                guild_id=guild.id if guild else None,
                sku_ids=[sku.id for sku in skus] if skus else None,
                with_payments=with_payments,
                exclude_ended=exclude_ended,
            )
            if data:
                if limit is not None:
                    limit -= len(data)
                after = Object(id=int(data[0]['id']))
            return data, after, limit
        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await state.http.get_app_entitlements(
                self.id,
                limit=retrieve,
                before=before_id,
                user_id=user.id if user else None,
                guild_id=guild.id if guild else None,
                sku_ids=[sku.id for sku in skus] if skus else None,
                with_payments=with_payments,
                exclude_ended=exclude_ended,
            )
            if data:
                if limit is not None:
                    limit -= len(data)
                before = Object(id=int(data[-1]['id']))
            return data, before, limit
        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))
        if oldest_first in (MISSING, None):
            reverse = after is not None
        else:
            reverse = oldest_first
        after = after or OLDEST_OBJECT
        predicate = None
        if reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda m: int(m['id']) < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda m: int(m['id']) > after.id
        while True:
            retrieve = min(100 if limit is None else limit, 100)
            if retrieve < 1:
                return
            data, state, limit = await strategy(retrieve, state, limit)
            if len(data) < 100:
                limit = 0
            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)
            for entitlement in data:
                yield Entitlement(data=entitlement, state=state)
    async def fetch_entitlement(self, entitlement_id: int, /) -> Entitlement:
        state = self.state
        data = await state.http.get_app_entitlement(self.id, entitlement_id)
        return Entitlement(data=data, state=state)
    async def gift_batches(self) -> List[GiftBatch]:
        state = self.state
        app_id = self.id
        data = await state.http.get_gift_batches(app_id)
        return [GiftBatch(data=batch, state=state, application_id=app_id) for batch in data]
    async def create_gift_batch(
        self,
        sku: Snowflake,
        *,
        amount: int,
        description: str,
        entitlement_branches: Optional[List[Snowflake]] = None,
        entitlement_starts_at: Optional[date] = None,
        entitlement_ends_at: Optional[date] = None,
    ) -> GiftBatch:
        state = self.state
        app_id = self.id
        data = await state.http.create_gift_batch(
            app_id,
            sku.id,
            amount,
            description,
            entitlement_branches=[branch.id for branch in entitlement_branches] if entitlement_branches else None,
            entitlement_starts_at=entitlement_starts_at.isoformat() if entitlement_starts_at else None,
            entitlement_ends_at=entitlement_ends_at.isoformat() if entitlement_ends_at else None,
        )
        return GiftBatch(data=data, state=state, application_id=app_id)
    async def branches(self) -> List[ApplicationBranch]:
        state = self.state
        app_id = self.id
        data = await state.http.get_app_branches(app_id)
        return [ApplicationBranch(data=branch, state=state, application_id=app_id) for branch in data]
    async def create_branch(self, name: str) -> ApplicationBranch:
        state = self.state
        app_id = self.id
        data = await state.http.create_app_branch(app_id, name)
        return ApplicationBranch(data=data, state=state, application_id=app_id)
    async def manifest_labels(self) -> List[ManifestLabel]:
        state = self.state
        app_id = self.id
        data = await state.http.get_app_manifest_labels(app_id)
        return [ManifestLabel(data=label, application_id=app_id) for label in data]
    async def fetch_discoverability(self) -> Tuple[ApplicationDiscoverabilityState, ApplicationDiscoveryFlags]:
        data = await self.state.http.get_app_discoverability(self.id)
        return try_enum(
            ApplicationDiscoverabilityState, data['discoverability_state']
        ), ApplicationDiscoveryFlags._from_value(data['discovery_eligibility_flags'])
    async def fetch_embedded_activity_config(self) -> EmbeddedActivityConfig:
        data = await self.state.http.get_embedded_activity_config(self.id)
        return EmbeddedActivityConfig(data=data, application=self)
    async def edit_embedded_activity_config(
        self,
        *,
        supported_platforms: Collection[EmbeddedActivityPlatform] = MISSING,
        platform_configs: Collection[EmbeddedActivityPlatformConfig] = MISSING,
        orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        tablet_orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        requires_age_gate: bool = MISSING,
        shelf_rank: int = MISSING,
        free_period_starts_at: Optional[datetime] = MISSING,
        free_period_ends_at: Optional[datetime] = MISSING,
        preview_video_asset: Optional[Snowflake] = MISSING,
    ) -> EmbeddedActivityConfig:
        data = await self.state.http.edit_embedded_activity_config(
            self.id,
            supported_platforms=[str(x) for x in (supported_platforms)] if supported_platforms is not MISSING else None,
            platform_config={c.platform.value: c.to_dict() for c in (platform_configs)}
            if platform_configs is not MISSING
            else None,
            orientation_lock_state=int(orientation_lock_state) if orientation_lock_state is not MISSING else None,
            tablet_orientation_lock_state=int(tablet_orientation_lock_state)
            if tablet_orientation_lock_state is not MISSING
            else None,
            requires_age_gate=requires_age_gate if requires_age_gate is not MISSING else None,
            shelf_rank=shelf_rank if shelf_rank is not MISSING else None,
            free_period_starts_at=free_period_starts_at.isoformat() if free_period_starts_at else None,
            free_period_ends_at=free_period_ends_at.isoformat() if free_period_ends_at else None,
            preview_video_asset_id=(preview_video_asset.id if preview_video_asset else None)
            if preview_video_asset is not MISSING
            else MISSING,
        )
        if self.embedded_activity_config is not None:
            self.embedded_activity_config._update(data)
        else:
            self.embedded_activity_config = EmbeddedActivityConfig(data=data, application=self)
        return self.embedded_activity_config
    async def secret(self) -> str:
        data = await self.state.http.reset_secret(self.id)
        return data['secret']
class IntegrationApplication(Hashable):
    __slots__ = (
        'state',
        'id',
        'name',
        'bot',
        'description',
        'deeplink_uri',
        'type',
        'primary_sku_id',
        'role_connections_verification_url',
        'third_party_skus',
        '_icon',
        '_cover_image',
        '_splash',
    )
    def __init__(self, *, state: ConnectionState, data: BaseApplicationPayload):
        self.state: ConnectionState = state
        self._update(data)
    def __str__(self) -> str:
        return self.name
    def _update(self, data: BaseApplicationPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data.get('description') or ''
        self.deeplink_uri: Optional[str] = data.get('deeplink_uri')
        self.type: Optional[ApplicationType] = try_enum(ApplicationType, data['type']) if 'type' in data else None
        self._icon: Optional[str] = data.get('icon')
        self._cover_image: Optional[str] = data.get('cover_image')
        self._splash: Optional[str] = data.get('splash')
        self.bot: Optional[User] = self.state.create_user(data['bot']) if 'bot' in data else None
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self.role_connections_verification_url: Optional[str] = data.get('role_connections_verification_url')
        self.third_party_skus: List[ThirdPartySKU] = [
            ThirdPartySKU(data=t, application=self) for t in data.get('third_party_skus', [])
        ]
    def __repr__(self) -> str:
        return f'<IntegrationApplication id={self.id} name={self.name!r}>'
    @property
    def created_at(self) -> datetime:
        return utils.snowflake_time(self.id)
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='app')
    @property
    def cover_image(self) -> Optional[Asset]:
        if self._cover_image is None:
            return None
        return Asset._from_icon(self.state, self.id, self._cover_image, path='app')
    @property
    def splash(self) -> Optional[Asset]:
        if self._splash is None:
            return None
        return Asset._from_icon(self.state, self.id, self._splash, path='app')
    @property
    def primary_sku_url(self) -> Optional[str]:
        if self.primary_sku_id:
            return f'https://discord.com/store/skus/{self.primary_sku_id}/unknown'
    async def assets(self) -> List[ApplicationAsset]:
        data = await self.state.http.get_app_assets(self.id)
        return [ApplicationAsset(data=d, application=self) for d in data]
    async def published_store_listings(self, *, localize: bool = True) -> List[StoreListing]:
        state = self.state
        data = await state.http.get_app_store_listings(self.id, country_code=state.country_code or 'US', localize=localize)
        return [StoreListing(state=state, data=d) for d in data]
    async def primary_store_listing(self, *, localize: bool = True) -> StoreListing:
        state = self.state
        data = await state.http.get_app_store_listing(self.id, country_code=state.country_code or 'US', localize=localize)
        return StoreListing(state=state, data=data)
    async def entitlements(self, *, exclude_consumed: bool = True) -> List[Entitlement]:
        state = self.state
        data = await state.http.get_user_app_entitlements(self.id, exclude_consumed=exclude_consumed)
        return [Entitlement(data=entitlement, state=state) for entitlement in data]
    async def ticket(self) -> str:
        state = self.state
        data = await state.http.get_app_ticket(self.id)
        return data['ticket']
    async def entitlement_ticket(self) -> str:
        state = self.state
        data = await state.http.get_app_entitlement_ticket(self.id)
        return data['ticket']
    async def activity_statistics(self) -> List[ApplicationActivityStatistics]:
        state = self.state
        app_id = self.id
        data = await state.http.get_app_activity_statistics(app_id)
        return [ApplicationActivityStatistics(data=activity, state=state, application_id=app_id) for activity in data]
class UnverifiedApplication:
    __slots__ = ('name', 'hash', 'missing_data')
    def __init__(self, *, data: UnverifiedApplicationPayload):
        self.name: str = data['name']
        self.hash: str = data['hash']
        self.missing_data: List[str] = data.get('missing_data', [])
    def __repr__(self) -> str:
        return f'<UnverifiedApplication name={self.name!r} hash={self.hash!r}>'
    def __hash__(self) -> int:
        return hash(self.hash)
    def __str__(self) -> str:
        return self.name
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, UnverifiedApplication):
            return self.hash == other.hash
        return NotImplemented
    def __ne__(self, other: Any) -> bool:
        if isinstance(other, UnverifiedApplication):
            return self.hash != other.hash
        return NotImplemented