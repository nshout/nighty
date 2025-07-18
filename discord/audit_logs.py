from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Mapping, Generator, List, Optional, Tuple, Type, TypeVar, Union
from . import enums, flags, utils
from .asset import Asset
from .colour import Colour
from .invite import Invite
from .mixins import Hashable
from .object import Object
from .permissions import PermissionOverwrite, Permissions
from .automod import AutoModTrigger, AutoModRuleAction, AutoModPresets, AutoModRule
from .role import Role
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .member import Member
from .scheduled_event import ScheduledEvent
from .stage_instance import StageInstance
from .sticker import GuildSticker
from .threads import Thread
from .channel import ForumChannel, StageChannel, ForumTag
__all__ = (
    'AuditLogDiff',
    'AuditLogChanges',
    'AuditLogEntry',
)
if TYPE_CHECKING:
    import datetime
    from . import abc
    from .guild import Guild
    from .state import ConnectionState
    from .types.audit_log import (
        AuditLogChange as AuditLogChangePayload,
        AuditLogEntry as AuditLogEntryPayload,
    )
    from .types.channel import (
        PermissionOverwrite as PermissionOverwritePayload,
        ForumTag as ForumTagPayload,
        DefaultReaction as DefaultReactionPayload,
    )
    from .types.invite import Invite as InvitePayload
    from .types.role import Role as RolePayload
    from .types.snowflake import Snowflake
    from .types.automod import AutoModerationTriggerMetadata, AutoModerationAction
    from .user import User
    from .webhook import Webhook
    TargetType = Union[
        Guild,
        abc.GuildChannel,
        Member,
        User,
        Role,
        Invite,
        Emoji,
        StageInstance,
        GuildSticker,
        Thread,
        Object,
        AutoModRule,
        ScheduledEvent,
        Webhook,
        None,
    ]
def _transform_timestamp(entry: AuditLogEntry, data: Optional[str]) -> Optional[datetime.datetime]:
    return utils.parse_time(data)
def _transform_color(entry: AuditLogEntry, data: int) -> Colour:
    return Colour(data)
def _transform_snowflake(entry: AuditLogEntry, data: Snowflake) -> int:
    return int(data)
def _transform_channel(entry: AuditLogEntry, data: Optional[Snowflake]) -> Optional[Union[abc.GuildChannel, Object]]:
    if data is None:
        return None
    return entry.guild.get_channel(int(data)) or Object(id=data)
def _transform_channels_or_threads(
    entry: AuditLogEntry, data: List[Snowflake]
) -> List[Union[abc.GuildChannel, Thread, Object]]:
    return [entry.guild.get_channel_or_thread(int(data)) or Object(id=data) for data in data]
def _transform_member_id(entry: AuditLogEntry, data: Optional[Snowflake]) -> Union[Member, User, None]:
    if data is None:
        return None
    return entry._get_member(int(data))
def _transform_guild_id(entry: AuditLogEntry, data: Optional[Snowflake]) -> Optional[Guild]:
    if data is None:
        return None
    return entry.state._get_guild(int(data))
def _transform_roles(entry: AuditLogEntry, data: List[Snowflake]) -> List[Union[Role, Object]]:
    return [entry.guild.get_role(int(role_id)) or Object(role_id, type=Role) for role_id in data]
def _transform_applied_forum_tags(entry: AuditLogEntry, data: List[Snowflake]) -> List[Union[ForumTag, Object]]:
    thread = entry.target
    if isinstance(thread, Thread) and isinstance(thread.parent, ForumChannel):
        return [thread.parent.get_tag(tag_id) or Object(id=tag_id, type=ForumTag) for tag_id in map(int, data)]
    return [Object(id=tag_id, type=ForumTag) for tag_id in data]
def _transform_overloaded_flags(entry: AuditLogEntry, data: int) -> Union[int, flags.ChannelFlags]:
    channel_audit_log_types = (
        enums.AuditLogAction.channel_create,
        enums.AuditLogAction.channel_update,
        enums.AuditLogAction.channel_delete,
        enums.AuditLogAction.thread_create,
        enums.AuditLogAction.thread_update,
        enums.AuditLogAction.thread_delete,
    )
    if entry.action in channel_audit_log_types:
        return flags.ChannelFlags._from_value(data)
    return data
