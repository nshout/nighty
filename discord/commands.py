from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Protocol, Tuple, Type, Union, runtime_checkable
from .enums import ApplicationCommandOptionType, ApplicationCommandType, ChannelType, InteractionType, try_enum
from .interactions import _wrapped_interaction
from .mixins import Hashable
from .permissions import Permissions
from .utils import _generate_nonce, _get_as_snowflake
if TYPE_CHECKING:
    from .abc import Messageable, Snowflake
    from .application import IntegrationApplication
    from .file import _FileBase
    from .guild import Guild
    from .interactions import Interaction
    from .message import Message
    from .state import ConnectionState
    from .types.command import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption,
        ApplicationCommandOptionChoice as OptionChoicePayload,
        SubCommand as SubCommandPayload,
        _ValueApplicationCommandOption as OptionPayload,
    )
    from .types.interactions import (
        ApplicationCommandInteractionData,
        ChatInputCommandInteractionData,
        MessageCommandInteractionData,
        UserCommandInteractionData,
        ApplicationCommandInteractionDataOption as InteractionDataOption,
    )
    from .types.message import PartialAttachment as PartialAttachmentPayload
__all__ = (
    'BaseCommand',
    'UserCommand',
    'MessageCommand',
    'SlashCommand',
    'SubCommand',
    'Option',
    'OptionChoice',
)
@runtime_checkable
class ApplicationCommand(Protocol):
    __slots__ = ()
    if TYPE_CHECKING:
        state: ConnectionState
        _channel: Optional[Messageable]
        _default_member_permissions: Optional[int]
        name: str
        description: str
        version: int
        type: ApplicationCommandType
        dm_permission: bool
        nsfw: bool
        application_id: int
        application: Optional[IntegrationApplication]
        mention: str
        guild_id: Optional[int]
    def __str__(self) -> str:
        return self.name
    async def __call__(
        self,
        data: ApplicationCommandInteractionData,
        files: Optional[List[_FileBase]] = None,
        channel: Optional[Messageable] = None,
    ) -> Interaction:
        channel = channel or self.target_channel
        if channel is None:
            raise TypeError('__call__() missing 1 required argument: \'channel\'')
        return await _wrapped_interaction(
            self.state,
            _generate_nonce(),
            InteractionType.application_command,
            data['name'],
            await channel._get_channel(),
            data,
            files=files,
            application_id=self.application_id,
        )
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_guild(self.guild_id)
    def is_group(self) -> bool:
        return False
    @property
    def target_channel(self) -> Optional[Messageable]:
        return self._channel
    @target_channel.setter
    def target_channel(self, value: Optional[Messageable]) -> None:
        from .abc import Messageable
        if not isinstance(value, Messageable) and value is not None:
            raise TypeError('channel must derive from Messageable')
        self._channel = value
    @property
    def default_member_permissions(self) -> Optional[Permissions]:
        perms = self._default_member_permissions
        return Permissions(perms) if perms is not None else None
class BaseCommand(ApplicationCommand, Hashable):
    __slots__ = (
        'name',
        'description',
        'id',
        'version',
        'application',
        'application_id',
        'dm_permission',
        'nsfw',
        'guild_id',
        '_data',
        'state',
        '_channel',
        '_default_member_permissions',
    )
    if TYPE_CHECKING:
        type: ApplicationCommandType
    def __init__(
        self,
        *,
        state: ConnectionState,
        data: ApplicationCommandPayload,
        channel: Optional[Messageable] = None,
        application: Optional[IntegrationApplication] = None,
        **kwargs,
    ) -> None:
        self.state = state
        self._data = data
        self.application = application
        self.name = data['name']
        self.description = data.get('description', '')
        self._channel = channel
        self.application_id: int = int(data['application_id'])
        self.id: int = int(data['id'])
        self.version = int(data['version'])
        self._default_member_permissions = _get_as_snowflake(data, 'default_member_permissions')
        dm_permission = data.get('dm_permission')
        self.dm_permission = dm_permission if dm_permission is not None else True
        self.nsfw: bool = data.get('nsfw', False)
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r}>'
    @property
    def mention(self) -> str:
        return f'</{self.name}:{self.id}>'
