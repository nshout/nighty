from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired
from .snowflake import Snowflake
from .user import PartialUser
class PremiumGuildSubscription(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    user_id: Snowflake
    user: NotRequired[PartialUser]
    ended: bool
    ends_at: NotRequired[str]
class PremiumGuildSubscriptionSlot(TypedDict):
    id: Snowflake
    subscription_id: Snowflake
    canceled: bool
    cooldown_ends_at: Optional[str]
    premium_guild_subscription: Optional[PremiumGuildSubscription]
class PremiumGuildSubscriptionCooldown(TypedDict):
    ends_at: str
    limit: int
    remaining: int
class SubscriptionItem(TypedDict):
    id: Snowflake
    quantity: int
    plan_id: Snowflake
class SubscriptionDiscount(TypedDict):
    type: Literal[1, 2, 3, 4]
    amount: int
class SubscriptionInvoiceItem(TypedDict):
    id: Snowflake
    quantity: int
    amount: int
    proration: bool
    subscription_plan_id: Snowflake
    subscription_plan_price: int
    discounts: List[SubscriptionDiscount]
    tenant_metadata: NotRequired[Dict[str, Any]]
class SubscriptionInvoice(TypedDict):
    id: Snowflake
    status: NotRequired[Literal[1, 2, 3, 4]]
    currency: str
    subtotal: int
    tax: int
    total: int
    tax_inclusive: bool
    items: List[SubscriptionInvoiceItem]
    current_period_start: str
    current_period_end: str
    applied_discount_ids: NotRequired[List[Snowflake]]
    applied_user_discounts: NotRequired[Dict[Snowflake, Optional[Any]]]
class SubscriptionRenewalMutations(TypedDict, total=False):
    payment_gateway_plan_id: Optional[str]
    items: List[SubscriptionItem]
class PartialSubscription(TypedDict):
    id: Snowflake
    type: Literal[1, 2, 3]
    payment_gateway: Optional[Literal[1, 2, 3, 4, 5, 6]]
    currency: str
    items: List[SubscriptionItem]
    payment_gateway_plan_id: Optional[str]
    payment_gateway_subscription_id: NotRequired[Optional[str]]
    current_period_start: str
    current_period_end: str
    streak_started_at: NotRequired[str]
class Subscription(PartialSubscription):
    status: Literal[0, 1, 2, 3, 4, 5, 6]
    renewal_mutations: NotRequired[SubscriptionRenewalMutations]
    trial_id: NotRequired[Snowflake]
    payment_source_id: Optional[Snowflake]
    created_at: str
    canceled_at: NotRequired[str]
    country_code: Optional[str]
    trial_ends_at: NotRequired[str]
    metadata: NotRequired[Dict[str, Any]]
    latest_invoice: NotRequired[SubscriptionInvoice]
    use_storekit_resubscribe: bool
    price: Optional[int]
class SubscriptionTrial(TypedDict):
    id: Snowflake
    interval: Literal[1, 2, 3]
    interval_count: int
    sku_id: Snowflake
class SubscriptionPrice(TypedDict):
    currency: str
    amount: int
    exponent: int
class CountryCode(TypedDict):
    country_code: str
class SubscriptionCountryPrice(CountryCode):
    prices: List[SubscriptionPrice]
class SubscriptionPrices(TypedDict):
    country_prices: SubscriptionCountryPrice
    payment_source_prices: Dict[Snowflake, List[SubscriptionPrice]]
class PartialSubscriptionPlan(TypedDict):
    id: Snowflake
    name: str
    sku_id: Snowflake
    interval: Literal[1, 2, 3]
    interval_count: int
    tax_inclusive: bool
class SubscriptionPlan(PartialSubscriptionPlan):
    prices: Dict[Literal[0, 1, 2, 3, 4], SubscriptionPrices]
    price_tier: Literal[None]
    currency: str
    price: int
    discount_price: NotRequired[int]
    fallback_currency: NotRequired[str]
    fallback_price: NotRequired[int]
    fallback_discount_price: NotRequired[int]