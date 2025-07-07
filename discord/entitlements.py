from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Optional
from .enums import EntitlementType, GiftStyle, PremiumType, try_enum
from .flags import GiftFlags
from .mixins import Hashable
from .payments import EntitlementPayment
from .promotions import Promotion
from .store import SKU, StoreListing, SubscriptionPlan
from .subscriptions import Subscription, SubscriptionTrial
from .utils import _get_as_snowflake, parse_time, utcnow
if TYPE_CHECKING:
    from datetime import datetime
    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.entitlements import (
        Entitlement as EntitlementPayload,
        Gift as GiftPayload,
        GiftBatch as GiftBatchPayload,
    )
    from .user import User
__all__ = (
    'Entitlement',
    'Gift',
    'GiftBatch',
)
class Entitlement(Hashable):
    __slots__ = (
        'id',
        'type',
        'user_id',
        'sku_id',
        'application_id',
        'promotion_id',
        'parent_id',
        'guild_id',
        'branches',
        'gifter_id',
        'gift_style',
        'gift_batch_id',
        '_gift_flags',
        'deleted',
        'consumed',
        'starts_at',
        'ends_at',
        'subscription_id',
        'subscription_plan',
        'sku',
        'payment',
        'state',
    )
    def __init__(self, *, data: EntitlementPayload, state: ConnectionState):
        self.state = state
        self._update(data)
    def _update(self, data: EntitlementPayload):
        state = self.state
        self.id: int = int(data['id'])
        self.type: EntitlementType = try_enum(EntitlementType, data['type'])
        self.user_id: int = int(data.get('user_id') or state.self_id)
        self.sku_id: int = int(data['sku_id'])
        self.application_id: int = int(data['application_id'])
        self.promotion_id: Optional[int] = _get_as_snowflake(data, 'promotion_id')
        self.parent_id: Optional[int] = _get_as_snowflake(data, 'parent_id')
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.branches: List[int] = [int(branch) for branch in data.get('branches', [])]
        self.gifter_id: Optional[int] = _get_as_snowflake(data, 'gifter_user_id')
        self.gift_style: Optional[GiftStyle] = try_enum(GiftStyle, data.get('gift_style'))
        self.gift_batch_id: Optional[int] = _get_as_snowflake(data, 'gift_code_batch_id')
        self._gift_flags: int = data.get('gift_code_flags', 0)
        self.deleted: bool = data.get('deleted', False)
        self.consumed: bool = data.get('consumed', False)
        self.starts_at: Optional[datetime] = parse_time(data.get('starts_at'))
        self.ends_at: Optional[datetime] = parse_time(data.get('ends_at'))
        self.subscription_id: Optional[int] = _get_as_snowflake(data, 'subscription_id')
        self.subscription_plan: Optional[SubscriptionPlan] = (
            SubscriptionPlan(data=data['subscription_plan'], state=state) if 'subscription_plan' in data else None
        )
        self.sku: Optional[SKU] = SKU(data=data['sku'], state=state) if 'sku' in data else None
        self.payment: Optional[EntitlementPayment] = (
            EntitlementPayment(data=data['payment'], entitlement=self) if 'payment' in data else None
        )
    def __repr__(self) -> str:
        return f'<Entitlement id={self.id} type={self.type!r} sku_id={self.sku_id} application_id={self.application_id}>'
    def __bool__(self) -> bool:
        return self.is_active()
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    @property
    def premium_type(self) -> Optional[PremiumType]:
        return PremiumType.from_sku_id(self.sku_id)
    @property
    def gift_flags(self) -> GiftFlags:
        return GiftFlags._from_value(self._gift_flags)
    def is_giftable(self) -> bool:
        return self.type == EntitlementType.user_gift and not self.gifter_id
    def is_active(self) -> bool:
        if self.is_giftable() or self.deleted:
            return False
        if self.starts_at and self.starts_at > utcnow():
            return False
        if self.ends_at and self.ends_at < utcnow():
            return False
        if self.type == EntitlementType.premium_subscription:
            sku = self.sku
            if sku and not sku.premium:
                return False
            if self.state.user and not self.state.user.premium_type == PremiumType.nitro:
                return False
        return True
    async def subscription(self) -> Optional[Subscription]:
        if not self.subscription_id:
            return
        data = await self.state.http.get_subscription(self.subscription_id)
        return Subscription(data=data, state=self.state)
    async def consume(self) -> None:
        await self.state.http.consume_app_entitlement(self.application_id, self.id)
    async def delete(self) -> None:
        await self.state.http.delete_app_entitlement(self.application_id, self.id)
