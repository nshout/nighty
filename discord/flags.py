from __future__ import annotations
from functools import reduce
from operator import or_
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    overload,
)
from .enums import UserFlags
if TYPE_CHECKING:
    from typing_extensions import Self
__all__ = (
    'Capabilities',
    'SystemChannelFlags',
    'MessageFlags',
    'PublicUserFlags',
    'PrivateUserFlags',
    'MemberCacheFlags',
    'ApplicationFlags',
    'ChannelFlags',
    'PremiumUsageFlags',
    'PurchasedFlags',
    'PaymentSourceFlags',
    'SKUFlags',
    'PaymentFlags',
    'PromotionFlags',
    'GiftFlags',
    'LibraryApplicationFlags',
    'ApplicationDiscoveryFlags',
    'FriendSourceFlags',
    'FriendDiscoveryFlags',
    'HubProgressFlags',
    'OnboardingProgressFlags',
    'AutoModPresets',
    'MemberFlags',
    'ReadStateFlags',
    'InviteFlags',
    'AttachmentFlags',
)
BF = TypeVar('BF', bound='BaseFlags')
class flag_value:
    def __init__(self, func: Callable[[Any], int]):
        self.flag: int = func(None)
        self.__doc__: Optional[str] = func.__doc__
    @overload
    def __get__(self, instance: None, owner: Type[BF]) -> Self:
        ...
    @overload
    def __get__(self, instance: BF, owner: Type[BF]) -> bool:
        ...
    def __get__(self, instance: Optional[BF], owner: Type[BF]) -> Any:
        if instance is None:
            return self
        return instance._has_flag(self.flag)
    def __set__(self, instance: BaseFlags, value: bool) -> None:
        instance._set_flag(self.flag, value)
    def __repr__(self) -> str:
        return f'<flag_value flag={self.flag!r}>'
class alias_flag_value(flag_value):
    pass
def fill_with_flags(*, inverted: bool = False) -> Callable[[Type[BF]], Type[BF]]:
    def decorator(cls: Type[BF]) -> Type[BF]:
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }
        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2**max_bits)
        else:
            cls.DEFAULT_VALUE = 0
        return cls
    return decorator
class BaseFlags:
    VALID_FLAGS: ClassVar[Dict[str, int]]
    DEFAULT_VALUE: ClassVar[int]
    value: int
    __slots__ = ('value',)
    def __init__(self, **kwargs: bool):
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
            setattr(self, key, value)
    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self
    def __or__(self, other: Self) -> Self:
        return self._from_value(self.value | other.value)
    def __and__(self, other: Self) -> Self:
        return self._from_value(self.value & other.value)
    def __xor__(self, other: Self) -> Self:
        return self._from_value(self.value ^ other.value)
    def __ior__(self, other: Self) -> Self:
        self.value |= other.value
        return self
    def __iand__(self, other: Self) -> Self:
        self.value &= other.value
        return self
    def __ixor__(self, other: Self) -> Self:
        self.value ^= other.value
        return self
    def __invert__(self) -> Self:
        max_bits = max(self.VALID_FLAGS.values()).bit_length()
        max_value = -1 + (2**max_bits)
        return self._from_value(self.value ^ max_value)
    def __bool__(self) -> bool:
        return self.value != self.DEFAULT_VALUE
    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return hash(self.value)
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} value={self.value}>'
    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, alias_flag_value):
                continue
            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))
    def _has_flag(self, o: int) -> bool:
        return (self.value & o) == o
    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError(f'Value to set for {self.__class__.__name__} must be a bool.')
class ArrayFlags(BaseFlags):
    @classmethod
    def _from_value(cls: Type[Self], value: Sequence[int]) -> Self:
        self = cls.__new__(cls)
        self.value = reduce(or_, map((1).__lshift__, value), 0) >> 1
        return self
    def to_array(self) -> List[int]:
        return [i + 1 for i in range(self.value.bit_length()) if self.value & (1 << i)]
