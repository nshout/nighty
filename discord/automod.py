from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, List, Set, Union, Sequence, overload
from .enums import AutoModRuleTriggerType, AutoModRuleActionType, AutoModRuleEventType, try_enum
from .flags import AutoModPresets
from . import utils
from .utils import MISSING, cached_slot_property
if TYPE_CHECKING:
    from typing_extensions import Self
    from .abc import Snowflake, GuildChannel
    from .threads import Thread
    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .types.automod import (
        AutoModerationRule as AutoModerationRulePayload,
        AutoModerationTriggerMetadata as AutoModerationTriggerMetadataPayload,
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationActionExecution as AutoModerationActionExecutionPayload,
    )
    from .role import Role
__all__ = (
    'AutoModRuleAction',
    'AutoModTrigger',
    'AutoModRule',
    'AutoModAction',
)
class AutoModRuleAction:
    __slots__ = ('type', 'channel_id', 'duration', 'custom_message')
    @overload
    def __init__(self, *, channel_id: Optional[int] = ...) -> None:
        ...
    @overload
    def __init__(self, *, duration: Optional[datetime.timedelta] = ...) -> None:
        ...
    @overload
    def __init__(self, *, custom_message: Optional[str] = ...) -> None:
        ...
    def __init__(
        self,
        *,
        channel_id: Optional[int] = None,
        duration: Optional[datetime.timedelta] = None,
        custom_message: Optional[str] = None,
    ) -> None:
        self.channel_id: Optional[int] = channel_id
        self.duration: Optional[datetime.timedelta] = duration
        self.custom_message: Optional[str] = custom_message
        if sum(v is None for v in (channel_id, duration, custom_message)) < 2:
            raise ValueError('Only one of channel_id, duration, or custom_message can be passed.')
        self.type: AutoModRuleActionType = AutoModRuleActionType.block_message
        if channel_id:
            self.type = AutoModRuleActionType.send_alert_message
        elif duration:
            self.type = AutoModRuleActionType.timeout
    def __repr__(self) -> str:
        return f'<AutoModRuleAction type={self.type.value} channel={self.channel_id} duration={self.duration}>'
    @classmethod
    def from_data(cls, data: AutoModerationActionPayload) -> Self:
        if data['type'] == AutoModRuleActionType.timeout.value:
            duration_seconds = data['metadata']['duration_seconds']
            return cls(duration=datetime.timedelta(seconds=duration_seconds))
        elif data['type'] == AutoModRuleActionType.send_alert_message.value:
            channel_id = int(data['metadata']['channel_id'])
            return cls(channel_id=channel_id)
        return cls(custom_message=data.get('metadata', {}).get('custom_message'))
    def to_dict(self) -> Dict[str, Any]:
        ret = {'type': self.type.value, 'metadata': {}}
        if self.type is AutoModRuleActionType.block_message and self.custom_message is not None:
            ret['metadata'] = {'custom_message': self.custom_message}
        elif self.type is AutoModRuleActionType.timeout:
            ret['metadata'] = {'duration_seconds': int(self.duration.total_seconds())}
        elif self.type is AutoModRuleActionType.send_alert_message:
            ret['metadata'] = {'channel_id': str(self.channel_id)}
        return ret
