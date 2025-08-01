from __future__ import annotations
import asyncio
from collections import deque
import logging
import struct
import time
import threading
import traceback
import zlib
from typing import Any, Callable, Coroutine, Dict, List, TYPE_CHECKING, NamedTuple, Optional, Sequence, TypeVar
import aiohttp
import yarl
from . import utils
from .activity import BaseActivity, Spotify
from .enums import SpeakingState
from .errors import ConnectionClosed
from .flags import Capabilities
_log = logging.getLogger(__name__)
__all__ = (
    'DiscordWebSocket',
    'KeepAliveHandler',
    'VoiceKeepAliveHandler',
    'DiscordVoiceWebSocket',
    'ReconnectWebSocket',
)
if TYPE_CHECKING:
    from typing_extensions import Self
    from .activity import ActivityTypes
    from .client import Client
    from .enums import Status
    from .state import ConnectionState
    from .types.snowflake import Snowflake
    from .types.gateway import BulkGuildSubscribePayload
    from .voice_client import VoiceClient
class ReconnectWebSocket(Exception):
    def __init__(self, *, resume: bool = True):
        self.resume = resume
        self.op: str = 'RESUME' if resume else 'IDENTIFY'
class WebSocketClosure(Exception):
    pass
class EventListener(NamedTuple):
    predicate: Callable[[Dict[str, Any]], bool]
    event: str
    result: Optional[Callable[[Dict[str, Any]], Any]]
    future: asyncio.Future[Any]
class GatewayRatelimiter:
    def __init__(self, count: int = 110, per: float = 60.0) -> None:
        self.max: int = count
        self.remaining: int = count
        self.window: float = 0.0
        self.per: float = per
        self.lock: asyncio.Lock = asyncio.Lock()
    def is_ratelimited(self) -> bool:
        current = time.time()
        if current > self.window + self.per:
            return False
        return self.remaining == 0
    def get_delay(self) -> float:
        current = time.time()
        if current > self.window + self.per:
            self.remaining = self.max
        if self.remaining == self.max:
            self.window = current
        if self.remaining == 0:
            return self.per - (current - self.window)
        self.remaining -= 1
        return 0.0
    async def block(self) -> None:
        async with self.lock:
            delta = self.get_delay()
            if delta:
                _log.warning('Gateway is ratelimited, waiting %.2f seconds.', delta)
                await asyncio.sleep(delta)
class KeepAliveHandler:
    def __init__(self, *, ws: DiscordWebSocket, interval: Optional[float] = None):
        self.ws: DiscordWebSocket = ws
        self.interval: Optional[float] = interval
        self.heartbeat_timeout: float = self.ws._max_heartbeat_timeout
        self.msg: str = 'Keeping websocket alive.'
        self.block_msg: str = 'Heartbeat blocked for more than %s seconds.'
        self.behind_msg: str = 'Can\'t keep up, websocket is %.1fs behind.'
        self.not_responding_msg: str = 'Gateway has stopped responding. Closing and restarting.'
        self.no_stop_msg: str = 'An error occurred while stopping the gateway. Ignoring.'
        self._stop: asyncio.Event = asyncio.Event()
        self._last_send: float = time.perf_counter()
        self._last_recv: float = time.perf_counter()
        self._last_ack: float = time.perf_counter()
        self.latency: float = float('inf')
    async def run(self) -> None:
        while True:
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass
            else:
                return
            if self._last_recv + self.heartbeat_timeout < time.perf_counter():
                _log.warning(self.not_responding_msg)
                try:
                    await self.ws.close(4000)
                except Exception:
                    _log.exception(self.no_stop_msg)
                finally:
                    self.stop()
                    return
            data = self.get_payload()
            _log.debug(self.msg)
            try:
                total = 0
                while True:
                    try:
                        await asyncio.wait_for(self.ws.send_heartbeat(data), timeout=10)
                        break
                    except asyncio.TimeoutError:
                        total += 10
                        stack = ''.join(traceback.format_stack())
                        msg = f'{self.block_msg}\nLoop traceback (most recent call last):\n{stack}'
                        _log.warning(msg, total)
            except Exception:
                self.stop()
            else:
                self._last_send = time.perf_counter()
    def get_payload(self) -> Dict[str, Any]:
        return {
            'op': self.ws.HEARTBEAT,
            'd': self.ws.sequence,
        }
    def start(self) -> None:
        self.ws.loop.create_task(self.run())
    def stop(self) -> None:
        self._stop.set()
    def tick(self) -> None:
        self._last_recv = time.perf_counter()
    def ack(self) -> None:
        ack_time = time.perf_counter()
        self._last_ack = ack_time
        self.latency = ack_time - self._last_send
        if self.latency > 10:
            _log.warning(self.behind_msg, self.latency)
