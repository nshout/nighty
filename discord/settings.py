from __future__ import annotations
import base64
import logging
import struct
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Collection, Dict, List, Literal, Optional, Sequence, Tuple, Type, Union, overload
from discord_protos import PreloadedUserSettings
from google.protobuf.json_format import MessageToDict, ParseDict
from .activity import CustomActivity
from .colour import Colour
from .enums import (
    EmojiPickerSection,
    HighlightLevel,
    InboxTab,
    Locale,
    NotificationLevel,
    SpoilerRenderOptions,
    Status,
    StickerAnimationOptions,
    StickerPickerSection,
    Theme,
    UserContentFilter,
    try_enum,
)
from .flags import FriendDiscoveryFlags, FriendSourceFlags, HubProgressFlags, OnboardingProgressFlags
from .object import Object
from .utils import MISSING, _get_as_snowflake, _ocast, find, parse_time, parse_timestamp, utcnow
if TYPE_CHECKING:
    from google.protobuf.message import Message
    from typing_extensions import Self
    from .abc import GuildChannel, Snowflake
    from .channel import DMChannel, GroupChannel
    from .guild import Guild
    from .state import ConnectionState
    from .types.user import (
        ConsentSettings as ConsentSettingsPayload,
        EmailSettings as EmailSettingsPayload,
        PartialConsentSettings as PartialConsentSettingsPayload,
        UserGuildSettings as UserGuildSettingsPayload,
        ChannelOverride as ChannelOverridePayload,
        MuteConfig as MuteConfigPayload,
    )
    from .user import ClientUser, User
    PrivateChannel = Union[DMChannel, GroupChannel]
