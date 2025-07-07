from __future__ import annotations
from typing import Literal, TypedDict
from typing_extensions import NotRequired
class BillingAddress(TypedDict):
    line_1: str
    line_2: NotRequired[str]
    name: str
    postal_code: NotRequired[str]
    city: str
    state: NotRequired[str]
    country: str
    email: NotRequired[str]
class BillingAddressToken(TypedDict):
    token: str
class PartialPaymentSource(TypedDict):
    id: str
    brand: NotRequired[str]
    country: NotRequired[str]
    last_4: NotRequired[str]
    type: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    payment_gateway: Literal[1, 2, 3, 4, 5, 6]
    invalid: bool
    flags: int
    expires_month: NotRequired[int]
    expires_year: NotRequired[int]
    email: NotRequired[str]
    bank: NotRequired[str]
    username: NotRequired[str]
    screen_status: int
class PaymentSource(PartialPaymentSource):
    billing_address: BillingAddress
    default: bool
class PremiumUsageValue(TypedDict):
    value: int
class PremiumUsage(TypedDict):
    nitro_sticker_sends: PremiumUsageValue
    total_animated_emojis: PremiumUsageValue
    total_global_emojis: PremiumUsageValue
    total_large_uploads: PremiumUsageValue
    total_hd_streams: PremiumUsageValue
    hd_hours_streamed: PremiumUsageValue