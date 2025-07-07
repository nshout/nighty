from __future__ import annotations
import logging
import asyncio
import re
from urllib.parse import quote as urlquote
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING, Sequence, Tuple, Union, TypeVar, Type, overload
from contextvars import ContextVar
import weakref
import aiohttp
from .. import utils
from ..errors import HTTPException, Forbidden, NotFound, DiscordServerError
from ..message import Message
from ..enums import try_enum, WebhookType, ChannelType
from ..user import BaseUser, User
from ..flags import MessageFlags
from ..asset import Asset
from ..partial_emoji import PartialEmoji
from ..http import Route, handle_message_parameters, json_or_text, HTTPClient
from ..mixins import Hashable
from ..channel import TextChannel, ForumChannel, PartialMessageable
from ..file import File
__all__ = (
    'Webhook',
    'WebhookMessage',
    'PartialWebhookChannel',
    'PartialWebhookGuild',
)
_log = logging.getLogger(__name__)
if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType
    from ..embeds import Embed
    from ..client import Client
    from ..mentions import AllowedMentions
    from ..message import Attachment
    from ..state import ConnectionState
    from ..http import Response
    from ..guild import Guild
    from ..emoji import Emoji
    from ..channel import VoiceChannel
    from ..abc import Snowflake
    import datetime
    from ..types.webhook import (
        Webhook as WebhookPayload,
        SourceGuild as SourceGuildPayload,
        SourceChannel as SourceChannelPayload,
    )
    from ..types.message import (
        Message as MessagePayload,
    )
    from ..types.user import (
        User as UserPayload,
        PartialUser as PartialUserPayload,
    )
    from ..types.emoji import PartialEmoji as PartialEmojiPayload
    BE = TypeVar('BE', bound=BaseException)
    _State = Union[ConnectionState, '_WebhookState']
MISSING: Any = utils.MISSING
class AsyncDeferredLock:
    def __init__(self, lock: asyncio.Lock):
        self.lock = lock
        self.delta: Optional[float] = None
    async def __aenter__(self) -> Self:
        await self.lock.acquire()
        return self
    def delay_by(self, delta: float) -> None:
        self.delta = delta
    async def __aexit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.delta:
            await asyncio.sleep(self.delta)
        self.lock.release()
