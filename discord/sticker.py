from __future__ import annotations
from typing import Literal, TYPE_CHECKING, List, Optional, Tuple, Type, Union
import unicodedata
from .mixins import Hashable
from .asset import Asset, AssetMixin
from .utils import cached_slot_property, find, snowflake_time, get, MISSING, _get_as_snowflake
from .errors import InvalidData
from .enums import StickerType, StickerFormatType, try_enum
__all__ = (
    'StickerPack',
    'StickerItem',
    'Sticker',
    'StandardSticker',
    'GuildSticker',
)
if TYPE_CHECKING:
    import datetime
    from .state import ConnectionState
    from .user import User
    from .guild import Guild
    from .types.sticker import (
        StickerPack as StickerPackPayload,
        StickerItem as StickerItemPayload,
        Sticker as StickerPayload,
        StandardSticker as StandardStickerPayload,
        GuildSticker as GuildStickerPayload,
    )
class StickerPack(Hashable):
    __slots__ = (
        'state',
        'id',
        'stickers',
        'name',
        'sku_id',
        'cover_sticker_id',
        'cover_sticker',
        'description',
        '_banner',
    )
    def __init__(self, *, state: ConnectionState, data: StickerPackPayload) -> None:
        self.state: ConnectionState = state
        self._from_data(data)
    def _from_data(self, data: StickerPackPayload) -> None:
        self.id: int = int(data['id'])
        stickers = data['stickers']
        self.stickers: List[StandardSticker] = [StandardSticker(state=self.state, data=sticker) for sticker in stickers]
        self.name: str = data['name']
        self.sku_id: int = int(data['sku_id'])
        self.cover_sticker_id: Optional[int] = _get_as_snowflake(data, 'cover_sticker_id')
        self.cover_sticker: Optional[StandardSticker] = get(self.stickers, id=self.cover_sticker_id)
        self.description: str = data['description']
        self._banner: Optional[int] = _get_as_snowflake(data, 'banner_asset_id')
    @property
    def banner(self) -> Optional[Asset]:
        return self._banner and Asset._from_sticker_banner(self.state, self._banner)
    def __repr__(self) -> str:
        return f'<StickerPack id={self.id} name={self.name!r} description={self.description!r}>'
    def __str__(self) -> str:
        return self.name
class _StickerTag(Hashable, AssetMixin):
    __slots__ = ()
    id: int
    format: StickerFormatType
    async def read(self) -> bytes:
        if self.format is StickerFormatType.lottie:
            raise TypeError('Cannot read stickers of format "lottie"')
        return await super().read()
class StickerItem(_StickerTag):
    __slots__ = ('state', 'name', 'id', 'format', 'url')
    def __init__(self, *, state: ConnectionState, data: StickerItemPayload):
        self.state: ConnectionState = state
        self.name: str = data['name']
        self.id: int = int(data['id'])
        self.format: StickerFormatType = try_enum(StickerFormatType, data['format_type'])
        self.url: str = f'{Asset.BASE}/stickers/{self.id}.{self.format.file_extension}'
    def __repr__(self) -> str:
        return f'<StickerItem id={self.id} name={self.name!r} format={self.format}>'
    def __str__(self) -> str:
        return self.name
    async def fetch(self) -> Union[Sticker, StandardSticker, GuildSticker]:
        data = await self.state.http.get_sticker(self.id)
        cls, _ = _sticker_factory(data['type'])
        return cls(state=self.state, data=data)
    async def fetch_guild(self) -> Guild:
        state = self.state
        data = await state.http.get_sticker_guild(self.id)
        return state.create_guild(data)
class Sticker(_StickerTag):
    __slots__ = ('state', 'id', 'name', 'description', 'format', 'url')
    def __init__(self, *, state: ConnectionState, data: StickerPayload) -> None:
        self.state: ConnectionState = state
        self._from_data(data)
    def _from_data(self, data: StickerPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.format: StickerFormatType = try_enum(StickerFormatType, data['format_type'])
        self.url: str = f'{Asset.BASE}/stickers/{self.id}.{self.format.file_extension}'
    def __repr__(self) -> str:
        return f'<Sticker id={self.id} name={self.name!r}>'
    def __str__(self) -> str:
        return self.name
    @property
    def created_at(self) -> datetime.datetime:
        return snowflake_time(self.id)
class StandardSticker(Sticker):
    __slots__ = ('sort_value', 'pack_id', 'type', 'tags')
    def _from_data(self, data: StandardStickerPayload) -> None:
        super()._from_data(data)
        self.sort_value: int = data['sort_value']
        self.pack_id: int = int(data['pack_id'])
        self.type: StickerType = StickerType.standard
        try:
            self.tags: List[str] = [tag.strip() for tag in data['tags'].split(',')]
        except KeyError:
            self.tags = []
    def __repr__(self) -> str:
        return f'<StandardSticker id={self.id} name={self.name!r} pack_id={self.pack_id}>'
    async def pack(self) -> StickerPack:
        data = await self.state.http.list_premium_sticker_packs()
        packs = data['sticker_packs']
        pack = find(lambda d: int(d['id']) == self.pack_id, packs)
        if pack:
            return StickerPack(state=self.state, data=pack)
        raise InvalidData(f'Could not find corresponding sticker pack for {self!r}')
class GuildSticker(Sticker):
    __slots__ = ('available', 'guild_id', 'user', 'emoji', 'type', '_cs_guild')
    def _from_data(self, data: GuildStickerPayload) -> None:
        super()._from_data(data)
        self.available: bool = data.get('available', True)
        self.guild_id: int = int(data['guild_id'])
        user = data.get('user')
        self.user: Optional[User] = self.state.store_user(user) if user else None
        self.emoji: str = data['tags']
        self.type: StickerType = StickerType.guild
    def __repr__(self) -> str:
        return f'<GuildSticker name={self.name!r} id={self.id} guild_id={self.guild_id} user={self.user!r}>'
    @cached_slot_property('_cs_guild')
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        emoji: str = MISSING,
        reason: Optional[str] = None,
    ) -> GuildSticker:
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if description is not MISSING:
            payload['description'] = description
        if emoji is not MISSING:
            try:
                emoji = unicodedata.name(emoji)
            except TypeError:
                pass
            else:
                emoji = emoji.replace(' ', '_')
            payload['tags'] = emoji
        data = await self.state.http.modify_guild_sticker(self.guild_id, self.id, payload, reason)
        return GuildSticker(state=self.state, data=data)
    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_guild_sticker(self.guild_id, self.id, reason)
    async def fetch_guild(self) -> Guild:
        state = self.state
        data = await state.http.get_sticker_guild(self.id)
        return state.create_guild(data)
def _sticker_factory(sticker_type: Literal[1, 2]) -> Tuple[Type[Union[StandardSticker, GuildSticker, Sticker]], StickerType]:
    value = try_enum(StickerType, sticker_type)
    if value == StickerType.standard:
        return StandardSticker, value
    elif value == StickerType.guild:
        return GuildSticker, value
    else:
        return Sticker, value