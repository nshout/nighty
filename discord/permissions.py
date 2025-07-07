from __future__ import annotations
from typing import Callable, Any, ClassVar, Dict, Iterator, Set, TYPE_CHECKING, Tuple, Optional
from .flags import BaseFlags, flag_value, fill_with_flags, alias_flag_value
__all__ = (
    'Permissions',
    'PermissionOverwrite',
)
if TYPE_CHECKING:
    from typing_extensions import Self
class permission_alias(alias_flag_value):
    alias: str
def make_permission_alias(alias: str) -> Callable[[Callable[[Any], int]], permission_alias]:
    def decorator(func: Callable[[Any], int]) -> permission_alias:
        ret = permission_alias(func)
        ret.alias = alias
        return ret
    return decorator
@fill_with_flags()
class Permissions(BaseFlags):
    __slots__ = ()
    def __init__(self, permissions: int = 0, **kwargs: bool):
        if not isinstance(permissions, int):
            raise TypeError(f'Expected int parameter, received {permissions.__class__.__name__} instead.')
        self.value = permissions
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid permission name.')
            setattr(self, key, value)
    def is_subset(self, other: Permissions) -> bool:
        if isinstance(other, Permissions):
            return (self.value & other.value) == self.value
        else:
            raise TypeError(f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}")
    def is_superset(self, other: Permissions) -> bool:
        if isinstance(other, Permissions):
            return (self.value | other.value) == self.value
        else:
            raise TypeError(f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}")
    def is_strict_subset(self, other: Permissions) -> bool:
        return self.is_subset(other) and self != other
    def is_strict_superset(self, other: Permissions) -> bool:
        return self.is_superset(other) and self != other
    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset
    @classmethod
    def none(cls) -> Self:
        return cls(0)
    @classmethod
    def all(cls) -> Self:
        return cls(0b11111111111111111111111111111111111111111111111)
    @classmethod
    def _timeout_mask(cls) -> int:
        p = cls.all()
        p.view_channel = False
        p.read_message_history = False
        return ~p.value
    @classmethod
    def _dm_permissions(cls) -> Self:
        base = cls.text()
        base.read_messages = True
        base.send_tts_messages = False
        base.manage_messages = False
        base.create_private_threads = False
        base.create_public_threads = False
        base.manage_threads = False
        base.send_messages_in_threads = False
        return base
    @classmethod
    def all_channel(cls) -> Self:
        return cls(0b01000111110110110011111101111111111101010001)
    @classmethod
    def general(cls) -> Self:
        return cls(0b10000000000001110000000010000000010010110000)
    @classmethod
    def membership(cls) -> Self:
        return cls(0b10000000000001100000000000000000000000111)
    @classmethod
    def text(cls) -> Self:
        return cls(0b10000000111110010000000000001111111100001000000)
    @classmethod
    def voice(cls) -> Self:
        return cls(0b1001001000000000000011111100000000001100000000)
    @classmethod
    def stage(cls) -> Self:
        return cls(1 << 32)
    @classmethod
    def stage_moderator(cls) -> Self:
        return cls(0b1010000000000000000010000)
    @classmethod
    def elevated(cls) -> Self:
        return cls(0b10000010001110000000000000010000000111110)
    @classmethod
    def advanced(cls) -> Self:
        return cls(1 << 3)
    def update(self, **kwargs: bool) -> None:
        r
        for key, value in kwargs.items():
            if key in self.VALID_FLAGS:
                setattr(self, key, value)
    def handle_overwrite(self, allow: int, deny: int) -> None:
        self.value: int = (self.value & ~deny) | allow
    @flag_value
    def create_instant_invite(self) -> int:
        return 1 << 0
    @flag_value
    def kick_members(self) -> int:
        return 1 << 1
    @flag_value
    def ban_members(self) -> int:
        return 1 << 2
    @flag_value
    def administrator(self) -> int:
        return 1 << 3
    @flag_value
    def manage_channels(self) -> int:
        return 1 << 4
    @flag_value
    def manage_guild(self) -> int:
        return 1 << 5
    @flag_value
    def add_reactions(self) -> int:
        return 1 << 6
    @flag_value
    def view_audit_log(self) -> int:
        return 1 << 7
    @flag_value
    def priority_speaker(self) -> int:
        return 1 << 8
    @flag_value
    def stream(self) -> int:
        return 1 << 9
    @flag_value
    def read_messages(self) -> int:
        return 1 << 10
    @make_permission_alias('read_messages')
    def view_channel(self) -> int:
        return 1 << 10
    @flag_value
    def send_messages(self) -> int:
        return 1 << 11
    @flag_value
    def send_tts_messages(self) -> int:
        return 1 << 12
    @flag_value
    def manage_messages(self) -> int:
        return 1 << 13
    @flag_value
    def embed_links(self) -> int:
        return 1 << 14
    @flag_value
    def attach_files(self) -> int:
        return 1 << 15
    @flag_value
    def read_message_history(self) -> int:
        return 1 << 16
    @flag_value
    def mention_everyone(self) -> int:
        return 1 << 17
    @flag_value
    def external_emojis(self) -> int:
        return 1 << 18
    @make_permission_alias('external_emojis')
    def use_external_emojis(self) -> int:
        return 1 << 18
    @flag_value
    def view_guild_insights(self) -> int:
        return 1 << 19
    @flag_value
    def connect(self) -> int:
        return 1 << 20
    @flag_value
    def speak(self) -> int:
        return 1 << 21
    @flag_value
    def mute_members(self) -> int:
        return 1 << 22
    @flag_value
    def deafen_members(self) -> int:
        return 1 << 23
    @flag_value
    def move_members(self) -> int:
        return 1 << 24
    @flag_value
    def use_voice_activation(self) -> int:
        return 1 << 25
    @flag_value
    def change_nickname(self) -> int:
        return 1 << 26
    @flag_value
    def manage_nicknames(self) -> int:
        return 1 << 27
    @flag_value
    def manage_roles(self) -> int:
        return 1 << 28
    @make_permission_alias('manage_roles')
    def manage_permissions(self) -> int:
        return 1 << 28
    @flag_value
    def manage_webhooks(self) -> int:
        return 1 << 29
    @flag_value
    def manage_expressions(self) -> int:
        return 1 << 30
    @make_permission_alias('manage_expressions')
    def manage_emojis(self) -> int:
        return 1 << 30
    @make_permission_alias('manage_expressions')
    def manage_emojis_and_stickers(self) -> int:
        return 1 << 30
    @flag_value
    def use_application_commands(self) -> int:
        return 1 << 31
    @flag_value
    def request_to_speak(self) -> int:
        return 1 << 32
    @flag_value
    def manage_events(self) -> int:
        return 1 << 33
    @flag_value
    def manage_threads(self) -> int:
        return 1 << 34
    @flag_value
    def create_public_threads(self) -> int:
        return 1 << 35
    @flag_value
    def create_private_threads(self) -> int:
        return 1 << 36
    @flag_value
    def external_stickers(self) -> int:
        return 1 << 37
    @make_permission_alias('external_stickers')
    def use_external_stickers(self) -> int:
        return 1 << 37
    @flag_value
    def send_messages_in_threads(self) -> int:
        return 1 << 38
    @flag_value
    def use_embedded_activities(self) -> int:
        return 1 << 39
    @flag_value
    def moderate_members(self) -> int:
        return 1 << 40
    @flag_value
    def use_soundboard(self) -> int:
        return 1 << 42
    @flag_value
    def create_expressions(self) -> int:
        return 1 << 43
    @flag_value
    def use_external_sounds(self) -> int:
        return 1 << 45
    @flag_value
    def send_voice_messages(self) -> int:
        return 1 << 46
