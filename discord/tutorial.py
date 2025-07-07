from __future__ import annotations
from typing import TYPE_CHECKING, List, Sequence
from .utils import SequenceProxy
if TYPE_CHECKING:
    from typing_extensions import Self
    from .state import ConnectionState
    from .types.gateway import Tutorial as TutorialPayload
__all__ = (
    'Tutorial',
)
class Tutorial:
    __slots__ = ('suppressed', '_indicators', 'state')
    def __init__(self, *, data: TutorialPayload, state: ConnectionState):
        self.state: ConnectionState = state
        self.suppressed: bool = data.get('indicators_suppressed', True)
        self._indicators: List[str] = data.get('indicators_confirmed', [])
    def __repr__(self) -> str:
        return f'<Tutorial suppressed={self.suppressed} indicators={self._indicators!r}>'
    @classmethod
    def default(cls, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self.suppressed = True
        self._indicators = []
        return self
    @property
    def indicators(self) -> Sequence[str]:
        return SequenceProxy(self._indicators)
    async def suppress(self) -> None:
        await self.state.http.suppress_tutorial()
        self.suppressed = True
    async def confirm(self, *indicators: str) -> None:
        r
        req = self.state.http.confirm_tutorial_indicator
        for indicator in indicators:
            if indicator not in self.indicators:
                await req(indicator)
                self._indicators.append(indicator)
        self._indicators.sort()