def _transform_forum_tags(entry: AuditLogEntry, data: List[ForumTagPayload]) -> List[ForumTag]:
    return [ForumTag.from_data(state=entry.state, data=d, channel_id=entry.id) for d in data]
def _transform_default_reaction(entry: AuditLogEntry, data: DefaultReactionPayload) -> Optional[PartialEmoji]:
    if data is None:
        return None
    emoji_name = data.get('emoji_name') or ''
    emoji_id = utils._get_as_snowflake(data, 'emoji_id') or None
    return PartialEmoji.with_state(state=entry.state, name=emoji_name, id=emoji_id)
def _transform_overwrites(
    entry: AuditLogEntry, data: List[PermissionOverwritePayload]
) -> List[Tuple[Object, PermissionOverwrite]]:
    overwrites = []
    for elem in data:
        allow = Permissions(int(elem['allow']))
        deny = Permissions(int(elem['deny']))
        ow = PermissionOverwrite.from_pair(allow, deny)
        ow_type = elem['type']
        ow_id = int(elem['id'])
        target = None
        if ow_type == '0':
            target = entry.guild.get_role(ow_id)
        elif ow_type == '1':
            target = entry._get_member(ow_id)
        if target is None:
            target = Object(id=ow_id, type=Role if ow_type == '0' else Member)
        overwrites.append((target, ow))
    return overwrites
def _transform_icon(entry: AuditLogEntry, data: Optional[str]) -> Optional[Asset]:
    if data is None:
        return None
    if entry.action is enums.AuditLogAction.guild_update:
        return Asset._from_guild_icon(entry.state, entry.guild.id, data)
    else:
        return Asset._from_icon(entry.state, entry._target_id, data, path='role')
def _transform_avatar(entry: AuditLogEntry, data: Optional[str]) -> Optional[Asset]:
    if data is None:
        return None
    return Asset._from_avatar(entry.state, entry._target_id, data)
def _transform_cover_image(entry: AuditLogEntry, data: Optional[str]) -> Optional[Asset]:
    if data is None:
        return None
    return Asset._from_scheduled_event_cover_image(entry.state, entry._target_id, data)
def _guild_hash_transformer(path: str) -> Callable[[AuditLogEntry, Optional[str]], Optional[Asset]]:
    def _transform(entry: AuditLogEntry, data: Optional[str]) -> Optional[Asset]:
        if data is None:
            return None
        return Asset._from_guild_image(entry.state, entry.guild.id, data, path=path)
    return _transform
def _transform_automod_trigger_metadata(
    entry: AuditLogEntry, data: AutoModerationTriggerMetadata
) -> Optional[AutoModTrigger]:
    if isinstance(entry.target, AutoModRule):
        try:
            return AutoModTrigger.from_data(type=entry.target.trigger.type.value, data=data)
        except Exception:
            pass
    if 'presets' in data:
        return AutoModTrigger(
            type=enums.AutoModRuleTriggerType.keyword_preset,
            presets=AutoModPresets._from_value(data['presets']),
            allow_list=data.get('allow_list'),
        )
    elif 'keyword_filter' in data:
        return AutoModTrigger(
            type=enums.AutoModRuleTriggerType.keyword,
            keyword_filter=data['keyword_filter'],
            allow_list=data.get('allow_list'),
            regex_patterns=data.get('regex_patterns'),
        )
    elif 'mention_total_limit' in data:
        return AutoModTrigger(type=enums.AutoModRuleTriggerType.mention_spam, mention_limit=data['mention_total_limit'])
    else:
        return AutoModTrigger(type=enums.AutoModRuleTriggerType.spam)
def _transform_automod_actions(entry: AuditLogEntry, data: List[AutoModerationAction]) -> List[AutoModRuleAction]:
    return [AutoModRuleAction.from_data(action) for action in data]
