from __future__ import annotations
import asyncio
import datetime
import functools
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)
import re
import discord
from ._types import _BaseCommand, CogT
from .cog import Cog
from .context import Context
from .converter import Greedy, run_converters
from .cooldowns import BucketType, Cooldown, CooldownMapping, DynamicCooldownMapping, MaxConcurrency
from .errors import *
from .parameters import Parameter, Signature
if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec, Self
    from ._types import BotT, Check, ContextT, Coro, CoroFunc, Error, Hook, UserCheck
__all__ = (
    'Command',
    'Group',
    'GroupMixin',
    'command',
    'group',
    'has_role',
    'has_permissions',
    'has_any_role',
    'check',
    'check_any',
    'before_invoke',
    'after_invoke',
    'bot_has_role',
    'bot_has_permissions',
    'bot_has_any_role',
    'cooldown',
    'dynamic_cooldown',
    'max_concurrency',
    'dm_only',
    'guild_only',
    'is_owner',
    'is_nsfw',
    'has_guild_permissions',
    'bot_has_guild_permissions',
)
MISSING: Any = discord.utils.MISSING
ARG_NAME_SUBREGEX = r'(?:\\?\*){0,2}(?P<name>\w+)'
ARG_DESCRIPTION_SUBREGEX = r'(?P<description>(?:.|\n)+?(?:\Z|\r?\n(?=[\S\r\n])))'
ARG_TYPE_SUBREGEX = r'(?:.+)'
NUMPY_DOCSTRING_ARG_REGEX = re.compile(
    rf'^{ARG_NAME_SUBREGEX}(?:[ \t]*:)?(?:[ \t]+{ARG_TYPE_SUBREGEX})?[ \t]*\r?\n[ \t]+{ARG_DESCRIPTION_SUBREGEX}',
    re.MULTILINE,
)
T = TypeVar('T')
CommandT = TypeVar('CommandT', bound='Command[Any, ..., Any]')
GroupT = TypeVar('GroupT', bound='Group[Any, ..., Any]')
if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')
def unwrap_function(function: Callable[..., Any], /) -> Callable[..., Any]:
    partial = functools.partial
    while True:
        if hasattr(function, '__wrapped__'):
            function = function.__wrapped__
        elif isinstance(function, partial):
            function = function.func
        else:
            return function
def get_signature_parameters(
    function: Callable[..., Any],
    globalns: Dict[str, Any],
    /,
    *,
    skip_parameters: Optional[int] = None,
) -> Dict[str, Parameter]:
    signature = Signature.from_callable(function)
    params: Dict[str, Parameter] = {}
    cache: Dict[str, Any] = {}
    eval_annotation = discord.utils.evaluate_annotation
    required_params = discord.utils.is_inside_class(function) + 1 if skip_parameters is None else skip_parameters
    if len(signature.parameters) < required_params:
        raise TypeError(f'Command signature requires at least {required_params - 1} parameter(s)')
    iterator = iter(signature.parameters.items())
    for _ in range(0, required_params):
        next(iterator)
    for name, parameter in iterator:
        default = parameter.default
        if isinstance(default, Parameter):
            if default.annotation is not Parameter.empty:
                if default._fallback:
                    if parameter.annotation is Parameter.empty:
                        parameter._annotation = default.annotation
                else:
                    parameter._annotation = default.annotation
            parameter._default = default.default
            parameter._description = default._description
            parameter._displayed_default = default._displayed_default
            parameter._displayed_name = default._displayed_name
        annotation = parameter.annotation
        if annotation is None:
            params[name] = parameter.replace(annotation=type(None))
            continue
        annotation = eval_annotation(annotation, globalns, globalns, cache)
        if annotation is Greedy:
            raise TypeError('Unparameterized Greedy[...] is disallowed in signature.')
        params[name] = parameter.replace(annotation=annotation)
    return params
PARAMETER_HEADING_REGEX = re.compile(r'Parameters?\n---+\n', re.I)
def _fold_text(input: str) -> str:
    def replacer(m: re.Match[str]) -> str:
        if len(m.group()) <= 1:
            return ' '
        return '\n'
    return re.sub(r'\n+', replacer, inspect.cleandoc(input))
def extract_descriptions_from_docstring(function: Callable[..., Any], params: Dict[str, Parameter], /) -> Optional[str]:
    docstring = inspect.getdoc(function)
    if docstring is None:
        return None
    divide = PARAMETER_HEADING_REGEX.split(docstring, 1)
    if len(divide) == 1:
        return docstring
    description, param_docstring = divide
    for match in NUMPY_DOCSTRING_ARG_REGEX.finditer(param_docstring):
        name = match.group('name')
        if name not in params:
            is_display_name = discord.utils.get(params.values(), displayed_name=name)
            if is_display_name:
                name = is_display_name.name
            else:
                continue
        param = params[name]
        if param.description is None:
            param._description = _fold_text(match.group('description'))
    return _fold_text(description.strip())
