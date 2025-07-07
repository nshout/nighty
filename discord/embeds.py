from __future__ import annotations
import datetime
from typing import Any, Dict, List, Mapping, Optional, Protocol, TYPE_CHECKING, TypeVar, Union
from . import utils
from .colour import Colour
__all__ = (
    'Embed',
)
class EmbedProxy:
    def __init__(self, layer: Dict[str, Any]):
        self.__dict__.update(layer)
    def __len__(self) -> int:
        return len(self.__dict__)
    def __repr__(self) -> str:
        inner = ', '.join((f'{k}={v!r}' for k, v in self.__dict__.items() if not k.startswith('_')))
        return f'EmbedProxy({inner})'
    def __getattr__(self, attr: str) -> None:
        return None
    def __eq__(self, other: object) -> bool:
        return isinstance(other, EmbedProxy) and self.__dict__ == other.__dict__
if TYPE_CHECKING:
    from typing_extensions import Self
    from .types.embed import Embed as EmbedData, EmbedType
    T = TypeVar('T')
    class _EmbedFooterProxy(Protocol):
        text: Optional[str]
        icon_url: Optional[str]
    class _EmbedFieldProxy(Protocol):
        name: Optional[str]
        value: Optional[str]
        inline: bool
    class _EmbedMediaProxy(Protocol):
        url: Optional[str]
        proxy_url: Optional[str]
        height: Optional[int]
        width: Optional[int]
    class _EmbedVideoProxy(Protocol):
        url: Optional[str]
        height: Optional[int]
        width: Optional[int]
    class _EmbedProviderProxy(Protocol):
        name: Optional[str]
        url: Optional[str]
    class _EmbedAuthorProxy(Protocol):
        name: Optional[str]
        url: Optional[str]
        icon_url: Optional[str]
        proxy_icon_url: Optional[str]
