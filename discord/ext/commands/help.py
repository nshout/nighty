from __future__ import annotations
import itertools
import copy
import functools
import re
from typing import (
    TYPE_CHECKING,
    Optional,
    Generator,
    List,
    TypeVar,
    Callable,
    Any,
    Dict,
    Tuple,
    Iterable,
    Sequence,
    Mapping,
)
import discord.utils
from discord.utils import MISSING
from .core import Group, Command, get_signature_parameters
from .errors import CommandError
if TYPE_CHECKING:
    from typing_extensions import Self
    import discord.abc
    from .bot import BotBase
    from .context import Context
    from .cog import Cog
    from .parameters import Parameter
    from ._types import (
        UserCheck,
        BotT,
        _Bot,
    )
__all__ = (
    'Paginator',
    'HelpCommand',
    'DefaultHelpCommand',
    'MinimalHelpCommand',
)
FuncT = TypeVar('FuncT', bound=Callable[..., Any])
class Paginator:
    def __init__(
        self, prefix: Optional[str] = '```', suffix: Optional[str] = '```', max_size: int = 2000, linesep: str = '\n'
    ) -> None:
        self.prefix: Optional[str] = prefix
        self.suffix: Optional[str] = suffix
        self.max_size: int = max_size
        self.linesep: str = linesep
        self.clear()
    def clear(self) -> None:
        if self.prefix is not None:
            self._current_page: List[str] = [self.prefix]
            self._count: int = len(self.prefix) + self._linesep_len
        else:
            self._current_page = []
            self._count = 0
        self._pages: List[str] = []
    @property
    def _prefix_len(self) -> int:
        return len(self.prefix) if self.prefix else 0
    @property
    def _suffix_len(self) -> int:
        return len(self.suffix) if self.suffix else 0
    @property
    def _linesep_len(self) -> int:
        return len(self.linesep)
    def add_line(self, line: str = '', *, empty: bool = False) -> None:
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2 * self._linesep_len
        if len(line) > max_page_size:
            raise RuntimeError(f'Line exceeds maximum page size {max_page_size}')
        if self._count + len(line) + self._linesep_len > self.max_size - self._suffix_len:
            self.close_page()
        self._count += len(line) + self._linesep_len
        self._current_page.append(line)
        if empty:
            self._current_page.append('')
            self._count += self._linesep_len
    def close_page(self) -> None:
        if self.suffix is not None:
            self._current_page.append(self.suffix)
        self._pages.append(self.linesep.join(self._current_page))
        if self.prefix is not None:
            self._current_page = [self.prefix]
            self._count = len(self.prefix) + self._linesep_len
        else:
            self._current_page = []
            self._count = 0
    def __len__(self) -> int:
        total = sum(len(p) for p in self._pages)
        return total + self._count
    @property
    def pages(self) -> List[str]:
        if len(self._current_page) > (0 if self.prefix is None else 1):
            self.close_page()
        return self._pages
    def __repr__(self) -> str:
        fmt = '<Paginator prefix: {0.prefix!r} suffix: {0.suffix!r} linesep: {0.linesep!r} max_size: {0.max_size} count: {0._count}>'
        return fmt.format(self)
def _not_overridden(f: FuncT) -> FuncT:
    f.__help_command_not_overridden__ = True
    return f