class SlashMixin(ApplicationCommand, Protocol):
    if TYPE_CHECKING:
        _parent: SlashCommand
        options: List[Option]
        children: List[SubCommand]
    async def __call__(
        self,
        options: List[InteractionDataOption],
        files: Optional[List[_FileBase]],
        attachments: List[PartialAttachmentPayload],
        channel: Optional[Messageable] = None,
    ) -> Interaction:
        obj = self._parent
        command = obj._data
        data: ChatInputCommandInteractionData = {
            'application_command': command,
            'attachments': attachments,
            'id': str(obj.id),
            'name': obj.name,
            'options': options,
            'type': ApplicationCommandType.chat_input.value,
            'version': str(obj.version),
        }
        if self.guild_id:
            data['guild_id'] = str(self.guild_id)
        return await super().__call__(data, files, channel)
    def _parse_kwargs(
        self, kwargs: Dict[str, Any]
    ) -> Tuple[List[InteractionDataOption], List[_FileBase], List[PartialAttachmentPayload]]:
        possible_options = {o.name: o for o in self.options}
        kwargs = {k: v for k, v in kwargs.items() if k in possible_options}
        options = []
        files = []
        for k, v in kwargs.items():
            option = possible_options[k]
            type = option.type
            if type in {
                ApplicationCommandOptionType.user,
                ApplicationCommandOptionType.channel,
                ApplicationCommandOptionType.role,
                ApplicationCommandOptionType.mentionable,
            }:
                v = str(v.id)
            elif type is ApplicationCommandOptionType.boolean:
                v = bool(v)
            elif type is ApplicationCommandOptionType.attachment:
                files.append(v)
                v = len(files) - 1
            else:
                v = option._convert(v)
            if type is ApplicationCommandOptionType.string:
                v = str(v)
            elif type is ApplicationCommandOptionType.integer:
                v = int(v)
            elif type is ApplicationCommandOptionType.number:
                v = float(v)
            options.append({'name': k, 'value': v, 'type': type.value})
        attachments = []
        for index, file in enumerate(files):
            attachments.append(file.to_dict(index))
        return options, files, attachments
    def _unwrap_options(self, data: List[ApplicationCommandOption]) -> None:
        options = []
        children = []
        for option in data:
            type = try_enum(ApplicationCommandOptionType, option['type'])
            if type in (
                ApplicationCommandOptionType.sub_command,
                ApplicationCommandOptionType.sub_command_group,
            ):
                children.append(SubCommand(parent=self, data=option))
            else:
                options.append(Option(option))
        self.options = options
        self.children = children
class UserCommand(BaseCommand):
    __slots__ = ('_user',)
    def __init__(self, *, target: Optional[Snowflake] = None, **kwargs):
        super().__init__(**kwargs)
        self._user = target
    async def __call__(self, user: Optional[Snowflake] = None, *, channel: Optional[Messageable] = None):
        user = user or self._user
        if user is None:
            raise TypeError('__call__() missing 1 required positional argument: \'user\'')
        command = self._data
        data: UserCommandInteractionData = {
            'application_command': command,
            'attachments': [],
            'id': str(self.id),
            'name': self.name,
            'options': [],
            'target_id': str(user.id),
            'type': ApplicationCommandType.user.value,
            'version': str(self.version),
        }
        return await super().__call__(data, None, channel)
    @property
    def type(self) -> Literal[ApplicationCommandType.user]:
        return ApplicationCommandType.user
    @property
    def target_user(self) -> Optional[Snowflake]:
        return self._user
    @target_user.setter
    def target_user(self, value: Optional[Snowflake]) -> None:
        from .abc import Snowflake
        if not isinstance(value, Snowflake) and value is not None:
            raise TypeError('user must be Snowflake')
        self._user = value
class MessageCommand(BaseCommand):
    __slots__ = ('_message',)
    def __init__(self, *, target: Optional[Message] = None, **kwargs):
        super().__init__(**kwargs)
        self._message = target
    async def __call__(self, message: Optional[Message] = None, *, channel: Optional[Messageable] = None):
        message = message or self._message
        if message is None:
            raise TypeError('__call__() missing 1 required positional argument: \'message\'')
        command = self._data
        data: MessageCommandInteractionData = {
            'application_command': command,
            'attachments': [],
            'id': str(self.id),
            'name': self.name,
            'options': [],
            'target_id': str(message.id),
            'type': self.type.value,
            'version': str(self.version),
        }
        return await super().__call__(data, None, channel)
    @property
    def type(self) -> Literal[ApplicationCommandType.message]:
        return ApplicationCommandType.message
    @property
    def target_message(self) -> Optional[Message]:
        return self._message
    @target_message.setter
    def target_message(self, value: Optional[Message]) -> None:
        from .message import Message
        if not isinstance(value, Message) and value is not None:
            raise TypeError('message must be Message')
        self._message = value
class SlashCommand(BaseCommand, SlashMixin):
    __slots__ = ('_parent', 'options', 'children')
    def __init__(self, *, data: ApplicationCommandPayload, **kwargs) -> None:
        super().__init__(data=data, **kwargs)
        self._parent = self
        self._unwrap_options(data.get('options', []))
    async def __call__(self, channel: Optional[Messageable] = None, /, **kwargs):
        r
        if self.is_group():
            raise TypeError('Cannot use a group')
        return await super().__call__(*self._parse_kwargs(kwargs), channel)
    def __repr__(self) -> str:
        BASE = f'<SlashCommand id={self.id} name={self.name!r}'
        if self.options:
            BASE += f' options={len(self.options)}'
        if self.children:
            BASE += f' children={len(self.children)}'
        return BASE + '>'
    @property
    def type(self) -> Literal[ApplicationCommandType.chat_input]:
        return ApplicationCommandType.chat_input
    def is_group(self) -> bool:
        return bool(self.children)