E = TypeVar('E', bound=enums.Enum)
def _enum_transformer(enum: Type[E]) -> Callable[[AuditLogEntry, int], E]:
    def _transform(entry: AuditLogEntry, data: int) -> E:
        return enums.try_enum(enum, data)
    return _transform
F = TypeVar('F', bound=flags.BaseFlags)
def _flag_transformer(cls: Type[F]) -> Callable[[AuditLogEntry, Union[int, str]], F]:
    def _transform(entry: AuditLogEntry, data: Union[int, str]) -> F:
        return cls._from_value(int(data))
    return _transform
def _transform_type(
    entry: AuditLogEntry, data: Union[int, str]
) -> Union[enums.ChannelType, enums.StickerType, enums.WebhookType, str]:
    if entry.action.name.startswith('sticker_'):
        return enums.try_enum(enums.StickerType, data)
    elif entry.action.name.startswith('integration_'):
        return data
    elif entry.action.name.startswith('webhook_'):
        return enums.try_enum(enums.WebhookType, data)
    else:
        return enums.try_enum(enums.ChannelType, data)
class AuditLogDiff:
    def __len__(self) -> int:
        return len(self.__dict__)
    def __iter__(self) -> Generator[Tuple[str, Any], None, None]:
        yield from self.__dict__.items()
    def __repr__(self) -> str:
        values = ' '.join('%s=%r' % item for item in self.__dict__.items())
        return f'<AuditLogDiff {values}>'
    if TYPE_CHECKING:
        def __getattr__(self, item: str) -> Any:
            ...
        def __setattr__(self, key: str, value: Any) -> Any:
            ...