@fill_with_flags()
class Capabilities(BaseFlags):
    __slots__ = ()
    @classmethod
    def default(cls: Type[Self]) -> Self:
        return cls(
            lazy_user_notes=True,
            versioned_read_states=True,
            versioned_user_guild_settings=True,
            dedupe_user_objects=True,
            prioritized_ready_payload=True,
            multiple_guild_experiment_populations=True,
            non_channel_read_states=True,
            auth_token_refresh=True,
            user_settings_proto=True,
            client_state_v2=True,
            passive_guild_update=True,
            auto_call_connect=True,
        )
    @flag_value
    def lazy_user_notes(self):
        return 1 << 0
    @flag_value
    def no_affine_user_ids(self):
        return 1 << 1
    @flag_value
    def versioned_read_states(self):
        return 1 << 2
    @flag_value
    def versioned_user_guild_settings(self):
        return 1 << 3
    @flag_value
    def dedupe_user_objects(self):
        return 1 << 4
    @flag_value
    def prioritized_ready_payload(self):
        return 1 << 5 | 1 << 4
    @flag_value
    def multiple_guild_experiment_populations(self):
        return 1 << 6
    @flag_value
    def non_channel_read_states(self):
        return 1 << 7
    @flag_value
    def auth_token_refresh(self):
        return 1 << 8
    @flag_value
    def user_settings_proto(self):
        return 1 << 9
    @flag_value
    def client_state_v2(self):
        return 1 << 10
    @flag_value
    def passive_guild_update(self):
        return 1 << 11
    @flag_value
    def auto_call_connect(self):
        return 1 << 12
    @flag_value
    def debounce_message_reactions(self):
        return 1 << 13
@fill_with_flags(inverted=True)
class SystemChannelFlags(BaseFlags):
    r
    __slots__ = ()
    def _has_flag(self, o: int) -> bool:
        return (self.value & o) != o
    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value &= ~o
        elif toggle is False:
            self.value |= o
        else:
            raise TypeError('Value to set for SystemChannelFlags must be a bool')
    @flag_value
    def join_notifications(self):
        return 1
    @flag_value
    def premium_subscriptions(self):
        return 2
    @flag_value
    def guild_reminder_notifications(self):
        return 4
    @flag_value
    def join_notification_replies(self):
        return 8
    @flag_value
    def role_subscription_purchase_notifications(self):
        return 16
    @flag_value
    def role_subscription_purchase_notification_replies(self):
        return 32
@fill_with_flags()
class MessageFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def crossposted(self):
        return 1
    @flag_value
    def is_crossposted(self):
        return 2
    @flag_value
    def suppress_embeds(self):
        return 4
    @flag_value
    def source_message_deleted(self):
        return 8
    @flag_value
    def urgent(self):
        return 16
    @flag_value
    def has_thread(self):
        return 32
    @flag_value
    def ephemeral(self):
        return 64
    @flag_value
    def loading(self):
        return 128
    @flag_value
    def failed_to_mention_some_roles_in_thread(self):
        return 256
    @flag_value
    def link_not_discord_warning(self):
        return 1024
    @flag_value
    def suppress_notifications(self):
        return 4096
    @alias_flag_value
    def silent(self):
        return 4096
    @flag_value
    def voice(self):
        return 8192
