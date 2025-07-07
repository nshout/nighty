from __future__ import annotations
import colorsys
import random
import re
from typing import TYPE_CHECKING, Optional, Tuple, Union
if TYPE_CHECKING:
    from typing_extensions import Self
__all__ = (
    'Colour',
    'Color',
)
RGB_REGEX = re.compile(r'rgb\s*\((?P<r>[0-9.]+%?)\s*,\s*(?P<g>[0-9.]+%?)\s*,\s*(?P<b>[0-9.]+%?)\s*\)')
def parse_hex_number(argument: str) -> Colour:
    arg = ''.join(i * 2 for i in argument) if len(argument) == 3 else argument
    try:
        value = int(arg, base=16)
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError('hex number out of range for 24-bit colour')
    except ValueError:
        raise ValueError('invalid hex digit given') from None
    else:
        return Color(value=value)
def parse_rgb_number(number: str) -> int:
    if number[-1] == '%':
        value = float(number[:-1])
        if not (0 <= value <= 100):
            raise ValueError('rgb percentage can only be between 0 to 100')
        return round(255 * (value / 100))
    value = int(number)
    if not (0 <= value <= 255):
        raise ValueError('rgb number can only be between 0 to 255')
    return value
def parse_rgb(argument: str, *, regex: re.Pattern[str] = RGB_REGEX) -> Colour:
    match = regex.match(argument)
    if match is None:
        raise ValueError('invalid rgb syntax found')
    red = parse_rgb_number(match.group('r'))
    green = parse_rgb_number(match.group('g'))
    blue = parse_rgb_number(match.group('b'))
    return Color.from_rgb(red, green, blue)
class Colour:
    __slots__ = ('value',)
    def __init__(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'Expected int parameter, received {value.__class__.__name__} instead.')
        self.value: int = value
    def _get_byte(self, byte: int) -> int:
        return (self.value >> (8 * byte)) & 0xFF
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Colour) and self.value == other.value
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    def __str__(self) -> str:
        return f'
    def __int__(self) -> int:
        return self.value
    def __repr__(self) -> str:
        return f'<Colour value={self.value}>'
    def __hash__(self) -> int:
        return hash(self.value)
    @property
    def r(self) -> int:
        return self._get_byte(2)
    @property
    def g(self) -> int:
        return self._get_byte(1)
    @property
    def b(self) -> int:
        return self._get_byte(0)
    def to_rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)
    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Self:
        return cls((r << 16) + (g << 8) + b)
    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> Self:
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(*(int(x * 255) for x in rgb))
    @classmethod
    def from_str(cls, value: str) -> Self:
        if value[0] == '
            return parse_hex_number(value[1:])
        if value[0:2] == '0x':
            rest = value[2:]
            if rest.startswith('
                return parse_hex_number(rest[1:])
            return parse_hex_number(rest)
        arg = value.lower()
        if arg[0:3] == 'rgb':
            return parse_rgb(arg)
        raise ValueError('unknown colour format given')
    @classmethod
    def default(cls) -> Self:
        return cls(0)
    @classmethod
    def random(cls, *, seed: Optional[Union[int, str, float, bytes, bytearray]] = None) -> Self:
        rand = random if seed is None else random.Random(seed)
        return cls.from_hsv(rand.random(), 1, 1)
    @classmethod
    def teal(cls) -> Self:
        return cls(0x1ABC9C)
    @classmethod
    def dark_teal(cls) -> Self:
        return cls(0x11806A)
    @classmethod
    def brand_green(cls) -> Self:
        return cls(0x57F287)
    @classmethod
    def green(cls) -> Self:
        return cls(0x2ECC71)
    @classmethod
    def dark_green(cls) -> Self:
        return cls(0x1F8B4C)
    @classmethod
    def blue(cls) -> Self:
        return cls(0x3498DB)
    @classmethod
    def dark_blue(cls) -> Self:
        return cls(0x206694)
    @classmethod
    def purple(cls) -> Self:
        return cls(0x9B59B6)
    @classmethod
    def dark_purple(cls) -> Self:
        return cls(0x71368A)
    @classmethod
    def magenta(cls) -> Self:
        return cls(0xE91E63)
    @classmethod
    def dark_magenta(cls) -> Self:
        return cls(0xAD1457)
    @classmethod
    def gold(cls) -> Self:
        return cls(0xF1C40F)
    @classmethod
    def dark_gold(cls) -> Self:
        return cls(0xC27C0E)
    @classmethod
    def orange(cls) -> Self:
        return cls(0xE67E22)
    @classmethod
    def dark_orange(cls) -> Self:
        return cls(0xA84300)
    @classmethod
    def brand_red(cls) -> Self:
        return cls(0xED4245)
    @classmethod
    def red(cls) -> Self:
        return cls(0xE74C3C)
    @classmethod
    def dark_red(cls) -> Self:
        return cls(0x992D22)
    @classmethod
    def lighter_grey(cls) -> Self:
        return cls(0x95A5A6)
    lighter_gray = lighter_grey
    @classmethod
    def dark_grey(cls) -> Self:
        return cls(0x607D8B)
    dark_gray = dark_grey
    @classmethod
    def light_grey(cls) -> Self:
        return cls(0x979C9F)
    light_gray = light_grey
    @classmethod
    def darker_grey(cls) -> Self:
        return cls(0x546E7A)
    darker_gray = darker_grey
    @classmethod
    def og_blurple(cls) -> Self:
        return cls(0x7289DA)
    @classmethod
    def blurple(cls) -> Self:
        return cls(0x5865F2)
    @classmethod
    def greyple(cls) -> Self:
        return cls(0x99AAB5)
    @classmethod
    def dark_theme(cls) -> Self:
        return cls(0x313338)
    @classmethod
    def fuchsia(cls) -> Self:
        return cls(0xEB459E)
    @classmethod
    def yellow(cls) -> Self:
        return cls(0xFEE75C)
    @classmethod
    def dark_embed(cls) -> Self:
        return cls(0x2B2D31)
    @classmethod
    def light_embed(cls) -> Self:
        return cls(0xEEEFF1)
    @classmethod
    def pink(cls) -> Self:
        return cls(0xEB459F)
Color = Colour