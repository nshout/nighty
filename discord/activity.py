from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, overload
from .asset import Asset
from .colour import Colour
from .enums import ActivityType, ClientType, OperatingSystem, Status, try_enum
from .partial_emoji import PartialEmoji
from .utils import _get_as_snowflake, parse_time, parse_timestamp
__all__ = (
    'BaseActivity',
    'Activity',
    'Streaming',
    'Game',
    'Spotify',
    'CustomActivity',
    'Session',
)
if TYPE_CHECKING:
    from typing_extensions import Self
    from .state import ConnectionState
    from .types.activity import (
        Activity as ActivityPayload,
        ActivityAssets,
        ActivityParty,
        ActivityTimestamps,
    )
    from .types.gateway import Session as SessionPayload
class BaseActivity:
    __slots__ = ('_created_at',)
    def __init__(self, **kwargs: Any) -> None:
        self._created_at: Optional[float] = kwargs.pop('created_at', None)
    @property
    def created_at(self) -> Optional[datetime.datetime]:
        if self._created_at is not None:
            return datetime.datetime.fromtimestamp(self._created_at / 1000, tz=datetime.timezone.utc)
    def to_dict(self) -> ActivityPayload:
        raise NotImplementedError
class Activity(BaseActivity):
    __slots__ = (
        'state',
        'details',
        'timestamps',
        'assets',
        'party',
        'flags',
        'sync_id',
        'session_id',
        'type',
        'name',
        'url',
        'application_id',
        'emoji',
        'buttons',
        'metadata',
    )
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.state: Optional[str] = kwargs.pop('state', None)
        self.details: Optional[str] = kwargs.pop('details', None)
        self.timestamps: ActivityTimestamps = kwargs.pop('timestamps', {})
        self.assets: ActivityAssets = kwargs.pop('assets', {})
        self.party: ActivityParty = kwargs.pop('party', {})
        self.application_id: Optional[int] = _get_as_snowflake(kwargs, 'application_id')
        self.name: Optional[str] = kwargs.pop('name', None)
        self.url: Optional[str] = kwargs.pop('url', None)
        self.flags: int = kwargs.pop('flags', 0)
        self.sync_id: Optional[str] = kwargs.pop('sync_id', None)
        self.session_id: Optional[str] = kwargs.pop('session_id', None)
        self.buttons: Optional[List[str]] = kwargs.pop('buttons', None)
        self.metadata: Optional[dict] = kwargs.pop('metadata', None)
        activity_type = kwargs.pop('type', -1)
        self.type: ActivityType = (
            activity_type if isinstance(activity_type, ActivityType) else try_enum(ActivityType, activity_type)
        )
        emoji = kwargs.pop('emoji', None)
        self.emoji: Optional[PartialEmoji] = PartialEmoji.from_dict(emoji) if emoji is not None else None
    def __repr__(self) -> str:
        attrs = (
            ('type', self.type),
            ('name', self.name),
            ('url', self.url),
            ('details', self.details),
            ('application_id', self.application_id),
            ('session_id', self.session_id),
            ('emoji', self.emoji),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<Activity {inner}>'
    def __eq__(self, other):
        return (
            isinstance(other, Activity)
            and other.type == self.type
            and other.name == self.name
            and other.url == self.url
            and other.emoji == self.emoji
            and other.state == self.state
            and other.session_id == self.session_id
            and other.sync_id == self.sync_id
            and other.start == self.start
        )
    def __ne__(self, other):
        return not self.__eq__(other)
    def to_dict(self) -> ActivityPayload:
        ret: Dict[str, Any] = {}
        for attr in self.__slots__:
            value = getattr(self, attr, None)
            if value is None:
                continue
            if isinstance(value, dict) and len(value) == 0:
                continue
            ret[attr] = value
        ret['type'] = int(self.type)
        if self.emoji:
            ret['emoji'] = self.emoji.to_dict()
        return ret
    @property
    def start(self) -> Optional[datetime.datetime]:
        try:
            timestamp = self.timestamps['start'] / 1000
        except KeyError:
            return None
        else:
            return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    @property
    def end(self) -> Optional[datetime.datetime]:
        try:
            timestamp = self.timestamps['end'] / 1000
        except KeyError:
            return None
        else:
            return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    @property
    def large_image_url(self) -> Optional[str]:
        try:
            large_image = self.assets['large_image']
        except KeyError:
            return None
        else:
            return self._image_url(large_image)
    @property
    def small_image_url(self) -> Optional[str]:
        try:
            small_image = self.assets['small_image']
        except KeyError:
            return None
        else:
            return self._image_url(small_image)
    def _image_url(self, image: str) -> Optional[str]:
        if image.startswith('mp:'):
            return f'https://media.discordapp.net/{image[3:]}'
        elif self.application_id is not None:
            return Asset.BASE + f'/app-assets/{self.application_id}/{image}.png'
    @property
    def large_image_text(self) -> Optional[str]:
        return self.assets.get('large_text', None)
    @property
    def small_image_text(self) -> Optional[str]:
        return self.assets.get('small_text', None)
class Game(BaseActivity):
    __slots__ = ('name', '_end', '_start')
    def __init__(self, name: str, **extra: Any) -> None:
        super().__init__(**extra)
        self.name: str = name
        try:
            timestamps: ActivityTimestamps = extra['timestamps']
        except KeyError:
            self._start = 0
            self._end = 0
        else:
            self._start = timestamps.get('start', 0)
            self._end = timestamps.get('end', 0)
    @property
    def type(self) -> ActivityType:
        return ActivityType.playing
    @property
    def start(self) -> Optional[datetime.datetime]:
        if self._start:
            return datetime.datetime.fromtimestamp(self._start / 1000, tz=datetime.timezone.utc)
        return None
    @property
    def end(self) -> Optional[datetime.datetime]:
        if self._end:
            return datetime.datetime.fromtimestamp(self._end / 1000, tz=datetime.timezone.utc)
        return None
    def __str__(self) -> str:
        return str(self.name)
    def __repr__(self) -> str:
        return f'<Game name={self.name!r}>'
    def to_dict(self) -> ActivityPayload:
        timestamps: Dict[str, Any] = {}
        if self._start:
            timestamps['start'] = self._start
        if self._end:
            timestamps['end'] = self._end
        return {
            'type': ActivityType.playing.value,
            'name': str(self.name),
            'timestamps': timestamps,
        }
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Game) and other.name == self.name
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return hash(self.name)
class Streaming(BaseActivity):
    __slots__ = ('platform', 'name', 'game', 'url', 'details', 'assets')
    def __init__(self, *, name: Optional[str], url: str, **extra: Any) -> None:
        super().__init__(**extra)
        self.platform: Optional[str] = name
        self.name: Optional[str] = extra.pop('details', name)
        self.game: Optional[str] = extra.pop('state', None)
        self.url: str = url
        self.details: Optional[str] = extra.pop('details', self.name)
        self.assets: ActivityAssets = extra.pop('assets', {})
    @property
    def type(self) -> ActivityType:
        return ActivityType.streaming
    def __str__(self) -> str:
        return str(self.name)
    def __repr__(self) -> str:
        return f'<Streaming name={self.name!r}>'
    @property
    def twitch_name(self) -> Optional[str]:
        try:
            name = self.assets['large_image']
        except KeyError:
            return None
        else:
            return name[7:] if name[:7] == 'twitch:' else None
    def to_dict(self) -> ActivityPayload:
        ret: Dict[str, Any] = {
            'type': ActivityType.streaming.value,
            'name': str(self.name),
            'url': str(self.url),
            'assets': self.assets,
        }
        if self.details:
            ret['details'] = self.details
        return ret
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Streaming) and other.name == self.name and other.url == self.url
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return hash(self.name)
class Spotify:
    __slots__ = ('state', '_details', '_timestamps', '_assets', '_party', '_sync_id', '_session_id', '_created_at')
    def __init__(self, **data: Any) -> None:
        self.state: str = data.pop('state', '')
        self._details: str = data.pop('details', '')
        self._timestamps: ActivityTimestamps = data.pop('timestamps', {})
        self._assets: ActivityAssets = data.pop('assets', {})
        self._party: ActivityParty = data.pop('party', {})
        self._sync_id: str = data.pop('sync_id', '')
        self._session_id: Optional[str] = data.pop('session_id')
        self._created_at: Optional[float] = data.pop('created_at', None)
    @property
    def type(self) -> ActivityType:
        return ActivityType.listening
    @property
    def created_at(self) -> Optional[datetime.datetime]:
        if self._created_at is not None:
            return datetime.datetime.fromtimestamp(self._created_at / 1000, tz=datetime.timezone.utc)
    @property
    def colour(self) -> Colour:
        return Colour(0x1DB954)
    @property
    def color(self) -> Colour:
        return self.colour
    def to_dict(self) -> ActivityPayload:
        return {
            'flags': 48,
            'name': 'Spotify',
            'assets': self._assets,
            'party': self._party,
            'sync_id': self._sync_id,
            'session_id': self._session_id,
            'timestamps': self._timestamps,
            'details': self._details,
            'state': self.state,
        }
    @property
    def name(self) -> str:
        return 'Spotify'
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Spotify)
            and other._session_id == self._session_id
            and other._sync_id == self._sync_id
            and other.start == self.start
        )
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return hash(self._session_id)
    def __str__(self) -> str:
        return 'Spotify'
    def __repr__(self) -> str:
        return f'<Spotify title={self.title!r} artist={self.artist!r} track_id={self.track_id!r}>'
    @property
    def title(self) -> str:
        return self._details
    @property
    def artists(self) -> List[str]:
        return self.state.split('; ')
    @property
    def artist(self) -> str:
        return self.state
    @property
    def album(self) -> str:
        return self._assets.get('large_text', '')
    @property
    def album_cover_url(self) -> str:
        large_image = self._assets.get('large_image', '')
        if large_image[:8] != 'spotify:':
            return ''
        album_image_id = large_image[8:]
        return 'https://i.scdn.co/image/' + album_image_id
    @property
    def track_id(self) -> str:
        return self._sync_id
    @property
    def track_url(self) -> str:
        return f'https://open.spotify.com/track/{self.track_id}'
    @property
    def start(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self._timestamps['start'] / 1000, tz=datetime.timezone.utc)
    @property
    def end(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self._timestamps['end'] / 1000, tz=datetime.timezone.utc)
    @property
    def duration(self) -> datetime.timedelta:
        return self.end - self.start
    @property
    def party_id(self) -> str:
        return self._party.get('id', '')
