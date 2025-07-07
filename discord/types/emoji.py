from typing import List, Optional, TypedDict
from .snowflake import Snowflake, SnowflakeList
from .user import User
class PartialEmoji(TypedDict):
    id: Optional[Snowflake]
    name: Optional[str]
class Emoji(PartialEmoji, total=False):
    roles: SnowflakeList
    user: User
    require_colons: bool
    managed: bool
    animated: bool
    available: bool
class EditEmoji(TypedDict):
    name: str
    roles: Optional[SnowflakeList]
class TopEmoji(TypedDict):
    emoji_id: Snowflake
    emoji_rank: int
class TopEmojis(TypedDict):
    items: List[TopEmoji]