class AsyncWebhookAdapter:
    def __init__(self):
        self._locks: weakref.WeakValueDictionary[Any, asyncio.Lock] = weakref.WeakValueDictionary()
    async def request(
        self,
        route: Route,
        session: aiohttp.ClientSession,
        *,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        files: Optional[Sequence[File]] = None,
        reason: Optional[str] = None,
        auth_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        headers: Dict[str, str] = {}
        files = files or []
        to_send: Optional[Union[str, aiohttp.FormData]] = None
        bucket = (route.webhook_id, route.webhook_token)
        try:
            lock = self._locks[bucket]
        except KeyError:
            self._locks[bucket] = lock = asyncio.Lock()
        if payload is not None:
            headers['Content-Type'] = 'application/json'
            to_send = utils._to_json(payload)
        if auth_token is not None:
            headers['Authorization'] = f'{auth_token}'
        if reason is not None:
            headers['X-Audit-Log-Reason'] = urlquote(reason)
        response: Optional[aiohttp.ClientResponse] = None
        data: Optional[Union[Dict[str, Any], str]] = None
        method = route.method
        url = route.url
        webhook_id = route.webhook_id
        async with AsyncDeferredLock(lock) as lock:
            for attempt in range(5):
                for file in files:
                    file.reset(seek=attempt)
                if multipart:
                    form_data = aiohttp.FormData(quote_fields=False)
                    for p in multipart:
                        form_data.add_field(**p)
                    to_send = form_data
                try:
                    async with session.request(
                        method, url, data=to_send, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        _log.debug(
                            'Webhook ID %s with %s %s has returned status code %s.',
                            webhook_id,
                            method,
                            url,
                            response.status,
                        )
                        data = await json_or_text(response)
                        remaining = response.headers.get('X-Ratelimit-Remaining')
                        if remaining == '0' and response.status != 429:
                            delta = utils._parse_ratelimit_header(response)
                            _log.debug(
                                'Webhook ID %s has exhausted its rate limit bucket (retry: %s).',
                                webhook_id,
                                delta,
                            )
                            lock.delay_by(delta)
                        if 300 > response.status >= 200:
                            return data
                        if response.status == 429:
                            if not response.headers.get('Via'):
                                raise HTTPException(response, data)
                            fmt = 'Webhook ID %s is rate limited. Retrying in %.2f seconds.'
                            retry_after: float = data['retry_after']
                            _log.warning(fmt, webhook_id, retry_after)
                            await asyncio.sleep(retry_after)
                            continue
                        if response.status >= 500:
                            await asyncio.sleep(1 + attempt * 2)
                            continue
                        if response.status == 403:
                            raise Forbidden(response, data)
                        elif response.status == 404:
                            raise NotFound(response, data)
                        else:
                            raise HTTPException(response, data)
                except OSError as e:
                    if attempt < 4 and e.errno in (54, 10054):
                        await asyncio.sleep(1 + attempt * 2)
                        continue
                    raise
            if response:
                if response.status >= 500:
                    raise DiscordServerError(response, data)
                raise HTTPException(response, data)
            raise RuntimeError('Unreachable code in HTTP handling.')
    def delete_webhook(
        self,
        webhook_id: int,
        *,
        token: Optional[str] = None,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        reason: Optional[str] = None,
    ) -> Response[None]:
        route = Route('DELETE', '/webhooks/{webhook_id}', webhook_id=webhook_id)
        return self.request(route, session=session, proxy=proxy, proxy_auth=proxy_auth, reason=reason, auth_token=token)
    def delete_webhook_with_token(
        self,
        webhook_id: int,
        token: str,
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        reason: Optional[str] = None,
    ) -> Response[None]:
        route = Route('DELETE', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(route, session=session, proxy=proxy, proxy_auth=proxy_auth, reason=reason)
    def edit_webhook(
        self,
        webhook_id: int,
        token: str,
        payload: Dict[str, Any],
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        reason: Optional[str] = None,
    ) -> Response[WebhookPayload]:
        route = Route('PATCH', '/webhooks/{webhook_id}', webhook_id=webhook_id)
        return self.request(
            route,
            session=session,
            proxy=proxy,
            proxy_auth=proxy_auth,
            reason=reason,
            payload=payload,
            auth_token=token,
        )
    def edit_webhook_with_token(
        self,
        webhook_id: int,
        token: str,
        payload: Dict[str, Any],
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        reason: Optional[str] = None,
    ) -> Response[WebhookPayload]:
        route = Route('PATCH', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(route, session=session, proxy=proxy, proxy_auth=proxy_auth, reason=reason, payload=payload)
    def execute_webhook(
        self,
        webhook_id: int,
        token: str,
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[Sequence[File]] = None,
        thread_id: Optional[int] = None,
        wait: bool = False,
    ) -> Response[Optional[MessagePayload]]:
        params = {'wait': int(wait)}
        if thread_id:
            params['thread_id'] = thread_id
        route = Route('POST', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(
            route,
            session=session,
            proxy=proxy,
            proxy_auth=proxy_auth,
            payload=payload,
            multipart=multipart,
            files=files,
            params=params,
        )
    def get_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        thread_id: Optional[int] = None,
    ) -> Response[MessagePayload]:
        route = Route(
            'GET',
            '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=webhook_id,
            webhook_token=token,
            message_id=message_id,
        )
        params = None if thread_id is None else {'thread_id': thread_id}
        return self.request(route, session=session, proxy=proxy, proxy_auth=proxy_auth, params=params)
    def edit_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[Sequence[File]] = None,
        thread_id: Optional[int] = None,
    ) -> Response[Message]:
        route = Route(
            'PATCH',
            '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=webhook_id,
            webhook_token=token,
            message_id=message_id,
        )
        params = None if thread_id is None else {'thread_id': thread_id}
        return self.request(
            route,
            session=session,
            proxy=proxy,
            proxy_auth=proxy_auth,
            payload=payload,
            multipart=multipart,
            files=files,
            params=params,
        )
    def delete_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        thread_id: Optional[int] = None,
    ) -> Response[None]:
        route = Route(
            'DELETE',
            '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=webhook_id,
            webhook_token=token,
            message_id=message_id,
        )
        params = None if thread_id is None else {'thread_id': thread_id}
        return self.request(route, session=session, proxy=proxy, proxy_auth=proxy_auth, params=params)
    def fetch_webhook(
        self,
        webhook_id: int,
        token: str,
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
    ) -> Response[WebhookPayload]:
        route = Route('GET', '/webhooks/{webhook_id}', webhook_id=webhook_id)
        return self.request(route, session=session, proxy=proxy, proxy_auth=proxy_auth, auth_token=token)
    def fetch_webhook_with_token(
        self,
        webhook_id: int,
        token: str,
        *,
        session: aiohttp.ClientSession,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
    ) -> Response[WebhookPayload]:
        route = Route('GET', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(route, session=session, proxy=proxy, proxy_auth=proxy_auth)
async_context: ContextVar[AsyncWebhookAdapter] = ContextVar('async_webhook_context', default=AsyncWebhookAdapter())
class PartialWebhookChannel(Hashable):
    __slots__ = ('id', 'name')
    def __init__(self, *, data: SourceChannelPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
    def __repr__(self) -> str:
        return f'<PartialWebhookChannel name={self.name!r} id={self.id}>'
class PartialWebhookGuild(Hashable):
    __slots__ = ('id', 'name', '_icon', '_state')
    def __init__(self, *, data: SourceGuildPayload, state: _State) -> None:
        self._state: _State = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: str = data['icon']
    def __repr__(self) -> str:
        return f'<PartialWebhookGuild name={self.name!r} id={self.id}>'
    @property
    def icon(self) -> Optional[Asset]:
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self._state, self.id, self._icon)
class _FriendlyHttpAttributeErrorHelper:
    __slots__ = ()
    def __getattr__(self, attr: str) -> Any:
        raise AttributeError('PartialWebhookState does not support http methods.')
class _WebhookState:
    __slots__ = ('_parent', '_webhook', '_thread')
    def __init__(self, webhook: Any, parent: Optional[_State], thread: Snowflake = MISSING):
        self._webhook: Any = webhook
        self._parent: Optional[ConnectionState]
        if isinstance(parent, _WebhookState):
            self._parent = None
        else:
            self._parent = parent
        self._thread: Snowflake = thread
    def _get_guild(self, guild_id: Optional[int]) -> Optional[Guild]:
        if self._parent is not None:
            return self._parent._get_guild(guild_id)
        return None
    def store_user(self, data: Union[UserPayload, PartialUserPayload], *, cache: bool = True) -> BaseUser:
        if self._parent is not None:
            return self._parent.store_user(data, cache=cache)
        return BaseUser(state=self, data=data)
    def create_user(self, data: Union[UserPayload, PartialUserPayload]) -> BaseUser:
        return BaseUser(state=self, data=data)
    @property
    def allowed_mentions(self) -> Optional[AllowedMentions]:
        return None
    def get_reaction_emoji(self, data: PartialEmojiPayload) -> Union[PartialEmoji, Emoji, str]:
        if self._parent is not None:
            return self._parent.get_reaction_emoji(data)
        emoji_id = utils._get_as_snowflake(data, 'id')
        if not emoji_id:
            return data['name']
        return PartialEmoji(animated=data.get('animated', False), id=emoji_id, name=data['name'])
    @property
    def http(self) -> Union[HTTPClient, _FriendlyHttpAttributeErrorHelper]:
        if self._parent is not None:
            return self._parent.http
        return _FriendlyHttpAttributeErrorHelper()
    def __getattr__(self, attr: str) -> Any:
        if self._parent is not None:
            return getattr(self._parent, attr)
        raise AttributeError(f'PartialWebhookState does not support {attr!r}')
class WebhookMessage(Message):
    _state: _WebhookState
    async def edit(
        self,
        content: Optional[str] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
    ) -> WebhookMessage:
        return await self._state._webhook.edit_message(
            self.id,
            content=content,
            embeds=embeds,
            embed=embed,
            attachments=attachments,
            allowed_mentions=allowed_mentions,
            thread=self._state._thread,
        )
    async def add_files(self, *files: File) -> WebhookMessage:
        r
        return await self.edit(attachments=[*self.attachments, *files])
    async def remove_attachments(self, *attachments: Attachment) -> WebhookMessage:
        r
        return await self.edit(attachments=[a for a in self.attachments if a not in attachments])
    async def delete(self, *, delay: Optional[float] = None) -> None:
        if delay is not None:
            async def inner_call(delay: float = delay):
                await asyncio.sleep(delay)
                try:
                    await self._state._webhook.delete_message(self.id, thread=self._state._thread)
                except HTTPException:
                    pass
            asyncio.create_task(inner_call())
        else:
            await self._state._webhook.delete_message(self.id, thread=self._state._thread)
class BaseWebhook(Hashable):
    __slots__: Tuple[str, ...] = (
        'id',
        'type',
        'guild_id',
        'channel_id',
        'token',
        'auth_token',
        'user',
        'name',
        '_avatar',
        'source_channel',
        'source_guild',
        '_state',
    )
    def __init__(
        self,
        data: WebhookPayload,
        token: Optional[str] = None,
        state: Optional[_State] = None,
    ) -> None:
        self.auth_token: Optional[str] = token
        self._state: _State = state or _WebhookState(self, parent=state)
        self._update(data)
    def _update(self, data: WebhookPayload) -> None:
        self.id: int = int(data['id'])
        self.type: WebhookType = try_enum(WebhookType, int(data['type']))
        self.channel_id: Optional[int] = utils._get_as_snowflake(data, 'channel_id')
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.name: Optional[str] = data.get('name')
        self._avatar: Optional[str] = data.get('avatar')
        self.token: Optional[str] = data.get('token')
        user = data.get('user')
        self.user: Optional[Union[BaseUser, User]] = None
        if user is not None:
            self.user = User(state=self._state, data=user)
        source_channel = data.get('source_channel')
        if source_channel:
            source_channel = PartialWebhookChannel(data=source_channel)
        self.source_channel: Optional[PartialWebhookChannel] = source_channel
        source_guild = data.get('source_guild')
        if source_guild:
            source_guild = PartialWebhookGuild(data=source_guild, state=self._state)
        self.source_guild: Optional[PartialWebhookGuild] = source_guild
    def is_partial(self) -> bool:
        return self.channel_id is None
    def is_authenticated(self) -> bool:
        return self.auth_token is not None
    @property
    def guild(self) -> Optional[Guild]:
        return self._state and self._state._get_guild(self.guild_id)
    @property
    def channel(self) -> Optional[Union[ForumChannel, VoiceChannel, TextChannel]]:
        guild = self.guild
        return guild and guild.get_channel(self.channel_id)
    @property
    def created_at(self) -> datetime.datetime:
        return utils.snowflake_time(self.id)
    @property
    def avatar(self) -> Optional[Asset]:
        if self._avatar is not None:
            return Asset._from_avatar(self._state, self.id, self._avatar)
        return None
    @property
    def default_avatar(self) -> Asset:
        return Asset._from_default_avatar(self._state, 0)
    @property
    def display_avatar(self) -> Asset:
        return self.avatar or self.default_avatar
class Webhook(BaseWebhook):
    __slots__: Tuple[str, ...] = ('session', 'proxy', 'proxy_auth')
    def __init__(
        self,
        data: WebhookPayload,
        session: aiohttp.ClientSession,
        token: Optional[str] = None,
        state: Optional[_State] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
    ) -> None:
        super().__init__(data, token, state)
        self.session: aiohttp.ClientSession = session
        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[aiohttp.BasicAuth] = proxy_auth
    def __repr__(self) -> str:
        return f'<Webhook id={self.id!r}>'
    @property
    def url(self) -> str:
        return f'https://discord.com/api/webhooks/{self.id}/{self.token}'
    @classmethod
    def partial(
        cls,
        id: int,
        token: str,
        *,
        session: aiohttp.ClientSession = MISSING,
        client: Client = MISSING,
        user_token: Optional[str] = None,
    ) -> Self:
        data: WebhookPayload = {
            'id': id,
            'type': 1,
            'token': token,
        }
        state = None
        if client is not MISSING:
            state = client._connection
            if session is MISSING:
                session = client.http._HTTPClient__session
        if session is MISSING:
            raise TypeError('session or client must be given')
        return cls(data, session, token=user_token, state=state)
    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        session: aiohttp.ClientSession = MISSING,
        client: Client = MISSING,
        user_token: Optional[str] = None,
    ) -> Self:
        m = re.search(r'discord(?:app)?\.com/api/webhooks/(?P<id>[0-9]{17,20})/(?P<token>[A-Za-z0-9\.\-\_]{60,})', url)
        if m is None:
            raise ValueError('Invalid webhook URL given')
        state = None
        if client is not MISSING:
            state = client._connection
            if session is MISSING:
                session = client.http._HTTPClient__session
        if session is MISSING:
            raise TypeError('session or client must be given')
        data: Dict[str, Any] = m.groupdict()
        data['type'] = 1
        return cls(data, session, token=user_token, state=state)
    @classmethod
    def _as_follower(cls, data, *, channel, user) -> Self:
        name = f"{channel.guild}
        feed: WebhookPayload = {
            'id': data['webhook_id'],
            'type': 2,
            'name': name,
            'channel_id': channel.id,
            'guild_id': channel.guild.id,
            'user': user._to_minimal_user_json(),
        }
        state = channel._state
        http = state.http
        session = http._HTTPClient__session
        proxy_auth = http.proxy_auth
        proxy = http.proxy
        return cls(feed, session=session, state=state, proxy_auth=proxy_auth, proxy=proxy, token=state.http.token)
    @classmethod
    def from_state(cls, data: WebhookPayload, state: ConnectionState) -> Self:
        http = state.http
        session = http._HTTPClient__session
        proxy_auth = http.proxy_auth
        proxy = http.proxy
        return cls(data, session=session, state=state, proxy_auth=proxy_auth, proxy=proxy, token=state.http.token)
    async def fetch(self, *, prefer_auth: bool = True) -> Webhook:
        adapter = async_context.get()
        if prefer_auth and self.auth_token:
            data = await adapter.fetch_webhook(
                self.id,
                self.auth_token,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
            )
        elif self.token:
            data = await adapter.fetch_webhook_with_token(
                self.id,
                self.token,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
            )
        else:
            raise ValueError('This webhook does not have a token associated with it')
        return Webhook(
            data,
            session=self.session,
            proxy=self.proxy,
            proxy_auth=self.proxy_auth,
            token=self.auth_token,
            state=self._state,
        )
    async def delete(self, *, reason: Optional[str] = None, prefer_auth: bool = True) -> None:
        if self.token is None and self.auth_token is None:
            raise ValueError('This webhook does not have a token associated with it')
        adapter = async_context.get()
        if prefer_auth and self.auth_token:
            await adapter.delete_webhook(
                self.id,
                token=self.auth_token,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                reason=reason,
            )
        elif self.token:
            await adapter.delete_webhook_with_token(
                self.id,
                self.token,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                reason=reason,
            )
    async def edit(
        self,
        *,
        reason: Optional[str] = None,
        name: Optional[str] = MISSING,
        avatar: Optional[bytes] = MISSING,
        channel: Optional[Snowflake] = None,
        prefer_auth: bool = True,
    ) -> Webhook:
        if self.token is None and self.auth_token is None:
            raise ValueError('This webhook does not have a token associated with it')
        payload = {}
        if name is not MISSING:
            payload['name'] = str(name) if name is not None else None
        if avatar is not MISSING:
            payload['avatar'] = utils._bytes_to_base64_data(avatar) if avatar is not None else None
        adapter = async_context.get()
        data: Optional[WebhookPayload] = None
        if channel is not None:
            if self.auth_token is None:
                raise ValueError('Editing channel requires authenticated webhook')
            payload['channel_id'] = channel.id
            data = await adapter.edit_webhook(
                self.id,
                self.auth_token,
                payload=payload,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                reason=reason,
            )
        elif prefer_auth and self.auth_token:
            data = await adapter.edit_webhook(
                self.id,
                self.auth_token,
                payload=payload,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                reason=reason,
            )
        elif self.token:
            data = await adapter.edit_webhook_with_token(
                self.id,
                self.token,
                payload=payload,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                reason=reason,
            )
        if data is None:
            raise RuntimeError('Unreachable code hit: data was not assigned')
        return Webhook(
            data,
            session=self.session,
            proxy=self.proxy,
            proxy_auth=self.proxy_auth,
            token=self.auth_token,
            state=self._state,
        )
    def _create_message(self, data, *, thread: Snowflake):
        state = _WebhookState(self, parent=self._state, thread=thread)
        if thread is MISSING:
            channel_id = int(data['channel_id'])
            channel = self.channel
            if self.channel_id != channel_id:
                type = ChannelType.public_thread if isinstance(channel, ForumChannel) else (channel and channel.type)
                channel = PartialMessageable(state=self._state, guild_id=self.guild_id, id=channel_id, type=type)
            else:
                channel = self.channel or PartialMessageable(state=self._state, guild_id=self.guild_id, id=channel_id)
        else:
            channel = self.channel
            if isinstance(channel, (ForumChannel, TextChannel)):
                channel = channel.get_thread(thread.id)
            if channel is None:
                channel = PartialMessageable(state=self._state, guild_id=self.guild_id, id=int(data['channel_id']))
        return WebhookMessage(data=data, state=state, channel=channel)
    @overload
    async def send(
        self,
        content: str = MISSING,
        *,
        username: str = MISSING,
        avatar_url: Any = MISSING,
        tts: bool = MISSING,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
        embed: Embed = MISSING,
        embeds: Sequence[Embed] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        thread: Snowflake = MISSING,
        thread_name: str = MISSING,
        wait: Literal[True],
        suppress_embeds: bool = MISSING,
        silent: bool = MISSING,
    ) -> WebhookMessage:
        ...
    @overload
    async def send(
        self,
        content: str = MISSING,
        *,
        username: str = MISSING,
        avatar_url: Any = MISSING,
        tts: bool = MISSING,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
        embed: Embed = MISSING,
        embeds: Sequence[Embed] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        thread: Snowflake = MISSING,
        thread_name: str = MISSING,
        wait: Literal[False] = ...,
        suppress_embeds: bool = MISSING,
        silent: bool = MISSING,
    ) -> None:
        ...
    async def send(
        self,
        content: str = MISSING,
        *,
        username: str = MISSING,
        avatar_url: Any = MISSING,
        tts: bool = False,
        file: File = MISSING,
        files: Sequence[File] = MISSING,
        embed: Embed = MISSING,
        embeds: Sequence[Embed] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        thread: Snowflake = MISSING,
        thread_name: str = MISSING,
        wait: bool = False,
        suppress_embeds: bool = False,
        silent: bool = False,
    ) -> Optional[WebhookMessage]:
        if self.token is None:
            raise ValueError('This webhook does not have a token associated with it')
        previous_mentions: Optional[AllowedMentions] = getattr(self._state, 'allowed_mentions', None)
        if content is None:
            content = MISSING
        if suppress_embeds or silent:
            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
            flags.suppress_notifications = silent
        else:
            flags = MISSING
        if self.type is WebhookType.application:
            wait = True
        if thread_name is not MISSING and thread is not MISSING:
            raise TypeError('Cannot mix thread_name and thread keyword arguments.')
        with handle_message_parameters(
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            file=file,
            files=files,
            embed=embed,
            embeds=embeds,
            flags=flags,
            thread_name=thread_name,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_mentions,
        ) as params:
            adapter = async_context.get()
            thread_id: Optional[int] = None
            if thread is not MISSING:
                thread_id = thread.id
            data = await adapter.execute_webhook(
                self.id,
                self.token,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                payload=params.payload,
                multipart=params.multipart,
                files=params.files,
                thread_id=thread_id,
                wait=wait,
            )
        msg = None
        if wait:
            msg = self._create_message(data, thread=thread)
        return msg
    async def fetch_message(self, id: int, /, *, thread: Snowflake = MISSING) -> WebhookMessage:
        if self.token is None:
            raise ValueError('This webhook does not have a token associated with it')
        thread_id: Optional[int] = None
        if thread is not MISSING:
            thread_id = thread.id
        adapter = async_context.get()
        data = await adapter.get_webhook_message(
            self.id,
            self.token,
            id,
            session=self.session,
            proxy=self.proxy,
            proxy_auth=self.proxy_auth,
            thread_id=thread_id,
        )
        return self._create_message(data, thread=thread)
    async def edit_message(
        self,
        message_id: int,
        *,
        content: Optional[str] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
        thread: Snowflake = MISSING,
    ) -> WebhookMessage:
        if self.token is None:
            raise ValueError('This webhook does not have a token associated with it')
        previous_mentions: Optional[AllowedMentions] = getattr(self._state, 'allowed_mentions', None)
        with handle_message_parameters(
            content=content,
            attachments=attachments,
            embed=embed,
            embeds=embeds,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_mentions,
        ) as params:
            thread_id: Optional[int] = None
            if thread is not MISSING:
                thread_id = thread.id
            adapter = async_context.get()
            data = await adapter.edit_webhook_message(
                self.id,
                self.token,
                message_id,
                session=self.session,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                payload=params.payload,
                multipart=params.multipart,
                files=params.files,
                thread_id=thread_id,
            )
        message = self._create_message(data, thread=thread)
        return message
    async def delete_message(self, message_id: int, /, *, thread: Snowflake = MISSING) -> None:
        if self.token is None:
            raise ValueError('This webhook does not have a token associated with it')
        thread_id: Optional[int] = None
        if thread is not MISSING:
            thread_id = thread.id
        adapter = async_context.get()
        await adapter.delete_webhook_message(
            self.id,
            self.token,
            message_id,
            session=self.session,
            proxy=self.proxy,
            proxy_auth=self.proxy_auth,
            thread_id=thread_id,
        )