class CustomActivity(BaseActivity):
    __slots__ = ('name', 'emoji', 'expires_at')
    def __init__(
        self,
        name: Optional[str],
        *,
        emoji: Optional[PartialEmoji] = None,
        state: Optional[str] = None,
        expires_at: Optional[datetime.datetime] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if name == 'Custom Status':
            name = state
        self.name: Optional[str] = name
        self.expires_at = expires_at
        self.emoji: Optional[PartialEmoji]
        if isinstance(emoji, dict):
            self.emoji = PartialEmoji.from_dict(emoji)
        elif isinstance(emoji, str):
            self.emoji = PartialEmoji(name=emoji)
        elif isinstance(emoji, PartialEmoji) or emoji is None:
            self.emoji = emoji
        else:
            raise TypeError(f'Expected str, PartialEmoji, or None, received {type(emoji)!r} instead.')
    @classmethod
    def _from_legacy_settings(cls, *, data: Optional[dict], state: ConnectionState) -> Optional[Self]:
        if not data:
            return
        emoji = None
        if data.get('emoji_id'):
            emoji = state.get_emoji(int(data['emoji_id']))
            if not emoji:
                emoji = PartialEmoji(id=int(data['emoji_id']), name=data['emoji_name'])
                emoji.state = state
            else:
                emoji = emoji._to_partial()
        elif data.get('emoji_name'):
            emoji = PartialEmoji(name=data['emoji_name'])
            emoji.state = state
        return cls(name=data.get('text'), emoji=emoji, expires_at=parse_time(data.get('expires_at')))
    @classmethod
    def _from_settings(cls, *, data: Any, state: ConnectionState) -> Self:
        emoji = None
        if data.emoji_id:
            emoji = state.get_emoji(data.emoji_id)
            if not emoji:
                emoji = PartialEmoji(id=data.emoji_id, name=data.emoji_name)
                emoji.state = state
            else:
                emoji = emoji._to_partial()
        elif data.emoji_name:
            emoji = PartialEmoji(name=data.emoji_name)
            emoji.state = state
        return cls(name=data.text, emoji=emoji, expires_at=parse_timestamp(data.expires_at_ms))
    @property
    def type(self) -> ActivityType:
        return ActivityType.custom
    def to_dict(self) -> ActivityPayload:
        payload = {
            'type': ActivityType.custom.value,
            'state': self.name,
            'name': 'Custom Status',
        }
        if self.emoji:
            payload['emoji'] = self.emoji.to_dict()
        return payload
    def to_legacy_settings_dict(self) -> Dict[str, Optional[Union[str, int]]]:
        payload: Dict[str, Optional[Union[str, int]]] = {}
        if self.name:
            payload['text'] = self.name
        if self.emoji:
            emoji = self.emoji
            payload['emoji_name'] = emoji.name
            if emoji.id:
                payload['emoji_id'] = emoji.id
        if self.expires_at is not None:
            payload['expires_at'] = self.expires_at.isoformat()
        return payload
    def to_settings_dict(self) -> Dict[str, Optional[Union[str, int]]]:
        payload: Dict[str, Optional[Union[str, int]]] = {}
        if self.name:
            payload['text'] = self.name
        if self.emoji:
            emoji = self.emoji
            payload['emoji_name'] = emoji.name
            if emoji.id:
                payload['emoji_id'] = emoji.id
        if self.expires_at is not None:
            payload['expires_at_ms'] = int(self.expires_at.timestamp() * 1000)
        return payload
    def __eq__(self, other: object) -> bool:
        return isinstance(other, CustomActivity) and other.name == self.name and other.emoji == self.emoji
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __hash__(self) -> int:
        return hash((self.name, str(self.emoji)))
    def __str__(self) -> str:
        if self.emoji:
            if self.name:
                return f'{self.emoji} {self.name}'
            return str(self.emoji)
        else:
            return str(self.name)
    def __repr__(self) -> str:
        return f'<CustomActivity name={self.name!r} emoji={self.emoji!r}>'
class Session:
    __slots__ = (
        'session_id',
        'active',
        'os',
        'client',
        'version',
        'status',
        'activities',
        'state',
    )
    def __init__(self, *, data: SessionPayload, state: ConnectionState):
        self.state = state
        client_info = data['client_info']
        self.session_id: str = data['session_id']
        self.os: OperatingSystem = OperatingSystem.from_string(client_info['os'])
        self.client: ClientType = try_enum(ClientType, client_info['client'])
        self.version: int = client_info.get('version', 0)
        self._update(data)
    def _update(self, data: SessionPayload):
        state = self.state
        self.active: bool = data.get('active', False)
        self.status: Status = try_enum(Status, data['status'])
        self.activities: Tuple[ActivityTypes, ...] = tuple(
            create_activity(activity, state) for activity in data['activities']
        )
    def __repr__(self) -> str:
        return f'<Session session_id={self.session_id!r} active={self.active!r} status={self.status!r} activities={self.activities!r}>'
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Session) and self.session_id == other.session_id
    def __ne__(self, other: object) -> bool:
        if isinstance(other, Session):
            return self.session_id != other.session_id
        return True
    def __hash__(self) -> int:
        return hash(self.session_id)
    @classmethod
    def _fake_all(cls, *, state: ConnectionState, data: SessionPayload) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self.session_id = 'all'
        self.os = OperatingSystem.unknown
        self.client = ClientType.unknown
        self.version = 0
        self._update(data)
        return self
    def is_overall(self) -> bool:
        return self.session_id == 'all'
    def is_headless(self) -> bool:
        return self.session_id.startswith('h:')
    def is_current(self) -> bool:
        return self.session_id == self.state.session_id
