from __future__ import annotations
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Collection, Dict, List, Mapping, Optional, Sequence, Tuple, Union
from .asset import Asset, AssetMixin
from .enums import (
    ContentRatingAgency,
    ESRBContentDescriptor,
    ESRBRating,
    GiftStyle,
    Locale,
    OperatingSystem,
    PEGIContentDescriptor,
    PEGIRating,
    PremiumType,
    SKUAccessLevel,
    SKUFeature,
    SKUGenre,
    SKUProductLine,
    SKUType,
    SubscriptionInterval,
    SubscriptionPlanPurchaseType,
    try_enum,
)
from .flags import SKUFlags
from .mixins import Hashable
from .utils import (
    MISSING,
    _get_as_snowflake,
    _get_extension_for_mime_type,
    _parse_localizations,
    get,
    parse_date,
    parse_time,
    utcnow,
)
if TYPE_CHECKING:
    from datetime import date
    from typing_extensions import Self
    from .abc import Snowflake
    from .application import Application, PartialApplication
    from .entitlements import Entitlement, Gift, GiftBatch
    from .guild import Guild
    from .library import LibraryApplication
    from .state import ConnectionState
    from .types.application import StoreAsset as StoreAssetPayload
    from .types.entitlements import Gift as GiftPayload
    from .types.snowflake import Snowflake as SnowflakeType
    from .types.store import (
        SKU as SKUPayload,
        CarouselItem as CarouselItemPayload,
        ContentRating as ContentRatingPayload,
        PremiumPrice as PremiumPricePayload,
        SKUPrice as SKUPricePayload,
        StoreListing as StoreListingPayload,
        StoreNote as StoreNotePayload,
        SystemRequirements as SystemRequirementsPayload,
    )
    from .types.subscriptions import (
        PartialSubscriptionPlan as PartialSubscriptionPlanPayload,
        SubscriptionPlan as SubscriptionPlanPayload,
        SubscriptionPrice as SubscriptionPricePayload,
        SubscriptionPrices as SubscriptionPricesPayload,
    )
    from .user import User
__all__ = (
    'StoreAsset',
    'StoreNote',
    'SystemRequirements',
    'StoreListing',
    'SKUPrice',
    'ContentRating',
    'SKU',
    'SubscriptionPlanPrices',
    'SubscriptionPlan',
)
THE_GAME_AWARDS_WINNERS = (500428425362931713, 451550535720501248, 471376328319303681, 466696214818193408)
class StoreAsset(AssetMixin, Hashable):
    __slots__ = ('state', 'parent', 'id', 'size', 'height', 'width', 'mime_type')
    def __init__(self, *, data: StoreAssetPayload, state: ConnectionState, parent: Union[StoreListing, Application]) -> None:
        self.state: ConnectionState = state
        self.parent = parent
        self.size: int = data['size']
        self.height: int = data['height']
        self.width: int = data['width']
        self.mime_type: str = data['mime_type']
        self.id: SnowflakeType
        try:
            self.id = int(data['id'])
        except ValueError:
            self.id = data['id']
    @classmethod
    def _from_id(
        cls, *, id: SnowflakeType, mime_type: str = '', state: ConnectionState, parent: Union[StoreListing, Application]
    ) -> StoreAsset:
        data: StoreAssetPayload = {'id': id, 'size': 0, 'height': 0, 'width': 0, 'mime_type': mime_type}
        return cls(data=data, state=state, parent=parent)
    @classmethod
    def _from_carousel_item(
        cls, *, data: CarouselItemPayload, state: ConnectionState, store_listing: StoreListing
    ) -> StoreAsset:
        asset_id = _get_as_snowflake(data, 'asset_id')
        if asset_id:
            return get(store_listing.assets, id=asset_id) or StoreAsset._from_id(
                id=asset_id, state=state, parent=store_listing
            )
        else:
            return cls._from_id(id=data['youtube_video_id'], mime_type='video/youtube', state=state, parent=store_listing)
    def __repr__(self) -> str:
        return f'<ApplicationAsset id={self.id} height={self.height} width={self.width}>'
    @property
    def application_id(self) -> int:
        parent = self.parent
        return parent.sku.application_id if hasattr(parent, 'sku') else parent.id
    @property
    def animated(self) -> bool:
        return self.mime_type in {'video/youtube', 'image/gif', 'video/mp4'}
    @property
    def url(self) -> str:
        if self.is_youtube_video():
            return f'https://youtube.com/watch?v={self.id}'
        return (
            f'{Asset.BASE}/app-assets/{self.application_id}/store/{self.id}.{_get_extension_for_mime_type(self.mime_type)}'
        )
    def is_youtube_video(self) -> bool:
        return self.mime_type == 'video/youtube'
    def to_carousel_item(self) -> dict:
        if self.is_youtube_video():
            return {'youtube_video_id': self.id}
        return {'asset_id': self.id}
    async def read(self) -> bytes:
        if self.is_youtube_video():
            raise ValueError('StoreAsset is not a real asset')
        return await super().read()
    async def delete(self) -> None:
        if self.is_youtube_video():
            raise ValueError('StoreAsset is not a real asset')
        await self.state.http.delete_store_asset(self.application_id, self.id)
class StoreNote:
    __slots__ = ('user', 'content')
    def __init__(self, *, data: StoreNotePayload, state: ConnectionState) -> None:
        self.user: Optional[User] = state.create_user(data['user']) if data.get('user') else None
        self.content: str = data['content']
    def __repr__(self) -> str:
        return f'<StoreNote user={self.user!r} content={self.content!r}>'
    def __str__(self) -> str:
        return self.content