def wrap_callback(coro: Callable[P, Coro[T]], /) -> Callable[P, Coro[Optional[T]]]:
    @functools.wraps(coro)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            raise
        except asyncio.CancelledError:
            return
        except Exception as exc:
            raise CommandInvokeError(exc) from exc
        return ret
    return wrapped
def hooked_wrapped_callback(
    command: Command[Any, ..., Any], ctx: Context[BotT], coro: Callable[P, Coro[T]], /
) -> Callable[P, Coro[Optional[T]]]:
    @functools.wraps(coro)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            ctx.command_failed = True
            raise
        except asyncio.CancelledError:
            ctx.command_failed = True
            return
        except Exception as exc:
            ctx.command_failed = True
            raise CommandInvokeError(exc) from exc
        finally:
            if command._max_concurrency is not None:
                await command._max_concurrency.release(ctx.message)
            await command.call_after_hooks(ctx)
        return ret
    return wrapped
class _CaseInsensitiveDict(dict):
    def __contains__(self, k):
        return super().__contains__(k.casefold())
    def __delitem__(self, k):
        return super().__delitem__(k.casefold())
    def __getitem__(self, k):
        return super().__getitem__(k.casefold())
    def get(self, k, default=None):
        return super().get(k.casefold(), default)
    def pop(self, k, default=None):
        return super().pop(k.casefold(), default)
    def __setitem__(self, k, v):
        super().__setitem__(k.casefold(), v)
class _AttachmentIterator:
    def __init__(self, data: List[discord.Attachment]):
        self.data: List[discord.Attachment] = data
        self.index: int = 0
    def __iter__(self) -> Self:
        return self
    def __next__(self) -> discord.Attachment:
        try:
            value = self.data[self.index]
        except IndexError:
            raise StopIteration
        else:
            self.index += 1
            return value
    def is_empty(self) -> bool:
        return self.index >= len(self.data)
