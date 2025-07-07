from __future__ import annotations
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from .billing import PaymentSource
from .enums import (
    PaymentGateway,
    SubscriptionDiscountType,
    SubscriptionInterval,
    SubscriptionInvoiceStatus,
    SubscriptionStatus,
    SubscriptionType,
    try_enum,
)
from .metadata import Metadata
from .mixins import Hashable
from .utils import MISSING, _get_as_snowflake, parse_time, snowflake_time, utcnow
if TYPE_CHECKING:
    from typing_extensions import Self
    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.subscriptions import (
        SubscriptionDiscount as SubscriptionDiscountPayload,
        SubscriptionInvoice as SubscriptionInvoicePayload,
        SubscriptionInvoiceItem as SubscriptionInvoiceItemPayload,
        SubscriptionItem as SubscriptionItemPayload,
        SubscriptionRenewalMutations as SubscriptionRenewalMutationsPayload,
        PartialSubscription as PartialSubscriptionPayload,
        Subscription as SubscriptionPayload,
        SubscriptionTrial as SubscriptionTrialPayload,
    )
__all__ = (
    'SubscriptionItem',
    'SubscriptionDiscount',
    'SubscriptionInvoiceItem',
    'SubscriptionInvoice',
    'SubscriptionRenewalMutations',
    'Subscription',
    'SubscriptionTrial',
)
class SubscriptionItem(Hashable):
    __slots__ = ('id', 'quantity', 'plan_id')
    def __init__(self, *, id: Optional[int] = None, plan_id: int, quantity: int = 1) -> None:
        self.id: Optional[int] = id
        self.quantity: int = quantity
        self.plan_id: int = plan_id
    def __repr__(self) -> str:
        return f'<SubscriptionItem {f"id={self.id} " if self.id else ""}plan_id={self.plan_id} quantity={self.quantity}>'
    def __len__(self) -> int:
        return self.quantity
    @classmethod
    def from_dict(cls, data: SubscriptionItemPayload) -> Self:
        return cls(id=int(data['id']), plan_id=int(data['plan_id']), quantity=int(data.get('quantity', 1)))
    def to_dict(self, with_id: bool = True) -> dict:
        data = {
            'quantity': self.quantity,
            'plan_id': self.plan_id,
        }
        if self.id and with_id:
            data['id'] = self.id
        return data
class SubscriptionDiscount:
    __slots__ = ('type', 'amount')
    def __init__(self, data: SubscriptionDiscountPayload) -> None:
        self.type: SubscriptionDiscountType = try_enum(SubscriptionDiscountType, data['type'])
        self.amount: int = data['amount']
    def __repr__(self) -> str:
        return f'<SubscriptionDiscount type={self.type!r} amount={self.amount}>'
    def __int__(self) -> int:
        return self.amount
class SubscriptionInvoiceItem(Hashable):
    __slots__ = ('id', 'quantity', 'amount', 'proration', 'plan_id', 'plan_price', 'discounts', 'metadata')
    def __init__(self, data: SubscriptionInvoiceItemPayload) -> None:
        self.id: int = int(data['id'])
        self.quantity: int = data['quantity']
        self.amount: int = data['amount']
        self.proration: bool = data.get('proration', False)
        self.plan_id: int = int(data['subscription_plan_id'])
        self.plan_price: int = data['subscription_plan_price']
        self.discounts: List[SubscriptionDiscount] = [SubscriptionDiscount(d) for d in data['discounts']]
        self.metadata: Metadata = Metadata(data.get('tenant_metadata', {}))
    def __repr__(self) -> str:
        return f'<SubscriptionInvoiceItem id={self.id} quantity={self.quantity} amount={self.amount}>'
    def __len__(self) -> int:
        return self.quantity
    @property
    def savings(self) -> int:
        return self.plan_price - self.amount
    def is_discounted(self) -> bool:
        return bool(self.discounts)
    def is_trial(self) -> bool:
        return not self.amount or any(discount.type is SubscriptionDiscountType.premium_trial for discount in self.discounts)