class SystemRequirements:
    if TYPE_CHECKING:
        os: OperatingSystem
        minimum_ram: Optional[int]
        recommended_ram: Optional[int]
        minimum_disk: Optional[int]
        recommended_disk: Optional[int]
        minimum_os_version: Optional[str]
        minimum_os_version_localizations: Dict[Locale, str]
        recommended_os_version: Optional[str]
        recommended_os_version_localizations: Dict[Locale, str]
        minimum_cpu: Optional[str]
        minimum_cpu_localizations: Dict[Locale, str]
        recommended_cpu: Optional[str]
        recommended_cpu_localizations: Dict[Locale, str]
        minimum_gpu: Optional[str]
        minimum_gpu_localizations: Dict[Locale, str]
        recommended_gpu: Optional[str]
        recommended_gpu_localizations: Dict[Locale, str]
        minimum_sound_card: Optional[str]
        minimum_sound_card_localizations: Dict[Locale, str]
        recommended_sound_card: Optional[str]
        recommended_sound_card_localizations: Dict[Locale, str]
        minimum_directx: Optional[str]
        minimum_directx_localizations: Dict[Locale, str]
        recommended_directx: Optional[str]
        recommended_directx_localizations: Dict[Locale, str]
        minimum_network: Optional[str]
        minimum_network_localizations: Dict[Locale, str]
        recommended_network: Optional[str]
        recommended_network_localizations: Dict[Locale, str]
        minimum_notes: Optional[str]
        minimum_notes_localizations: Dict[Locale, str]
        recommended_notes: Optional[str]
        recommended_notes_localizations: Dict[Locale, str]
    __slots__ = (
        'os',
        'minimum_ram',
        'recommended_ram',
        'minimum_disk',
        'recommended_disk',
        'minimum_os_version',
        'minimum_os_version_localizations',
        'recommended_os_version',
        'recommended_os_version_localizations',
        'minimum_cpu',
        'minimum_cpu_localizations',
        'recommended_cpu',
        'recommended_cpu_localizations',
        'minimum_gpu',
        'minimum_gpu_localizations',
        'recommended_gpu',
        'recommended_gpu_localizations',
        'minimum_sound_card',
        'minimum_sound_card_localizations',
        'recommended_sound_card',
        'recommended_sound_card_localizations',
        'minimum_directx',
        'minimum_directx_localizations',
        'recommended_directx',
        'recommended_directx_localizations',
        'minimum_network',
        'minimum_network_localizations',
        'recommended_network',
        'recommended_network_localizations',
        'minimum_notes',
        'minimum_notes_localizations',
        'recommended_notes',
        'recommended_notes_localizations',
    )
    def __init__(
        self,
        os: OperatingSystem,
        *,
        minimum_ram: Optional[int] = None,
        recommended_ram: Optional[int] = None,
        minimum_disk: Optional[int] = None,
        recommended_disk: Optional[int] = None,
        minimum_os_version: Optional[str] = None,
        minimum_os_version_localizations: Optional[Dict[Locale, str]] = None,
        recommended_os_version: Optional[str] = None,
        recommended_os_version_localizations: Optional[Dict[Locale, str]] = None,
        minimum_cpu: Optional[str] = None,
        minimum_cpu_localizations: Optional[Dict[Locale, str]] = None,
        recommended_cpu: Optional[str] = None,
        recommended_cpu_localizations: Optional[Dict[Locale, str]] = None,
        minimum_gpu: Optional[str] = None,
        minimum_gpu_localizations: Optional[Dict[Locale, str]] = None,
        recommended_gpu: Optional[str] = None,
        recommended_gpu_localizations: Optional[Dict[Locale, str]] = None,
        minimum_sound_card: Optional[str] = None,
        minimum_sound_card_localizations: Optional[Dict[Locale, str]] = None,
        recommended_sound_card: Optional[str] = None,
        recommended_sound_card_localizations: Optional[Dict[Locale, str]] = None,
        minimum_directx: Optional[str] = None,
        minimum_directx_localizations: Optional[Dict[Locale, str]] = None,
        recommended_directx: Optional[str] = None,
        recommended_directx_localizations: Optional[Dict[Locale, str]] = None,
        minimum_network: Optional[str] = None,
        minimum_network_localizations: Optional[Dict[Locale, str]] = None,
        recommended_network: Optional[str] = None,
        recommended_network_localizations: Optional[Dict[Locale, str]] = None,
        minimum_notes: Optional[str] = None,
        minimum_notes_localizations: Optional[Dict[Locale, str]] = None,
        recommended_notes: Optional[str] = None,
        recommended_notes_localizations: Optional[Dict[Locale, str]] = None,
    ) -> None:
        self.os = os
        self.minimum_ram = minimum_ram
        self.recommended_ram = recommended_ram
        self.minimum_disk = minimum_disk
        self.recommended_disk = recommended_disk
        self.minimum_os_version = minimum_os_version
        self.minimum_os_version_localizations = minimum_os_version_localizations or {}
        self.recommended_os_version = recommended_os_version
        self.recommended_os_version_localizations = recommended_os_version_localizations or {}
        self.minimum_cpu = minimum_cpu
        self.minimum_cpu_localizations = minimum_cpu_localizations or {}
        self.recommended_cpu = recommended_cpu
        self.recommended_cpu_localizations = recommended_cpu_localizations or {}
        self.minimum_gpu = minimum_gpu
        self.minimum_gpu_localizations = minimum_gpu_localizations or {}
        self.recommended_gpu = recommended_gpu
        self.recommended_gpu_localizations = recommended_gpu_localizations or {}
        self.minimum_sound_card = minimum_sound_card
        self.minimum_sound_card_localizations = minimum_sound_card_localizations or {}
        self.recommended_sound_card = recommended_sound_card
        self.recommended_sound_card_localizations = recommended_sound_card_localizations or {}
        self.minimum_directx = minimum_directx
        self.minimum_directx_localizations = minimum_directx_localizations or {}
        self.recommended_directx = recommended_directx
        self.recommended_directx_localizations = recommended_directx_localizations or {}
        self.minimum_network = minimum_network
        self.minimum_network_localizations = minimum_network_localizations or {}
        self.recommended_network = recommended_network
        self.recommended_network_localizations = recommended_network_localizations or {}
        self.minimum_notes = minimum_notes
        self.minimum_notes_localizations = minimum_notes_localizations or {}
        self.recommended_notes = recommended_notes
        self.recommended_notes_localizations = recommended_notes_localizations or {}
    @classmethod
    def from_dict(cls, os: OperatingSystem, data: SystemRequirementsPayload) -> Self:
        minimum = data.get('minimum', {})
        recommended = data.get('recommended', {})
        minimum_os_version, minimum_os_version_localizations = _parse_localizations(minimum, 'operating_system_version')
        recommended_os_version, recommended_os_version_localizations = _parse_localizations(
            recommended, 'operating_system_version'
        )
        minimum_cpu, minimum_cpu_localizations = _parse_localizations(minimum, 'cpu')
        recommended_cpu, recommended_cpu_localizations = _parse_localizations(recommended, 'cpu')
        minimum_gpu, minimum_gpu_localizations = _parse_localizations(minimum, 'gpu')
        recommended_gpu, recommended_gpu_localizations = _parse_localizations(recommended, 'gpu')
        minimum_sound_card, minimum_sound_card_localizations = _parse_localizations(minimum, 'sound_card')
        recommended_sound_card, recommended_sound_card_localizations = _parse_localizations(recommended, 'sound_card')
        minimum_directx, minimum_directx_localizations = _parse_localizations(minimum, 'directx')
        recommended_directx, recommended_directx_localizations = _parse_localizations(recommended, 'directx')
        minimum_network, minimum_network_localizations = _parse_localizations(minimum, 'network')
        recommended_network, recommended_network_localizations = _parse_localizations(recommended, 'network')
        minimum_notes, minimum_notes_localizations = _parse_localizations(minimum, 'notes')
        recommended_notes, recommended_notes_localizations = _parse_localizations(recommended, 'notes')
        return cls(
            os,
            minimum_ram=minimum.get('ram'),
            recommended_ram=recommended.get('ram'),
            minimum_disk=minimum.get('disk'),
            recommended_disk=recommended.get('disk'),
            minimum_os_version=minimum_os_version,
            minimum_os_version_localizations=minimum_os_version_localizations,
            recommended_os_version=recommended_os_version,
            recommended_os_version_localizations=recommended_os_version_localizations,
            minimum_cpu=minimum_cpu,
            minimum_cpu_localizations=minimum_cpu_localizations,
            recommended_cpu=recommended_cpu,
            recommended_cpu_localizations=recommended_cpu_localizations,
            minimum_gpu=minimum_gpu,
            minimum_gpu_localizations=minimum_gpu_localizations,
            recommended_gpu=recommended_gpu,
            recommended_gpu_localizations=recommended_gpu_localizations,
            minimum_sound_card=minimum_sound_card,
            minimum_sound_card_localizations=minimum_sound_card_localizations,
            recommended_sound_card=recommended_sound_card,
            recommended_sound_card_localizations=recommended_sound_card_localizations,
            minimum_directx=minimum_directx,
            minimum_directx_localizations=minimum_directx_localizations,
            recommended_directx=recommended_directx,
            recommended_directx_localizations=recommended_directx_localizations,
            minimum_network=minimum_network,
            minimum_network_localizations=minimum_network_localizations,
            recommended_network=recommended_network,
            recommended_network_localizations=recommended_network_localizations,
            minimum_notes=minimum_notes,
            minimum_notes_localizations=minimum_notes_localizations,
            recommended_notes=recommended_notes,
            recommended_notes_localizations=recommended_notes_localizations,
        )
    def __repr__(self) -> str:
        return f'<SystemRequirements os={self.os!r}>'
    def to_dict(self) -> dict:
        minimum = {}
        recommended = {}
        for key in self.__slots__:
            if key.endswith('_localizations'):
                continue
            value = getattr(self, key)
            localizations = getattr(self, f'{key}_localizations', None)
            if value or localizations:
                data = (
                    value
                    if localizations is None
                    else {'default': value, 'localizations': {str(k): v for k, v in localizations.items()}}
                )
                if key.startswith('minimum_'):
                    minimum[key[8:]] = data
                elif key.startswith('recommended_'):
                    recommended[key[12:]] = data
        return {'minimum': minimum, 'recommended': recommended}