class Command(_BaseCommand, Generic[CogT, P, T]):
    r
    __original_kwargs__: Dict[str, Any]
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        self = super().__new__(cls)
        self.__original_kwargs__ = kwargs.copy()
        return self
    def __init__(
        self,
        func: Union[
            Callable[Concatenate[CogT, Context[Any], P], Coro[T]],
            Callable[Concatenate[Context[Any], P], Coro[T]],
        ],
        /,
        **kwargs: Any,
    ) -> None:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')
        name = kwargs.get('name') or func.__name__
        if not isinstance(name, str):
            raise TypeError('Name of a command must be a string.')
        self.name: str = name
        self.callback = func
        self.enabled: bool = kwargs.get('enabled', True)
        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = extract_descriptions_from_docstring(func, self.params)
        self.help: Optional[str] = help_doc
        self.brief: Optional[str] = kwargs.get('brief')
        self.usage: Optional[str] = kwargs.get('usage')
        self.rest_is_raw: bool = kwargs.get('rest_is_raw', False)
        self.aliases: Union[List[str], Tuple[str]] = kwargs.get('aliases', [])
        self.extras: Dict[Any, Any] = kwargs.get('extras', {})
        if not isinstance(self.aliases, (list, tuple)):
            raise TypeError("Aliases of a command must be a list or a tuple of strings.")
        self.description: str = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden: bool = kwargs.get('hidden', False)
        try:
            checks = func.__commands_checks__
            checks.reverse()
        except AttributeError:
            checks = kwargs.get('checks', [])
        self.checks: List[UserCheck[Context[Any]]] = checks
        try:
            cooldown = func.__commands_cooldown__
        except AttributeError:
            cooldown = kwargs.get('cooldown')
        if cooldown is None:
            buckets = CooldownMapping(cooldown, BucketType.default)
        elif isinstance(cooldown, CooldownMapping):
            buckets: CooldownMapping[Context[Any]] = cooldown
        else:
            raise TypeError("Cooldown must be an instance of CooldownMapping or None.")
        self._buckets: CooldownMapping[Context[Any]] = buckets
        try:
            max_concurrency = func.__commands_max_concurrency__
        except AttributeError:
            max_concurrency = kwargs.get('max_concurrency')
        self._max_concurrency: Optional[MaxConcurrency] = max_concurrency
        self.require_var_positional: bool = kwargs.get('require_var_positional', False)
        self.ignore_extra: bool = kwargs.get('ignore_extra', True)
        self.cooldown_after_parsing: bool = kwargs.get('cooldown_after_parsing', False)
        self.cog: CogT = None
        parent: Optional[GroupMixin[Any]] = kwargs.get('parent')
        self.parent: Optional[GroupMixin[Any]] = parent if isinstance(parent, _BaseCommand) else None
        self._before_invoke: Optional[Hook] = None
        try:
            before_invoke = func.__before_invoke__
        except AttributeError:
            pass
        else:
            self.before_invoke(before_invoke)
        self._after_invoke: Optional[Hook] = None
        try:
            after_invoke = func.__after_invoke__
        except AttributeError:
            pass
        else:
            self.after_invoke(after_invoke)
    @property
    def callback(
        self,
    ) -> Union[Callable[Concatenate[CogT, Context[Any], P], Coro[T]], Callable[Concatenate[Context[Any], P], Coro[T]],]:
        return self._callback
    @callback.setter
    def callback(
        self,
        function: Union[
            Callable[Concatenate[CogT, Context[Any], P], Coro[T]],
            Callable[Concatenate[Context[Any], P], Coro[T]],
        ],
    ) -> None:
        self._callback = function
        unwrap = unwrap_function(function)
        self.module: str = unwrap.__module__
        try:
            globalns = unwrap.__globals__
        except AttributeError:
            globalns = {}
        self.params: Dict[str, Parameter] = get_signature_parameters(function, globalns)
    def add_check(self, func: UserCheck[Context[Any]], /) -> None:
        self.checks.append(func)
    def remove_check(self, func: UserCheck[Context[Any]], /) -> None:
        try:
            self.checks.remove(func)
        except ValueError:
            pass
    def update(self, **kwargs: Any) -> None:
        cog = self.cog
        self.__init__(self.callback, **dict(self.__original_kwargs__, **kwargs))
        self.cog = cog
    async def __call__(self, context: Context[BotT], /, *args: P.args, **kwargs: P.kwargs) -> T:
        if self.cog is not None:
            return await self.callback(self.cog, context, *args, **kwargs)
        else:
            return await self.callback(context, *args, **kwargs)
    def _ensure_assignment_on_copy(self, other: Self) -> Self:
        other._before_invoke = self._before_invoke
        other._after_invoke = self._after_invoke
        other.extras = self.extras
        if self.checks != other.checks:
            other.checks = self.checks.copy()
        if self._buckets.valid and not other._buckets.valid:
            other._buckets = self._buckets.copy()
        if self._max_concurrency and self._max_concurrency != other._max_concurrency:
            other._max_concurrency = self._max_concurrency.copy()
        try:
            other.on_error = self.on_error
        except AttributeError:
            pass
        return other
    def copy(self) -> Self:
        ret = self.__class__(self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)
    def _update_copy(self, kwargs: Dict[str, Any]) -> Self:
        if kwargs:
            kw = kwargs.copy()
            kw.update(self.__original_kwargs__)
            copy = self.__class__(self.callback, **kw)
            return self._ensure_assignment_on_copy(copy)
        else:
            return self.copy()
    async def dispatch_error(self, ctx: Context[BotT], error: CommandError, /) -> None:
        ctx.command_failed = True
        cog = self.cog
        try:
            coro = self.on_error
        except AttributeError:
            pass
        else:
            injected = wrap_callback(coro)
            if cog is not None:
                await injected(cog, ctx, error)
            else:
                await injected(ctx, error)
        try:
            if cog is not None:
                local = Cog._get_overridden_method(cog.cog_command_error)
                if local is not None:
                    wrapped = wrap_callback(local)
                    await wrapped(ctx, error)
        finally:
            ctx.bot.dispatch('command_error', ctx, error)
    async def transform(self, ctx: Context[BotT], param: Parameter, attachments: _AttachmentIterator, /) -> Any:
        converter = param.converter
        consume_rest_is_special = param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        view = ctx.view
        view.skip_ws()
        if isinstance(converter, Greedy):
            if converter.converter is discord.Attachment:
                return list(attachments)
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                return await self._transform_greedy_pos(ctx, param, param.required, converter.constructed_converter)
            elif param.kind == param.VAR_POSITIONAL:
                return await self._transform_greedy_var_pos(ctx, param, converter.constructed_converter)
            else:
                converter = converter.constructed_converter
        if converter is discord.Attachment:
            try:
                return next(attachments)
            except StopIteration:
                raise MissingRequiredAttachment(param)
        if self._is_typing_optional(param.annotation) and param.annotation.__args__[0] is discord.Attachment:
            if attachments.is_empty():
                return None if param.default is param.empty else param.default
            return next(attachments)
        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise RuntimeError()
            if param.required:
                if self._is_typing_optional(param.annotation):
                    return None
                if hasattr(converter, '__commands_is_flag__') and converter._can_be_constructible():
                    return await converter._construct_default(ctx)
                raise MissingRequiredArgument(param)
            return await param.get_default(ctx)
        previous = view.index
        if consume_rest_is_special:
            ctx.current_argument = argument = view.read_rest().strip()
        else:
            try:
                ctx.current_argument = argument = view.get_quoted_word()
            except ArgumentParsingError as exc:
                if self._is_typing_optional(param.annotation):
                    view.index = previous
                    return None
                else:
                    raise exc
        view.previous = previous
        return await run_converters(ctx, converter, argument, param)
    async def _transform_greedy_pos(self, ctx: Context[BotT], param: Parameter, required: bool, converter: Any) -> Any:
        view = ctx.view
        result = []
        while not view.eof:
            previous = view.index
            view.skip_ws()
            try:
                ctx.current_argument = argument = view.get_quoted_word()
                value = await run_converters(ctx, converter, argument, param)
            except (CommandError, ArgumentParsingError):
                view.index = previous
                break
            else:
                result.append(value)
        if not result and not required:
            return await param.get_default(ctx)
        return result
    async def _transform_greedy_var_pos(self, ctx: Context[BotT], param: Parameter, converter: Any) -> Any:
        view = ctx.view
        previous = view.index
        try:
            ctx.current_argument = argument = view.get_quoted_word()
            value = await run_converters(ctx, converter, argument, param)
        except (CommandError, ArgumentParsingError):
            view.index = previous
            raise RuntimeError() from None
        else:
            return value
    @property
    def clean_params(self) -> Dict[str, Parameter]:
        return self.params.copy()
    @property
    def cooldown(self) -> Optional[Cooldown]:
        return self._buckets._cooldown
    @property
    def full_parent_name(self) -> str:
        entries = []
        command = self
        while command.parent is not None:
            command = command.parent
            entries.append(command.name)
        return ' '.join(reversed(entries))
    @property
    def parents(self) -> List[Group[Any, ..., Any]]:
        entries = []
        command = self
        while command.parent is not None:
            command = command.parent
            entries.append(command)
        return entries
    @property
    def root_parent(self) -> Optional[Group[Any, ..., Any]]:
        if not self.parent:
            return None
        return self.parents[-1]
    @property
    def qualified_name(self) -> str:
        parent = self.full_parent_name
        if parent:
            return parent + ' ' + self.name
        else:
            return self.name
    def __str__(self) -> str:
        return self.qualified_name
    async def _parse_arguments(self, ctx: Context[BotT]) -> None:
        ctx.args = [ctx] if self.cog is None else [self.cog, ctx]
        ctx.kwargs = {}
        args = ctx.args
        kwargs = ctx.kwargs
        attachments = _AttachmentIterator(ctx.message.attachments)
        view = ctx.view
        iterator = iter(self.params.items())
        for name, param in iterator:
            ctx.current_parameter = param
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                transformed = await self.transform(ctx, param, attachments)
                args.append(transformed)
            elif param.kind == param.KEYWORD_ONLY:
                if self.rest_is_raw:
                    ctx.current_argument = argument = view.read_rest()
                    kwargs[name] = await run_converters(ctx, param.converter, argument, param)
                else:
                    kwargs[name] = await self.transform(ctx, param, attachments)
                break
            elif param.kind == param.VAR_POSITIONAL:
                if view.eof and self.require_var_positional:
                    raise MissingRequiredArgument(param)
                while not view.eof:
                    try:
                        transformed = await self.transform(ctx, param, attachments)
                        args.append(transformed)
                    except RuntimeError:
                        break
        if not self.ignore_extra and not view.eof:
            raise TooManyArguments('Too many arguments passed to ' + self.qualified_name)
    async def call_before_hooks(self, ctx: Context[BotT], /) -> None:
        cog = self.cog
        if self._before_invoke is not None:
            instance = getattr(self._before_invoke, '__self__', cog)
            if instance:
                await self._before_invoke(instance, ctx)
            else:
                await self._before_invoke(ctx)
        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_before_invoke)
            if hook is not None:
                await hook(ctx)
        hook = ctx.bot._before_invoke
        if hook is not None:
            await hook(ctx)
    async def call_after_hooks(self, ctx: Context[BotT], /) -> None:
        cog = self.cog
        if self._after_invoke is not None:
            instance = getattr(self._after_invoke, '__self__', cog)
            if instance:
                await self._after_invoke(instance, ctx)
            else:
                await self._after_invoke(ctx)
        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_after_invoke)
            if hook is not None:
                await hook(ctx)
        hook = ctx.bot._after_invoke
        if hook is not None:
            await hook(ctx)
    def _prepare_cooldowns(self, ctx: Context[BotT]) -> None:
        if self._buckets.valid:
            dt = ctx.message.edited_at or ctx.message.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(ctx, current)
            if bucket is not None:
                retry_after = bucket.update_rate_limit(current)
                if retry_after:
                    raise CommandOnCooldown(bucket, retry_after, self._buckets.type)
    async def prepare(self, ctx: Context[BotT], /) -> None:
        ctx.command = self
        if not await self.can_run(ctx):
            raise CheckFailure(f'The check functions for command {self.qualified_name} failed.')
        if self._max_concurrency is not None:
            await self._max_concurrency.acquire(ctx)
        try:
            if self.cooldown_after_parsing:
                await self._parse_arguments(ctx)
                self._prepare_cooldowns(ctx)
            else:
                self._prepare_cooldowns(ctx)
                await self._parse_arguments(ctx)
            await self.call_before_hooks(ctx)
        except:
            if self._max_concurrency is not None:
                await self._max_concurrency.release(ctx)
            raise
    def is_on_cooldown(self, ctx: Context[BotT], /) -> bool:
        if not self._buckets.valid:
            return False
        bucket = self._buckets.get_bucket(ctx)
        if bucket is None:
            return False
        dt = ctx.message.edited_at or ctx.message.created_at
        current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
        return bucket.get_tokens(current) == 0
    def reset_cooldown(self, ctx: Context[BotT], /) -> None:
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx)
            if bucket is not None:
                bucket.reset()
    def get_cooldown_retry_after(self, ctx: Context[BotT], /) -> float:
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx)
            if bucket is None:
                return 0.0
            dt = ctx.message.edited_at or ctx.message.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            return bucket.get_retry_after(current)
        return 0.0
    async def invoke(self, ctx: Context[BotT], /) -> None:
        await self.prepare(ctx)
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(*ctx.args, **ctx.kwargs)
    async def reinvoke(self, ctx: Context[BotT], /, *, call_hooks: bool = False) -> None:
        ctx.command = self
        await self._parse_arguments(ctx)
        if call_hooks:
            await self.call_before_hooks(ctx)
        ctx.invoked_subcommand = None
        try:
            await self.callback(*ctx.args, **ctx.kwargs)
        except:
            ctx.command_failed = True
            raise
        finally:
            if call_hooks:
                await self.call_after_hooks(ctx)
    def error(self, coro: Error[CogT, ContextT], /) -> Error[CogT, ContextT]:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')
        self.on_error: Error[CogT, Any] = coro
        return coro
    def has_error_handler(self) -> bool:
        return hasattr(self, 'on_error')
    def before_invoke(self, coro: Hook[CogT, ContextT], /) -> Hook[CogT, ContextT]:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The pre-invoke hook must be a coroutine.')
        self._before_invoke = coro
        return coro
    def after_invoke(self, coro: Hook[CogT, ContextT], /) -> Hook[CogT, ContextT]:
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The post-invoke hook must be a coroutine.')
        self._after_invoke = coro
        return coro
    @property
    def cog_name(self) -> Optional[str]:
        return type(self.cog).__cog_name__ if self.cog is not None else None
    @property
    def short_doc(self) -> str:
        if self.brief is not None:
            return self.brief
        if self.help is not None:
            return self.help.split('\n', 1)[0]
        return ''
    def _is_typing_optional(self, annotation: Union[T, Optional[T]]) -> bool:
        return getattr(annotation, '__origin__', None) is Union and type(None) in annotation.__args__
    @property
    def signature(self) -> str:
        if self.usage is not None:
            return self.usage
        params = self.clean_params
        if not params:
            return ''
        result = []
        for param in params.values():
            name = param.displayed_name or param.name
            greedy = isinstance(param.converter, Greedy)
            optional = False
            annotation: Any = param.converter.converter if greedy else param.converter
            origin = getattr(annotation, '__origin__', None)
            if not greedy and origin is Union:
                none_cls = type(None)
                union_args = annotation.__args__
                optional = union_args[-1] is none_cls
                if len(union_args) == 2 and optional:
                    annotation = union_args[0]
                    origin = getattr(annotation, '__origin__', None)
            if annotation is discord.Attachment:
                if optional:
                    result.append(f'[{name} (upload a file)]')
                elif greedy:
                    result.append(f'[{name} (upload files)]...')
                else:
                    result.append(f'<{name} (upload a file)>')
                continue
            if origin is Literal:
                name = '|'.join(f'"{v}"' if isinstance(v, str) else str(v) for v in annotation.__args__)
            if not param.required:
                if param.displayed_default:
                    result.append(
                        f'[{name}={param.displayed_default}]' if not greedy else f'[{name}={param.displayed_default}]...'
                    )
                    continue
                else:
                    result.append(f'[{name}]')
            elif param.kind == param.VAR_POSITIONAL:
                if self.require_var_positional:
                    result.append(f'<{name}...>')
                else:
                    result.append(f'[{name}...]')
            elif greedy:
                result.append(f'[{name}]...')
            elif optional:
                result.append(f'[{name}]')
            else:
                result.append(f'<{name}>')
        return ' '.join(result)
    async def can_run(self, ctx: Context[BotT], /) -> bool:
        if not self.enabled:
            raise DisabledCommand(f'{self.name} command is disabled')
        original = ctx.command
        ctx.command = self
        try:
            if not await ctx.bot.can_run(ctx):
                raise CheckFailure(f'The global check functions for command {self.qualified_name} failed.')
            cog = self.cog
            if cog is not None:
                local_check = Cog._get_overridden_method(cog.cog_check)
                if local_check is not None:
                    ret = await discord.utils.maybe_coroutine(local_check, ctx)
                    if not ret:
                        return False
            predicates = self.checks
            if not predicates:
                return True
            return await discord.utils.async_all(predicate(ctx) for predicate in predicates)
        finally:
            ctx.command = original
