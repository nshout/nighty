from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Union
from .utils import snowflake_time, _get_as_snowflake, resolve_invite
from .user import BaseUser
from .activity import BaseActivity, Spotify, create_activity
from .invite import Invite
from .enums import Status, try_enum
if TYPE_CHECKING:
    import datetime
    from .state import ConnectionState
    from .types.widget import (
        WidgetMember as WidgetMemberPayload,
        Widget as WidgetPayload,
    )
__all__ = (
    'WidgetChannel',
    'WidgetMember',
    'Widget',
)
class WidgetChannel:
    __slots__ = ('id', 'name', 'position')
    def __init__(self, id: int, name: str, position: int) -> None:
        self.id: int = id
        self.name: str = name
        self.position: int = position
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return f'<WidgetChannel id={self.id} name={self.name!r} position={self.position!r}>'
    @property
    def mention(self) -> str:
        return f'<
    @property
    def created_at(self) -> datetime.datetime:
        return snowflake_time(self.id)
class WidgetMember(BaseUser):
    __slots__ = (
        'status',
        'nick',
        'avatar',
        'activity',
        'deafened',
        'suppress',
        'muted',
        'connected_channel',
    )
    if TYPE_CHECKING:
        activity: Optional[Union[BaseActivity, Spotify]]
    def __init__(
        self,
        *,
        state: ConnectionState,
        data: WidgetMemberPayload,
        connected_channel: Optional[WidgetChannel] = None,
    ) -> None:
        super().__init__(state=state, data=data)
        self.nick: Optional[str] = data.get('nick')
        self.status: Status = try_enum(Status, data.get('status'))
        self.deafened: Optional[bool] = data.get('deaf', False) or data.get('self_deaf', False)
        self.muted: Optional[bool] = data.get('mute', False) or data.get('self_mute', False)
        self.suppress: Optional[bool] = data.get('suppress', False)
        try:
            game = data['game']
        except KeyError:
            activity = None
        else:
            activity = create_activity(game, state)
        self.activity: Optional[Union[BaseActivity, Spotify]] = activity
        self.connected_channel: Optional[WidgetChannel] = connected_channel
    def __repr__(self) -> str:
        return f"<WidgetMember name={self.name!r} global_name={self.global_name!r} bot={self.bot} nick={self.nick!r}>"
    @property
    def display_name(self) -> str:
        return self.nick or self.name
class Widget:
    __slots__ = ('state', 'channels', '_invite', 'id', 'members', 'name', 'presence_count')
    def __init__(self, *, state: ConnectionState, data: WidgetPayload) -> None:
        self.state = state
        self._invite = data['instant_invite']
        self.name: str = data['name']
        self.id: int = int(data['id'])
        self.channels: List[WidgetChannel] = []
        for channel in data.get('channels', []):
            _id = int(channel['id'])
            self.channels.append(WidgetChannel(id=_id, name=channel['name'], position=channel['position']))
        self.members: List[WidgetMember] = []
        channels = {channel.id: channel for channel in self.channels}
        for member in data.get('members', []):
            connected_channel = _get_as_snowflake(member, 'channel_id')
            if connected_channel is not None:
                if connected_channel in channels:
                    connected_channel = channels[connected_channel]
                else:
                    connected_channel = WidgetChannel(id=connected_channel, name='', position=0)
            self.members.append(WidgetMember(state=self.state, data=member, connected_channel=connected_channel))
        self.presence_count: int = data['presence_count']
    def __str__(self) -> str:
        return self.json_url
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Widget):
            return self.id == other.id
        return False
    def __repr__(self) -> str:
        return f'<Widget id={self.id} name={self.name!r} invite_url={self.invite_url!r}>'
    @property
    def created_at(self) -> datetime.datetime:
        return snowflake_time(self.id)
    @property
    def json_url(self) -> str:
        return f"https://discord.com/api/guilds/{self.id}/widget.json"
    @property
    def invite_url(self) -> Optional[str]:
        return self._invite
    async def fetch_invite(self, *, with_counts: bool = True) -> Optional[Invite]:
        if self._invite:
            resolved = resolve_invite(self._invite)
            data = await self.state.http.get_invite(resolved.code, with_counts=with_counts)
            return Invite.from_incomplete(state=self.state, data=data)
        return None