ActivityTypes = Union[Activity, Game, CustomActivity, Streaming, Spotify]
@overload
def create_activity(data: ActivityPayload, state: ConnectionState) -> ActivityTypes:
    ...
@overload
def create_activity(data: None, state: ConnectionState) -> None:
    ...
@overload
def create_activity(data: Optional[ActivityPayload], state: ConnectionState) -> Optional[ActivityTypes]:
    ...
def create_activity(data: Optional[ActivityPayload], state: ConnectionState) -> Optional[ActivityTypes]:
    if not data:
        return None
    game_type = try_enum(ActivityType, data.get('type', -1))
    if game_type is ActivityType.playing:
        if 'application_id' in data or 'session_id' in data:
            return Activity(**data)
        return Game(**data)
    elif game_type is ActivityType.custom:
        try:
            name = data.pop('name')
        except KeyError:
            ret = Activity(**data)
        else:
            ret = CustomActivity(name=name, **data)
    elif game_type is ActivityType.streaming:
        if 'url' in data:
            return Streaming(**data)
        return Activity(**data)
    elif game_type is ActivityType.listening and 'sync_id' in data and 'session_id' in data:
        return Spotify(**data)
    else:
        ret = Activity(**data)
    if isinstance(ret.emoji, PartialEmoji):
        ret.emoji.state = state
    return ret