@fill_with_flags()
class PublicUserFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def staff(self):
        return UserFlags.staff.value
    @flag_value
    def partner(self):
        return UserFlags.partner.value
    @flag_value
    def hypesquad(self):
        return UserFlags.hypesquad.value
    @flag_value
    def bug_hunter(self):
        return UserFlags.bug_hunter.value
    @alias_flag_value
    def bug_hunter_level_1(self):
        return UserFlags.bug_hunter_level_1.value
    @flag_value
    def hypesquad_bravery(self):
        return UserFlags.hypesquad_bravery.value
    @flag_value
    def hypesquad_brilliance(self):
        return UserFlags.hypesquad_brilliance.value
    @flag_value
    def hypesquad_balance(self):
        return UserFlags.hypesquad_balance.value
    @flag_value
    def early_supporter(self):
        return UserFlags.early_supporter.value
    @flag_value
    def team_user(self):
        return UserFlags.team_user.value
    @flag_value
    def system(self):
        return UserFlags.system.value
    @flag_value
    def bug_hunter_level_2(self):
        return UserFlags.bug_hunter_level_2.value
    @flag_value
    def verified_bot(self):
        return UserFlags.verified_bot.value
    @flag_value
    def verified_bot_developer(self):
        return UserFlags.verified_bot_developer.value
    @alias_flag_value
    def early_verified_bot_developer(self):
        return UserFlags.verified_bot_developer.value
    @flag_value
    def discord_certified_moderator(self):
        return UserFlags.discord_certified_moderator.value
    @flag_value
    def bot_http_interactions(self):
        return UserFlags.bot_http_interactions.value
    @flag_value
    def spammer(self):
        return UserFlags.spammer.value
    @flag_value
    def active_developer(self):
        return UserFlags.active_developer.value
    def all(self) -> List[UserFlags]:
        return [public_flag for public_flag in UserFlags if self._has_flag(public_flag.value)]
@fill_with_flags()
class PrivateUserFlags(PublicUserFlags):
    r
    __slots__ = ()
    @flag_value
    def premium_promo_dismissed(self):
        return UserFlags.premium_promo_dismissed.value
    @flag_value
    def has_unread_urgent_messages(self):
        return UserFlags.has_unread_urgent_messages.value
    @flag_value
    def mfa_sms(self):
        return UserFlags.mfa_sms.value
    @flag_value
    def underage_deleted(self):
        return UserFlags.underage_deleted.value
    @flag_value
    def partner_or_verification_application(self):
        return UserFlags.partner_or_verification_application.value
    @flag_value
    def disable_premium(self):
        return UserFlags.disable_premium.value
    @flag_value
    def quarantined(self):
        return UserFlags.quarantined.value
@fill_with_flags()
class PremiumUsageFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def premium_discriminator(self):
        return 1 << 0
    @flag_value
    def animated_avatar(self):
        return 1 << 1
    @flag_value
    def profile_banner(self):
        return 1 << 2
@fill_with_flags()
class PurchasedFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def nitro_classic(self):
        return 1 << 0
    @flag_value
    def nitro(self):
        return 1 << 1
    @flag_value
    def guild_boost(self):
        return 1 << 2
    @flag_value
    def nitro_basic(self):
        return 1 << 3
@fill_with_flags()
class MemberCacheFlags(BaseFlags):
    __slots__ = ()
    def __init__(self, **kwargs: bool):
        bits = max(self.VALID_FLAGS.values()).bit_length()
        self.value: int = (1 << bits) - 1
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
            setattr(self, key, value)
    @classmethod
    def all(cls: Type[MemberCacheFlags]) -> MemberCacheFlags:
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = (1 << bits) - 1
        self = cls.__new__(cls)
        self.value = value
        return self
    @classmethod
    def none(cls: Type[MemberCacheFlags]) -> MemberCacheFlags:
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self
    @property
    def _empty(self):
        return self.value == self.DEFAULT_VALUE
    @flag_value
    def voice(self):
        return 1
    @flag_value
    def joined(self):
        return 2
    @alias_flag_value
    def other(self):
        return 2
    @property
    def _voice_only(self):
        return self.value == 1
