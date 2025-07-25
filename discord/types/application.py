from __future__ import annotations
from typing import Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired
from .command import ApplicationCommand
from .guild import PartialGuild
from .snowflake import Snowflake
from .team import Team
from .user import APIUser, PartialUser
class Token(TypedDict):
    token: str
class OptionalToken(TypedDict):
    token: Optional[str]
class Secret(TypedDict):
    secret: str
class _BaseApplication(TypedDict):
    id: Snowflake
    name: str
    description: str
    icon: Optional[str]
    cover_image: NotRequired[str]
    splash: NotRequired[str]
    type: Optional[int]
    primary_sku_id: NotRequired[Snowflake]
    summary: NotRequired[Literal['']]
    deeplink_uri: NotRequired[str]
    third_party_skus: NotRequired[List[ThirdPartySKU]]
class BaseApplication(_BaseApplication):
    bot: NotRequired[PartialUser]
class IntegrationApplication(BaseApplication):
    role_connections_verification_url: NotRequired[Optional[str]]
class PartialApplication(_BaseApplication):
    owner: NotRequired[APIUser]
    team: NotRequired[Team]
    verify_key: str
    flags: NotRequired[int]
    rpc_origins: NotRequired[List[str]]
    hook: NotRequired[bool]
    overlay: NotRequired[bool]
    overlay_warn: NotRequired[bool]
    overlay_compatibility_hook: NotRequired[bool]
    terms_of_service_url: NotRequired[str]
    privacy_policy_url: NotRequired[str]
    max_participants: NotRequired[Optional[int]]
    bot_public: NotRequired[bool]
    bot_require_code_grant: NotRequired[bool]
    integration_public: NotRequired[bool]
    integration_require_code_grant: NotRequired[bool]
    guild_id: NotRequired[Snowflake]
    primary_sku_id: NotRequired[Snowflake]
    slug: NotRequired[str]
    developers: NotRequired[List[Company]]
    publishers: NotRequired[List[Company]]
    aliases: NotRequired[List[str]]
    eula_id: NotRequired[Snowflake]
    embedded_activity_config: NotRequired[EmbeddedActivityConfig]
    guild: NotRequired[PartialGuild]
    install_params: NotRequired[ApplicationInstallParams]
    store_listing_sku_id: NotRequired[Snowflake]
    executables: NotRequired[List[ApplicationExecutable]]
class ApplicationDiscoverability(TypedDict):
    discoverability_state: int
    discovery_eligibility_flags: int
    bad_commands: List[ApplicationCommand]
InteractionsVersion = Literal[1, 2]
class Application(PartialApplication, IntegrationApplication):
    bot_disabled: NotRequired[bool]
    bot_quarantined: NotRequired[bool]
    redirect_uris: List[str]
    interactions_endpoint_url: Optional[str]
    interactions_version: InteractionsVersion
    interactions_event_types: List[str]
    verification_state: int
    store_application_state: int
    rpc_application_state: int
    creator_monetization_state: int
    discoverability_state: int
    discovery_eligibility_flags: int
    monetization_state: int
    monetization_eligibility_flags: int
    approximate_guild_count: NotRequired[int]
class WhitelistedUser(TypedDict):
    user: PartialUser
    state: Literal[1, 2]
class Asset(TypedDict):
    id: Snowflake
    name: str
    type: int
class StoreAsset(TypedDict):
    id: Snowflake
    size: int
    width: int
    height: int
    mime_type: str
class Company(TypedDict):
    id: Snowflake
    name: str
class EULA(TypedDict):
    id: Snowflake
    name: str
    content: str
class ApplicationExecutable(TypedDict):
    name: str
    os: Literal['win32', 'linux', 'darwin']
    is_launcher: bool
class ThirdPartySKU(TypedDict):
    distributor: Literal['discord', 'steam', 'twitch', 'uplay', 'battlenet', 'origin', 'gog', 'epic', 'google_play']
    id: Optional[str]
    sku_id: Optional[str]