class StoreListing(Hashable):
    __slots__ = (
        'state',
        'id',
        'summary',
        'summary_localizations',
        'description',
        'description_localizations',
        'tagline',
        'tagline_localizations',
        'flavor',
        'sku',
        'child_skus',
        'alternative_skus',
        'entitlement_branch_id',
        'guild',
        'published',
        'published_at',
        'unpublished_at',
        'staff_note',
        'assets',
        'carousel_items',
        'preview_video',
        'header_background',
        'hero_background',
        'hero_video',
        'box_art',
        'thumbnail',
        'header_logo_light',
        'header_logo_dark',
    )
    if TYPE_CHECKING:
        summary: Optional[str]
        summary_localizations: Dict[Locale, str]
        description: Optional[str]
        description_localizations: Dict[Locale, str]
        tagline: Optional[str]
        tagline_localizations: Dict[Locale, str]
    def __init__(
        self, *, data: StoreListingPayload, state: ConnectionState, application: Optional[PartialApplication] = None
    ) -> None:
        self.state = state
        self._update(data, application=application)
    def __str__(self) -> str:
        return self.summary or ''
    def __repr__(self) -> str:
        return f'<StoreListing id={self.id} summary={self.summary!r} sku={self.sku!r}>'
    def _update(self, data: StoreListingPayload, application: Optional[PartialApplication] = None) -> None:
        state = self.state
        self.summary, self.summary_localizations = _parse_localizations(data, 'summary')
        self.description, self.description_localizations = _parse_localizations(data, 'description')
        self.tagline, self.tagline_localizations = _parse_localizations(data, 'tagline')
        self.id: int = int(data['id'])
        self.flavor: Optional[str] = data.get('flavor_text')
        self.sku: SKU = SKU(data=data['sku'], state=state, application=application)
        self.child_skus: List[SKU] = [SKU(data=sku, state=state) for sku in data.get('child_skus', [])]
        self.alternative_skus: List[SKU] = [SKU(data=sku, state=state) for sku in data.get('alternative_skus', [])]
        self.entitlement_branch_id: Optional[int] = _get_as_snowflake(data, 'entitlement_branch_id')
        self.guild: Optional[Guild] = state.create_guild(data['guild']) if 'guild' in data else None
        self.published: bool = data.get('published', True)
        self.published_at: Optional[datetime] = parse_time(data['published_at']) if 'published_at' in data else None
        self.unpublished_at: Optional[datetime] = parse_time(data['unpublished_at']) if 'unpublished_at' in data else None
        self.staff_note: Optional[StoreNote] = (
            StoreNote(data=data['staff_notes'], state=state) if 'staff_notes' in data else None
        )
        self.assets: List[StoreAsset] = [
            StoreAsset(data=asset, state=state, parent=self) for asset in data.get('assets', [])
        ]
        self.carousel_items: List[StoreAsset] = [
            StoreAsset._from_carousel_item(data=asset, state=state, store_listing=self)
            for asset in data.get('carousel_items', [])
        ]
        self.preview_video: Optional[StoreAsset] = (
            StoreAsset(data=data['preview_video'], state=state, parent=self) if 'preview_video' in data else None
        )
        self.header_background: Optional[StoreAsset] = (
            StoreAsset(data=data['header_background'], state=state, parent=self) if 'header_background' in data else None
        )
        self.hero_background: Optional[StoreAsset] = (
            StoreAsset(data=data['hero_background'], state=state, parent=self) if 'hero_background' in data else None
        )
        self.hero_video: Optional[StoreAsset] = (
            StoreAsset(data=data['hero_video'], state=state, parent=self) if 'hero_video' in data else None
        )
        self.box_art: Optional[StoreAsset] = (
            StoreAsset(data=data['box_art'], state=state, parent=self) if 'box_art' in data else None
        )
        self.thumbnail: Optional[StoreAsset] = (
            StoreAsset(data=data['thumbnail'], state=state, parent=self) if 'thumbnail' in data else None
        )
        self.header_logo_light: Optional[StoreAsset] = (
            StoreAsset(data=data['header_logo_light_theme'], state=state, parent=self)
            if 'header_logo_light_theme' in data
            else None
        )
        self.header_logo_dark: Optional[StoreAsset] = (
            StoreAsset(data=data['header_logo_dark_theme'], state=state, parent=self)
            if 'header_logo_dark_theme' in data
            else None
        )
    async def edit(
        self,
        *,
        summary: Optional[str] = MISSING,
        summary_localizations: Mapping[Locale, str] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Mapping[Locale, str] = MISSING,
        tagline: Optional[str] = MISSING,
        tagline_localizations: Mapping[Locale, str] = MISSING,
        child_skus: Sequence[Snowflake] = MISSING,
        guild: Optional[Snowflake] = MISSING,
        published: bool = MISSING,
        carousel_items: Sequence[Union[StoreAsset, str]] = MISSING,
        preview_video: Optional[Snowflake] = MISSING,
        header_background: Optional[Snowflake] = MISSING,
        hero_background: Optional[Snowflake] = MISSING,
        hero_video: Optional[Snowflake] = MISSING,
        box_art: Optional[Snowflake] = MISSING,
        thumbnail: Optional[Snowflake] = MISSING,
        header_logo_light: Optional[Snowflake] = MISSING,
        header_logo_dark: Optional[Snowflake] = MISSING,
    ):
        payload = {}
        if summary is not MISSING or summary_localizations is not MISSING:
            localizations = (
                (summary_localizations or {}) if summary_localizations is not MISSING else self.summary_localizations
            )
            payload['name'] = {
                'default': (summary if summary is not MISSING else self.summary) or '',
                'localizations': {str(k): v for k, v in localizations.items()},
            }
        if description is not MISSING or description_localizations is not MISSING:
            localizations = (
                (description_localizations or {})
                if description_localizations is not MISSING
                else self.description_localizations
            )
            payload['description'] = {
                'default': (description if description is not MISSING else self.description) or '',
                'localizations': {str(k): v for k, v in localizations.items()},
            }
        if tagline is not MISSING or tagline_localizations is not MISSING:
            localizations = (
                (tagline_localizations or {}) if tagline_localizations is not MISSING else self.tagline_localizations
            )
            payload['tagline'] = {
                'default': (tagline if tagline is not MISSING else self.tagline) or '',
                'localizations': {str(k): v for k, v in localizations.items()},
            }
        if child_skus is not MISSING:
            payload['child_sku_ids'] = [sku.id for sku in child_skus] if child_skus else []
        if guild is not MISSING:
            payload['guild_id'] = guild.id if guild else None
        if published is not MISSING:
            payload['published'] = published
        if carousel_items is not MISSING:
            payload['carousel_items'] = (
                [
                    item.to_carousel_item() if isinstance(item, StoreAsset) else {'youtube_video_id': item}
                    for item in carousel_items
                ]
                if carousel_items
                else []
            )
        if preview_video is not MISSING:
            payload['preview_video_asset_id'] = preview_video.id if preview_video else None
        if header_background is not MISSING:
            payload['header_background_asset_id'] = header_background.id if header_background else None
        if hero_background is not MISSING:
            payload['hero_background_asset_id'] = hero_background.id if hero_background else None
        if hero_video is not MISSING:
            payload['hero_video_asset_id'] = hero_video.id if hero_video else None
        if box_art is not MISSING:
            payload['box_art_asset_id'] = box_art.id if box_art else None
        if thumbnail is not MISSING:
            payload['thumbnail_asset_id'] = thumbnail.id if thumbnail else None
        if header_logo_light is not MISSING:
            payload['header_logo_light_theme_asset_id'] = header_logo_light.id if header_logo_light else None
        if header_logo_dark is not MISSING:
            payload['header_logo_dark_theme_asset_id'] = header_logo_dark.id if header_logo_dark else None
        data = await self.state.http.edit_store_listing(self.id, payload)
        self._update(data, application=self.sku.application)
    @property
    def url(self) -> str:
        return self.sku.url