def _augment_from_permissions(cls):
    cls.VALID_NAMES = set(Permissions.VALID_FLAGS)
    aliases = set()
    for name, value in Permissions.__dict__.items():
        if isinstance(value, permission_alias):
            key = value.alias
            aliases.add(name)
        elif isinstance(value, flag_value):
            key = name
        else:
            continue
        def getter(self, x=key):
            return self._values.get(x)
        def setter(self, value, x=key):
            self._set(x, value)
        prop = property(getter, setter)
        setattr(cls, name, prop)
    cls.PURE_FLAGS = cls.VALID_NAMES - aliases
    return cls
@_augment_from_permissions
class PermissionOverwrite:
    r
    __slots__ = ('_values',)
    if TYPE_CHECKING:
        VALID_NAMES: ClassVar[Set[str]]
        PURE_FLAGS: ClassVar[Set[str]]
        create_instant_invite: Optional[bool]
        kick_members: Optional[bool]
        ban_members: Optional[bool]
        administrator: Optional[bool]
        manage_channels: Optional[bool]
        manage_guild: Optional[bool]
        add_reactions: Optional[bool]
        view_audit_log: Optional[bool]
        priority_speaker: Optional[bool]
        stream: Optional[bool]
        read_messages: Optional[bool]
        view_channel: Optional[bool]
        send_messages: Optional[bool]
        send_tts_messages: Optional[bool]
        manage_messages: Optional[bool]
        embed_links: Optional[bool]
        attach_files: Optional[bool]
        read_message_history: Optional[bool]
        mention_everyone: Optional[bool]
        external_emojis: Optional[bool]
        use_external_emojis: Optional[bool]
        view_guild_insights: Optional[bool]
        connect: Optional[bool]
        speak: Optional[bool]
        mute_members: Optional[bool]
        deafen_members: Optional[bool]
        move_members: Optional[bool]
        use_voice_activation: Optional[bool]
        change_nickname: Optional[bool]
        manage_nicknames: Optional[bool]
        manage_roles: Optional[bool]
        manage_permissions: Optional[bool]
        manage_webhooks: Optional[bool]
        manage_expressions: Optional[bool]
        manage_emojis: Optional[bool]
        manage_emojis_and_stickers: Optional[bool]
        use_application_commands: Optional[bool]
        request_to_speak: Optional[bool]
        manage_events: Optional[bool]
        manage_threads: Optional[bool]
        create_public_threads: Optional[bool]
        create_private_threads: Optional[bool]
        send_messages_in_threads: Optional[bool]
        external_stickers: Optional[bool]
        use_external_stickers: Optional[bool]
        use_embedded_activities: Optional[bool]
        moderate_members: Optional[bool]
        use_soundboard: Optional[bool]
        use_external_sounds: Optional[bool]
        send_voice_messages: Optional[bool]
        create_expressions: Optional[bool]
    def __init__(self, **kwargs: Optional[bool]):
        self._values: Dict[str, Optional[bool]] = {}
        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                raise ValueError(f'no permission called {key}.')
            setattr(self, key, value)
    def __eq__(self, other: object) -> bool:
        return isinstance(other, PermissionOverwrite) and self._values == other._values
    def _set(self, key: str, value: Optional[bool]) -> None:
        if value not in (True, None, False):
            raise TypeError(f'Expected bool or NoneType, received {value.__class__.__name__}')
        if value is None:
            self._values.pop(key, None)
        else:
            self._values[key] = value
    def pair(self) -> Tuple[Permissions, Permissions]:
        allow = Permissions.none()
        deny = Permissions.none()
        for key, value in self._values.items():
            if value is True:
                setattr(allow, key, True)
            elif value is False:
                setattr(deny, key, True)
        return allow, deny
    @classmethod
    def from_pair(cls, allow: Permissions, deny: Permissions) -> Self:
        ret = cls()
        for key, value in allow:
            if value is True:
                setattr(ret, key, True)
        for key, value in deny:
            if value is True:
                setattr(ret, key, False)
        return ret
    def is_empty(self) -> bool:
        return len(self._values) == 0
    def update(self, **kwargs: Optional[bool]) -> None:
        r
        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                continue
            setattr(self, key, value)
    def __iter__(self) -> Iterator[Tuple[str, Optional[bool]]]:
        for key in self.PURE_FLAGS:
            yield key, self._values.get(key)