class GroupMixin(Generic[CogT]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        case_insensitive = kwargs.get('case_insensitive', False)
        self.all_commands: Dict[str, Command[CogT, ..., Any]] = _CaseInsensitiveDict() if case_insensitive else {}
        self.case_insensitive: bool = case_insensitive
        super().__init__(*args, **kwargs)
    @property
    def commands(self) -> Set[Command[CogT, ..., Any]]:
        return set(self.all_commands.values())
    def recursively_remove_all_commands(self) -> None:
        for command in self.all_commands.copy().values():
            if isinstance(command, GroupMixin):
                command.recursively_remove_all_commands()
            self.remove_command(command.name)
    def add_command(self, command: Command[CogT, ..., Any], /) -> None:
        if not isinstance(command, Command):
            raise TypeError('The command passed must be a subclass of Command')
        if isinstance(self, Command):
            command.parent = self
        if command.name in self.all_commands:
            raise CommandRegistrationError(command.name)
        self.all_commands[command.name] = command
        for alias in command.aliases:
            if alias in self.all_commands:
                self.remove_command(command.name)
                raise CommandRegistrationError(alias, alias_conflict=True)
            self.all_commands[alias] = command
    def remove_command(self, name: str, /) -> Optional[Command[CogT, ..., Any]]:
        command = self.all_commands.pop(name, None)
        if command is None:
            return None
        if name in command.aliases:
            return command
        for alias in command.aliases:
            cmd = self.all_commands.pop(alias, None)
            if cmd is not None and cmd != command:
                self.all_commands[alias] = cmd
        return command
    def walk_commands(self) -> Generator[Command[CogT, ..., Any], None, None]:
        for command in self.commands:
            yield command
            if isinstance(command, GroupMixin):
                yield from command.walk_commands()
    def get_command(self, name: str, /) -> Optional[Command[CogT, ..., Any]]:
        if ' ' not in name:
            return self.all_commands.get(name)
        names = name.split()
        if not names:
            return None
        obj = self.all_commands.get(names[0])
        if not isinstance(obj, GroupMixin):
            return obj
        for name in names[1:]:
            try:
                obj = obj.all_commands[name]
            except (AttributeError, KeyError):
                return None
        return obj
    @overload
    def command(
        self: GroupMixin[CogT],
        name: str = ...,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [
            Union[
                Callable[Concatenate[CogT, ContextT, P], Coro[T]],
                Callable[Concatenate[ContextT, P], Coro[T]],
            ]
        ],
        Command[CogT, P, T],
    ]:
        ...
    @overload
    def command(
        self: GroupMixin[CogT],
        name: str = ...,
        cls: Type[CommandT] = ...,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [
            Union[
                Callable[Concatenate[CogT, ContextT, P], Coro[T]],
                Callable[Concatenate[ContextT, P], Coro[T]],
            ]
        ],
        CommandT,
    ]:
        ...
    def command(
        self,
        name: str = MISSING,
        cls: Type[Command[Any, ..., Any]] = MISSING,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = command(name=name, cls=cls, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator
    @overload
    def group(
        self: GroupMixin[CogT],
        name: str = ...,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [
            Union[
                Callable[Concatenate[CogT, ContextT, P], Coro[T]],
                Callable[Concatenate[ContextT, P], Coro[T]],
            ]
        ],
        Group[CogT, P, T],
    ]:
        ...
    @overload
    def group(
        self: GroupMixin[CogT],
        name: str = ...,
        cls: Type[GroupT] = ...,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [
            Union[
                Callable[Concatenate[CogT, ContextT, P], Coro[T]],
                Callable[Concatenate[ContextT, P], Coro[T]],
            ]
        ],
        GroupT,
    ]:
        ...
    def group(
        self,
        name: str = MISSING,
        cls: Type[Group[Any, ..., Any]] = MISSING,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = group(name=name, cls=cls, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator
class Group(GroupMixin[CogT], Command[CogT, P, T]):
    def __init__(self, *args: Any, **attrs: Any) -> None:
        self.invoke_without_command: bool = attrs.pop('invoke_without_command', False)
        super().__init__(*args, **attrs)
    def copy(self) -> Self:
        ret = super().copy()
        for cmd in self.commands:
            ret.add_command(cmd.copy())
        return ret
    async def invoke(self, ctx: Context[BotT], /) -> None:
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)
        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()
        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)
        if early_invoke:
            injected = hooked_wrapped_callback(self, ctx, self.callback)
            await injected(*ctx.args, **ctx.kwargs)
        ctx.invoked_parents.append(ctx.invoked_with)
        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)
    async def reinvoke(self, ctx: Context[BotT], /, *, call_hooks: bool = False) -> None:
        ctx.invoked_subcommand = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            ctx.command = self
            await self._parse_arguments(ctx)
            if call_hooks:
                await self.call_before_hooks(ctx)
        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()
        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)
        if early_invoke:
            try:
                await self.callback(*ctx.args, **ctx.kwargs)
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await self.call_after_hooks(ctx)
        ctx.invoked_parents.append(ctx.invoked_with)
        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.reinvoke(ctx, call_hooks=call_hooks)
        elif not early_invoke:
            view.index = previous
            view.previous = previous
            await super().reinvoke(ctx, call_hooks=call_hooks)
if TYPE_CHECKING:
    class _CommandDecorator:
        @overload
        def __call__(self, func: Callable[Concatenate[CogT, ContextT, P], Coro[T]], /) -> Command[CogT, P, T]:
            ...
        @overload
        def __call__(self, func: Callable[Concatenate[ContextT, P], Coro[T]], /) -> Command[None, P, T]:
            ...
        def __call__(self, func: Callable[..., Coro[T]], /) -> Any:
            ...
    class _GroupDecorator:
        @overload
        def __call__(self, func: Callable[Concatenate[CogT, ContextT, P], Coro[T]], /) -> Group[CogT, P, T]:
            ...
        @overload
        def __call__(self, func: Callable[Concatenate[ContextT, P], Coro[T]], /) -> Group[None, P, T]:
            ...
        def __call__(self, func: Callable[..., Coro[T]], /) -> Any:
            ...
@overload
def command(
    name: str = ...,
    **attrs: Any,
) -> _CommandDecorator:
    ...
@overload
def command(
    name: str = ...,
    cls: Type[CommandT] = ...,
    **attrs: Any,
) -> Callable[
    [
        Union[
            Callable[Concatenate[ContextT, P], Coro[Any]],
            Callable[Concatenate[CogT, ContextT, P], Coro[Any]],
        ]
    ],
    CommandT,
]:
    ...
def command(
    name: str = MISSING,
    cls: Type[Command[Any, ..., Any]] = MISSING,
    **attrs: Any,
) -> Any:
    if cls is MISSING:
        cls = Command
    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)
    return decorator
