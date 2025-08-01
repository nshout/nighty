from __future__ import annotations
import inspect
import re
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Literal, Optional, Pattern, Set, Tuple, Union
from discord.utils import MISSING, maybe_coroutine, resolve_annotation
from .converter import run_converters
from .errors import BadFlagArgument, MissingFlagArgument, MissingRequiredFlag, TooManyFlags, TooManyArguments
from .view import StringView
__all__ = (
    'Flag',
    'flag',
    'FlagConverter',
)
if TYPE_CHECKING:
    from typing_extensions import Self
    from ._types import BotT
    from .context import Context
    from .parameters import Parameter
@dataclass
class Flag:
    name: str = MISSING
    aliases: List[str] = field(default_factory=list)
    attribute: str = MISSING
    annotation: Any = MISSING
    default: Any = MISSING
    max_args: int = MISSING
    override: bool = MISSING
    cast_to_dict: bool = False
    @property
    def required(self) -> bool:
        return self.default is MISSING
def flag(
    *,
    name: str = MISSING,
    aliases: List[str] = MISSING,
    default: Any = MISSING,
    max_args: int = MISSING,
    override: bool = MISSING,
    converter: Any = MISSING,
) -> Any:
    return Flag(name=name, aliases=aliases, default=default, max_args=max_args, override=override, annotation=converter)
def validate_flag_name(name: str, forbidden: Set[str]) -> None:
    if not name:
        raise ValueError('flag names should not be empty')
    for ch in name:
        if ch.isspace():
            raise ValueError(f'flag name {name!r} cannot have spaces')
        if ch == '\\':
            raise ValueError(f'flag name {name!r} cannot have backslashes')
        if ch in forbidden:
            raise ValueError(f'flag name {name!r} cannot have any of {forbidden!r} within them')
def get_flags(namespace: Dict[str, Any], globals: Dict[str, Any], locals: Dict[str, Any]) -> Dict[str, Flag]:
    annotations = namespace.get('__annotations__', {})
    case_insensitive = namespace['__commands_flag_case_insensitive__']
    flags: Dict[str, Flag] = {}
    cache: Dict[str, Any] = {}
    names: Set[str] = set()
    for name, annotation in annotations.items():
        flag = namespace.pop(name, MISSING)
        if isinstance(flag, Flag):
            if flag.annotation is MISSING:
                flag.annotation = annotation
        else:
            flag = Flag(name=name, annotation=annotation, default=flag)
        flag.attribute = name
        if flag.name is MISSING:
            flag.name = name
        annotation = flag.annotation = resolve_annotation(flag.annotation, globals, locals, cache)
        if flag.default is MISSING and hasattr(annotation, '__commands_is_flag__') and annotation._can_be_constructible():
            flag.default = annotation._construct_default
        if flag.aliases is MISSING:
            flag.aliases = []
        try:
            origin = annotation.__origin__
        except AttributeError:
            if flag.max_args is MISSING:
                flag.max_args = 1
        else:
            if origin is Union:
                if flag.max_args is MISSING:
                    flag.max_args = 1
                if annotation.__args__[-1] is type(None) and flag.default is MISSING:
                    flag.default = None
            elif origin is tuple:
                if flag.max_args is MISSING:
                    flag.max_args = 1
            elif origin is list:
                if flag.max_args is MISSING:
                    flag.max_args = -1
            elif origin is dict:
                flag.cast_to_dict = True
                if flag.max_args is MISSING:
                    flag.max_args = -1
                if flag.override is MISSING:
                    flag.override = True
            elif origin is Literal:
                if flag.max_args is MISSING:
                    flag.max_args = 1
            else:
                raise TypeError(f'Unsupported typing annotation {annotation!r} for {flag.name!r} flag')
        if flag.override is MISSING:
            flag.override = False
        name = flag.name.casefold() if case_insensitive else flag.name
        if name in names:
            raise TypeError(f'{flag.name!r} flag conflicts with previous flag or alias.')
        else:
            names.add(name)
        for alias in flag.aliases:
            alias = alias.casefold() if case_insensitive else alias
            if alias in names:
                raise TypeError(f'{flag.name!r} flag alias {alias!r} conflicts with previous flag or alias.')
            else:
                names.add(alias)
        flags[flag.name] = flag
    return flags