Transformer = Callable[["AuditLogEntry", Any], Any]
class AuditLogChanges:
    TRANSFORMERS: ClassVar[Mapping[str, Tuple[Optional[str], Optional[Transformer]]]] = {
        'verification_level':                    (None, _enum_transformer(enums.VerificationLevel)),
        'explicit_content_filter':               (None, _enum_transformer(enums.ContentFilter)),
        'allow':                                 (None, _flag_transformer(Permissions)),
        'deny':                                  (None, _flag_transformer(Permissions)),
        'permissions':                           (None, _flag_transformer(Permissions)),
        'id':                                    (None, _transform_snowflake),
        'color':                                 ('colour', _transform_color),
        'owner_id':                              ('owner', _transform_member_id),
        'inviter_id':                            ('inviter', _transform_member_id),
        'channel_id':                            ('channel', _transform_channel),
        'afk_channel_id':                        ('afk_channel', _transform_channel),
        'system_channel_id':                     ('system_channel', _transform_channel),
        'system_channel_flags':                  (None, _flag_transformer(flags.SystemChannelFlags)),
        'widget_channel_id':                     ('widget_channel', _transform_channel),
        'rules_channel_id':                      ('rules_channel', _transform_channel),
        'public_updates_channel_id':             ('public_updates_channel', _transform_channel),
        'permission_overwrites':                 ('overwrites', _transform_overwrites),
        'splash_hash':                           ('splash', _guild_hash_transformer('splashes')),
        'banner_hash':                           ('banner', _guild_hash_transformer('banners')),
        'discovery_splash_hash':                 ('discovery_splash', _guild_hash_transformer('discovery-splashes')),
        'icon_hash':                             ('icon', _transform_icon),
        'avatar_hash':                           ('avatar', _transform_avatar),
        'rate_limit_per_user':                   ('slowmode_delay', None),
        'default_thread_rate_limit_per_user':    ('default_thread_slowmode_delay', None),
        'guild_id':                              ('guild', _transform_guild_id),
        'tags':                                  ('emoji', None),
        'default_message_notifications':         ('default_notifications', _enum_transformer(enums.NotificationLevel)),
        'video_quality_mode':                    (None, _enum_transformer(enums.VideoQualityMode)),
        'privacy_level':                         (None, _enum_transformer(enums.PrivacyLevel)),
        'format_type':                           (None, _enum_transformer(enums.StickerFormatType)),
        'type':                                  (None, _transform_type),
        'communication_disabled_until':          ('timed_out_until', _transform_timestamp),
        'expire_behavior':                       (None, _enum_transformer(enums.ExpireBehaviour)),
        'mfa_level':                             (None, _enum_transformer(enums.MFALevel)),
        'status':                                (None, _enum_transformer(enums.EventStatus)),
        'entity_type':                           (None, _enum_transformer(enums.EntityType)),
        'preferred_locale':                      (None, _enum_transformer(enums.Locale)),
        'image_hash':                            ('cover_image', _transform_cover_image),
        'trigger_type':                          (None, _enum_transformer(enums.AutoModRuleTriggerType)),
        'event_type':                            (None, _enum_transformer(enums.AutoModRuleEventType)),
        'trigger_metadata':                      ('trigger', _transform_automod_trigger_metadata),
        'actions':                               (None, _transform_automod_actions),
        'exempt_channels':                       (None, _transform_channels_or_threads),
        'exempt_roles':                          (None, _transform_roles),
        'applied_tags':                          (None, _transform_applied_forum_tags),
        'available_tags':                        (None, _transform_forum_tags),
        'flags':                                 (None, _transform_overloaded_flags),
        'default_reaction_emoji':                (None, _transform_default_reaction),
    }
    def __init__(self, entry: AuditLogEntry, data: List[AuditLogChangePayload]):
        self.before: AuditLogDiff = AuditLogDiff()
        self.after: AuditLogDiff = AuditLogDiff()
        for elem in data:
            attr = elem['key']
            if attr == '$add':
                self._handle_role(self.before, self.after, entry, elem['new_value'])
                continue
            elif attr == '$remove':
                self._handle_role(self.after, self.before, entry, elem['new_value'])
                continue
            try:
                key, transformer = self.TRANSFORMERS[attr]
            except (ValueError, KeyError):
                transformer = None
            else:
                if key:
                    attr = key
            transformer: Optional[Transformer]
            try:
                before = elem['old_value']
            except KeyError:
                before = None
            else:
                if transformer:
                    before = transformer(entry, before)
            setattr(self.before, attr, before)
            try:
                after = elem['new_value']
            except KeyError:
                after = None
            else:
                if transformer:
                    after = transformer(entry, after)
            setattr(self.after, attr, after)
        if hasattr(self.after, 'colour'):
            self.after.color = self.after.colour
            self.before.color = self.before.colour
        if hasattr(self.after, 'expire_behavior'):
            self.after.expire_behaviour = self.after.expire_behavior
            self.before.expire_behaviour = self.before.expire_behavior
    def __repr__(self) -> str:
        return f'<AuditLogChanges before={self.before!r} after={self.after!r}>'
    def _handle_role(self, first: AuditLogDiff, second: AuditLogDiff, entry: AuditLogEntry, elem: List[RolePayload]) -> None:
        if not hasattr(first, 'roles'):
            setattr(first, 'roles', [])
        data = []
        g: Guild = entry.guild
        for e in elem:
            role_id = int(e['id'])
            role = g.get_role(role_id)
            if role is None:
                role = Object(id=role_id, type=Role)
                role.name = e['name']
            data.append(role)
        setattr(second, 'roles', data)
class _AuditLogProxy:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
class _AuditLogProxyMemberPrune(_AuditLogProxy):
    delete_member_days: int
    members_removed: int
class _AuditLogProxyMemberMoveOrMessageDelete(_AuditLogProxy):
    channel: Union[abc.GuildChannel, Thread]
    count: int
class _AuditLogProxyMemberDisconnect(_AuditLogProxy):
    count: int
class _AuditLogProxyPinAction(_AuditLogProxy):
    channel: Union[abc.GuildChannel, Thread]
    message_id: int
class _AuditLogProxyStageInstanceAction(_AuditLogProxy):
    channel: abc.GuildChannel
class _AuditLogProxyMessageBulkDelete(_AuditLogProxy):
    count: int
class _AuditLogProxyAutoModAction(_AuditLogProxy):
    automod_rule_name: str
    automod_rule_trigger_type: str
    channel: Optional[Union[abc.GuildChannel, Thread]]
