from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Generator, Optional, Type, TypeVar
if TYPE_CHECKING:
    from .abc import Messageable, MessageableChannel
    from types import TracebackType
    BE = TypeVar('BE', bound=BaseException)
__all__ = (
    'Typing',
)
def _typing_done_callback(fut: asyncio.Future) -> None:
    try:
        fut.exception()
    except (asyncio.CancelledError, Exception):
        pass
class Typing:
    def __init__(self, messageable: Messageable) -> None:
        self.loop: asyncio.AbstractEventLoop = messageable.state.loop
        self.messageable: Messageable = messageable
        self.channel: Optional[MessageableChannel] = None
    async def _get_channel(self) -> MessageableChannel:
        if self.channel:
            return self.channel
        self.channel = channel = await self.messageable._get_channel()
        return channel
    async def wrapped_typer(self) -> None:
        channel = await self._get_channel()
        await channel.state.http.send_typing(channel.id)
    def __await__(self) -> Generator[None, None, None]:
        return self.wrapped_typer().__await__()
    async def do_typing(self) -> None:
        channel = await self._get_channel()
        typing = channel.state.http.send_typing
        while True:
            await asyncio.sleep(5)
            await typing(channel.id)
    async def __aenter__(self) -> None:
        channel = await self._get_channel()
        await channel.state.http.send_typing(channel.id)
        self.task: asyncio.Task[None] = self.loop.create_task(self.do_typing())
        self.task.add_done_callback(_typing_done_callback)
    async def __aexit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        self.task.cancel()