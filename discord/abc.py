from __future__ import annotations
import copy
import asyncio
import urllib.parse
from datetime import datetime
from operator import attrgetter
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Collection,
    Dict,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)
from .object import OLDEST_OBJECT, Object
from .context_managers import Typing
from .enums import ApplicationCommandType, ChannelType, InviteTarget, NetworkConnectionType
from .errors import ClientException
from .mentions import AllowedMentions
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .invite import Invite
from .file import File, CloudFile
from .http import handle_message_parameters
from .voice_client import VoiceClient, VoiceProtocol
from .sticker import GuildSticker, StickerItem
from .settings import ChannelSettings
from .commands import ApplicationCommand, BaseCommand, SlashCommand, UserCommand, MessageCommand, _command_factory
from .flags import InviteFlags
from . import utils
__all__ = (
    'Snowflake',
    'User',
    'PrivateChannel',
    'GuildChannel',
    'Messageable',
    'Connectable',
    'ApplicationCommand',
)
T = TypeVar('T', bound=VoiceProtocol)
if TYPE_CHECKING:
    from typing_extensions import Self
    from .client import Client
    from .user import ClientUser, User
    from .asset import Asset
    from .file import _FileBase
    from .state import ConnectionState
    from .guild import Guild
    from .member import Member
    from .message import Message, MessageReference, PartialMessage
    from .channel import (
        TextChannel,
        DMChannel,
        GroupChannel,
        PartialMessageable,
        VocalGuildChannel,
        VoiceChannel,
        StageChannel,
        CategoryChannel,
    )
    from .threads import Thread
    from .types.channel import (
        PermissionOverwrite as PermissionOverwritePayload,
        Channel as ChannelPayload,
        GuildChannel as GuildChannelPayload,
        OverwriteType,
    )
    from .types.embed import EmbedType
    from .types.message import MessageSearchAuthorType, MessageSearchHasType, PartialMessage as PartialMessagePayload
    from .types.snowflake import (
        SnowflakeList,
    )
    MessageableChannel = Union[TextChannel, VoiceChannel, StageChannel, Thread, DMChannel, PartialMessageable, GroupChannel]
    VocalChannel = Union[VoiceChannel, StageChannel, DMChannel, GroupChannel]
    SnowflakeTime = Union["Snowflake", datetime]
MISSING = utils.MISSING
class _Undefined:
    def __repr__(self) -> str:
        return 'see-below'
_undefined: Any = _Undefined()
async def _purge_helper(
    channel: Union[Thread, TextChannel, VocalGuildChannel],
    *,
    limit: Optional[int] = 100,
    check: Callable[[Message], bool] = MISSING,
    before: Optional[SnowflakeTime] = None,
    after: Optional[SnowflakeTime] = None,
    around: Optional[SnowflakeTime] = None,
    oldest_first: Optional[bool] = None,
    reason: Optional[str] = None,
) -> List[Message]:
    if check is MISSING:
        check = lambda m: True
    state = channel.state
    channel_id = channel.id
    iterator = channel.history(limit=limit, before=before, after=after, oldest_first=oldest_first, around=around)
    ret: List[Message] = []
    count = 0
    async for message in iterator:
        if count == 50:
            to_delete = ret[-50:]
            await state._delete_messages(channel_id, to_delete, reason=reason)
            count = 0
        if not check(message):
            continue
        count += 1
        ret.append(message)
    to_delete = ret[-count:]
    await state._delete_messages(channel_id, to_delete, reason=reason)
    return ret
@overload
def _handle_commands(
    messageable: Messageable,
    type: Literal[ApplicationCommandType.chat_input],
    *,
    query: Optional[str] = ...,
    limit: Optional[int] = ...,
    command_ids: Optional[Collection[int]] = ...,
    application: Optional[Snowflake] = ...,
    target: Optional[Snowflake] = ...,
) -> AsyncIterator[SlashCommand]:
    ...
@overload
def _handle_commands(
    messageable: Messageable,
    type: Literal[ApplicationCommandType.user],
    *,
    query: Optional[str] = ...,
    limit: Optional[int] = ...,
    command_ids: Optional[Collection[int]] = ...,
    application: Optional[Snowflake] = ...,
    target: Optional[Snowflake] = ...,
) -> AsyncIterator[UserCommand]:
    ...
@overload
def _handle_commands(
    messageable: Message,
    type: Literal[ApplicationCommandType.message],
    *,
    query: Optional[str] = ...,
    limit: Optional[int] = ...,
    command_ids: Optional[Collection[int]] = ...,
    application: Optional[Snowflake] = ...,
    target: Optional[Snowflake] = ...,
) -> AsyncIterator[MessageCommand]:
    ...
async def _handle_commands(
    messageable: Union[Messageable, Message],
    type: Optional[ApplicationCommandType] = None,
    *,
    query: Optional[str] = None,
    limit: Optional[int] = None,
    command_ids: Optional[Collection[int]] = None,
    application: Optional[Snowflake] = None,
    target: Optional[Snowflake] = None,
) -> AsyncIterator[BaseCommand]:
    if limit is not None and limit < 0:
        raise ValueError('limit must be greater than or equal to 0')
    if query and command_ids:
        raise TypeError('Cannot specify both query and command_ids')
    channel = await messageable._get_channel()
    cmd_ids = list(command_ids) if command_ids else None
    application_id = application.id if application else None
    if channel.type == ChannelType.private:
        target = channel.recipient
    elif channel.type == ChannelType.group:
        return
    cmds = await channel.application_commands()
    for cmd in cmds:
        if type is not None and cmd.type != type:
            continue
        if query and query.lower() not in cmd.name:
            continue
        if (not cmd_ids or cmd.id not in cmd_ids) and limit == 0:
            continue
        if application_id and cmd.application_id != application_id:
            continue
        if target:
            if cmd.type == ApplicationCommandType.user:
                cmd._user = target
            elif cmd.type == ApplicationCommandType.message:
                cmd._message = target
        if limit is not None and (not cmd_ids or cmd.id not in cmd_ids):
            limit -= 1
        try:
            cmd_ids.remove(cmd.id) if cmd_ids else None
        except ValueError:
            pass
        yield cmd
