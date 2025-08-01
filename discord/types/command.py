from __future__ import annotations
from typing import List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired, Required
from .application import IntegrationApplication
from .channel import ChannelType
from .snowflake import Snowflake
ApplicationCommandType = Literal[1, 2, 3]
ApplicationCommandOptionType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
class _BaseApplicationCommandOption(TypedDict):
    name: str
    description: str
class _SubCommandCommandOption(_BaseApplicationCommandOption):
    type: Literal[1]
    options: List[_ValueApplicationCommandOption]
class _SubCommandGroupCommandOption(_BaseApplicationCommandOption):
    type: Literal[2]
    options: List[_SubCommandCommandOption]
class _BaseValueApplicationCommandOption(_BaseApplicationCommandOption, total=False):
    required: bool
class _StringApplicationCommandOptionChoice(TypedDict):
    name: str
    value: str
class _StringApplicationCommandOption(_BaseApplicationCommandOption):
    type: Literal[3]
    choices: NotRequired[List[_StringApplicationCommandOptionChoice]]
    autocomplete: NotRequired[bool]
class _IntegerApplicationCommandOptionChoice(TypedDict):
    name: str
    value: int
class _IntegerApplicationCommandOption(_BaseApplicationCommandOption, total=False):
    type: Required[Literal[4]]
    min_value: int
    max_value: int
    choices: List[_IntegerApplicationCommandOptionChoice]
    autocomplete: bool
class _BooleanApplicationCommandOption(_BaseValueApplicationCommandOption):
    type: Literal[5]
class _ChannelApplicationCommandOptionChoice(_BaseApplicationCommandOption):
    type: Literal[7]
    channel_types: NotRequired[List[ChannelType]]
class _NonChannelSnowflakeApplicationCommandOptionChoice(_BaseValueApplicationCommandOption):
    type: Literal[6, 8, 9, 11]
_SnowflakeApplicationCommandOptionChoice = Union[
    _ChannelApplicationCommandOptionChoice,
    _NonChannelSnowflakeApplicationCommandOptionChoice,
]
class _NumberApplicationCommandOptionChoice(TypedDict):
    name: str
    value: float
class _NumberApplicationCommandOption(_BaseValueApplicationCommandOption, total=False):
    type: Required[Literal[10]]
    min_value: float
    max_value: float
    choices: List[_NumberApplicationCommandOptionChoice]
    autocomplete: bool
SubCommand = Union[_SubCommandCommandOption, _SubCommandGroupCommandOption]
_ValueApplicationCommandOption = Union[
    _StringApplicationCommandOption,
    _IntegerApplicationCommandOption,
    _BooleanApplicationCommandOption,
    _SnowflakeApplicationCommandOptionChoice,
    _NumberApplicationCommandOption,
]
ApplicationCommandOption = Union[
    _SubCommandGroupCommandOption,
    _SubCommandCommandOption,
    _ValueApplicationCommandOption,
]
ApplicationCommandOptionChoice = Union[
    _StringApplicationCommandOptionChoice,
    _IntegerApplicationCommandOptionChoice,
    _NumberApplicationCommandOptionChoice,
]
class _BaseApplicationCommand(TypedDict):
    id: Snowflake
    application_id: Snowflake
    name: str
    version: Snowflake
class _ChatInputApplicationCommand(_BaseApplicationCommand):
    description: str
    type: Literal[1]
    options: NotRequired[List[ApplicationCommandOption]]
class _BaseContextMenuApplicationCommand(_BaseApplicationCommand):
    description: Literal[""]
class _UserApplicationCommand(_BaseContextMenuApplicationCommand):
    type: Literal[2]
class _MessageApplicationCommand(_BaseContextMenuApplicationCommand):
    type: Literal[3]
GlobalApplicationCommand = Union[
    _ChatInputApplicationCommand,
    _UserApplicationCommand,
    _MessageApplicationCommand,
]
class _GuildChatInputApplicationCommand(_ChatInputApplicationCommand):
    guild_id: Snowflake
class _GuildUserApplicationCommand(_UserApplicationCommand):
    guild_id: Snowflake
class _GuildMessageApplicationCommand(_MessageApplicationCommand):
    guild_id: Snowflake
ChatInputCommand = Union[
    _ChatInputApplicationCommand,
    _GuildChatInputApplicationCommand,
]
UserCommand = Union[
    _UserApplicationCommand,
    _GuildUserApplicationCommand,
]
MessageCommand = Union[
    _MessageApplicationCommand,
    _GuildMessageApplicationCommand,
]
GuildApplicationCommand = Union[
    _GuildChatInputApplicationCommand,
    _GuildUserApplicationCommand,
    _GuildMessageApplicationCommand,
]
ApplicationCommand = Union[
    GlobalApplicationCommand,
    GuildApplicationCommand,
]
ApplicationCommandPermissionType = Literal[1, 2]
class ApplicationCommandPermissions(TypedDict):
    id: Snowflake
    type: ApplicationCommandPermissionType
    permission: bool
class GuildApplicationCommandPermissions(TypedDict):
    id: Snowflake
    application_id: Snowflake
    guild_id: Snowflake
    permissions: List[ApplicationCommandPermissions]
class ApplicationCommandCursor(TypedDict):
    next: Optional[str]
    previous: Optional[str]
    repaired: Optional[str]
class ApplicationCommandIndex(TypedDict):
    application_commands: List[ApplicationCommand]
    applications: Optional[List[IntegrationApplication]]
class GuildApplicationCommandIndex(ApplicationCommandIndex):
    version: Snowflake
class ApplicationCommandSearch(ApplicationCommandIndex):
    cursor: ApplicationCommandCursor