class _HelpCommandImpl(Command):
    def __init__(self, inject: HelpCommand, *args: Any, **kwargs: Any) -> None:
        super().__init__(inject.command_callback, *args, **kwargs)
        self._original: HelpCommand = inject
        self._injected: HelpCommand = inject
        self.params: Dict[str, Parameter] = get_signature_parameters(inject.command_callback, globals(), skip_parameters=1)
    async def prepare(self, ctx: Context[Any]) -> None:
        self._injected = injected = self._original.copy()
        injected.context = ctx
        self.callback = injected.command_callback
        self.params = get_signature_parameters(injected.command_callback, globals(), skip_parameters=1)
        on_error = injected.on_help_command_error
        if not hasattr(on_error, '__help_command_not_overridden__'):
            if self.cog is not None:
                self.on_error = self._on_error_cog_implementation
            else:
                self.on_error = on_error
        await super().prepare(ctx)
    async def _parse_arguments(self, ctx: Context[BotT]) -> None:
        original_cog = self.cog
        self.cog = None
        try:
            await super()._parse_arguments(ctx)
        finally:
            self.cog = original_cog
    async def _on_error_cog_implementation(self, _, ctx: Context[BotT], error: CommandError) -> None:
        await self._injected.on_help_command_error(ctx, error)
    def _inject_into_cog(self, cog: Cog) -> None:
        def wrapped_get_commands(
            *, _original: Callable[[], List[Command[Any, ..., Any]]] = cog.get_commands
        ) -> List[Command[Any, ..., Any]]:
            ret = _original()
            ret.append(self)
            return ret
        def wrapped_walk_commands(
            *, _original: Callable[[], Generator[Command[Any, ..., Any], None, None]] = cog.walk_commands
        ):
            yield from _original()
            yield self
        functools.update_wrapper(wrapped_get_commands, cog.get_commands)
        functools.update_wrapper(wrapped_walk_commands, cog.walk_commands)
        cog.get_commands = wrapped_get_commands
        cog.walk_commands = wrapped_walk_commands
        self.cog = cog
    def _eject_cog(self) -> None:
        if self.cog is None:
            return
        cog = self.cog
        cog.get_commands = cog.get_commands.__wrapped__
        cog.walk_commands = cog.walk_commands.__wrapped__
        self.cog = None
        self.on_error = self._injected.on_help_command_error