class AuditLogEntry(Hashable):
    r
    def __init__(
        self,
        *,
        users: Mapping[int, User],
        automod_rules: Mapping[int, AutoModRule],
        webhooks: Mapping[int, Webhook],
        data: AuditLogEntryPayload,
        guild: Guild,
    ):
        self.state: ConnectionState = guild.state
        self.guild: Guild = guild
        self._users: Mapping[int, User] = users
        self._automod_rules: Mapping[int, AutoModRule] = automod_rules
        self._webhooks: Mapping[int, Webhook] = webhooks
        self._from_data(data)
    def _from_data(self, data: AuditLogEntryPayload) -> None:
        self.action: enums.AuditLogAction = enums.try_enum(enums.AuditLogAction, data['action_type'])
        self.id: int = int(data['id'])
        self.reason: Optional[str] = data.get('reason')
        extra = data.get('options')
        self.extra: Union[
            _AuditLogProxyMemberPrune,
            _AuditLogProxyMemberMoveOrMessageDelete,
            _AuditLogProxyMemberDisconnect,
            _AuditLogProxyPinAction,
            _AuditLogProxyStageInstanceAction,
            _AuditLogProxyMessageBulkDelete,
            _AuditLogProxyAutoModAction,
            Member, User, None,
            Role, Object
        ] = None
        if isinstance(self.action, enums.AuditLogAction) and extra:
            if self.action is enums.AuditLogAction.member_prune:
                self.extra = _AuditLogProxyMemberPrune(
                    delete_member_days=int(extra['delete_member_days']),
                    members_removed=int(extra['members_removed']),
                )
            elif self.action is enums.AuditLogAction.member_move or self.action is enums.AuditLogAction.message_delete:
                channel_id = int(extra['channel_id'])
                self.extra = _AuditLogProxyMemberMoveOrMessageDelete(
                    count=int(extra['count']),
                    channel=self.guild.get_channel_or_thread(channel_id) or Object(id=channel_id),
                )
            elif self.action is enums.AuditLogAction.member_disconnect:
                self.extra = _AuditLogProxyMemberDisconnect(count=int(extra['count']))
            elif self.action is enums.AuditLogAction.message_bulk_delete:
                self.extra = _AuditLogProxyMessageBulkDelete(count=int(extra['count']))
            elif self.action.name.endswith('pin'):
                channel_id = int(extra['channel_id'])
                self.extra = _AuditLogProxyPinAction(
                    channel=self.guild.get_channel_or_thread(channel_id) or Object(id=channel_id),
                    message_id=int(extra['message_id']),
                )
            elif (
                self.action is enums.AuditLogAction.automod_block_message
                or self.action is enums.AuditLogAction.automod_flag_message
                or self.action is enums.AuditLogAction.automod_timeout_member
            ):
                channel_id = utils._get_as_snowflake(extra, 'channel_id')
                channel = None
                if channel_id:
                    channel = self.guild.get_channel_or_thread(channel_id) or Object(id=channel_id)
                self.extra = _AuditLogProxyAutoModAction(
                    automod_rule_name=extra['auto_moderation_rule_name'],
                    automod_rule_trigger_type=enums.try_enum(
                        enums.AutoModRuleTriggerType, extra['auto_moderation_rule_trigger_type']
                    ),
                    channel=channel,
                )
            elif self.action.name.startswith('overwrite_'):
                instance_id = int(extra['id'])
                the_type = extra.get('type')
                if the_type == '1':
                    self.extra = self._get_member(instance_id)
                elif the_type == '0':
                    role = self.guild.get_role(instance_id)
                    if role is None:
                        role = Object(id=instance_id, type=Role)
                        role.name = extra.get('role_name')
                    self.extra = role
            elif self.action.name.startswith('stage_instance'):
                channel_id = int(extra['channel_id'])
                self.extra = _AuditLogProxyStageInstanceAction(
                    channel=self.guild.get_channel(channel_id) or Object(id=channel_id, type=StageChannel)
                )
        self._changes = data.get('changes', [])
        self.user_id: Optional[int] = utils._get_as_snowflake(data, 'user_id')
        self.user: Optional[Union[User, Member]] = self._get_member(self.user_id)
        self._target_id = utils._get_as_snowflake(data, 'target_id')
    def _get_member(self, user_id: Optional[int]) -> Union[Member, User, None]:
        if user_id is None:
            return None
        return self.guild.get_member(user_id) or self._users.get(user_id)
    def __repr__(self) -> str:
        return f'<AuditLogEntry id={self.id} action={self.action} user={self.user!r}>'
    @utils.cached_property
    def created_at(self) -> datetime.datetime:
        return utils.snowflake_time(self.id)
    @utils.cached_property
    def target(self) -> TargetType:
        if self.action.target_type is None:
            return None
        try:
            converter = getattr(self, '_convert_target_' + self.action.target_type)
        except AttributeError:
            if self._target_id is None:
                return None
            return Object(id=self._target_id)
        else:
            return converter(self._target_id)
    @utils.cached_property
    def category(self) -> Optional[enums.AuditLogActionCategory]:
        return self.action.category
    @utils.cached_property
    def changes(self) -> AuditLogChanges:
        obj = AuditLogChanges(self, self._changes)
        del self._changes
        return obj
    @utils.cached_property
    def before(self) -> AuditLogDiff:
        return self.changes.before
    @utils.cached_property
    def after(self) -> AuditLogDiff:
        return self.changes.after
    def _convert_target_guild(self, target_id: int) -> Guild:
        return self.guild
    def _convert_target_channel(self, target_id: int) -> Union[abc.GuildChannel, Object]:
        return self.guild.get_channel(target_id) or Object(id=target_id)
    def _convert_target_user(self, target_id: Optional[int]) -> Optional[Union[Member, User, Object]]:
        if target_id is None:
            return None
        return self._get_member(target_id) or Object(id=target_id, type=Member)
    def _convert_target_role(self, target_id: int) -> Union[Role, Object]:
        return self.guild.get_role(target_id) or Object(id=target_id, type=Role)
    def _convert_target_invite(self, target_id: None) -> Invite:
        changeset = self.before if self.action is enums.AuditLogAction.invite_delete else self.after
        fake_payload: InvitePayload = {
            'max_age': changeset.max_age,
            'max_uses': changeset.max_uses,
            'code': changeset.code,
            'temporary': changeset.temporary,
            'uses': changeset.uses,
            'channel': None,
        }
        obj = Invite(state=self.state, data=fake_payload, guild=self.guild, channel=changeset.channel)
        try:
            obj.inviter = changeset.inviter
        except AttributeError:
            pass
        return obj
    def _convert_target_emoji(self, target_id: int) -> Union[Emoji, Object]:
        return self.state.get_emoji(target_id) or Object(id=target_id, type=Emoji)
    def _convert_target_message(self, target_id: int) -> Union[Member, User, Object]:
        return self._get_member(target_id) or Object(id=target_id, type=Member)
    def _convert_target_stage_instance(self, target_id: int) -> Union[StageInstance, Object]:
        return self.guild.get_stage_instance(target_id) or Object(id=target_id, type=StageInstance)
    def _convert_target_sticker(self, target_id: int) -> Union[GuildSticker, Object]:
        return self.state.get_sticker(target_id) or Object(id=target_id, type=GuildSticker)
    def _convert_target_thread(self, target_id: int) -> Union[Thread, Object]:
        return self.guild.get_thread(target_id) or Object(id=target_id, type=Thread)
    def _convert_target_guild_scheduled_event(self, target_id: int) -> Union[ScheduledEvent, Object]:
        return self.guild.get_scheduled_event(target_id) or Object(id=target_id, type=ScheduledEvent)
    def _convert_target_auto_moderation(self, target_id: int) -> Union[AutoModRule, Object]:
        return self._automod_rules.get(target_id) or Object(target_id, type=AutoModRule)
    def _convert_target_webhook(self, target_id: int) -> Union[Webhook, Object]:
        from .webhook import Webhook
        return self._webhooks.get(target_id) or Object(target_id, type=Webhook)