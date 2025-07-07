from __future__ import annotations
from typing import Callable, Dict, Iterable, List, Literal, Optional, Sequence, Union, TYPE_CHECKING
import asyncio
import array
import copy
from .mixins import Hashable
from .abc import Messageable, GuildChannel, _purge_helper
from .enums import ChannelType, try_enum
from .errors import ClientException, InvalidData
from .flags import ChannelFlags
from .permissions import Permissions
from .utils import MISSING, parse_time, snowflake_time, _get_as_snowflake, _unique
__all__ = (
    'Thread',
    'ThreadMember',
)
if TYPE_CHECKING:
    from datetime import date, datetime
    from typing_extensions import Self
    from .types.gateway import ThreadMemberListUpdateEvent
    from .types.threads import (
        BaseThreadMember as BaseThreadMemberPayload,
        Thread as ThreadPayload,
        ThreadMember as ThreadMemberPayload,
        ThreadMetadata,
        ThreadArchiveDuration,
    )
    from .guild import Guild
    from .channel import TextChannel, CategoryChannel, ForumChannel, ForumTag
    from .member import Member
    from .message import Message, PartialMessage
    from .abc import Snowflake, SnowflakeTime
    from .role import Role
    from .state import ConnectionState
    from .read_state import ReadState
class Thread(Messageable, Hashable):
    __slots__ = (
        'name',
        'id',
        'guild',
        '_type',
        'state',
        '_members',
        'owner_id',
        'parent_id',
        'last_message_id',
        'last_pin_timestamp',
        'message_count',
        'member_count',
        'slowmode_delay',
        'locked',
        'archived',
        'invitable',
        'auto_archive_duration',
        'archive_timestamp',
        '_member_ids',
        '_created_at',
        '_flags',
        '_applied_tags',
    )
    def __init__(self, *, guild: Guild, state: ConnectionState, data: ThreadPayload) -> None:
        self.state: ConnectionState = state
        self.guild: Guild = guild
        self._members: Dict[int, ThreadMember] = {}
        self._from_data(data)
    async def _get_channel(self) -> Self:
        return self
    def __repr__(self) -> str:
        return (
            f'<Thread id={self.id!r} name={self.name!r} parent={self.parent}'
            f' owner_id={self.owner_id!r} locked={self.locked} archived={self.archived}>'
        )
    def __str__(self) -> str:
        return self.name
    def _from_data(self, data: ThreadPayload):
        self.id: int = int(data['id'])
        self.parent_id: int = int(data['parent_id'])
        self.owner_id: int = int(data['owner_id'])
        self.name: str = data['name']
        self._type: ChannelType = try_enum(ChannelType, data['type'])
        self.last_message_id: Optional[int] = _get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime] = parse_time(data.get('last_pin_timestamp'))
        self.slowmode_delay: int = data.get('rate_limit_per_user', 0)
        self.message_count: int = data['message_count']
        self.member_count: int = data['member_count']
        self._member_ids: List[Union[str, int]] = data['member_ids_preview']
        self._flags: int = data.get('flags', 0)
        self._applied_tags: array.array[int] = array.array('Q', map(int, data.get('applied_tags', [])))
        self._unroll_metadata(data['thread_metadata'])
    def _unroll_metadata(self, data: ThreadMetadata):
        self.archived: bool = data['archived']
        self.auto_archive_duration: int = data['auto_archive_duration']
        self.archive_timestamp: datetime = parse_time(data['archive_timestamp'])
        self.locked: bool = data.get('locked', False)
        self.invitable: bool = data.get('invitable', True)
        self._created_at: Optional[datetime] = parse_time(data.get('create_timestamp'))
    def _update(self, data):
        old = copy.copy(self)
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._flags: int = data.get('flags', 0)
        self._applied_tags: array.array[int] = array.array('Q', map(int, data.get('applied_tags', [])))
        if (meta := data.get('thread_metadata')) is not None:
            self._unroll_metadata(meta)
        if (name := data.get('name')) is not None:
            self.name = name
        if (last_message_id := _get_as_snowflake(data, 'last_message_id')) is not None:
            self.last_message_id = last_message_id
        if (message_count := data.get('message_count')) is not None:
            self.message_count = message_count
        if (member_count := data.get('member_count')) is not None:
            self.member_count = member_count
        if (member_ids := data.get('member_ids_preview')) is not None:
            self._member_ids = member_ids
        attrs = [x for x in self.__slots__ if not any(y in x for y in ('member', 'guild', 'state', 'count'))]
        if any(getattr(self, attr) != getattr(old, attr) for attr in attrs):
            return old
    @property
    def type(self) -> ChannelType:
        return self._type
    @property
    def parent(self) -> Optional[Union[TextChannel, ForumChannel]]:
        return self.guild.get_channel(self.parent_id)
    @property
    def channel(self) -> Optional[Union[TextChannel, ForumChannel]]:
        return self.parent
    @property
    def flags(self) -> ChannelFlags:
        return ChannelFlags._from_value(self._flags)
    @property
    def owner(self) -> Optional[Member]:
        return self.guild.get_member(self.owner_id)
    @property
    def mention(self) -> str:
        return f'<
    @property
    def created_at(self) -> datetime:
        return self._created_at or snowflake_time(self.id)
    @property
    def jump_url(self) -> str:
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'
    @property
    def members(self) -> List[ThreadMember]:
        return list(self._members.values())
    @property
    def applied_tags(self) -> List[ForumTag]:
        tags = []
        if self.parent is None or self.parent.type != ChannelType.forum:
            return tags
        parent = self.parent
        for tag_id in self._applied_tags:
            tag = parent.get_tag(tag_id)
            if tag is not None:
                tags.append(tag)
        return tags
    @property
    def read_state(self) -> ReadState:
        return self.state.get_read_state(self.id)
    @property
    def starter_message(self) -> Optional[Message]:
        return self.state._get_message(self.id)
    @property
    def last_message(self) -> Optional[Message]:
        return self.state._get_message(self.last_message_id) if self.last_message_id else None
    @property
    def acked_message_id(self) -> int:
        return self.read_state.last_acked_id
    @property
    def acked_message(self) -> Optional[Message]:
        acked_message_id = self.acked_message_id
        if acked_message_id is None:
            return
        message = self.state._get_message(acked_message_id)
        if message and message.channel.id == self.id:
            return message
    @property
    def acked_pin_timestamp(self) -> Optional[datetime]:
        return self.read_state.last_pin_timestamp
    @property
    def mention_count(self) -> int:
        return self.read_state.badge_count
    @property
    def last_viewed_timestamp(self) -> date:
        return self.read_state.last_viewed
    @property
    def category(self) -> Optional[CategoryChannel]:
        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')
        return parent.category
    @property
    def category_id(self) -> Optional[int]:
        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')
        return parent.category_id
    @property
    def me(self) -> Optional[ThreadMember]:
        self_id = self.state.self_id
        return self._members.get(self_id)
    @me.setter
    def me(self, member) -> None:
        self._members[member.id] = member
    def is_private(self) -> bool:
        return self._type is ChannelType.private_thread
    def is_news(self) -> bool:
        return self._type is ChannelType.news_thread
    def is_nsfw(self) -> bool:
        parent = self.parent
        return parent is not None and parent.is_nsfw()
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')
        base = GuildChannel.permissions_for(parent, obj)
        if not base.send_messages_in_threads:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value
        return base
    async def delete_messages(self, messages: Iterable[Snowflake], /, *, reason: Optional[str] = None) -> None:
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)
        if len(messages) == 0:
            return
        await self.state._delete_messages(self.id, messages, reason=reason)
    async def purge(
        self,
        *,
        limit: Optional[int] = 100,
        check: Callable[[Message], bool] = MISSING,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
        reason: Optional[str] = None,
    ) -> List[Message]:
        return await _purge_helper(
            self,
            limit=limit,
            check=check,
            before=before,
            after=after,
            around=around,
            oldest_first=oldest_first,
            reason=reason,
        )
    async def edit(
        self,
        *,
        name: str = MISSING,
        archived: bool = MISSING,
        locked: bool = MISSING,
        invitable: bool = MISSING,
        pinned: bool = MISSING,
        slowmode_delay: int = MISSING,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        applied_tags: Sequence[ForumTag] = MISSING,
        reason: Optional[str] = None,
    ) -> Thread:
        payload = {}
        if name is not MISSING:
            payload['name'] = str(name)
        if archived is not MISSING:
            payload['archived'] = archived
        if auto_archive_duration is not MISSING:
            payload['auto_archive_duration'] = auto_archive_duration
        if locked is not MISSING:
            payload['locked'] = locked
        if invitable is not MISSING:
            payload['invitable'] = invitable
        if slowmode_delay is not MISSING:
            payload['rate_limit_per_user'] = slowmode_delay
        if pinned is not MISSING:
            flags = self.flags
            flags.pinned = pinned
            payload['flags'] = flags.value
        if applied_tags is not MISSING:
            payload['applied_tags'] = [str(tag.id) for tag in applied_tags]
        data = await self.state.http.edit_channel(self.id, **payload, reason=reason)
        return Thread(data=data, state=self.state, guild=self.guild)
    async def add_tags(self, *tags: Snowflake, reason: Optional[str] = None) -> None:
        r
        applied_tags = [str(tag) for tag in self._applied_tags]
        applied_tags.extend(str(tag.id) for tag in tags)
        await self.state.http.edit_channel(self.id, applied_tags=_unique(applied_tags), reason=reason)
    async def remove_tags(self, *tags: Snowflake, reason: Optional[str] = None) -> None:
        r
        applied_tags: Dict[str, Literal[None]] = {str(tag): None for tag in self._applied_tags}
        for tag in tags:
            applied_tags.pop(str(tag.id), None)
        await self.state.http.edit_channel(self.id, applied_tags=list(applied_tags.keys()), reason=reason)
    async def join(self) -> None:
        await self.state.http.join_thread(self.id)
    async def leave(self) -> None:
        await self.state.http.leave_thread(self.id)
    async def add_user(self, user: Snowflake, /) -> None:
        await self.state.http.add_user_to_thread(self.id, user.id)
    async def remove_user(self, user: Snowflake, /) -> None:
        await self.state.http.remove_user_from_thread(self.id, user.id)
    async def fetch_members(self) -> List[ThreadMember]:
        state = self.state
        await state.subscriptions.subscribe_to_threads(self.guild, self)
        future = state.ws.wait_for('thread_member_list_update', lambda d: int(d['thread_id']) == self.id)
        try:
            data: ThreadMemberListUpdateEvent = await asyncio.wait_for(future, timeout=15)
        except asyncio.TimeoutError as exc:
            raise InvalidData('Didn\'t receieve a response from Discord') from exc
        _self = self.guild.get_thread(self.id)
        if _self is not None:
            return _self.members
        else:
            members = [ThreadMember(self, member) for member in data['members']]
            for m in members:
                self._add_member(m)
            return self.members
    async def delete(self) -> None:
        await self.state.http.delete_channel(self.id)
    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        from .message import PartialMessage
        return PartialMessage(channel=self, id=message_id)
    def _add_member(self, member: ThreadMember, /) -> None:
        if member.id != self.state.self_id or self.me is None:
            self._members[member.id] = member
    def _pop_member(self, member_id: int, /) -> Optional[ThreadMember]:
        return self._members.pop(member_id, None)