class HelpCommand:
    r
    MENTION_TRANSFORMS = {
        '@everyone': '@\u200beveryone',
        '@here': '@\u200bhere',
        r'<@!?[0-9]{17,22}>': '@deleted-user',
        r'<@&[0-9]{17,22}>': '@deleted-role',
    }
    MENTION_PATTERN = re.compile('|'.join(MENTION_TRANSFORMS.keys()))
    if TYPE_CHECKING:
        __original_kwargs__: Dict[str, Any]
        __original_args__: Tuple[Any, ...]
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        self = super().__new__(cls)
        deepcopy = copy.deepcopy
        self.__original_kwargs__ = {k: deepcopy(v) for k, v in kwargs.items()}
        self.__original_args__ = deepcopy(args)
        return self
    def __init__(self, **options: Any) -> None:
        self.show_hidden: bool = options.pop('show_hidden', False)
        self.verify_checks: bool = options.pop('verify_checks', True)
        self.command_attrs: Dict[str, Any]
        self.command_attrs = attrs = options.pop('command_attrs', {})
        attrs.setdefault('name', 'help')
        attrs.setdefault('help', 'Shows this message')
        self.context: Context[_Bot] = MISSING
        self._command_impl = _HelpCommandImpl(self, **self.command_attrs)
    def copy(self) -> Self:
        obj = self.__class__(*self.__original_args__, **self.__original_kwargs__)
        obj._command_impl = self._command_impl
        return obj
    def _add_to_bot(self, bot: BotBase) -> None:
        command = _HelpCommandImpl(self, **self.command_attrs)
        bot.add_command(command)
        self._command_impl = command
    def _remove_from_bot(self, bot: BotBase) -> None:
        bot.remove_command(self._command_impl.name)
        self._command_impl._eject_cog()
    def add_check(self, func: UserCheck[Context[Any]], /) -> None:
        self._command_impl.add_check(func)
    def remove_check(self, func: UserCheck[Context[Any]], /) -> None:
        self._command_impl.remove_check(func)
    def get_bot_mapping(self) -> Dict[Optional[Cog], List[Command[Any, ..., Any]]]:
        bot = self.context.bot
        mapping: Dict[Optional[Cog], List[Command[Any, ..., Any]]] = {cog: cog.get_commands() for cog in bot.cogs.values()}
        mapping[None] = [c for c in bot.commands if c.cog is None]
        return mapping
    @property
    def invoked_with(self) -> Optional[str]:
        command_name = self._command_impl.name
        ctx = self.context
        if ctx is MISSING or ctx.command is None or ctx.command.qualified_name != command_name:
            return command_name
        return ctx.invoked_with
    def get_command_signature(self, command: Command[Any, ..., Any], /) -> str:
        parent: Optional[Group[Any, ..., Any]] = command.parent
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + ' ' + parent.signature)
            parent = parent.parent
        parent_sig = ' '.join(reversed(entries))
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'[{command.name}|{aliases}]'
            if parent_sig:
                fmt = parent_sig + ' ' + fmt
            alias = fmt
        else:
            alias = command.name if not parent_sig else parent_sig + ' ' + command.name
        return f'{self.context.clean_prefix}{alias} {command.signature}'
    def remove_mentions(self, string: str, /) -> str:
        def replace(obj: re.Match, *, transforms: Dict[str, str] = self.MENTION_TRANSFORMS) -> str:
            return transforms.get(obj.group(0), '@invalid')
        return self.MENTION_PATTERN.sub(replace, string)
    @property
    def cog(self) -> Optional[Cog]:
        return self._command_impl.cog
    @cog.setter
    def cog(self, cog: Optional[Cog]) -> None:
        self._command_impl._eject_cog()
        if cog is not None:
            self._command_impl._inject_into_cog(cog)
    def command_not_found(self, string: str, /) -> str:
        return f'No command called "{string}" found.'
    def subcommand_not_found(self, command: Command[Any, ..., Any], string: str, /) -> str:
        if isinstance(command, Group) and len(command.all_commands) > 0:
            return f'Command "{command.qualified_name}" has no subcommand named {string}'
        return f'Command "{command.qualified_name}" has no subcommands.'
    async def filter_commands(
        self,
        commands: Iterable[Command[Any, ..., Any]],
        /,
        *,
        sort: bool = False,
        key: Optional[Callable[[Command[Any, ..., Any]], Any]] = None,
    ) -> List[Command[Any, ..., Any]]:
        if sort and key is None:
            key = lambda c: c.name
        iterator = commands if self.show_hidden else filter(lambda c: not c.hidden, commands)
        if self.verify_checks is False:
            return sorted(iterator, key=key) if sort else list(iterator)
        if self.verify_checks is None and not self.context.guild:
            return sorted(iterator, key=key) if sort else list(iterator)
        async def predicate(cmd: Command[Any, ..., Any]) -> bool:
            try:
                return await cmd.can_run(self.context)
            except CommandError:
                return False
        ret = []
        for cmd in iterator:
            valid = await predicate(cmd)
            if valid:
                ret.append(cmd)
        if sort:
            ret.sort(key=key)
        return ret
    def get_max_size(self, commands: Sequence[Command[Any, ..., Any]], /) -> int:
        as_lengths = (discord.utils._string_width(c.name) for c in commands)
        return max(as_lengths, default=0)
    def get_destination(self) -> discord.abc.MessageableChannel:
        return self.context.channel
    async def send_error_message(self, error: str, /) -> None:
        destination = self.get_destination()
        await destination.send(error)
    @_not_overridden
    async def on_help_command_error(self, ctx: Context[BotT], error: CommandError, /) -> None:
        pass
    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:
        return None
    async def send_cog_help(self, cog: Cog, /) -> None:
        return None
    async def send_group_help(self, group: Group[Any, ..., Any], /) -> None:
        return None
    async def send_command_help(self, command: Command[Any, ..., Any], /) -> None:
        return None
    async def prepare_help_command(self, ctx: Context[BotT], command: Optional[str] = None, /) -> None:
        pass
    async def command_callback(self, ctx: Context[BotT], /, *, command: Optional[str] = None) -> None:
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot
        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)
        cog = bot.get_cog(command)
        if cog is not None:
            return await self.send_cog_help(cog)
        maybe_coro = discord.utils.maybe_coroutine
        keys = command.split(' ')
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
            return await self.send_error_message(string)
        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                cmd = found
        if isinstance(cmd, Group):
            return await self.send_group_help(cmd)
        else:
            return await self.send_command_help(cmd)
