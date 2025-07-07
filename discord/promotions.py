from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Union
from .enums import PaymentSourceType, try_enum
from .flags import PromotionFlags
from .mixins import Hashable
from .subscriptions import SubscriptionTrial
from .utils import _get_as_snowflake, parse_time, utcnow
if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.promotions import (
        ClaimedPromotion as ClaimedPromotionPayload,
        Promotion as PromotionPayload,
        TrialOffer as TrialOfferPayload,
        PricingPromotion as PricingPromotionPayload,
    )
__all__ = (
    'Promotion',
    'TrialOffer',
    'PricingPromotion',
)
class Promotion(Hashable):
    __slots__ = (
        'id',
        'trial_id',
        'starts_at',
        'ends_at',
        'claimed_at',
        'code',
        'outbound_title',
        'outbound_description',
        'outbound_link',
        'outbound_restricted_countries',
        'inbound_title',
        'inbound_description',
        'inbound_link',
        'inbound_restricted_countries',
        'terms_and_conditions',
        '_flags',
        'state',
    )
    def __init__(self, *, data: Union[PromotionPayload, ClaimedPromotionPayload], state: ConnectionState) -> None:
        self.state = state
        self._update(data)
    def __str__(self) -> str:
        return self.outbound_title
    def __repr__(self) -> str:
        return f'<Promotion id={self.id} title={self.outbound_title!r}>'
    def _update(self, data: Union[PromotionPayload, ClaimedPromotionPayload]) -> None:
        promotion: PromotionPayload = data.get('promotion', data)
        self.id: int = int(promotion['id'])
        self.trial_id: Optional[int] = _get_as_snowflake(promotion, 'trial_id')
        self.starts_at: datetime = parse_time(promotion['start_date'])
        self.ends_at: datetime = parse_time(promotion['end_date'])
        self.claimed_at: Optional[datetime] = parse_time(data.get('claimed_at'))
        self.code: Optional[str] = data.get('code')
        self._flags: int = promotion.get('flags', 0)
        self.outbound_title: str = promotion['outbound_title']
        self.outbound_description: str = promotion['outbound_redemption_modal_body']
        self.outbound_link: str = promotion.get(
            'outbound_redemption_page_link',
            promotion.get('outbound_redemption_url_format', '').replace('{code}', self.code or '{code}'),
        )
        self.outbound_restricted_countries: List[str] = promotion.get('outbound_restricted_countries', [])
        self.inbound_title: Optional[str] = promotion.get('inbound_header_text')
        self.inbound_description: Optional[str] = promotion.get('inbound_body_text')
        self.inbound_link: Optional[str] = promotion.get('inbound_help_center_link')
        self.inbound_restricted_countries: List[str] = promotion.get('inbound_restricted_countries', [])
        self.terms_and_conditions: str = promotion['outbound_terms_and_conditions']
    @property
    def flags(self) -> PromotionFlags:
        return PromotionFlags._from_value(self._flags)
    def is_claimed(self) -> bool:
        return self.claimed_at is not None
    def is_active(self) -> bool:
        return self.starts_at <= utcnow() <= self.ends_at
    async def claim(self) -> str:
        data = await self.state.http.claim_promotion(self.id)
        self._update(data)
        return data['code']
class TrialOffer(Hashable):
    __slots__ = (
        'id',
        'expires_at',
        'trial_id',
        'trial',
        'state',
    )
    def __init__(self, *, data: TrialOfferPayload, state: ConnectionState) -> None:
        self.state = state
        self._update(data)
    def _update(self, data: TrialOfferPayload) -> None:
        self.id: int = int(data['id'])
        self.expires_at: Optional[datetime] = parse_time(data.get('expires_at'))
        self.trial_id: int = int(data['trial_id'])
        self.trial: SubscriptionTrial = SubscriptionTrial(data['subscription_trial'])
    def __repr__(self) -> str:
        return f'<TrialOffer id={self.id} trial={self.trial!r}>'
    def is_acked(self) -> bool:
        return self.expires_at is not None
    async def ack(self) -> None:
        data = await self.state.http.ack_trial_offer(self.id)
        self._update(data)
class PricingPromotion:
    __slots__ = (
        'subscription_plan_id',
        'country_code',
        'payment_source_types',
        'amount',
        'currency',
    )
    def __init__(self, *, data: PricingPromotionPayload) -> None:
        self.subscription_plan_id: int = int(data['plan_id'])
        self.country_code: str = data['country_code']
        self.payment_source_types: List[PaymentSourceType] = [
            try_enum(PaymentSourceType, t) for t in data['payment_source_types']
        ]
        price = data['price']
        self.amount: int = price['amount']
        self.currency: str = price['currency']
    def __repr__(self) -> str:
        return f'<PricingPromotion plan_id={self.subscription_plan_id} country_code={self.country_code!r} amount={self.amount} currency={self.currency!r}>'