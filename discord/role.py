from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .asset import Asset
from .permissions import Permissions
from .colour import Colour
from .mixins import Hashable
from .utils import snowflake_time, _get_as_snowflake, MISSING, _bytes_to_base64_data
__all__ = (
    'RoleTags',
    'Role',
)
if TYPE_CHECKING:
    import datetime
    from .types.role import (
        Role as RolePayload,
        RoleTags as RoleTagPayload,
    )
    from .types.guild import RolePositionUpdate
    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .abc import Snowflake
class RoleTags:
    __slots__ = (
        'bot_id',
        'integration_id',
        '_premium_subscriber',
        '_available_for_purchase',
        'subscription_listing_id',
        '_guild_connections',
    )
    def __init__(self, data: RoleTagPayload):
        self.bot_id: Optional[int] = _get_as_snowflake(data, 'bot_id')
        self.integration_id: Optional[int] = _get_as_snowflake(data, 'integration_id')
        self.subscription_listing_id: Optional[int] = _get_as_snowflake(data, 'subscription_listing_id')
        self._premium_subscriber: bool = data.get('premium_subscriber', MISSING) is None
        self._available_for_purchase: bool = data.get('available_for_purchase', MISSING) is None
        self._guild_connections: bool = data.get('guild_connections', MISSING) is None
    def is_bot_managed(self) -> bool:
        return self.bot_id is not None
    def is_premium_subscriber(self) -> bool:
        return self._premium_subscriber
    def is_integration(self) -> bool:
        return self.integration_id is not None
    def is_available_for_purchase(self) -> bool:
        return self._available_for_purchase
    def is_guild_connection(self) -> bool:
        return self._guild_connections
    def __repr__(self) -> str:
        return (
            f'<RoleTags bot_id={self.bot_id} integration_id={self.integration_id} '
            f'premium_subscriber={self.is_premium_subscriber()}>'
        )