class SubscriptionInvoice(Hashable):
    __slots__ = (
        'state',
        'subscription',
        'id',
        'status',
        'currency',
        'subtotal',
        'tax',
        'total',
        'tax_inclusive',
        'items',
        'current_period_start',
        'current_period_end',
        'applied_discount_ids',
        'applied_user_discounts',
    )
    def __init__(
        self, subscription: Optional[Subscription], *, data: SubscriptionInvoicePayload, state: ConnectionState
    ) -> None:
        self.state = state
        self.subscription = subscription
        self._update(data)
    def _update(self, data: SubscriptionInvoicePayload) -> None:
        self.id: int = int(data['id'])
        self.status: Optional[SubscriptionInvoiceStatus] = (
            try_enum(SubscriptionInvoiceStatus, data['status']) if 'status' in data else None
        )
        self.currency: str = data['currency']
        self.subtotal: int = data['subtotal']
        self.tax: int = data.get('tax', 0)
        self.total: int = data['total']
        self.tax_inclusive: bool = data['tax_inclusive']
        self.items: List[SubscriptionInvoiceItem] = [SubscriptionInvoiceItem(d) for d in data.get('invoice_items', [])]
        self.current_period_start: datetime = parse_time(data['subscription_period_start'])
        self.current_period_end: datetime = parse_time(data['subscription_period_end'])
        self.applied_discount_ids: List[int] = [int(id) for id in data.get('applied_discount_ids', [])]
        self.applied_user_discounts: Dict[int, Optional[Any]] = {
            int(k): v for k, v in data.get('applied_user_discounts', {}).items()
        }
    def __repr__(self) -> str:
        return f'<SubscriptionInvoice id={self.id} status={self.status!r} total={self.total}>'
    def is_discounted(self) -> bool:
        return any(item.discounts for item in self.items)
    def is_preview(self) -> bool:
        return self.subscription is None or self.status is None
    async def pay(
        self,
        payment_source: Optional[Snowflake] = None,
        currency: str = 'usd',
        *,
        payment_source_token: Optional[str] = None,
        return_url: Optional[str] = None,
    ) -> None:
        if self.is_preview() or not self.subscription:
            raise TypeError('Cannot pay a nonexistant invoice')
        data = await self.state.http.pay_invoice(
            self.subscription.id,
            self.id,
            payment_source.id if payment_source else None,
            payment_source_token,
            currency,
            return_url,
        )
        self.subscription._update(data)
class SubscriptionRenewalMutations:
    __slots__ = ('payment_gateway_plan_id', 'items')
    def __init__(self, data: SubscriptionRenewalMutationsPayload) -> None:
        self.payment_gateway_plan_id: Optional[str] = data.get('payment_gateway_plan_id')
        self.items: Optional[List[SubscriptionItem]] = (
            [SubscriptionItem.from_dict(item) for item in data['items']] if 'items' in data else None
        )
    def __repr__(self) -> str:
        return (
            f'<SubscriptionRenewalMutations payment_gateway_plan_id={self.payment_gateway_plan_id!r} items={self.items!r}>'
        )
    def __len__(self) -> int:
        return sum(item.quantity for item in self.items) if self.items else 0
    def __bool__(self) -> bool:
        return self.is_mutated()
    def is_mutated(self) -> bool:
        return self.payment_gateway_plan_id is not None or self.items is not None