class BaseAchievement(TypedDict):
    id: Snowflake
    name: Union[str, Dict[str, Union[str, Dict[str, str]]]]
    name_localizations: NotRequired[Dict[str, str]]
    description: Union[str, Dict[str, Union[str, Dict[str, str]]]]
    description_localizations: NotRequired[Dict[str, str]]
    icon_hash: str
    secure: bool
    secret: bool
class Achievement(BaseAchievement):
    application_id: Snowflake
class Ticket(TypedDict):
    ticket: str
class Branch(TypedDict):
    id: Snowflake
    live_build_id: NotRequired[Optional[Snowflake]]
    created_at: NotRequired[str]
    name: NotRequired[str]
class BranchSize(TypedDict):
    size_kb: str
class DownloadSignature(TypedDict):
    endpoint: str
    expires: int
    signature: str
class Build(TypedDict):
    application_id: NotRequired[Snowflake]
    created_at: NotRequired[str]
    id: Snowflake
    manifests: List[Manifest]
    status: Literal['CORRUPTED', 'INVALID', 'READY', 'VALIDATING', 'UPLOADED', 'UPLOADING', 'CREATED']
    source_build_id: NotRequired[Optional[Snowflake]]
    version: NotRequired[Optional[str]]
class CreatedBuild(TypedDict):
    build: Build
    manifest_uploads: List[Manifest]
class BuildFile(TypedDict):
    id: Snowflake
    md5_hash: NotRequired[str]
class CreatedBuildFile(TypedDict):
    id: str
    url: str
class ManifestLabel(TypedDict):
    application_id: Snowflake
    id: Snowflake
    name: NotRequired[str]
class Manifest(TypedDict):
    id: Snowflake
    label: ManifestLabel
    redistributable_label_ids: NotRequired[List[Snowflake]]
    url: Optional[str]
class ActivityStatistics(TypedDict):
    application_id: NotRequired[Snowflake]
    user_id: NotRequired[Snowflake]
    total_duration: int
    total_discord_sku_duration: NotRequired[int]
    last_played_at: str
class GlobalActivityStatistics(TypedDict):
    application_id: Snowflake
    user_id: Snowflake
    duration: int
    updated_at: str
EmbeddedActivityPlatform = Literal['web', 'android', 'ios']
EmbeddedActivityPlatformReleasePhase = Literal[
    'in_development', 'activities_team', 'employee_release', 'soft_launch', 'global_launch'
]
class EmbeddedActivityPlatformConfig(TypedDict):
    label_type: Literal[0, 1, 2]
    label_until: Optional[str]
    release_phase: EmbeddedActivityPlatformReleasePhase
class EmbeddedActivityConfig(TypedDict):
    application_id: NotRequired[Snowflake]
    activity_preview_video_asset_id: NotRequired[Optional[Snowflake]]
    client_platform_config: Dict[EmbeddedActivityPlatform, EmbeddedActivityPlatformConfig]
    default_orientation_lock_state: Literal[1, 2, 3]
    tablet_default_orientation_lock_state: Literal[1, 2, 3]
    free_period_ends_at: NotRequired[Optional[str]]
    free_period_starts_at: NotRequired[Optional[str]]
    premium_tier_requirement: NotRequired[Optional[Literal[1, 2, 3]]]
    requires_age_gate: bool
    shelf_rank: int
    supported_platforms: List[EmbeddedActivityPlatform]
class ApplicationInstallParams(TypedDict):
    scopes: List[str]
    permissions: int
class ActiveDeveloperWebhook(TypedDict):
    channel_id: Snowflake
    webhook_id: Snowflake
class ActiveDeveloperResponse(TypedDict):
    follower: ActiveDeveloperWebhook
class RoleConnectionMetadata(TypedDict):
    type: Literal[1, 2, 3, 4, 5, 6, 7, 8]
    key: str
    name: str
    description: str
    name_localizations: NotRequired[Dict[str, str]]
    description_localizations: NotRequired[Dict[str, str]]
class PartialRoleConnection(TypedDict):
    platform_name: Optional[str]
    platform_username: Optional[str]
    metadata: Dict[str, str]
class RoleConnection(PartialRoleConnection):
    application: BaseApplication
    application_metadata: List[RoleConnectionMetadata]
class UnverifiedApplication(TypedDict):
    name: str
    hash: str
    missing_data: List[str]