class SKUPrice:
    __slots__ = ('currency', 'amount', 'sale_amount', 'sale_percentage', 'exponent', 'premium')
    def __init__(self, data: Union[SKUPricePayload, SubscriptionPricePayload]) -> None:
        self.currency: str = data.get('currency', 'usd')
        self.amount: int = data.get('amount', 0)
        self.sale_amount: Optional[int] = data.get('sale_amount')
        self.sale_percentage: int = data.get('sale_percentage', 0)
        self.exponent: int = data.get('exponent', data.get('currency_exponent', 0))
        self.premium: Dict[PremiumType, SKUPrice] = {
            try_enum(PremiumType, premium_type): SKUPrice.from_premium(self, premium_data)
            for premium_type, premium_data in data.get('premium', {}).items()
        }
    @classmethod
    def from_private(cls, data: SKUPayload) -> SKUPrice:
        payload: SKUPricePayload = {
            'currency': 'usd',
            'currency_exponent': 2,
            'amount': data.get('price_tier') or 0,
            'sale_amount': data.get('sale_price_tier'),
        }
        if payload['sale_amount'] is not None:
            payload['sale_percentage'] = int((1 - (payload['sale_amount'] / payload['amount'])) * 100)
        return cls(payload)
    @classmethod
    def from_premium(cls, parent: SKUPrice, data: PremiumPricePayload) -> SKUPrice:
        payload: SKUPricePayload = {
            'currency': parent.currency,
            'currency_exponent': parent.exponent,
            'amount': parent.amount,
            'sale_amount': data.get('amount'),
            'sale_percentage': data.get('percentage'),
        }
        return cls(payload)
    def __repr__(self) -> str:
        return f'<SKUPrice amount={self.amount} currency={self.currency!r}>'
    def __bool__(self) -> bool:
        return self.amount > 0
    def __int__(self) -> int:
        return self.amount
    def is_discounted(self) -> bool:
        return self.sale_percentage > 0
    def is_free(self) -> bool:
        return self.sale_amount == 0 or self.amount == 0
    @property
    def discounts(self) -> int:
        return self.amount - (self.sale_amount or self.amount)
