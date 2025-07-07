from __future__ import annotations
from typing import Literal, Optional, TypedDict
from typing_extensions import NotRequired
from .snowflake import Snowflake
ReadStateType = Literal[0, 1, 2, 3, 4]
class ReadState(TypedDict):
    id: Snowflake
    read_state_type: NotRequired[ReadStateType]
    last_message_id: NotRequired[Snowflake]
    last_acked_id: NotRequired[Snowflake]
    last_pin_timestamp: NotRequired[str]
    mention_count: NotRequired[int]
    badge_count: NotRequired[int]
    flags: NotRequired[int]
    last_viewed: NotRequired[Optional[int]]
class BulkReadState(TypedDict):
    channel_id: Snowflake
    message_id: Snowflake
    read_state_type: ReadStateType
class AcknowledgementToken(TypedDict):
    token: Optional[str]