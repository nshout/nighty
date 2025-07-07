from __future__ import annotations
from typing import Any, Collection, Iterator, List, Optional, TYPE_CHECKING, Tuple
from .asset import Asset, AssetMixin
from .utils import SnowflakeList, snowflake_time, MISSING
from .partial_emoji import _EmojiTag, PartialEmoji
from .user import User
__all__ = (
    'Emoji',
)
if TYPE_CHECKING:
    from .types.emoji import Emoji as EmojiPayload
    from .guild import Guild
    from .state import ConnectionState
    from .abc import Snowflake
    from .role import Role
    from datetime import datetime
class Emoji(_EmojiTag, AssetMixin):
    __slots__: Tuple[str, ...] = (
        'require_colons',
        'animated',
        'managed',
        'id',
        'name',
        '_roles',
        'guild_id',
        'state',
        'user',
        'available',
    )
    def __init__(self, *, guild: Guild, state: ConnectionState, data: EmojiPayload):
        self.guild_id: int = guild.id
        self.state: ConnectionState = state
        self._from_data(data)
    def _from_data(self, emoji: EmojiPayload):
        self.require_colons: bool = emoji.get('require_colons', False)
        self.managed: bool = emoji.get('managed', False)
        self.id: int = int(emoji['id'])
        self.name: str = emoji['name']
        self.animated: bool = emoji.get('animated', False)
        self.available: bool = emoji.get('available', True)
        self._roles: SnowflakeList = SnowflakeList(map(int, emoji.get('roles', [])))
        user = emoji.get('user')
        self.user: Optional[User] = User(state=self.state, data=user) if user else None
    def _to_partial(self) -> PartialEmoji:
        return PartialEmoji(name=self.name, animated=self.animated, id=self.id)
    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        for attr in self.__slots__:
            if attr[0] != '_':
                value = getattr(self, attr, None)
                if value is not None:
                    yield (attr, value)
    def __str__(self) -> str:
        if self.animated:
            return f'<a:{self.name}:{self.id}>'
        return f'<:{self.name}:{self.id}>'
    def __repr__(self) -> str:
        return f'<Emoji id={self.id} name={self.name!r} animated={self.animated} managed={self.managed}>'
    def __eq__(self, other: object) -> bool:
        return isinstance(other, _EmojiTag) and self.id == other.id
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return self.id >> 22
    @property
    def created_at(self) -> datetime:
        return snowflake_time(self.id)
    @property
    def url(self) -> str:
        fmt = 'gif' if self.animated else 'png'
        return f'{Asset.BASE}/emojis/{self.id}.{fmt}'
    @property
    def roles(self) -> List[Role]:
        guild = self.guild
        if guild is None:
            return []
        return [role for role in guild.roles if self._roles.has(role.id)]
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    def is_usable(self) -> bool:
        if not self.available or not self.guild or self.guild.unavailable:
            return False
        if not self._roles:
            return True
        emoji_roles, my_roles = self._roles, self.guild.me._roles
        return any(my_roles.has(role_id) for role_id in emoji_roles)
    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_custom_emoji(self.guild_id, self.id, reason=reason)
    async def edit(
        self, *, name: str = MISSING, roles: Collection[Snowflake] = MISSING, reason: Optional[str] = None
    ) -> Emoji:
        r
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if roles is not MISSING:
            payload['roles'] = [role.id for role in roles]
        data = await self.state.http.edit_custom_emoji(self.guild_id, self.id, payload=payload, reason=reason)
        return Emoji(guild=self.guild, data=data, state=self.state)
    async def fetch_guild(self) -> Guild:
        state = self.state
        data = await state.http.get_emoji_guild(self.id)
        return state.create_guild(data)