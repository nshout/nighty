from typing import Optional, TypedDict, List, Literal
from typing_extensions import NotRequired
from .snowflake import Snowflake
from .member import MemberWithUser
SupportedModes = Literal['xsalsa20_poly1305_lite', 'xsalsa20_poly1305_suffix', 'xsalsa20_poly1305']
class BaseVoiceState(TypedDict):
    user_id: Snowflake
    session_id: str
    deaf: bool
    mute: bool
    self_deaf: bool
    self_mute: bool
    self_video: bool
    suppress: bool
    member: NotRequired[MemberWithUser]
    self_stream: NotRequired[bool]
class VoiceState(BaseVoiceState):
    channel_id: Snowflake
class PrivateVoiceState(BaseVoiceState):
    channel_id: Optional[Snowflake]
class GuildVoiceState(PrivateVoiceState):
    guild_id: Snowflake
class VoiceRegion(TypedDict):
    id: str
    name: str
    vip: bool
    optimal: bool
    deprecated: bool
    custom: bool
class VoiceServerUpdate(TypedDict):
    token: str
    guild_id: Snowflake
    channel_id: Snowflake
    endpoint: Optional[str]
class VoiceIdentify(TypedDict):
    server_id: Snowflake
    user_id: Snowflake
    session_id: str
    token: str
class VoiceReady(TypedDict):
    ssrc: int
    ip: str
    port: int
    modes: List[SupportedModes]
    heartbeat_interval: int