class VoiceKeepAliveHandler(KeepAliveHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recent_ack_latencies: deque[float] = deque(maxlen=20)
        self.msg: str = 'Keeping voice websocket alive.'
        self.block_msg: str = 'Voice heartbeat blocked for more than %s seconds'
        self.behind_msg: str = 'High socket latency, heartbeat is %.1fs behind'
        self.not_responding_msg: str = 'Voice gateway has stopped responding. Closing and restarting.'
        self.no_stop_msg: str = 'An error occurred while stopping the voice gateway. Ignoring.'
    def get_payload(self) -> Dict[str, Any]:
        return {
            'op': self.ws.HEARTBEAT,
            'd': int(time.time() * 1000),
        }
    def ack(self) -> None:
        ack_time = time.perf_counter()
        self._last_ack = ack_time
        self._last_recv = ack_time
        self.latency: float = ack_time - self._last_send
        self.recent_ack_latencies.append(self.latency)
        if self.latency > 10:
            _log.warning(self.behind_msg, self.latency)
DWS = TypeVar('DWS', bound='DiscordWebSocket')
class DiscordWebSocket:
    if TYPE_CHECKING:
        token: Optional[str]
        _connection: ConnectionState
        _discord_parsers: Dict[str, Callable[..., Any]]
        call_hooks: Callable[..., Any]
        _initial_identify: bool
        shard_id: Optional[int]
        shard_count: Optional[int]
        gateway: yarl.URL
        _max_heartbeat_timeout: float
        _user_agent: str
        _super_properties: Dict[str, Any]
        _zlib_enabled: bool
    DEFAULT_GATEWAY       = yarl.URL('wss://gateway.discord.gg/')
    DISPATCH              = 0
    HEARTBEAT             = 1
    IDENTIFY              = 2
    PRESENCE              = 3
    VOICE_STATE           = 4
    VOICE_PING            = 5
    RESUME                = 6
    RECONNECT             = 7
    REQUEST_MEMBERS       = 8
    INVALIDATE_SESSION    = 9
    HELLO                 = 10
    HEARTBEAT_ACK         = 11
    CALL_CONNECT          = 13
    GUILD_SUBSCRIBE       = 14
    SEARCH_RECENT_MEMBERS = 35
    BULK_GUILD_SUBSCRIBE  = 37
    def __init__(self, socket: aiohttp.ClientWebSocketResponse, *, loop: asyncio.AbstractEventLoop) -> None:
        self.socket: aiohttp.ClientWebSocketResponse = socket
        self.loop: asyncio.AbstractEventLoop = loop
        self._dispatch: Callable[..., Any] = lambda *args: None
        self._dispatch_listeners: List[EventListener] = []
        self._keep_alive: Optional[KeepAliveHandler] = None
        self.thread_id: int = threading.get_ident()
        self.session_id: Optional[str] = None
        self.sequence: Optional[int] = None
        self._zlib: zlib._Decompress = zlib.decompressobj()
        self._buffer: bytearray = bytearray()
        self._close_code: Optional[int] = None
        self._rate_limiter: GatewayRatelimiter = GatewayRatelimiter()
        self.afk: bool = False
        self.idle_since: int = 0
    @property
    def open(self) -> bool:
        return not self.socket.closed
    @property
    def capabilities(self) -> Capabilities:
        return Capabilities.default()
    def is_ratelimited(self) -> bool:
        return self._rate_limiter.is_ratelimited()
    def debug_log_receive(self, data: Dict[str, Any], /) -> None:
        self._dispatch('socket_raw_receive', data)
    def log_receive(self, _: Dict[str, Any], /) -> None:
        pass
    @classmethod
    async def from_client(
        cls,
        client: Client,
        *,
        initial: bool = False,
        session_spoof: str = "windows",
        startup_status: str = "offline",
        gateway: Optional[yarl.URL] = None,
        session: Optional[str] = None,
        sequence: Optional[int] = None,
        resume: bool = False,
        encoding: str = 'json',
        zlib: bool = True,
    ) -> Self:
        from .http import INTERNAL_API_VERSION
        gateway = gateway or cls.DEFAULT_GATEWAY
        if zlib:
            url = gateway.with_query(v=INTERNAL_API_VERSION, encoding=encoding, compress='zlib-stream')
        else:
            url = gateway.with_query(v=INTERNAL_API_VERSION, encoding=encoding)
        socket = await client.http.ws_connect(str(url))
        ws = cls(socket, loop=client.loop)
        ws.token = client.http.token
        ws._connection = client._connection
        ws._discord_parsers = client._connection.parsers
        ws._dispatch = client.dispatch
        ws.gateway = gateway
        ws.call_hooks = client._connection.call_hooks
        ws._initial_identify = initial
        ws.session_id = session
        ws.sequence = sequence
        ws._max_heartbeat_timeout = client._connection.heartbeat_timeout
        ws._user_agent = client.http.user_agent
        ws._super_properties = client.http.super_properties
        ws._zlib_enabled = zlib
        ws.afk = client._connection._afk
        ws.idle_since = client._connection._idle_since
        if client._enable_debug_events:
            ws.send = ws.debug_send
            ws.log_receive = ws.debug_log_receive
        client._connection._update_references(ws)
        _log.debug('Connected to %s.', gateway)
        await ws.poll_event()
        if not resume:
            await ws.identify(session_spoof=session_spoof, startup_status=startup_status)
            return ws
        await ws.resume()
        return ws
    def wait_for(
        self,
        event: str,
        predicate: Callable[[Dict[str, Any]], bool],
        result: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> asyncio.Future[Any]:
        event = event.upper()
        future = self.loop.create_future()
        entry = EventListener(event=event, predicate=predicate, result=result, future=future)
        self._dispatch_listeners.append(entry)
        return future
    async def identify(self, *, session_spoof: str, startup_status: str) -> None:
        presence = {
            'status': startup_status,
            'since': 0,
            'activities': [],
            'afk': False,
        }
        existing = self._connection.current_session
        if existing is not None:
            if existing.status == Status.idle:
                presence['since'] = int(time.time() * 1000)
            presence['activities'] = [a.to_dict() for a in existing.activities]
        properties = self._super_properties
        if "windows" in session_spoof:
            properties = {
                "os": "Windows",
                "browser": "Discord Client",
                "device": "Windows",
                "system_locale": "en-US",
                "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
            }
        elif "linux" in session_spoof:
            properties = {
                "os": "Linux",
                "browser": "Discord Client",
                "device": "Linux",
                "system_locale": "en-US",
                "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
            }
        elif "android" in session_spoof:
            properties = {
                "os": "Android",
                "browser": "Discord Android",
                "device": "Android",
                "system_locale": "en-US",
                "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
            }
        elif "ios" in session_spoof:
            properties = {
                "os": "iOS",
                "browser": "Discord iOS",
                "device": "iOS",
                "system_locale": "en-US",
                "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
            }
        elif "ps5" in session_spoof:
            properties = {
                "os": "PS5",
                "browser": "Discord Embedded",
                "device": "PS5",
                "system_locale": "en-US",
                "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
            }
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'capabilities': self.capabilities.value,
                'properties': properties,
                'presence': presence,
                'compress': not self._zlib_enabled,
                'client_state': {
                    'api_code_version': 0,
                    'guild_versions': {},
                    'highest_last_message_id': '0',
                    'private_channels_version': '0',
                    'read_state_version': 0,
                    'user_guild_settings_version': -1,
                    'user_settings_version': -1,
                },
            },
        }
        await self.call_hooks('before_identify', initial=self._initial_identify)
        await self.send_as_json(payload)
        _log.info('Gateway has sent the IDENTIFY payload.')
    async def resume(self) -> None:
        payload = {
            'op': self.RESUME,
            'd': {
                'seq': self.sequence,
                'session_id': self.session_id,
                'token': self.token,
            },
        }
        await self.send_as_json(payload)
        _log.debug('Gateway has sent the RESUME payload.')
    async def received_message(self, msg: Any, /) -> None:
        if type(msg) is bytes:
            self._buffer.extend(msg)
            if len(msg) < 4 or msg[-4:] != b'\x00\x00\xff\xff':
                return
            msg = self._zlib.decompress(self._buffer)
            msg = msg.decode('utf-8')
            self._buffer = bytearray()
        self.log_receive(msg)
        msg = utils._from_json(msg)
        _log.debug('Gateway event: %s.', msg)
        event = msg.get('t')
        if event:
            self._dispatch('socket_event_type', event)
        op = msg.get('op')
        data = msg.get('d')
        seq = msg.get('s')
        if seq is not None:
            self.sequence = seq
        if self._keep_alive:
            self._keep_alive.tick()
        if op != self.DISPATCH:
            if op == self.RECONNECT:
                _log.debug('Received RECONNECT opcode.')
                await self.close()
                raise ReconnectWebSocket
            if op == self.HEARTBEAT_ACK:
                if self._keep_alive:
                    self._keep_alive.ack()
                return
            if op == self.HEARTBEAT:
                if self._keep_alive:
                    beat = self._keep_alive.get_payload()
                    await self.send_as_json(beat)
                return
            if op == self.HELLO:
                interval = data['heartbeat_interval'] / 1000.0
                self._keep_alive = KeepAliveHandler(ws=self, interval=interval)
                await self.send_as_json(self._keep_alive.get_payload())
                self._keep_alive.start()
                return
            if op == self.INVALIDATE_SESSION:
                if data is True:
                    await self.close()
                    raise ReconnectWebSocket
                self.sequence = None
                self.session_id = None
                self.gateway = self.DEFAULT_GATEWAY
                _log.info('Gateway session has been invalidated.')
                await self.close(code=1000)
                raise ReconnectWebSocket(resume=False)
            _log.warning('Unknown OP code %s.', op)
            return
        if event == 'READY':
            self._trace = data.get('_trace', [])
            self.sequence = msg['s']
            self.session_id = data['session_id']
            self.gateway = yarl.URL(data['resume_gateway_url'])
            _log.info('Connected to Gateway (Session ID: %s).', self.session_id)
            await self.voice_state()
        elif event == 'RESUMED':
            _log.info('Gateway has successfully RESUMED session %s.', self.session_id)
        try:
            func = self._discord_parsers[event]
        except KeyError:
            _log.debug('Unknown event %s.', event)
        else:
            _log.debug('Parsing event %s.', event)
            func(data)
        removed = []
        for index, entry in enumerate(self._dispatch_listeners):
            if entry.event != event:
                continue
            future = entry.future
            if future.cancelled():
                removed.append(index)
                continue
            try:
                valid = entry.predicate(data)
            except Exception as exc:
                future.set_exception(exc)
                removed.append(index)
            else:
                if valid:
                    ret = data if entry.result is None else entry.result(data)
                    future.set_result(ret)
                    removed.append(index)
        for index in reversed(removed):
            del self._dispatch_listeners[index]
    @property
    def latency(self) -> float:
        heartbeat = self._keep_alive
        return float('inf') if heartbeat is None else heartbeat.latency
    def _can_handle_close(self) -> bool:
        code = self._close_code or self.socket.close_code
        return code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014)
    async def poll_event(self) -> None:
        try:
            msg = await self.socket.receive(timeout=self._max_heartbeat_timeout)
            if msg.type is aiohttp.WSMsgType.TEXT:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.BINARY:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.ERROR:
                _log.debug('Received %s.', msg)
                raise msg.data
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
                _log.debug('Received %s.', msg)
                raise WebSocketClosure
        except (asyncio.TimeoutError, WebSocketClosure) as e:
            if self._keep_alive:
                self._keep_alive.stop()
                self._keep_alive = None
            if isinstance(e, asyncio.TimeoutError):
                _log.debug('Timed out receiving packet. Attempting a reconnect.')
                raise ReconnectWebSocket from None
            code = self._close_code or self.socket.close_code
            if self._can_handle_close():
                _log.debug('Websocket closed with %s, attempting a reconnect.', code)
                raise ReconnectWebSocket from None
            else:
                _log.debug('Websocket closed with %s, cannot reconnect.', code)
                raise ConnectionClosed(self.socket, code=code) from None
    async def debug_send(self, data: str, /) -> None:
        await self._rate_limiter.block()
        self._dispatch('socket_raw_send', data)
        await self.socket.send_str(data)
    async def send(self, data: str, /) -> None:
        await self._rate_limiter.block()
        await self.socket.send_str(data)
    async def send_as_json(self, data: Any) -> None:
        try:
            await self.send(utils._to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket) from exc
    async def send_heartbeat(self, data: Any) -> None:
        try:
            await self.socket.send_str(utils._to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket) from exc
    async def change_presence(
        self,
        *,
        activities: Optional[Sequence[ActivityTypes]] = None,
        status: Optional[Status] = None,
        since: int = 0,
        afk: bool = False,
    ) -> None:
        if activities is not None:
            if not all(isinstance(activity, (BaseActivity, Spotify)) for activity in activities):
                raise TypeError('activity must derive from BaseActivity')
            activities_data = [activity.to_dict() for activity in activities]
        else:
            activities_data = []
        payload = {
            'op': self.PRESENCE,
            'd': {'activities': activities_data, 'afk': afk, 'since': since, 'status': str(status or 'unknown')},
        }
        _log.debug('Sending %s to change presence.', payload['d'])
        await self.send_as_json(payload)
        self.afk = afk
        self.idle_since = since
    async def change_custom_presence(self, *, payload=None):
        sent = utils._to_json(payload)
        _log.debug('Sending "%s" to change status', sent)
        await self.send(sent)
    async def guild_subscribe(
        self,
        guild_id: Snowflake,
        *,
        typing: Optional[bool] = None,
        threads: Optional[bool] = None,
        activities: Optional[bool] = None,
        members: Optional[List[Snowflake]] = None,
        channels: Optional[Dict[Snowflake, List[List[int]]]] = None,
        thread_member_lists: Optional[List[Snowflake]] = None,
    ):
        payload = {
            'op': self.GUILD_SUBSCRIBE,
            'd': {
                'guild_id': str(guild_id),
            },
        }
        data = payload['d']
        if typing is not None:
            data['typing'] = typing
        if threads is not None:
            data['threads'] = threads
        if activities is not None:
            data['activities'] = activities
        if members is not None:
            data['members'] = members
        if channels is not None:
            data['channels'] = channels
        if thread_member_lists is not None:
            data['thread_member_lists'] = thread_member_lists
        _log.debug('Subscribing to guild %s with payload %s', guild_id, payload['d'])
        await self.send_as_json(payload)
    async def bulk_guild_subscribe(self, subscriptions: BulkGuildSubscribePayload) -> None:
        payload = {
            'op': self.BULK_GUILD_SUBSCRIBE,
            'd': {
                'subscriptions': subscriptions,
            },
        }
        _log.debug('Subscribing to guilds with payload %s', payload['d'])
        await self.send_as_json(payload)
    async def request_chunks(
        self,
        guild_ids: List[Snowflake],
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        user_ids: Optional[List[Snowflake]] = None,
        presences: bool = True,
        nonce: Optional[str] = None,
    ) -> None:
        payload = {
            'op': self.REQUEST_MEMBERS,
            'd': {
                'guild_id': guild_ids,
                'query': query,
                'limit': limit,
                'presences': presences,
                'user_ids': user_ids,
            },
        }
        if nonce is not None:
            payload['d']['nonce'] = nonce
        await self.send_as_json(payload)
    async def voice_state(
        self,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
        *,
        preferred_region: Optional[str] = None,
    ) -> None:
        payload = {
            'op': self.VOICE_STATE,
            'd': {
                'guild_id': guild_id,
                'channel_id': channel_id,
                'self_mute': self_mute,
                'self_deaf': self_deaf,
                'self_video': self_video,
            },
        }
        if preferred_region is not None:
            payload['d']['preferred_region'] = preferred_region
        _log.debug('Updating %s voice state to %s.', guild_id or 'client', payload)
        await self.send_as_json(payload)
    async def call_connect(self, channel_id: Snowflake):
        payload = {'op': self.CALL_CONNECT, 'd': {'channel_id': str(channel_id)}}
        _log.debug('Requesting call connect for channel %s.', channel_id)
        await self.send_as_json(payload)
    async def search_recent_members(
        self, guild_id: Snowflake, query: str = '', *, after: Optional[Snowflake] = None, nonce: Optional[str] = None
    ) -> None:
        payload = {
            'op': self.SEARCH_RECENT_MEMBERS,
            'd': {
                'guild_id': str(guild_id),
                'query': query,
                'continuation_token': str(after) if after else None,
            },
        }
        if nonce is not None:
            payload['d']['nonce'] = nonce
        await self.send_as_json(payload)
    async def close(self, code: int = 4000) -> None:
        if self._keep_alive:
            self._keep_alive.stop()
            self._keep_alive = None
        self._close_code = code
        await self.socket.close(code=code)
