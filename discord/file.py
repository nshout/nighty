from __future__ import annotations
import io
import os
from base64 import b64encode
from hashlib import md5
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union
import yarl
from .utils import MISSING, cached_slot_property
if TYPE_CHECKING:
    from typing_extensions import Self
    from .state import ConnectionState
    from .types.message import (
        CloudAttachment as CloudAttachmentPayload,
        PartialAttachment as PartialAttachmentPayload,
        UploadedAttachment as UploadedAttachmentPayload,
    )
__all__ = (
    'File',
    'CloudFile',
)
def _strip_spoiler(filename: str) -> Tuple[str, bool]:
    stripped = filename
    while stripped.startswith('SPOILER_'):
        stripped = stripped[8:]
    spoiler = stripped != filename
    return stripped, spoiler
class _FileBase:
    __slots__ = ('_filename', 'spoiler', 'description')
    def __init__(self, filename: str, *, spoiler: bool = False, description: Optional[str] = None):
        self._filename, filename_spoiler = _strip_spoiler(filename)
        if spoiler is MISSING:
            spoiler = filename_spoiler
        self.spoiler: bool = spoiler
        self.description: Optional[str] = description
    @property
    def filename(self) -> str:
        return 'SPOILER_' + self._filename if self.spoiler else self._filename
    @filename.setter
    def filename(self, value: str) -> None:
        self._filename, self.spoiler = _strip_spoiler(value)
    def to_dict(self, index: int) -> PartialAttachmentPayload:
        payload: PartialAttachmentPayload = {
            'id': str(index),
            'filename': self.filename,
        }
        if self.description is not None:
            payload['description'] = self.description
        return payload
    def reset(self, *, seek: Union[int, bool] = True) -> None:
        return
    def close(self) -> None:
        return
class File(_FileBase):
    r
    __slots__ = ('fp', '_original_pos', '_owner', '_closer', '_cs_md5', '_cs_size')
    def __init__(
        self,
        fp: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase],
        filename: Optional[str] = None,
        *,
        spoiler: bool = MISSING,
        description: Optional[str] = None,
    ):
        if isinstance(fp, io.IOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError(f'File buffer {fp!r} must be seekable and readable')
            self.fp: io.BufferedIOBase = fp
            self._original_pos = fp.tell()
            self._owner = False
        else:
            self.fp = open(fp, 'rb')
            self._original_pos = 0
            self._owner = True
        self._closer = self.fp.close
        self.fp.close = lambda: None
        if filename is None:
            if isinstance(fp, str):
                _, filename = os.path.split(fp)
            else:
                filename = getattr(fp, 'name', 'untitled')
        super().__init__(filename, spoiler=spoiler, description=description)
    @cached_slot_property('_cs_md5')
    def md5(self):
        try:
            return md5(self.fp.read())
        finally:
            self.reset()
    @property
    def b64_md5(self) -> str:
        return b64encode(self.md5.digest()).decode('ascii')
    @cached_slot_property('_cs_size')
    def size(self) -> int:
        self.fp.seek(0, os.SEEK_END)
        try:
            return self.fp.tell()
        finally:
            self.reset()
    def to_upload_dict(self, index: int) -> UploadedAttachmentPayload:
        return {
            'id': str(index),
            'filename': self.filename,
            'file_size': self.size,
        }
    def reset(self, *, seek: Union[int, bool] = True) -> None:
        if seek:
            self.fp.seek(self._original_pos)
    def close(self) -> None:
        self.fp.close = self._closer
        if self._owner:
            self._closer()
class CloudFile(_FileBase):
    __slots__ = ('url', 'upload_filename', 'state')
    def __init__(
        self,
        url: str,
        filename: str,
        upload_filename: str,
        *,
        spoiler: bool = MISSING,
        description: Optional[str] = None,
        state: ConnectionState,
    ):
        super().__init__(filename, spoiler=spoiler, description=description)
        self.url = url
        self.upload_filename = upload_filename
        self.state = state
    @classmethod
    async def from_file(cls, *, file: File, state: ConnectionState, data: CloudAttachmentPayload) -> Self:
        await state.http.upload_to_cloud(data['upload_url'], file)
        return cls(data['upload_url'], file._filename, data['upload_filename'], description=file.description, state=state)
    @property
    def upload_id(self) -> str:
        url = yarl.URL(self.url)
        return url.query['upload_id']
    def to_dict(self, index: int) -> PartialAttachmentPayload:
        payload = super().to_dict(index)
        payload['uploaded_filename'] = self.upload_filename
        return payload
    async def delete(self) -> None:
        await self.state.http.delete_attachment(self.upload_filename)