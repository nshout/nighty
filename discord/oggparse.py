from __future__ import annotations
import struct
from typing import TYPE_CHECKING, ClassVar, IO, Generator, Tuple, Optional
from .errors import DiscordException
__all__ = (
    'OggError',
    'OggPage',
    'OggStream',
)
class OggError(DiscordException):
    pass
class OggPage:
    _header: ClassVar[struct.Struct] = struct.Struct('<xBQIIIB')
    if TYPE_CHECKING:
        flag: int
        gran_pos: int
        serial: int
        pagenum: int
        crc: int
        segnum: int
    def __init__(self, stream: IO[bytes]) -> None:
        try:
            header = stream.read(struct.calcsize(self._header.format))
            self.flag, self.gran_pos, self.serial, self.pagenum, self.crc, self.segnum = self._header.unpack(header)
            self.segtable: bytes = stream.read(self.segnum)
            bodylen = sum(struct.unpack('B' * self.segnum, self.segtable))
            self.data: bytes = stream.read(bodylen)
        except Exception:
            raise OggError('bad data stream') from None
    def iter_packets(self) -> Generator[Tuple[bytes, bool], None, None]:
        packetlen = offset = 0
        partial = True
        for seg in self.segtable:
            if seg == 255:
                packetlen += 255
                partial = True
            else:
                packetlen += seg
                yield self.data[offset : offset + packetlen], True
                offset += packetlen
                packetlen = 0
                partial = False
        if partial:
            yield self.data[offset:], False
class OggStream:
    def __init__(self, stream: IO[bytes]) -> None:
        self.stream: IO[bytes] = stream
    def _next_page(self) -> Optional[OggPage]:
        head = self.stream.read(4)
        if head == b'OggS':
            return OggPage(self.stream)
        elif not head:
            return None
        else:
            raise OggError('invalid header magic')
    def _iter_pages(self) -> Generator[OggPage, None, None]:
        page = self._next_page()
        while page:
            yield page
            page = self._next_page()
    def iter_packets(self) -> Generator[bytes, None, None]:
        partial = b''
        for page in self._iter_pages():
            for data, complete in page.iter_packets():
                partial += data
                if complete:
                    yield partial
                    partial = b''