class ThreadMember(Hashable):
    __slots__ = (
        'id',
        'thread_id',
        'joined_at',
        'flags',
        'state',
        'parent',
    )
    def __init__(self, parent: Thread, data: Union[BaseThreadMemberPayload, ThreadMemberPayload]) -> None:
        self.parent: Thread = parent
        self.thread_id: int = parent.id
        self.state: ConnectionState = parent.state
        self._from_data(data)
    def __repr__(self) -> str:
        return f'<ThreadMember id={self.id} thread_id={self.thread_id} joined_at={self.joined_at!r}>'
    def _from_data(self, data: Union[BaseThreadMemberPayload, ThreadMemberPayload]) -> None:
        state = self.state
        self.id: int
        try:
            self.id = int(data['user_id'])
        except KeyError:
            self.id = state.self_id
        self.joined_at = parse_time(data.get('join_timestamp'))
        self.flags = data.get('flags')
        guild = state._get_guild(self.parent.guild.id)
        if not guild:
            return
        member_data = data.get('member')
        if member_data is not None:
            state._handle_member_update(guild, member_data)
        presence = data.get('presence')
        if presence is not None:
            state._handle_presence_update(guild, presence)
    @property
    def thread(self) -> Thread:
        return self.parent
    @property
    def member(self) -> Optional[Member]:
        return self.parent.guild.get_member(self.id)