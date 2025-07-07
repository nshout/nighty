from __future__ import annotations
import io
import os
from typing import Any, Literal, Optional, TYPE_CHECKING, Tuple, Union
from .errors import DiscordException
from . import utils
from .file import File
import yarl
__all__ = (
    'Asset',
)
if TYPE_CHECKING:
    from typing_extensions import Self
    from .state import ConnectionState
    from .webhook.async_ import _WebhookState
    _State = Union[ConnectionState, _WebhookState]
    ValidStaticFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png']
    ValidAssetFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png', 'gif']
VALID_STATIC_FORMATS = frozenset({"jpeg", "jpg", "webp", "png"})
VALID_ASSET_FORMATS = VALID_STATIC_FORMATS | {"gif"}
MISSING = utils.MISSING
class AssetMixin:
    __slots__ = ()
    url: str
    state: Optional[Any]
    async def read(self) -> bytes:
        if self.state is None:
            raise DiscordException('Invalid state (no ConnectionState provided)')
        return await self.state.http.get_from_cdn(self.url)
    async def save(self, fp: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase], *, seek_begin: bool = True) -> int:
        data = await self.read()
        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)
    async def to_file(
        self,
        *,
        filename: Optional[str] = MISSING,
        description: Optional[str] = None,
        spoiler: bool = False,
    ) -> File:
        data = await self.read()
        file_filename = filename if filename is not MISSING else yarl.URL(self.url).name
        return File(io.BytesIO(data), filename=file_filename, description=description, spoiler=spoiler)
