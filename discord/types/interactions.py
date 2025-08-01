from __future__ import annotations
from typing import List, Literal, TypedDict, Union
from typing_extensions import NotRequired
from .application import IntegrationApplication
from .command import ApplicationCommand
from .components import ModalActionRow
from .member import Member
from .message import PartialAttachment
from .snowflake import Snowflake
from .user import User
InteractionType = Literal[1, 2, 3, 4, 5]
class _BaseApplicationCommandInteractionDataOption(TypedDict):
    name: str
class _CommandGroupApplicationCommandInteractionDataOption(_BaseApplicationCommandInteractionDataOption):
    type: Literal[1, 2]
    options: List[ApplicationCommandInteractionDataOption]
class _BaseValueApplicationCommandInteractionDataOption(_BaseApplicationCommandInteractionDataOption, total=False):
    focused: bool
class _StringValueApplicationCommandInteractionDataOption(_BaseValueApplicationCommandInteractionDataOption):
    type: Literal[3]
    value: str
class _IntegerValueApplicationCommandInteractionDataOption(_BaseValueApplicationCommandInteractionDataOption):
    type: Literal[4]
    value: int
class _BooleanValueApplicationCommandInteractionDataOption(_BaseValueApplicationCommandInteractionDataOption):
    type: Literal[5]
    value: bool
class _SnowflakeValueApplicationCommandInteractionDataOption(_BaseValueApplicationCommandInteractionDataOption):
    type: Literal[6, 7, 8, 9, 11]
    value: Snowflake
class _NumberValueApplicationCommandInteractionDataOption(_BaseValueApplicationCommandInteractionDataOption):
    type: Literal[10]
    value: float
_ValueApplicationCommandInteractionDataOption = Union[
    _StringValueApplicationCommandInteractionDataOption,
    _IntegerValueApplicationCommandInteractionDataOption,
    _BooleanValueApplicationCommandInteractionDataOption,
    _SnowflakeValueApplicationCommandInteractionDataOption,
    _NumberValueApplicationCommandInteractionDataOption,
]
ApplicationCommandInteractionDataOption = Union[
    _CommandGroupApplicationCommandInteractionDataOption,
    _ValueApplicationCommandInteractionDataOption,
]
class _BaseApplicationCommandInteractionData(TypedDict):
    id: Snowflake
    name: str
    version: Snowflake
    guild_id: NotRequired[Snowflake]
    application_command: ApplicationCommand
    attachments: List[PartialAttachment]
    options: List[ApplicationCommandInteractionDataOption]
class ChatInputCommandInteractionData(_BaseApplicationCommandInteractionData, total=False):
    type: Literal[1]
class _BaseNonChatInputApplicationCommandInteractionData(_BaseApplicationCommandInteractionData):
    target_id: Snowflake
class UserCommandInteractionData(_BaseNonChatInputApplicationCommandInteractionData):
    type: Literal[2]
class MessageCommandInteractionData(_BaseNonChatInputApplicationCommandInteractionData):
    type: Literal[3]
ApplicationCommandInteractionData = Union[
    ChatInputCommandInteractionData,
    UserCommandInteractionData,
    MessageCommandInteractionData,
]
class _BaseMessageComponentInteractionData(TypedDict):
    custom_id: str
class ButtonInteractionData(_BaseMessageComponentInteractionData):
    component_type: Literal[2]
class SelectInteractionData(_BaseMessageComponentInteractionData):
    component_type: Literal[3]
    values: List[str]
MessageComponentInteractionData = Union[ButtonInteractionData, SelectInteractionData]
class TextInputInteractionData(TypedDict):
    type: Literal[4]
    custom_id: str
    value: str
ModalSubmitComponentInteractionData = TextInputInteractionData
class MessageActionRowData(TypedDict):
    type: Literal[1]
    components: List[MessageComponentInteractionData]
class ModalSubmitActionRowData(TypedDict):
    type: Literal[1]
    components: List[ModalSubmitComponentInteractionData]
class ModalSubmitInteractionData(TypedDict):
    id: Snowflake
    custom_id: str
    components: List[ModalSubmitComponentInteractionData]
ActionRowInteractionData = Union[MessageActionRowData, ModalSubmitActionRowData]
ComponentInteractionData = Union[MessageComponentInteractionData, ModalSubmitComponentInteractionData]
InteractionData = Union[
    ApplicationCommandInteractionData,
    MessageComponentInteractionData,
    ModalSubmitInteractionData,
]
class MessageInteraction(TypedDict):
    id: Snowflake
    type: InteractionType
    name: str
    user: User
    member: NotRequired[Member]
class Modal(TypedDict):
    id: int
    nonce: NotRequired[Snowflake]
    channel_id: Snowflake
    title: str
    custom_id: str
    application: IntegrationApplication
    components: List[ModalActionRow]