class DefaultHelpCommand(HelpCommand):
    def __init__(self, **options: Any) -> None:
        self.width: int = options.pop('width', 80)
        self.indent: int = options.pop('indent', 2)
        self.sort_commands: bool = options.pop('sort_commands', True)
        self.dm_help: bool = options.pop('dm_help', False)
        self.dm_help_threshold: int = options.pop('dm_help_threshold', 1000)
        self.arguments_heading: str = options.pop('arguments_heading', "Arguments:")
        self.commands_heading: str = options.pop('commands_heading', 'Commands:')
        self.default_argument_description: str = options.pop('default_argument_description', 'No description given')
        self.no_category: str = options.pop('no_category', 'No Category')
        self.paginator: Paginator = options.pop('paginator', None)
        self.show_parameter_descriptions: bool = options.pop('show_parameter_descriptions', True)
        if self.paginator is None:
            self.paginator: Paginator = Paginator()
        super().__init__(**options)
    def shorten_text(self, text: str, /) -> str:
        if len(text) > self.width:
            return text[: self.width - 3].rstrip() + '...'
        return text
    def get_ending_note(self) -> str:
        command_name = self.invoked_with
        return (
            f'Type {self.context.clean_prefix}{command_name} command for more info on a command.\n'
            f'You can also type {self.context.clean_prefix}{command_name} category for more info on a category.'
        )
    def get_command_signature(self, command: Command[Any, ..., Any], /) -> str:
        if not self.show_parameter_descriptions:
            return super().get_command_signature(command)
        name = command.name
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            name = f'[{command.name}|{aliases}]'
        return f'{self.context.clean_prefix}{name}'
    def add_indented_commands(
        self, commands: Sequence[Command[Any, ..., Any]], /, *, heading: str, max_size: Optional[int] = None
    ) -> None:
        if not commands:
            return
        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)
        get_width = discord.utils._string_width
        for command in commands:
            name = command.name
            width = max_size - (get_width(name) - len(name))
            entry = f'{self.indent * " "}{name:<{width}} {command.short_doc}'
            self.paginator.add_line(self.shorten_text(entry))
    def add_command_arguments(self, command: Command[Any, ..., Any], /) -> None:
        arguments = command.clean_params.values()
        if not arguments:
            return
        self.paginator.add_line(self.arguments_heading)
        max_size = self.get_max_size(arguments)
        get_width = discord.utils._string_width
        for argument in arguments:
            name = argument.displayed_name or argument.name
            width = max_size - (get_width(name) - len(name))
            entry = f'{self.indent * " "}{name:<{width}} {argument.description or self.default_argument_description}'
            entry = self.shorten_text(entry)
            if argument.displayed_default is not None:
                entry += f' (default: {argument.displayed_default})'
            self.paginator.add_line(entry)
    async def send_pages(self) -> None:
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(page)
    def add_command_formatting(self, command: Command[Any, ..., Any], /) -> None:
        if command.description:
            self.paginator.add_line(command.description, empty=True)
        signature = self.get_command_signature(command)
        self.paginator.add_line(signature, empty=True)
        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()
        if self.show_parameter_descriptions:
            self.add_command_arguments(command)
    def get_destination(self) -> discord.abc.Messageable:
        ctx = self.context
        if self.dm_help is True:
            return ctx.author
        elif self.dm_help is None and len(self.paginator) > self.dm_help_threshold:
            return ctx.author
        else:
            return ctx.channel
    async def prepare_help_command(self, ctx: Context[BotT], command: Optional[str], /) -> None:
        self.paginator.clear()
        await super().prepare_help_command(ctx, command)
    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:
        ctx = self.context
        bot = ctx.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)
        no_category = f'\u200b{self.no_category}:'
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else no_category
        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_indented_commands(commands, heading=category, max_size=max_size)
        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)
        await self.send_pages()
    async def send_command_help(self, command: Command[Any, ..., Any], /) -> None:
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()
    async def send_group_help(self, group: Group[Any, ..., Any], /) -> None:
        self.add_command_formatting(group)
        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)
        if filtered:
            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)
        await self.send_pages()
    async def send_cog_help(self, cog: Cog, /) -> None:
        if cog.description:
            self.paginator.add_line(cog.description, empty=True)
        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)
        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)
        await self.send_pages()
