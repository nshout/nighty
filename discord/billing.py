from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Union
from .enums import (
    PaymentGateway,
    PaymentSourceType,
    try_enum,
)
from .flags import PaymentSourceFlags
from .mixins import Hashable
from .utils import MISSING
if TYPE_CHECKING:
    from datetime import date
    from typing_extensions import Self
    from .state import ConnectionState
    from .types.billing import (
        BillingAddress as BillingAddressPayload,
        PartialPaymentSource as PartialPaymentSourcePayload,
        PaymentSource as PaymentSourcePayload,
        PremiumUsage as PremiumUsagePayload,
    )
__all__ = (
    'BillingAddress',
    'PaymentSource',
    'PremiumUsage',
)
class BillingAddress:
    __slots__ = ('_state', 'name', 'address', 'postal_code', 'city', 'state', 'country', 'email')
    def __init__(
        self,
        *,
        name: str,
        address: str,
        city: str,
        country: str,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        email: Optional[str] = None,
        _state: Optional[ConnectionState] = None,
    ) -> None:
        self._state = _state
        self.name = name
        self.address = address
        self.postal_code = postal_code
        self.city = city
        self.state = state
        self.country = country
        self.email = email
    def __repr__(self) -> str:
        return f'<BillingAddress name={self.name!r} address={self.address!r} city={self.city!r} country={self.country!r}>'
    def __eq__(self, other: object) -> bool:
        return isinstance(other, BillingAddress) and self.to_dict() == other.to_dict()
    def __ne__(self, other: object) -> bool:
        if not isinstance(other, BillingAddress):
            return True
        return self.to_dict() != other.to_dict()
    def __hash__(self) -> int:
        return hash(self.to_dict())
    @classmethod
    def from_dict(cls, data: BillingAddressPayload, state: ConnectionState) -> Self:
        address = '\n'.join(filter(None, (data['line_1'], data.get('line_2'))))
        return cls(
            _state=state,
            name=data['name'],
            address=address,
            postal_code=data.get('postal_code'),
            city=data['city'],
            state=data.get('state'),
            country=data['country'],
            email=data.get('email'),
        )
    def to_dict(self) -> dict:
        line1, _, line2 = self.address.partition('\n')
        data = {
            'name': self.name,
            'line_1': line1,
            'line_2': line2 or '',
            'city': self.city,
            'country': self.country,
        }
        if self.postal_code:
            data['postal_code'] = self.postal_code
        if self.state:
            data['state'] = self.state
        if self.email:
            data['email'] = self.email
        return data
    async def validate(self) -> str:
        if self._state is None:
            raise TypeError('BillingAddress does not have state available')
        data = await self._state.http.validate_billing_address(self.to_dict())
        return data['token']
class PaymentSource(Hashable):
    __slots__ = (
        '_state',
        'id',
        'brand',
        'country',
        'partial_card_number',
        'billing_address',
        'type',
        'payment_gateway',
        'default',
        'invalid',
        'expires_at',
        'email',
        'bank',
        'username',
        '_flags',
    )
    def __init__(self, *, data: Union[PaymentSourcePayload, PartialPaymentSourcePayload], state: ConnectionState) -> None:
        self._state = state
        self._update(data)
    def __repr__(self) -> str:
        return f'<PaymentSource id={self.id} type={self.type!r} country={self.country!r}>'
    def _update(self, data: Union[PaymentSourcePayload, PartialPaymentSourcePayload]) -> None:
        self.id: int = int(data['id'])
        self.brand: Optional[str] = data.get('brand')
        self.country: Optional[str] = data.get('country')
        self.partial_card_number: Optional[str] = data.get('last_4')
        self.billing_address: Optional[BillingAddress] = (
            BillingAddress.from_dict(data['billing_address'], state=self._state) if 'billing_address' in data else None
        )
        self.type: PaymentSourceType = try_enum(PaymentSourceType, data['type'])
        self.payment_gateway: PaymentGateway = try_enum(PaymentGateway, data['payment_gateway'])
        self.default: bool = data.get('default', False)
        self.invalid: bool = data['invalid']
        self._flags: int = data.get('flags', 0)
        month = data.get('expires_month')
        year = data.get('expires_year')
        self.expires_at: Optional[date] = datetime(year=year, month=month or 1, day=1).date() if year else None
        self.email: Optional[str] = data.get('email')
        self.bank: Optional[str] = data.get('bank')
        self.username: Optional[str] = data.get('username')
        if not self.country and self.billing_address:
            self.country = self.billing_address.country
        if not self.email and self.billing_address:
            self.email = self.billing_address.email
    @property
    def flags(self) -> PaymentSourceFlags:
        return PaymentSourceFlags._from_value(self._flags)
    async def edit(
        self, *, billing_address: BillingAddress = MISSING, default: bool = MISSING, expires_at: date = MISSING
    ) -> None:
        payload = {}
        if billing_address is not MISSING:
            payload['billing_address'] = billing_address.to_dict()
        if default is not MISSING:
            payload['default'] = default
        if expires_at is not MISSING:
            payload['expires_month'] = expires_at.month
            payload['expires_year'] = expires_at.year
        data = await self._state.http.edit_payment_source(self.id, payload)
        self._update(data)
    async def delete(self) -> None:
        await self._state.http.delete_payment_source(self.id)
class PremiumUsage:
    __slots__ = (
        'sticker_sends',
        'animated_emojis',
        'global_emojis',
        'large_uploads',
        'hd_streams',
        'hd_hours_streamed',
    )
    def __init__(self, *, data: PremiumUsagePayload) -> None:
        self.sticker_sends: int = data['nitro_sticker_sends']['value']
        self.animated_emojis: int = data['total_animated_emojis']['value']
        self.global_emojis: int = data['total_global_emojis']['value']
        self.large_uploads: int = data['total_large_uploads']['value']
        self.hd_streams: int = data['total_hd_streams']['value']
        self.hd_hours_streamed: int = data['hd_hours_streamed']['value']