class SubCommand(SlashMixin):
    __slots__ = (
        '_parent',
        'state',
        '_type',
        'parent',
        'options',
        'children',
    )
    def __init__(self, *, parent: Union[SlashCommand, SubCommand], data: SubCommandPayload):
        self.name = data['name']
        self.description = data.get('description')
        self.state = parent.state
        self.parent = parent
        self._parent: SlashCommand = getattr(parent, 'parent', parent)
        self._type: Literal[
            ApplicationCommandOptionType.sub_command, ApplicationCommandOptionType.sub_command_group
        ] = try_enum(
            ApplicationCommandOptionType, data['type']
        )
        self._unwrap_options(data.get('options', []))
    def __str__(self) -> str:
        return self.name
    def _walk_parents(self):
        parent = self.parent
        while True:
            if isinstance(parent, SlashCommand):
                break
            else:
                yield parent
                parent = parent.parent
    async def __call__(self, channel: Optional[Messageable] = None, /, **kwargs):
        r
        if self.is_group():
            raise TypeError('Cannot use a group')
        options, files, attachments = self._parse_kwargs(kwargs)
        options: List[InteractionDataOption] = [
            {
                'type': self._type.value,
                'name': self.name,
                'options': options,
            }
        ]
        for parent in self._walk_parents():
            options: List[InteractionDataOption] = [
                {
                    'type': parent._type.value,
                    'name': parent.name,
                    'options': options,
                }
            ]
        return await super().__call__(options, files, attachments, channel)
    def __repr__(self) -> str:
        BASE = f'<SubCommand name={self.name!r}'
        if self.options:
            BASE += f' options={len(self.options)}'
        if self.children:
            BASE += f' children={len(self.children)}'
        return BASE + '>'
    @property
    def type(self) -> Literal[ApplicationCommandType.chat_input]:
        return ApplicationCommandType.chat_input
    @property
    def qualified_name(self) -> str:
        names = [self.name, self.parent.name]
        if isinstance(self.parent, SubCommand):
            names.append(self._parent.name)
        return ' '.join(reversed(names))
    @property
    def mention(self) -> str:
        return f'</{self.qualified_name}:{self._parent.id}>'
    @property
    def _default_member_permissions(self) -> Optional[int]:
        return self._parent._default_member_permissions
    @property
    def application_id(self) -> int:
        return self._parent.application_id
    @property
    def version(self) -> int:
        return self._parent.version
    @property
    def dm_permission(self) -> bool:
        return self._parent.dm_permission
    @property
    def nsfw(self) -> bool:
        return self._parent.nsfw
    @property
    def guild_id(self) -> Optional[int]:
        return self._parent.guild_id
    @property
    def guild(self) -> Optional[Guild]:
        return self._parent.guild
    def is_group(self) -> bool:
        return self._type is ApplicationCommandOptionType.sub_command_group
    @property
    def application(self):
        return self._parent.application
    @property
    def target_channel(self) -> Optional[Messageable]:
        return self._parent.target_channel
    @target_channel.setter
    def target_channel(self, value: Optional[Messageable]) -> None:
        self._parent.target_channel = value
class Option:
    __slots__ = (
        'name',
        'description',
        'type',
        'required',
        'min_value',
        'max_value',
        'choices',
        'channel_types',
        'autocomplete',
    )
    def __init__(self, data: OptionPayload):
        self.name: str = data['name']
        self.description: str = data['description']
        self.type: ApplicationCommandOptionType = try_enum(ApplicationCommandOptionType, data['type'])
        self.required: bool = data.get('required', False)
        self.min_value: Optional[Union[int, float]] = data.get('min_value')
        self.max_value: Optional[Union[int, float]] = data.get('max_value')
        self.choices = [OptionChoice(choice, self.type) for choice in data.get('choices', [])]
        self.channel_types: List[ChannelType] = [try_enum(ChannelType, c) for c in data.get('channel_types', [])]
        self.autocomplete: bool = data.get('autocomplete', False)
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return f'<Option name={self.name!r} type={self.type!r} required={self.required}>'
    def _convert(self, value):
        for choice in self.choices:
            if (new_value := choice._convert(value)) != value:
                return new_value
        return value
class OptionChoice:
    __slots__ = ('name', 'value')
    def __init__(self, data: OptionChoicePayload, type: ApplicationCommandOptionType):
        self.name: str = data['name']
        self.value: Union[str, int, float]
        if type is ApplicationCommandOptionType.string:
            self.value = data['value']
        elif type is ApplicationCommandOptionType.integer:
            self.value = int(data['value'])
        elif type is ApplicationCommandOptionType.number:
            self.value = float(data['value'])
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return f'<OptionChoice name={self.name!r} value={self.value!r}>'
    def _convert(self, value):
        if value == self.name:
            return self.value
        return value
def _command_factory(command_type: int) -> Tuple[ApplicationCommandType, Type[BaseCommand]]:
    value = try_enum(ApplicationCommandType, command_type)
    if value is ApplicationCommandType.chat_input:
        return value, SlashCommand
    elif value is ApplicationCommandType.user:
        return value, UserCommand
    elif value is ApplicationCommandType.message:
        return value, MessageCommand
    else:
        return value, BaseCommand