class ContentRating:
    _AGENCY_MAP = {
        ContentRatingAgency.esrb: (ESRBRating, ESRBContentDescriptor),
        ContentRatingAgency.pegi: (PEGIRating, PEGIContentDescriptor),
    }
    __slots__ = ('agency', 'rating', 'descriptors')
    def __init__(
        self,
        *,
        agency: ContentRatingAgency,
        rating: Union[ESRBRating, PEGIRating],
        descriptors: Union[Collection[ESRBContentDescriptor], Collection[PEGIContentDescriptor]],
    ) -> None:
        self.agency = agency
        ratingcls, descriptorcls = self._AGENCY_MAP[agency]
        self.rating: Union[ESRBRating, PEGIRating] = try_enum(ratingcls, int(rating))
        self.descriptors: Union[List[ESRBContentDescriptor], List[PEGIContentDescriptor]] = [
            try_enum(descriptorcls, int(descriptor)) for descriptor in descriptors
        ]
    @classmethod
    def from_dict(cls, data: ContentRatingPayload, agency: int) -> ContentRating:
        return cls(
            agency=try_enum(ContentRatingAgency, agency),
            rating=data.get('rating', 1),
            descriptors=data.get('descriptors', []),
        )
    @classmethod
    def from_dicts(cls, datas: Optional[dict]) -> List[ContentRating]:
        if not datas:
            return []
        return [cls.from_dict(data, int(agency)) for agency, data in datas.items()]
    def __repr__(self) -> str:
        return f'<ContentRating agency={self.agency!r} rating={self.rating}>'
    def to_dict(self) -> dict:
        return {'rating': int(self.rating), 'descriptors': [int(descriptor) for descriptor in self.descriptors]}
