from __future__ import annotations
from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired
from .payments import PartialPayment
from .promotions import Promotion
from .snowflake import Snowflake
from .store import PublicSKU, PublicStoreListing
from .subscriptions import PartialSubscriptionPlan, SubscriptionPlan, SubscriptionTrial
from .user import PartialUser
class Entitlement(TypedDict):
    id: Snowflake
    type: Literal[1, 2, 3, 4, 5, 6, 7]
    user_id: Snowflake
    sku_id: Snowflake
    application_id: Snowflake
    promotion_id: Optional[Snowflake]
    parent_id: NotRequired[Snowflake]
    guild_id: NotRequired[Snowflake]
    branches: NotRequired[List[Snowflake]]
    gifter_user_id: NotRequired[Snowflake]
    gift_style: NotRequired[Literal[1, 2, 3]]
    gift_batch_id: NotRequired[Snowflake]
    gift_code_flags: NotRequired[int]
    deleted: bool
    consumed: NotRequired[bool]
    starts_at: NotRequired[str]
    ends_at: NotRequired[str]
    subscription_id: NotRequired[Snowflake]
    subscription_plan: NotRequired[PartialSubscriptionPlan]
    sku: NotRequired[PublicSKU]
    payment: NotRequired[PartialPayment]
class GatewayGift(TypedDict):
    code: str
    uses: int
    sku_id: Snowflake
    channel_id: NotRequired[Snowflake]
    guild_id: NotRequired[Snowflake]
class Gift(GatewayGift):
    expires_at: Optional[str]
    application_id: Snowflake
    batch_id: NotRequired[Snowflake]
    entitlement_branches: NotRequired[List[Snowflake]]
    gift_style: NotRequired[Optional[Literal[1, 2, 3]]]
    flags: int
    max_uses: int
    uses: int
    redeemed: bool
    revoked: NotRequired[bool]
    store_listing: NotRequired[PublicStoreListing]
    promotion: NotRequired[Promotion]
    subscription_trial: NotRequired[SubscriptionTrial]
    subscription_plan: NotRequired[SubscriptionPlan]
    user: NotRequired[PartialUser]
class GiftBatch(TypedDict):
    id: Snowflake
    sku_id: Snowflake
    amount: int
    description: NotRequired[str]
    entitlement_branches: NotRequired[List[Snowflake]]
    entitlement_starts_at: NotRequired[str]
    entitlement_ends_at: NotRequired[str]