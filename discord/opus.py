from __future__ import annotations
from typing import List, Tuple, TypedDict, Any, TYPE_CHECKING, Callable, TypeVar, Literal, Optional, overload
import array
import ctypes
import ctypes.util
import logging
import math
import os.path
import struct
import sys
from .errors import DiscordException
if TYPE_CHECKING:
    T = TypeVar('T')
    BAND_CTL = Literal['narrow', 'medium', 'wide', 'superwide', 'full']
    SIGNAL_CTL = Literal['auto', 'voice', 'music']
class BandCtl(TypedDict):
    narrow: int
    medium: int
    wide: int
    superwide: int
    full: int
class SignalCtl(TypedDict):
    auto: int
    voice: int
    music: int
__all__ = (
    'Encoder',
    'OpusError',
    'OpusNotLoaded',
)
_log = logging.getLogger(__name__)
c_int_ptr = ctypes.POINTER(ctypes.c_int)
c_int16_ptr = ctypes.POINTER(ctypes.c_int16)
c_float_ptr = ctypes.POINTER(ctypes.c_float)
_lib: Any = None
class EncoderStruct(ctypes.Structure):
    pass
class DecoderStruct(ctypes.Structure):
    pass
EncoderStructPtr = ctypes.POINTER(EncoderStruct)
DecoderStructPtr = ctypes.POINTER(DecoderStruct)
OK      = 0
BAD_ARG = -1
APPLICATION_AUDIO    = 2049
APPLICATION_VOIP     = 2048
APPLICATION_LOWDELAY = 2051
CTL_SET_BITRATE      = 4002
CTL_SET_BANDWIDTH    = 4008
CTL_SET_FEC          = 4012
CTL_SET_PLP          = 4014
CTL_SET_SIGNAL       = 4024
CTL_SET_GAIN             = 4034
CTL_LAST_PACKET_DURATION = 4039
band_ctl: BandCtl = {
    'narrow': 1101,
    'medium': 1102,
    'wide': 1103,
    'superwide': 1104,
    'full': 1105,
}
signal_ctl: SignalCtl = {
    'auto': -1000,
    'voice': 3001,
    'music': 3002,
}
def _err_lt(result: int, func: Callable, args: List) -> int:
    if result < OK:
        _log.debug('Error has happened in %s.', func.__name__)
        raise OpusError(result)
    return result
def _err_ne(result: T, func: Callable, args: List) -> T:
    ret = args[-1]._obj
    if ret.value != OK:
        _log.debug('Error has happened in %s.', func.__name__)
        raise OpusError(ret.value)
    return result