DVWS = TypeVar('DVWS', bound='DiscordVoiceWebSocket')
class DiscordVoiceWebSocket:
    if TYPE_CHECKING:
        thread_id: int
        _connection: VoiceClient
        gateway: str
        _max_heartbeat_timeout: float
    IDENTIFY            = 0
    SELECT_PROTOCOL     = 1
    READY               = 2
    HEARTBEAT           = 3
    SESSION_DESCRIPTION = 4
    SPEAKING            = 5
    HEARTBEAT_ACK       = 6
    RESUME              = 7
    HELLO               = 8
    RESUMED             = 9
    CLIENT_CONNECT      = 12
    CLIENT_DISCONNECT   = 13
    def __init__(
        self,
        socket: aiohttp.ClientWebSocketResponse,
        loop: asyncio.AbstractEventLoop,
        *,
        hook: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None,
    ) -> None:
        self.ws: aiohttp.ClientWebSocketResponse = socket
        self.loop: asyncio.AbstractEventLoop = loop
        self._keep_alive: Optional[VoiceKeepAliveHandler] = None
        self._close_code: Optional[int] = None
        self.secret_key: Optional[str] = None
        if hook:
            self._hook = hook
    async def _hook(self, *args: Any) -> None:
        pass
    async def send_as_json(self, data: Any) -> None:
        _log.debug('Voice gateway sending: %s.', data)
        await self.ws.send_str(utils._to_json(data))
    send_heartbeat = send_as_json
    async def resume(self) -> None:
        state = self._connection
        payload = {
            'op': self.RESUME,
            'd': {
                'token': state.token,
                'server_id': str(state.server_id),
                'session_id': state.session_id,
            },
        }
        await self.send_as_json(payload)
    async def identify(self) -> None:
        state = self._connection
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'server_id': str(state.server_id),
                'user_id': str(state.user.id),
                'session_id': state.session_id,
                'token': state.token,
            },
        }
        await self.send_as_json(payload)
    @classmethod
    async def from_client(
        cls, client: VoiceClient, *, resume: bool = False, hook: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    ) -> Self:
        gateway = 'wss://' + client.endpoint + '/?v=4'
        http = client.state.http
        socket = await http.ws_connect(gateway, compress=15)
        ws = cls(socket, loop=client.loop, hook=hook)
        ws.gateway = gateway
        ws._connection = client
        ws._max_heartbeat_timeout = 60.0
        ws.thread_id = threading.get_ident()
        if resume:
            await ws.resume()
        else:
            await ws.identify()
        return ws
    async def select_protocol(self, ip: str, port: int, mode: int) -> None:
        payload = {
            'op': self.SELECT_PROTOCOL,
            'd': {
                'protocol': 'udp',
                'data': {
                    'address': ip,
                    'port': port,
                    'mode': mode,
                },
            },
        }
        await self.send_as_json(payload)
    async def client_connect(self) -> None:
        payload = {
            'op': self.CLIENT_CONNECT,
            'd': {
                'audio_ssrc': self._connection.ssrc,
            },
        }
        await self.send_as_json(payload)
    async def speak(self, state: SpeakingState = SpeakingState.voice) -> None:
        payload = {
            'op': self.SPEAKING,
            'd': {
                'speaking': int(state),
                'delay': 0,
                'ssrc': self._connection.ssrc,
            },
        }
        await self.send_as_json(payload)
    async def received_message(self, msg: Dict[str, Any]) -> None:
        _log.debug('Voice gateway event: %s.', msg)
        op = msg['op']
        data = msg['d']
        if op == self.READY:
            await self.initial_connection(data)
        elif op == self.HEARTBEAT_ACK:
            if self._keep_alive:
                self._keep_alive.ack()
        elif op == self.RESUMED:
            _log.debug('Voice RESUME succeeded.')
        elif op == self.SESSION_DESCRIPTION:
            self._connection.mode = data['mode']
            await self.load_secret_key(data)
        elif op == self.HELLO:
            interval = data['heartbeat_interval'] / 1000.0
            self._keep_alive = VoiceKeepAliveHandler(ws=self, interval=min(interval, 5.0))
            self._keep_alive.start()
        await self._hook(self, msg)
    async def initial_connection(self, data: Dict[str, Any]) -> None:
        state = self._connection
        state.ssrc = data['ssrc']
        state.voice_port = data['port']
        state.endpoint_ip = data['ip']
        packet = bytearray(74)
        struct.pack_into('>H', packet, 0, 1)
        struct.pack_into('>H', packet, 2, 70)
        struct.pack_into('>I', packet, 4, state.ssrc)
        state.socket.sendto(packet, (state.endpoint_ip, state.voice_port))
        recv = await self.loop.sock_recv(state.socket, 74)
        _log.debug('Received packet in initial_connection: %s.', recv)
        ip_start = 8
        ip_end = recv.index(0, ip_start)
        state.ip = recv[ip_start:ip_end].decode('ascii')
        state.port = struct.unpack_from('>H', recv, len(recv) - 2)[0]
        _log.debug('Detected ip: %s, port: %s.', state.ip, state.port)
        modes = [mode for mode in data['modes'] if mode in self._connection.supported_modes]
        _log.debug('Received supported encryption modes: %s.', ", ".join(modes))
        mode = modes[0]
        await self.select_protocol(state.ip, state.port, mode)
        _log.debug('Selected the voice protocol for use: %s.', mode)
    @property
    def latency(self) -> float:
        heartbeat = self._keep_alive
        return float('inf') if heartbeat is None else heartbeat.latency
    @property
    def average_latency(self) -> float:
        heartbeat = self._keep_alive
        if heartbeat is None or not heartbeat.recent_ack_latencies:
            return float('inf')
        return sum(heartbeat.recent_ack_latencies) / len(heartbeat.recent_ack_latencies)
    async def load_secret_key(self, data: Dict[str, Any]) -> None:
        _log.debug('Received secret key for voice connection.')
        self.secret_key = self._connection.secret_key = data['secret_key']
        await self.speak(SpeakingState.none)
    async def poll_event(self) -> None:
        msg = await asyncio.wait_for(self.ws.receive(), timeout=30.0)
        if msg.type is aiohttp.WSMsgType.TEXT:
            await self.received_message(utils._from_json(msg.data))
        elif msg.type is aiohttp.WSMsgType.ERROR:
            _log.debug('Voice received %s.', msg)
            raise ConnectionClosed(self.ws) from msg.data
        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
            _log.debug('Voice received %s.', msg)
            raise ConnectionClosed(self.ws, code=self._close_code)
    async def close(self, code: int = 1000) -> None:
        if self._keep_alive is not None:
            self._keep_alive.stop()
        self._close_code = code
        await self.ws.close(code=code)