class Role(Hashable):
    __slots__ = (
        'id',
        'name',
        '_permissions',
        '_colour',
        'position',
        '_icon',
        'unicode_emoji',
        'managed',
        'mentionable',
        'hoist',
        'guild',
        'tags',
        'state',
    )
    def __init__(self, *, guild: Guild, state: ConnectionState, data: RolePayload):
        self.guild: Guild = guild
        self.state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(data)
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return f'<Role id={self.id} name={self.name!r}>'
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Role) or not isinstance(self, Role):
            return NotImplemented
        if self.guild != other.guild:
            raise RuntimeError('cannot compare roles from two different guilds.')
        guild_id = self.guild.id
        if self.id == guild_id:
            return other.id != guild_id
        if self.position < other.position:
            return True
        if self.position == other.position:
            return self.id > other.id
        return False
    def __le__(self, other: Any) -> bool:
        r = Role.__lt__(other, self)
        if r is NotImplemented:
            return NotImplemented
        return not r
    def __gt__(self, other: Any) -> bool:
        return Role.__lt__(other, self)
    def __ge__(self, other: object) -> bool:
        r = Role.__lt__(self, other)
        if r is NotImplemented:
            return NotImplemented
        return not r
    def _update(self, data: RolePayload):
        self.name: str = data['name']
        self._permissions: int = int(data.get('permissions', 0))
        self.position: int = data.get('position', 0)
        self._colour: int = data.get('color', 0)
        self.hoist: bool = data.get('hoist', False)
        self._icon: Optional[str] = data.get('icon')
        self.unicode_emoji: Optional[str] = data.get('unicode_emoji')
        self.managed: bool = data.get('managed', False)
        self.mentionable: bool = data.get('mentionable', False)
        self.tags: Optional[RoleTags]
        try:
            self.tags = RoleTags(data['tags'])
        except KeyError:
            self.tags = None
    def is_default(self) -> bool:
        return self.guild.id == self.id
    def is_bot_managed(self) -> bool:
        return self.tags is not None and self.tags.is_bot_managed()
    def is_premium_subscriber(self) -> bool:
        return self.tags is not None and self.tags.is_premium_subscriber()
    def is_integration(self) -> bool:
        return self.tags is not None and self.tags.is_integration()
    def is_assignable(self) -> bool:
        me = self.guild.me
        return not self.is_default() and not self.managed and (me.top_role > self or me.id == self.guild.owner_id)
    @property
    def permissions(self) -> Permissions:
        return Permissions(self._permissions)
    @property
    def colour(self) -> Colour:
        return Colour(self._colour)
    @property
    def color(self) -> Colour:
        return self.colour
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='role')
    @property
    def display_icon(self) -> Optional[Union[Asset, str]]:
        return self.icon or self.unicode_emoji
    @property
    def created_at(self) -> datetime.datetime:
        return snowflake_time(self.id)
    @property
    def mention(self) -> str:
        if self.id == self.guild.id:
            return '@everyone'
        return f'<@&{self.id}>'
    @property
    def members(self) -> List[Member]:
        all_members = list(self.guild._members.values())
        if self.is_default():
            return all_members
        role_id = self.id
        return [member for member in all_members if member._roles.has(role_id)]
    async def _move(self, position: int, reason: Optional[str]) -> None:
        if position <= 0:
            raise ValueError("Cannot move role to position 0 or below")
        if self.is_default():
            raise ValueError("Cannot move default role")
        if self.position == position:
            return
        http = self.state.http
        change_range = range(min(self.position, position), max(self.position, position) + 1)
        roles = [r.id for r in self.guild.roles[1:] if r.position in change_range and r.id != self.id]
        if self.position > position:
            roles.insert(0, self.id)
        else:
            roles.append(self.id)
        payload: List[RolePositionUpdate] = [{"id": z[0], "position": z[1]} for z in zip(roles, change_range)]
        await http.move_role_position(self.guild.id, payload, reason=reason)
    async def fetch_members(self, *, subscribe: bool = False) -> List[Member]:
        if self.is_default():
            raise TypeError('Cannot fetch the default role\'s members')
        guild = self.guild
        data = await self.state.http.get_role_members(guild.id, self.id)
        if data:
            return await guild.query_members(user_ids=data, subscribe=subscribe)
        return []
    async def add_members(self, *members: Snowflake, reason: Optional[str] = None) -> List[Member]:
        r
        if self.is_default():
            raise TypeError('Cannot add members to the default role')
        from .member import Member
        state = self.state
        guild = self.guild
        data = await state.http.add_members_to_role(guild.id, self.id, [m.id for m in members], reason=reason)
        return [Member(data=m, state=state, guild=guild) for m in data.values()]
    async def remove_members(self, *members: Snowflake, reason: Optional[str] = None) -> None:
        r
        if self.is_default():
            raise TypeError('Cannot remove members from the default role')
        req = self.state.http.remove_role
        guild_id = self.guild.id
        role_id = self.id
        for member in members:
            await req(guild_id, member.id, role_id, reason=reason)
    async def edit(
        self,
        *,
        name: str = MISSING,
        permissions: Permissions = MISSING,
        colour: Union[Colour, int] = MISSING,
        color: Union[Colour, int] = MISSING,
        hoist: bool = MISSING,
        display_icon: Optional[Union[bytes, str]] = MISSING,
        icon: Optional[bytes] = MISSING,
        unicode_emoji: Optional[str] = MISSING,
        mentionable: bool = MISSING,
        position: int = MISSING,
        reason: Optional[str] = MISSING,
    ) -> Optional[Role]:
        if display_icon and (icon or unicode_emoji):
            raise ValueError('Cannot set both icon/unicode_emoji and display_icon')
        if position is not MISSING:
            await self._move(position, reason=reason)
        payload: Dict[str, Any] = {}
        if color is not MISSING:
            colour = color
        if colour is not MISSING:
            if isinstance(colour, int):
                payload['color'] = colour
            else:
                payload['color'] = colour.value
        if name is not MISSING:
            payload['name'] = name
        if permissions is not MISSING:
            payload['permissions'] = permissions.value
        if hoist is not MISSING:
            payload['hoist'] = hoist
        if display_icon is not MISSING:
            if isinstance(display_icon, bytes):
                payload['icon'] = _bytes_to_base64_data(display_icon)
            elif display_icon:
                payload['unicode_emoji'] = display_icon
            else:
                payload['icon'] = None
                payload['unicode_emoji'] = None
        if icon is not MISSING:
            if icon is None:
                payload['icon'] = icon
            else:
                payload['icon'] = _bytes_to_base64_data(icon)
        if unicode_emoji is not MISSING:
            if unicode_emoji is None:
                payload['unicode_emoji'] = None
            else:
                payload['unicode_emoji'] = unicode_emoji
        if mentionable is not MISSING:
            payload['mentionable'] = mentionable
        data = await self.state.http.edit_role(self.guild.id, self.id, reason=reason, **payload)
        return Role(guild=self.guild, data=data, state=self.state)
    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_role(self.guild.id, self.id, reason=reason)
    async def member_count(self) -> int:
        if self.is_default():
            return self.guild.member_count or self.guild.approximate_member_count or 0
        data = await self.state.http.get_role_member_counts(self.guild.id)
        return data.get(str(self.id), 0)