@overload
def group(
    name: str = ...,
    **attrs: Any,
) -> _GroupDecorator:
    ...
@overload
def group(
    name: str = ...,
    cls: Type[GroupT] = ...,
    **attrs: Any,
) -> Callable[
    [
        Union[
            Callable[Concatenate[CogT, ContextT, P], Coro[Any]],
            Callable[Concatenate[ContextT, P], Coro[Any]],
        ]
    ],
    GroupT,
]:
    ...
def group(
    name: str = MISSING,
    cls: Type[Group[Any, ..., Any]] = MISSING,
    **attrs: Any,
) -> Any:
    if cls is MISSING:
        cls = Group
    return command(name=name, cls=cls, **attrs)
def check(predicate: UserCheck[ContextT], /) -> Check[ContextT]:
    r
    def decorator(func: Union[Command[Any, ..., Any], CoroFunc]) -> Union[Command[Any, ..., Any], CoroFunc]:
        if isinstance(func, Command):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__commands_checks__'):
                func.__commands_checks__ = []
            func.__commands_checks__.append(predicate)
        return func
    if inspect.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:
        @functools.wraps(predicate)
        async def wrapper(ctx: ContextT):
            return predicate(ctx)
        decorator.predicate = wrapper
    return decorator
def check_any(*checks: Check[ContextT]) -> Check[ContextT]:
    r
    unwrapped = []
    for wrapped in checks:
        try:
            pred = wrapped.predicate
        except AttributeError:
            raise TypeError(f'{wrapped!r} must be wrapped by commands.check decorator') from None
        else:
            unwrapped.append(pred)
    async def predicate(ctx: Context[BotT]) -> bool:
        errors = []
        for func in unwrapped:
            try:
                value = await func(ctx)
            except CheckFailure as e:
                errors.append(e)
            else:
                if value:
                    return True
        raise CheckAnyFailure(unwrapped, errors)
    return check(predicate)