__all__ = (
    'UserSettings',
    'GuildFolder',
    'GuildProgress',
    'AudioContext',
    'LegacyUserSettings',
    'MuteConfig',
    'ChannelSettings',
    'GuildSettings',
    'TrackingSettings',
    'EmailSettings',
)
_log = logging.getLogger(__name__)
class _ProtoSettings:
    __slots__ = (
        'state',
        'settings',
    )
    PROTOBUF_CLS: Type[Message] = MISSING
    settings: Any
    def __init__(self, state: ConnectionState, data: str):
        self.state: ConnectionState = state
        self._update(data)
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.settings == other.settings
        return False
    def __ne__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.settings != other.settings
        return True
    def _update(self, data: str, *, partial: bool = False):
        if partial:
            self.merge_from_base64(data)
        else:
            self.from_base64(data)
    @classmethod
    def _copy(cls, self: Self, /) -> Self:
        new = cls.__new__(cls)
        new.state = self.state
        new.settings = cls.PROTOBUF_CLS()
        new.settings.CopyFrom(self.settings)
        return new
    @overload
    def _get_guild(self, id: int, /, *, always_guild: Literal[True] = ...) -> Guild:
        ...
    @overload
    def _get_guild(self, id: int, /, *, always_guild: Literal[False] = ...) -> Union[Guild, Object]:
        ...
    def _get_guild(self, id: int, /, *, always_guild: bool = False) -> Union[Guild, Object]:
        id = int(id)
        if always_guild:
            return self.state._get_or_create_unavailable_guild(id)
        return self.state._get_guild(id) or Object(id=id)
    def to_dict(self, *, with_defaults: bool = False) -> Dict[str, Any]:
        return MessageToDict(
            self.settings,
            including_default_value_fields=with_defaults,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
    def dict_to_base64(self, data: Dict[str, Any]) -> str:
        message = ParseDict(data, self.PROTOBUF_CLS())
        return base64.b64encode(message.SerializeToString()).decode('ascii')
    def from_base64(self, data: str):
        self.settings = self.PROTOBUF_CLS().FromString(base64.b64decode(data))
    def merge_from_base64(self, data: str):
        self.settings.MergeFromString(base64.b64decode(data))
    def to_base64(self) -> str:
        return base64.b64encode(self.settings.SerializeToString()).decode('ascii')
class UserSettings(_ProtoSettings):
    __slots__ = ()
    PROTOBUF_CLS = PreloadedUserSettings
    SUPPORTED_CLIENT_VERSION = 17
    SUPPORTED_SERVER_VERSION = 0
    def __init__(self, *args):
        super().__init__(*args)
        if self.client_version < self.SUPPORTED_CLIENT_VERSION:
            _log.debug('PreloadedUserSettings client version is outdated, migration needed. Unexpected behaviour may occur.')
        if self.server_version > self.SUPPORTED_SERVER_VERSION:
            _log.debug('PreloadedUserSettings server version is newer than supported. Unexpected behaviour may occur.')
    @property
    def data_version(self) -> int:
        return self.settings.versions.data_version
    @property
    def client_version(self) -> int:
        return self.settings.versions.client_version
    @property
    def server_version(self) -> int:
        return self.settings.versions.server_version
    @property
    def inbox_tab(self) -> InboxTab:
        return try_enum(InboxTab, self.settings.inbox.current_tab)
    @property
    def inbox_tutorial_viewed(self) -> bool:
        return self.settings.inbox.viewed_tutorial
    @property
    def guild_progress_settings(self) -> List[GuildProgress]:
        state = self.state
        return [
            GuildProgress._from_settings(guild_id, data=settings, state=state)
            for guild_id, settings in self.settings.guilds.guilds.items()
        ]
    @property
    def dismissed_contents(self) -> Tuple[int, ...]:
        contents = self.settings.user_content.dismissed_contents
        return struct.unpack(f'>{len(contents)}B', contents)
    @property
    def last_dismissed_promotion_start_date(self) -> Optional[datetime]:
        return parse_time(self.settings.user_content.last_dismissed_outbound_promotion_start_date.value or None)
    @property
    def nitro_basic_modal_dismissed_at(self) -> Optional[datetime]:
        return (
            self.settings.user_content.premium_tier_0_modal_dismissed_at.ToDatetime(tzinfo=timezone.utc)
            if self.settings.user_content.HasField('premium_tier_0_modal_dismissed_at')
            else None
        )
    @property
    def always_preview_video(self) -> bool:
        return self.settings.voice_and_video.always_preview_video.value
    @property
    def afk_timeout(self) -> int:
        return self.settings.voice_and_video.afk_timeout.value or 600
    @property
    def stream_notifications_enabled(self) -> bool:
        return (
            self.settings.voice_and_video.stream_notifications_enabled.value
            if self.settings.voice_and_video.HasField('stream_notifications_enabled')
            else True
        )
    @property
    def native_phone_integration_enabled(self) -> bool:
        return (
            self.settings.voice_and_video.native_phone_integration_enabled.value
            if self.settings.voice_and_video.HasField('native_phone_integration_enabled')
            else True
        )
    @property
    def soundboard_volume(self) -> float:
        return (
            self.settings.voice_and_video.soundboard_settings.volume
            if self.settings.voice_and_video.HasField('soundboard_settings')
            else 100.0
        )
    @property
    def diversity_surrogate(self) -> Optional[str]:
        return self.settings.text_and_images.diversity_surrogate.value or None
    @property
    def use_thread_sidebar(self) -> bool:
        return (
            self.settings.text_and_images.use_thread_sidebar.value
            if self.settings.text_and_images.HasField('use_thread_sidebar')
            else True
        )
    @property
    def render_spoilers(self) -> SpoilerRenderOptions:
        return try_enum(SpoilerRenderOptions, self.settings.text_and_images.render_spoilers.value or 'ON_CLICK')
    @property
    def collapsed_emoji_picker_sections(self) -> Tuple[Union[EmojiPickerSection, Guild], ...]:
        return tuple(
            self._get_guild(section, always_guild=True) if section.isdigit() else try_enum(EmojiPickerSection, section)
            for section in self.settings.text_and_images.emoji_picker_collapsed_sections
        )
    @property
    def collapsed_sticker_picker_sections(self) -> Tuple[Union[StickerPickerSection, Guild, Object], ...]:
        return tuple(
            self._get_guild(section, always_guild=False) if section.isdigit() else try_enum(StickerPickerSection, section)
            for section in self.settings.text_and_images.sticker_picker_collapsed_sections
        )
    @property
    def view_image_descriptions(self) -> bool:
        return self.settings.text_and_images.view_image_descriptions.value
    @property
    def show_command_suggestions(self) -> bool:
        return (
            self.settings.text_and_images.show_command_suggestions.value
            if self.settings.text_and_images.HasField('show_command_suggestions')
            else True
        )
    @property
    def inline_attachment_media(self) -> bool:
        return (
            self.settings.text_and_images.inline_attachment_media.value
            if self.settings.text_and_images.HasField('inline_attachment_media')
            else True
        )
    @property
    def inline_embed_media(self) -> bool:
        return (
            self.settings.text_and_images.inline_embed_media.value
            if self.settings.text_and_images.HasField('inline_embed_media')
            else True
        )
    @property
    def gif_auto_play(self) -> bool:
        return (
            self.settings.text_and_images.gif_auto_play.value
            if self.settings.text_and_images.HasField('gif_auto_play')
            else True
        )
    @property
    def render_embeds(self) -> bool:
        return (
            self.settings.text_and_images.render_embeds.value
            if self.settings.text_and_images.HasField('render_embeds')
            else True
        )
    @property
    def render_reactions(self) -> bool:
        return (
            self.settings.text_and_images.render_reactions.value
            if self.settings.text_and_images.HasField('render_reactions')
            else True
        )
    @property
    def animate_emojis(self) -> bool:
        return (
            self.settings.text_and_images.animate_emoji.value
            if self.settings.text_and_images.HasField('animate_emoji')
            else True
        )
    @property
    def animate_stickers(self) -> StickerAnimationOptions:
        return try_enum(StickerAnimationOptions, self.settings.text_and_images.animate_stickers.value)
    @property
    def enable_tts_command(self) -> bool:
        return (
            self.settings.text_and_images.enable_tts_command.value
            if self.settings.text_and_images.HasField('enable_tts_command')
            else True
        )
    @property
    def message_display_compact(self) -> bool:
        return self.settings.text_and_images.message_display_compact.value
    @property
    def explicit_content_filter(self) -> UserContentFilter:
        return try_enum(
            UserContentFilter,
            self.settings.text_and_images.explicit_content_filter.value
            if self.settings.text_and_images.HasField('explicit_content_filter')
            else 1,
        )
    @property
    def view_nsfw_guilds(self) -> bool:
        return self.settings.text_and_images.view_nsfw_guilds.value
    @property
    def convert_emoticons(self) -> bool:
        r
        return (
            self.settings.text_and_images.convert_emoticons.value
            if self.settings.text_and_images.HasField('convert_emoticons')
            else True
        )
    @property
    def show_expression_suggestions(self) -> bool:
        return (
            self.settings.text_and_images.expression_suggestions_enabled.value
            if self.settings.text_and_images.HasField('expression_suggestions_enabled')
            else True
        )
    @property
    def view_nsfw_commands(self) -> bool:
        return self.settings.text_and_images.view_nsfw_commands.value
    @property
    def use_legacy_chat_input(self) -> bool:
        return self.settings.text_and_images.use_legacy_chat_input.value
    @property
    def in_app_notifications(self) -> bool:
        return (
            self.settings.notifications.show_in_app_notifications.value
            if self.settings.notifications.HasField('show_in_app_notifications')
            else True
        )
    @property
    def send_stream_notifications(self) -> bool:
        return self.settings.notifications.notify_friends_on_go_live.value
    @property
    def notification_center_acked_before_id(self) -> int:
        return self.settings.notifications.notification_center_acked_before_id
    @property
    def allow_activity_friend_joins(self) -> bool:
        return (
            self.settings.privacy.allow_activity_party_privacy_friends.value
            if self.settings.privacy.HasField('allow_activity_party_privacy_friends')
            else True
        )
    @property
    def allow_activity_voice_channel_joins(self) -> bool:
        return (
            self.settings.privacy.allow_activity_party_privacy_voice_channel.value
            if self.settings.privacy.HasField('allow_activity_party_privacy_voice_channel')
            else True
        )
    @property
    def restricted_guilds(self) -> List[Guild]:
        return list(map(self._get_guild, self.settings.privacy.restricted_guild_ids))
    @property
    def default_guilds_restricted(self) -> bool:
        return self.settings.privacy.default_guilds_restricted
    @property
    def allow_accessibility_detection(self) -> bool:
        return self.settings.privacy.allow_accessibility_detection
    @property
    def detect_platform_accounts(self) -> bool:
        return (
            self.settings.privacy.detect_platform_accounts.value
            if self.settings.privacy.HasField('detect_platform_accounts')
            else True
        )
    @property
    def passwordless(self) -> bool:
        return self.settings.privacy.passwordless.value if self.settings.privacy.HasField('passwordless') else True
    @property
    def contact_sync_enabled(self) -> bool:
        return self.settings.privacy.contact_sync_enabled.value
    @property
    def friend_source_flags(self) -> FriendSourceFlags:
        return (
            FriendSourceFlags._from_value(self.settings.privacy.friend_source_flags.value)
            if self.settings.privacy.HasField('friend_source_flags')
            else FriendSourceFlags.all()
        )
    @property
    def friend_discovery_flags(self) -> FriendDiscoveryFlags:
        return FriendDiscoveryFlags._from_value(self.settings.privacy.friend_discovery_flags.value)
    @property
    def activity_restricted_guilds(self) -> List[Guild]:
        return list(map(self._get_guild, self.settings.privacy.activity_restricted_guild_ids))
    @property
    def default_guilds_activity_restricted(self) -> bool:
        return self.settings.privacy.default_guilds_activity_restricted
    @property
    def activity_joining_restricted_guilds(self) -> List[Guild]:
        return list(map(self._get_guild, self.settings.privacy.activity_joining_restricted_guild_ids))
    @property
    def message_request_restricted_guilds(self) -> List[Guild]:
        return list(map(self._get_guild, self.settings.privacy.message_request_restricted_guild_ids))
    @property
    def default_message_request_restricted(self) -> bool:
        return self.settings.privacy.default_message_request_restricted.value
    @property
    def drops(self) -> bool:
        return not self.settings.privacy.drops_opted_out.value
    @property
    def non_spam_retraining(self) -> Optional[bool]:
        return (
            self.settings.privacy.non_spam_retraining_opt_in.value
            if self.settings.privacy.HasField('non_spam_retraining_opt_in')
            else None
        )
    @property
    def rtc_panel_show_voice_states(self) -> bool:
        return self.settings.debug.rtc_panel_show_voice_states.value
    @property
    def install_shortcut_desktop(self) -> bool:
        return self.settings.game_library.install_shortcut_desktop.value
    @property
    def install_shortcut_start_menu(self) -> bool:
        return (
            self.settings.game_library.install_shortcut_start_menu.value
            if self.settings.game_library.HasField('install_shortcut_start_menu')
            else True
        )
    @property
    def disable_games_tab(self) -> bool:
        return self.settings.game_library.disable_games_tab.value
    @property
    def status(self) -> Status:
        return try_enum(Status, self.settings.status.status.value or 'unknown')
    @property
    def custom_activity(self) -> Optional[CustomActivity]:
        return (
            CustomActivity._from_settings(data=self.settings.status.custom_status, state=self.state)
            if self.settings.status.HasField('custom_status')
            else None
        )
    @property
    def show_current_game(self) -> bool:
        return self.settings.status.show_current_game.value if self.settings.status.HasField('show_current_game') else True
    @property
    def locale(self) -> Locale:
        return try_enum(Locale, self.settings.localization.locale.value or 'en-US')
    @property
    def timezone_offset(self) -> int:
        return self.settings.localization.timezone_offset.value
    @property
    def theme(self) -> Theme:
        return Theme.from_int(self.settings.appearance.theme)
    @property
    def client_theme(self) -> Optional[Tuple[int, int, float]]:
        return (
            (
                self.settings.appearance.client_theme_settings.primary_color.value,
                self.settings.appearance.client_theme_settings.background_gradient_preset_id.value,
                self.settings.appearance.client_theme_settings.background_gradient_angle.value,
            )
            if self.settings.appearance.HasField('client_theme_settings')
            else None
        )
    @property
    def developer_mode(self) -> bool:
        return self.settings.appearance.developer_mode
    @property
    def disable_mobile_redesign(self) -> bool:
        return self.settings.appearance.mobile_redesign_disabled
    @property
    def guild_folders(self) -> List[GuildFolder]:
        state = self.state
        return [GuildFolder._from_settings(data=folder, state=state) for folder in self.settings.guild_folders.folders]
    @property
    def guild_positions(self) -> List[Guild]:
        return list(map(self._get_guild, self.settings.guild_folders.guild_positions))
    @property
    def user_audio_settings(self) -> List[AudioContext]:
        state = self.state
        return [
            AudioContext._from_settings(user_id, data=data, state=state)
            for user_id, data in self.settings.audio_context_settings.user.items()
        ]
    @property
    def stream_audio_settings(self) -> List[AudioContext]:
        state = self.state
        return [
            AudioContext._from_settings(stream_id, data=data, state=state)
            for stream_id, data in self.settings.audio_context_settings.stream.items()
        ]
    @property
    def home_auto_navigation(self) -> bool:
        return not self.settings.communities.disable_home_auto_nav.value
    @overload
    async def edit(self) -> Self:
        ...
    @overload
    async def edit(
        self,
        *,
        require_version: Union[bool, int] = False,
        client_version: int = ...,
        inbox_tab: InboxTab = ...,
        inbox_tutorial_viewed: bool = ...,
        guild_progress_settings: Sequence[GuildProgress] = ...,
        dismissed_contents: Sequence[int] = ...,
        last_dismissed_promotion_start_date: datetime = ...,
        nitro_basic_modal_dismissed_at: datetime = ...,
        soundboard_volume: float = ...,
        afk_timeout: int = ...,
        always_preview_video: bool = ...,
        native_phone_integration_enabled: bool = ...,
        stream_notifications_enabled: bool = ...,
        diversity_surrogate: Optional[str] = ...,
        render_spoilers: SpoilerRenderOptions = ...,
        collapsed_emoji_picker_sections: Sequence[Union[EmojiPickerSection, Snowflake]] = ...,
        collapsed_sticker_picker_sections: Sequence[Union[StickerPickerSection, Snowflake]] = ...,
        animate_emojis: bool = ...,
        animate_stickers: StickerAnimationOptions = ...,
        explicit_content_filter: UserContentFilter = ...,
        show_expression_suggestions: bool = ...,
        use_thread_sidebar: bool = ...,
        view_image_descriptions: bool = ...,
        show_command_suggestions: bool = ...,
        inline_attachment_media: bool = ...,
        inline_embed_media: bool = ...,
        gif_auto_play: bool = ...,
        render_embeds: bool = ...,
        render_reactions: bool = ...,
        enable_tts_command: bool = ...,
        message_display_compact: bool = ...,
        view_nsfw_guilds: bool = ...,
        convert_emoticons: bool = ...,
        view_nsfw_commands: bool = ...,
        use_legacy_chat_input: bool = ...,
        in_app_notifications: bool = ...,
        send_stream_notifications: bool = ...,
        notification_center_acked_before_id: int = ...,
        allow_activity_friend_joins: bool = ...,
        allow_activity_voice_channel_joins: bool = ...,
        friend_source_flags: FriendSourceFlags = ...,
        friend_discovery_flags: FriendDiscoveryFlags = ...,
        drops: bool = ...,
        non_spam_retraining: Optional[bool] = ...,
        restricted_guilds: Sequence[Snowflake] = ...,
        default_guilds_restricted: bool = ...,
        allow_accessibility_detection: bool = ...,
        detect_platform_accounts: bool = ...,
        passwordless: bool = ...,
        contact_sync_enabled: bool = ...,
        activity_restricted_guilds: Sequence[Snowflake] = ...,
        default_guilds_activity_restricted: bool = ...,
        activity_joining_restricted_guilds: Sequence[Snowflake] = ...,
        message_request_restricted_guilds: Sequence[Snowflake] = ...,
        default_message_request_restricted: bool = ...,
        rtc_panel_show_voice_states: bool = ...,
        install_shortcut_desktop: bool = ...,
        install_shortcut_start_menu: bool = ...,
        disable_games_tab: bool = ...,
        status: Status = ...,
        custom_activity: Optional[CustomActivity] = ...,
        show_current_game: bool = ...,
        locale: Locale = ...,
        timezone_offset: int = ...,
        theme: Theme = ...,
        client_theme: Optional[Tuple[int, int, float]] = ...,
        disable_mobile_redesign: bool = ...,
        developer_mode: bool = ...,
        guild_folders: Sequence[GuildFolder] = ...,
        guild_positions: Sequence[Snowflake] = ...,
        user_audio_settings: Collection[AudioContext] = ...,
        stream_audio_settings: Collection[AudioContext] = ...,
        home_auto_navigation: bool = ...,
    ) -> Self:
        ...
    async def edit(self, *, require_version: Union[bool, int] = False, **kwargs: Any) -> Self:
        r
        if not kwargs:
            raise TypeError('edit() missing at least 1 required keyword-only argument')
        versions = {}
        for field in ('data_version', 'client_version', 'server_version'):
            if field in kwargs:
                versions[field] = kwargs.pop(field)
        inbox = {}
        if 'inbox_tab' in kwargs:
            inbox['current_tab'] = _ocast(kwargs.pop('inbox_tab'), int)
        if 'inbox_tutorial_viewed' in kwargs:
            inbox['viewed_tutorial'] = kwargs.pop('inbox_tutorial_viewed')
        guilds = {}
        if 'guild_progress_settings' in kwargs and kwargs['guild_progress_settings'] is not MISSING:
            guilds['guilds'] = (
                {guild.guild_id: guild.to_dict() for guild in kwargs.pop('guild_progress_settings')}
                if kwargs['guild_progress_settings'] is not MISSING
                else MISSING
            )
        user_content = {}
        if 'dismissed_contents' in kwargs:
            contents = kwargs.pop('dismissed_contents')
            user_content['dismissed_contents'] = (
                struct.pack(f'>{len(contents)}B', *contents) if contents is not MISSING else MISSING
            )
        if 'last_dismissed_promotion_start_date' in kwargs:
            user_content['last_dismissed_outbound_promotion_start_date'] = (
                kwargs.pop('last_dismissed_promotion_start_date').isoformat()
                if kwargs['last_dismissed_promotion_start_date'] is not MISSING
                else MISSING
            )
        if 'nitro_basic_modal_dismissed_at' in kwargs:
            user_content['premium_tier_0_modal_dismissed_at'] = (
                kwargs.pop('nitro_basic_modal_dismissed_at').isoformat()
                if kwargs['nitro_basic_modal_dismissed_at'] is not MISSING
                else MISSING
            )
        voice_and_video = {}
        if 'soundboard_volume' in kwargs:
            voice_and_video['soundboard_settings'] = (
                {'volume': kwargs.pop('soundboard_volume')} if kwargs['soundboard_volume'] is not MISSING else {}
            )
        for field in (
            'afk_timeout',
            'always_preview_video',
            'native_phone_integration_enabled',
            'stream_notifications_enabled',
        ):
            if field in kwargs:
                voice_and_video[field] = kwargs.pop(field)
        text_and_images = {}
        if 'diversity_surrogate' in kwargs:
            text_and_images['diversity_surrogate'] = (
                kwargs.pop('diversity_surrogate') or '' if kwargs['diversity_surrogate'] is not MISSING else MISSING
            )
        if 'render_spoilers' in kwargs:
            text_and_images['render_spoilers'] = _ocast(kwargs.pop('render_spoilers'), str)
        if 'collapsed_emoji_picker_sections' in kwargs:
            text_and_images['emoji_picker_collapsed_sections'] = (
                [str(getattr(x, 'id', x)) for x in kwargs.pop('collapsed_emoji_picker_sections')]
                if kwargs['collapsed_emoji_picker_sections'] is not MISSING
                else MISSING
            )
        if 'collapsed_sticker_picker_sections' in kwargs:
            text_and_images['sticker_picker_collapsed_sections'] = (
                [str(getattr(x, 'id', x)) for x in kwargs.pop('collapsed_sticker_picker_sections')]
                if kwargs['collapsed_sticker_picker_sections'] is not MISSING
                else MISSING
            )
        if 'animate_emojis' in kwargs:
            text_and_images['animate_emoji'] = kwargs.pop('animate_emojis')
        if 'animate_stickers' in kwargs:
            text_and_images['animate_stickers'] = _ocast(kwargs.pop('animate_stickers'), int)
        if 'explicit_content_filter' in kwargs:
            text_and_images['explicit_content_filter'] = _ocast(kwargs.pop('explicit_content_filter'), int)
        if 'show_expression_suggestions' in kwargs:
            text_and_images['expression_suggestions_enabled'] = kwargs.pop('show_expression_suggestions')
        for field in (
            'use_thread_sidebar',
            'view_image_descriptions',
            'show_command_suggestions',
            'inline_attachment_media',
            'inline_embed_media',
            'gif_auto_play',
            'render_embeds',
            'render_reactions',
            'enable_tts_command',
            'message_display_compact',
            'view_nsfw_guilds',
            'convert_emoticons',
            'view_nsfw_commands',
            'use_legacy_chat_input',
            'use_rich_chat_input',
        ):
            if field in kwargs:
                text_and_images[field] = kwargs.pop(field)
        notifications = {}
        if 'in_app_notifications' in kwargs:
            notifications['show_in_app_notifications'] = kwargs.pop('in_app_notifications')
        if 'send_stream_notifications' in kwargs:
            notifications['notify_friends_on_go_live'] = kwargs.pop('send_stream_notifications')
        for field in ('notification_center_acked_before_id',):
            if field in kwargs:
                notifications[field] = kwargs.pop(field)
        privacy = {}
        if 'allow_activity_friend_joins' in kwargs:
            privacy['allow_activity_party_privacy_friends'] = kwargs.pop('allow_activity_friend_joins')
        if 'allow_activity_voice_channel_joins' in kwargs:
            privacy['allow_activity_party_privacy_voice_channel'] = kwargs.pop('allow_activity_voice_channel_joins')
        if 'friend_source_flags' in kwargs:
            privacy['friend_source_flags'] = (
                kwargs.pop('friend_source_flags').value if kwargs['friend_source_flags'] is not MISSING else MISSING
            )
        if 'friend_discovery_flags' in kwargs:
            privacy['friend_discovery_flags'] = (
                kwargs.pop('friend_discovery_flags').value if kwargs['friend_discovery_flags'] is not MISSING else MISSING
            )
        if 'drops' in kwargs:
            privacy['drops_opted_out'] = not kwargs.pop('drops') if kwargs['drops'] is not MISSING else MISSING
        if 'non_spam_retraining' in kwargs:
            privacy['non_spam_retraining_opt_in'] = (
                kwargs.pop('non_spam_retraining') if kwargs['non_spam_retraining'] not in {None, MISSING} else MISSING
            )
        for field in (
            'restricted_guilds',
            'default_guilds_restricted',
            'allow_accessibility_detection',
            'detect_platform_accounts',
            'passwordless',
            'contact_sync_enabled',
            'activity_restricted_guilds',
            'default_guilds_activity_restricted',
            'activity_joining_restricted_guilds',
            'message_request_restricted_guilds',
            'default_message_request_restricted',
        ):
            if field in kwargs:
                if field.endswith('_guilds'):
                    privacy[field.replace('_guilds', '_guild_ids')] = [g.id for g in kwargs.pop(field)]
                else:
                    privacy[field] = kwargs.pop(field)
        debug = {}
        for field in ('rtc_panel_show_voice_states',):
            if field in kwargs:
                debug[field] = kwargs.pop(field)
        game_library = {}
        for field in ('install_shortcut_desktop', 'install_shortcut_start_menu', 'disable_games_tab'):
            if field in kwargs:
                game_library[field] = kwargs.pop(field)
        status = {}
        if 'status' in kwargs:
            status['status'] = _ocast(kwargs.pop('status'), str)
        if 'custom_activity' in kwargs:
            status['custom_status'] = (
                kwargs.pop('custom_activity').to_settings_dict()
                if kwargs['custom_activity'] not in {MISSING, None}
                else MISSING
            )
        for field in ('show_current_game',):
            if field in kwargs:
                status[field] = kwargs.pop(field)
        localization = {}
        if 'locale' in kwargs:
            localization['locale'] = _ocast(kwargs.pop('locale'), str)
        for field in ('timezone_offset',):
            if field in kwargs:
                localization[field] = kwargs.pop(field)
        appearance = {}
        if 'theme' in kwargs:
            appearance['theme'] = _ocast(kwargs.pop('theme'), int)
        if 'client_theme' in kwargs:
            provided: tuple = kwargs.pop('client_theme')
            client_theme_settings = {} if provided is not MISSING else MISSING
            if provided:
                if provided[0] is not MISSING:
                    client_theme_settings['primary_color'] = provided[0]
                if len(provided) > 1 and provided[1] is not MISSING:
                    client_theme_settings['background_gradient_preset_id'] = provided[1]
                if len(provided) > 2 and provided[2] is not MISSING:
                    client_theme_settings['background_gradient_angle'] = float(provided[2])
                appearance['client_theme_settings'] = client_theme_settings
        if 'disable_mobile_redesign' in kwargs:
            appearance['mobile_redesign_disabled'] = kwargs.pop('disable_mobile_redesign')
        for field in ('developer_mode',):
            if field in kwargs:
                appearance[field] = kwargs.pop(field)
        guild_folders = {}
        if 'guild_folders' in kwargs:
            guild_folders['folders'] = (
                [f.to_dict() for f in kwargs.pop('guild_folders')] if kwargs['guild_folders'] is not MISSING else MISSING
            )
        if 'guild_positions' in kwargs:
            guild_folders['guild_positions'] = (
                [g.id for g in kwargs.pop('guild_positions')] if kwargs['guild_positions'] is not MISSING else MISSING
            )
        audio_context_settings = {}
        if 'user_audio_settings' in kwargs:
            audio_context_settings['user'] = (
                {s.id: s.to_dict() for s in kwargs.pop('user_audio_settings')}
                if kwargs['user_audio_settings'] is not MISSING
                else MISSING
            )
        if 'stream_audio_settings' in kwargs:
            audio_context_settings['stream'] = (
                {s.id: s.to_dict() for s in kwargs.pop('stream_audio_settings')}
                if kwargs['stream_audio_settings'] is not MISSING
                else MISSING
            )
        communities = {}
        if 'home_auto_navigation' in kwargs:
            communities['disable_home_auto_nav'] = (
                not kwargs.pop('home_auto_navigation') if kwargs['home_auto_navigation'] is not MISSING else MISSING
            )
        existing = self.to_dict()
        payload = {}
        for subsetting in (
            'versions',
            'inbox',
            'guilds',
            'user_content',
            'voice_and_video',
            'text_and_images',
            'notifications',
            'privacy',
            'debug',
            'game_library',
            'status',
            'localization',
            'appearance',
            'guild_folders',
            'audio_context_settings',
            'communities',
        ):
            subsetting_dict = locals()[subsetting]
            if subsetting_dict:
                original = existing.get(subsetting, {})
                original.update(subsetting_dict)
                for k, v in dict(original).items():
                    if v is MISSING:
                        del original[k]
                payload[subsetting] = original
        state = self.state
        require_version = self.data_version if require_version == True else require_version
        ret = await state.http.edit_proto_settings(1, self.dict_to_base64(payload), require_version or None)
        return UserSettings(state, ret['settings'])
class GuildFolder:
    __slots__ = ('state', 'id', 'name', '_colour', '_guild_ids')
    def __init__(
        self,
        *,
        id: Optional[int] = None,
        name: Optional[str] = None,
        colour: Optional[Colour] = None,
        color: Optional[Colour] = None,
        guilds: Sequence[Snowflake] = MISSING,
    ):
        self.state: Optional[ConnectionState] = None
        self.id: Optional[int] = id or None
        self.name: Optional[str] = name or None
        self._colour: Optional[int] = colour.value if colour else color.value if color else None
        self._guild_ids: List[int] = [guild.id for guild in guilds] if guilds else []
    def __str__(self) -> str:
        return self.name or ', '.join(guild.name for guild in [guild for guild in self.guilds if isinstance(guild, Guild)])
    def __repr__(self) -> str:
        return f'<GuildFolder id={self.id} name={self.name!r} guilds={self.guilds!r}>'
    def __len__(self) -> int:
        return len(self._guild_ids)
    @classmethod
    def _from_legacy_settings(cls, *, data: Dict[str, Any], state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self.id = _get_as_snowflake(data, 'id') or None
        self.name = data.get('name') or None
        self._colour = data.get('color')
        self._guild_ids = [int(guild_id) for guild_id in data['guild_ids']]
        return self
    @classmethod
    def _from_settings(cls, *, data: Any, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self.id = data.id.value or None
        self.name = data.name.value
        self._colour = data.color.value if data.HasField('color') else None
        self._guild_ids = data.guild_ids
        return self
    def _get_guild(self, id, /) -> Union[Guild, Object]:
        from .guild import Guild
        id = int(id)
        return self.state._get_or_create_unavailable_guild(id) if self.state else Object(id=id, type=Guild)
    def to_dict(self) -> dict:
        ret = {}
        if self.id is not None:
            ret['id'] = self.id
        if self.name is not None:
            ret['name'] = self.name
        if self._colour is not None:
            ret['color'] = self._colour
        ret['guild_ids'] = [str(guild_id) for guild_id in self._guild_ids]
        return ret
    def copy(self) -> Self:
        return self.__class__._from_legacy_settings(data=self.to_dict(), state=self.state)
    def add_guild(self, guild: Snowflake) -> Self:
        self._guild_ids.append(guild.id)
        return self
    def insert_guild_at(self, index: int, guild: Snowflake) -> Self:
        self._guild_ids.insert(index, guild.id)
        return self
    def clear_guilds(self) -> None:
        self._guild_ids.clear()
    def remove_guild(self, index: int) -> None:
        try:
            del self._guild_ids[index]
        except IndexError:
            pass
    def set_guild_at(self, index: int, guild: Snowflake) -> Self:
        self._guild_ids[index] = guild.id
        try:
            self._guild_ids[index] = guild.id
        except (TypeError, IndexError):
            raise IndexError('field index out of range')
        return self
    @property
    def guilds(self) -> List[Union[Guild, Object]]:
        return [self._get_guild(guild_id) for guild_id in self._guild_ids]
    @guilds.setter
    def guilds(self, value: Sequence[Snowflake]) -> None:
        self._guild_ids = [guild.id for guild in value]
    @property
    def colour(self) -> Optional[Colour]:
        return Colour(self._colour) if self._colour is not None else None
    @colour.setter
    def colour(self, value: Optional[Union[int, Colour]]) -> None:
        if value is None:
            self._colour = None
        elif isinstance(value, Colour):
            self._colour = value.value
        elif isinstance(value, int):
            self._colour = value
        else:
            raise TypeError(f'Expected discord.Colour, int, or None but received {value.__class__.__name__} instead.')
    @property
    def color(self) -> Optional[Colour]:
        return self.colour
    @color.setter
    def color(self, value: Optional[Union[int, Colour]]) -> None:
        self.colour = value
class GuildProgress:
    __slots__ = (
        'guild_id',
        '_hub_progress',
        '_onboarding_progress',
        'recents_dismissed_at',
        '_dismissed_contents',
        '_collapsed_channel_ids',
        'state',
    )
    def __init__(
        self,
        guild_id: int,
        *,
        hub_progress: HubProgressFlags,
        onboarding_progress: OnboardingProgressFlags,
        recents_dismissed_at: Optional[datetime] = None,
        dismissed_contents: Sequence[int] = MISSING,
        collapsed_channels: List[Snowflake] = MISSING,
    ) -> None:
        self.state: Optional[ConnectionState] = None
        self.guild_id = guild_id
        self._hub_progress = hub_progress.value
        self._onboarding_progress = onboarding_progress.value
        self.recents_dismissed_at: Optional[datetime] = recents_dismissed_at
        self._dismissed_contents = self._pack_dismissed_contents(dismissed_contents or [])
        self._collapsed_channel_ids = [channel.id for channel in collapsed_channels] or []
    def __repr__(self) -> str:
        return f'<GuildProgress guild_id={self.guild_id} hub_progress={self.hub_progress!r} onboarding_progress={self.onboarding_progress!r}>'
    @classmethod
    def _from_settings(cls, guild_id: int, *, data: Any, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self.guild_id = guild_id
        self._hub_progress = data.hub_progress
        self._onboarding_progress = data.guild_onboarding_progress
        self.recents_dismissed_at = (
            data.guild_recents_dismissed_at.ToDatetime(tzinfo=timezone.utc)
            if data.HasField('guild_recents_dismissed_at')
            else None
        )
        self._dismissed_contents = data.dismissed_guild_content
        self._collapsed_channel_ids = [
            channel_id for channel_id, settings in data.channels.items() if settings.collapsed_in_inbox
        ]
        return self
    def _get_channel(self, id: int, /) -> Union[GuildChannel, Object]:
        id = int(id)
        return self.guild.get_channel(id) or Object(id=id) if self.guild is not None else Object(id=id)
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'hub_progress': self._hub_progress,
            'guild_onboarding_progress': self._onboarding_progress,
            'dismissed_guild_content': self._dismissed_contents,
            'channels': {id: {'collapsed_in_inbox': True} for id in self._collapsed_channel_ids},
        }
        if self.recents_dismissed_at is not None:
            data['guild_recents_dismissed_at'] = self.recents_dismissed_at.isoformat()
        return data
    def copy(self) -> Self:
        cls = self.__class__(self.guild_id, hub_progress=self.hub_progress, onboarding_progress=self.onboarding_progress, recents_dismissed_at=self.recents_dismissed_at, dismissed_contents=self.dismissed_contents, collapsed_channels=self.collapsed_channels)
        cls.state = self.state
        return cls
    @property
    def guild(self) -> Optional[Guild]:
        return self.state._get_or_create_unavailable_guild(self.guild_id) if self.state is not None else None
    @property
    def hub_progress(self) -> HubProgressFlags:
        return HubProgressFlags._from_value(self._hub_progress)
    @hub_progress.setter
    def hub_progress(self, value: HubProgressFlags) -> None:
        self._hub_progress = value.value
    @property
    def onboarding_progress(self) -> OnboardingProgressFlags:
        return OnboardingProgressFlags._from_value(self._onboarding_progress)
    @onboarding_progress.setter
    def onboarding_progress(self, value: OnboardingProgressFlags) -> None:
        self._onboarding_progress = value.value
    @staticmethod
    def _pack_dismissed_contents(contents: Sequence[int]) -> bytes:
        return struct.pack(f'>{len(contents)}B', *contents)
    @property
    def dismissed_contents(self) -> Tuple[int, ...]:
        contents = self._dismissed_contents
        return struct.unpack(f'>{len(contents)}B', contents)
    @dismissed_contents.setter
    def dismissed_contents(self, value: Sequence[int]) -> None:
        self._dismissed_contents = self._pack_dismissed_contents(value)
    @property
    def collapsed_channels(self) -> List[Union[GuildChannel, Object]]:
        return list(map(self._get_channel, self._collapsed_channel_ids))
    @collapsed_channels.setter
    def collapsed_channels(self, value: Sequence[Snowflake]) -> None:
        self._collapsed_channel_ids = [channel.id for channel in value]
class AudioContext:
    __slots__ = ('state', 'user_id', 'muted', 'volume', 'modified_at')
    def __init__(self, user_id: int, *, muted: bool = False, volume: float) -> None:
        self.state: Optional[ConnectionState] = None
        self.user_id = user_id
        self.muted = muted
        self.volume = volume
        self.modified_at = utcnow()
    def __repr__(self) -> str:
        return (
            f'<AudioContext user_id={self.user_id} muted={self.muted} volume={self.volume} modified_at={self.modified_at!r}>'
        )
    @classmethod
    def _from_settings(cls, user_id: int, *, data: Any, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self.state = state
        self.user_id = user_id
        self.muted = data.muted
        self.volume = data.volume
        self.modified_at = parse_timestamp(data.modified_at)
        return self
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'muted': self.muted,
            'volume': self.volume,
            'modified_at': self.modified_at.isoformat(),
        }
    def copy(self) -> Self:
        cls = self.__class__(self.user_id, muted=self.muted, volume=self.volume)
        cls.modified_at = self.modified_at
        cls.state = self.state
        return cls
    @property
    def user(self) -> Optional[User]:
        return self.state.get_user(self.user_id) if self.state is not None else None
class LegacyUserSettings:
    if TYPE_CHECKING:
        afk_timeout: int
        allow_accessibility_detection: bool
        animate_emojis: bool
        contact_sync_enabled: bool
        convert_emoticons: bool
        default_guilds_restricted: bool
        detect_platform_accounts: bool
        developer_mode: bool
        disable_games_tab: bool
        enable_tts_command: bool
        gif_auto_play: bool
        inline_attachment_media: bool
        inline_embed_media: bool
        message_display_compact: bool
        native_phone_integration_enabled: bool
        render_embeds: bool
        render_reactions: bool
        show_current_game: bool
        stream_notifications_enabled: bool
        timezone_offset: int
        view_nsfw_commands: bool
        view_nsfw_guilds: bool
    def __init__(self, *, data, state: ConnectionState) -> None:
        self.state = state
        self._update(data)
    def __repr__(self) -> str:
        return '<LegacyUserSettings>'
    def _get_guild(self, id: int, /) -> Guild:
        return self.state._get_or_create_unavailable_guild(int(id))
    def _update(self, data: Dict[str, Any]) -> None:
        RAW_VALUES = {
            'afk_timeout',
            'allow_accessibility_detection',
            'animate_emojis',
            'contact_sync_enabled',
            'convert_emoticons',
            'default_guilds_restricted',
            'detect_platform_accounts',
            'developer_mode',
            'disable_games_tab',
            'enable_tts_command',
            'gif_auto_play',
            'inline_attachment_media',
            'inline_embed_media',
            'message_display_compact',
            'native_phone_integration_enabled',
            'render_embeds',
            'render_reactions',
            'show_current_game',
            'stream_notifications_enabled',
            'timezone_offset',
            'view_nsfw_commands',
            'view_nsfw_guilds',
        }
        for key, value in data.items():
            if key in RAW_VALUES:
                setattr(self, key, value)
            else:
                setattr(self, '_' + key, value)
    async def edit(self, **kwargs) -> Self:
        return await self.state.client.edit_legacy_settings(**kwargs)
    @property
    def activity_restricted_guilds(self) -> List[Guild]:
        return list(map(self._get_guild, getattr(self, '_activity_restricted_guild_ids', [])))
    @property
    def activity_joining_restricted_guilds(self) -> List[Guild]:
        return list(map(self._get_guild, getattr(self, '_activity_joining_restricted_guild_ids', [])))
    @property
    def animate_stickers(self) -> StickerAnimationOptions:
        return try_enum(StickerAnimationOptions, getattr(self, '_animate_stickers', 0))
    @property
    def custom_activity(self) -> Optional[CustomActivity]:
        return CustomActivity._from_legacy_settings(data=getattr(self, '_custom_status', None), state=self.state)
    @property
    def explicit_content_filter(self) -> UserContentFilter:
        return try_enum(UserContentFilter, getattr(self, '_explicit_content_filter', 0))
    @property
    def friend_source_flags(self) -> FriendSourceFlags:
        return FriendSourceFlags._from_dict(getattr(self, '_friend_source_flags', {'all': True}))
    @property
    def friend_discovery_flags(self) -> FriendDiscoveryFlags:
        return FriendDiscoveryFlags._from_value(getattr(self, '_friend_discovery_flags', 0))
    @property
    def guild_folders(self) -> List[GuildFolder]:
        state = self.state
        return [
            GuildFolder._from_legacy_settings(data=folder, state=state) for folder in getattr(self, '_guild_folders', [])
        ]
    @property
    def guild_positions(self) -> List[Guild]:
        return list(map(self._get_guild, getattr(self, '_guild_positions', [])))
    @property
    def locale(self) -> Locale:
        return try_enum(Locale, getattr(self, '_locale', 'en-US'))
    @property
    def passwordless(self) -> bool:
        return getattr(self, '_passwordless', False)
    @property
    def restricted_guilds(self) -> List[Guild]:
        return list(map(self._get_guild, getattr(self, '_restricted_guilds', [])))
    @property
    def status(self) -> Status:
        return try_enum(Status, getattr(self, '_status', 'online'))
    @property
    def theme(self) -> Theme:
        return try_enum(Theme, getattr(self, '_theme', 'dark'))
class MuteConfig:
    def __init__(self, muted: bool, config: Optional[MuteConfigPayload] = None) -> None:
        until = parse_time(config.get('end_time') if config else None)
        if until is not None:
            if until <= utcnow():
                muted = False
                until = None
        self.muted: bool = muted
        self.until: Optional[datetime] = until
    def __repr__(self) -> str:
        return str(self.muted)
    def __int__(self) -> int:
        return int(self.muted)
    def __bool__(self) -> bool:
        return self.muted
    def __eq__(self, other: object) -> bool:
        return self.muted == bool(other)
    def __ne__(self, other: object) -> bool:
        return not self.muted == bool(other)
class ChannelSettings:
    if TYPE_CHECKING:
        _channel_id: int
        level: NotificationLevel
        muted: MuteConfig
        collapsed: bool
    def __init__(self, guild_id: Optional[int] = None, *, data: ChannelOverridePayload, state: ConnectionState) -> None:
        self._guild_id = guild_id
        self.state = state
        self._update(data)
    def __repr__(self) -> str:
        return f'<ChannelSettings channel={self.channel} level={self.level} muted={self.muted} collapsed={self.collapsed}>'
    def _update(self, data: ChannelOverridePayload) -> None:
        self._channel_id = int(data['channel_id'])
        self.collapsed = data.get('collapsed', False)
        self.level = try_enum(NotificationLevel, data.get('message_notifications', 3))
        self.muted = MuteConfig(data.get('muted', False), data.get('mute_config'))
    @property
    def channel(self) -> Union[GuildChannel, PrivateChannel]:
        guild = self.state._get_or_create_unavailable_guild(self._guild_id) if self._guild_id else None
        if guild:
            channel = guild.get_channel(self._channel_id)
        else:
            channel = self.state._get_private_channel(self._channel_id)
        if not channel:
            channel = Object(id=self._channel_id)
        return channel
    async def edit(
        self,
        *,
        muted_until: Optional[Union[bool, datetime]] = MISSING,
        collapsed: bool = MISSING,
        level: NotificationLevel = MISSING,
    ) -> ChannelSettings:
        state = self.state
        guild_id = self._guild_id
        channel_id = self._channel_id
        payload = {}
        if muted_until is not MISSING:
            if not muted_until:
                payload['muted'] = False
            else:
                payload['muted'] = True
                if muted_until is True:
                    payload['mute_config'] = {'selected_time_window': -1, 'end_time': None}
                else:
                    if muted_until.tzinfo is None:
                        raise TypeError(
                            'muted_until must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                        )
                    mute_config = {
                        'selected_time_window': (muted_until - utcnow()).total_seconds(),
                        'end_time': muted_until.isoformat(),
                    }
                    payload['mute_config'] = mute_config
        if collapsed is not MISSING:
            payload['collapsed'] = collapsed
        if level is not MISSING:
            payload['message_notifications'] = level.value
        fields = {'channel_overrides': {str(channel_id): payload}}
        data = await state.http.edit_guild_settings(guild_id or '@me', fields)
        override = find(lambda x: x.get('channel_id') == str(channel_id), data['channel_overrides']) or {
            'channel_id': channel_id
        }
        return ChannelSettings(guild_id, data=override, state=state)
class GuildSettings:
    if TYPE_CHECKING:
        _channel_overrides: Dict[int, ChannelSettings]
        _guild_id: Optional[int]
        level: NotificationLevel
        muted: MuteConfig
        suppress_everyone: bool
        suppress_roles: bool
        hide_muted_channels: bool
        mobile_push: bool
        mute_scheduled_events: bool
        notify_highlights: HighlightLevel
        version: int
    def __init__(self, *, data: UserGuildSettingsPayload, state: ConnectionState) -> None:
        self.state = state
        self.version = -1
        self._update(data)
    def __repr__(self) -> str:
        return f'<GuildSettings guild={self.guild!r} level={self.level} muted={self.muted} suppress_everyone={self.suppress_everyone} suppress_roles={self.suppress_roles}>'
    def _update(self, data: UserGuildSettingsPayload) -> None:
        self._guild_id = guild_id = _get_as_snowflake(data, 'guild_id')
        self.level = try_enum(NotificationLevel, data.get('message_notifications', 3))
        self.suppress_everyone = data.get('suppress_everyone', False)
        self.suppress_roles = data.get('suppress_roles', False)
        self.hide_muted_channels = data.get('hide_muted_channels', False)
        self.mobile_push = data.get('mobile_push', True)
        self.mute_scheduled_events = data.get('mute_scheduled_events', False)
        self.notify_highlights = try_enum(HighlightLevel, data.get('notify_highlights', 0))
        self.version = data.get('version', self.version)
        self.muted = MuteConfig(data.get('muted', False), data.get('mute_config'))
        self._channel_overrides = overrides = {}
        state = self.state
        for override in data.get('channel_overrides', []):
            channel_id = int(override['channel_id'])
            overrides[channel_id] = ChannelSettings(guild_id, data=override, state=state)
    @property
    def guild(self) -> Union[Guild, ClientUser]:
        if self._guild_id:
            return self.state._get_or_create_unavailable_guild(self._guild_id)
        return self.state.user
    @property
    def channel_overrides(self) -> List[ChannelSettings]:
        return list(self._channel_overrides.values())
    async def edit(
        self,
        muted_until: Optional[Union[bool, datetime]] = MISSING,
        level: NotificationLevel = MISSING,
        suppress_everyone: bool = MISSING,
        suppress_roles: bool = MISSING,
        mobile_push: bool = MISSING,
        hide_muted_channels: bool = MISSING,
        mute_scheduled_events: bool = MISSING,
        notify_highlights: HighlightLevel = MISSING,
    ) -> Optional[GuildSettings]:
        payload = {}
        if muted_until is not MISSING:
            if not muted_until:
                payload['muted'] = False
            else:
                payload['muted'] = True
                if muted_until is not True:
                    if muted_until.tzinfo is None:
                        raise TypeError(
                            'muted_until must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                        )
                    mute_config = {
                        'selected_time_window': (muted_until - utcnow()).total_seconds(),
                        'end_time': muted_until.isoformat(),
                    }
                    payload['mute_config'] = mute_config
        if level is not MISSING:
            payload['message_notifications'] = level.value
        if suppress_everyone is not MISSING:
            payload['suppress_everyone'] = suppress_everyone
        if suppress_roles is not MISSING:
            payload['suppress_roles'] = suppress_roles
        if mobile_push is not MISSING:
            payload['mobile_push'] = mobile_push
        if hide_muted_channels is not MISSING:
            payload['hide_muted_channels'] = hide_muted_channels
        if mute_scheduled_events is not MISSING:
            payload['mute_scheduled_events'] = mute_scheduled_events
        if notify_highlights is not MISSING:
            payload['notify_highlights'] = notify_highlights.value
        data = await self.state.http.edit_guild_settings(self._guild_id or '@me', payload)
        return GuildSettings(data=data, state=self.state)
class TrackingSettings:
    __slots__ = ('state', 'personalization', 'usage_statistics')
    def __init__(
        self, *, data: Union[PartialConsentSettingsPayload, ConsentSettingsPayload], state: ConnectionState
    ) -> None:
        self.state = state
        self._update(data)
    def __repr__(self) -> str:
        return f'<TrackingSettings personalization={self.personalization} usage_statistics={self.usage_statistics}>'
    def __bool__(self) -> bool:
        return any((self.personalization, self.usage_statistics))
    def _update(self, data: Union[PartialConsentSettingsPayload, ConsentSettingsPayload]):
        self.personalization = data.get('personalization', {}).get('consented', False)
        self.usage_statistics = data.get('usage_statistics', {}).get('consented', False)
    @overload
    async def edit(self) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        personalization: bool = ...,
        usage_statistics: bool = ...,
    ) -> None:
        ...
    async def edit(self, **kwargs) -> None:
        payload = {
            'grant': [k for k, v in kwargs.items() if v is True],
            'revoke': [k for k, v in kwargs.items() if v is False],
        }
        data = await self.state.http.edit_tracking(payload)
        self._update(data)
class EmailSettings:
    __slots__ = (
        'state',
        'initialized',
        'communication',
        'social',
        'recommendations_and_events',
        'tips',
        'updates_and_announcements',
        'family_center_digest',
    )
    def __init__(self, *, data: EmailSettingsPayload, state: ConnectionState):
        self.state = state
        self._update(data)
    def __repr__(self) -> str:
        return f'<EmailSettings initialized={self.initialized}>'
    def _update(self, data: EmailSettingsPayload):
        self.initialized: bool = data.get('initialized', False)
        categories = data.get('categories', {})
        self.communication: bool = categories.get('communication', False)
        self.social: bool = categories.get('social', False)
        self.recommendations_and_events: bool = categories.get('recommendations_and_events', False)
        self.tips: bool = categories.get('tips', False)
        self.updates_and_announcements: bool = categories.get('updates_and_announcements', False)
        self.family_center_digest: bool = categories.get('family_center_digest', False)
    @overload
    async def edit(self) -> None:
        ...
    @overload
    async def edit(
        self,
        *,
        initialized: bool = MISSING,
        communication: bool = MISSING,
        social: bool = MISSING,
        recommendations_and_events: bool = MISSING,
        tips: bool = MISSING,
        updates_and_announcements: bool = MISSING,
    ) -> None:
        ...
    async def edit(self, **kwargs) -> None:
        payload = {}
        initialized = kwargs.pop('initialized', MISSING)
        if initialized is not MISSING:
            payload['initialized'] = initialized
        if kwargs:
            payload['categories'] = kwargs
        data = await self.state.http.edit_email_settings(**payload)
        self._update(data)