class Gift:
    __slots__ = (
        'code',
        'expires_at',
        'application_id',
        'batch_id',
        'sku_id',
        'entitlement_branches',
        'gift_style',
        '_flags',
        'max_uses',
        'uses',
        'redeemed',
        'revoked',
        'guild_id',
        'channel_id',
        'store_listing',
        'promotion',
        'subscription_trial',
        'subscription_plan_id',
        'subscription_plan',
        'user',
        'state',
    )
    def __init__(self, *, data: GiftPayload, state: ConnectionState) -> None:
        self.state = state
        self._update(data)
    def _update(self, data: GiftPayload) -> None:
        state = self.state
        self.code: str = data['code']
        self.expires_at: Optional[datetime] = parse_time(data.get('expires_at'))
        self.application_id: Optional[int] = _get_as_snowflake(data, 'application_id')
        self.batch_id: Optional[int] = _get_as_snowflake(data, 'batch_id')
        self.subscription_plan_id: Optional[int] = _get_as_snowflake(data, 'subscription_plan_id')
        self.sku_id: int = int(data['sku_id'])
        self.entitlement_branches: List[int] = [int(x) for x in data.get('entitlement_branches', [])]
        self.gift_style: Optional[GiftStyle] = try_enum(GiftStyle, data['gift_style']) if data.get('gift_style') else None
        self._flags: int = data.get('flags', 0)
        self.max_uses: int = data.get('max_uses', 0)
        self.uses: int = data.get('uses', 0)
        self.redeemed: bool = data.get('redeemed', False)
        self.revoked: bool = data.get('revoked', False)
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.channel_id: Optional[int] = _get_as_snowflake(data, 'channel_id')
        self.store_listing: Optional[StoreListing] = (
            StoreListing(data=data['store_listing'], state=state) if 'store_listing' in data else None
        )
        self.promotion: Optional[Promotion] = Promotion(data=data['promotion'], state=state) if 'promotion' in data else None
        self.subscription_trial: Optional[SubscriptionTrial] = (
            SubscriptionTrial(data['subscription_trial']) if 'subscription_trial' in data else None
        )
        self.subscription_plan: Optional[SubscriptionPlan] = (
            SubscriptionPlan(data=data['subscription_plan'], state=state) if 'subscription_plan' in data else None
        )
        self.user: Optional[User] = self.state.create_user(data['user']) if 'user' in data else None
    def __repr__(self) -> str:
        return f'<Gift code={self.code!r} sku_id={self.sku_id} uses={self.uses} max_uses={self.max_uses} redeemed={self.redeemed}>'
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Gift) and other.code == self.code
    def __ne__(self, other: Any) -> bool:
        if isinstance(other, Gift):
            return other.code != self.code
        return True
    def __hash__(self) -> int:
        return hash(self.code)
    @property
    def id(self) -> str:
        return self.code
    @property
    def url(self) -> str:
        return f'https://discord.gift/{self.code}'
    @property
    def remaining_uses(self) -> int:
        return self.max_uses - self.uses
    @property
    def flags(self) -> GiftFlags:
        return GiftFlags._from_value(self._flags)
    @property
    def premium_type(self) -> Optional[PremiumType]:
        return PremiumType.from_sku_id(self.sku_id) if self.is_subscription() else None
    def is_claimed(self) -> bool:
        return self.uses >= self.max_uses if self.max_uses else False
    def is_expired(self) -> bool:
        return self.expires_at < utcnow() if self.expires_at else False
    def is_subscription(self) -> bool:
        return self.subscription_plan_id is not None
    def is_premium_subscription(self) -> bool:
        return self.is_subscription() and self.application_id == self.state.premium_subscriptions_application.id
    async def redeem(
        self,
        payment_source: Optional[Snowflake] = None,
        *,
        channel: Optional[Snowflake] = None,
        gateway_checkout_context: Optional[str] = None,
    ) -> Entitlement:
        data = await self._state.http.redeem_gift(
            self.code,
            payment_source.id if payment_source else None,
            channel.id if channel else None,
            gateway_checkout_context,
        )
        return Entitlement(data=data, state=self._state)
    async def delete(self) -> None:
        await self._state.http.delete_gift(self.code)
class GiftBatch(Hashable):
    __slots__ = (
        'id',
        'application_id',
        'sku_id',
        'amount',
        'description',
        'entitlement_branches',
        'entitlement_starts_at',
        'entitlement_ends_at',
        '_state',
    )
    def __init__(self, *, data: GiftBatchPayload, state: ConnectionState, application_id: int) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.application_id = application_id
        self.sku_id: int = int(data['sku_id'])
        self.amount: int = data['amount']
        self.description: str = data.get('description', '')
        self.entitlement_branches: List[int] = [int(branch) for branch in data.get('entitlement_branches', [])]
        self.entitlement_starts_at: Optional[datetime] = parse_time(data.get('entitlement_starts_at'))
        self.entitlement_ends_at: Optional[datetime] = parse_time(data.get('entitlement_ends_at'))
    def __repr__(self) -> str:
        return f'<GiftBatch id={self.id} sku_id={self.sku_id} amount={self.amount} description={self.description!r}>'
    def __str__(self) -> str:
        return self.description
    def is_valid(self) -> bool:
        if self.entitlement_starts_at and self.entitlement_starts_at > utcnow():
            return False
        if self.entitlement_ends_at and self.entitlement_ends_at < utcnow():
            return False
        return True
    async def download(self) -> bytes:
        return await self._state.http.get_gift_batch_csv(self.application_id, self.id)