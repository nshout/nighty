from __future__ import annotations
from typing import List, Literal, TypedDict, Union
from typing_extensions import NotRequired
from .emoji import PartialEmoji
ComponentType = Literal[1, 2, 3, 4]
ButtonStyle = Literal[1, 2, 3, 4, 5]
TextStyle = Literal[1, 2]
class MessageActionRow(TypedDict):
    type: Literal[1]
    components: List[MessageChildComponent]
class ModalActionRow(TypedDict):
    type: Literal[1]
    components: List[ModalChildComponent]
ActionRow = Union[MessageActionRow, ModalActionRow]
class ButtonComponent(TypedDict):
    type: Literal[2]
    style: ButtonStyle
    custom_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]
    emoji: NotRequired[PartialEmoji]
    label: NotRequired[str]
class SelectOption(TypedDict):
    label: str
    value: str
    default: bool
    description: NotRequired[str]
    emoji: NotRequired[PartialEmoji]
class SelectMenu(TypedDict):
    type: Literal[3]
    custom_id: str
    options: List[SelectOption]
    placeholder: NotRequired[str]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]
class TextInput(TypedDict):
    type: Literal[4]
    custom_id: str
    style: TextStyle
    label: str
    placeholder: NotRequired[str]
    value: NotRequired[str]
    required: NotRequired[bool]
    min_length: NotRequired[int]
    max_length: NotRequired[int]
MessageChildComponent = Union[ButtonComponent, SelectMenu]
ModalChildComponent = TextInput
ActionRowChildComponent = Union[MessageChildComponent, ModalChildComponent]
Component = Union[ActionRow, ActionRowChildComponent]