from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from .utils import MISSING, _get_as_snowflake
from .mixins import Hashable
from .enums import PrivacyLevel, try_enum
__all__ = (
    'StageInstance',
)
if TYPE_CHECKING:
    from typing_extensions import Self
    from .types.channel import StageInstance as StageInstancePayload, InviteStageInstance as InviteStageInstancePayload
    from .state import ConnectionState
    from .channel import StageChannel
    from .guild import Guild
    from .scheduled_event import ScheduledEvent
    from .invite import Invite
    from .member import Member
class StageInstance(Hashable):
    __slots__ = (
        'state',
        'id',
        'guild',
        'channel_id',
        'topic',
        'privacy_level',
        'discoverable_disabled',
        'invite_code',
        'scheduled_event_id',
        '_members',
        '_participant_count',
    )
    def __init__(self, *, state: ConnectionState, guild: Guild, data: StageInstancePayload) -> None:
        self.state: ConnectionState = state
        self.guild: Guild = guild
        self._members: Optional[List[Member]] = None
        self._participant_count: Optional[int] = None
        self._update(data)
    def _update(self, data: StageInstancePayload, /) -> None:
        self.id: int = int(data['id'])
        self.channel_id: int = int(data['channel_id'])
        self.topic: str = data['topic']
        self.privacy_level: PrivacyLevel = try_enum(PrivacyLevel, data['privacy_level'])
        self.discoverable_disabled: bool = data.get('discoverable_disabled', False)
        self.invite_code: Optional[str] = data.get('invite_code')
        self.scheduled_event_id: Optional[int] = _get_as_snowflake(data, 'guild_scheduled_event_id')
    @staticmethod
    def _resolve_stage_instance_id(invite: Invite) -> int:
        try:
            return invite.channel.instance.id
        except AttributeError:
            return invite.channel.id
    @classmethod
    def from_invite(cls, invite: Invite, data: InviteStageInstancePayload, /) -> Self:
        state = invite.state
        payload: StageInstancePayload = {
            'id': cls._resolve_stage_instance_id(invite),
            'guild_id': invite.guild.id,
            'channel_id': invite.channel.id,
            'topic': data['topic'],
            'privacy_level': PrivacyLevel.public.value,
            'discoverable_disabled': False,
            'invite_code': invite.code,
            'guild_scheduled_event_id': invite.scheduled_event.id if invite.scheduled_event else None,
        }
        self = cls(state=state, guild=invite.guild, data=payload)
        self._members = [Member(data=mdata, state=state, guild=invite.guild) for mdata in data['members']]
        self._participant_count = data.get('participant_count', len(self._members))
        return self
    def __repr__(self) -> str:
        return f'<StageInstance id={self.id} guild={self.guild!r} channel_id={self.channel_id} topic={self.topic!r}>'
    @property
    def invite_url(self) -> Optional[str]:
        if self.invite_code is None:
            return None
        return f'https://discord.gg/{self.invite_code}'
    @property
    def discoverable(self) -> bool:
        return not self.discoverable_disabled
    @property
    def channel(self) -> Optional[StageChannel]:
        return self.guild._resolve_channel(self.channel_id)
    @property
    def scheduled_event(self) -> Optional[ScheduledEvent]:
        return self.guild.get_scheduled_event(self.scheduled_event_id)
    @property
    def speakers(self) -> List[Member]:
        if self._members is not None or self.channel is None:
            return self._members or []
        return self.channel.speakers
    @property
    def participant_count(self) -> int:
        if self._participant_count is not None or self.channel is None:
            return self._participant_count or 0
        return len(self.channel.voice_states)
    async def edit(
        self,
        *,
        topic: str = MISSING,
        privacy_level: PrivacyLevel = MISSING,
        reason: Optional[str] = None,
    ) -> None:
        payload = {}
        if topic is not MISSING:
            payload['topic'] = topic
        if privacy_level is not MISSING:
            if not isinstance(privacy_level, PrivacyLevel):
                raise TypeError('privacy_level field must be of type PrivacyLevel')
            payload['privacy_level'] = privacy_level.value
        if payload:
            await self.state.http.edit_stage_instance(self.channel_id, **payload, reason=reason)
    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_stage_instance(self.channel_id, reason=reason)