class FlagsMeta(type):
    if TYPE_CHECKING:
        __commands_is_flag__: bool
        __commands_flags__: Dict[str, Flag]
        __commands_flag_aliases__: Dict[str, str]
        __commands_flag_regex__: Pattern[str]
        __commands_flag_case_insensitive__: bool
        __commands_flag_delimiter__: str
        __commands_flag_prefix__: str
    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
        *,
        case_insensitive: bool = MISSING,
        delimiter: str = MISSING,
        prefix: str = MISSING,
    ) -> Self:
        attrs['__commands_is_flag__'] = True
        try:
            global_ns = sys.modules[attrs['__module__']].__dict__
        except KeyError:
            global_ns = {}
        frame = inspect.currentframe()
        try:
            if frame is None:
                local_ns = {}
            else:
                if frame.f_back is None:
                    local_ns = frame.f_locals
                else:
                    local_ns = frame.f_back.f_locals
        finally:
            del frame
        flags: Dict[str, Flag] = {}
        aliases: Dict[str, str] = {}
        for base in reversed(bases):
            if base.__dict__.get('__commands_is_flag__', False):
                flags.update(base.__dict__['__commands_flags__'])
                aliases.update(base.__dict__['__commands_flag_aliases__'])
                if case_insensitive is MISSING:
                    attrs['__commands_flag_case_insensitive__'] = base.__dict__['__commands_flag_case_insensitive__']
                if delimiter is MISSING:
                    attrs['__commands_flag_delimiter__'] = base.__dict__['__commands_flag_delimiter__']
                if prefix is MISSING:
                    attrs['__commands_flag_prefix__'] = base.__dict__['__commands_flag_prefix__']
        if case_insensitive is not MISSING:
            attrs['__commands_flag_case_insensitive__'] = case_insensitive
        if delimiter is not MISSING:
            attrs['__commands_flag_delimiter__'] = delimiter
        if prefix is not MISSING:
            attrs['__commands_flag_prefix__'] = prefix
        case_insensitive = attrs.setdefault('__commands_flag_case_insensitive__', False)
        delimiter = attrs.setdefault('__commands_flag_delimiter__', ':')
        prefix = attrs.setdefault('__commands_flag_prefix__', '')
        for flag_name, flag in get_flags(attrs, global_ns, local_ns).items():
            flags[flag_name] = flag
            aliases.update({alias_name: flag_name for alias_name in flag.aliases})
        forbidden = set(delimiter).union(prefix)
        for flag_name in flags:
            validate_flag_name(flag_name, forbidden)
        for alias_name in aliases:
            validate_flag_name(alias_name, forbidden)
        regex_flags = 0
        if case_insensitive:
            flags = {key.casefold(): value for key, value in flags.items()}
            aliases = {key.casefold(): value.casefold() for key, value in aliases.items()}
            regex_flags = re.IGNORECASE
        keys = [re.escape(k) for k in flags]
        keys.extend(re.escape(a) for a in aliases)
        keys = sorted(keys, key=len, reverse=True)
        joined = '|'.join(keys)
        pattern = re.compile(f'(({re.escape(prefix)})(?P<flag>{joined}){re.escape(delimiter)})', regex_flags)
        attrs['__commands_flag_regex__'] = pattern
        attrs['__commands_flags__'] = flags
        attrs['__commands_flag_aliases__'] = aliases
        return type.__new__(cls, name, bases, attrs)
async def tuple_convert_all(ctx: Context[BotT], argument: str, flag: Flag, converter: Any) -> Tuple[Any, ...]:
    view = StringView(argument)
    results = []
    param: Parameter = ctx.current_parameter
    while not view.eof:
        view.skip_ws()
        if view.eof:
            break
        word = view.get_quoted_word()
        if word is None:
            break
        try:
            converted = await run_converters(ctx, converter, word, param)
        except Exception as e:
            raise BadFlagArgument(flag, word, e) from e
        else:
            results.append(converted)
    return tuple(results)
async def tuple_convert_flag(ctx: Context[BotT], argument: str, flag: Flag, converters: Any) -> Tuple[Any, ...]:
    view = StringView(argument)
    results = []
    param: Parameter = ctx.current_parameter
    for converter in converters:
        view.skip_ws()
        if view.eof:
            break
        word = view.get_quoted_word()
        if word is None:
            break
        try:
            converted = await run_converters(ctx, converter, word, param)
        except Exception as e:
            raise BadFlagArgument(flag, word, e) from e
        else:
            results.append(converted)
    if len(results) != len(converters):
        raise MissingFlagArgument(flag)
    return tuple(results)