class SKU(Hashable):
    __slots__ = (
        'id',
        'name',
        'name_localizations',
        'summary',
        'summary_localizations',
        'legal_notice',
        'legal_notice_localizations',
        'type',
        'product_line',
        'slug',
        'price_tier',
        'price_overrides',
        'sale_price_tier',
        'sale_price_overrides',
        'price',
        'dependent_sku_id',
        'application_id',
        'application',
        'access_level',
        'features',
        'locales',
        'genres',
        'available_regions',
        'content_ratings',
        'system_requirements',
        'release_date',
        'preorder_release_date',
        'preorder_released_at',
        'external_purchase_url',
        'premium',
        'restricted',
        'exclusive',
        'deleted',
        'show_age_gate',
        'bundled_skus',
        'manifests',
        'manifest_label_ids',
        '_flags',
        'state',
    )
    if TYPE_CHECKING:
        name: str
        name_localizations: Dict[Locale, str]
        summary: Optional[str]
        summary_localizations: Dict[Locale, str]
        legal_notice: Optional[str]
        legal_notice_localizations: Dict[Locale, str]
    def __init__(
        self, *, data: SKUPayload, state: ConnectionState, application: Optional[PartialApplication] = None
    ) -> None:
        self.state = state
        self.application = application
        self._update(data)
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return f'<SKU id={self.id} name={self.name!r} type={self.type!r}>'
    def _update(self, data: SKUPayload) -> None:
        from .application import PartialApplication
        state = self.state
        self.name, self.name_localizations = _parse_localizations(data, 'name')
        self.summary, self.summary_localizations = _parse_localizations(data, 'summary')
        self.legal_notice, self.legal_notice_localizations = _parse_localizations(data, 'legal_notice')
        self.id: int = int(data['id'])
        self.type: SKUType = try_enum(SKUType, data['type'])
        self.product_line: Optional[SKUProductLine] = (
            try_enum(SKUProductLine, data['product_line']) if data.get('product_line') else None
        )
        self.slug: str = data['slug']
        self.dependent_sku_id: Optional[int] = _get_as_snowflake(data, 'dependent_sku_id')
        self.application_id: int = int(data['application_id'])
        self.application: Optional[PartialApplication] = (
            PartialApplication(data=data['application'], state=state)
            if 'application' in data
            else (
                state.premium_subscriptions_application
                if self.application_id == state.premium_subscriptions_application.id
                else self.application
            )
        )
        self._flags: int = data.get('flags', 0)
        self.price_tier: Optional[int] = data.get('price_tier')
        self.price_overrides: Dict[str, int] = data.get('price') or {}
        self.sale_price_tier: Optional[int] = data.get('sale_price_tier')
        self.sale_price_overrides: Dict[str, int] = data.get('sale_price') or {}
        if self.price_overrides and any(x in self.price_overrides for x in ('amount', 'currency')):
            self.price: SKUPrice = SKUPrice(data['price'])
            self.price_overrides = {}
        else:
            self.price = SKUPrice.from_private(data)
        self.access_level: SKUAccessLevel = try_enum(SKUAccessLevel, data.get('access_type', 1))
        self.features: List[SKUFeature] = [try_enum(SKUFeature, feature) for feature in data.get('features', [])]
        self.locales: List[Locale] = [try_enum(Locale, locale) for locale in data.get('locales', ['en-US'])]
        self.genres: List[SKUGenre] = [try_enum(SKUGenre, genre) for genre in data.get('genres', [])]
        self.available_regions: Optional[List[str]] = data.get('available_regions')
        self.content_ratings: List[ContentRating] = (
            [ContentRating.from_dict(data['content_rating'], data['content_rating_agency'])]
            if 'content_rating' in data and 'content_rating_agency' in data
            else ContentRating.from_dicts(data.get('content_ratings'))
        )
        self.system_requirements: List[SystemRequirements] = [
            SystemRequirements.from_dict(try_enum(OperatingSystem, int(os)), reqs)
            for os, reqs in data.get('system_requirements', {}).items()
        ]
        self.release_date: Optional[date] = parse_date(data.get('release_date'))
        self.preorder_release_date: Optional[date] = parse_date(data.get('preorder_approximate_release_date'))
        self.preorder_released_at: Optional[datetime] = parse_time(data.get('preorder_release_at'))
        self.external_purchase_url: Optional[str] = data.get('external_purchase_url')
        self.premium: bool = data.get('premium', False)
        self.restricted: bool = data.get('restricted', False)
        self.exclusive: bool = data.get('exclusive', False)
        self.deleted: bool = data.get('deleted', False)
        self.show_age_gate: bool = data.get('show_age_gate', False)
        self.bundled_skus: List[SKU] = [
            SKU(data=sku, state=state, application=self.application) for sku in data.get('bundled_skus', [])
        ]
        self.manifest_label_ids: List[int] = [int(label) for label in data.get('manifest_labels') or []]
    def is_free(self) -> bool:
        return self.price.is_free() and not self.premium
    def is_paid(self) -> bool:
        return not self.price.is_free() and not self.premium
    def is_preorder(self) -> bool:
        return self.preorder_release_date is not None or self.preorder_released_at is not None
    def is_released(self) -> bool:
        return self.release_date is not None and self.release_date <= utcnow()
    def is_giftable(self) -> bool:
        return (
            self.type == SKUType.durable_primary
            and self.flags.available
            and not self.external_purchase_url
            and self.is_paid()
        )
    def is_premium_perk(self) -> bool:
        return self.premium and (self.flags.premium_and_distribution or self.flags.premium_purchase)
    def is_premium_subscription(self) -> bool:
        return self.application_id == self.state.premium_subscriptions_application.id
    def is_game_awards_winner(self) -> bool:
        return self.id in THE_GAME_AWARDS_WINNERS
    @property
    def url(self) -> str:
        return f'https://discord.com/store/skus/{self.id}/{self.slug}'
    @property
    def flags(self) -> SKUFlags:
        return SKUFlags._from_value(self._flags)
    @property
    def supported_operating_systems(self) -> List[OperatingSystem]:
        return [reqs.os for reqs in self.system_requirements] or [OperatingSystem.windows]
    async def edit(
        self,
        name: str = MISSING,
        name_localizations: Mapping[Locale, str] = MISSING,
        legal_notice: Optional[str] = MISSING,
        legal_notice_localizations: Mapping[Locale, str] = MISSING,
        price_tier: Optional[int] = MISSING,
        price_overrides: Mapping[str, int] = MISSING,
        sale_price_tier: Optional[int] = MISSING,
        sale_price_overrides: Mapping[str, int] = MISSING,
        dependent_sku: Optional[Snowflake] = MISSING,
        flags: SKUFlags = MISSING,
        access_level: SKUAccessLevel = MISSING,
        features: Collection[SKUFeature] = MISSING,
        locales: Collection[Locale] = MISSING,
        genres: Collection[SKUGenre] = MISSING,
        content_ratings: Collection[ContentRating] = MISSING,
        system_requirements: Collection[SystemRequirements] = MISSING,
        release_date: Optional[date] = MISSING,
        bundled_skus: Sequence[Snowflake] = MISSING,
        manifest_labels: Sequence[Snowflake] = MISSING,
    ) -> None:
        payload = {}
        if name is not MISSING or name_localizations is not MISSING:
            payload['name'] = {
                'default': name or self.name,
                'localizations': {
                    str(k): v
                    for k, v in (
                        (name_localizations or {}) if name_localizations is not MISSING else self.name_localizations
                    ).items()
                },
            }
        if legal_notice or legal_notice_localizations:
            payload['legal_notice'] = {
                'default': legal_notice,
                'localizations': {
                    str(k): v
                    for k, v in (
                        (legal_notice_localizations or {})
                        if legal_notice_localizations is not MISSING
                        else self.legal_notice_localizations
                    ).items()
                },
            }
        if price_tier is not MISSING:
            payload['price_tier'] = price_tier
        if price_overrides is not MISSING:
            payload['price'] = {str(k): v for k, v in price_overrides.items()}
        if sale_price_tier is not MISSING:
            payload['sale_price_tier'] = sale_price_tier
        if sale_price_overrides is not MISSING:
            payload['sale_price'] = {str(k): v for k, v in (sale_price_overrides or {}).items()}
        if dependent_sku is not MISSING:
            payload['dependent_sku_id'] = dependent_sku.id if dependent_sku else None
        if flags is not MISSING:
            payload['flags'] = flags.value if flags else 0
        if access_level is not MISSING:
            payload['access_level'] = int(access_level)
        if locales is not MISSING:
            payload['locales'] = [str(l) for l in locales] if locales else []
        if features is not MISSING:
            payload['features'] = [int(f) for f in features] if features else []
        if genres is not MISSING:
            payload['genres'] = [int(g) for g in genres] if genres else []
        if content_ratings is not MISSING:
            payload['content_ratings'] = (
                {content_rating.agency: content_rating.to_dict() for content_rating in content_ratings}
                if content_ratings
                else {}
            )
        if system_requirements is not MISSING:
            payload['system_requirements'] = (
                {system_requirement.os: system_requirement.to_dict() for system_requirement in system_requirements}
                if system_requirements
                else {}
            )
        if release_date is not MISSING:
            payload['release_date'] = release_date.isoformat() if release_date else None
        if bundled_skus is not MISSING:
            payload['bundled_skus'] = [s.id for s in bundled_skus] if bundled_skus else []
        if manifest_labels is not MISSING:
            payload['manifest_labels'] = [m.id for m in manifest_labels] if manifest_labels else []
        data = await self.state.http.edit_sku(self.id, **payload)
        self._update(data)
    async def subscription_plans(
        self,
        *,
        country_code: str = MISSING,
        payment_source: Snowflake = MISSING,
        with_unpublished: bool = False,
    ) -> List[SubscriptionPlan]:
        r
        state = self.state
        data = await state.http.get_store_listing_subscription_plans(
            self.id,
            country_code=country_code if country_code is not MISSING else None,
            payment_source_id=payment_source.id if payment_source is not MISSING else None,
            include_unpublished=with_unpublished,
        )
        return [SubscriptionPlan(state=state, data=d) for d in data]
    async def store_listings(self, localize: bool = True) -> List[StoreListing]:
        r
        data = await self.state.http.get_sku_store_listings(self.id, localize=localize)
        return [StoreListing(data=listing, state=self.state, application=self.application) for listing in data]
    async def create_store_listing(
        self,
        *,
        summary: str,
        summary_localizations: Optional[Mapping[Locale, str]] = None,
        description: str,
        description_localizations: Optional[Mapping[Locale, str]] = None,
        tagline: Optional[str] = None,
        tagline_localizations: Optional[Mapping[Locale, str]] = None,
        child_skus: Optional[Collection[Snowflake]] = None,
        guild: Optional[Snowflake] = None,
        published: bool = False,
        carousel_items: Optional[Collection[Union[StoreAsset, str]]] = None,
        preview_video: Optional[Snowflake] = None,
        header_background: Optional[Snowflake] = None,
        hero_background: Optional[Snowflake] = None,
        hero_video: Optional[Snowflake] = None,
        box_art: Optional[Snowflake] = None,
        thumbnail: Optional[Snowflake] = None,
        header_logo_light: Optional[Snowflake] = None,
        header_logo_dark: Optional[Snowflake] = None,
    ) -> StoreListing:
        payload: Dict[str, Any] = {
            'summary': {
                'default': summary or '',
                'localizations': {str(k): v for k, v in (summary_localizations or {}).items()},
            },
            'description': {
                'default': description or '',
                'localizations': {str(k): v for k, v in (description_localizations or {}).items()},
            },
        }
        if tagline or tagline_localizations:
            payload['tagline'] = {
                'default': tagline or '',
                'localizations': {str(k): v for k, v in (tagline_localizations or {}).items()},
            }
        if child_skus:
            payload['child_sku_ids'] = [sku.id for sku in child_skus]
        if guild:
            payload['guild_id'] = guild.id
        if published:
            payload['published'] = True
        if carousel_items:
            payload['carousel_items'] = [
                item.to_carousel_item() if isinstance(item, StoreAsset) else {'youtube_video_id': item}
                for item in carousel_items
            ]
        if preview_video:
            payload['preview_video_asset_id'] = preview_video.id
        if header_background:
            payload['header_background_asset_id'] = header_background.id
        if hero_background:
            payload['hero_background_asset_id'] = hero_background.id
        if hero_video:
            payload['hero_video_asset_id'] = hero_video.id
        if box_art:
            payload['box_art_asset_id'] = box_art.id
        if thumbnail:
            payload['thumbnail_asset_id'] = thumbnail.id
        if header_logo_light:
            payload['header_logo_light_theme_asset_id'] = header_logo_light.id
        if header_logo_dark:
            payload['header_logo_dark_theme_asset_id'] = header_logo_dark.id
        data = await self.state.http.create_store_listing(self.application_id, self.id, payload)
        return StoreListing(data=data, state=self.state, application=self.application)
    async def create_discount(self, user: Snowflake, percent_off: int, *, ttl: int = 3600) -> None:
        await self.state.http.create_sku_discount(self.id, user.id, percent_off, ttl)
    async def delete_discount(self, user: Snowflake) -> None:
        await self.state.http.delete_sku_discount(self.id, user.id)
    async def create_gift_batch(
        self,
        *,
        amount: int,
        description: str,
        entitlement_branches: Optional[List[Snowflake]] = None,
        entitlement_starts_at: Optional[date] = None,
        entitlement_ends_at: Optional[date] = None,
    ) -> GiftBatch:
        from .entitlements import GiftBatch
        state = self.state
        app_id = self.application_id
        data = await state.http.create_gift_batch(
            app_id,
            self.id,
            amount,
            description,
            entitlement_branches=[branch.id for branch in entitlement_branches] if entitlement_branches else None,
            entitlement_starts_at=entitlement_starts_at.isoformat() if entitlement_starts_at else None,
            entitlement_ends_at=entitlement_ends_at.isoformat() if entitlement_ends_at else None,
        )
        return GiftBatch(data=data, state=state, application_id=app_id)
    async def gifts(self, subscription_plan: Optional[Snowflake] = None) -> List[Gift]:
        from .entitlements import Gift
        data = await self.state.http.get_sku_gifts(self.id, subscription_plan.id if subscription_plan else None)
        return [Gift(data=gift, state=self.state) for gift in data]
    async def create_gift(
        self, *, subscription_plan: Optional[Snowflake] = None, gift_style: Optional[GiftStyle] = None
    ) -> Gift:
        from .entitlements import Gift
        state = self.state
        data = await state.http.create_gift(
            self.id,
            subscription_plan_id=subscription_plan.id if subscription_plan else None,
            gift_style=int(gift_style) if gift_style else None,
        )
        return Gift(data=data, state=state)
    async def preview_purchase(
        self, payment_source: Snowflake, *, subscription_plan: Optional[Snowflake] = None, test_mode: bool = False
    ) -> SKUPrice:
        data = await self.state.http.preview_sku_purchase(
            self.id, payment_source.id, subscription_plan.id if subscription_plan else None, test_mode=test_mode
        )
        return SKUPrice(data=data)
    async def purchase(
        self,
        payment_source: Optional[Snowflake] = None,
        *,
        subscription_plan: Optional[Snowflake] = None,
        expected_amount: Optional[int] = None,
        expected_currency: Optional[str] = None,
        gift: bool = False,
        gift_style: Optional[GiftStyle] = None,
        test_mode: bool = False,
        payment_source_token: Optional[str] = None,
        purchase_token: Optional[str] = None,
        return_url: Optional[str] = None,
        gateway_checkout_context: Optional[str] = None,
    ) -> Tuple[List[Entitlement], List[LibraryApplication], Optional[Gift]]:
        if not gift and gift_style:
            raise TypeError('gift_style can only be used with gifts')
        state = self.state
        data = await state.http.purchase_sku(
            self.id,
            payment_source.id if payment_source else None,
            subscription_plan_id=subscription_plan.id if subscription_plan else None,
            expected_amount=expected_amount,
            expected_currency=expected_currency,
            gift=gift,
            gift_style=int(gift_style) if gift_style else None,
            test_mode=test_mode,
            payment_source_token=payment_source_token,
            purchase_token=purchase_token,
            return_url=return_url,
            gateway_checkout_context=gateway_checkout_context,
        )
        from .entitlements import Entitlement, Gift
        from .library import LibraryApplication
        entitlements = [Entitlement(state=state, data=entitlement) for entitlement in data.get('entitlements', [])]
        library_applications = [
            LibraryApplication(state=state, data=application) for application in data.get('library_applications', [])
        ]
        gift_code = data.get('gift_code')
        gift_ = None
        if gift_code:
            gift_data: GiftPayload = {
                'code': gift_code,
                'application_id': self.application_id,
                'subscription_plan_id': subscription_plan.id if subscription_plan else None,
                'sku_id': self.id,
                'gift_style': int(gift_style) if gift_style else None,
                'max_uses': 1,
                'uses': 0,
                'user': state.user._to_minimal_user_json(),
            }
            gift_ = Gift(state=state, data=gift_data)
            if subscription_plan and isinstance(subscription_plan, SubscriptionPlan):
                gift_.subscription_plan = subscription_plan
        return entitlements, library_applications, gift_
