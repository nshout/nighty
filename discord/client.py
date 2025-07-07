from __future__ import annotations
import asyncio
from datetime import datetime
import logging
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Coroutine,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    overload,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)
import aiohttp
from .user import _UserTag, User, ClientUser, Note
from .invite import Invite
from .template import Template
from .widget import Widget
from .guild import UserGuild
from .emoji import Emoji
from .channel import _private_channel_factory, _threaded_channel_factory, GroupChannel, PartialMessageable
from .enums import ActivityType, ChannelType, ClientType, ConnectionType, EntitlementType, Status
from .mentions import AllowedMentions
from .errors import *
from .enums import RelationshipType, Status
from .gateway import *
from .gateway import ConnectionClosed
from .activity import ActivityTypes, BaseActivity, Session, Spotify, create_activity
from .voice_client import VoiceClient
from .http import HTTPClient
from .state import ConnectionState
from . import utils
from .utils import MISSING
from .object import Object, OLDEST_OBJECT
from .backoff import ExponentialBackoff
from .webhook import Webhook
from .application import Application, ApplicationActivityStatistics, Company, EULA, PartialApplication, UnverifiedApplication
from .stage_instance import StageInstance
from .threads import Thread
from .sticker import GuildSticker, StandardSticker, StickerPack, _sticker_factory
from .profile import UserProfile
from .connections import Connection
from .team import Team
from .billing import PaymentSource, PremiumUsage
from .subscriptions import Subscription, SubscriptionItem, SubscriptionInvoice
from .payments import Payment
from .promotions import PricingPromotion, Promotion, TrialOffer
from .entitlements import Entitlement, Gift
from .store import SKU, StoreListing, SubscriptionPlan
from .guild_premium import *
from .library import LibraryApplication
from .relationship import FriendSuggestion, Relationship
from .settings import UserSettings, LegacyUserSettings, TrackingSettings, EmailSettings
from .affinity import *
from .oauth2 import OAuth2Authorization, OAuth2Token
from .experiment import UserExperiment, GuildExperiment
if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType
    from .guild import GuildChannel
    from .abc import Snowflake, SnowflakeTime
    from .channel import DMChannel
    from .message import Message
    from .member import Member
    from .voice_client import VoiceProtocol
    from .settings import GuildSettings
    from .billing import BillingAddress
    from .enums import Distributor, OperatingSystem, PaymentGateway, RequiredActionType
    from .metadata import MetadataObject
    from .permissions import Permissions
    from .read_state import ReadState
    from .tutorial import Tutorial
    from .file import File
    from .guild import Guild
    from .types.snowflake import Snowflake as _Snowflake
    PrivateChannel = Union[DMChannel, GroupChannel]
__all__ = (
    'Client',
)
Coro = TypeVar('Coro', bound=Callable[..., Coroutine[Any, Any, Any]])
_log = logging.getLogger(__name__)
class _LoopSentinel:
    __slots__ = ()
    def __getattr__(self, attr: str) -> None:
        msg = (
            'loop attribute cannot be accessed in non-async contexts. '
            'Consider using either an asynchronous main function and passing it to asyncio.run or '
            'using asynchronous initialisation hooks such as Client.setup_hook'
        )
        raise AttributeError(msg)