@fill_with_flags()
class ApplicationFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def managed_emoji(self):
        return 1 << 2
    @flag_value
    def embedded_iap(self):
        return 1 << 3
    @flag_value
    def group_dm_create(self):
        return 1 << 4
    @flag_value
    def automod_badge(self):
        return 1 << 6
    @flag_value
    def gateway_presence(self):
        return 1 << 12
    @flag_value
    def gateway_presence_limited(self):
        return 1 << 13
    @flag_value
    def gateway_guild_members(self):
        return 1 << 14
    @flag_value
    def gateway_guild_members_limited(self):
        return 1 << 15
    @flag_value
    def verification_pending_guild_limit(self):
        return 1 << 16
    @flag_value
    def embedded(self):
        return 1 << 17
    @flag_value
    def gateway_message_content(self):
        return 1 << 18
    @flag_value
    def gateway_message_content_limited(self):
        return 1 << 19
    @flag_value
    def embedded_first_party(self):
        return 1 << 20
    @flag_value
    def application_command_badge(self):
        return 1 << 23
    @flag_value
    def active(self):
        return 1 << 24
@fill_with_flags()
class ChannelFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def pinned(self):
        return 1 << 1
    @flag_value
    def require_tag(self):
        return 1 << 4
@fill_with_flags()
class PaymentSourceFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def new(self):
        return 1 << 0
    @flag_value
    def unknown(self):
        return 1 << 1
@fill_with_flags()
class SKUFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def premium_purchase(self):
        return 1 << 0
    @flag_value
    def free_premium_content(self):
        return 1 << 1
    @flag_value
    def available(self):
        return 1 << 2
    @flag_value
    def premium_and_distribution(self):
        return 1 << 3
    @flag_value
    def sticker_pack(self):
        return 1 << 4
    @flag_value
    def guild_role_subscription(self):
        return 1 << 5
    @flag_value
    def premium_subscription(self):
        return 1 << 6
    @flag_value
    def application_guild_subscription(self):
        return 1 << 7
    @flag_value
    def application_user_subscription(self):
        return 1 << 8
    @flag_value
    def creator_monetization(self):
        return 1 << 9
    @flag_value
    def guild_product(self):
        return 1 << 10
@fill_with_flags()
class PaymentFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def gift(self):
        return 1 << 0
    @flag_value
    def preorder(self):
        return 1 << 3
    @flag_value
    def temporary_authorization(self):
        return 1 << 5
    @flag_value
    def unknown(self):
        return 1 << 6
@fill_with_flags()
class PromotionFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def unknown_0(self):
        return 1 << 0
    @flag_value
    def unknown_1(self):
        return 1 << 1
    @flag_value
    def unknown_2(self):
        return 1 << 2
    @flag_value
    def unknown_3(self):
        return 1 << 3
    @flag_value
    def unknown_4(self):
        return 1 << 4
    @flag_value
    def blocked_ios(self):
        return 1 << 5
    @flag_value
    def outbound_redeemable_by_trial_users(self):
        return 1 << 6
@fill_with_flags()
class GiftFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def payment_source_required(self):
        return 1 << 0
    @flag_value
    def existing_subscription_disallowed(self):
        return 1 << 1
    @flag_value
    def not_self_redeemable(self):
        return 1 << 2
    @flag_value
    def promotion(self):
        return 1 << 3
@fill_with_flags()
class LibraryApplicationFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def hidden(self):
        return 1 << 0
    @flag_value
    def private(self):
        return 1 << 1
    @flag_value
    def overlay_disabled(self):
        return 1 << 2
    @flag_value
    def entitled(self):
        return 1 << 3
    @flag_value
    def premium(self):
        return 1 << 4
@fill_with_flags()
class ApplicationDiscoveryFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def verified(self):
        return 1 << 0
    @flag_value
    def tag(self):
        return 1 << 1
    @flag_value
    def description(self):
        return 1 << 2
    @flag_value
    def terms_of_service(self):
        return 1 << 3
    @flag_value
    def privacy_policy(self):
        return 1 << 4
    @flag_value
    def install_params(self):
        return 1 << 5
    @flag_value
    def safe_name(self):
        return 1 << 6
    @flag_value
    def safe_description(self):
        return 1 << 7
    @flag_value
    def approved_commands(self):
        return 1 << 8
    @flag_value
    def support_guild(self):
        return 1 << 9
    @flag_value
    def safe_commands(self):
        return 1 << 10
    @flag_value
    def mfa(self):
        return 1 << 11
    @flag_value
    def safe_directory_overview(self):
        return 1 << 12
    @flag_value
    def supported_locales(self):
        return 1 << 13
    @flag_value
    def safe_short_description(self):
        return 1 << 14
    @flag_value
    def safe_role_connections(self):
        return 1 << 15
    @flag_value
    def eligible(self):
        return 1 << 16
