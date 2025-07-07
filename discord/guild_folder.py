from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from .colour import Colour
from .object import Object
if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.snowflake import Snowflake
__all__ = (
    'GuildFolder',
)
class GuildFolder:
    __slots__ = ('state', 'id', 'name', '_colour', 'guilds')
    def __init__(self, *, data, state: ConnectionState) -> None:
        self.state = state
        self.id: Snowflake = data['id']
        self.name: str = data['name']
        self._colour: int = data['color']
        self.guilds: List[Guild] = list(filter(None, map(self._get_guild, data['guild_ids'])))
    def __str__(self) -> str:
        return self.name or 'None'
    def __repr__(self) -> str:
        return f'<GuildFolder id={self.id} name={self.name} guilds={self.guilds!r}>'
    def __eq__(self, other) -> bool:
        return isinstance(other, GuildFolder) and self.id == other.id
    def __ne__(self, other) -> bool:
        if isinstance(other, GuildFolder):
            return self.id != other.id
        return True
    def __hash__(self) -> int:
        return hash(self.id)
    def __len__(self) -> int:
        return len(self.guilds)
    def _get_guild(self, id):
        return self.state._get_guild(int(id)) or Object(id=int(id))
    @property
    def colour(self) -> Optional[Colour]:
        colour = self._colour
        return Colour(colour) if colour is not None else None
    @property
    def color(self) -> Optional[Colour]:
        return self.colour