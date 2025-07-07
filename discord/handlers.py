from __future__ import annotations
from typing import Any, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from aiohttp import BasicAuth
__all__ = (
    'CaptchaHandler',
)
class CaptchaHandler:
    async def startup(self):
        pass
    async def prefetch_token(self, proxy: Optional[str], proxy_auth: Optional[BasicAuth], /) -> None:
        pass
    async def fetch_token(
        self,
        data: Dict[str, Any],
        proxy: Optional[str],
        proxy_auth: Optional[BasicAuth],
        /,
    ) -> str:
        raise NotImplementedError