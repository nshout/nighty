from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Union
from discord.errors import ClientException, DiscordException
if TYPE_CHECKING:
    from discord.abc import GuildChannel
    from discord.threads import Thread
    from discord.types.snowflake import Snowflake, SnowflakeList
    from ._types import BotT
    from .context import Context
    from .converter import Converter
    from .cooldowns import BucketType, Cooldown
    from .flags import Flag
    from .parameters import Parameter
__all__ = (
    'CommandError',
    'MissingRequiredArgument',
    'MissingRequiredAttachment',
    'BadArgument',
    'PrivateMessageOnly',
    'NoPrivateMessage',
    'CheckFailure',
    'CheckAnyFailure',
    'CommandNotFound',
    'DisabledCommand',
    'CommandInvokeError',
    'TooManyArguments',
    'UserInputError',
    'CommandOnCooldown',
    'MaxConcurrencyReached',
    'NotOwner',
    'MessageNotFound',
    'ObjectNotFound',
    'MemberNotFound',
    'GuildNotFound',
    'UserNotFound',
    'ChannelNotFound',
    'ThreadNotFound',
    'ChannelNotReadable',
    'BadColourArgument',
    'BadColorArgument',
    'RoleNotFound',
    'BadInviteArgument',
    'EmojiNotFound',
    'GuildStickerNotFound',
    'ScheduledEventNotFound',
    'PartialEmojiConversionFailure',
    'BadBoolArgument',
    'MissingRole',
    'BotMissingRole',
    'MissingAnyRole',
    'BotMissingAnyRole',
    'MissingPermissions',
    'BotMissingPermissions',
    'NSFWChannelRequired',
    'ConversionError',
    'BadUnionArgument',
    'BadLiteralArgument',
    'ArgumentParsingError',
    'UnexpectedQuoteError',
    'InvalidEndOfQuotedStringError',
    'ExpectedClosingQuoteError',
    'ExtensionError',
    'ExtensionAlreadyLoaded',
    'ExtensionNotLoaded',
    'NoEntryPointError',
    'ExtensionFailed',
    'ExtensionNotFound',
    'CommandRegistrationError',
    'FlagError',
    'BadFlagArgument',
    'MissingFlagArgument',
    'TooManyFlags',
    'MissingRequiredFlag',
    'RangeError',
)
class CommandError(DiscordException):
    r
    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        if message is not None:
            m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(m, *args)
        else:
            super().__init__(*args)
class ConversionError(CommandError):
    def __init__(self, converter: Converter[Any], original: Exception) -> None:
        self.converter: Converter[Any] = converter
        self.original: Exception = original
class UserInputError(CommandError):
    pass
class CommandNotFound(CommandError):
    pass
class MissingRequiredArgument(UserInputError):
    def __init__(self, param: Parameter) -> None:
        self.param: Parameter = param
        super().__init__(f'{param.displayed_name or param.name} is a required argument that is missing.')
class MissingRequiredAttachment(UserInputError):
    def __init__(self, param: Parameter) -> None:
        self.param: Parameter = param
        super().__init__(f'{param.displayed_name or param.name} is a required argument that is missing an attachment.')
class TooManyArguments(UserInputError):
    pass
class BadArgument(UserInputError):
    pass
class CheckFailure(CommandError):
    pass
class CheckAnyFailure(CheckFailure):
    def __init__(self, checks: List[Callable[[Context[BotT]], bool]], errors: List[CheckFailure]) -> None:
        self.checks: List[Callable[[Context[BotT]], bool]] = checks
        self.errors: List[CheckFailure] = errors
        super().__init__('You do not have permission to run this command.')
class PrivateMessageOnly(CheckFailure):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or 'This command can only be used in private messages.')
class NoPrivateMessage(CheckFailure):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or 'This command cannot be used in private messages.')
class NotOwner(CheckFailure):
    pass
class ObjectNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'{argument!r} does not follow a valid ID or mention format.')
class MemberNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Member "{argument}" not found.')
class GuildNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Guild "{argument}" not found.')
class UserNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'User "{argument}" not found.')
class MessageNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Message "{argument}" not found.')
class ChannelNotReadable(BadArgument):
    def __init__(self, argument: Union[GuildChannel, Thread]) -> None:
        self.argument: Union[GuildChannel, Thread] = argument
        super().__init__(f"Can't read messages in {argument.mention}.")
class ChannelNotFound(BadArgument):
    def __init__(self, argument: Union[int, str]) -> None:
        self.argument: Union[int, str] = argument
        super().__init__(f'Channel "{argument}" not found.')
class ThreadNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Thread "{argument}" not found.')
class BadColourArgument(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Colour "{argument}" is invalid.')
BadColorArgument = BadColourArgument
class RoleNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Role "{argument}" not found.')
class BadInviteArgument(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Invite "{argument}" is invalid or expired.')
class EmojiNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Emoji "{argument}" not found.')
class PartialEmojiConversionFailure(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Couldn\'t convert "{argument}" to PartialEmoji.')
class GuildStickerNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'Sticker "{argument}" not found.')
class ScheduledEventNotFound(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'ScheduledEvent "{argument}" not found.')
class BadBoolArgument(BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument: str = argument
        super().__init__(f'{argument} is not a recognised boolean option')
class RangeError(BadArgument):
    def __init__(
        self,
        value: Union[int, float, str],
        minimum: Optional[Union[int, float]],
        maximum: Optional[Union[int, float]],
    ) -> None:
        self.value: Union[int, float, str] = value
        self.minimum: Optional[Union[int, float]] = minimum
        self.maximum: Optional[Union[int, float]] = maximum
        label: str = ''
        if minimum is None and maximum is not None:
            label = f'no more than {maximum}'
        elif minimum is not None and maximum is None:
            label = f'not less than {minimum}'
        elif maximum is not None and minimum is not None:
            label = f'between {minimum} and {maximum}'
        if label and isinstance(value, str):
            label += ' characters'
            count = len(value)
            if count == 1:
                value = '1 character'
            else:
                value = f'{count} characters'
        super().__init__(f'value must be {label} but received {value}')
class DisabledCommand(CommandError):
    pass
class CommandInvokeError(CommandError):
    def __init__(self, e: Exception) -> None:
        self.original: Exception = e
        super().__init__(f'Command raised an exception: {e.__class__.__name__}: {e}')
class CommandOnCooldown(CommandError):
    def __init__(self, cooldown: Cooldown, retry_after: float, type: BucketType) -> None:
        self.cooldown: Cooldown = cooldown
        self.retry_after: float = retry_after
        self.type: BucketType = type
        super().__init__(f'You are on cooldown. Try again in {retry_after:.2f}s')
class MaxConcurrencyReached(CommandError):
    def __init__(self, number: int, per: BucketType) -> None:
        self.number: int = number
        self.per: BucketType = per
        name = per.name
        suffix = 'per %s' % name if per.name != 'default' else 'globally'
        plural = '%s times %s' if number > 1 else '%s time %s'
        fmt = plural % (number, suffix)
        super().__init__(f'Too many people are using this command. It can only be used {fmt} concurrently.')
class MissingRole(CheckFailure):
    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f'Role {missing_role!r} is required to run this command.'
        super().__init__(message)
class BotMissingRole(CheckFailure):
    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f'Bot requires the role {missing_role!r} to run this command'
        super().__init__(message)
class MissingAnyRole(CheckFailure):
    def __init__(self, missing_roles: SnowflakeList) -> None:
        self.missing_roles: SnowflakeList = missing_roles
        missing = [f"'{role}'" for role in missing_roles]
        if len(missing) > 2:
            fmt = '{}, or {}'.format(', '.join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)
        message = f'You are missing at least one of the required roles: {fmt}'
        super().__init__(message)
class BotMissingAnyRole(CheckFailure):
    def __init__(self, missing_roles: SnowflakeList) -> None:
        self.missing_roles: SnowflakeList = missing_roles
        missing = [f"'{role}'" for role in missing_roles]
        if len(missing) > 2:
            fmt = '{}, or {}'.format(', '.join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)
        message = f'Bot is missing at least one of the required roles: {fmt}'
        super().__init__(message)
class NSFWChannelRequired(CheckFailure):
    def __init__(self, channel: Union[GuildChannel, Thread]) -> None:
        self.channel: Union[GuildChannel, Thread] = channel
        super().__init__(f"Channel '{channel}' needs to be NSFW for this command to work.")
class MissingPermissions(CheckFailure):
    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]
        if len(missing) > 2:
            fmt = '{}, and {}'.format(', '.join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = f'You are missing {fmt} permission(s) to run this command.'
        super().__init__(message, *args)
class BotMissingPermissions(CheckFailure):
    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]
        if len(missing) > 2:
            fmt = '{}, and {}'.format(', '.join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = f'Bot requires {fmt} permission(s) to run this command.'
        super().__init__(message, *args)
class BadUnionArgument(UserInputError):
    def __init__(self, param: Parameter, converters: Tuple[type, ...], errors: List[CommandError]) -> None:
        self.param: Parameter = param
        self.converters: Tuple[type, ...] = converters
        self.errors: List[CommandError] = errors
        def _get_name(x):
            try:
                return x.__name__
            except AttributeError:
                if hasattr(x, '__origin__'):
                    return repr(x)
                return x.__class__.__name__
        to_string = [_get_name(x) for x in converters]
        if len(to_string) > 2:
            fmt = '{}, or {}'.format(', '.join(to_string[:-1]), to_string[-1])
        else:
            fmt = ' or '.join(to_string)
        super().__init__(f'Could not convert "{param.displayed_name or param.name}" into {fmt}.')
class BadLiteralArgument(UserInputError):
    def __init__(self, param: Parameter, literals: Tuple[Any, ...], errors: List[CommandError], argument: str = "") -> None:
        self.param: Parameter = param
        self.literals: Tuple[Any, ...] = literals
        self.errors: List[CommandError] = errors
        self.argument: str = argument
        to_string = [repr(l) for l in literals]
        if len(to_string) > 2:
            fmt = '{}, or {}'.format(', '.join(to_string[:-1]), to_string[-1])
        else:
            fmt = ' or '.join(to_string)
        super().__init__(f'Could not convert "{param.displayed_name or param.name}" into the literal {fmt}.')
class ArgumentParsingError(UserInputError):
    pass
class UnexpectedQuoteError(ArgumentParsingError):
    def __init__(self, quote: str) -> None:
        self.quote: str = quote
        super().__init__(f'Unexpected quote mark, {quote!r}, in non-quoted string')
class InvalidEndOfQuotedStringError(ArgumentParsingError):
    def __init__(self, char: str) -> None:
        self.char: str = char
        super().__init__(f'Expected space after closing quotation but received {char!r}')
class ExpectedClosingQuoteError(ArgumentParsingError):
    def __init__(self, close_quote: str) -> None:
        self.close_quote: str = close_quote
        super().__init__(f'Expected closing {close_quote}.')
class ExtensionError(DiscordException):
    def __init__(self, message: Optional[str] = None, *args: Any, name: str) -> None:
        self.name: str = name
        message = message or f'Extension {name!r} had an error.'
        m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
        super().__init__(m, *args)
class ExtensionAlreadyLoaded(ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f'Extension {name!r} is already loaded.', name=name)
class ExtensionNotLoaded(ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f'Extension {name!r} has not been loaded.', name=name)
class NoEntryPointError(ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} has no 'setup' function.", name=name)
class ExtensionFailed(ExtensionError):
    def __init__(self, name: str, original: Exception) -> None:
        self.original: Exception = original
        msg = f'Extension {name!r} raised an error: {original.__class__.__name__}: {original}'
        super().__init__(msg, name=name)
class ExtensionNotFound(ExtensionError):
    def __init__(self, name: str) -> None:
        msg = f'Extension {name!r} could not be loaded.'
        super().__init__(msg, name=name)
class CommandRegistrationError(ClientException):
    def __init__(self, name: str, *, alias_conflict: bool = False) -> None:
        self.name: str = name
        self.alias_conflict: bool = alias_conflict
        type_ = 'alias' if alias_conflict else 'command'
        super().__init__(f'The {type_} {name} is already an existing command or alias.')
class FlagError(BadArgument):
    pass
class TooManyFlags(FlagError):
    def __init__(self, flag: Flag, values: List[str]) -> None:
        self.flag: Flag = flag
        self.values: List[str] = values
        super().__init__(f'Too many flag values, expected {flag.max_args} but received {len(values)}.')
class BadFlagArgument(FlagError):
    def __init__(self, flag: Flag, argument: str, original: Exception) -> None:
        self.flag: Flag = flag
        try:
            name = flag.annotation.__name__
        except AttributeError:
            name = flag.annotation.__class__.__name__
        self.argument: str = argument
        self.original: Exception = original
        super().__init__(f'Could not convert to {name!r} for flag {flag.name!r}')
class MissingRequiredFlag(FlagError):
    def __init__(self, flag: Flag) -> None:
        self.flag: Flag = flag
        super().__init__(f'Flag {flag.name!r} is required and missing')
class MissingFlagArgument(FlagError):
    def __init__(self, flag: Flag) -> None:
        self.flag: Flag = flag
        super().__init__(f'Flag {flag.name!r} does not have an argument')