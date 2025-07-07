from __future__ import annotations
import threading
import subprocess
import audioop
import asyncio
import logging
import shlex
import time
import json
import sys
import re
import io
from typing import Any, Callable, Generic, IO, Optional, TYPE_CHECKING, Tuple, TypeVar, Union
from .enums import SpeakingState
from .errors import ClientException
from .opus import Encoder as OpusEncoder
from .oggparse import OggStream
from .utils import MISSING
if TYPE_CHECKING:
    from typing_extensions import Self
    from .voice_client import VoiceClient
AT = TypeVar('AT', bound='AudioSource')
_log = logging.getLogger(__name__)
__all__ = (
    'AudioSource',
    'PCMAudio',
    'FFmpegAudio',
    'FFmpegPCMAudio',
    'FFmpegOpusAudio',
    'PCMVolumeTransformer',
)
CREATE_NO_WINDOW: int
if sys.platform != 'win32':
    CREATE_NO_WINDOW = 0
else:
    CREATE_NO_WINDOW = 0x08000000
class AudioSource:
    def read(self) -> bytes:
        raise NotImplementedError
    def is_opus(self) -> bool:
        return False
    def cleanup(self) -> None:
        pass
    def __del__(self) -> None:
        self.cleanup()
class PCMAudio(AudioSource):
    def __init__(self, stream: io.BufferedIOBase) -> None:
        self.stream: io.BufferedIOBase = stream
    def read(self) -> bytes:
        ret = self.stream.read(OpusEncoder.FRAME_SIZE)
        if len(ret) != OpusEncoder.FRAME_SIZE:
            return b''
        return ret
class FFmpegAudio(AudioSource):
    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        executable: str = 'ffmpeg',
        args: Any,
        **subprocess_kwargs: Any,
    ):
        piping = subprocess_kwargs.get('stdin') == subprocess.PIPE
        if piping and isinstance(source, str):
            raise TypeError("parameter conflict: 'source' parameter cannot be a string when piping to stdin")
        args = [executable, *args]
        kwargs = {'stdout': subprocess.PIPE}
        kwargs.update(subprocess_kwargs)
        self._process: subprocess.Popen = MISSING
        self._process = self._spawn_process(args, **kwargs)
        self._stdout: IO[bytes] = self._process.stdout
        self._stdin: Optional[IO[bytes]] = None
        self._pipe_thread: Optional[threading.Thread] = None
        if piping:
            n = f'popen-stdin-writer:{id(self):
            self._stdin = self._process.stdin
            self._pipe_thread = threading.Thread(target=self._pipe_writer, args=(source,), daemon=True, name=n)
            self._pipe_thread.start()
    def _spawn_process(self, args: Any, **subprocess_kwargs: Any) -> subprocess.Popen:
        process = None
        try:
            process = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW, **subprocess_kwargs)
        except FileNotFoundError:
            executable = args.partition(' ')[0] if isinstance(args, str) else args[0]
            raise ClientException(executable + ' was not found.') from None
        except subprocess.SubprocessError as exc:
            raise ClientException(f'Popen failed: {exc.__class__.__name__}: {exc}') from exc
        else:
            return process
    def _kill_process(self) -> None:
        proc = self._process
        if proc is MISSING:
            return
        _log.debug('Preparing to terminate ffmpeg process %s.', proc.pid)
        try:
            proc.kill()
        except Exception:
            _log.exception('Ignoring error attempting to kill ffmpeg process %s.', proc.pid)
        if proc.poll() is None:
            _log.info('ffmpeg process %s has not terminated. Waiting to terminate...', proc.pid)
            proc.communicate()
            _log.info('ffmpeg process %s should have terminated with a return code of %s.', proc.pid, proc.returncode)
        else:
            _log.info('ffmpeg process %s successfully terminated with return code of %s.', proc.pid, proc.returncode)
    def _pipe_writer(self, source: io.BufferedIOBase) -> None:
        while self._process:
            data = source.read(8192)
            if not data:
                if self._stdin is not None:
                    self._stdin.close()
                return
            try:
                if self._stdin is not None:
                    self._stdin.write(data)
            except Exception:
                _log.debug('Write error for %s, this is probably not a problem.', self, exc_info=True)
                self._process.terminate()
                return
    def cleanup(self) -> None:
        self._kill_process()
        self._process = self._stdout = self._stdin = MISSING