class MinimalHelpCommand(HelpCommand):
    def __init__(self, **options: Any) -> None:
        self.sort_commands: bool = options.pop('sort_commands', True)
        self.commands_heading: str = options.pop('commands_heading', 'Commands')
        self.dm_help: bool = options.pop('dm_help', False)
        self.dm_help_threshold: int = options.pop('dm_help_threshold', 1000)
        self.aliases_heading: str = options.pop('aliases_heading', 'Aliases:')
        self.no_category: str = options.pop('no_category', 'No Category')
        self.paginator: Paginator = options.pop('paginator', None)
        if self.paginator is None:
            self.paginator: Paginator = Paginator(suffix=None, prefix=None)
        super().__init__(**options)
    async def send_pages(self) -> None:
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(page)
    def get_opening_note(self) -> str:
        command_name = self.invoked_with
        return (
            f'Use `{self.context.clean_prefix}{command_name} [command]` for more info on a command.\n'
            f'You can also use `{self.context.clean_prefix}{command_name} [category]` for more info on a category.'
        )
    def get_command_signature(self, command: Command[Any, ..., Any], /) -> str:
        return f'{self.context.clean_prefix}{command.qualified_name} {command.signature}'
    def get_ending_note(self) -> str:
        return ''
    def add_bot_commands_formatting(self, commands: Sequence[Command[Any, ..., Any]], heading: str, /) -> None:
        if commands:
            joined = '\u2002'.join(c.name for c in commands)
            self.paginator.add_line(f'__**{heading}**__')
            self.paginator.add_line(joined)
    def add_subcommand_formatting(self, command: Command[Any, ..., Any], /) -> None:
        fmt = '{0}{1} \N{EN DASH} {2}' if command.short_doc else '{0}{1}'
        self.paginator.add_line(fmt.format(self.context.clean_prefix, command.qualified_name, command.short_doc))
    def add_aliases_formatting(self, aliases: Sequence[str], /) -> None:
        self.paginator.add_line(f'**{self.aliases_heading}** {", ".join(aliases)}', empty=True)
    def add_command_formatting(self, command: Command[Any, ..., Any], /) -> None:
        if command.description:
            self.paginator.add_line(command.description, empty=True)
        signature = self.get_command_signature(command)
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature, empty=True)
        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()
    def get_destination(self) -> discord.abc.Messageable:
        ctx = self.context
        if self.dm_help is True:
            return ctx.author
        elif self.dm_help is None and len(self.paginator) > self.dm_help_threshold:
            return ctx.author
        else:
            return ctx.channel
    async def prepare_help_command(self, ctx: Context[BotT], command: Optional[str], /) -> None:
        self.paginator.clear()
        await super().prepare_help_command(ctx, command)
    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:
        ctx = self.context
        bot = ctx.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)
        no_category = f'\u200b{self.no_category}'
        def get_category(command: Command[Any, ..., Any], *, no_category: str = no_category) -> str:
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category
        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_bot_commands_formatting(commands, category)
        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)
        await self.send_pages()
    async def send_cog_help(self, cog: Cog, /) -> None:
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)
        if cog.description:
            self.paginator.add_line(cog.description, empty=True)
        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line(f'**{cog.qualified_name} {self.commands_heading}**')
            for command in filtered:
                self.add_subcommand_formatting(command)
            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)
        await self.send_pages()
    async def send_group_help(self, group: Group[Any, ..., Any], /) -> None:
        self.add_command_formatting(group)
        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            note = self.get_opening_note()
            if note:
                self.paginator.add_line(note, empty=True)
            self.paginator.add_line(f'**{self.commands_heading}**')
            for command in filtered:
                self.add_subcommand_formatting(command)
            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)
        await self.send_pages()
    async def send_command_help(self, command: Command[Any, ..., Any], /) -> None:
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()