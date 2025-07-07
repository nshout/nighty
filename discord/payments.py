from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from .billing import PaymentSource
from .enums import (
    PaymentGateway,
    PaymentStatus,
    RefundDisqualificationReason,
    RefundReason,
    SubscriptionType,
    try_enum,
)
from .flags import PaymentFlags
from .mixins import Hashable
from .store import SKU
from .subscriptions import Subscription
from .utils import _get_as_snowflake, parse_time
if TYPE_CHECKING:
    from .entitlements import Entitlement
    from .state import ConnectionState
    from .types.payments import (
        PartialPayment as PartialPaymentPayload,
        Payment as PaymentPayload,
    )
__all__ = (
    'Payment',
    'EntitlementPayment',
)
class Payment(Hashable):
    __slots__ = (
        'id',
        'amount',
        'amount_refunded',
        'tax',
        'tax_inclusive',
        'currency',
        'description',
        'status',
        'created_at',
        'sku',
        'sku_id',
        'sku_price',
        'subscription_plan_id',
        'subscription',
        'payment_source',
        'payment_gateway',
        'payment_gateway_payment_id',
        'invoice_url',
        'refund_invoices_urls',
        'refund_disqualification_reasons',
        '_flags',
        'state',
    )
    def __init__(self, *, data: PaymentPayload, state: ConnectionState):
        self.state: ConnectionState = state
        self._update(data)
    def _update(self, data: PaymentPayload) -> None:
        state = self.state
        self.id: int = int(data['id'])
        self.amount: int = data['amount']
        self.amount_refunded: int = data.get('amount_refunded') or 0
        self.tax: int = data.get('tax') or 0
        self.tax_inclusive: bool = data.get('tax_inclusive', True)
        self.currency: str = data.get('currency', 'usd')
        self.description: str = data['description']
        self.status: PaymentStatus = try_enum(PaymentStatus, data['status'])
        self.created_at: datetime = parse_time(data['created_at'])
        self.sku: Optional[SKU] = SKU(data=data['sku'], state=state) if 'sku' in data else None
        self.sku_id: Optional[int] = _get_as_snowflake(data, 'sku_id')
        self.sku_price: Optional[int] = data.get('sku_price')
        self.subscription_plan_id: Optional[int] = _get_as_snowflake(data, 'sku_subscription_plan_id')
        self.payment_gateway: Optional[PaymentGateway] = (
            try_enum(PaymentGateway, data['payment_gateway']) if 'payment_gateway' in data else None
        )
        self.payment_gateway_payment_id: Optional[str] = data.get('payment_gateway_payment_id')
        self.invoice_url: Optional[str] = data.get('downloadable_invoice')
        self.refund_invoices_urls: List[str] = data.get('downloadable_refund_invoices', [])
        self.refund_disqualification_reasons: List[RefundDisqualificationReason] = [
            try_enum(RefundDisqualificationReason, r) for r in data.get('premium_refund_disqualification_reasons', [])
        ]
        self._flags: int = data.get('flags', 0)
        self.payment_source: Optional[PaymentSource] = (
            PaymentSource(data=data['payment_source'], state=state) if 'payment_source' in data else None
        )
        if 'subscription' in data and self.payment_source:
            data['subscription']['payment_source_id'] = self.payment_source.id
        self.subscription: Optional[Subscription] = (
            Subscription(data=data['subscription'], state=state) if 'subscription' in data else None
        )
    def __repr__(self) -> str:
        return f'<Payment id={self.id} amount={self.amount} currency={self.currency} status={self.status}>'
    def __str__(self) -> str:
        return self.description
    def is_subscription(self) -> bool:
        return self.subscription is not None
    def is_premium_subscription(self) -> bool:
        return self.subscription is not None and self.subscription.type == SubscriptionType.premium
    def is_premium_subscription_gift(self) -> bool:
        return self.flags.gift and self.sku_id in self.state.premium_subscriptions_sku_ids.values()
    def is_purchased_externally(self) -> bool:
        return self.payment_gateway in (PaymentGateway.apple, PaymentGateway.google)
    @property
    def flags(self) -> PaymentFlags:
        return PaymentFlags._from_value(self._flags)
    async def void(self) -> None:
        await self.state.http.void_payment(self.id)
        self.status = PaymentStatus.failed
    async def refund(self, reason: RefundReason = RefundReason.other) -> None:
        await self.state.http.refund_payment(self.id, int(reason))
        self.status = PaymentStatus.refunded
class EntitlementPayment(Hashable):
    __slots__ = ('entitlement', 'id', 'amount', 'tax', 'tax_inclusive', 'currency')
    def __init__(self, *, data: PartialPaymentPayload, entitlement: Entitlement):
        self.entitlement = entitlement
        self.id: int = int(data['id'])
        self.amount: int = data['amount']
        self.tax: int = data.get('tax') or 0
        self.tax_inclusive: bool = data.get('tax_inclusive', True)
        self.currency: str = data.get('currency', 'usd')
    def __repr__(self) -> str:
        return f'<EntitlementPayment id={self.id} amount={self.amount} currency={self.currency}>'