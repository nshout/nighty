from typing import Literal, TypedDict, List, Union, Optional
from typing_extensions import NotRequired
from .snowflake import Snowflake
AutoModerationRuleTriggerType = Literal[1, 2, 3, 4]
AutoModerationActionTriggerType = Literal[1, 2, 3]
AutoModerationRuleEventType = Literal[1]
AutoModerationTriggerPresets = Literal[1, 2, 3]
class Empty(TypedDict):
    ...
class _AutoModerationActionMetadataAlert(TypedDict):
    channel_id: Snowflake
class _AutoModerationActionMetadataTimeout(TypedDict):
    duration_seconds: int
class _AutoModerationActionMetadataCustomMessage(TypedDict):
    custom_message: str
class _AutoModerationActionBlockMessage(TypedDict):
    type: Literal[1]
    metadata: NotRequired[_AutoModerationActionMetadataCustomMessage]
class _AutoModerationActionAlert(TypedDict):
    type: Literal[2]
    metadata: _AutoModerationActionMetadataAlert
class _AutoModerationActionTimeout(TypedDict):
    type: Literal[3]
    metadata: _AutoModerationActionMetadataTimeout
AutoModerationAction = Union[_AutoModerationActionBlockMessage, _AutoModerationActionAlert, _AutoModerationActionTimeout]
class _AutoModerationTriggerMetadataKeyword(TypedDict):
    keyword_filter: List[str]
    regex_patterns: NotRequired[List[str]]
class _AutoModerationTriggerMetadataKeywordPreset(TypedDict):
    presets: List[AutoModerationTriggerPresets]
    allow_list: List[str]
class _AutoModerationTriggerMetadataMentionLimit(TypedDict):
    mention_total_limit: int
AutoModerationTriggerMetadata = Union[
    _AutoModerationTriggerMetadataKeyword,
    _AutoModerationTriggerMetadataKeywordPreset,
    _AutoModerationTriggerMetadataMentionLimit,
    Empty,
]
class _BaseAutoModerationRule(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    name: str
    creator_id: Snowflake
    event_type: AutoModerationRuleEventType
    actions: List[AutoModerationAction]
    enabled: bool
    exempt_roles: List[Snowflake]
    exempt_channels: List[Snowflake]
class _AutoModerationRuleKeyword(_BaseAutoModerationRule):
    trigger_type: Literal[1]
    trigger_metadata: _AutoModerationTriggerMetadataKeyword
class _AutoModerationRuleKeywordPreset(_BaseAutoModerationRule):
    trigger_type: Literal[4]
    trigger_metadata: _AutoModerationTriggerMetadataKeywordPreset
class _AutoModerationRuleOther(_BaseAutoModerationRule):
    trigger_type: Literal[2, 3]
AutoModerationRule = Union[_AutoModerationRuleKeyword, _AutoModerationRuleKeywordPreset, _AutoModerationRuleOther]
class AutoModerationActionExecution(TypedDict):
    guild_id: Snowflake
    action: AutoModerationAction
    rule_id: Snowflake
    rule_trigger_type: AutoModerationRuleTriggerType
    user_id: Snowflake
    channel_id: NotRequired[Snowflake]
    message_id: NotRequired[Snowflake]
    alert_system_message_id: NotRequired[Snowflake]
    content: str
    matched_keyword: Optional[str]
    matched_content: Optional[str]