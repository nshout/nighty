from __future__ import annotations
from typing import Optional, Tuple, Dict
import argparse
import sys
from pathlib import Path
import discord
import importlib.metadata
import aiohttp
import platform
def show_version() -> None:
    entries = []
    entries.append('- Python v{0.major}.{0.minor}.{0.micro}-{0.releaselevel}'.format(sys.version_info))
    version_info = discord.version_info
    entries.append('- discord.py-self v{0.major}.{0.minor}.{0.micro}-{0.releaselevel}'.format(version_info))
    if version_info.releaselevel != 'final':
        version = importlib.metadata.version('discord.py-self')
        if version:
            entries.append(f'    - discord.py-self metadata: v{version}')
    entries.append(f'- aiohttp v{aiohttp.__version__}')
    uname = platform.uname()
    entries.append('- system info: {0.system} {0.release} {0.version}'.format(uname))
    print('\n'.join(entries))
def core(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.version:
        show_version()
    else:
        parser.print_help()
_bot_template =
_gitignore_template =
_cog_template =
_cog_extras =
_base_table: Dict[str, Optional[str]] = {
    '<': '-',
    '>': '-',
    ':': '-',
    '"': '-',
    '|': '-',
    '?': '-',
    '*': '-',
}
_base_table.update((chr(i), None) for i in range(32))
_translation_table = str.maketrans(_base_table)
def to_path(parser: argparse.ArgumentParser, name: str, *, replace_spaces: bool = False) -> Path:
    if isinstance(name, Path):
        return name
    if sys.platform == 'win32':
        forbidden = (
            'CON',
            'PRN',
            'AUX',
            'NUL',
            'COM1',
            'COM2',
            'COM3',
            'COM4',
            'COM5',
            'COM6',
            'COM7',
            'COM8',
            'COM9',
            'LPT1',
            'LPT2',
            'LPT3',
            'LPT4',
            'LPT5',
            'LPT6',
            'LPT7',
            'LPT8',
            'LPT9',
        )
        if len(name) <= 4 and name.upper() in forbidden:
            parser.error('invalid directory name given, use a different one')
    name = name.translate(_translation_table)
    if replace_spaces:
        name = name.replace(' ', '-')
    return Path(name)
def newbot(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    new_directory = to_path(parser, args.directory) / to_path(parser, args.name)
    try:
        new_directory.mkdir(exist_ok=True, parents=True)
    except OSError as exc:
        parser.error(f'could not create our bot directory ({exc})')
    cogs = new_directory / 'cogs'
    try:
        cogs.mkdir(exist_ok=True)
        init = cogs / '__init__.py'
        init.touch()
    except OSError as exc:
        print(f'warning: could not create cogs directory ({exc})')
    try:
        with open(str(new_directory / 'config.py'), 'w', encoding='utf-8') as fp:
            fp.write('token = "place your token here"\ncogs = []\n')
    except OSError as exc:
        parser.error(f'could not create config file ({exc})')
    try:
        with open(str(new_directory / 'bot.py'), 'w', encoding='utf-8') as fp:
            fp.write(_bot_template.format(prefix=args.prefix))
    except OSError as exc:
        parser.error(f'could not create bot file ({exc})')
    if not args.no_git:
        try:
            with open(str(new_directory / '.gitignore'), 'w', encoding='utf-8') as fp:
                fp.write(_gitignore_template)
        except OSError as exc:
            print(f'warning: could not create .gitignore file ({exc})')
    print('successfully made bot at', new_directory)
def newcog(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    cog_dir = to_path(parser, args.directory)
    try:
        cog_dir.mkdir(exist_ok=True)
    except OSError as exc:
        print(f'warning: could not create cogs directory ({exc})')
    directory = cog_dir / to_path(parser, args.name)
    directory = directory.with_suffix('.py')
    try:
        with open(str(directory), 'w', encoding='utf-8') as fp:
            attrs = ''
            extra = _cog_extras if args.full else ''
            if args.class_name:
                name = args.class_name
            else:
                name = str(directory.stem)
                if '-' in name or '_' in name:
                    translation = str.maketrans('-_', '  ')
                    name = name.translate(translation).title().replace(' ', '')
                else:
                    name = name.title()
            if args.display_name:
                attrs += f', name="{args.display_name}"'
            if args.hide_commands:
                attrs += ', command_attrs=dict(hidden=True)'
            fp.write(_cog_template.format(name=name, extra=extra, attrs=attrs))
    except OSError as exc:
        parser.error(f'could not create cog file ({exc})')
    else:
        print('successfully made cog at', directory)
def add_newbot_args(subparser: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparser.add_parser('newbot', help='creates a command bot project quickly')
    parser.set_defaults(func=newbot)
    parser.add_argument('name', help='the bot project name')
    parser.add_argument('directory', help='the directory to place it in (default: .)', nargs='?', default=Path.cwd())
    parser.add_argument('--prefix', help='the bot prefix (default: $)', default='$', metavar='<prefix>')
    parser.add_argument('--no-git', help='do not create a .gitignore file', action='store_true', dest='no_git')
def add_newcog_args(subparser: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparser.add_parser('newcog', help='creates a new cog template quickly')
    parser.set_defaults(func=newcog)
    parser.add_argument('name', help='the cog name')
    parser.add_argument('directory', help='the directory to place it in (default: cogs)', nargs='?', default=Path('cogs'))
    parser.add_argument('--class-name', help='the class name of the cog (default: <name>)', dest='class_name')
    parser.add_argument('--display-name', help='the cog name (default: <name>)')
    parser.add_argument('--hide-commands', help='whether to hide all commands in the cog', action='store_true')
    parser.add_argument('--full', help='add all special methods as well', action='store_true')
def parse_args() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = argparse.ArgumentParser(prog='discord', description='Tools for helping with discord.py-self')
    parser.add_argument('-v', '--version', action='store_true', help='shows the library version')
    parser.set_defaults(func=core)
    subparser = parser.add_subparsers(dest='subcommand', title='subcommands')
    add_newbot_args(subparser)
    add_newcog_args(subparser)
    return parser, parser.parse_args()
def main() -> None:
    parser, args = parse_args()
    args.func(parser, args)
if __name__ == '__main__':
    main()