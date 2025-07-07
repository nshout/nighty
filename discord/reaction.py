from __future__ import annotations
from typing import TYPE_CHECKING, AsyncIterator, Union, Optional
from .user import User
from .object import Object
__all__ = (
    'Reaction',
)
if TYPE_CHECKING:
    from .member import Member
    from .types.message import Reaction as ReactionPayload
    from .message import Message
    from .partial_emoji import PartialEmoji
    from .emoji import Emoji
    from .abc import Snowflake
class Reaction:
    __slots__ = ('message', 'count', 'emoji', 'me')
    def __init__(self, *, message: Message, data: ReactionPayload, emoji: Optional[Union[PartialEmoji, Emoji, str]] = None):
        self.message: Message = message
        self.emoji: Union[PartialEmoji, Emoji, str] = emoji or message.state.get_reaction_emoji(data['emoji'])
        self.count: int = data.get('count', 1)
        self.me: bool = data['me']
    def is_custom_emoji(self) -> bool:
        return not isinstance(self.emoji, str)
    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.emoji == self.emoji
    def __ne__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return other.emoji != self.emoji
        return True
    def __hash__(self) -> int:
        return hash(self.emoji)
    def __str__(self) -> str:
        return str(self.emoji)
    def __repr__(self) -> str:
        return f'<Reaction emoji={self.emoji!r} me={self.me} count={self.count}>'
    async def remove(self, user: Snowflake) -> None:
        await self.message.remove_reaction(self.emoji, user)
    async def clear(self) -> None:
        await self.message.clear_reaction(self.emoji)
    async def users(
        self, *, limit: Optional[int] = None, after: Optional[Snowflake] = None
    ) -> AsyncIterator[Union[Member, User]]:
        if not isinstance(self.emoji, str):
            emoji = f'{self.emoji.name}:{self.emoji.id}'
        else:
            emoji = self.emoji
        if limit is None:
            limit = self.count
        while limit > 0:
            retrieve = min(limit, 100)
            message = self.message
            guild = message.guild
            state = message.state
            after_id = after.id if after else None
            data = await state.http.get_reaction_users(message.channel.id, message.id, emoji, retrieve, after=after_id)
            if data:
                limit -= len(data)
                after = Object(id=int(data[-1]['id']))
            else:
                limit = 0
            if guild is None or isinstance(guild, Object):
                for raw_user in reversed(data):
                    yield User(state=state, data=raw_user)
                continue
            for raw_user in reversed(data):
                member_id = int(raw_user['id'])
                member = guild.get_member(member_id)
                yield member or User(state=state, data=raw_user)