exported_functions: List[Tuple[Any, ...]] = [
    ('opus_get_version_string', [], ctypes.c_char_p, None),
    ('opus_strerror', [ctypes.c_int], ctypes.c_char_p, None),
    ('opus_encoder_get_size', [ctypes.c_int], ctypes.c_int, None),
    ('opus_encoder_create', [ctypes.c_int, ctypes.c_int, ctypes.c_int, c_int_ptr], EncoderStructPtr, _err_ne),
    ('opus_encode', [EncoderStructPtr, c_int16_ptr, ctypes.c_int, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int32, _err_lt),
    (
        'opus_encode_float',
        [EncoderStructPtr, c_float_ptr, ctypes.c_int, ctypes.c_char_p, ctypes.c_int32],
        ctypes.c_int32,
        _err_lt,
    ),
    ('opus_encoder_ctl', [EncoderStructPtr, ctypes.c_int], ctypes.c_int32, _err_lt),
    ('opus_encoder_destroy', [EncoderStructPtr], None, None),
    ('opus_decoder_get_size', [ctypes.c_int], ctypes.c_int, None),
    ('opus_decoder_create', [ctypes.c_int, ctypes.c_int, c_int_ptr], DecoderStructPtr, _err_ne),
    (
        'opus_decode',
        [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32, c_int16_ptr, ctypes.c_int, ctypes.c_int],
        ctypes.c_int,
        _err_lt,
    ),
    (
        'opus_decode_float',
        [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32, c_float_ptr, ctypes.c_int, ctypes.c_int],
        ctypes.c_int,
        _err_lt,
    ),
    ('opus_decoder_ctl', [DecoderStructPtr, ctypes.c_int], ctypes.c_int32, _err_lt),
    ('opus_decoder_destroy', [DecoderStructPtr], None, None),
    ('opus_decoder_get_nb_samples', [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int, _err_lt),
    ('opus_packet_get_bandwidth', [ctypes.c_char_p], ctypes.c_int, _err_lt),
    ('opus_packet_get_nb_channels', [ctypes.c_char_p], ctypes.c_int, _err_lt),
    ('opus_packet_get_nb_frames', [ctypes.c_char_p, ctypes.c_int], ctypes.c_int, _err_lt),
    ('opus_packet_get_samples_per_frame', [ctypes.c_char_p, ctypes.c_int], ctypes.c_int, _err_lt),
]
def libopus_loader(name: str) -> Any:
    lib = ctypes.cdll.LoadLibrary(name)
    for item in exported_functions:
        func = getattr(lib, item[0])
        try:
            if item[1]:
                func.argtypes = item[1]
            func.restype = item[2]
        except KeyError:
            pass
        try:
            if item[3]:
                func.errcheck = item[3]
        except KeyError:
            _log.exception("Error assigning check function to %s", func)
    return lib
def _load_default() -> bool:
    global _lib
    try:
        if sys.platform == 'win32':
            _basedir = os.path.dirname(os.path.abspath(__file__))
            _bitness = struct.calcsize('P') * 8
            _target = 'x64' if _bitness > 32 else 'x86'
            _filename = os.path.join(_basedir, 'bin', f'libopus-0.{_target}.dll')
            _lib = libopus_loader(_filename)
        else:
            _lib = libopus_loader(ctypes.util.find_library('opus'))
    except Exception:
        _lib = None
    return _lib is not None
def load_opus(name: str) -> None:
    global _lib
    _lib = libopus_loader(name)
def is_loaded() -> bool:
    global _lib
    return _lib is not None
class OpusError(DiscordException):
    def __init__(self, code: int):
        self.code: int = code
        msg = _lib.opus_strerror(self.code).decode('utf-8')
        _log.debug('"%s" has happened', msg)
        super().__init__(msg)
class OpusNotLoaded(DiscordException):
    pass
class _OpusStruct:
    SAMPLING_RATE = 48000
    CHANNELS = 2
    FRAME_LENGTH = 20
    SAMPLE_SIZE = struct.calcsize('h') * CHANNELS
    SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)
    FRAME_SIZE = SAMPLES_PER_FRAME * SAMPLE_SIZE
    @staticmethod
    def get_opus_version() -> str:
        if not is_loaded() and not _load_default():
            raise OpusNotLoaded()
        return _lib.opus_get_version_string().decode('utf-8')
class Encoder(_OpusStruct):
    def __init__(self, application: int = APPLICATION_AUDIO):
        _OpusStruct.get_opus_version()
        self.application: int = application
        self.state: EncoderStruct = self._create_state()
        self.set_bitrate(128)
        self.set_fec(True)
        self.set_expected_packet_loss_percent(0.15)
        self.set_bandwidth('full')
        self.set_signal_type('auto')
    def __del__(self) -> None:
        if hasattr(self, 'state'):
            _lib.opus_encoder_destroy(self.state)
            self.state = None
    def _create_state(self) -> EncoderStruct:
        ret = ctypes.c_int()
        return _lib.opus_encoder_create(self.SAMPLING_RATE, self.CHANNELS, self.application, ctypes.byref(ret))
    def set_bitrate(self, kbps: int) -> int:
        kbps = min(512, max(16, int(kbps)))
        _lib.opus_encoder_ctl(self.state, CTL_SET_BITRATE, kbps * 1024)
        return kbps
    def set_bandwidth(self, req: BAND_CTL) -> None:
        if req not in band_ctl:
            raise KeyError(f'{req!r} is not a valid bandwidth setting. Try one of: {",".join(band_ctl)}')
        k = band_ctl[req]
        _lib.opus_encoder_ctl(self.state, CTL_SET_BANDWIDTH, k)
    def set_signal_type(self, req: SIGNAL_CTL) -> None:
        if req not in signal_ctl:
            raise KeyError(f'{req!r} is not a valid bandwidth setting. Try one of: {",".join(signal_ctl)}')
        k = signal_ctl[req]
        _lib.opus_encoder_ctl(self.state, CTL_SET_SIGNAL, k)
    def set_fec(self, enabled: bool = True) -> None:
        _lib.opus_encoder_ctl(self.state, CTL_SET_FEC, 1 if enabled else 0)
    def set_expected_packet_loss_percent(self, percentage: float) -> None:
        _lib.opus_encoder_ctl(self.state, CTL_SET_PLP, min(100, max(0, int(percentage * 100))))
    def encode(self, pcm: bytes, frame_size: int) -> bytes:
        max_data_bytes = len(pcm)
        pcm_ptr = ctypes.cast(pcm, c_int16_ptr)
        data = (ctypes.c_char * max_data_bytes)()
        ret = _lib.opus_encode(self.state, pcm_ptr, frame_size, data, max_data_bytes)
        return array.array('b', data[:ret]).tobytes()
class Decoder(_OpusStruct):
    def __init__(self):
        _OpusStruct.get_opus_version()
        self.state: DecoderStruct = self._create_state()
    def __del__(self) -> None:
        if hasattr(self, 'state'):
            _lib.opus_decoder_destroy(self.state)
            self.state = None
    def _create_state(self) -> DecoderStruct:
        ret = ctypes.c_int()
        return _lib.opus_decoder_create(self.SAMPLING_RATE, self.CHANNELS, ctypes.byref(ret))
    @staticmethod
    def packet_get_nb_frames(data: bytes) -> int:
        return _lib.opus_packet_get_nb_frames(data, len(data))
    @staticmethod
    def packet_get_nb_channels(data: bytes) -> int:
        return _lib.opus_packet_get_nb_channels(data)
    @classmethod
    def packet_get_samples_per_frame(cls, data: bytes) -> int:
        return _lib.opus_packet_get_samples_per_frame(data, cls.SAMPLING_RATE)
    def _set_gain(self, adjustment: int) -> int:
        return _lib.opus_decoder_ctl(self.state, CTL_SET_GAIN, adjustment)
    def set_gain(self, dB: float) -> int:
        dB_Q8 = max(-32768, min(32767, round(dB * 256)))
        return self._set_gain(dB_Q8)
    def set_volume(self, mult: float) -> int:
        return self.set_gain(20 * math.log10(mult))
    def _get_last_packet_duration(self) -> int:
        ret = ctypes.c_int32()
        _lib.opus_decoder_ctl(self.state, CTL_LAST_PACKET_DURATION, ctypes.byref(ret))
        return ret.value
    @overload
    def decode(self, data: bytes, *, fec: bool) -> bytes:
        ...
    @overload
    def decode(self, data: Literal[None], *, fec: Literal[False]) -> bytes:
        ...
    def decode(self, data: Optional[bytes], *, fec: bool = False) -> bytes:
        if data is None and fec:
            raise TypeError("Invalid arguments: FEC cannot be used with null data")
        if data is None:
            frame_size = self._get_last_packet_duration() or self.SAMPLES_PER_FRAME
            channel_count = self.CHANNELS
        else:
            frames = self.packet_get_nb_frames(data)
            channel_count = self.CHANNELS
            samples_per_frame = self.packet_get_samples_per_frame(data)
            frame_size = frames * samples_per_frame
        pcm = (ctypes.c_int16 * (frame_size * channel_count))()
        pcm_ptr = ctypes.cast(pcm, c_int16_ptr)
        ret = _lib.opus_decode(self.state, data, len(data) if data else 0, pcm_ptr, frame_size, fec)
        return array.array('h', pcm[: ret * channel_count]).tobytes()