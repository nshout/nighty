from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Optional
from .application import ApplicationActivityStatistics, ApplicationBranch, PartialApplication
from .entitlements import Entitlement
from .enums import SKUType, try_enum
from .flags import LibraryApplicationFlags
from .mixins import Hashable
from .utils import MISSING, _get_as_snowflake, find, parse_date, parse_time
if TYPE_CHECKING:
    from datetime import date, datetime
    from .asset import Asset
    from .state import ConnectionState
    from .types.application import Branch as BranchPayload
    from .types.library import LibraryApplication as LibraryApplicationPayload
    from .types.store import PartialSKU as PartialSKUPayload
__all__ = (
    'LibrarySKU',
    'LibraryApplication',
)
class LibrarySKU(Hashable):
    __slots__ = (
        'id',
        'type',
        'preorder_release_date',
        'preorder_released_at',
        'premium',
    )
    def __init__(self, data: PartialSKUPayload):
        self.id: int = int(data['id'])
        self.type: SKUType = try_enum(SKUType, data['type'])
        self.preorder_release_date: Optional[date] = parse_date(data.get('preorder_approximate_release_date'))
        self.preorder_released_at: Optional[datetime] = parse_time(data.get('preorder_release_at'))
        self.premium: bool = data.get('premium', False)
    def __repr__(self) -> str:
        return f'<LibrarySKU id={self.id} type={self.type!r} preorder_release_date={self.preorder_release_date!r} preorder_released_at={self.preorder_released_at!r} premium={self.premium!r}>'
class LibraryApplication:
    __slots__ = (
        'created_at',
        'application',
        'sku_id',
        'sku',
        'entitlements',
        'branch_id',
        'branch',
        '_flags',
        'state',
    )
    def __init__(self, *, state: ConnectionState, data: LibraryApplicationPayload):
        self.state = state
        self._update(data)
    def _update(self, data: LibraryApplicationPayload):
        state = self.state
        self.created_at: datetime = parse_time(data['created_at'])
        self.application: PartialApplication = PartialApplication(state=state, data=data['application'])
        self.sku_id: int = int(data['sku_id'])
        self.sku: LibrarySKU = LibrarySKU(data=data['sku'])
        self.entitlements: List[Entitlement] = [Entitlement(state=state, data=e) for e in data.get('entitlements', [])]
        self._flags = data.get('flags', 0)
        self.branch_id: int = int(data['branch_id'])
        branch: Optional[BranchPayload] = data.get('branch')
        if not branch:
            branch = {'id': self.branch_id, 'name': 'master'}
        self.branch: ApplicationBranch = ApplicationBranch(state=state, data=branch, application_id=self.application.id)
    def __repr__(self) -> str:
        return f'<LibraryApplication created_at={self.created_at!r} application={self.application!r} sku={self.sku!r} branch={self.branch!r}>'
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LibraryApplication):
            return self.application.id == other.application.id and self.branch_id == other.branch_id
        return False
    def __ne__(self, other: Any) -> bool:
        if isinstance(other, LibraryApplication):
            return self.application.id != other.application.id or self.branch_id != other.branch_id
        return True
    def __hash__(self) -> int:
        return hash((self.application.id, self.branch_id))
    def __str__(self) -> str:
        return self.application.name
    @property
    def name(self) -> str:
        return self.application.name
    @property
    def icon(self) -> Optional[Asset]:
        return self.application.icon
    @property
    def flags(self) -> LibraryApplicationFlags:
        return LibraryApplicationFlags._from_value(self._flags)
    async def activity_statistics(self) -> ApplicationActivityStatistics:
        state = self.state
        data = await state.http.get_activity_statistics()
        app = find(lambda a: _get_as_snowflake(a, 'application_id') == self.application.id, data)
        return ApplicationActivityStatistics(
            data=app
            or {'application_id': self.application.id, 'total_duration': 0, 'last_played_at': '1970-01-01T00:00:00+00:00'},
            state=state,
        )
    async def mark_installed(self) -> None:
        await self.state.http.mark_library_entry_installed(self.application.id, self.branch_id)
    async def edit(self, *, flags: LibraryApplicationFlags = MISSING) -> None:
        payload = {}
        if flags is not MISSING:
            payload['flags'] = flags.value
        data = await self.state.http.edit_library_entry(self.application.id, self.branch_id, payload)
        self._update(data)
    async def delete(self) -> None:
        await self.state.http.delete_library_entry(self.application.id, self.branch_id)