async def convert_flag(ctx: Context[BotT], argument: str, flag: Flag, annotation: Any = None) -> Any:
    param: Parameter = ctx.current_parameter
    annotation = annotation or flag.annotation
    try:
        origin = annotation.__origin__
    except AttributeError:
        pass
    else:
        if origin is tuple:
            if annotation.__args__[-1] is Ellipsis:
                return await tuple_convert_all(ctx, argument, flag, annotation.__args__[0])
            else:
                return await tuple_convert_flag(ctx, argument, flag, annotation.__args__)
        elif origin is list:
            annotation = annotation.__args__[0]
            return await convert_flag(ctx, argument, flag, annotation)
        elif origin is Union and type(None) in annotation.__args__:
            annotation = Union[tuple(arg for arg in annotation.__args__ if arg is not type(None))]
            return await run_converters(ctx, annotation, argument, param)
        elif origin is dict:
            return await tuple_convert_flag(ctx, argument, flag, annotation.__args__)
    try:
        return await run_converters(ctx, annotation, argument, param)
    except Exception as e:
        raise BadFlagArgument(flag, argument, e) from e
class FlagConverter(metaclass=FlagsMeta):
    @classmethod
    def get_flags(cls) -> Dict[str, Flag]:
        return cls.__commands_flags__.copy()
    @classmethod
    def _can_be_constructible(cls) -> bool:
        return all(not flag.required for flag in cls.__commands_flags__.values())
    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        for flag in self.__class__.__commands_flags__.values():
            yield (flag.name, getattr(self, flag.attribute))
    @classmethod
    async def _construct_default(cls, ctx: Context[BotT]) -> Self:
        self = cls.__new__(cls)
        flags = cls.__commands_flags__
        for flag in flags.values():
            if callable(flag.default):
                default = await maybe_coroutine(flag.default, ctx)
                setattr(self, flag.attribute, default)
            else:
                setattr(self, flag.attribute, flag.default)
        return self
    def __repr__(self) -> str:
        pairs = ' '.join([f'{flag.attribute}={getattr(self, flag.attribute)!r}' for flag in self.get_flags().values()])
        return f'<{self.__class__.__name__} {pairs}>'
    @classmethod
    def parse_flags(cls, argument: str, *, ignore_extra: bool = True) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        flags = cls.__commands_flags__
        aliases = cls.__commands_flag_aliases__
        last_position = 0
        last_flag: Optional[Flag] = None
        case_insensitive = cls.__commands_flag_case_insensitive__
        for match in cls.__commands_flag_regex__.finditer(argument):
            begin, end = match.span(0)
            key = match.group('flag')
            if case_insensitive:
                key = key.casefold()
            if key in aliases:
                key = aliases[key]
            flag = flags.get(key)
            if last_position and last_flag is not None:
                value = argument[last_position : begin - 1].lstrip()
                if not value:
                    raise MissingFlagArgument(last_flag)
                name = last_flag.name.casefold() if case_insensitive else last_flag.name
                try:
                    values = result[name]
                except KeyError:
                    result[name] = [value]
                else:
                    values.append(value)
            last_position = end
            last_flag = flag
        value = argument[last_position:].strip()
        if last_flag is not None:
            if not value:
                raise MissingFlagArgument(last_flag)
            name = last_flag.name.casefold() if case_insensitive else last_flag.name
            try:
                values = result[name]
            except KeyError:
                result[name] = [value]
            else:
                values.append(value)
        elif value and not ignore_extra:
            raise TooManyArguments(f'Too many arguments passed to {cls.__name__}')
        return result
    @classmethod
    async def convert(cls, ctx: Context[BotT], argument: str) -> Self:
        ignore_extra = True
        if (
            ctx.command is not None
            and ctx.current_parameter is not None
            and ctx.current_parameter.kind == ctx.current_parameter.KEYWORD_ONLY
        ):
            ignore_extra = ctx.command.ignore_extra
        arguments = cls.parse_flags(argument, ignore_extra=ignore_extra)
        flags = cls.__commands_flags__
        self = cls.__new__(cls)
        for name, flag in flags.items():
            try:
                values = arguments[name]
            except KeyError:
                if flag.required:
                    raise MissingRequiredFlag(flag)
                else:
                    if callable(flag.default):
                        default = await maybe_coroutine(flag.default, ctx)
                        setattr(self, flag.attribute, default)
                    else:
                        setattr(self, flag.attribute, flag.default)
                    continue
            if flag.max_args > 0 and len(values) > flag.max_args:
                if flag.override:
                    values = values[-flag.max_args :]
                else:
                    raise TooManyFlags(flag, values)
            if flag.max_args == 1:
                value = await convert_flag(ctx, values[0], flag)
                setattr(self, flag.attribute, value)
                continue
            values = [await convert_flag(ctx, value, flag) for value in values]
            if flag.cast_to_dict:
                values = dict(values)
            setattr(self, flag.attribute, values)
        return self