class FFmpegPCMAudio(FFmpegAudio):
    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        executable: str = 'ffmpeg',
        pipe: bool = False,
        stderr: Optional[IO[str]] = None,
        before_options: Optional[str] = None,
        options: Optional[str] = None,
    ) -> None:
        args = []
        subprocess_kwargs = {'stdin': subprocess.PIPE if pipe else subprocess.DEVNULL, 'stderr': stderr}
        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))
        args.append('-i')
        args.append('-' if pipe else source)
        args.extend(('-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning'))
        if isinstance(options, str):
            args.extend(shlex.split(options))
        args.append('pipe:1')
        super().__init__(source, executable=executable, args=args, **subprocess_kwargs)
    def read(self) -> bytes:
        ret = self._stdout.read(OpusEncoder.FRAME_SIZE)
        if len(ret) != OpusEncoder.FRAME_SIZE:
            return b''
        return ret
    def is_opus(self) -> bool:
        return False
class FFmpegOpusAudio(FFmpegAudio):
    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        bitrate: Optional[int] = None,
        codec: Optional[str] = None,
        executable: str = 'ffmpeg',
        pipe: bool = False,
        stderr: Optional[IO[bytes]] = None,
        before_options: Optional[str] = None,
        options: Optional[str] = None,
    ) -> None:
        args = []
        subprocess_kwargs = {'stdin': subprocess.PIPE if pipe else subprocess.DEVNULL, 'stderr': stderr}
        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))
        args.append('-i')
        args.append('-' if pipe else source)
        codec = 'copy' if codec in ('opus', 'libopus') else 'libopus'
        bitrate = bitrate if bitrate is not None else 128
        args.extend(('-map_metadata', '-1',
                     '-f', 'opus',
                     '-c:a', codec,
                     '-ar', '48000',
                     '-ac', '2',
                     '-b:a', f'{bitrate}k',
                     '-loglevel', 'warning'))
        if isinstance(options, str):
            args.extend(shlex.split(options))
        args.append('pipe:1')
        super().__init__(source, executable=executable, args=args, **subprocess_kwargs)
        self._packet_iter = OggStream(self._stdout).iter_packets()
    @classmethod
    async def from_probe(
        cls,
        source: str,
        *,
        method: Optional[Union[str, Callable[[str, str], Tuple[Optional[str], Optional[int]]]]] = None,
        **kwargs: Any,
    ) -> Self:
        executable = kwargs.get('executable')
        codec, bitrate = await cls.probe(source, method=method, executable=executable)
        return cls(source, bitrate=bitrate, codec=codec, **kwargs)
    @classmethod
    async def probe(
        cls,
        source: str,
        *,
        method: Optional[Union[str, Callable[[str, str], Tuple[Optional[str], Optional[int]]]]] = None,
        executable: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[int]]:
        method = method or 'native'
        executable = executable or 'ffmpeg'
        probefunc = fallback = None
        if isinstance(method, str):
            probefunc = getattr(cls, '_probe_codec_' + method, None)
            if probefunc is None:
                raise AttributeError(f'Invalid probe method {method!r}.')
            if probefunc is cls._probe_codec_native:
                fallback = cls._probe_codec_fallback
        elif callable(method):
            probefunc = method
            fallback = cls._probe_codec_fallback
        else:
            raise TypeError(f"Expected str or callable for parameter 'probe', not '{method.__class__.__name__}'")
        codec = bitrate = None
        loop = asyncio.get_running_loop()
        try:
            codec, bitrate = await loop.run_in_executor(None, lambda: probefunc(source, executable))
        except Exception:
            if not fallback:
                _log.exception("Probe '%s' using '%s' failed.", method, executable)
                return
            _log.exception("Probe '%s' using '%s' failed, trying fallback.", method, executable)
            try:
                codec, bitrate = await loop.run_in_executor(None, lambda: fallback(source, executable))
            except Exception:
                _log.exception("Fallback probe using '%s' failed.", executable)
            else:
                _log.debug('Fallback probe found codec=%s, bitrate=%s.', codec, bitrate)
        else:
            _log.debug('Probe found codec=%s, bitrate=%s.', codec, bitrate)
        finally:
            return codec, bitrate
    @staticmethod
    def _probe_codec_native(source, executable: str = 'ffmpeg') -> Tuple[Optional[str], Optional[int]]:
        exe = executable[:2] + 'probe' if executable in ('ffmpeg', 'avconv') else executable
        args = [exe, '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a:0', source]
        output = subprocess.check_output(args, timeout=20)
        codec = bitrate = None
        if output:
            data = json.loads(output)
            streamdata = data['streams'][0]
            codec = streamdata.get('codec_name')
            bitrate = int(streamdata.get('bit_rate', 0))
            bitrate = max(round(bitrate / 1000), 512)
        return codec, bitrate
    @staticmethod
    def _probe_codec_fallback(source, executable: str = 'ffmpeg') -> Tuple[Optional[str], Optional[int]]:
        args = [executable, '-hide_banner', '-i', source]
        proc = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate(timeout=20)
        output = out.decode('utf8')
        codec = bitrate = None
        codec_match = re.search(r"Stream
        if codec_match:
            codec = codec_match.group(1)
        br_match = re.search(r"(\d+) [kK]b/s", output)
        if br_match:
            bitrate = max(int(br_match.group(1)), 512)
        return codec, bitrate
    def read(self) -> bytes:
        return next(self._packet_iter, b'')
    def is_opus(self) -> bool:
        return True
class PCMVolumeTransformer(AudioSource, Generic[AT]):
    def __init__(self, original: AT, volume: float = 1.0):
        if not isinstance(original, AudioSource):
            raise TypeError(f'expected AudioSource not {original.__class__.__name__}.')
        if original.is_opus():
            raise ClientException('AudioSource must not be Opus encoded.')
        self.original: AT = original
        self.volume = volume
    @property
    def volume(self) -> float:
        return self._volume
    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(value, 0.0)
    def cleanup(self) -> None:
        self.original.cleanup()
    def read(self) -> bytes:
        ret = self.original.read()
        return audioop.mul(ret, 2, min(self._volume, 2.0))
class AudioPlayer(threading.Thread):
    DELAY: float = OpusEncoder.FRAME_LENGTH / 1000.0
    def __init__(
        self,
        source: AudioSource,
        client: VoiceClient,
        *,
        after: Optional[Callable[[Optional[Exception]], Any]] = None,
    ) -> None:
        threading.Thread.__init__(self)
        self.daemon: bool = True
        self.source: AudioSource = source
        self.client: VoiceClient = client
        self.after: Optional[Callable[[Optional[Exception]], Any]] = after
        self._end: threading.Event = threading.Event()
        self._resumed: threading.Event = threading.Event()
        self._resumed.set()
        self._current_error: Optional[Exception] = None
        self._connected: threading.Event = client._connected
        self._lock: threading.Lock = threading.Lock()
        if after is not None and not callable(after):
            raise TypeError('Expected a callable for the "after" parameter.')
    def _do_run(self) -> None:
        self.loops = 0
        self._start = time.perf_counter()
        play_audio = self.client.send_audio_packet
        self._speak(SpeakingState.voice)
        while not self._end.is_set():
            if not self._resumed.is_set():
                self._resumed.wait()
                continue
            if not self._connected.is_set():
                self._connected.wait()
                self.loops = 0
                self._start = time.perf_counter()
            self.loops += 1
            data = self.source.read()
            if not data:
                self.stop()
                break
            play_audio(data, encode=not self.source.is_opus())
            next_time = self._start + self.DELAY * self.loops
            delay = max(0, self.DELAY + (next_time - time.perf_counter()))
            time.sleep(delay)
    def run(self) -> None:
        try:
            self._do_run()
        except Exception as exc:
            self._current_error = exc
            self.stop()
        finally:
            self._call_after()
            self.source.cleanup()
    def _call_after(self) -> None:
        error = self._current_error
        if self.after is not None:
            try:
                self.after(error)
            except Exception as exc:
                exc.__context__ = error
                _log.exception('Calling the after function failed.', exc_info=exc)
        elif error:
            _log.exception('Exception in voice thread %s.', self.name, exc_info=error)
    def stop(self) -> None:
        self._end.set()
        self._resumed.set()
        self._speak(SpeakingState.none)
    def pause(self, *, update_speaking: bool = True) -> None:
        self._resumed.clear()
        if update_speaking:
            self._speak(SpeakingState.none)
    def resume(self, *, update_speaking: bool = True) -> None:
        self.loops: int = 0
        self._start: float = time.perf_counter()
        self._resumed.set()
        if update_speaking:
            self._speak(SpeakingState.voice)
    def is_playing(self) -> bool:
        return self._resumed.is_set() and not self._end.is_set()
    def is_paused(self) -> bool:
        return not self._end.is_set() and not self._resumed.is_set()
    def _set_source(self, source: AudioSource) -> None:
        with self._lock:
            self.pause(update_speaking=False)
            self.source = source
            self.resume(update_speaking=False)
    def _speak(self, speaking: SpeakingState) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self.client.ws.speak(speaking), self.client.client.loop)
        except Exception:
            _log.exception('Speaking call in player failed.')