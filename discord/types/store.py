from __future__ import annotations
from typing import Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired
from .application import PartialApplication, StoreAsset
from .entitlements import Entitlement
from .guild import PartialGuild
from .library import LibraryApplication
from .snowflake import Snowflake
from .user import PartialUser
LOCALIZED_STR = Union[str, Dict[str, str]]
class StoreNote(TypedDict):
    content: str
    user: Optional[PartialUser]
class SystemRequirement(TypedDict, total=False):
    ram: int
    disk: int
    operating_system_version: LOCALIZED_STR
    cpu: LOCALIZED_STR
    gpu: LOCALIZED_STR
    sound_card: LOCALIZED_STR
    directx: LOCALIZED_STR
    network: LOCALIZED_STR
    notes: LOCALIZED_STR
class SystemRequirements(TypedDict, total=False):
    minimum: SystemRequirement
    recommended: SystemRequirement
class CarouselItem(TypedDict, total=False):
    asset_id: Snowflake
    youtube_video_id: str
class BaseStoreListing(TypedDict):
    id: Snowflake
    summary: NotRequired[LOCALIZED_STR]
    description: NotRequired[LOCALIZED_STR]
    tagline: NotRequired[LOCALIZED_STR]
    flavor_text: NotRequired[str]
    entitlement_branch_id: NotRequired[Snowflake]
    staff_notes: NotRequired[StoreNote]
    assets: NotRequired[List[StoreAsset]]
    carousel_items: NotRequired[List[CarouselItem]]
    preview_video: NotRequired[StoreAsset]
    header_background: NotRequired[StoreAsset]
    hero_background: NotRequired[StoreAsset]
    hero_video: NotRequired[StoreAsset]
    box_art: NotRequired[StoreAsset]
    thumbnail: NotRequired[StoreAsset]
    header_logo_light_theme: NotRequired[StoreAsset]
    header_logo_dark_theme: NotRequired[StoreAsset]
    sku: PublicSKU
    child_skus: NotRequired[List[PublicSKU]]
    alternative_skus: NotRequired[List[PublicSKU]]
    published_at: NotRequired[str]
    unpublished_at: NotRequired[str]
class PublicStoreListing(BaseStoreListing):
    guild: NotRequired[PartialGuild]
class PrivateStoreListing(BaseStoreListing):
    published: bool
StoreListing = Union[PublicStoreListing, PrivateStoreListing]
class PremiumPrice(TypedDict):
    amount: int
    percentage: int
class SKUPrice(TypedDict):
    currency: str
    currency_exponent: int
    amount: int
    sale_amount: NotRequired[Optional[int]]
    sale_percentage: NotRequired[int]
    premium: NotRequired[Dict[Literal[1, 2, 3], PremiumPrice]]
class ContentRating(TypedDict):
    rating: int
    descriptors: List[int]
SKUType = Literal[1, 2, 3, 4, 5, 6]
class PartialSKU(TypedDict):
    id: Snowflake
    type: SKUType
    premium: bool
    preorder_release_date: Optional[str]
    preorder_released_at: Optional[str]
class BaseSKU(PartialSKU):
    id: Snowflake
    type: SKUType
    product_line: Optional[Literal[1, 2, 3, 4, 5, 6, 7]]
    name: LOCALIZED_STR
    summary: NotRequired[LOCALIZED_STR]
    legal_notice: NotRequired[LOCALIZED_STR]
    slug: str
    dependent_sku_id: Optional[Snowflake]
    application_id: Snowflake
    application: NotRequired[PartialApplication]
    flags: int
    access_level: Literal[1, 2, 3]
    features: List[int]
    locales: NotRequired[List[str]]
    genres: NotRequired[List[int]]
    available_regions: NotRequired[List[str]]
    system_requirements: NotRequired[Dict[Literal[1, 2, 3], SystemRequirements]]
    release_date: Optional[str]
    preorder_release_date: NotRequired[Optional[str]]
    preorder_released_at: NotRequired[Optional[str]]
    external_purchase_url: NotRequired[str]
    premium: NotRequired[bool]
    restricted: NotRequired[bool]
    exclusive: NotRequired[bool]
    deleted: NotRequired[bool]
    show_age_gate: bool
    manifest_labels: Optional[List[Snowflake]]
class PublicSKU(BaseSKU):
    bundled_skus: NotRequired[List[PublicSKU]]
    price: SKUPrice
    content_rating_agency: NotRequired[Literal[1, 2]]
    content_rating: NotRequired[ContentRating]
class PrivateSKU(BaseSKU):
    bundled_skus: NotRequired[List[PrivateSKU]]
    price_tier: int
    price: Dict[str, int]
    sale_price_tier: int
    sale_price: Dict[str, int]
    content_ratings: Dict[Literal[1, 2], ContentRating]
SKU = Union[PublicSKU, PrivateSKU]
class SKUPurchase(TypedDict):
    entitlements: List[Entitlement]
    library_applications: NotRequired[List[LibraryApplication]]
    gift_code: NotRequired[str]