from __future__ import annotations
from typing import List, Literal, TypedDict
from typing_extensions import NotRequired
from .billing import PartialPaymentSource
from .snowflake import Snowflake
from .store import PublicSKU
from .subscriptions import PartialSubscription
class PartialPayment(TypedDict):
    id: Snowflake
    amount: int
    tax: int
    tax_inclusive: bool
    currency: str
class Payment(PartialPayment):
    amount_refunded: int
    description: str
    status: Literal[0, 1, 2, 3, 4, 5]
    created_at: str
    sku_id: NotRequired[Snowflake]
    sku_price: NotRequired[int]
    sku_subscription_plan_id: NotRequired[Snowflake]
    payment_gateway: NotRequired[Literal[1, 2, 3, 4, 5, 6]]
    payment_gateway_payment_id: NotRequired[str]
    downloadable_invoice: NotRequired[str]
    downloadable_refund_invoices: NotRequired[List[str]]
    refund_disqualification_reasons: NotRequired[List[str]]
    flags: int
    sku: NotRequired[PublicSKU]
    payment_source: NotRequired[PartialPaymentSource]
    subscription: NotRequired[PartialSubscription]