from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, List, Literal, Optional, Tuple, Union, overload
from .enums import ButtonStyle, ComponentType, InteractionType, TextStyle, try_enum
from .interactions import _wrapped_interaction
from .partial_emoji import PartialEmoji, _EmojiTag
from .utils import MISSING, _generate_nonce, get_slots
if TYPE_CHECKING:
    from typing_extensions import Self
    from .emoji import Emoji
    from .interactions import Interaction
    from .message import Message
    from .types.components import (
        ActionRow as ActionRowPayload,
        ActionRowChildComponent,
        ButtonComponent as ButtonComponentPayload,
        Component as ComponentPayload,
        MessageChildComponent,
        ModalChildComponent,
        SelectMenu as SelectMenuPayload,
        SelectOption as SelectOptionPayload,
        TextInput as TextInputPayload,
    )
    from .types.interactions import (
        ActionRowInteractionData,
        ButtonInteractionData,
        ComponentInteractionData,
        SelectInteractionData,
        TextInputInteractionData,
    )
    MessageChildComponentType = Union['Button', 'SelectMenu']
    ActionRowChildComponentType = Union[MessageChildComponentType, 'TextInput']
__all__ = (
    'Component',
    'ActionRow',
    'Button',
    'SelectMenu',
    'SelectOption',
    'TextInput',
)
class Component:
    __slots__ = ('message',)
    __repr_info__: ClassVar[Tuple[str, ...]]
    message: Message
    def __repr__(self) -> str:
        attrs = ' '.join(f'{key}={getattr(self, key)!r}' for key in self.__repr_info__)
        return f'<{self.__class__.__name__} {attrs}>'
    @property
    def type(self) -> ComponentType:
        raise NotImplementedError
    @classmethod
    def _raw_construct(cls, **kwargs) -> Self:
        self = cls.__new__(cls)
        for slot in get_slots(cls):
            try:
                value = kwargs[slot]
            except KeyError:
                pass
            else:
                setattr(self, slot, value)
        return self
    def to_dict(self) -> Union[ActionRowInteractionData, ComponentInteractionData]:
        raise NotImplementedError
class ActionRow(Component):
    __slots__ = ('children',)
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__
    def __init__(self, data: ActionRowPayload, message: Message):
        self.message = message
        self.children: List[ActionRowChildComponentType] = []
        for component_data in data.get('components', []):
            component = _component_factory(component_data, message)
            if component is not None:
                self.children.append(component)
    @property
    def type(self) -> Literal[ComponentType.action_row]:
        return ComponentType.action_row
    def to_dict(self) -> ActionRowInteractionData:
        return {
            'type': ComponentType.action_row.value,
            'components': [c.to_dict() for c in self.children],
        }
class Button(Component):
    __slots__ = (
        'style',
        'custom_id',
        'url',
        'disabled',
        'label',
        'emoji',
    )
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__
    def __init__(self, data: ButtonComponentPayload, message: Message):
        self.message = message
        self.style: ButtonStyle = try_enum(ButtonStyle, data['style'])
        self.custom_id: Optional[str] = data.get('custom_id')
        self.url: Optional[str] = data.get('url')
        self.disabled: bool = data.get('disabled', False)
        self.label: Optional[str] = data.get('label')
        self.emoji: Optional[PartialEmoji]
        try:
            self.emoji = PartialEmoji.from_dict(data['emoji'])
        except KeyError:
            self.emoji = None
    @property
    def type(self) -> Literal[ComponentType.button]:
        return ComponentType.button
    def to_dict(self) -> ButtonInteractionData:
        return {
            'component_type': self.type.value,
            'custom_id': self.custom_id or '',
        }
    async def click(self) -> Union[str, Interaction]:
        if self.url:
            return self.url
        message = self.message
        return await _wrapped_interaction(
            message.state,
            _generate_nonce(),
            InteractionType.component,
            None,
            message.channel,
            self.to_dict(),
            message=message,
        )
class SelectMenu(Component):
    __slots__ = (
        'custom_id',
        'placeholder',
        'min_values',
        'max_values',
        'options',
        'disabled',
        'hash',
    )
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__
    def __init__(self, data: SelectMenuPayload, message: Message):
        self.message = message
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self.min_values: int = data.get('min_values', 1)
        self.max_values: int = data.get('max_values', 1)
        self.options: List[SelectOption] = [SelectOption.from_dict(option) for option in data.get('options', [])]
        self.disabled: bool = data.get('disabled', False)
        self.hash: str = data.get('hash', '')
    @property
    def type(self) -> Literal[ComponentType.select]:
        return ComponentType.select
    def to_dict(self, options: Optional[Tuple[SelectOption]] = None) -> SelectInteractionData:
        return {
            'component_type': self.type.value,
            'custom_id': self.custom_id,
            'values': [option.value for option in options] if options else [],
        }
    async def choose(self, *options: SelectOption) -> Interaction:
        message = self.message
        return await _wrapped_interaction(
            message.state,
            _generate_nonce(),
            InteractionType.component,
            None,
            message.channel,
            self.to_dict(options),
            message=message,
        )
