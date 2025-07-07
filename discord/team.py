from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterator, List, Optional, Union, overload
from . import utils
from .asset import Asset
from .enums import ApplicationMembershipState, PayoutAccountStatus, PayoutReportType, PayoutStatus, try_enum
from .metadata import Metadata
from .mixins import Hashable
from .object import Object
from .user import User, _UserTag
if TYPE_CHECKING:
    from datetime import date
    from .abc import Snowflake, SnowflakeTime
    from .application import Application, Company
    from .state import ConnectionState
    from .types.team import Team as TeamPayload, TeamMember as TeamMemberPayload, TeamPayout as TeamPayoutPayload
    from .types.user import PartialUser as PartialUserPayload
__all__ = (
    'Team',
    'TeamMember',
    'TeamPayout',
)
MISSING = utils.MISSING
class Team(Hashable):
    __slots__ = (
        'state',
        'id',
        'name',
        '_icon',
        'owner_id',
        'members',
        'payout_account_status',
        'stripe_connect_account_id',
    )
    def __init__(self, state: ConnectionState, data: TeamPayload):
        self.state: ConnectionState = state
        self.members: List[TeamMember] = []
        self.payout_account_status: Optional[PayoutAccountStatus] = None
        self.stripe_connect_account_id: Optional[str] = None
        self._update(data)
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'
    def __str__(self) -> str:
        return self.name
    def _update(self, data: TeamPayload):
        state = self.state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data['icon']
        self.owner_id = owner_id = int(data['owner_user_id'])
        if 'members' in data:
            self.members = [TeamMember(self, state=state, data=member) for member in data.get('members', [])]
        if not self.owner:
            owner = self.state.get_user(owner_id)
            if owner:
                user: PartialUserPayload = owner._to_minimal_user_json()
                member: TeamMemberPayload = {
                    'user': user,
                    'team_id': self.id,
                    'membership_state': 2,
                    'permissions': ['*'],
                }
                self.members.append(TeamMember(self, self.state, member))
        if 'payout_account_status' in data:
            self.payout_account_status = try_enum(PayoutAccountStatus, data.get('payout_account_status'))
        if 'stripe_connect_account_id' in data:
            self.stripe_connect_account_id = data.get('stripe_connect_account_id')
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_icon(self.state, self.id, self._icon, path='team')
    @property
    def default_icon(self) -> Asset:
        return Asset._from_default_avatar(self.state, int(self.id) % 5)
    @property
    def display_icon(self) -> Asset:
        return self.icon or self.default_icon
    @property
    def owner(self) -> Optional[TeamMember]:
        return utils.get(self.members, id=self.owner_id)
    async def edit(
        self,
        *,
        name: str = MISSING,
        icon: Optional[bytes] = MISSING,
        owner: Snowflake = MISSING,
    ) -> None:
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if icon is not MISSING:
            if icon is not None:
                payload['icon'] = utils._bytes_to_base64_data(icon)
            else:
                payload['icon'] = ''
        if owner is not MISSING:
            payload['owner_user_id'] = owner.id
        data = await self.state.http.edit_team(self.id, payload)
        self._update(data)
    async def applications(self) -> List[Application]:
        from .application import Application
        state = self.state
        data = await state.http.get_team_applications(self.id)
        return [Application(state=state, data=app, team=self) for app in data]
    async def fetch_members(self) -> List[TeamMember]:
        data = await self.state.http.get_team_members(self.id)
        members = [TeamMember(self, self.state, member) for member in data]
        self.members = members
        return members
    @overload
    async def invite_member(self, user: _UserTag, /) -> TeamMember:
        ...
    @overload
    async def invite_member(self, user: str, /) -> TeamMember:
        ...
    @overload
    async def invite_member(self, username: str, discriminator: str, /) -> TeamMember:
        ...
    async def invite_member(self, *args: Union[_UserTag, str]) -> TeamMember:
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, _UserTag):
                user = str(user)
            username, _, discrim = user.partition('
        elif len(args) == 2:
            username, discrim = args
        else:
            raise TypeError(f'invite_member() takes 1 or 2 arguments but {len(args)} were given')
        state = self.state
        data = await state.http.invite_team_member(self.id, username, discrim or 0)
        member = TeamMember(self, state, data)
        self.members.append(member)
        return member
    async def create_company(self, name: str, /) -> Company:
        from .application import Company
        state = self.state
        data = await state.http.create_team_company(self.id, name)
        return Company(data=data)
    async def payouts(
        self,
        *,
        limit: Optional[int] = 96,
        before: Optional[SnowflakeTime] = None,
    ) -> AsyncIterator[TeamPayout]:
        async def strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await self.state.http.get_team_payouts(self.id, limit=retrieve, before=before_id)
            if data:
                if limit is not None:
                    limit -= len(data)
                before = Object(id=int(data[-1]['id']))
            return data, before, limit
        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        while True:
            retrieve = min(96 if limit is None else limit, 100)
            if retrieve < 1:
                return
            data, before, limit = await strategy(retrieve, before, limit)
            if len(data) < 96:
                limit = 0
            for payout in data:
                yield TeamPayout(data=payout, team=self)
    async def leave(self) -> None:
        await self.state.http.remove_team_member(self.id, self.state.self_id)
    async def delete(self) -> None:
        await self.state.http.delete_team(self.id)
class TeamMember(User):
    __slots__ = ('team', 'membership_state', 'permissions')
    def __init__(self, team: Team, state: ConnectionState, data: TeamMemberPayload):
        self.team: Team = team
        self.membership_state: ApplicationMembershipState = try_enum(ApplicationMembershipState, data['membership_state'])
        self.permissions: List[str] = data.get('permissions', ['*'])
        super().__init__(state=state, data=data['user'])
    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'global_name={self.global_name!r} membership_state={self.membership_state!r}>'
        )
    async def remove(self) -> None:
        await self.state.http.remove_team_member(self.team.id, self.id)
class TeamPayout(Hashable):
    def __init__(self, *, data: TeamPayoutPayload, team: Team):
        self.team: Team = team
        self.id: int = int(data['id'])
        self.user_id: int = int(data['user_id'])
        self.status: PayoutStatus = try_enum(PayoutStatus, data['status'])
        self.amount: int = data['amount']
        self.period_start: date = utils.parse_date(data['period_start'])
        self.period_end: Optional[date] = utils.parse_date(data.get('period_end'))
        self.payout_date: Optional[date] = utils.parse_date(data.get('payout_date'))
        self.tipalti_submission_response: Optional[Metadata] = (
            Metadata(data['latest_tipalti_submission_response']) if 'latest_tipalti_submission_response' in data else None
        )
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} status={self.status!r}>'
    async def report(self, type: PayoutReportType) -> bytes:
        return await self.team.state.http.get_team_payout_report(self.team.id, self.id, str(type))