class AutoModTrigger:
    r
    __slots__ = (
        'type',
        'keyword_filter',
        'presets',
        'allow_list',
        'mention_limit',
        'regex_patterns',
    )
    def __init__(
        self,
        *,
        type: Optional[AutoModRuleTriggerType] = None,
        keyword_filter: Optional[List[str]] = None,
        presets: Optional[AutoModPresets] = None,
        allow_list: Optional[List[str]] = None,
        mention_limit: Optional[int] = None,
        regex_patterns: Optional[List[str]] = None,
    ) -> None:
        if type is None and sum(arg is not None for arg in (keyword_filter or regex_patterns, presets, mention_limit)) > 1:
            raise ValueError('Please pass only one of keyword_filter, regex_patterns, presets, or mention_limit.')
        if type is not None:
            self.type = type
        elif keyword_filter is not None or regex_patterns is not None:
            self.type = AutoModRuleTriggerType.keyword
        elif presets is not None:
            self.type = AutoModRuleTriggerType.keyword_preset
        elif mention_limit is not None:
            self.type = AutoModRuleTriggerType.mention_spam
        else:
            raise ValueError(
                'Please pass the trigger type explicitly if not using keyword_filter, presets, or mention_limit.'
            )
        self.keyword_filter: List[str] = keyword_filter if keyword_filter is not None else []
        self.presets: AutoModPresets = presets if presets is not None else AutoModPresets()
        self.allow_list: List[str] = allow_list if allow_list is not None else []
        self.mention_limit: int = mention_limit if mention_limit is not None else 0
        self.regex_patterns: List[str] = regex_patterns if regex_patterns is not None else []
    def __repr__(self) -> str:
        data = self.to_metadata_dict()
        if data:
            joined = ' '.join(f'{k}={v!r}' for k, v in data.items())
            return f'<AutoModTrigger type={self.type} {joined}>'
        return f'<AutoModTrigger type={self.type}>'
    @classmethod
    def from_data(cls, type: int, data: Optional[AutoModerationTriggerMetadataPayload]) -> Self:
        type_ = try_enum(AutoModRuleTriggerType, type)
        if data is None:
            return cls(type=type_)
        elif type_ is AutoModRuleTriggerType.keyword:
            return cls(
                type=type_,
                keyword_filter=data.get('keyword_filter'),
                regex_patterns=data.get('regex_patterns'),
                allow_list=data.get('allow_list'),
            )
        elif type_ is AutoModRuleTriggerType.keyword_preset:
            return cls(
                type=type_, presets=AutoModPresets._from_value(data.get('presets', [])), allow_list=data.get('allow_list')
            )
        elif type_ is AutoModRuleTriggerType.mention_spam:
            return cls(type=type_, mention_limit=data.get('mention_total_limit'))
        else:
            return cls(type=type_)
    def to_metadata_dict(self) -> Optional[Dict[str, Any]]:
        if self.type is AutoModRuleTriggerType.keyword:
            return {
                'keyword_filter': self.keyword_filter,
                'regex_patterns': self.regex_patterns,
                'allow_list': self.allow_list,
            }
        elif self.type is AutoModRuleTriggerType.keyword_preset:
            return {'presets': self.presets.to_array(), 'allow_list': self.allow_list}
        elif self.type is AutoModRuleTriggerType.mention_spam:
            return {'mention_total_limit': self.mention_limit}
