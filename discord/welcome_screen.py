from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Union
from .object import Object
from .partial_emoji import PartialEmoji
from .utils import _get_as_snowflake, MISSING
if TYPE_CHECKING:
    from .abc import Snowflake
    from .emoji import Emoji
    from .guild import Guild
    from .invite import PartialInviteGuild
    from .state import ConnectionState
    from .types.welcome_screen import (
        WelcomeScreen as WelcomeScreenPayload,
        WelcomeScreenChannel as WelcomeScreenChannelPayload,
    )
__all__ = (
    'WelcomeChannel',
    'WelcomeScreen',
)
class WelcomeChannel:
    def __init__(
        self, *, channel: Snowflake, description: str, emoji: Optional[Union[PartialEmoji, Emoji, str]] = None
    ) -> None:
        self.channel = channel
        self.description = description
        if isinstance(emoji, str):
            emoji = PartialEmoji(name=emoji)
        self.emoji = emoji
    def __repr__(self) -> str:
        return f'<WelcomeChannel channel={self.channel!r} description={self.description} emoji={self.emoji!r}>'
    @classmethod
    def _from_dict(cls, *, data: WelcomeScreenChannelPayload, state: ConnectionState) -> WelcomeChannel:
        channel_id = int(data['channel_id'])
        channel = state.get_channel(channel_id) or Object(id=channel_id)
        emoji = None
        if (emoji_id := _get_as_snowflake(data, 'emoji_id')) is not None:
            emoji = state.get_emoji(emoji_id)
        elif (emoji_name := data.get('emoji_name')) is not None:
            emoji = PartialEmoji(name=emoji_name)
        return cls(channel=channel, description=data.get('description', ''), emoji=emoji)
    def _to_dict(self) -> WelcomeScreenChannelPayload:
        data: WelcomeScreenChannelPayload = {
            'channel_id': self.channel.id,
            'description': self.description,
            'emoji_id': None,
            'emoji_name': None,
        }
        if (emoji := self.emoji) is not None:
            data['emoji_id'] = emoji.id
            data['emoji_name'] = emoji.name
        return data
class WelcomeScreen:
    def __init__(self, *, data: WelcomeScreenPayload, guild: Union[Guild, PartialInviteGuild]) -> None:
        self.guild = guild
        self._update(data)
    def _update(self, data: WelcomeScreenPayload) -> None:
        state = self.guild.state
        channels = data.get('welcome_channels', [])
        self.welcome_channels: List[WelcomeChannel] = [
            WelcomeChannel._from_dict(data=channel, state=state) for channel in channels
        ]
        self.description: str = data.get('description', '')
    def __repr__(self) -> str:
        return f'<WelcomeScreen enabled={self.enabled} description={self.description} welcome_channels={self.welcome_channels!r}>'
    def __bool__(self) -> bool:
        return self.enabled
    @property
    def enabled(self) -> bool:
        return 'WELCOME_SCREEN_ENABLED' in self.guild.features
    async def edit(
        self,
        *,
        description: str = MISSING,
        welcome_channels: List[WelcomeChannel] = MISSING,
        enabled: bool = MISSING,
        reason: Optional[str] = None,
    ):
        payload = {}
        if enabled is not MISSING:
            payload['enabled'] = enabled
        if description is not MISSING:
            payload['description'] = description
        if welcome_channels is not MISSING:
            channels = [channel._to_dict() for channel in welcome_channels] if welcome_channels else []
            payload['welcome_channels'] = channels
        if payload:
            guild = self.guild
            data = await guild.state.http.edit_welcome_screen(guild.id, payload, reason=reason)
            self._update(data)