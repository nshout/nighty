from __future__ import annotations
from typing import Literal, TypedDict, List, Optional
from typing_extensions import NotRequired
from .user import PartialUser
from .snowflake import Snowflake
class TeamMember(TypedDict):
    user: PartialUser
    membership_state: int
    permissions: List[str]
    team_id: Snowflake
class Team(TypedDict):
    id: Snowflake
    name: str
    owner_user_id: Snowflake
    icon: Optional[str]
    payout_account_status: NotRequired[Optional[Literal[1, 2, 3, 4, 5, 6]]]
    stripe_connect_account_id: NotRequired[Optional[str]]
    members: NotRequired[List[TeamMember]]
class TeamPayout(TypedDict):
    id: Snowflake
    user_id: Snowflake
    amount: int
    status: Literal[1, 2, 3, 4, 5]
    period_start: str
    period_end: Optional[str]
    payout_date: Optional[str]
    latest_tipalti_submission_response: NotRequired[dict]