def has_role(item: Union[int, str], /) -> Check[Any]:
    def predicate(ctx: Context[BotT]) -> bool:
        if ctx.guild is None:
            raise NoPrivateMessage()
        if isinstance(item, int):
            role = ctx.author.get_role(item)
        else:
            role = discord.utils.get(ctx.author.roles, name=item)
        if role is None:
            raise MissingRole(item)
        return True
    return check(predicate)
def has_any_role(*items: Union[int, str]) -> Callable[[T], T]:
    r
    def predicate(ctx):
        if ctx.guild is None:
            raise NoPrivateMessage()
        if any(
            ctx.author.get_role(item) is not None
            if isinstance(item, int)
            else discord.utils.get(ctx.author.roles, name=item) is not None
            for item in items
        ):
            return True
        raise MissingAnyRole(list(items))
    return check(predicate)
def bot_has_role(item: int, /) -> Callable[[T], T]:
    def predicate(ctx):
        if ctx.guild is None:
            raise NoPrivateMessage()
        if isinstance(item, int):
            role = ctx.me.get_role(item)
        else:
            role = discord.utils.get(ctx.me.roles, name=item)
        if role is None:
            raise BotMissingRole(item)
        return True
    return check(predicate)
def bot_has_any_role(*items: int) -> Callable[[T], T]:
    def predicate(ctx):
        if ctx.guild is None:
            raise NoPrivateMessage()
        me = ctx.me
        if any(
            me.get_role(item) is not None if isinstance(item, int) else discord.utils.get(me.roles, name=item) is not None
            for item in items
        ):
            return True
        raise BotMissingAnyRole(list(items))
    return check(predicate)