class SelectOption:
    __slots__ = (
        'label',
        'value',
        'description',
        'emoji',
        'default',
    )
    def __init__(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        self.label: str = label
        self.value: str = label if value is MISSING else value
        self.description: Optional[str] = description
        if emoji is not None:
            if isinstance(emoji, str):
                emoji = PartialEmoji.from_str(emoji)
            elif isinstance(emoji, _EmojiTag):
                emoji = emoji._to_partial()
            else:
                raise TypeError(f'expected emoji to be str, Emoji, or PartialEmoji not {emoji.__class__}')
        self.emoji: Optional[PartialEmoji] = emoji
        self.default: bool = default
    def __repr__(self) -> str:
        return (
            f'<SelectOption label={self.label!r} value={self.value!r} description={self.description!r} '
            f'emoji={self.emoji!r} default={self.default!r}>'
        )
    def __str__(self) -> str:
        if self.emoji:
            base = f'{self.emoji} {self.label}'
        else:
            base = self.label
        if self.description:
            return f'{base}\n{self.description}'
        return base
    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        try:
            emoji = PartialEmoji.from_dict(data['emoji'])
        except KeyError:
            emoji = None
        return cls(
            label=data['label'],
            value=data['value'],
            description=data.get('description'),
            emoji=emoji,
            default=data.get('default', False),
        )
class TextInput(Component):
    __slots__ = (
        'style',
        'label',
        'custom_id',
        'placeholder',
        '_value',
        '_answer',
        'required',
        'min_length',
        'max_length',
    )
    __repr_info__: ClassVar[Tuple[str, ...]] = (
        'style',
        'label',
        'custom_id',
        'placeholder',
        'required',
        'min_length',
        'max_length',
        'default',
    )
    def __init__(self, data: TextInputPayload, *args) -> None:
        self.style: TextStyle = try_enum(TextStyle, data['style'])
        self.label: str = data['label']
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self._value: Optional[str] = data.get('value')
        self.required: bool = data.get('required', True)
        self.min_length: Optional[int] = data.get('min_length')
        self.max_length: Optional[int] = data.get('max_length')
    @property
    def type(self) -> Literal[ComponentType.text_input]:
        return ComponentType.text_input
    @property
    def value(self) -> Optional[str]:
        return getattr(self, '_answer', self._value)
    @value.setter
    def value(self, value: Optional[str]) -> None:
        length = len(value) if value is not None else 0
        if (self.required or value is not None) and (
            (self.min_length is not None and length < self.min_length)
            or (self.max_length is not None and length > self.max_length)
        ):
            raise ValueError(
                f'value cannot be shorter than {self.min_length or 0} or longer than {self.max_length or "infinity"}'
            )
        self._answer = value
    @property
    def default(self) -> Optional[str]:
        return self._value
    def answer(self, value: Optional[str], /) -> None:
        self.value = value
    def to_dict(self) -> TextInputInteractionData:
        return {
            'type': self.type.value,
            'custom_id': self.custom_id,
            'value': self.value or '',
        }
@overload
def _component_factory(data: ActionRowPayload, message: Message = ...) -> ActionRow:
    ...
@overload
def _component_factory(data: MessageChildComponent, message: Message = ...) -> Optional[MessageChildComponentType]:
    ...
@overload
def _component_factory(data: ModalChildComponent, message: Message = ...) -> Optional[TextInput]:
    ...
@overload
def _component_factory(data: ActionRowChildComponent, message: Message = ...) -> Optional[ActionRowChildComponentType]:
    ...
@overload
def _component_factory(data: ComponentPayload, message: Message = ...) -> Optional[Component]:
    ...
def _component_factory(data: ComponentPayload, message: Message = MISSING) -> Optional[Component]:
    if data['type'] == 1:
        return ActionRow(data, message)
    elif data['type'] == 2:
        return Button(data, message)
    elif data['type'] == 3:
        return SelectMenu(data, message)
    elif data['type'] == 4:
        return TextInput(data, message)