class Subscription(Hashable):
    __slots__ = (
        'state',
        'id',
        'type',
        'status',
        'payment_gateway',
        'country_code',
        'currency',
        'items',
        'renewal_mutations',
        'trial_id',
        'payment_source_id',
        'payment_gateway_plan_id',
        'payment_gateway_subscription_id',
        'price',
        'created_at',
        'canceled_at',
        'current_period_start',
        'current_period_end',
        'trial_ends_at',
        'streak_started_at',
        'ended_at',
        'use_storekit_resubscribe',
        'metadata',
        'latest_invoice',
    )
    def __init__(self, *, data: Union[PartialSubscriptionPayload, SubscriptionPayload], state: ConnectionState) -> None:
        self.state = state
        self._update(data)
    def __repr__(self) -> str:
        return f'<Subscription id={self.id} currency={self.currency!r} items={self.items!r}>'
    def __len__(self) -> int:
        return sum(item.quantity for item in self.items)
    def __bool__(self) -> bool:
        return self.is_active()
    def _update(self, data: Union[PartialSubscriptionPayload, SubscriptionPayload]) -> None:
        self.id: int = int(data['id'])
        self.type: SubscriptionType = try_enum(SubscriptionType, data['type'])
        self.status: Optional[SubscriptionStatus] = (
            try_enum(SubscriptionStatus, data['status']) if 'status' in data else None
        )
        self.payment_gateway: Optional[PaymentGateway] = (
            try_enum(PaymentGateway, data['payment_gateway']) if 'payment_gateway' in data else None
        )
        self.country_code: Optional[str] = data.get('country_code')
        self.currency: str = data.get('currency', 'usd')
        self.items: List[SubscriptionItem] = [SubscriptionItem.from_dict(item) for item in data.get('items', [])]
        self.renewal_mutations: SubscriptionRenewalMutations = SubscriptionRenewalMutations(
            data.get('renewal_mutations') or {}
        )
        self.trial_id: Optional[int] = _get_as_snowflake(data, 'trial_id')
        self.payment_source_id: Optional[int] = _get_as_snowflake(data, 'payment_source_id')
        self.payment_gateway_plan_id: Optional[str] = data.get('payment_gateway_plan_id')
        self.payment_gateway_subscription_id: Optional[str] = data.get('payment_gateway_subscription_id')
        self.price: Optional[int] = data.get('price')
        self.created_at: datetime = parse_time(data.get('created_at')) or snowflake_time(self.id)
        self.canceled_at: Optional[datetime] = parse_time(data.get('canceled_at'))
        self.current_period_start: datetime = parse_time(data['current_period_start'])
        self.current_period_end: datetime = parse_time(data['current_period_end'])
        self.trial_ends_at: Optional[datetime] = parse_time(data.get('trial_ends_at'))
        self.streak_started_at: Optional[datetime] = parse_time(data.get('streak_started_at'))
        self.use_storekit_resubscribe: bool = data.get('use_storekit_resubscribe', False)
        metadata = data.get('metadata') or {}
        self.ended_at: Optional[datetime] = parse_time(metadata.get('ended_at', None))
        self.metadata: Metadata = Metadata(metadata)
        self.latest_invoice: Optional[SubscriptionInvoice] = (
            SubscriptionInvoice(self, data=data['latest_invoice'], state=self.state) if 'latest_invoice' in data else None
        )
    @property
    def cancelled_at(self) -> Optional[datetime]:
        return self.canceled_at
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.metadata.guild_id)
    @property
    def grace_period(self) -> timedelta:
        return timedelta(days=7 if self.payment_source_id else 3)
    @property
    def remaining(self) -> timedelta:
        if self.status in (SubscriptionStatus.active, SubscriptionStatus.cancelled):
            return self.current_period_end - utcnow()
        elif self.status == SubscriptionStatus.past_due:
            if self.payment_gateway == PaymentGateway.google and self.metadata.google_grace_period_expires_date:
                return self.metadata.google_grace_period_expires_date - utcnow()
            return (self.current_period_start + self.grace_period) - utcnow()
        elif self.status == SubscriptionStatus.account_hold:
            return (self.current_period_start + timedelta(days=30)) - utcnow()
        return timedelta()
    @property
    def trial_remaining(self) -> timedelta:
        if not self.trial_id:
            return timedelta()
        if not self.trial_ends_at:
            return self.remaining
        return self.trial_ends_at - utcnow()
    def is_active(self) -> bool:
        return self.remaining > timedelta()
    def is_trial(self) -> bool:
        return self.trial_id is not None
    async def edit(
        self,
        items: List[SubscriptionItem] = MISSING,
        payment_source: Snowflake = MISSING,
        currency: str = MISSING,
        *,
        status: SubscriptionStatus = MISSING,
        payment_source_token: Optional[str] = None,
    ) -> None:
        payload = {}
        if items is not MISSING:
            payload['items'] = [item.to_dict() for item in items] if items else []
        if payment_source is not MISSING:
            payload['payment_source_id'] = payment_source.id
            payload['payment_source_token'] = payment_source_token
        if currency is not MISSING:
            payload['currency'] = currency
        if status is not MISSING:
            payload['status'] = int(status)
        data = await self.state.http.edit_subscription(self.id, **payload)
        self._update(data)
    async def delete(self) -> None:
        await self.state.http.delete_subscription(self.id)
    async def cancel(self) -> None:
        await self.delete()
    async def preview_invoice(
        self,
        *,
        items: List[SubscriptionItem] = MISSING,
        payment_source: Snowflake = MISSING,
        currency: str = MISSING,
        apply_entitlements: bool = MISSING,
        renewal: bool = MISSING,
    ) -> SubscriptionInvoice:
        payload: Dict[str, Any] = {}
        if items is not MISSING:
            payload['items'] = [item.to_dict() for item in items] if items else []
        if payment_source:
            payload['payment_source_id'] = payment_source.id
        if currency:
            payload['currency'] = currency
        if apply_entitlements is not MISSING:
            payload['apply_entitlements'] = apply_entitlements
        if renewal is not MISSING:
            payload['renewal'] = renewal
        if payload:
            data = await self.state.http.preview_subscription_update(self.id, **payload)
        else:
            data = await self.state.http.get_subscription_preview(self.id)
        return SubscriptionInvoice(self, data=data, state=self.state)
    async def payment_source(self) -> Optional[PaymentSource]:
        if not self.payment_source_id:
            return
        data = await self.state.http.get_payment_source(self.payment_source_id)
        return PaymentSource(data=data, state=self.state)
    async def invoices(self):
        state = self.state
        data = await state.http.get_subscription_invoices(self.id)
        return [SubscriptionInvoice(self, data=d, state=state) for d in data]
class SubscriptionTrial(Hashable):
    __slots__ = ('id', 'interval', 'interval_count', 'sku_id')
    _INTERVAL_TABLE = {
        SubscriptionInterval.day: 1,
        SubscriptionInterval.month: 30,
        SubscriptionInterval.year: 365,
    }
    def __init__(self, data: SubscriptionTrialPayload):
        self.id: int = int(data['id'])
        self.interval: SubscriptionInterval = try_enum(SubscriptionInterval, data['interval'])
        self.interval_count: int = data['interval_count']
        self.sku_id: int = int(data['sku_id'])
    def __repr__(self) -> str:
        return (
            f'<SubscriptionTrial id={self.id} interval={self.interval} '
            f'interval_count={self.interval_count} sku_id={self.sku_id}>'
        )
    @property
    def duration(self) -> timedelta:
        return timedelta(days=self.interval_count * self._INTERVAL_TABLE[self.interval])