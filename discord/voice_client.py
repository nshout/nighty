from __future__ import annotations
import asyncio
import socket
import logging
import struct
import threading
from typing import Any, Callable, List, Optional, TYPE_CHECKING, Tuple
from . import opus, utils
from .backoff import ExponentialBackoff
from .gateway import *
from .errors import ClientException, ConnectionClosed
from .player import AudioPlayer, AudioSource
from .utils import _get_as_snowflake, MISSING
if TYPE_CHECKING:
    from .client import Client
    from .guild import Guild
    from .state import ConnectionState
    from .user import ClientUser
    from .opus import Encoder
    from . import abc
    from .types.gateway import VoiceStateUpdateEvent as VoiceStateUpdatePayload
    from .types.voice import (
        VoiceServerUpdate as VoiceServerUpdatePayload,
        SupportedModes,
    )
    VocalChannel = abc.VocalChannel
has_nacl: bool
try:
    import nacl.secret
    import nacl.utils
    has_nacl = True
except ImportError:
    has_nacl = False
__all__ = (
    'VoiceProtocol',
    'VoiceClient',
)
_log = logging.getLogger(__name__)
class VoiceProtocol:
    def __init__(self, client: Client, channel: VocalChannel) -> None:
        self.client: Client = client
        self.channel: VocalChannel = channel
    async def on_voice_state_update(self, data: VoiceStateUpdatePayload, /) -> None:
        raise NotImplementedError
    async def on_voice_server_update(self, data: VoiceServerUpdatePayload, /) -> None:
        raise NotImplementedError
    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        raise NotImplementedError
    async def disconnect(self, *, force: bool) -> None:
        raise NotImplementedError
    def cleanup(self) -> None:
        key_id, _ = self.channel._get_voice_client_key()
        self.client._connection._remove_voice_client(key_id)