_loop: Any = _LoopSentinel()
async def getImageID(client_id: dict, key: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://discord.com/api/v10/oauth2/applications/{client_id}/assets") as req:
            app_assets = await req.json()
    for t_list in app_assets:
        try:
            if str(key) == t_list["name"]:
                return t_list["id"]
        except:
            pass
    return None
class Client:
    r
    def __init__(self, **options: Any) -> None:
        self.loop: asyncio.AbstractEventLoop = _loop
        self.ws: DiscordWebSocket = None
        self._listeners: Dict[str, List[Tuple[asyncio.Future, Callable[..., bool]]]] = {}
        proxy: Optional[str] = options.pop('proxy', None)
        proxy_auth: Optional[aiohttp.BasicAuth] = options.pop('proxy_auth', None)
        unsync_clock: bool = options.pop('assume_unsync_clock', True)
        http_trace: Optional[aiohttp.TraceConfig] = options.pop('http_trace', None)
        max_ratelimit_timeout: Optional[float] = options.pop('max_ratelimit_timeout', None)
        self.captcha_handler: Optional[Callable[[CaptchaRequired, Client], Awaitable[str]]] = options.pop(
            'captcha_handler', None
        )
        self.http: HTTPClient = HTTPClient(
            proxy=proxy,
            proxy_auth=proxy_auth,
            unsync_clock=unsync_clock,
            http_trace=http_trace,
            captcha=self.handle_captcha,
            max_ratelimit_timeout=max_ratelimit_timeout,
            locale=lambda: self._connection.locale,
        )
        self._handlers: Dict[str, Callable[..., None]] = {
            'ready': self._handle_ready,
            'connect': self._handle_connect,
        }
        self._hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {
            'before_identify': self._call_before_identify_hook,
        }
        self._enable_debug_events: bool = options.pop('enable_debug_events', False)
        self._sync_presences: bool = options.pop('sync_presence', True)
        self._connection: ConnectionState = self._get_state(**options)
        self._closed: bool = False
        self._ready: asyncio.Event = MISSING
        if VoiceClient.warn_nacl:
            VoiceClient.warn_nacl = False
            _log.warning('PyNaCl is not installed, voice will NOT be supported.')
    async def __aenter__(self) -> Self:
        await self._async_setup_hook()
        return self
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if not self.is_closed():
            await self.close()
    def _get_state(self, **options: Any) -> ConnectionState:
        return ConnectionState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            loop=self.loop,
            client=self,
            **options,
        )
    def _handle_ready(self) -> None:
        self._ready.set()
    def _handle_connect(self) -> None:
        state = self._connection
        activities = self.initial_activities
        status = self.initial_status
        if status or activities:
            if status is None:
                status = getattr(state.settings, 'status', None) or Status.unknown
            _log.debug('Setting initial presence to %s %s', status, activities)
            self.loop.create_task(self.change_presence(activities=activities, status=status))
    @property
    def latency(self) -> float:
        ws = self.ws
        return float('nan') if not ws else ws.latency
    def is_ws_ratelimited(self) -> bool:
        if self.ws:
            return self.ws.is_ratelimited()
        return False
    @property
    def user(self) -> Optional[ClientUser]:
        return self._connection.user
    @property
    def required_action(self) -> Optional[RequiredActionType]:
        return self._connection.required_action
    @property
    def guilds(self) -> Sequence[Guild]:
        return self._connection.guilds
    @property
    def emojis(self) -> Sequence[Emoji]:
        return self._connection.emojis
    @property
    def stickers(self) -> Sequence[GuildSticker]:
        return self._connection.stickers
    @property
    def sessions(self) -> Sequence[Session]:
        return utils.SequenceProxy(self._connection._sessions.values())
    @property
    def cached_messages(self) -> Sequence[Message]:
        return utils.SequenceProxy(self._connection._messages or [])
    @property
    def connections(self) -> Sequence[Connection]:
        return utils.SequenceProxy(self._connection.connections.values())
    @property
    def private_channels(self) -> Sequence[PrivateChannel]:
        return self._connection.private_channels
    @property
    def relationships(self) -> Sequence[Relationship]:
        return utils.SequenceProxy(self._connection._relationships.values())
    @property
    def friends(self) -> List[Relationship]:
        r
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.friend]
    @property
    def blocked(self) -> List[Relationship]:
        r
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.blocked]
    def get_relationship(self, user_id: int, /) -> Optional[Relationship]:
        return self._connection._relationships.get(user_id)
    @property
    def settings(self) -> Optional[UserSettings]:
        return self._connection.settings
    @property
    def tracking_settings(self) -> Optional[TrackingSettings]:
        return self._connection.consents
    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        return self._connection.voice_clients
    @property
    def country_code(self) -> Optional[str]:
        return self._connection.country_code
    @property
    def preferred_rtc_regions(self) -> List[str]:
        return self._connection.preferred_rtc_regions
    @property
    def pending_payments(self) -> Sequence[Payment]:
        return utils.SequenceProxy(self._connection.pending_payments.values())
    @property
    def read_states(self) -> List[ReadState]:
        return [read_state for group in self._connection._read_states.values() for read_state in group.values()]
    @property
    def friend_suggestion_count(self) -> int:
        return self._connection.friend_suggestion_count
    @property
    def tutorial(self) -> Tutorial:
        return self._connection.tutorial
    @property
    def experiments(self) -> Sequence[UserExperiment]:
        return utils.SequenceProxy(self._connection.experiments.values())
    @property
    def guild_experiments(self) -> Sequence[GuildExperiment]:
        return utils.SequenceProxy(self._connection.guild_experiments.values())
    def get_experiment(self, experiment: Union[str, int], /) -> Optional[Union[UserExperiment, GuildExperiment]]:
        name = None
        if not isinstance(experiment, int) and not experiment.isdigit():
            name = experiment
            experiment_hash = utils.murmurhash32(experiment, signed=False)
        else:
            experiment_hash = int(experiment)
        exp = self._connection.experiments.get(experiment_hash, self._connection.guild_experiments.get(experiment_hash))
        if exp and not exp.name and name:
            exp.name = name
        return exp
    @property
    def disclose(self) -> Sequence[str]:
        return utils.SequenceProxy(self._connection.disclose)
    def is_ready(self) -> bool:
        return self._ready is not MISSING and self._ready.is_set()
    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass
    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        return self.loop.create_task(wrapped, name=f'discord.py: {event_name}')
    def dispatch(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        _log.debug('Dispatching event %s.', event)
        method = 'on_' + event
        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue
                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)
            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]
        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)
    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        _log.exception('Ignoring exception in %s', event_method)
    async def on_internal_settings_update(self, old_settings: UserSettings, new_settings: UserSettings, /):
        if not self._sync_presences:
            return
        if (
            old_settings is not None
            and old_settings.status == new_settings.status
            and old_settings.custom_activity == new_settings.custom_activity
        ):
            return
        current_activity = None
        for activity in self.activities:
            if activity.type != ActivityType.custom:
                current_activity = activity
                break
        if new_settings.status == self.client_status and new_settings.custom_activity == current_activity:
            return
        status = new_settings.status
        activities = [a for a in self.client_activities if a.type != ActivityType.custom]
        if new_settings.custom_activity is not None:
            activities.append(new_settings.custom_activity)
        _log.debug('Syncing presence to %s %s', status, new_settings.custom_activity)
        await self.change_presence(status=status, activities=activities, edit_settings=False)
    async def _call_before_identify_hook(self, *, initial: bool = False) -> None:
        await self.before_identify_hook(initial=initial)
    async def before_identify_hook(self, *, initial: bool = False) -> None:
        pass
    async def handle_captcha(self, exception: CaptchaRequired, /) -> str:
        handler = self.captcha_handler
        if handler is None:
            raise exception
        return await handler(exception, self)
    async def _async_setup_hook(self) -> None:
        loop = asyncio.get_running_loop()
        self.loop = loop
        self._connection.loop = loop
        await self._connection.async_setup()
        self._ready = asyncio.Event()
    async def setup_hook(self) -> None:
        pass
    async def login(self, token: str) -> None:
        _log.info('Logging in using static token.')
        if self.loop is _loop:
            await self._async_setup_hook()
        if not isinstance(token, str):
            raise TypeError(f'expected token to be a str, received {token.__class__!r} instead')
        state = self._connection
        data = await state.http.static_login(token.strip())
        state.analytics_token = data.get('analytics_token', '')
        state.user = ClientUser(state=state, data=data)
        await self.setup_hook()
    async def connect(self, *, reconnect: bool = True, session_spoof: str = "windows", startup_status: str) -> None:
        backoff = ExponentialBackoff()
        ws_params = {
            'initial': True,
            'session_spoof': session_spoof,
            'startup_status': startup_status
        }
        while not self.is_closed():
            try:
                coro = DiscordWebSocket.from_client(
                    self, **ws_params)
                self.ws = await asyncio.wait_for(coro, timeout=60.0)
                ws_params['initial'] = False
                while True:
                    await self.ws.poll_event()
            except ReconnectWebSocket as e:
                _log.info('Got a request to %s the websocket.', e.op)
                self.dispatch('disconnect')
                ws_params.update(sequence=self.ws.sequence,
                                 resume=e.resume, session=self.ws.session_id)
                continue
            except (
                OSError,
                HTTPException,
                GatewayNotFound,
                ConnectionClosed,
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as exc:
                self.dispatch('disconnect')
                if not reconnect:
                    await self.close()
                    if isinstance(exc, ConnectionClosed) and exc.code == 1000:
                        return
                    raise
                if self.is_closed():
                    return
                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    ws_params.update(
                        sequence=self.ws.sequence, initial=False, resume=True, session=self.ws.session_id)
                    continue
                if isinstance(exc, ConnectionClosed):
                    if exc.code != 1000:
                        await self.close()
                        raise
                retry = backoff.delay()
                _log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
                ws_params.update(sequence=self.ws.sequence,
                                 resume=True, session=self.ws.session_id)
    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for voice in self.voice_clients:
            try:
                await voice.disconnect(force=True)
            except Exception:
                pass
        if self.ws is not None and self.ws.open:
            await self.ws.close(code=1000)
        await self.http.close()
        if self._ready is not MISSING:
            self._ready.clear()
        self.loop = MISSING
    def clear(self) -> None:
        self._closed = False
        self._ready.clear()
        self._connection.clear(full=True)
        self.http.clear()
    async def start(self, token: str, *, reconnect: bool = True, session_spoof: str = "windows", startup_status) -> None:
        await self.login(token)
        await self.connect(reconnect=reconnect, session_spoof=session_spoof, startup_status=startup_status)
    def run(
        self,
        token: str,
        *,
        reconnect: bool = True,
        session_spoof: str = "windows",
        startup_status: str,
        log_handler: Optional[logging.Handler] = MISSING,
        log_formatter: logging.Formatter = MISSING,
        log_level: int = MISSING,
        root_logger: bool = False,
    ) -> None:
        async def runner():
            async with self:
                await self.start(token, reconnect=reconnect, session_spoof=session_spoof, startup_status=startup_status)
        if log_handler is not None:
            utils.setup_logging(
                handler=log_handler,
                formatter=log_formatter,
                level=log_level,
                root=root_logger,
            )
        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            return
    def is_closed(self) -> bool:
        return self._closed
    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        return self._connection._get_voice_client(self._connection.self_id)
    @property
    def notification_settings(self) -> GuildSettings:
        state = self._connection
        return state.guild_settings.get(None, state.default_guild_settings(None))
    @property
    def initial_activity(self) -> Optional[ActivityTypes]:
        state = self._connection
        return create_activity(state._activities[0], state) if state._activities else None
    @initial_activity.setter
    def initial_activity(self, value: Optional[ActivityTypes]) -> None:
        if value is None:
            self._connection._activities = []
        elif isinstance(value, BaseActivity):
            self._connection._activities = [value.to_dict()]
        else:
            raise TypeError('activity must derive from BaseActivity')
    @property
    def initial_activities(self) -> List[ActivityTypes]:
        state = self._connection
        return [create_activity(activity, state) for activity in state._activities]
    @initial_activities.setter
    def initial_activities(self, values: Sequence[ActivityTypes]) -> None:
        if not values:
            self._connection._activities = []
        elif all(isinstance(value, (BaseActivity, Spotify)) for value in values):
            self._connection._activities = [value.to_dict() for value in values]
        else:
            raise TypeError('activity must derive from BaseActivity')
    @property
    def initial_status(self) -> Optional[Status]:
        if self._connection._status in {state.value for state in Status}:
            return Status(self._connection._status)
    @initial_status.setter
    def initial_status(self, value: Status):
        if value is Status.offline:
            self._connection._status = 'invisible'
        elif isinstance(value, Status):
            self._connection._status = str(value)
        else:
            raise TypeError('status must derive from Status')
    @property
    def status(self) -> Status:
        status = getattr(self._connection.all_session, 'status', None)
        if status is None and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status or Status.offline
    @property
    def raw_status(self) -> str:
        return str(self.status)
    @property
    def client_status(self) -> Status:
        status = getattr(self._connection.current_session, 'status', None)
        if status is None and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status or Status.offline
    def is_on_mobile(self) -> bool:
        return any(session.client == ClientType.mobile for session in self._connection._sessions.values())
    @property
    def activities(self) -> Tuple[ActivityTypes]:
        state = self._connection
        activities = state.all_session.activities if state.all_session else None
        if activities is None and not self.is_closed():
            activity = getattr(state.settings, 'custom_activity', None)
            activities = (activity,) if activity else activities
        return activities or tuple()
    @property
    def activity(self) -> Optional[ActivityTypes]:
        if activities := self.activities:
            return activities[0]
    @property
    def client_activities(self) -> Tuple[ActivityTypes]:
        state = self._connection
        activities = state.current_session.activities if state.current_session else None
        if activities is None and not self.is_closed():
            activity = getattr(state.settings, 'custom_activity', None)
            activities = (activity,) if activity else activities
        return activities or tuple()
    def is_afk(self) -> bool:
        if self.ws:
            return self.ws.afk
        return False
    @property
    def idle_since(self) -> Optional[datetime]:
        ws = self.ws
        if ws is None or not ws.idle_since:
            return None
        return utils.parse_timestamp(ws.idle_since)
    @property
    def allowed_mentions(self) -> Optional[AllowedMentions]:
        return self._connection.allowed_mentions
    @allowed_mentions.setter
    def allowed_mentions(self, value: Optional[AllowedMentions]) -> None:
        if value is None or isinstance(value, AllowedMentions):
            self._connection.allowed_mentions = value
        else:
            raise TypeError(f'allowed_mentions must be AllowedMentions not {value.__class__!r}')
    @property
    def users(self) -> List[User]:
        return list(self._connection._users.values())
    def get_channel(self, id: int, /) -> Optional[Union[GuildChannel, Thread, PrivateChannel]]:
        return self._connection.get_channel(id)
    def get_partial_messageable(
        self, id: int, *, guild_id: Optional[int] = None, type: Optional[ChannelType] = None
    ) -> PartialMessageable:
        return PartialMessageable(state=self._connection, id=id, guild_id=guild_id, type=type)
    def get_stage_instance(self, id: int, /) -> Optional[StageInstance]:
        from .channel import StageChannel
        channel = self._connection.get_channel(id)
        if isinstance(channel, StageChannel):
            return channel.instance
    def get_guild(self, id: int, /) -> Optional[Guild]:
        return self._connection._get_guild(id)
    def get_user(self, id: int, /) -> Optional[User]:
        return self._connection.get_user(id)
    def get_emoji(self, id: int, /) -> Optional[Emoji]:
        return self._connection.get_emoji(id)
    def get_sticker(self, id: int, /) -> Optional[GuildSticker]:
        return self._connection.get_sticker(id)
    def get_all_channels(self) -> Generator[GuildChannel, None, None]:
        for guild in self.guilds:
            yield from guild.channels
    def get_all_members(self) -> Generator[Member, None, None]:
        for guild in self.guilds:
            yield from guild.members
    async def wait_until_ready(self) -> None:
        if self._ready is not MISSING:
            await self._ready.wait()
        else:
            raise RuntimeError(
                'Client has not been properly initialised. '
                'Please use the login method or asynchronous context manager before calling this method'
            )
    def wait_for(
        self,
        event: str,
        /,
        *,
        check: Optional[Callable[..., bool]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        future = self.loop.create_future()
        if check is None:
            def _check(*args):
                return True
            check = _check
        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners
        listeners.append((future, check))
        return asyncio.wait_for(future, timeout)
    def event(self, coro: Coro, /) -> Coro:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('event registered must be a coroutine function')
        setattr(self, coro.__name__, coro)
        _log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro
    async def change_presence(
        self,
        *,
        activity: Optional[ActivityTypes] = MISSING,
        activities: List[ActivityTypes] = MISSING,
        status: Status = MISSING,
        afk: bool = MISSING,
        idle_since: Optional[datetime] = MISSING,
        edit_settings: bool = True,
    ) -> None:
        if activity is not MISSING and activities is not MISSING:
            raise TypeError('Cannot pass both activity and activities')
        skip_activities = False
        if activities is MISSING:
            if activity is not MISSING:
                activities = [activity] if activity else []
            else:
                activities = list(self.client_activities)
                skip_activities = True
        else:
            activities = activities or []
        skip_status = status is MISSING
        if status is MISSING:
            status = self.client_status
        if status is Status.offline:
            status = Status.invisible
        if afk is MISSING:
            afk = self.ws.afk if self.ws else False
        if idle_since is MISSING:
            since = self.ws.idle_since if self.ws else 0
        else:
            since = int(idle_since.timestamp() * 1000) if idle_since else 0
        custom_activity = None
        if not skip_activities:
            for activity in activities:
                if getattr(activity, 'type', None) is ActivityType.custom:
                    if custom_activity is not None:
                        raise ValueError('More than one custom activity was passed')
                    custom_activity = activity
        await self.ws.change_presence(status=status, activities=activities, afk=afk, since=since)
        if edit_settings and self.settings:
            payload: Dict[str, Any] = {}
            if not skip_status and status != self.settings.status:
                payload['status'] = status
            if not skip_activities and custom_activity != self.settings.custom_activity:
                payload['custom_activity'] = custom_activity
            if payload:
                await self.settings.edit(**payload)
    async def change_rich_presence(self, *, client_id: str = None, name: str = None, activity_type: int=None, state: str = None, details: str = None, large_image: str = None, large_text: str = None, small_image: str = None, small_text: str = None, button: str = None, button_url: str = None, button_2: str = None, button_2_url: str = None, timer=False, start_unix=[], end_unix=[], party: dict=None, stream_url:str=None, status, platform: str="Desktop"):
        payload = {
            "op": 3,
            "d": {
                "status": status,
                "since": 0,
                "activities": [{
                    'type': activity_type or 0,
                    'assets': {}
                }],
                "afk": True
            }
        }
        if client_id:
            payload["d"]["activities"][0]["application_id"] = client_id
        if name:
            payload["d"]["activities"][0]["name"] = name
        if state:
            payload["d"]["activities"][0]["state"] = state
        if details:
            payload["d"]["activities"][0]["details"] = details
        if platform:
            payload["d"]["activities"][0]["platform"] = platform
        if large_image:
            payload["d"]["activities"][0]["assets"]["large_image"] = large_image
        if large_text:
            payload["d"]["activities"][0]["assets"]["large_text"] = large_text
        if small_image:
            payload["d"]["activities"][0]["assets"]["small_image"] = small_image
        if small_text:
            payload["d"]["activities"][0]["assets"]["small_text"] = small_text
        if button:
            payload["d"]["activities"][0]['buttons'] = []
            payload["d"]["activities"][0]["buttons"].append(button)
            if button_url:
                payload["d"]["activities"][0]['metadata'] = {'button_urls': []}
                payload["d"]["activities"][0]["metadata"]["button_urls"].append(button_url)
        if button_2:
            payload["d"]["activities"][0]["buttons"].append(button_2)
            if button_2_url:
                payload["d"]["activities"][0]["metadata"]["button_urls"].append(button_2_url)
        if timer:
            if start_unix:
                payload["d"]["activities"][0]["timestamps"] = {
                    "start": start_unix
                }
                if end_unix:
                    payload["d"]["activities"][0]["timestamps"]["end"] = end_unix
        if party:
            payload["d"]["activities"][0]["party"] = party
        if stream_url:
            payload["d"]["activities"][0]["url"] = stream_url
        if activity_type == 6:
            payload["d"]["activities"][0]["name"] = 'Spotify'
            payload["d"]["activities"][0]["party"] = {'id': f'spotify:{client_id}'}
            payload["d"]["activities"][0]["details"] = name
            if details:
                payload["d"]["activities"][0]["assets"]["large_text"] = details
            payload["d"]["activities"][0]["type"] = 2
        await self.ws.change_custom_presence(payload=payload)
    async def change_voice_state(
        self,
        *,
        channel: Optional[Snowflake],
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
        preferred_region: Optional[str] = MISSING,
    ) -> None:
        state = self._connection
        ws = self.ws
        channel_id = channel.id if channel else None
        if preferred_region is None or channel_id is None:
            region = None
        else:
            region = str(preferred_region) if preferred_region else state.preferred_rtc_region
        await ws.voice_state(None, channel_id, self_mute, self_deaf, self_video, preferred_region=region)
    async def fetch_guilds(self, *, with_counts: bool = True) -> List[UserGuild]:
        state = self._connection
        guilds = await state.http.get_guilds(with_counts)
        return [UserGuild(data=data, state=state) for data in guilds]
    async def fetch_template(self, code: Union[Template, str]) -> Template:
        code = utils.resolve_template(code)
        data = await self.http.get_template(code)
        return Template(data=data, state=self._connection)
    async def fetch_guild(self, guild_id: int, /, *, with_counts: bool = True) -> Guild:
        state = self._connection
        data = await state.http.get_guild(guild_id, with_counts)
        guild = state.create_guild(data)
        guild._cs_joined = True
        return guild
    async def fetch_guild_preview(self, guild_id: int, /) -> Guild:
        state = self._connection
        data = await state.http.get_guild_preview(guild_id)
        return state.create_guild(data)
    async def create_guild(
        self,
        name: str,
        icon: bytes = MISSING,
        code: str = MISSING,
    ) -> Guild:
        state = self._connection
        if icon is not MISSING:
            icon_base64 = utils._bytes_to_base64_data(icon)
        else:
            icon_base64 = None
        if code:
            data = await state.http.create_from_template(code, name, icon_base64)
        else:
            data = await state.http.create_guild(name, icon_base64)
        guild = state.create_guild(data)
        guild._cs_joined = True
        return guild
    async def join_guild(self, guild_id: int, /, lurking: bool = False) -> Guild:
        state = self._connection
        data = await state.http.join_guild(guild_id, lurking, state.session_id)
        guild = state.create_guild(data)
        guild._cs_joined = not lurking
        return guild
    async def leave_guild(self, guild: Snowflake, /, lurking: bool = MISSING) -> None:
        if lurking is MISSING:
            attr = getattr(guild, 'joined', lurking)
            if attr is not MISSING:
                lurking = not attr
            elif (new_guild := self._connection._get_guild(guild.id)) is not None:
                lurking = not new_guild.is_joined()
        await self.http.leave_guild(guild.id, lurking=lurking or False)
    async def fetch_stage_instance(self, channel_id: int, /) -> StageInstance:
        data = await self.http.get_stage_instance(channel_id)
        guild = self.get_guild(int(data['guild_id']))
        return StageInstance(guild=guild, state=self._connection, data=data)
    async def invites(self) -> List[Invite]:
        r
        state = self._connection
        data = await state.http.get_friend_invites()
        return [Invite.from_incomplete(state=state, data=d) for d in data]
    async def fetch_invite(
        self,
        url: Union[Invite, str],
        /,
        *,
        with_counts: bool = True,
        scheduled_event_id: Optional[int] = None,
    ) -> Invite:
        resolved = utils.resolve_invite(url)
        if scheduled_event_id and resolved.event:
            raise ValueError('Cannot specify scheduled_event_id and contain an event_id in the url.')
        scheduled_event_id = scheduled_event_id or resolved.event
        data = await self.http.get_invite(
            resolved.code,
            with_counts=with_counts,
            guild_scheduled_event_id=scheduled_event_id,
        )
        return Invite.from_incomplete(state=self._connection, data=data)
    async def create_invite(self) -> Invite:
        state = self._connection
        data = await state.http.create_friend_invite()
        return Invite.from_incomplete(state=state, data=data)
    async def accept_invite(self, url: Union[Invite, str], /) -> Invite:
        state = self._connection
        resolved = utils.resolve_invite(url)
        data = await state.http.get_invite(
            resolved.code,
            with_counts=True,
            input_value=resolved.code if isinstance(url, Invite) else url,
        )
        if isinstance(url, Invite):
            invite = url
        else:
            invite = Invite.from_incomplete(state=state, data=data)
        state = self._connection
        type = invite.type
        kwargs = {}
        if not invite._message:
            kwargs = {
                'guild_id': getattr(invite.guild, 'id', MISSING),
                'channel_id': getattr(invite.channel, 'id', MISSING),
                'channel_type': getattr(invite.channel, 'type', MISSING),
            }
        data = await state.http.accept_invite(
            invite.code, type, state.session_id or utils._generate_session_id(), message=invite._message, **kwargs
        )
        return Invite.from_incomplete(state=state, data=data, message=invite._message)
    async def delete_invite(self, invite: Union[Invite, str], /) -> Invite:
        resolved = utils.resolve_invite(invite)
        state = self._connection
        data = await state.http.delete_invite(resolved.code)
        return Invite.from_incomplete(state=state, data=data)
    async def revoke_invites(self) -> List[Invite]:
        r
        state = self._connection
        data = await state.http.delete_friend_invites()
        return [Invite(state=state, data=d) for d in data]
    async def fetch_widget(self, guild_id: int, /) -> Widget:
        data = await self.http.get_widget(guild_id)
        return Widget(state=self._connection, data=data)
    async def fetch_user(self, user_id: int, /) -> User:
        data = await self.http.get_user(user_id)
        return User(state=self._connection, data=data)
    @overload
    async def fetch_user_named(self, user: str, /) -> User:
        ...
    @overload
    async def fetch_user_named(self, username: str, discriminator: str, /) -> User:
        ...
    async def fetch_user_named(self, *args: str) -> User:
        if len(args) == 1:
            username, _, discrim = args[0].partition('
        elif len(args) == 2:
            username, discrim = args
        else:
            raise TypeError(f'fetch_user_named() takes 1 or 2 arguments but {len(args)} were given')
        data = await self.http.get_user_named(username, discrim)
        return User(state=self._connection, data=data)
    async def fetch_user_profile(
        self,
        user_id: int,
        /,
        *,
        with_mutual_guilds: bool = True,
        with_mutual_friends_count: bool = False,
        with_mutual_friends: bool = True,
    ) -> UserProfile:
        state = self._connection
        data = await state.http.get_user_profile(
            user_id, with_mutual_guilds=with_mutual_guilds, with_mutual_friends_count=with_mutual_friends_count
        )
        mutual_friends = None
        if with_mutual_friends and not data['user'].get('bot', False):
            mutual_friends = await state.http.get_mutual_friends(user_id)
        return UserProfile(state=state, data=data, mutual_friends=mutual_friends)
    async def fetch_channel(self, channel_id: int, /) -> Union[GuildChannel, PrivateChannel, Thread]:
        data = await self.http.get_channel(channel_id)
        factory, ch_type = _threaded_channel_factory(data['type'])
        if factory is None:
            raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(data))
        if ch_type in (ChannelType.group, ChannelType.private):
            channel = factory(me=self.user, data=data, state=self._connection)
        else:
            guild_id = int(data['guild_id'])
            guild = self._connection._get_or_create_unavailable_guild(guild_id)
            channel = factory(guild=guild, state=self._connection, data=data)
        return channel
    async def fetch_webhook(self, webhook_id: int, /) -> Webhook:
        data = await self.http.get_webhook(webhook_id)
        return Webhook.from_state(data, state=self._connection)
    async def fetch_sticker(self, sticker_id: int, /) -> Union[StandardSticker, GuildSticker]:
        data = await self.http.get_sticker(sticker_id)
        cls, _ = _sticker_factory(data['type'])
        return cls(state=self._connection, data=data)
    async def sticker_packs(self) -> List[StickerPack]:
        state = self._connection
        data = await self.http.list_premium_sticker_packs(state.country_code or 'US', state.locale)
        return [StickerPack(state=state, data=pack) for pack in data['sticker_packs']]
    async def fetch_sticker_pack(self, pack_id: int, /):
        data = await self.http.get_sticker_pack(pack_id)
        return StickerPack(state=self._connection, data=data)
    async def notes(self) -> List[Note]:
        state = self._connection
        data = await state.http.get_notes()
        return [Note(state, int(id), note=note) for id, note in data.items()]
    async def fetch_note(self, user_id: int, /) -> Note:
        note = Note(self._connection, int(user_id))
        await note.fetch()
        return note
    async def fetch_connections(self) -> List[Connection]:
        state = self._connection
        data = await state.http.get_connections()
        return [Connection(data=d, state=state) for d in data]
    async def authorize_connection(
        self,
        type: ConnectionType,
        two_way_link_type: Optional[ClientType] = None,
        two_way_user_code: Optional[str] = None,
        continuation: bool = False,
    ) -> str:
        data = await self.http.authorize_connection(
            str(type), str(two_way_link_type) if two_way_link_type else None, two_way_user_code, continuation=continuation
        )
        return data['url']
    async def create_connection(
        self,
        type: ConnectionType,
        code: str,
        state: str,
        *,
        two_way_link_code: Optional[str] = None,
        insecure: bool = True,
        friend_sync: bool = MISSING,
    ) -> None:
        friend_sync = (
            friend_sync if friend_sync is not MISSING else type in (ConnectionType.facebook, ConnectionType.contacts)
        )
        await self.http.add_connection(
            str(type),
            code=code,
            state=state,
            two_way_link_code=two_way_link_code,
            insecure=insecure,
            friend_sync=friend_sync,
        )
    async def fetch_private_channels(self) -> List[PrivateChannel]:
        state = self._connection
        channels = await state.http.get_private_channels()
        return [_private_channel_factory(data['type'])[0](me=self.user, data=data, state=state) for data in channels]
    async def fetch_settings(self) -> UserSettings:
        state = self._connection
        data = await state.http.get_proto_settings(1)
        return UserSettings(state, data['settings'])
    @utils.deprecated('Client.fetch_settings')
    async def legacy_settings(self) -> LegacyUserSettings:
        state = self._connection
        data = await state.http.get_settings()
        return LegacyUserSettings(data=data, state=state)
    async def email_settings(self) -> EmailSettings:
        state = self._connection
        data = await state.http.get_email_settings()
        return EmailSettings(data=data, state=state)
    async def fetch_tracking_settings(self) -> TrackingSettings:
        state = self._connection
        data = await state.http.get_tracking()
        return TrackingSettings(state=state, data=data)
    @utils.deprecated('Client.edit_settings')
    @utils.copy_doc(LegacyUserSettings.edit)
    async def edit_legacy_settings(self, **kwargs) -> LegacyUserSettings:
        payload = {}
        content_filter = kwargs.pop('explicit_content_filter', None)
        if content_filter:
            payload['explicit_content_filter'] = content_filter.value
        animate_stickers = kwargs.pop('animate_stickers', None)
        if animate_stickers:
            payload['animate_stickers'] = animate_stickers.value
        friend_source_flags = kwargs.pop('friend_source_flags', None)
        if friend_source_flags:
            payload['friend_source_flags'] = friend_source_flags.to_dict()
        friend_discovery_flags = kwargs.pop('friend_discovery_flags', None)
        if friend_discovery_flags:
            payload['friend_discovery_flags'] = friend_discovery_flags.value
        guild_positions = kwargs.pop('guild_positions', None)
        if guild_positions:
            guild_positions = [str(x.id) for x in guild_positions]
            payload['guild_positions'] = guild_positions
        restricted_guilds = kwargs.pop('restricted_guilds', None)
        if restricted_guilds:
            restricted_guilds = [str(x.id) for x in restricted_guilds]
            payload['restricted_guilds'] = restricted_guilds
        activity_restricted_guilds = kwargs.pop('activity_restricted_guilds', None)
        if activity_restricted_guilds:
            activity_restricted_guilds = [str(x.id) for x in activity_restricted_guilds]
            payload['activity_restricted_guild_ids'] = activity_restricted_guilds
        activity_joining_restricted_guilds = kwargs.pop('activity_joining_restricted_guilds', None)
        if activity_joining_restricted_guilds:
            activity_joining_restricted_guilds = [str(x.id) for x in activity_joining_restricted_guilds]
            payload['activity_joining_restricted_guild_ids'] = activity_joining_restricted_guilds
        status = kwargs.pop('status', None)
        if status:
            payload['status'] = status.value
        custom_activity = kwargs.pop('custom_activity', MISSING)
        if custom_activity is not MISSING:
            payload['custom_status'] = custom_activity and custom_activity.to_legacy_settings_dict()
        theme = kwargs.pop('theme', None)
        if theme:
            payload['theme'] = theme.value
        locale = kwargs.pop('locale', None)
        if locale:
            payload['locale'] = str(locale)
        payload.update(kwargs)
        state = self._connection
        data = await state.http.edit_settings(**payload)
        return LegacyUserSettings(data=data, state=state)
    async def fetch_relationships(self) -> List[Relationship]:
        state = self._connection
        data = await state.http.get_relationships()
        return [Relationship(state=state, data=d) for d in data]
    async def friend_suggestions(self) -> List[FriendSuggestion]:
        state = self._connection
        data = await state.http.get_friend_suggestions()
        return [FriendSuggestion(state=state, data=d) for d in data]
    async def fetch_country_code(self) -> str:
        data = await self.http.get_country_code()
        return data['country_code']
    async def fetch_preferred_voice_regions(self) -> List[str]:
        data = await self.http.get_preferred_voice_regions()
        return [v['region'] for v in data]
    async def create_dm(self, user: Snowflake, /) -> DMChannel:
        state = self._connection
        found = state._get_private_channel_by_user(user.id)
        if found:
            return found
        data = await state.http.start_private_message(user.id)
        return state.add_dm_channel(data)
    async def create_group(self, *recipients: Snowflake) -> GroupChannel:
        r
        if len(recipients) == 1:
            raise TypeError('Cannot create a group with only one recipient')
        users: List[_Snowflake] = [u.id for u in recipients]
        state = self._connection
        data = await state.http.start_group(users)
        return GroupChannel(me=self.user, data=data, state=state)
    @overload
    async def send_friend_request(self, user: _UserTag, /) -> None:
        ...
    @overload
    async def send_friend_request(self, user: str, /) -> None:
        ...
    @overload
    async def send_friend_request(self, username: str, discriminator: str, /) -> None:
        ...
    async def send_friend_request(self, *args: Union[_UserTag, str]) -> None:
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, _UserTag):
                user = str(user)
            username, _, discrim = user.partition('
        elif len(args) == 2:
            username, discrim = args
        else:
            raise TypeError(f'send_friend_request() takes 1 or 2 arguments but {len(args)} were given')
        state = self._connection
        await state.http.send_friend_request(username, discrim or 0)
    async def applications(self, *, with_team_applications: bool = True) -> List[Application]:
        state = self._connection
        data = await state.http.get_my_applications(with_team_applications=with_team_applications)
        return [Application(state=state, data=d) for d in data]
    async def detectable_applications(self) -> List[PartialApplication]:
        state = self._connection
        data = await state.http.get_detectable_applications()
        return [PartialApplication(state=state, data=d) for d in data]
    async def fetch_application(self, application_id: int, /) -> Application:
        state = self._connection
        data = await state.http.get_my_application(application_id)
        return Application(state=state, data=data)
    async def fetch_partial_application(self, application_id: int, /) -> PartialApplication:
        state = self._connection
        data = await state.http.get_partial_application(application_id)
        return PartialApplication(state=state, data=data)
    async def fetch_public_application(self, application_id: int, /, *, with_guild: bool = False) -> PartialApplication:
        state = self._connection
        data = await state.http.get_public_application(application_id, with_guild=with_guild)
        return PartialApplication(state=state, data=data)
    async def fetch_public_applications(self, *application_ids: int) -> List[PartialApplication]:
        r
        if not application_ids:
            return []
        state = self._connection
        data = await state.http.get_public_applications(application_ids)
        return [PartialApplication(state=state, data=d) for d in data]
    async def teams(self, *, with_payout_account_status: bool = False) -> List[Team]:
        state = self._connection
        data = await state.http.get_teams(include_payout_account_status=with_payout_account_status)
        return [Team(state=state, data=d) for d in data]
    async def fetch_team(self, team_id: int, /) -> Team:
        state = self._connection
        data = await state.http.get_team(team_id)
        return Team(state=state, data=data)
    async def create_application(self, name: str, /, *, team: Optional[Snowflake] = None) -> Application:
        state = self._connection
        data = await state.http.create_app(name, team.id if team else None)
        return Application(state=state, data=data)
    async def create_team(self, name: str, /):
        state = self._connection
        data = await state.http.create_team(name)
        return Team(state=state, data=data)
    async def search_companies(self, query: str, /) -> List[Company]:
        state = self._connection
        data = await state.http.search_companies(query)
        return [Company(data=d) for d in data]
    async def activity_statistics(self) -> List[ApplicationActivityStatistics]:
        state = self._connection
        data = await state.http.get_activity_statistics()
        return [ApplicationActivityStatistics(state=state, data=d) for d in data]
    async def relationship_activity_statistics(self) -> List[ApplicationActivityStatistics]:
        state = self._connection
        data = await state.http.get_global_activity_statistics()
        return [ApplicationActivityStatistics(state=state, data=d) for d in data]
    async def payment_sources(self) -> List[PaymentSource]:
        state = self._connection
        data = await state.http.get_payment_sources()
        return [PaymentSource(state=state, data=d) for d in data]
    async def fetch_payment_source(self, source_id: int, /) -> PaymentSource:
        state = self._connection
        data = await state.http.get_payment_source(source_id)
        return PaymentSource(state=state, data=data)
    async def create_payment_source(
        self,
        *,
        token: str,
        payment_gateway: PaymentGateway,
        billing_address: BillingAddress,
        billing_address_token: Optional[str] = MISSING,
        return_url: Optional[str] = None,
        bank: Optional[str] = None,
    ) -> PaymentSource:
        state = self._connection
        billing_address.state = state
        data = await state.http.create_payment_source(
            token=token,
            payment_gateway=int(payment_gateway),
            billing_address=billing_address.to_dict(),
            billing_address_token=billing_address_token or await billing_address.validate()
            if billing_address is not None
            else None,
            return_url=return_url,
            bank=bank,
        )
        return PaymentSource(state=state, data=data)
    async def subscriptions(self, limit: Optional[int] = None, with_inactive: bool = False) -> List[Subscription]:
        state = self._connection
        data = await state.http.get_subscriptions(limit=limit, include_inactive=with_inactive)
        return [Subscription(state=state, data=d) for d in data]
    async def premium_guild_subscriptions(self) -> List[PremiumGuildSubscription]:
        state = self._connection
        data = await state.http.get_applied_guild_subscriptions()
        return [PremiumGuildSubscription(state=state, data=d) for d in data]
    async def premium_guild_subscription_slots(self) -> List[PremiumGuildSubscriptionSlot]:
        state = self._connection
        data = await state.http.get_guild_subscription_slots()
        return [PremiumGuildSubscriptionSlot(state=state, data=d) for d in data]
    async def premium_guild_subscription_cooldown(self) -> PremiumGuildSubscriptionCooldown:
        state = self._connection
        data = await state.http.get_guild_subscriptions_cooldown()
        return PremiumGuildSubscriptionCooldown(state=state, data=data)
    async def fetch_subscription(self, subscription_id: int, /) -> Subscription:
        state = self._connection
        data = await state.http.get_subscription(subscription_id)
        return Subscription(state=state, data=data)
    async def preview_subscription(
        self,
        items: List[SubscriptionItem],
        *,
        payment_source: Optional[Snowflake] = None,
        currency: str = 'usd',
        trial: Optional[Snowflake] = None,
        apply_entitlements: bool = True,
        renewal: bool = False,
        code: Optional[str] = None,
        metadata: Optional[MetadataObject] = None,
        guild: Optional[Snowflake] = None,
    ) -> SubscriptionInvoice:
        state = self._connection
        metadata = dict(metadata) if metadata else {}
        if guild:
            metadata['guild_id'] = str(guild.id)
        data = await state.http.preview_subscriptions_update(
            [item.to_dict(False) for item in items],
            currency,
            payment_source_id=payment_source.id if payment_source else None,
            trial_id=trial.id if trial else None,
            apply_entitlements=apply_entitlements,
            renewal=renewal,
            code=code,
            metadata=metadata if metadata else None,
        )
        return SubscriptionInvoice(None, data=data, state=state)
    async def create_subscription(
        self,
        items: List[SubscriptionItem],
        payment_source: Snowflake,
        currency: str = 'usd',
        *,
        trial: Optional[Snowflake] = None,
        payment_source_token: Optional[str] = None,
        purchase_token: Optional[str] = None,
        return_url: Optional[str] = None,
        gateway_checkout_context: Optional[str] = None,
        code: Optional[str] = None,
        metadata: Optional[MetadataObject] = None,
        guild: Optional[Snowflake] = None,
    ) -> Subscription:
        state = self._connection
        metadata = dict(metadata) if metadata else {}
        if guild:
            metadata['guild_id'] = str(guild.id)
        data = await state.http.create_subscription(
            [i.to_dict(False) for i in items],
            payment_source.id,
            currency,
            trial_id=trial.id if trial else None,
            payment_source_token=payment_source_token,
            return_url=return_url,
            purchase_token=purchase_token,
            gateway_checkout_context=gateway_checkout_context,
            code=code,
            metadata=metadata if metadata else None,
        )
        return Subscription(state=state, data=data)
    async def payments(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
    ) -> AsyncIterator[Payment]:
        state = self._connection
        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await state.http.get_payments(retrieve, after=after_id)
            if data:
                if limit is not None:
                    limit -= len(data)
                after = Object(id=int(data[0]['id']))
            return data, after, limit
        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await state.http.get_payments(retrieve, before=before_id)
            if data:
                if limit is not None:
                    limit -= len(data)
                before = Object(id=int(data[-1]['id']))
            return data, before, limit
        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))
        if oldest_first is None:
            reverse = after is not None
        else:
            reverse = oldest_first
        after = after or OLDEST_OBJECT
        predicate = None
        if reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda m: int(m['id']) < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda m: int(m['id']) > after.id
        while True:
            retrieve = min(100 if limit is None else limit, 100)
            if retrieve < 1:
                return
            data, state, limit = await strategy(retrieve, state, limit)
            if len(data) < 100:
                limit = 0
            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)
            for payment in data:
                yield Payment(data=payment, state=state)
    async def fetch_payment(self, payment_id: int) -> Payment:
        state = self._connection
        data = await state.http.get_payment(payment_id)
        return Payment(data=data, state=state)
    async def promotions(self, claimed: bool = False) -> List[Promotion]:
        state = self._connection
        data = (
            await state.http.get_claimed_promotions(state.locale)
            if claimed
            else await state.http.get_promotions(state.locale)
        )
        return [Promotion(state=state, data=d) for d in data]
    async def trial_offer(self) -> TrialOffer:
        state = self._connection
        data = await state.http.get_trial_offer()
        return TrialOffer(data=data, state=state)
    async def pricing_promotion(self) -> Optional[PricingPromotion]:
        state = self._connection
        data = await state.http.get_pricing_promotion()
        state.country_code = data['country_code']
        if data['localized_pricing_promo'] is not None:
            return PricingPromotion(data=data['localized_pricing_promo'])
    async def library(self) -> List[LibraryApplication]:
        state = self._connection
        data = await state.http.get_library_entries(state.country_code or 'US')
        return [LibraryApplication(state=state, data=d) for d in data]
    async def authorizations(self) -> List[OAuth2Token]:
        state = self._connection
        data = await state.http.get_oauth2_tokens()
        return [OAuth2Token(state=state, data=d) for d in data]
    async def fetch_authorization(
        self,
        application_id: int,
        /,
        *,
        scopes: Collection[str],
        response_type: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
        code_challenge: Optional[str] = None,
        state: Optional[str] = None,
    ) -> OAuth2Authorization:
        state = self._connection
        data = await state.http.get_oauth2_authorization(
            application_id,
            list(scopes),
            response_type,
            redirect_uri,
            code_challenge_method,
            code_challenge,
            state,
        )
        return OAuth2Authorization(
            state=state,
            data=data,
            scopes=list(scopes),
            response_type=response_type,
            code_challenge_method=code_challenge_method,
            code_challenge=code_challenge,
        )
    async def create_authorization(
        self,
        application_id: int,
        /,
        *,
        scopes: Collection[str],
        response_type: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
        code_challenge: Optional[str] = None,
        state: Optional[str] = None,
        guild: Snowflake = MISSING,
        channel: Snowflake = MISSING,
        permissions: Permissions = MISSING,
    ) -> str:
        state = self._connection
        data = await state.http.authorize_oauth2(
            application_id,
            list(scopes),
            response_type,
            redirect_uri,
            code_challenge_method,
            code_challenge,
            state,
            guild_id=guild.id if guild else None,
            webhook_channel_id=channel.id if channel else None,
            permissions=permissions.value if permissions else None,
        )
        return data['location']
    async def entitlements(
        self, *, with_sku: bool = True, with_application: bool = True, entitlement_type: Optional[EntitlementType] = None
    ) -> List[Entitlement]:
        state = self._connection
        data = await state.http.get_user_entitlements(
            with_sku=with_sku,
            with_application=with_application,
            entitlement_type=int(entitlement_type) if entitlement_type else None,
        )
        return [Entitlement(state=state, data=d) for d in data]
    async def giftable_entitlements(self) -> List[Entitlement]:
        state = self._connection
        data = await state.http.get_giftable_entitlements(state.country_code or 'US')
        return [Entitlement(state=state, data=d) for d in data]
    async def premium_entitlements(self, *, exclude_consumed: bool = True) -> List[Entitlement]:
        return await self.fetch_entitlements(
            self._connection.premium_subscriptions_application.id, exclude_consumed=exclude_consumed
        )
    async def fetch_entitlements(self, application_id: int, /, *, exclude_consumed: bool = True) -> List[Entitlement]:
        state = self._connection
        data = await state.http.get_user_app_entitlements(application_id, exclude_consumed=exclude_consumed)
        return [Entitlement(data=entitlement, state=state) for entitlement in data]
    async def fetch_gift(
        self, code: Union[Gift, str], *, with_application: bool = False, with_subscription_plan: bool = True
    ) -> Gift:
        state = self._connection
        code = utils.resolve_gift(code)
        data = await state.http.get_gift(
            code, with_application=with_application, with_subscription_plan=with_subscription_plan
        )
        return Gift(state=state, data=data)
    async def fetch_sku(self, sku_id: int, /, *, localize: bool = True) -> SKU:
        state = self._connection
        data = await state.http.get_sku(sku_id, country_code=state.country_code or 'US', localize=localize)
        return SKU(state=state, data=data)
    async def fetch_store_listing(self, listing_id: int, /, *, localize: bool = True) -> StoreListing:
        state = self._connection
        data = await state.http.get_store_listing(listing_id, country_code=state.country_code or 'US', localize=localize)
        return StoreListing(state=state, data=data)
    async def fetch_published_store_listing(self, sku_id: int, /, *, localize: bool = True) -> StoreListing:
        state = self._connection
        data = await state.http.get_store_listing_by_sku(
            sku_id,
            country_code=state.country_code or 'US',
            localize=localize,
        )
        return StoreListing(state=state, data=data)
    async def fetch_published_store_listings(self, application_id: int, /, localize: bool = True) -> List[StoreListing]:
        state = self._connection
        data = await state.http.get_app_store_listings(
            application_id, country_code=state.country_code or 'US', localize=localize
        )
        return [StoreListing(state=state, data=d) for d in data]
    async def fetch_primary_store_listing(self, application_id: int, /, *, localize: bool = True) -> StoreListing:
        state = self._connection
        data = await state.http.get_app_store_listing(
            application_id, country_code=state.country_code or 'US', localize=localize
        )
        return StoreListing(state=state, data=data)
    async def fetch_primary_store_listings(self, *application_ids: int, localize: bool = True) -> List[StoreListing]:
        r
        if not application_ids:
            return []
        state = self._connection
        data = await state.http.get_apps_store_listing(
            application_ids, country_code=state.country_code or 'US', localize=localize
        )
        return [StoreListing(state=state, data=listing) for listing in data]
    async def premium_subscription_plans(self) -> List[SubscriptionPlan]:
        state = self._connection
        sku_ids = [v for k, v in state.premium_subscriptions_sku_ids.items() if k != 'none']
        data = await state.http.get_store_listings_subscription_plans(sku_ids)
        return [SubscriptionPlan(state=state, data=d) for d in data]
    async def fetch_sku_subscription_plans(
        self,
        sku_id: int,
        /,
        *,
        country_code: str = MISSING,
        payment_source: Snowflake = MISSING,
        with_unpublished: bool = False,
    ) -> List[SubscriptionPlan]:
        state = self._connection
        data = await state.http.get_store_listing_subscription_plans(
            sku_id,
            country_code=country_code if country_code is not MISSING else None,
            payment_source_id=payment_source.id if payment_source is not MISSING else None,
            include_unpublished=with_unpublished,
        )
        return [SubscriptionPlan(state=state, data=d) for d in data]
    async def fetch_skus_subscription_plans(
        self,
        *sku_ids: int,
        country_code: str = MISSING,
        payment_source: Snowflake = MISSING,
        with_unpublished: bool = False,
    ) -> List[SubscriptionPlan]:
        r
        if not sku_ids:
            return []
        state = self._connection
        data = await state.http.get_store_listings_subscription_plans(
            sku_ids,
            country_code=country_code if country_code is not MISSING else None,
            payment_source_id=payment_source.id if payment_source is not MISSING else None,
            include_unpublished=with_unpublished,
        )
        return [SubscriptionPlan(state=state, data=d) for d in data]
    async def fetch_eula(self, eula_id: int, /) -> EULA:
        data = await self._connection.http.get_eula(eula_id)
        return EULA(data=data)
    async def fetch_live_build_ids(self, *branch_ids: int) -> Dict[int, Optional[int]]:
        r
        if not branch_ids:
            return {}
        data = await self._connection.http.get_build_ids(branch_ids)
        return {int(b['id']): utils._get_as_snowflake(b, 'live_build_id') for b in data}
    async def price_tiers(self) -> List[int]:
        return await self._connection.http.get_price_tiers()
    async def fetch_price_tier(self, price_tier: int, /) -> Dict[str, int]:
        return await self._connection.http.get_price_tier(price_tier)
    async def premium_usage(self) -> PremiumUsage:
        data = await self._connection.http.get_premium_usage()
        return PremiumUsage(data=data)
    async def recent_mentions(
        self,
        *,
        limit: Optional[int] = 25,
        before: SnowflakeTime = MISSING,
        guild: Snowflake = MISSING,
        roles: bool = True,
        everyone: bool = True,
    ) -> AsyncIterator[Message]:
        state = self._connection
        async def strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await state.http.get_recent_mentions(
                retrieve, before=before_id, guild_id=guild.id if guild else None, roles=roles, everyone=everyone
            )
            if data:
                if limit is not None:
                    limit -= len(data)
                before = Object(id=int(data[-1]['id']))
            return data, before, limit
        if isinstance(before, datetime):
            state = Object(id=utils.time_snowflake(before, high=False))
        else:
            state = before
        while True:
            retrieve = min(100 if limit is None else limit, 100)
            if retrieve < 1:
                return
            data, state, limit = await strategy(retrieve, state, limit)
            if len(data) < 100:
                limit = 0
            for raw_message in data:
                channel, _ = state._get_guild_channel(raw_message)
                yield state.create_message(channel=channel, data=raw_message)
    async def delete_recent_mention(self, message: Snowflake) -> None:
        await self._connection.http.delete_recent_mention(message.id)
    async def user_affinities(self) -> List[UserAffinity]:
        state = self._connection
        data = await state.http.get_user_affinities()
        return [UserAffinity(data=d, state=state) for d in data['user_affinities']]
    async def guild_affinities(self) -> List[GuildAffinity]:
        state = self._connection
        data = await state.http.get_guild_affinities()
        return [GuildAffinity(data=d, state=state) for d in data['guild_affinities']]
    async def join_active_developer_program(self, *, application: Snowflake, channel: Snowflake) -> int:
        data = await self._connection.http.enroll_active_developer(application.id, channel.id)
        return int(data['follower']['webhook_id'])
    async def leave_active_developer_program(self) -> None:
        await self._connection.http.unenroll_active_developer()
    async def report_unverified_application(
        self,
        name: str,
        *,
        icon: File,
        os: OperatingSystem,
        executable: str = MISSING,
        publisher: str = MISSING,
        distributor: Distributor = MISSING,
        sku: str = MISSING,
    ) -> UnverifiedApplication:
        state = self._connection
        data = await state.http.report_unverified_application(
            name=name,
            icon_hash=icon.md5.hexdigest(),
            os=str(os),
            executable=executable,
            publisher=publisher,
            distributor=str(distributor) if distributor else None,
            sku=sku,
        )
        app = UnverifiedApplication(data=data)
        if 'icon' in app.missing_data:
            icon_data = utils._bytes_to_base64_data(icon.fp.read())
            await state.http.upload_unverified_application_icon(app.name, app.hash, icon_data)
        return app
    @overload
    async def fetch_experiments(
        self, with_guild_experiments: Literal[True] = ...
    ) -> List[Union[UserExperiment, GuildExperiment]]:
        ...
    @overload
    async def fetch_experiments(self, with_guild_experiments: Literal[False] = ...) -> List[UserExperiment]:
        ...
    @overload
    async def fetch_experiments(
        self, with_guild_experiments: bool = True
    ) -> Union[List[UserExperiment], List[Union[UserExperiment, GuildExperiment]]]:
        ...
    async def fetch_experiments(
        self, with_guild_experiments: bool = True
    ) -> Union[List[UserExperiment], List[Union[UserExperiment, GuildExperiment]]]:
        state = self._connection
        data = await state.http.get_experiments(with_guild_experiments=with_guild_experiments)
        experiments: List[Union[UserExperiment, GuildExperiment]] = [
            UserExperiment(state=state, data=exp) for exp in data['assignments']
        ]
        for exp in data.get('guild_experiments', []):
            experiments.append(GuildExperiment(state=state, data=exp))
        return experiments
    async def join_hub_waitlist(self, email: str, school: str) -> None:
        await self._connection.http.hub_waitlist_signup(email, school)
    async def lookup_hubs(self, email: str, /) -> List[Guild]:
        state = self._connection
        data = await state.http.hub_lookup(email)
        return [state.create_guild(d) for d in data.get('guilds_info', [])]
    @overload
    async def join_hub(self, guild: Snowflake, email: str, *, code: None = ...) -> None:
        ...
    @overload
    async def join_hub(self, guild: Snowflake, email: str, *, code: str = ...) -> Guild:
        ...
    async def join_hub(self, guild: Snowflake, email: str, *, code: Optional[str] = None) -> Optional[Guild]:
        state = self._connection
        if not code:
            data = await state.http.hub_lookup(email, guild.id)
            if not data.get('has_matching_guild'):
                raise ValueError('Guild does not match email')
            return
        data = await state.http.join_hub(email, guild.id, code)
        return state.create_guild(data['guild'])
    async def pomelo_suggestion(self) -> str:
        data = await self.http.pomelo_suggestion()
        return data['username']
    async def check_pomelo_username(self, username: str) -> bool:
        data = await self.http.pomelo_attempt(username)
        return data['taken']