def has_permissions(**perms: bool) -> Check[Any]:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")
    def predicate(ctx: Context[BotT]) -> bool:
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        if not missing:
            return True
        raise MissingPermissions(missing)
    return check(predicate)
def bot_has_permissions(**perms: bool) -> Check[Any]:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")
    def predicate(ctx: Context[BotT]) -> bool:
        guild = ctx.guild
        me = guild.me if guild is not None else ctx.bot.user
        permissions = ctx.channel.permissions_for(me)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        if not missing:
            return True
        raise BotMissingPermissions(missing)
    return check(predicate)
def has_guild_permissions(**perms: bool) -> Check[Any]:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")
    def predicate(ctx: Context[BotT]) -> bool:
        if not ctx.guild:
            raise NoPrivateMessage
        permissions = ctx.author.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        if not missing:
            return True
        raise MissingPermissions(missing)
    return check(predicate)
def bot_has_guild_permissions(**perms: bool) -> Check[Any]:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")
    def predicate(ctx: Context[BotT]) -> bool:
        if not ctx.guild:
            raise NoPrivateMessage
        permissions = ctx.me.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        if not missing:
            return True
        raise BotMissingPermissions(missing)
    return check(predicate)
def dm_only() -> Check[Any]:
    def predicate(ctx: Context[BotT]) -> bool:
        if ctx.guild is not None:
            raise PrivateMessageOnly()
        return True
    return check(predicate)