class AutoModRule:
    __slots__ = (
        'state',
        '_cs_exempt_roles',
        '_cs_exempt_channels',
        '_cs_actions',
        'id',
        'guild',
        'name',
        'creator_id',
        'event_type',
        'trigger',
        'enabled',
        'exempt_role_ids',
        'exempt_channel_ids',
        '_actions',
    )
    def __init__(self, *, data: AutoModerationRulePayload, guild: Guild, state: ConnectionState) -> None:
        self.state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.creator_id = int(data['creator_id'])
        self.event_type: AutoModRuleEventType = try_enum(AutoModRuleEventType, data['event_type'])
        self.trigger: AutoModTrigger = AutoModTrigger.from_data(data['trigger_type'], data=data.get('trigger_metadata'))
        self.enabled: bool = data['enabled']
        self.exempt_role_ids: Set[int] = {int(role_id) for role_id in data['exempt_roles']}
        self.exempt_channel_ids: Set[int] = {int(channel_id) for channel_id in data['exempt_channels']}
        self._actions: List[AutoModerationActionPayload] = data['actions']
    def __repr__(self) -> str:
        return f'<AutoModRule id={self.id} name={self.name!r} guild={self.guild!r}>'
    def to_dict(self) -> AutoModerationRulePayload:
        ret: AutoModerationRulePayload = {
            'id': str(self.id),
            'guild_id': str(self.guild.id),
            'name': self.name,
            'creator_id': str(self.creator_id),
            'event_type': self.event_type.value,
            'trigger_type': self.trigger.type.value,
            'trigger_metadata': self.trigger.to_metadata_dict(),
            'actions': [action.to_dict() for action in self.actions],
            'enabled': self.enabled,
            'exempt_roles': [str(role_id) for role_id in self.exempt_role_ids],
            'exempt_channels': [str(channel_id) for channel_id in self.exempt_channel_ids],
        }
        return ret
    @property
    def creator(self) -> Optional[Member]:
        return self.guild.get_member(self.creator_id)
    @cached_slot_property('_cs_exempt_roles')
    def exempt_roles(self) -> List[Role]:
        result = []
        get_role = self.guild.get_role
        for role_id in self.exempt_role_ids:
            role = get_role(role_id)
            if role is not None:
                result.append(role)
        return utils._unique(result)
    @cached_slot_property('_cs_exempt_channels')
    def exempt_channels(self) -> List[Union[GuildChannel, Thread]]:
        it = filter(None, map(self.guild._resolve_channel, self.exempt_channel_ids))
        return utils._unique(it)
    @cached_slot_property('_cs_actions')
    def actions(self) -> List[AutoModRuleAction]:
        return [AutoModRuleAction.from_data(action) for action in self._actions]
    def is_exempt(self, obj: Snowflake, /) -> bool:
        return obj.id in self.exempt_channel_ids or obj.id in self.exempt_role_ids
    async def edit(
        self,
        *,
        name: str = MISSING,
        event_type: AutoModRuleEventType = MISSING,
        actions: List[AutoModRuleAction] = MISSING,
        trigger: AutoModTrigger = MISSING,
        enabled: bool = MISSING,
        exempt_roles: Sequence[Snowflake] = MISSING,
        exempt_channels: Sequence[Snowflake] = MISSING,
        reason: str = MISSING,
    ) -> Self:
        payload = {}
        if actions is not MISSING:
            payload['actions'] = [action.to_dict() for action in actions]
        if name is not MISSING:
            payload['name'] = name
        if event_type is not MISSING:
            payload['event_type'] = event_type
        if trigger is not MISSING:
            trigger_metadata = trigger.to_metadata_dict()
            if trigger_metadata is not None:
                payload['trigger_metadata'] = trigger_metadata
        if enabled is not MISSING:
            payload['enabled'] = enabled
        if exempt_roles is not MISSING:
            payload['exempt_roles'] = [x.id for x in exempt_roles]
        if exempt_channels is not MISSING:
            payload['exempt_channels'] = [x.id for x in exempt_channels]
        data = await self.state.http.edit_auto_moderation_rule(
            self.guild.id,
            self.id,
            reason=reason,
            **payload,
        )
        return AutoModRule(data=data, guild=self.guild, state=self.state)
    async def delete(self, *, reason: str = MISSING) -> None:
        await self.state.http.delete_auto_moderation_rule(self.guild.id, self.id, reason=reason)
class AutoModAction:
    __slots__ = (
        'state',
        'action',
        'rule_id',
        'rule_trigger_type',
        'guild_id',
        'user_id',
        'channel_id',
        'message_id',
        'alert_system_message_id',
        'content',
        'matched_keyword',
        'matched_content',
    )
    def __init__(self, *, data: AutoModerationActionExecutionPayload, state: ConnectionState) -> None:
        self.state: ConnectionState = state
        self.message_id: Optional[int] = utils._get_as_snowflake(data, 'message_id')
        self.action: AutoModRuleAction = AutoModRuleAction.from_data(data['action'])
        self.rule_id: int = int(data['rule_id'])
        self.rule_trigger_type: AutoModRuleTriggerType = try_enum(AutoModRuleTriggerType, data['rule_trigger_type'])
        self.guild_id: int = int(data['guild_id'])
        self.channel_id: Optional[int] = utils._get_as_snowflake(data, 'channel_id')
        self.user_id: int = int(data['user_id'])
        self.alert_system_message_id: Optional[int] = utils._get_as_snowflake(data, 'alert_system_message_id')
        self.content: str = data.get('content', '')
        self.matched_keyword: Optional[str] = data['matched_keyword']
        self.matched_content: Optional[str] = data.get('matched_content')
    def __repr__(self) -> str:
        return f'<AutoModRuleExecution rule_id={self.rule_id} action={self.action!r}>'
    @property
    def guild(self) -> Guild:
        return self.state._get_or_create_unavailable_guild(self.guild_id)
    @property
    def channel(self) -> Optional[Union[GuildChannel, Thread]]:
        if self.channel_id:
            return self.guild.get_channel_or_thread(self.channel_id)
        return None
    @property
    def member(self) -> Optional[Member]:
        return self.guild.get_member(self.user_id)
    async def fetch_rule(self) -> AutoModRule:
        data = await self.state.http.get_auto_moderation_rule(self.guild.id, self.rule_id)
        return AutoModRule(data=data, guild=self.guild, state=self.state)