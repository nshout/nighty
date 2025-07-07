from __future__ import annotations
import re
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from . import utils
from .asset import Asset, AssetMixin
__all__ = (
    'PartialEmoji',
)
if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self
    from .guild import Guild
    from .state import ConnectionState
    from .types.activity import ActivityEmoji
    from .types.emoji import Emoji as EmojiPayload, PartialEmoji as PartialEmojiPayload
class _EmojiTag:
    __slots__ = ()
    id: int
    def _to_partial(self) -> PartialEmoji:
        raise NotImplementedError
class PartialEmoji(_EmojiTag, AssetMixin):
    __slots__ = ('animated', 'name', 'id', 'state')
    _CUSTOM_EMOJI_RE = re.compile(r'<?(?:(?P<animated>a)?:)?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?')
    if TYPE_CHECKING:
        id: Optional[int]
    def __init__(self, *, name: str, animated: bool = False, id: Optional[int] = None):
        self.animated: bool = animated
        self.name: str = name
        self.id: Optional[int] = id
        self.state: Optional[ConnectionState] = None
    @classmethod
    def from_dict(cls, data: Union[PartialEmojiPayload, ActivityEmoji, Dict[str, Any]]) -> Self:
        return cls(
            animated=data.get('animated', False),
            id=utils._get_as_snowflake(data, 'id'),
            name=data.get('name') or '',
        )
    @classmethod
    def from_dict_stateful(
        cls, data: Union[PartialEmojiPayload, ActivityEmoji, Dict[str, Any]], state: ConnectionState
    ) -> Self:
        self = cls.from_dict(data)
        self.state = state
        return self
    @classmethod
    def from_str(cls, value: str) -> Self:
        match = cls._CUSTOM_EMOJI_RE.match(value)
        if match is not None:
            groups = match.groupdict()
            animated = bool(groups['animated'])
            emoji_id = int(groups['id'])
            name = groups['name']
            return cls(name=name, animated=animated, id=emoji_id)
        return cls(name=value, id=None, animated=False)
    def to_dict(self) -> EmojiPayload:
        payload: EmojiPayload = {
            'id': self.id,
            'name': self.name,
        }
        if self.animated:
            payload['animated'] = self.animated
        return payload
    def _to_partial(self) -> PartialEmoji:
        return self
    def _to_forum_tag_payload(self) -> Dict[str, Any]:
        if self.id is not None:
            return {'emoji_id': self.id, 'emoji_name': None}
        return {'emoji_id': None, 'emoji_name': self.name}
    @classmethod
    def with_state(
        cls,
        state: ConnectionState,
        *,
        name: str,
        animated: bool = False,
        id: Optional[int] = None,
    ) -> Self:
        self = cls(name=name, animated=animated, id=id)
        self.state = state
        return self
    def __str__(self) -> str:
        name = self.name or '_'
        if self.id is None:
            return name
        if self.animated:
            return f'<a:{name}:{self.id}>'
        return f'<:{name}:{self.id}>'
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} animated={self.animated} name={self.name!r} id={self.id}>'
    def __eq__(self, other: object) -> bool:
        if self.is_unicode_emoji():
            return isinstance(other, PartialEmoji) and self.name == other.name
        if isinstance(other, _EmojiTag):
            return self.id == other.id
        return False
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return hash((self.id, self.name))
    def is_custom_emoji(self) -> bool:
        return self.id is not None
    def is_unicode_emoji(self) -> bool:
        return self.id is None
    def _as_reaction(self) -> str:
        if self.id is None:
            return self.name
        return f'{self.name}:{self.id}'
    @property
    def created_at(self) -> Optional[datetime]:
        if self.id is None:
            return None
        return utils.snowflake_time(self.id)
    @property
    def url(self) -> str:
        if self.is_unicode_emoji():
            return ''
        fmt = 'gif' if self.animated else 'png'
        return f'{Asset.BASE}/emojis/{self.id}.{fmt}'
    async def read(self) -> bytes:
        if self.is_unicode_emoji():
            raise ValueError('PartialEmoji is not a custom emoji')
        return await super().read()
    async def fetch_guild(self) -> Guild:
        if self.id is None:
            raise ValueError('PartialEmoji is not a custom emoji')
        if self.state is None:
            raise TypeError('PartialEmoji does not have state available')
        state = self.state
        data = await state.http.get_emoji_guild(self.id)
        return state.create_guild(data)