@fill_with_flags()
class FriendSourceFlags(BaseFlags):
    r
    __slots__ = ()
    @classmethod
    def _from_dict(cls, data: dict) -> Self:
        self = cls()
        if data.get('mutual_friends'):
            self.mutual_friends = True
        if data.get('mutual_guilds'):
            self.mutual_guilds = True
        if data.get('all'):
            self.no_relation = True
        return self
    def _to_dict(self) -> dict:
        return {
            'mutual_friends': self.mutual_friends,
            'mutual_guilds': self.mutual_guilds,
            'all': self.no_relation,
        }
    @classmethod
    def none(cls) -> Self:
        return cls()
    @classmethod
    def all(cls) -> Self:
        self = cls()
        self.no_relation = True
        return self
    @flag_value
    def mutual_friends(self):
        return 1 << 1
    @flag_value
    def mutual_guilds(self):
        return 1 << 2
    @flag_value
    def no_relation(self):
        return 1 << 3 | 1 << 2 | 1 << 1
@fill_with_flags()
class FriendDiscoveryFlags(BaseFlags):
    r
    __slots__ = ()
    @classmethod
    def none(cls) -> Self:
        return cls()
    @classmethod
    def all(cls) -> Self:
        self = cls()
        self.find_by_email = True
        self.find_by_phone = True
        return self
    @flag_value
    def find_by_phone(self):
        return 1 << 1
    @flag_value
    def find_by_email(self):
        return 1 << 2
@fill_with_flags()
class HubProgressFlags(BaseFlags):
    __slots__ = ()
    @flag_value
    def join_guild(self):
        return 1 << 0
    @flag_value
    def invite_user(self):
        return 1 << 1
    @flag_value
    def contact_sync(self):
        return 1 << 2
@fill_with_flags()
class OnboardingProgressFlags(BaseFlags):
    __slots__ = ()
    @flag_value
    def notice_shown(self):
        return 1 << 0
    @flag_value
    def notice_cleared(self):
        return 1 << 1
@fill_with_flags()
class AutoModPresets(ArrayFlags):
    r
    __slots__ = ()
    @classmethod
    def all(cls: Type[Self]) -> Self:
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = (1 << bits) - 1
        self = cls.__new__(cls)
        self.value = value
        return self
    @classmethod
    def none(cls: Type[Self]) -> Self:
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self
    @flag_value
    def profanity(self):
        return 1 << 0
    @flag_value
    def sexual_content(self):
        return 1 << 1
    @flag_value
    def slurs(self):
        return 1 << 2
@fill_with_flags()
class MemberFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def did_rejoin(self):
        return 1 << 0
    @flag_value
    def completed_onboarding(self):
        return 1 << 1
    @flag_value
    def bypasses_verification(self):
        return 1 << 2
    @flag_value
    def started_onboarding(self):
        return 1 << 3
    @flag_value
    def guest(self):
        return 1 << 4
@fill_with_flags()
class ReadStateFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def guild_channel(self):
        return 1 << 0
    @flag_value
    def thread(self):
        return 1 << 1
@fill_with_flags()
class InviteFlags(BaseFlags):
    r
    __slots__ = ()
    @flag_value
    def guest(self):
        return 1 << 0
@fill_with_flags()
class AttachmentFlags(BaseFlags):
    r
    @flag_value
    def clip(self):
        return 1 << 0
    @flag_value
    def thumbnail(self):
        return 1 << 1
    @flag_value
    def remix(self):
        return 1 << 2