class Embed:
    __slots__ = (
        'title',
        'url',
        'type',
        '_timestamp',
        '_colour',
        '_footer',
        '_image',
        '_thumbnail',
        '_video',
        '_provider',
        '_author',
        '_fields',
        'description',
    )
    def __init__(
        self,
        *,
        colour: Optional[Union[int, Colour]] = None,
        color: Optional[Union[int, Colour]] = None,
        title: Optional[Any] = None,
        type: EmbedType = 'rich',
        url: Optional[Any] = None,
        description: Optional[Any] = None,
        timestamp: Optional[datetime.datetime] = None,
    ):
        self.colour = colour if colour is not None else color
        self.title: Optional[str] = title
        self.type: EmbedType = type
        self.url: Optional[str] = url
        self.description: Optional[str] = description
        if self.title is not None:
            self.title = str(self.title)
        if self.description is not None:
            self.description = str(self.description)
        if self.url is not None:
            self.url = str(self.url)
        if timestamp is not None:
            self.timestamp = timestamp
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        self = cls.__new__(cls)
        self.title = data.get('title', None)
        self.type = data.get('type', None)
        self.description = data.get('description', None)
        self.url = data.get('url', None)
        if self.title is not None:
            self.title = str(self.title)
        if self.description is not None:
            self.description = str(self.description)
        if self.url is not None:
            self.url = str(self.url)
        try:
            self._colour = Colour(value=data['color'])
        except KeyError:
            pass
        try:
            self._timestamp = utils.parse_time(data['timestamp'])
        except KeyError:
            pass
        for attr in ('thumbnail', 'video', 'provider', 'author', 'fields', 'image', 'footer'):
            try:
                value = data[attr]
            except KeyError:
                continue
            else:
                setattr(self, '_' + attr, value)
        return self
    def copy(self) -> Self:
        return self.__class__.from_dict(self.to_dict())
    def __len__(self) -> int:
        total = len(self.title or '') + len(self.description or '')
        for field in getattr(self, '_fields', []):
            total += len(field['name']) + len(field['value'])
        try:
            footer_text = self._footer['text']
        except (AttributeError, KeyError):
            pass
        else:
            total += len(footer_text)
        try:
            author = self._author
        except AttributeError:
            pass
        else:
            total += len(author['name'])
        return total
    def __bool__(self) -> bool:
        return any(
            (
                self.title,
                self.url,
                self.description,
                self.colour,
                self.fields,
                self.timestamp,
                self.author,
                self.thumbnail,
                self.footer,
                self.image,
                self.provider,
                self.video,
            )
        )
    def __eq__(self, other: Embed) -> bool:
        return isinstance(other, Embed) and (
            self.type == other.type
            and self.title == other.title
            and self.url == other.url
            and self.description == other.description
            and self.colour == other.colour
            and self.fields == other.fields
            and self.timestamp == other.timestamp
            and self.author == other.author
            and self.thumbnail == other.thumbnail
            and self.footer == other.footer
            and self.image == other.image
            and self.provider == other.provider
            and self.video == other.video
        )
    @property
    def colour(self) -> Optional[Colour]:
        return getattr(self, '_colour', None)
    @colour.setter
    def colour(self, value: Optional[Union[int, Colour]]) -> None:
        if value is None:
            self._colour = None
        elif isinstance(value, Colour):
            self._colour = value
        elif isinstance(value, int):
            self._colour = Colour(value=value)
        else:
            raise TypeError(f'Expected discord.Colour, int, or None but received {value.__class__.__name__} instead.')
    color = colour
    @property
    def timestamp(self) -> Optional[datetime.datetime]:
        return getattr(self, '_timestamp', None)
    @timestamp.setter
    def timestamp(self, value: Optional[datetime.datetime]) -> None:
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                value = value.astimezone()
            self._timestamp = value
        elif value is None:
            self._timestamp = None
        else:
            raise TypeError(f"Expected datetime.datetime or None received {value.__class__.__name__} instead")
    @property
    def footer(self) -> _EmbedFooterProxy:
        return EmbedProxy(getattr(self, '_footer', {}))
    def set_footer(self, *, text: Optional[Any] = None, icon_url: Optional[Any] = None) -> Self:
        self._footer = {}
        if text is not None:
            self._footer['text'] = str(text)
        if icon_url is not None:
            self._footer['icon_url'] = str(icon_url)
        return self
    def remove_footer(self) -> Self:
        try:
            del self._footer
        except AttributeError:
            pass
        return self
    @property
    def image(self) -> _EmbedMediaProxy:
        return EmbedProxy(getattr(self, '_image', {}))
    def set_image(self, *, url: Optional[Any]) -> Self:
        if url is None:
            try:
                del self._image
            except AttributeError:
                pass
        else:
            self._image = {
                'url': str(url),
            }
        return self
    @property
    def thumbnail(self) -> _EmbedMediaProxy:
        return EmbedProxy(getattr(self, '_thumbnail', {}))
    def set_thumbnail(self, *, url: Optional[Any]) -> Self:
        if url is None:
            try:
                del self._thumbnail
            except AttributeError:
                pass
        else:
            self._thumbnail = {
                'url': str(url),
            }
        return self
    @property
    def video(self) -> _EmbedVideoProxy:
        return EmbedProxy(getattr(self, '_video', {}))
    @property
    def provider(self) -> _EmbedProviderProxy:
        return EmbedProxy(getattr(self, '_provider', {}))
    @property
    def author(self) -> _EmbedAuthorProxy:
        return EmbedProxy(getattr(self, '_author', {}))
    def set_author(self, *, name: Any, url: Optional[Any] = None, icon_url: Optional[Any] = None) -> Self:
        self._author = {
            'name': str(name),
        }
        if url is not None:
            self._author['url'] = str(url)
        if icon_url is not None:
            self._author['icon_url'] = str(icon_url)
        return self
    def remove_author(self) -> Self:
        try:
            del self._author
        except AttributeError:
            pass
        return self
    @property
    def fields(self) -> List[_EmbedFieldProxy]:
        return [EmbedProxy(d) for d in getattr(self, '_fields', [])]
    def add_field(self, *, name: Any, value: Any, inline: bool = True) -> Self:
        field = {
            'inline': inline,
            'name': str(name),
            'value': str(value),
        }
        try:
            self._fields.append(field)
        except AttributeError:
            self._fields = [field]
        return self
    def insert_field_at(self, index: int, *, name: Any, value: Any, inline: bool = True) -> Self:
        field = {
            'inline': inline,
            'name': str(name),
            'value': str(value),
        }
        try:
            self._fields.insert(index, field)
        except AttributeError:
            self._fields = [field]
        return self
    def clear_fields(self) -> None:
        try:
            self._fields.clear()
        except AttributeError:
            self._fields = []
    def remove_field(self, index: int) -> None:
        try:
            del self._fields[index]
        except (AttributeError, IndexError):
            pass
    def set_field_at(self, index: int, *, name: Any, value: Any, inline: bool = True) -> Self:
        try:
            field = self._fields[index]
        except (TypeError, IndexError, AttributeError):
            raise IndexError('field index out of range')
        field['name'] = str(name)
        field['value'] = str(value)
        field['inline'] = inline
        return self
    def to_dict(self) -> EmbedData:
        result = {
            key[1:]: getattr(self, key)
            for key in self.__slots__
            if key[0] == '_' and hasattr(self, key)
        }
        try:
            colour = result.pop('colour')
        except KeyError:
            pass
        else:
            if colour:
                result['color'] = colour.value
        try:
            timestamp = result.pop('timestamp')
        except KeyError:
            pass
        else:
            if timestamp:
                if timestamp.tzinfo:
                    result['timestamp'] = timestamp.astimezone(tz=datetime.timezone.utc).isoformat()
                else:
                    result['timestamp'] = timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()
        if self.type:
            result['type'] = self.type
        if self.description:
            result['description'] = self.description
        if self.url:
            result['url'] = self.url
        if self.title:
            result['title'] = self.title
        return result