def guild_only() -> Check[Any]:
    def predicate(ctx: Context[BotT]) -> bool:
        if ctx.guild is None:
            raise NoPrivateMessage()
        return True
    return check(predicate)
def is_owner() -> Check[Any]:
    async def predicate(ctx: Context[BotT]) -> bool:
        if not await ctx.bot.is_owner(ctx.author):
            raise NotOwner('You do not own this bot.')
        return True
    return check(predicate)
def is_nsfw() -> Check[Any]:
    def pred(ctx: Context[BotT]) -> bool:
        ch = ctx.channel
        if ctx.guild is None or (
            isinstance(ch, (discord.TextChannel, discord.Thread, discord.VoiceChannel)) and ch.is_nsfw()
        ):
            return True
        raise NSFWChannelRequired(ch)
    return check(pred)
def cooldown(
    rate: int,
    per: float,
    type: Union[BucketType, Callable[[Context[Any]], Any]] = BucketType.default,
) -> Callable[[T], T]:
    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func._buckets = CooldownMapping(Cooldown(rate, per), type)
        else:
            func.__commands_cooldown__ = CooldownMapping(Cooldown(rate, per), type)
        return func
    return decorator
def dynamic_cooldown(
    cooldown: Callable[[Context[Any]], Optional[Cooldown]],
    type: Union[BucketType, Callable[[Context[Any]], Any]],
) -> Callable[[T], T]:
    if not callable(cooldown):
        raise TypeError("A callable must be provided")
    if type is BucketType.default:
        raise ValueError('BucketType.default cannot be used in dynamic cooldowns')
    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func._buckets = DynamicCooldownMapping(cooldown, type)
        else:
            func.__commands_cooldown__ = DynamicCooldownMapping(cooldown, type)
        return func
    return decorator
def max_concurrency(number: int, per: BucketType = BucketType.default, *, wait: bool = False) -> Callable[[T], T]:
    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        value = MaxConcurrency(number, per=per, wait=wait)
        if isinstance(func, Command):
            func._max_concurrency = value
        else:
            func.__commands_max_concurrency__ = value
        return func
    return decorator
def before_invoke(coro: Hook[CogT, ContextT], /) -> Callable[[T], T]:
    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func.before_invoke(coro)
        else:
            func.__before_invoke__ = coro
        return func
    return decorator
def after_invoke(coro: Hook[CogT, ContextT], /) -> Callable[[T], T]:
    def decorator(func: Union[Command, CoroFunc]) -> Union[Command, CoroFunc]:
        if isinstance(func, Command):
            func.after_invoke(coro)
        else:
            func.__after_invoke__ = coro
        return func
    return decorator