class Asset(AssetMixin):
    __slots__: Tuple[str, ...] = (
        'state',
        '_url',
        '_animated',
        '_passthrough',
        '_key',
    )
    BASE = 'https://cdn.discordapp.com'
    def __init__(self, state: _State, *, url: str, key: str, animated: bool = False, passthrough: bool = MISSING) -> None:
        self.state: _State = state
        self._url: str = url
        self._animated: bool = animated
        self._passthrough: bool = passthrough
        self._key: str = key
    @classmethod
    def _from_default_avatar(cls, state: _State, index: int) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/embed/avatars/{index}.png',
            key=str(index),
            animated=False,
            passthrough=True,
        )
    @classmethod
    def _from_avatar(cls, state: _State, user_id: int, avatar: str) -> Self:
        animated = avatar.startswith('a_')
        format = 'gif' if animated else 'png'
        return cls(
            state,
            url=f'{cls.BASE}/avatars/{user_id}/{avatar}.{format}?size=1024',
            key=avatar,
            animated=animated,
        )
    @classmethod
    def _from_avatar_decoration(cls, state: _State, decoration: str) -> Self:
        url = f'{cls.BASE}/avatar-decoration-presets/{decoration}.png?size=256&passthrough=true'
        return cls(state, url=url, key=decoration, animated=False, passthrough=True)
    @classmethod
    def _from_guild_avatar(cls, state: _State, guild_id: int, member_id: int, avatar: str) -> Self:
        animated = avatar.startswith('a_')
        format = 'gif' if animated else 'png'
        return cls(
            state,
            url=f"{cls.BASE}/guilds/{guild_id}/users/{member_id}/avatars/{avatar}.{format}?size=1024",
            key=avatar,
            animated=animated,
        )
    @classmethod
    def _from_guild_banner(cls, state: _State, guild_id: int, member_id: int, avatar: str) -> Self:
        animated = avatar.startswith('a_')
        format = 'gif' if animated else 'png'
        return cls(
            state,
            url=f"{cls.BASE}/guilds/{guild_id}/users/{member_id}/banners/{avatar}.{format}?size=512",
            key=avatar,
            animated=animated,
        )
    @classmethod
    def _from_icon(cls, state: _State, object_id: int, icon_hash: str, path: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/{path}-icons/{object_id}/{icon_hash}.png?size=1024',
            key=icon_hash,
            animated=False,
        )
    @classmethod
    def _from_scheduled_event_cover_image(cls, state: _State, scheduled_event_id: int, cover_image_hash: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/guild-events/{scheduled_event_id}/{cover_image_hash}.png?size=1024',
            key=cover_image_hash,
            animated=False,
        )
    @classmethod
    def _from_guild_image(cls, state: _State, guild_id: int, image: str, path: str) -> Self:
        animated = image.startswith('a_')
        format = 'gif' if animated else 'png'
        return cls(
            state,
            url=f'{cls.BASE}/{path}/{guild_id}/{image}.{format}?size=1024',
            key=image,
            animated=animated,
        )
    @classmethod
    def _from_guild_icon(cls, state: _State, guild_id: int, icon_hash: str) -> Self:
        animated = icon_hash.startswith('a_')
        format = 'gif' if animated else 'png'
        return cls(
            state,
            url=f'{cls.BASE}/icons/{guild_id}/{icon_hash}.{format}?size=1024',
            key=icon_hash,
            animated=animated,
        )
    @classmethod
    def _from_sticker_banner(cls, state: _State, banner: int) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/app-assets/710982414301790216/store/{banner}.png',
            key=str(banner),
            animated=False,
        )
    @classmethod
    def _from_user_banner(cls, state: _State, user_id: int, banner_hash: str) -> Self:
        animated = banner_hash.startswith('a_')
        format = 'gif' if animated else 'png'
        return cls(
            state,
            url=f'{cls.BASE}/banners/{user_id}/{banner_hash}.{format}?size=512',
            key=banner_hash,
            animated=animated,
        )
    @classmethod
    def _from_role_icon(cls, state, role_id: int, icon_hash: str) -> Asset:
        return cls(
            state,
            url=f'{cls.BASE}/role-icons/{role_id}/{icon_hash}.png',
            key=icon_hash,
            animated=False,
        )
    @classmethod
    def _from_achievement_icon(cls, state, app_id: int, achievement_id: int, icon_hash: str) -> Asset:
        return cls(
            state,
            url=f'{cls.BASE}/app-assets/{app_id}/achievements/{achievement_id}/icons/{icon_hash}.png',
            key=icon_hash,
            animated=False,
        )
    def __str__(self) -> str:
        return self._url
    def __len__(self) -> int:
        return len(self._url)
    def __repr__(self) -> str:
        shorten = self._url.replace(self.BASE, '')
        return f'<Asset url={shorten!r}>'
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Asset) and self._url == other._url
    def __hash__(self) -> int:
        return hash(self._url)
    @property
    def url(self) -> str:
        return self._url
    @property
    def key(self) -> str:
        return self._key
    def is_animated(self) -> bool:
        return self._animated
    def is_passthrough(self) -> bool:
        return self._passthrough
    def replace(
        self,
        *,
        size: int = MISSING,
        format: ValidAssetFormatTypes = MISSING,
        static_format: ValidStaticFormatTypes = MISSING,
        passthrough: Optional[bool] = MISSING,
        keep_aspect_ratio: bool = False,
    ) -> Self:
        url = yarl.URL(self._url)
        path, _ = os.path.splitext(url.path)
        if format is not MISSING:
            if self._animated:
                if format not in VALID_ASSET_FORMATS:
                    raise ValueError(f'format must be one of {VALID_ASSET_FORMATS}')
            else:
                if static_format is MISSING and format not in VALID_STATIC_FORMATS:
                    raise ValueError(f'format must be one of {VALID_STATIC_FORMATS}')
            query = dict(url.query)
            if self._passthrough:
                query['passthrough'] = 'false'
            url = url.with_path(f'{path}.{format}').with_query(query)
        if static_format is not MISSING and not self._animated:
            if static_format not in VALID_STATIC_FORMATS:
                raise ValueError(f'static_format must be one of {VALID_STATIC_FORMATS}')
            query = dict(url.query)
            if self._passthrough:
                query['passthrough'] = 'false'
            url = url.with_path(f'{path}.{static_format}').with_query(query)
        if size is not MISSING or passthrough is not MISSING or keep_aspect_ratio:
            if size is not MISSING and not utils.valid_icon_size(size):
                raise ValueError('size must be a power of 2 between 16 and 4096')
            query = dict(url.query)
            if size is not MISSING:
                query['size'] = str(size)
                if passthrough is MISSING and self._passthrough:
                    passthrough = False
            if passthrough is not MISSING:
                if passthrough is None:
                    passthrough = MISSING
                    query.pop('passthrough', None)
                else:
                    query['passthrough'] = str(passthrough).lower()
            if keep_aspect_ratio:
                query['keep_aspect_ratio'] = 'true'
            url = url.with_query(query)
        else:
            url = url.with_query(url.query)
        url = str(url)
        return Asset(state=self.state, url=url, key=self._key, animated=self._animated, passthrough=passthrough)
    def with_size(self, size: int, /) -> Self:
        if not utils.valid_icon_size(size):
            raise ValueError('size must be a power of 2 between 16 and 4096')
        url = yarl.URL(self._url)
        query = {**url.query, 'size': str(size)}
        if self._passthrough:
            query['passthrough'] = 'false'
        url = str(url.with_query(query))
        return Asset(state=self.state, url=url, key=self._key, animated=self._animated)
    def with_format(self, format: ValidAssetFormatTypes, /) -> Self:
        if self._animated:
            if format not in VALID_ASSET_FORMATS:
                raise ValueError(f'format must be one of {VALID_ASSET_FORMATS}')
        else:
            if format not in VALID_STATIC_FORMATS:
                raise ValueError(f'format must be one of {VALID_STATIC_FORMATS}')
        url = yarl.URL(self._url)
        path, _ = os.path.splitext(url.path)
        query = dict(url.query)
        if self._passthrough:
            query['passthrough'] = 'false'
        url = str(url.with_path(f'{path}.{format}').with_query(query))
        return Asset(state=self.state, url=url, key=self._key, animated=self._animated)
    def with_static_format(self, format: ValidStaticFormatTypes, /) -> Self:
        if self._animated:
            return self
        return self.with_format(format)