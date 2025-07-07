from __future__ import annotations
from typing import List, Optional, TypedDict
from typing_extensions import NotRequired
from .snowflake import Snowflake
from .subscriptions import SubscriptionTrial
class Promotion(TypedDict):
    id: Snowflake
    trial_id: NotRequired[Snowflake]
    start_date: str
    end_date: str
    flags: int
    outbound_title: str
    outbound_redemption_modal_body: str
    outbound_redemption_page_link: NotRequired[str]
    outbound_redemption_url_format: NotRequired[str]
    outbound_restricted_countries: NotRequired[List[str]]
    outbound_terms_and_conditions: str
    inbound_title: NotRequired[str]
    inbound_body_text: NotRequired[str]
    inbound_help_center_link: NotRequired[str]
    inbound_restricted_countries: NotRequired[List[str]]
class ClaimedPromotion(TypedDict):
    promotion: Promotion
    code: str
    claimed_at: str
class TrialOffer(TypedDict):
    id: Snowflake
    expires_at: Optional[str]
    trial_id: Snowflake
    subscription_trial: SubscriptionTrial
class PromotionalPrice(TypedDict):
    amount: int
    currency: str
class PricingPromotion(TypedDict):
    plan_id: Snowflake
    country_code: str
    payment_source_types: List[str]
    price: PromotionalPrice
class WrappedPricingPromotion(TypedDict):
    country_code: str
    localized_pricing_promo: Optional[PricingPromotion]