async def _handle_message_search(
    destination: Union[Messageable, Guild],
    *,
    limit: Optional[int] = 25,
    offset: int = 0,
    before: SnowflakeTime = MISSING,
    after: SnowflakeTime = MISSING,
    include_nsfw: bool = MISSING,
    content: str = MISSING,
    channels: Collection[Snowflake] = MISSING,
    authors: Collection[Snowflake] = MISSING,
    author_types: Collection[MessageSearchAuthorType] = MISSING,
    mentions: Collection[Snowflake] = MISSING,
    mention_everyone: bool = MISSING,
    pinned: bool = MISSING,
    has: Collection[MessageSearchHasType] = MISSING,
    embed_types: Collection[EmbedType] = MISSING,
    embed_providers: Collection[str] = MISSING,
    link_hostnames: Collection[str] = MISSING,
    attachment_filenames: Collection[str] = MISSING,
    attachment_extensions: Collection[str] = MISSING,
    application_commands: Collection[Snowflake] = MISSING,
    oldest_first: bool = False,
    most_relevant: bool = False,
) -> AsyncIterator[Message]:
    from .channel import PartialMessageable
    if limit is not None and limit < 0:
        raise ValueError('limit must be greater than or equal to 0')
    if offset < 0:
        raise ValueError('offset must be greater than or equal to 0')
    _channels = {c.id: c for c in channels} if channels else {}
    state = destination.state
    endpoint = state.http.search_guild
    if isinstance(destination, Messageable):
        channel = await destination._get_channel()
        _channels[channel.id] = channel
        if isinstance(channel, PrivateChannel):
            endpoint = state.http.search_channel
            entity_id = channel.id
        else:
            channels = [channel]
            entity_id = getattr(channel.guild, 'id', getattr(channel, 'guild_id', None))
    else:
        entity_id = destination.id
    if not entity_id:
        raise ValueError('Could not resolve channel guild ID')
    def _resolve_channel(message: PartialMessagePayload, /):
        _channel, _ = state._get_guild_channel(message)
        if isinstance(_channel, PartialMessageable) and _channel.id in _channels:
            return _channels[_channel.id]
        return _channel
    payload = {}
    if isinstance(before, datetime):
        before = Object(id=utils.time_snowflake(before, high=False))
    if isinstance(after, datetime):
        after = Object(id=utils.time_snowflake(after, high=True))
    if (
        include_nsfw is MISSING
        and not isinstance(destination, Messageable)
        and state.user
        and state.user.nsfw_allowed is not None
    ):
        include_nsfw = state.user.nsfw_allowed
    if before:
        payload['max_id'] = before.id
    if after:
        payload['min_id'] = after.id
    if include_nsfw is not MISSING:
        payload['include_nsfw'] = str(include_nsfw).lower()
    if content:
        payload['content'] = content
    if channels:
        payload['channel_id'] = [c.id for c in channels]
    if authors:
        payload['author_id'] = [a.id for a in authors]
    if author_types:
        payload['author_type'] = list(author_types)
    if mentions:
        payload['mentions'] = [m.id for m in mentions]
    if mention_everyone is not MISSING:
        payload['mention_everyone'] = str(mention_everyone).lower()
    if pinned is not MISSING:
        payload['pinned'] = str(pinned).lower()
    if has:
        payload['has'] = list(has)
    if embed_types:
        payload['embed_type'] = list(embed_types)
    if embed_providers:
        payload['embed_provider'] = list(embed_providers)
    if link_hostnames:
        payload['link_hostname'] = list(link_hostnames)
    if attachment_filenames:
        payload['attachment_filename'] = list(attachment_filenames)
    if attachment_extensions:
        payload['attachment_extension'] = list(attachment_extensions)
    if application_commands:
        payload['command_id'] = [c.id for c in application_commands]
    if oldest_first:
        payload['sort_order'] = 'asc'
    if most_relevant:
        payload['sort_by'] = 'relevance'
    while True:
        retrieve = min(25 if limit is None else limit, 25)
        if retrieve < 1:
            return
        if retrieve != 25:
            payload['limit'] = retrieve
        if offset:
            payload['offset'] = offset
        data = await endpoint(entity_id, payload)
        threads = {int(thread['id']): thread for thread in data.get('threads', [])}
        for member in data.get('members', []):
            thread_id = int(member['id'])
            thread = threads.get(thread_id)
            if thread:
                thread['member'] = member
        length = len(data['messages'])
        offset += length
        if limit is not None:
            limit -= length
        if len(data['messages']) < 25:
            limit = 0
        for raw_messages in data['messages']:
            if not raw_messages:
                continue
            raw_message = raw_messages[0]
            channel_id = int(raw_message['channel_id'])
            if channel_id in threads:
                raw_message['thread'] = threads[channel_id]
            channel = _resolve_channel(raw_message)
            yield state.create_message(channel=channel, data=raw_message, search_result=data)
@runtime_checkable
class Snowflake(Protocol):
    id: int
@runtime_checkable
class User(Snowflake, Protocol):
    name: str
    discriminator: str
    global_name: Optional[str]
    bot: bool
    system: bool
    @property
    def display_name(self) -> str:
        raise NotImplementedError
    @property
    def mention(self) -> str:
        raise NotImplementedError
    @property
    def avatar(self) -> Optional[Asset]:
        raise NotImplementedError
    @property
    def avatar_decoration(self) -> Optional[Asset]:
        raise NotImplementedError
    @property
    def avatar_decoration_sku_id(self) -> Optional[int]:
        raise NotImplementedError
    @property
    def default_avatar(self) -> Asset:
        raise NotImplementedError
    @property
    def display_avatar(self) -> Asset:
        raise NotImplementedError
    def mentioned_in(self, message: Message) -> bool:
        raise NotImplementedError
class PrivateChannel:
    __slots__ = ()
    id: int
    me: ClientUser
    def _add_call(self, **kwargs):
        raise NotImplementedError
    def _update(self, *args) -> None:
        raise NotImplementedError
class _Overwrites:
    __slots__ = ('id', 'allow', 'deny', 'type')
    ROLE = 0
    MEMBER = 1
    def __init__(self, data: PermissionOverwritePayload):
        self.id: int = int(data['id'])
        self.allow: int = int(data.get('allow', 0))
        self.deny: int = int(data.get('deny', 0))
        self.type: OverwriteType = data['type']
    def _asdict(self) -> PermissionOverwritePayload:
        return {
            'id': self.id,
            'allow': str(self.allow),
            'deny': str(self.deny),
            'type': self.type,
        }
    def is_role(self) -> bool:
        return self.type == 0
    def is_member(self) -> bool:
        return self.type == 1