class SubscriptionPlanPrices:
    def __init__(self, data: SubscriptionPricesPayload):
        country_prices = data.get('country_prices') or {}
        payment_source_prices = data.get('payment_source_prices') or {}
        self.country_code: str = country_prices.get('country_code', 'US')
        self.country_prices: List[SKUPrice] = [SKUPrice(data=price) for price in country_prices.get('prices', [])]
        self.payment_source_prices: Dict[int, List[SKUPrice]] = {
            int(payment_source_id): [SKUPrice(data=price) for price in prices]
            for payment_source_id, prices in payment_source_prices.items()
        }
    def __repr__(self) -> str:
        return f'<SubscriptionPlanPrice country_code={self.country_code!r}>'
class SubscriptionPlan(Hashable):
    _INTERVAL_TABLE = {
        SubscriptionInterval.day: 1,
        SubscriptionInterval.month: 30,
        SubscriptionInterval.year: 365,
    }
    __slots__ = (
        'id',
        'name',
        'sku_id',
        'interval',
        'interval_count',
        'tax_inclusive',
        'prices',
        'currency',
        'price_tier',
        'price',
        'discount_price',
        'fallback_currency',
        'fallback_price',
        'fallback_discount_price',
        'state',
    )
    def __init__(
        self, *, data: Union[PartialSubscriptionPlanPayload, SubscriptionPlanPayload], state: ConnectionState
    ) -> None:
        self.state = state
        self._update(data)
    def _update(self, data: Union[PartialSubscriptionPlanPayload, SubscriptionPlanPayload]) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.sku_id: int = int(data['sku_id'])
        self.interval: SubscriptionInterval = try_enum(SubscriptionInterval, data['interval'])
        self.interval_count: int = data['interval_count']
        self.tax_inclusive: bool = data['tax_inclusive']
        self.prices: Dict[SubscriptionPlanPurchaseType, SubscriptionPlanPrices] = {
            try_enum(SubscriptionPlanPurchaseType, int(purchase_type)): SubscriptionPlanPrices(data=price_data)
            for purchase_type, price_data in (data.get('prices') or {}).items()
        }
        self.currency: Optional[str] = data.get('currency')
        self.price_tier: Optional[int] = data.get('price_tier')
        self.price: Optional[int] = data.get('price')
        self.discount_price: Optional[int] = data.get('discount_price')
        self.fallback_currency: Optional[str] = data.get('fallback_currency')
        self.fallback_price: Optional[int] = data.get('fallback_price')
        self.fallback_discount_price: Optional[int] = data.get('fallback_discount_price')
    def __repr__(self) -> str:
        return f'<SubscriptionPlan id={self.id} name={self.name!r} sku_id={self.sku_id} interval={self.interval!r} interval_count={self.interval_count}>'
    def __str__(self) -> str:
        return self.name
    @property
    def duration(self) -> timedelta:
        return timedelta(days=self.interval_count * self._INTERVAL_TABLE[self.interval])
    @property
    def premium_type(self) -> Optional[PremiumType]:
        return PremiumType.from_sku_id(self.sku_id)
    async def gifts(self) -> List[Gift]:
        from .entitlements import Gift
        data = await self.state.http.get_sku_gifts(self.sku_id, self.id)
        return [Gift(data=gift, state=self.state) for gift in data]
    async def create_gift(self, *, gift_style: Optional[GiftStyle] = None) -> Gift:
        from .entitlements import Gift
        state = self.state
        data = await state.http.create_gift(
            self.sku_id,
            subscription_plan_id=self.id,
            gift_style=int(gift_style) if gift_style else None,
        )
        return Gift(data=data, state=state)
    async def preview_purchase(self, payment_source: Snowflake, *, test_mode: bool = False) -> SKUPrice:
        data = await self.state.http.preview_sku_purchase(self.id, payment_source.id, self.id, test_mode=test_mode)
        return SKUPrice(data=data)
    async def purchase(
        self,
        payment_source: Optional[Snowflake] = None,
        *,
        expected_amount: Optional[int] = None,
        expected_currency: Optional[str] = None,
        gift: bool = False,
        gift_style: Optional[GiftStyle] = None,
        test_mode: bool = False,
        payment_source_token: Optional[str] = None,
        purchase_token: Optional[str] = None,
        return_url: Optional[str] = None,
        gateway_checkout_context: Optional[str] = None,
    ) -> Tuple[List[Entitlement], List[LibraryApplication], Optional[Gift]]:
        if not gift and gift_style:
            raise TypeError('gift_style can only be used with gifts')
        state = self.state
        data = await self.state.http.purchase_sku(
            self.sku_id,
            payment_source.id if payment_source else None,
            subscription_plan_id=self.id,
            expected_amount=expected_amount,
            expected_currency=expected_currency,
            gift=gift,
            gift_style=int(gift_style) if gift_style else None,
            test_mode=test_mode,
            payment_source_token=payment_source_token,
            purchase_token=purchase_token,
            return_url=return_url,
            gateway_checkout_context=gateway_checkout_context,
        )
        from .entitlements import Entitlement, Gift
        from .library import LibraryApplication
        entitlements = [Entitlement(state=state, data=entitlement) for entitlement in data.get('entitlements', [])]
        library_applications = [
            LibraryApplication(state=state, data=application) for application in data.get('library_applications', [])
        ]
        gift_code = data.get('gift_code')
        gift_ = None
        if gift_code:
            gift_data: GiftPayload = {
                'code': gift_code,
                'subscription_plan_id': self.id,
                'sku_id': self.sku_id,
                'gift_style': int(gift_style) if gift_style else None,
                'max_uses': 1,
                'uses': 0,
                'user': state.user._to_minimal_user_json(),
            }
            gift_ = Gift(state=state, data=gift_data)
            gift_.subscription_plan = self
        return entitlements, library_applications, gift_