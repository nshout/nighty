from __future__ import annotations
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional
from .mixins import Hashable
from .subscriptions import Subscription
from .utils import parse_time, utcnow
if TYPE_CHECKING:
    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.subscriptions import (
        PremiumGuildSubscription as PremiumGuildSubscriptionPayload,
        PremiumGuildSubscriptionSlot as PremiumGuildSubscriptionSlotPayload,
        PremiumGuildSubscriptionCooldown as PremiumGuildSubscriptionCooldownPayload,
    )
__all__ = (
    'PremiumGuildSubscription',
    'PremiumGuildSubscriptionSlot',
    'PremiumGuildSubscriptionCooldown',
)
class PremiumGuildSubscription(Hashable):
    def __init__(self, *, state: ConnectionState, data: PremiumGuildSubscriptionPayload):
        self.state = state
        self._update(data)
    def _update(self, data: PremiumGuildSubscriptionPayload):
        state = self.state
        self.id = int(data['id'])
        self.guild_id = int(data['guild_id'])
        self.user_id = int(data['user_id'])
        self.user = state.store_user(data['user']) if 'user' in data else state.user
        self.ended = data.get('ended', False)
        self.ends_at: Optional[datetime] = parse_time(data.get('ends_at'))
    def __repr__(self) -> str:
        return f'<PremiumGuildSubscription id={self.id} guild_id={self.guild_id} user_id={self.user_id} ended={self.ended}>'
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    @property
    def remaining(self) -> Optional[timedelta]:
        if self.ends_at is None or self.ends_at <= utcnow():
            return None
        return self.ends_at - utcnow()
    async def delete(self) -> None:
        await self.state.http.delete_guild_subscription(self.guild_id, self.id)
class PremiumGuildSubscriptionSlot(Hashable):
    __slots__ = (
        'id',
        'subscription_id',
        'canceled',
        'cooldown_ends_at',
        'premium_guild_subscription',
        'state',
    )
    def __init__(self, *, state: ConnectionState, data: PremiumGuildSubscriptionSlotPayload):
        self.state = state
        self._update(data)
    def _update(self, data: PremiumGuildSubscriptionSlotPayload):
        self.id = int(data['id'])
        self.subscription_id = int(data['subscription_id'])
        self.canceled = data.get('canceled', False)
        self.cooldown_ends_at: Optional[datetime] = parse_time(data.get('cooldown_ends_at'))
        premium_guild_subscription = data.get('premium_guild_subscription')
        self.premium_guild_subscription: Optional[PremiumGuildSubscription] = (
            PremiumGuildSubscription(state=self.state, data=premium_guild_subscription)
            if premium_guild_subscription is not None
            else None
        )
    def __repr__(self) -> str:
        return f'<PremiumGuildSubscriptionSlot id={self.id} subscription_id={self.subscription_id} canceled={self.canceled}>'
    def is_available(self) -> bool:
        return not self.premium_guild_subscription and not self.is_on_cooldown()
    def is_on_cooldown(self) -> bool:
        return self.cooldown_ends_at is not None and self.cooldown_ends_at > utcnow()
    @property
    def cancelled(self) -> bool:
        return self.canceled
    @property
    def cooldown_remaining(self) -> Optional[timedelta]:
        if self.cooldown_ends_at is None or self.cooldown_ends_at <= utcnow():
            return None
        return self.cooldown_ends_at - utcnow()
    async def subscription(self) -> Subscription:
        data = await self.state.http.get_subscription(self.subscription_id)
        return Subscription(data=data, state=self.state)
    async def apply(self, guild: Snowflake) -> PremiumGuildSubscription:
        state = self.state
        data = await state.http.apply_guild_subscription_slots(guild.id, (self.id,))
        return PremiumGuildSubscription(state=state, data=data[0])
    async def cancel(self) -> None:
        data = await self.state.http.cancel_guild_subscription_slot(self.id)
        self._update(data)
    async def uncancel(self) -> None:
        data = await self.state.http.uncancel_guild_subscription_slot(self.id)
        self._update(data)
class PremiumGuildSubscriptionCooldown:
    def __init__(self, *, state: ConnectionState, data: PremiumGuildSubscriptionCooldownPayload):
        self.state = state
        self._update(data)
    def _update(self, data: PremiumGuildSubscriptionCooldownPayload):
        self.ends_at: datetime = parse_time(data['ends_at'])
        self.limit = data['limit']
        self.remaining = data.get('remaining', 0)