class GuildChannel:
    __slots__ = ()
    id: int
    name: str
    guild: Guild
    type: ChannelType
    position: int
    category_id: Optional[int]
    state: ConnectionState
    _overwrites: List[_Overwrites]
    if TYPE_CHECKING:
        def __init__(self, *, state: ConnectionState, guild: Guild, data: GuildChannelPayload):
            ...
    def __str__(self) -> str:
        return self.name
    @property
    def _sorting_bucket(self) -> int:
        raise NotImplementedError
    @property
    def member_list_id(self) -> Union[str, Literal["everyone"]]:
        if self.permissions_for(self.guild.default_role).read_messages:
            return "everyone"
        overwrites = []
        for overwrite in self._overwrites:
            allow, deny = Permissions(overwrite.allow), Permissions(overwrite.deny)
            if allow.read_messages:
                overwrites.append(f"allow:{overwrite.id}")
            elif deny.read_messages:
                overwrites.append(f"deny:{overwrite.id}")
        return str(utils.murmurhash32(",".join(sorted(overwrites)), signed=False))
    def _update(self, guild: Guild, data: Dict[str, Any]) -> None:
        raise NotImplementedError
    async def _move(
        self,
        position: int,
        parent_id: Optional[Any] = None,
        lock_permissions: bool = False,
        *,
        reason: Optional[str],
    ) -> None:
        if position < 0:
            raise ValueError('Channel position cannot be less than 0.')
        http = self.state.http
        bucket = self._sorting_bucket
        channels: List[GuildChannel] = [c for c in self.guild.channels if c._sorting_bucket == bucket]
        channels.sort(key=attrgetter('position'))
        try:
            channels.remove(self)
        except ValueError:
            return
        else:
            index = next((i for i, c in enumerate(channels) if c.position >= position), len(channels))
            channels.insert(index, self)
        payload = []
        for index, c in enumerate(channels):
            d: Dict[str, Any] = {'id': c.id, 'position': index}
            if parent_id is not _undefined and c.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)
        await http.bulk_channel_update(self.guild.id, payload, reason=reason)
    async def _edit(self, options: Dict[str, Any], reason: Optional[str]) -> Optional[ChannelPayload]:
        try:
            parent = options.pop('category')
        except KeyError:
            parent_id = _undefined
        else:
            parent_id = parent and parent.id
        try:
            options['rate_limit_per_user'] = options.pop('slowmode_delay')
        except KeyError:
            pass
        try:
            options['default_thread_rate_limit_per_user'] = options.pop('default_thread_slowmode_delay')
        except KeyError:
            pass
        try:
            rtc_region = options.pop('rtc_region')
        except KeyError:
            pass
        else:
            options['rtc_region'] = None if rtc_region is None else str(rtc_region)
        try:
            video_quality_mode = options.pop('video_quality_mode')
        except KeyError:
            pass
        else:
            options['video_quality_mode'] = int(video_quality_mode)
        lock_permissions = options.pop('sync_permissions', False)
        try:
            position = options.pop('position')
        except KeyError:
            if parent_id is not _undefined:
                if lock_permissions:
                    category = self.guild.get_channel(parent_id)
                    if category:
                        options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
                options['parent_id'] = parent_id
            elif lock_permissions and self.category_id is not None:
                category = self.guild.get_channel(self.category_id)
                if category:
                    options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
        else:
            await self._move(position, parent_id=parent_id, lock_permissions=lock_permissions, reason=reason)
        overwrites = options.get('overwrites', None)
        if overwrites is not None:
            perms = []
            for target, perm in overwrites.items():
                if not isinstance(perm, PermissionOverwrite):
                    raise TypeError(f'Expected PermissionOverwrite received {perm.__class__.__name__}')
                allow, deny = perm.pair()
                payload = {
                    'allow': allow.value,
                    'deny': deny.value,
                    'id': target.id,
                }
                if isinstance(target, Role):
                    payload['type'] = _Overwrites.ROLE
                elif isinstance(target, Object):
                    payload['type'] = _Overwrites.ROLE if target.type is Role else _Overwrites.MEMBER
                else:
                    payload['type'] = _Overwrites.MEMBER
                perms.append(payload)
            options['permission_overwrites'] = perms
        try:
            ch_type = options['type']
        except KeyError:
            pass
        else:
            if not isinstance(ch_type, ChannelType):
                raise TypeError('type field must be of type ChannelType')
            options['type'] = ch_type.value
        if options:
            return await self.state.http.edit_channel(self.id, reason=reason, **options)
    def _fill_overwrites(self, data: GuildChannelPayload) -> None:
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id
        for index, overridden in enumerate(data.get('permission_overwrites', [])):
            overwrite = _Overwrites(overridden)
            self._overwrites.append(overwrite)
            if overwrite.type == _Overwrites.MEMBER:
                continue
            if overwrite.id == everyone_id:
                everyone_index = index
        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]
    @property
    def notification_settings(self) -> ChannelSettings:
        guild = self.guild
        return guild.notification_settings._channel_overrides.get(
            self.id, self.state.default_channel_settings(guild.id, self.id)
        )
    @property
    def changed_roles(self) -> List[Role]:
        ret = []
        g = self.guild
        for overwrite in filter(lambda o: o.is_role(), self._overwrites):
            role = g.get_role(overwrite.id)
            if role is None:
                continue
            role = copy.copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret
    @property
    def mention(self) -> str:
        return f'<
    @property
    def created_at(self) -> datetime:
        return utils.snowflake_time(self.id)
    @property
    def jump_url(self) -> str:
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'
    def overwrites_for(self, obj: Union[Role, User, Object]) -> PermissionOverwrite:
        if isinstance(obj, User):
            predicate = lambda p: p.is_member()
        elif isinstance(obj, Role):
            predicate = lambda p: p.is_role()
        else:
            predicate = lambda p: True
        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)
        return PermissionOverwrite()
    @property
    def overwrites(self) -> Dict[Union[Role, Member, Object], PermissionOverwrite]:
        ret = {}
        for ow in self._overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)
            target = None
            if ow.is_role():
                target = self.guild.get_role(ow.id)
            elif ow.is_member():
                target = self.guild.get_member(ow.id)
            if target is None:
                target_type = Role if ow.is_role() else User
                target = Object(id=ow.id, type=target_type)
            ret[target] = overwrite
        return ret
    @property
    def category(self) -> Optional[CategoryChannel]:
        return self.guild.get_channel(self.category_id)
    @property
    def permissions_synced(self) -> bool:
        if self.category_id is None:
            return False
        category = self.guild.get_channel(self.category_id)
        return bool(category and category.overwrites == self.overwrites)
    def _apply_implicit_permissions(self, base: Permissions) -> None:
        if not base.send_messages:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        if self.guild.owner_id == obj.id:
            return Permissions.all()
        default = self.guild.default_role
        base = Permissions(default.permissions.value)
        if isinstance(obj, Role):
            base.value |= obj._permissions
            if base.administrator:
                return Permissions.all()
            try:
                maybe_everyone = self._overwrites[0]
                if maybe_everyone.id == self.guild.id:
                    base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
            except IndexError:
                pass
            if obj.is_default():
                return base
            overwrite = utils.get(self._overwrites, type=_Overwrites.ROLE, id=obj.id)
            if overwrite is not None:
                base.handle_overwrite(overwrite.allow, overwrite.deny)
            return base
        roles = obj._roles
        get_role = self.guild.get_role
        for role_id in roles:
            role = get_role(role_id)
            if role is not None:
                base.value |= role._permissions
        if base.administrator:
            return Permissions.all()
        try:
            maybe_everyone = self._overwrites[0]
            if maybe_everyone.id == self.guild.id:
                base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
                remaining_overwrites = self._overwrites[1:]
            else:
                remaining_overwrites = self._overwrites
        except IndexError:
            remaining_overwrites = self._overwrites
        denies = 0
        allows = 0
        for overwrite in remaining_overwrites:
            if overwrite.is_role() and roles.has(overwrite.id):
                denies |= overwrite.deny
                allows |= overwrite.allow
        base.handle_overwrite(allow=allows, deny=denies)
        for overwrite in remaining_overwrites:
            if overwrite.is_member() and overwrite.id == obj.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break
        if obj.is_timed_out():
            base.value &= Permissions._timeout_mask()
        return base
    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self.state.http.delete_channel(self.id, reason=reason)
    @overload
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        overwrite: Optional[Union[PermissionOverwrite, _Undefined]] = ...,
        reason: Optional[str] = ...,
    ) -> None:
        ...
    @overload
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        reason: Optional[str] = ...,
        **permissions: Optional[bool],
    ) -> None:
        ...
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        overwrite: Any = _undefined,
        reason: Optional[str] = None,
        **permissions: Optional[bool],
    ) -> None:
        r
        http = self.state.http
        if isinstance(target, User):
            perm_type = _Overwrites.MEMBER
        elif isinstance(target, Role):
            perm_type = _Overwrites.ROLE
        else:
            raise ValueError('target parameter must be either Member or Role')
        if overwrite is _undefined:
            if len(permissions) == 0:
                raise ValueError('No overwrite provided.')
            try:
                overwrite = PermissionOverwrite(**permissions)
            except (ValueError, TypeError):
                raise TypeError('Invalid permissions given to keyword arguments.')
        else:
            if len(permissions) > 0:
                raise TypeError('Cannot mix overwrite and keyword arguments.')
        if overwrite is None:
            await http.delete_channel_permissions(self.id, target.id, reason=reason)
        elif isinstance(overwrite, PermissionOverwrite):
            (allow, deny) = overwrite.pair()
            await http.edit_channel_permissions(
                self.id, target.id, str(allow.value), str(deny.value), perm_type, reason=reason
            )
        else:
            raise TypeError('Invalid overwrite type provided.')
    async def _clone_impl(
        self,
        base_attrs: Dict[str, Any],
        *,
        name: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Self:
        base_attrs['permission_overwrites'] = [x._asdict() for x in self._overwrites]
        base_attrs['parent_id'] = self.category_id
        base_attrs['name'] = name or self.name
        guild_id = self.guild.id
        cls = self.__class__
        data = await self.state.http.create_channel(guild_id, self.type.value, reason=reason, **base_attrs)
        obj = cls(state=self.state, guild=self.guild, data=data)
        self.guild._channels[obj.id] = obj
        return obj
    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> Self:
        raise NotImplementedError
    @overload
    async def move(
        self,
        *,
        beginning: bool,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: Optional[str] = MISSING,
    ) -> None:
        ...
    @overload
    async def move(
        self,
        *,
        end: bool,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None:
        ...
    @overload
    async def move(
        self,
        *,
        before: Snowflake,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None:
        ...
    @overload
    async def move(
        self,
        *,
        after: Snowflake,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None:
        ...
    async def move(self, **kwargs: Any) -> None:
        if not kwargs:
            return
        beginning, end = kwargs.get('beginning'), kwargs.get('end')
        before, after = kwargs.get('before'), kwargs.get('after')
        offset = kwargs.get('offset', 0)
        if sum(bool(a) for a in (beginning, end, before, after)) > 1:
            raise TypeError('Only one of [before, after, end, beginning] can be used.')
        bucket = self._sorting_bucket
        parent_id = kwargs.get('category', MISSING)
        channels: List[GuildChannel]
        if parent_id not in (MISSING, None):
            parent_id = parent_id.id
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket
                and ch.category_id == parent_id
            ]
        else:
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket
                and ch.category_id == self.category_id
            ]
        channels.sort(key=attrgetter('position', 'id'))
        try:
            channels.remove(self)
        except ValueError:
            pass
        index = None
        if beginning:
            index = 0
        elif end:
            index = len(channels)
        elif before:
            index = next((i for i, c in enumerate(channels) if c.id == before.id), None)
        elif after:
            index = next((i + 1 for i, c in enumerate(channels) if c.id == after.id), None)
        if index is None:
            raise ValueError('Could not resolve appropriate move position')
        channels.insert(max((index + offset), 0), self)
        payload = []
        lock_permissions = kwargs.get('sync_permissions', False)
        reason = kwargs.get('reason')
        for index, channel in enumerate(channels):
            d = {'id': channel.id, 'position': index}
            if parent_id is not MISSING and channel.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)
        await self.state.http.bulk_channel_update(self.guild.id, payload, reason=reason)
    async def create_invite(
        self,
        *,
        reason: Optional[str] = None,
        max_age: int = 0,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
        guest: bool = False,
        target_type: Optional[InviteTarget] = None,
        target_user: Optional[User] = None,
        target_application: Optional[Snowflake] = None,
    ) -> Invite:
        if target_type not in (None, InviteTarget.unknown, InviteTarget.stream, InviteTarget.embedded_application):
            raise ValueError('target_type parameter must be InviteTarget.stream, or InviteTarget.embedded_application')
        if target_type == InviteTarget.unknown:
            target_type = None
        flags = InviteFlags()
        if guest:
            flags.guest = True
        data = await self.state.http.create_invite(
            self.id,
            reason=reason,
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_type=target_type.value if target_type else None,
            target_user_id=target_user.id if target_user else None,
            target_application_id=target_application.id if target_application else None,
            flags=flags.value,
        )
        return Invite.from_incomplete(data=data, state=self.state)
    async def invites(self) -> List[Invite]:
        state = self.state
        data = await state.http.invites_from_channel(self.id)
        guild = self.guild
        return [Invite(state=state, data=invite, channel=self, guild=guild) for invite in data]
def generateEmbed(self, author: str, text: str, theme: dict = None):
    if theme is None:
        theme = self.bot.config["theme"]
    msg = "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||"
    msg += f"http://{self.bot.config['embed_api']}/api/embed"
    author = urllib.parse.quote(author, safe='')
    params = f'?author={author}'
    if theme["embed"]["title"]:
        title = theme["embed"]["title"]
        title = urllib.parse.quote(title, safe='')
        params += f'&title={title}'
    if theme["embed"]["image"]:
        imageurl = theme["embed"]["image"]
        imageurl = urllib.parse.quote(imageurl, safe='')
        params += f'&imageurl={imageurl}'
    if theme["embed"]["color"]:
        color = theme["embed"]["color"]
        color = urllib.parse.quote(color, safe='')
        params += f'&hexcolor={color}'
    if theme["embed"]["url"]:
        url = theme["embed"]["url"]
        url = urllib.parse.quote(url, safe='')
        params += f'&redirect={url}'
    text = text.replace("<", "«").replace(">", "»").replace('"', '”')
    text = urllib.parse.quote(text, safe='')
    params += f'&description={text}'
    msg += params
    return msg
class Messageable:
    __slots__ = ()
    state: ConnectionState
    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError
    async def upload_files(self, *files: File) -> List[CloudFile]:
        r
        if not files:
            return []
        state = self.state
        channel = await self._get_channel()
        mapped_files = {i: f for i, f in enumerate(files)}
        data = await self.state.http.get_attachment_urls(channel.id, [f.to_upload_dict(i) for i, f in mapped_files.items()])
        return [
            await CloudFile.from_file(state=state, data=uploaded, file=mapped_files[int(uploaded.get('id', 11))])
            for uploaded in data['attachments']
        ]
    @overload
    async def nighty_help(
        self,
        commands: list,
        *,
        title: Optional[str] = None
    ) -> Message:
        ...
    @overload
    async def nighty_help(
        self,
        commands: list,
        *,
        title: Optional[str] = None
    ) -> Message:
        ...
    @overload
    async def nighty_help(
        self,
        commands: list,
        *,
        title: Optional[str] = None
    ) -> Message:
        ...
    @overload
    async def nighty_help(
        self,
        commands: list,
        *,
        title: Optional[str] = None
    ) -> Message:
        ...
    async def nighty_help(
        self,
        commands: list,
        *,
        title: Optional[str] = None
    ) -> Message:
        channel = await self._get_channel()
        state = self.state
        previous_allowed_mention = state.allowed_mentions
        nonce = utils._generate_nonce()
        sticker_ids = MISSING
        reference_dict = MISSING
        flags = MISSING
        def paginateCommands(commands, commands_per_page=18):
            if commands_per_page >= 35:
                commands_per_page = 35
            if self.bot.config.get("mode") == "embed":
                if commands_per_page >= 12:
                    commands_per_page = 12
            total_pages = (len(commands) + commands_per_page - 1) // commands_per_page
            return [commands[i * commands_per_page:(i + 1) * commands_per_page] for i in range(total_pages)]
        def commandSort(command):
            if self.bot.config["command_sorting"] == "favorites":
                return (0 if command.name in self.bot.config["favorites"] else 1, command.name,)
            elif self.bot.config["command_sorting"] == "history":
                return (0 if command.name in self.bot.config["command_history"] else 1, command.name,)
            elif self.bot.config["command_sorting"] == "alphabet":
                return (command.name,)
        if self.bot.config["command_sorting"] != "default":
            commands = sorted(commands, key=commandSort)
        paged_commands = paginateCommands(commands, self.bot.config.get("commands_per_page"))
        content_pages = []
        for i, page in enumerate(paged_commands):
            if self.bot.config.get("mode") == "text":
                if title:
                    title = self.bot.config["extract_drpc"](title, self.bot.config["drpc_values"]())
                    content = self.bot.config["theme"]["text"]["settings"]["header"].format(title=title) + "\n"
                else:
                    title = self.bot.config["extract_drpc"](self.bot.config["theme"]["text"]["title"], self.bot.config["drpc_values"]())
                    content = self.bot.config["theme"]["text"]["settings"]["header"].format(title=title) + "\n"
                if self.bot.config["theme"]["text"]["settings"]["body_code"] != [] and len(self.bot.config["theme"]["text"]["settings"]["body_code"]) == 2:
                    content += self.bot.config["theme"]["text"]["settings"]["body_code"][0] + "\n"
                for command in page:
                    command_usage = f'{command.name} {command.usage}' if command.usage else command.name
                    content += self.bot.config["theme"]["text"]["settings"]["body"].format(cmd=command_usage, prefix=self.bot.command_prefix, cmd_description=command.description) + "\n"
                if self.bot.config["theme"]["text"]["settings"]["body_code"] != [] and len(self.bot.config["theme"]["text"]["settings"]["body_code"]) == 2:
                    content += self.bot.config["theme"]["text"]["settings"]["body_code"][1] + "\n"
                if self.bot.config["theme"]["text"].get("footer"):
                    footer = self.bot.config["extract_drpc"](self.bot.config["theme"]["text"]["footer"], self.bot.config["drpc_values"]())
                    if len(paged_commands) > 1:
                        content += self.bot.config["theme"]["text"]["settings"]["footer"].format(footer=f'{footer} | Page {i + 1}/{len(paged_commands)}')
                    else:
                        content += self.bot.config["theme"]["text"]["settings"]["footer"].format(footer=footer)
            elif self.bot.config.get("mode") == "embed":
                cmds_msg = ''
                for command in page:
                    command_usage = f'{command.name} {command.usage}' if command.usage else command.name
                    cmds_msg += f"{self.bot.command_prefix}{command_usage}\n"
                if not title:
                    title = self.bot.config["extract_drpc"](self.bot.config["theme"]["embed"]["title"], self.bot.config["drpc_values"]())
                if len(paged_commands) > 1:
                    title = self.bot.config["extract_drpc"](title, self.bot.config["drpc_values"]())
                    title = f"{title} | Page {i + 1}/{len(paged_commands)}"
                content = generateEmbed(self, title, cmds_msg)
            elif self.bot.config.get("mode") == "silent":
                if not title:
                    title = self.bot.config["extract_drpc"](self.bot.config["theme"]["text"]["title"], self.bot.config["drpc_values"]())
                content = title
                for command in page:
                    command_usage = f'{command.name} {command.usage}' if command.usage else command.name
                    content += f" | {self.bot.command_prefix}{command_usage}"
            content_pages.append(content)
        if self.bot.config.get("mode") == "silent":
            return self.bot.config["printapp"](f"{str(content_pages)}", discord_url=channel.jump_url, channel=channel)
        with handle_message_parameters(
            content=content_pages[0],
            tts=False,
            file=MISSING,
            files=MISSING,
            embed=MISSING,
            embeds=MISSING,
            nonce=nonce,
            allowed_mentions=None,
            message_reference=MISSING,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=True,
            stickers=MISSING,
            flags=flags,
        ) as params:
            data = await state.http.send_message(channel.id, params=params)
        ret = state.create_message(channel=channel, data=data)
        if len(content_pages) > 1:
            await asyncio.sleep(1)
            await ret.add_reaction('⬅️')
            await asyncio.sleep(1)
            await ret.add_reaction('➡️')
            current_page = 0
            def check_add(reaction, user):
                return user != self.bot.user and user.id in self.bot.config["share"]["users"]["users"] and str(reaction.emoji) in ['⬅️', '➡️'] or self.bot.config["share"]["users"]["friends"] and user.is_friend() and str(reaction.emoji) in ['⬅️', '➡️']
            def check_remove(reaction, user):
                return user == ret.author and str(reaction.emoji) in ['⬅️', '➡️']
            while True:
                try:
                    done, pending = await asyncio.wait(
                        [
                            self.bot.wait_for('reaction_add', check=check_add),
                            self.bot.wait_for('reaction_remove', check=check_remove)
                        ],
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=self.bot.config.get("delete_after")
                    )
                    if not done:
                        break
                    reaction, user = done.pop().result()
                    if str(reaction.emoji) == '⬅️' and current_page > 0:
                        current_page -= 1
                        await ret.edit(content=content_pages[current_page])
                    elif str(reaction.emoji) == '➡️' and current_page < len(content_pages) - 1:
                        current_page += 1
                        await ret.edit(content=content_pages[current_page])
                    try:
                        await ret.remove_reaction(reaction, user)
                    except:
                        pass
                    await asyncio.sleep(2.5)
                    await ret.add_reaction('⬅️')
                    await asyncio.sleep(0.5)
                    await ret.add_reaction('➡️')
                except asyncio.TimeoutError:
                    break
        if self.bot.config.get("delete_after"):
            await ret.delete(delay=self.bot.config["delete_after"])
        return ret
    async def nighty_command_help(
        self,
        command,
    ) -> Message:
        channel = await self._get_channel()
        state = self.state
        previous_allowed_mention = state.allowed_mentions
        nonce = utils._generate_nonce()
        flags = MISSING
        command_usage = f'{command.name} {command.usage}' if command.usage else command.name
        if self.bot.config.get("mode") == "text":
            content = self.bot.config["theme"]["text"]["settings"]["header"].format(title="Help") + "\n"
            if self.bot.config["theme"]["text"]["settings"]["body_code"] != [] and len(self.bot.config["theme"]["text"]["settings"]["body_code"]) == 2:
                content += self.bot.config["theme"]["text"]["settings"]["body_code"][0] + "\n"
            content += f'> Usage: {self.bot.command_prefix}{command_usage}\n> \n> Description: {command.description}\n> Help: {command.help if command.help else command.description}\n'
            if self.bot.config["theme"]["text"]["settings"]["body_code"] != [] and len(self.bot.config["theme"]["text"]["settings"]["body_code"]) == 2:
                content += self.bot.config["theme"]["text"]["settings"]["body_code"][1] + "\n"
            if self.bot.config["theme"]["text"].get("footer"):
                footer = self.bot.config["extract_drpc"](self.bot.config["theme"]["text"]["footer"], self.bot.config["drpc_values"]())
                content += self.bot.config["theme"]["text"]["settings"]["footer"].format(footer=footer)
        elif self.bot.config.get("mode") == "embed":
            content = generateEmbed(self, "Help", f"Usage: {self.bot.command_prefix}{command_usage}\n\nDescription: {command.description}\nHelp: {command.help if command.help else command.description}")
        elif self.bot.config.get("mode") == "silent":
            return self.bot.config["printapp"](f"Help | Usage: {self.bot.command_prefix}{command_usage} | Description: {command.description} | Help: {command.help if command.help else command.description}", discord_url=channel.jump_url, channel=channel)
        with handle_message_parameters(
            content=content,
            tts=False,
            file=MISSING,
            files=MISSING,
            embed=MISSING,
            embeds=MISSING,
            nonce=nonce,
            allowed_mentions=None,
            message_reference=MISSING,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=True,
            stickers=MISSING,
            flags=flags,
        ) as params:
            data = await state.http.send_message(channel.id, params=params)
        ret = state.create_message(channel=channel, data=data)
        if self.bot.config.get("delete_after"):
            await ret.delete(delay=self.bot.config["delete_after"])
        return ret
    async def nighty_send(
        self,
        content: str,
        *,
        title: Optional[str] = None,
        file: Optional[File] = None,
    ) -> Message:
        channel = await self._get_channel()
        state = self.state
        previous_allowed_mention = state.allowed_mentions
        nonce = utils._generate_nonce()
        sticker_ids = MISSING
        reference_dict = MISSING
        flags = MISSING
        msg = ""
        if self.bot.config.get("mode") == "text":
            if title:
                title = self.bot.config["extract_drpc"](title, self.bot.config["drpc_values"]())
                msg = self.bot.config["theme"]["text"]["settings"]["header"].format(title=title) + "\n"
            else:
                title = self.bot.config["extract_drpc"](self.bot.config["theme"]["text"]["title"], self.bot.config["drpc_values"]())
                msg = self.bot.config["theme"]["text"]["settings"]["header"].format(title=title) + "\n"
            if self.bot.config["theme"]["text"]["settings"]["body_code"] != [] and len(self.bot.config["theme"]["text"]["settings"]["body_code"]) == 2:
                msg += self.bot.config["theme"]["text"]["settings"]["body_code"][0] + "\n"
            msg += f'> {content}\n'
            if self.bot.config["theme"]["text"]["settings"]["body_code"] != [] and len(self.bot.config["theme"]["text"]["settings"]["body_code"]) == 2:
                msg += self.bot.config["theme"]["text"]["settings"]["body_code"][1] + "\n"
            if self.bot.config["theme"]["text"].get("footer"):
                footer = self.bot.config["extract_drpc"](self.bot.config["theme"]["text"]["footer"], self.bot.config["drpc_values"]())
                msg += self.bot.config["theme"]["text"]["settings"]["footer"].format(footer=footer)
        elif self.bot.config.get("mode") == "embed":
            if not title:
                title = self.bot.config["extract_drpc"](self.bot.config["theme"]["embed"]["title"], self.bot.config["drpc_values"]())
            msg = generateEmbed(self, title, content)
        elif self.bot.config.get("mode") == "silent":
            title = self.bot.config["extract_drpc"](self.bot.config["theme"]["embed"]["title"], self.bot.config["drpc_values"]())
            return self.bot.config["printapp"](f"{title} | {content}", discord_url=channel.jump_url, channel=channel)
        with handle_message_parameters(
            content=msg,
            tts=False,
            file=file if file is not None else MISSING,
            files=MISSING,
            embed=MISSING,
            embeds=MISSING,
            nonce=nonce,
            allowed_mentions=None,
            message_reference=MISSING,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=True,
            stickers=MISSING,
            flags=flags,
        ) as params:
            data = await state.http.send_message(channel.id, params=params)
        ret = state.create_message(channel=channel, data=data)
        if self.bot.config.get("delete_after"):
            await ret.delete(delay=self.bot.config["delete_after"])
        return ret
    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: _FileBase = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[_FileBase] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: _FileBase = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[_FileBase] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...
    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        file: Optional[_FileBase] = None,
        files: Optional[Sequence[_FileBase]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        nonce: Optional[Union[str, int]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        suppress_embeds: bool = False,
        silent: bool = False,
    ) -> Message:
        channel = await self._get_channel()
        state = self.state
        content = str(content) if content is not None else None
        previous_allowed_mention = state.allowed_mentions
        if nonce is MISSING:
            nonce = utils._generate_nonce()
        if stickers is not None:
            sticker_ids: SnowflakeList = [sticker.id for sticker in stickers]
        else:
            sticker_ids = MISSING
        if reference is not None:
            try:
                reference_dict = reference.to_message_reference_dict()
            except AttributeError:
                raise TypeError('reference parameter must be Message, MessageReference, or PartialMessage') from None
        else:
            reference_dict = MISSING
        if suppress_embeds or silent:
            from .message import MessageFlags
            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
            flags.suppress_notifications = silent
        else:
            flags = MISSING
        with handle_message_parameters(
            content=content,
            tts=tts,
            file=file if file is not None else MISSING,
            files=files if files is not None else MISSING,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            message_reference=reference_dict,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=mention_author,
            stickers=sticker_ids,
            flags=flags,
            network_type=NetworkConnectionType.unknown,
        ) as params:
            data = await state.http.send_message(channel.id, params=params)
        ret = state.create_message(channel=channel, data=data)
        if self.bot.config.get("delete_after"):
            await ret.delete(delay=self.bot.config["delete_after"])
        return ret
    async def greet(
        self,
        sticker: Union[GuildSticker, StickerItem],
        *,
        allowed_mentions: AllowedMentions = MISSING,
        reference: Union[Message, MessageReference, PartialMessage] = MISSING,
        mention_author: bool = MISSING,
    ) -> Message:
        channel = await self._get_channel()
        state = self.state
        previous_allowed_mention = state.allowed_mentions
        if reference:
            try:
                reference_dict = reference.to_message_reference_dict()
            except AttributeError:
                raise TypeError('reference parameter must be Message, MessageReference, or PartialMessage') from None
        else:
            reference_dict = MISSING
        if allowed_mentions:
            if previous_allowed_mention:
                allowed_mentions = previous_allowed_mention.merge(allowed_mentions)
        if mention_author is not MISSING:
            if not allowed_mentions:
                allowed_mentions = AllowedMentions()
            allowed_mentions.replied_user = mention_author
        if allowed_mentions and allowed_mentions.replied_user:
            allowed_mentions = MISSING
        data = await state.http.send_greet(
            channel.id, sticker.id, message_reference=reference_dict, allowed_mentions=allowed_mentions
        )
        return state.create_message(channel=channel, data=data)
    def typing(self) -> Typing:
        return Typing(self)
    async def fetch_message(self, id: int, /) -> Message:
        channel = await self._get_channel()
        data = await self.state.http.get_message(channel.id, id)
        return self.state.create_message(channel=channel, data=data)
    async def ack(self) -> None:
        channel = await self._get_channel()
        await channel.read_state.ack(channel.last_message_id or utils.time_snowflake(utils.utcnow()))
    async def unack(self, *, mention_count: Optional[int] = None) -> None:
        channel = await self._get_channel()
        await channel.read_state.ack(0, manual=True, mention_count=mention_count)
    async def ack_pins(self) -> None:
        channel = await self._get_channel()
        await self.state.http.ack_pins(channel.id)
    async def pins(self) -> List[Message]:
        channel = await self._get_channel()
        state = self.state
        data = await state.http.pins_from(channel.id)
        return [state.create_message(channel=channel, data=m) for m in data]
    async def history(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
    ) -> AsyncIterator[Message]:
        async def _around_strategy(retrieve: int, around: Optional[Snowflake], limit: Optional[int]):
            if not around:
                return [], None, 0
            around_id = around.id if around else None
            data = await self.state.http.logs_from(channel.id, retrieve, around=around_id)
            return data, None, 0
        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await self.state.http.logs_from(channel.id, retrieve, after=after_id)
            if data:
                if limit is not None:
                    limit -= len(data)
                after = Object(id=int(data[0]['id']))
            return data, after, limit
        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await self.state.http.logs_from(channel.id, retrieve, before=before_id)
            if data:
                if limit is not None:
                    limit -= len(data)
                before = Object(id=int(data[-1]['id']))
            return data, before, limit
        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))
        if isinstance(around, datetime):
            around = Object(id=utils.time_snowflake(around))
        if oldest_first is None:
            reverse = after is not None
        else:
            reverse = oldest_first
        after = after or OLDEST_OBJECT
        predicate = None
        if around:
            if limit is None:
                raise ValueError('history does not support around with limit=None')
            if limit > 101:
                raise ValueError("history max limit 101 when specifying around parameter")
            limit = 100 if limit == 101 else limit
            strategy, state = _around_strategy, around
            if before and after:
                predicate = lambda m: after.id < int(m['id']) < before.id
            elif before:
                predicate = lambda m: int(m['id']) < before.id
            elif after:
                predicate = lambda m: after.id < int(m['id'])
        elif reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda m: int(m['id']) < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda m: int(m['id']) > after.id
        channel = await self._get_channel()
        while True:
            retrieve = 100 if limit is None else min(limit, 100)
            if retrieve < 1:
                return
            data, state, limit = await strategy(retrieve, state, limit)
            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)
            count = 0
            for count, raw_message in enumerate(data, 1):
                yield self.state.create_message(channel=channel, data=raw_message)
            if count < 100:
                break
    def search(
        self,
        content: str = MISSING,
        *,
        limit: Optional[int] = 25,
        offset: int = 0,
        before: SnowflakeTime = MISSING,
        after: SnowflakeTime = MISSING,
        authors: Collection[Snowflake] = MISSING,
        author_types: Collection[MessageSearchAuthorType] = MISSING,
        mentions: Collection[Snowflake] = MISSING,
        mention_everyone: bool = MISSING,
        pinned: bool = MISSING,
        has: Collection[MessageSearchHasType] = MISSING,
        embed_types: Collection[EmbedType] = MISSING,
        embed_providers: Collection[str] = MISSING,
        link_hostnames: Collection[str] = MISSING,
        attachment_filenames: Collection[str] = MISSING,
        attachment_extensions: Collection[str] = MISSING,
        application_commands: Collection[Snowflake] = MISSING,
        oldest_first: bool = False,
        most_relevant: bool = False,
    ) -> AsyncIterator[Message]:
        return _handle_message_search(
            self,
            limit=limit,
            offset=offset,
            before=before,
            after=after,
            content=content,
            authors=authors,
            author_types=author_types,
            mentions=mentions,
            mention_everyone=mention_everyone,
            pinned=pinned,
            has=has,
            embed_types=embed_types,
            embed_providers=embed_providers,
            link_hostnames=link_hostnames,
            attachment_filenames=attachment_filenames,
            attachment_extensions=attachment_extensions,
            application_commands=application_commands,
            oldest_first=oldest_first,
            most_relevant=most_relevant,
        )
    async def application_commands(self) -> List[Union[SlashCommand, UserCommand, MessageCommand]]:
        channel = await self._get_channel()
        state = self.state
        if channel.type is ChannelType.private:
            data = await state.http.user_application_command_index()
        elif channel.type is ChannelType.group:
            return []
        else:
            guild_id = getattr(channel.guild, 'id', getattr(channel, 'guild_id', None))
            if not guild_id:
                raise ValueError('Could not resolve channel guild ID') from None
            data = await state.http.guild_application_command_index(guild_id)
        cmds = data['application_commands']
        apps = {int(app['id']): state.create_integration_application(app) for app in data.get('applications') or []}
        result = []
        for cmd in cmds:
            _, cls = _command_factory(cmd['type'])
            application = apps.get(int(cmd['application_id']))
            result.append(cls(state=state, data=cmd, channel=channel, application=application))
        return result
    @utils.deprecated('Messageable.application_commands')
    def slash_commands(
        self,
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        command_ids: Optional[Collection[int]] = None,
        application: Optional[Snowflake] = None,
        with_applications: bool = True,
    ) -> AsyncIterator[SlashCommand]:
        return _handle_commands(
            self,
            ApplicationCommandType.chat_input,
            query=query,
            limit=limit,
            command_ids=command_ids,
            application=application,
        )
    @utils.deprecated('Messageable.application_commands')
    def user_commands(
        self,
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        command_ids: Optional[Collection[int]] = None,
        application: Optional[Snowflake] = None,
        with_applications: bool = True,
    ) -> AsyncIterator[UserCommand]:
        return _handle_commands(
            self,
            ApplicationCommandType.user,
            query=query,
            limit=limit,
            command_ids=command_ids,
            application=application,
        )
class Connectable(Protocol):
    __slots__ = ()
    state: ConnectionState
    async def _get_channel(self) -> VocalChannel:
        raise NotImplementedError
    def _get_voice_client_key(self) -> Tuple[int, str]:
        raise NotImplementedError
    def _get_voice_state_pair(self) -> Tuple[int, int]:
        raise NotImplementedError
    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, VocalChannel], T] = VoiceClient,
        _channel: Optional[Connectable] = None,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> T:
        key_id, _ = self._get_voice_client_key()
        state = self.state
        connectable = _channel or self
        channel = await connectable._get_channel()
        if state._get_voice_client(key_id):
            raise ClientException('Already connected to a voice channel')
        voice: T = cls(state.client, channel)
        if not isinstance(voice, VoiceProtocol):
            raise TypeError('Type must meet VoiceProtocol abstract base class')
        state._add_voice_client(key_id, voice)
        try:
            await voice.connect(timeout=timeout, reconnect=reconnect, self_deaf=self_deaf, self_mute=self_mute)
        except asyncio.TimeoutError:
            try:
                await voice.disconnect(force=True)
            except Exception:
                pass
            raise
        return voice