class VoiceClient(VoiceProtocol):
    channel: VocalChannel
    endpoint_ip: str
    voice_port: int
    ip: str
    port: int
    secret_key: List[int]
    ssrc: int
    def __init__(self, client: Client, channel: VocalChannel) -> None:
        if not has_nacl:
            raise RuntimeError("PyNaCl library needed in order to use voice")
        super().__init__(client, channel)
        state = client._connection
        self.token: str = MISSING
        self.server_id: int = MISSING
        self.socket = MISSING
        self.loop: asyncio.AbstractEventLoop = state.loop
        self.state: ConnectionState = state
        self._connected: threading.Event = threading.Event()
        self._handshaking: bool = False
        self._potentially_reconnecting: bool = False
        self._voice_state_complete: asyncio.Event = asyncio.Event()
        self._voice_server_complete: asyncio.Event = asyncio.Event()
        self.mode: str = MISSING
        self._connections: int = 0
        self.sequence: int = 0
        self.timestamp: int = 0
        self.timeout: float = 0
        self._runner: asyncio.Task = MISSING
        self._player: Optional[AudioPlayer] = None
        self.encoder: Encoder = MISSING
        self._lite_nonce: int = 0
        self.ws: DiscordVoiceWebSocket = MISSING
    warn_nacl: bool = not has_nacl
    supported_modes: Tuple[SupportedModes, ...] = (
        'xsalsa20_poly1305_lite',
        'xsalsa20_poly1305_suffix',
        'xsalsa20_poly1305',
    )
    @property
    def guild(self) -> Optional[Guild]:
        return getattr(self.channel, 'guild', None)
    @property
    def user(self) -> ClientUser:
        return self.state.user
    def checked_add(self, attr: str, value: int, limit: int) -> None:
        val = getattr(self, attr)
        if val + value > limit:
            setattr(self, attr, 0)
        else:
            setattr(self, attr, val + value)
    async def on_voice_state_update(self, data: VoiceStateUpdatePayload) -> None:
        self.session_id: str = data['session_id']
        channel_id = data['channel_id']
        if not self._handshaking or self._potentially_reconnecting:
            if channel_id is None:
                await self.disconnect()
            else:
                self.channel = channel_id and self.guild.get_channel(int(channel_id))
        else:
            self._voice_state_complete.set()
    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        if self._voice_server_complete.is_set():
            _log.warning('Ignoring extraneous voice server update.')
            return
        self.token = data['token']
        self.server_id = _get_as_snowflake(data, 'guild_id') or int(data['channel_id'])
        endpoint = data.get('endpoint')
        if endpoint is None or self.token is None:
            _log.warning(
                'Awaiting endpoint... This requires waiting. '
                'If timeout occurred considering raising the timeout and reconnecting.'
            )
            return
        self.endpoint, _, _ = endpoint.rpartition(':')
        if self.endpoint.startswith('wss://'):
            self.endpoint: str = self.endpoint[6:]
        self.endpoint_ip = MISSING
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        if not self._handshaking:
            await self.ws.close(4000)
            return
        self._voice_server_complete.set()
    async def voice_connect(self, self_deaf: bool = False, self_mute: bool = False) -> None:
        channel = self.channel
        if self.guild:
            await self.guild.change_voice_state(channel=channel, self_deaf=self_deaf, self_mute=self_mute)
        else:
            await self.state.client.change_voice_state(channel=channel, self_deaf=self_deaf, self_mute=self_mute)
    async def voice_disconnect(self) -> None:
        guild = self.guild
        _log.info(
            'The voice handshake is being terminated for channel ID %s (guild ID %s).',
            self.channel.id,
            getattr(guild, 'id', None),
        )
        if guild:
            await guild.change_voice_state(channel=None)
        else:
            await self.state.client.change_voice_state(channel=None)
    def prepare_handshake(self) -> None:
        self._voice_state_complete.clear()
        self._voice_server_complete.clear()
        self._handshaking = True
        _log.info('Starting voice handshake (connection attempt %d)...', self._connections + 1)
        self._connections += 1
    def finish_handshake(self) -> None:
        _log.info('Voice handshake complete. Endpoint found: %s.', self.endpoint)
        self._handshaking = False
        self._voice_server_complete.clear()
        self._voice_state_complete.clear()
    async def connect_websocket(self) -> DiscordVoiceWebSocket:
        ws = await DiscordVoiceWebSocket.from_client(self)
        self._connected.clear()
        while ws.secret_key is None:
            await ws.poll_event()
        self._connected.set()
        return ws
    async def connect(self, *, reconnect: bool, timeout: float, self_deaf: bool = False, self_mute: bool = False) -> None:
        _log.info('Connecting to voice...')
        self.timeout = timeout
        for i in range(5):
            self.prepare_handshake()
            futures = [
                self._voice_state_complete.wait(),
                self._voice_server_complete.wait(),
            ]
            await self.voice_connect(self_deaf=self_deaf, self_mute=self_mute)
            try:
                await utils.sane_wait_for(futures, timeout=timeout)
            except asyncio.TimeoutError:
                await self.disconnect(force=True)
                raise
            self.finish_handshake()
            try:
                self.ws = await self.connect_websocket()
                break
            except (ConnectionClosed, asyncio.TimeoutError):
                if reconnect:
                    _log.exception('Failed to connect to voice... Retrying...')
                    await asyncio.sleep(1 + i * 2.0)
                    await self.voice_disconnect()
                    continue
                else:
                    raise
        if self._runner is MISSING:
            self._runner = self.client.loop.create_task(self.poll_voice_ws(reconnect))
    async def potential_reconnect(self) -> bool:
        self._connected.clear()
        self.prepare_handshake()
        self._potentially_reconnecting = True
        try:
            await asyncio.wait_for(self._voice_server_complete.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            self._potentially_reconnecting = False
            await self.disconnect(force=True)
            return False
        self.finish_handshake()
        self._potentially_reconnecting = False
        try:
            self.ws = await self.connect_websocket()
        except (ConnectionClosed, asyncio.TimeoutError):
            return False
        else:
            return True
    @property
    def latency(self) -> float:
        ws = self.ws
        return float("inf") if not ws else ws.latency
    @property
    def average_latency(self) -> float:
        ws = self.ws
        return float("inf") if not ws else ws.average_latency
    async def poll_voice_ws(self, reconnect: bool) -> None:
        backoff = ExponentialBackoff()
        while True:
            try:
                await self.ws.poll_event()
            except (ConnectionClosed, asyncio.TimeoutError) as exc:
                if isinstance(exc, ConnectionClosed):
                    if exc.code in (1000, 4015):
                        _log.info('Disconnecting from voice normally, close code %d.', exc.code)
                        await self.disconnect()
                        break
                    if exc.code == 4014:
                        _log.info('Disconnected from voice by force... potentially reconnecting.')
                        successful = await self.potential_reconnect()
                        if not successful:
                            _log.info('Reconnect was unsuccessful, disconnecting from voice normally...')
                            await self.disconnect()
                            break
                        else:
                            continue
                if not reconnect:
                    await self.disconnect()
                    raise
                retry = backoff.delay()
                _log.exception('Disconnected from voice... Reconnecting in %.2fs.', retry)
                self._connected.clear()
                await asyncio.sleep(retry)
                await self.voice_disconnect()
                try:
                    await self.connect(reconnect=True, timeout=self.timeout)
                except asyncio.TimeoutError:
                    _log.warning('Could not connect to voice... Retrying...')
                    continue
    async def disconnect(self, *, force: bool = False) -> None:
        if not force and not self.is_connected():
            return
        self.stop()
        self._connected.clear()
        try:
            if self.ws:
                await self.ws.close()
            await self.voice_disconnect()
        finally:
            self.cleanup()
            if self.socket:
                self.socket.close()
    async def move_to(self, channel: Optional[abc.Snowflake]) -> None:
        if self.guild:
            await self.guild.change_voice_state(channel=channel)
        else:
            await self.state.client.change_voice_state(channel=channel)
    def is_connected(self) -> bool:
        return self._connected.is_set()
    def _get_voice_packet(self, data):
        header = bytearray(12)
        header[0] = 0x80
        header[1] = 0x78
        struct.pack_into('>H', header, 2, self.sequence)
        struct.pack_into('>I', header, 4, self.timestamp)
        struct.pack_into('>I', header, 8, self.ssrc)
        encrypt_packet = getattr(self, '_encrypt_' + self.mode)
        return encrypt_packet(header, data)
    def _encrypt_xsalsa20_poly1305(self, header: bytes, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))
        nonce = bytearray(24)
        nonce[:12] = header
        return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext
    def _encrypt_xsalsa20_poly1305_suffix(self, header: bytes, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))
        nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        return header + box.encrypt(bytes(data), nonce).ciphertext + nonce
    def _encrypt_xsalsa20_poly1305_lite(self, header: bytes, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))
        nonce = bytearray(24)
        nonce[:4] = struct.pack('>I', self._lite_nonce)
        self.checked_add('_lite_nonce', 1, 4294967295)
        return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext + nonce[:4]
    def play(self, source: AudioSource, *, after: Optional[Callable[[Optional[Exception]], Any]] = None) -> None:
        if not self.is_connected():
            raise ClientException('Not connected to voice.')
        if self.is_playing():
            raise ClientException('Already playing audio.')
        if not isinstance(source, AudioSource):
            raise TypeError(f'source must be an AudioSource not {source.__class__.__name__}')
        if not self.encoder and not source.is_opus():
            self.encoder = opus.Encoder()
        self._player = AudioPlayer(source, self, after=after)
        self._player.start()
    def is_playing(self) -> bool:
        return self._player is not None and self._player.is_playing()
    def is_paused(self) -> bool:
        return self._player is not None and self._player.is_paused()
    def stop(self) -> None:
        if self._player:
            self._player.stop()
            self._player = None
    def pause(self) -> None:
        if self._player:
            self._player.pause()
    def resume(self) -> None:
        if self._player:
            self._player.resume()
    @property
    def source(self) -> Optional[AudioSource]:
        return self._player.source if self._player else None
    @source.setter
    def source(self, value: AudioSource) -> None:
        if not isinstance(value, AudioSource):
            raise TypeError(f'expected AudioSource not {value.__class__.__name__}.')
        if self._player is None:
            raise ValueError('Not playing anything.')
        self._player._set_source(value)
    def send_audio_packet(self, data: bytes, *, encode: bool = True) -> None:
        self.checked_add('sequence', 1, 65535)
        if encode:
            encoded_data = self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME)
        else:
            encoded_data = data
        packet = self._get_voice_packet(encoded_data)
        try:
            self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
        except BlockingIOError:
            _log.warning('A packet has been dropped (seq: %s, timestamp: %s)', self.sequence, self.timestamp)
        self.checked_add('timestamp', opus.Encoder.SAMPLES_PER_FRAME, 4294967295)