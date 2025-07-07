from __future__ import annotations
import threading
import logging
import json
import time
import re
from urllib.parse import quote as urlquote
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING, Sequence, Tuple, Union, TypeVar, Type, overload
import weakref
from .. import utils
from ..errors import HTTPException, Forbidden, NotFound, DiscordServerError
from ..message import Message, MessageFlags
from ..http import Route, handle_message_parameters
from ..channel import PartialMessageable
from .async_ import BaseWebhook, _WebhookState
__all__ = (
    'SyncWebhook',
    'SyncWebhookMessage',
)
_log = logging.getLogger(__name__)
if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType
    from ..file import File
    from ..embeds import Embed
    from ..mentions import AllowedMentions
    from ..message import Attachment
    from ..abc import Snowflake
    from ..state import ConnectionState
    from ..types.webhook import (
        Webhook as WebhookPayload,
    )
    from ..types.message import (
        Message as MessagePayload,
    )
    BE = TypeVar('BE', bound=BaseException)
    try:
        from requests import Session, Response
    except ModuleNotFoundError:
        pass
MISSING: Any = utils.MISSING
class DeferredLock:
    def __init__(self, lock: threading.Lock) -> None:
        self.lock: threading.Lock = lock
        self.delta: Optional[float] = None
    def __enter__(self) -> Self:
        self.lock.acquire()
        return self
    def delay_by(self, delta: float) -> None:
        self.delta = delta
    def __exit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.delta:
            time.sleep(self.delta)
        self.lock.release()
class WebhookAdapter:
    def __init__(self):
        self._locks: weakref.WeakValueDictionary[Any, threading.Lock] = weakref.WeakValueDictionary()
    def request(
        self,
        route: Route,
        session: Session,
        *,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[Sequence[File]] = None,
        reason: Optional[str] = None,
        auth_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        headers: Dict[str, str] = {}
        files = files or []
        to_send: Optional[Union[str, bytes, Dict[str, Any]]] = None
        bucket = (route.webhook_id, route.webhook_token)
        try:
            lock = self._locks[bucket]
        except KeyError:
            self._locks[bucket] = lock = threading.Lock()
        if payload is not None:
            headers['Content-Type'] = 'application/json; charset=utf-8'
            to_send = utils._to_json(payload).encode('utf-8')
        if auth_token is not None:
            headers['Authorization'] = f'{auth_token}'
        if reason is not None:
            headers['X-Audit-Log-Reason'] = urlquote(reason)
        response: Optional[Response] = None
        data: Optional[Union[Dict[str, Any], str]] = None
        file_data: Optional[Dict[str, Any]] = None
        method = route.method
        url = route.url
        webhook_id = route.webhook_id
        with DeferredLock(lock) as lock:
            for attempt in range(5):
                for file in files:
                    file.reset(seek=attempt)
                if multipart:
                    file_data = {}
                    for p in multipart:
                        name = p['name']
                        if name == 'payload_json':
                            to_send = {'payload_json': p['value']}
                        else:
                            file_data[name] = (p['filename'], p['value'], p['content_type'])
                try:
                    with session.request(
                        method, url, data=to_send, files=file_data, headers=headers, params=params
                    ) as response:
                        _log.debug(
                            'Webhook ID %s with %s %s has returned status code %s.',
                            webhook_id,
                            method,
                            url,
                            response.status_code,
                        )
                        response.encoding = 'utf-8'
                        response.status = response.status_code
                        data = response.text or None
                        try:
                            if data and response.headers['Content-Type'] == 'application/json':
                                data = json.loads(data)
                        except KeyError:
                            pass
                        remaining = response.headers.get('X-Ratelimit-Remaining')
                        if remaining == '0' and response.status_code != 429:
                            delta = utils._parse_ratelimit_header(response)
                            _log.debug(
                                'Webhook ID %s has exhausted its rate limit bucket (retry: %s).',
                                webhook_id,
                                delta,
                            )
                            lock.delay_by(delta)
                        if 300 > response.status_code >= 200:
                            return data
                        if response.status_code == 429:
                            if not response.headers.get('Via'):
                                raise HTTPException(response, data)
                            fmt = 'Webhook ID %s is rate limited. Retrying in %.2f seconds.'
                            retry_after: float = data['retry_after']
                            _log.warning(fmt, webhook_id, retry_after)
                            time.sleep(retry_after)
                            continue
                        if response.status_code >= 500:
                            time.sleep(1 + attempt * 2)
                            continue
                        if response.status_code == 403:
                            raise Forbidden(response, data)
                        elif response.status_code == 404:
                            raise NotFound(response, data)
                        else:
                            raise HTTPException(response, data)
                except OSError as e:
                    if attempt < 4 and e.errno in (54, 10054):
                        time.sleep(1 + attempt * 2)
                        continue
                    raise
            if response:
                if response.status_code >= 500:
                    raise DiscordServerError(response, data)
                raise HTTPException(response, data)
            raise RuntimeError('Unreachable code in HTTP handling.')
    def delete_webhook(
        self,
        webhook_id: int,
        *,
        token: Optional[str] = None,
        session: Session,
        reason: Optional[str] = None,
    ) -> None:
        route = Route('DELETE', '/webhooks/{webhook_id}', webhook_id=webhook_id)
        return self.request(route, session, reason=reason, auth_token=token)
    def delete_webhook_with_token(
        self,
        webhook_id: int,
        token: str,
        *,
        session: Session,
        reason: Optional[str] = None,
    ) -> None:
        route = Route('DELETE', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(route, session, reason=reason)
    def edit_webhook(
        self,
        webhook_id: int,
        token: str,
        payload: Dict[str, Any],
        *,
        session: Session,
        reason: Optional[str] = None,
    ) -> WebhookPayload:
        route = Route('PATCH', '/webhooks/{webhook_id}', webhook_id=webhook_id)
        return self.request(route, session, reason=reason, payload=payload, auth_token=token)
    def edit_webhook_with_token(
        self,
        webhook_id: int,
        token: str,
        payload: Dict[str, Any],
        *,
        session: Session,
        reason: Optional[str] = None,
    ) -> WebhookPayload:
        route = Route('PATCH', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(route, session, reason=reason, payload=payload)
    def execute_webhook(
        self,
        webhook_id: int,
        token: str,
        *,
        session: Session,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[Sequence[File]] = None,
        thread_id: Optional[int] = None,
        wait: bool = False,
    ) -> MessagePayload:
        params = {'wait': int(wait)}
        if thread_id:
            params['thread_id'] = thread_id
        route = Route('POST', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(route, session, payload=payload, multipart=multipart, files=files, params=params)
    def get_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: Session,
        thread_id: Optional[int] = None,
    ) -> MessagePayload:
        route = Route(
            'GET',
            '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=webhook_id,
            webhook_token=token,
            message_id=message_id,
        )
        params = None if thread_id is None else {'thread_id': thread_id}
        return self.request(route, session, params=params)
    def edit_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: Session,
        payload: Optional[Dict[str, Any]] = None,
        multipart: Optional[List[Dict[str, Any]]] = None,
        files: Optional[Sequence[File]] = None,
        thread_id: Optional[int] = None,
    ) -> MessagePayload:
        route = Route(
            'PATCH',
            '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=webhook_id,
            webhook_token=token,
            message_id=message_id,
        )
        params = None if thread_id is None else {'thread_id': thread_id}
        return self.request(route, session, payload=payload, multipart=multipart, files=files, params=params)
    def delete_webhook_message(
        self,
        webhook_id: int,
        token: str,
        message_id: int,
        *,
        session: Session,
        thread_id: Optional[int] = None,
    ) -> None:
        route = Route(
            'DELETE',
            '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=webhook_id,
            webhook_token=token,
            message_id=message_id,
        )
        params = None if thread_id is None else {'thread_id': thread_id}
        return self.request(route, session, params=params)
    def fetch_webhook(
        self,
        webhook_id: int,
        token: str,
        *,
        session: Session,
    ) -> WebhookPayload:
        route = Route('GET', '/webhooks/{webhook_id}', webhook_id=webhook_id)
        return self.request(route, session=session, auth_token=token)
    def fetch_webhook_with_token(
        self,
        webhook_id: int,
        token: str,
        *,
        session: Session,
    ) -> WebhookPayload:
        route = Route('GET', '/webhooks/{webhook_id}/{webhook_token}', webhook_id=webhook_id, webhook_token=token)
        return self.request(route, session=session)
class _WebhookContext(threading.local):
    adapter: Optional[WebhookAdapter] = None
_context = _WebhookContext()
def _get_webhook_adapter() -> WebhookAdapter:
    if _context.adapter is None:
        _context.adapter = WebhookAdapter()
    return _context.adapter
class SyncWebhookMessage(Message):
    _state: _WebhookState
    def edit(
        self,
        content: Optional[str] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
    ) -> SyncWebhookMessage:
        return self._state._webhook.edit_message(
            self.id,
            content=content,
            embeds=embeds,
            embed=embed,
            attachments=attachments,
            allowed_mentions=allowed_mentions,
            thread=self._state._thread,
        )
    def add_files(self, *files: File) -> SyncWebhookMessage:
        r
        return self.edit(attachments=[*self.attachments, *files])
    def remove_attachments(self, *attachments: Attachment) -> SyncWebhookMessage:
        r
        return self.edit(attachments=[a for a in self.attachments if a not in attachments])
    def delete(self, *, delay: Optional[float] = None) -> None:
        if delay is not None:
            time.sleep(delay)
        self._state._webhook.delete_message(self.id, thread=self._state._thread)
class SyncWebhook(BaseWebhook):
    __slots__: Tuple[str, ...] = ('session',)
    def __init__(
        self,
        data: WebhookPayload,
        session: Session,
        token: Optional[str] = None,
        state: Optional[Union[ConnectionState, _WebhookState]] = None,
    ) -> None:
        super().__init__(data, token, state)
        self.session: Session = session
    def __repr__(self) -> str:
        return f'<Webhook id={self.id!r}>'
    @property
    def url(self) -> str:
        return f'https://discord.com/api/webhooks/{self.id}/{self.token}'
    @classmethod
    def partial(cls, id: int, token: str, *, session: Session = MISSING, user_token: Optional[str] = None) -> SyncWebhook:
        data: WebhookPayload = {
            'id': id,
            'type': 1,
            'token': token,
        }
        import requests
        if session is not MISSING:
            if not isinstance(session, requests.Session):
                raise TypeError(f'expected requests.Session not {session.__class__!r}')
        else:
            session = requests
        return cls(data, session, token=user_token)
    @classmethod
    def from_url(cls, url: str, *, session: Session = MISSING, user_token: Optional[str] = None) -> SyncWebhook:
        m = re.search(r'discord(?:app)?\.com/api/webhooks/(?P<id>[0-9]{17,20})/(?P<token>[A-Za-z0-9\.\-\_]{60,})', url)
        if m is None:
            raise ValueError('Invalid webhook URL given')
        data: Dict[str, Any] = m.groupdict()
        data['type'] = 1
        import requests
        if session is not MISSING:
            if not isinstance(session, requests.Session):
                raise TypeError(f'expected requests.Session not {session.__class__!r}')
        else:
            session = requests
        return cls(data, session, token=user_token)
    def fetch(self, *, prefer_auth: bool = True) -> SyncWebhook:
        adapter: WebhookAdapter = _get_webhook_adapter()
        if prefer_auth and self.auth_token:
            data = adapter.fetch_webhook(self.id, self.auth_token, session=self.session)
        elif self.token:
            data = adapter.fetch_webhook_with_token(self.id, self.token, session=self.session)
        else:
            raise ValueError('This webhook does not have a token associated with it')
        return SyncWebhook(data, self.session, token=self.auth_token, state=self._state)
    def delete(self, *, reason: Optional[str] = None, prefer_auth: bool = True) -> None:
        if self.token is None and self.auth_token is None:
            raise ValueError('This webhook does not have a token associated with it')
        adapter: WebhookAdapter = _get_webhook_adapter()
        if prefer_auth and self.auth_token:
            adapter.delete_webhook(self.id, token=self.auth_token, session=self.session, reason=reason)
        elif self.token:
            adapter.delete_webhook_with_token(self.id, self.token, session=self.session, reason=reason)
    def edit(
        self,
        *,
        reason: Optional[str] = None,
        name: Optional[str] = MISSING,
        avatar: Optional[bytes] = MISSING,
        channel: Optional[Snowflake] = None,
        prefer_auth: bool = True,
    ) -> SyncWebhook:
        if self.token is None and self.auth_token is None:
            raise ValueError('This webhook does not have a token associated with it')
        payload = {}
        if name is not MISSING:
            payload['name'] = str(name) if name is not None else None
        if avatar is not MISSING:
            payload['avatar'] = utils._bytes_to_base64_data(avatar) if avatar is not None else None
        adapter: WebhookAdapter = _get_webhook_adapter()
        data: Optional[WebhookPayload] = None
        if channel is not None:
            if self.auth_token is None:
                raise ValueError('Editing channel requires authenticated webhook')
            payload['channel_id'] = channel.id
            data = adapter.edit_webhook(self.id, self.auth_token, payload=payload, session=self.session, reason=reason)
        elif prefer_auth and self.auth_token:
            data = adapter.edit_webhook(self.id, self.auth_token, payload=payload, session=self.session, reason=reason)
        elif self.token:
            data = adapter.edit_webhook_with_token(self.id, self.token, payload=payload, session=self.session, reason=reason)
        if data is None:
            raise RuntimeError('Unreachable code hit: data was not assigned')
        return SyncWebhook(data=data, session=self.session, token=self.auth_token, state=self._state)
    def _create_message(self, data: MessagePayload, *, thread: Snowflake = MISSING) -> SyncWebhookMessage:
        state = _WebhookState(self, parent=self._state, thread=thread)
        channel = self.channel or PartialMessageable(state=self._state, guild_id=self.guild_id, id=int(data['channel_id']))
        return SyncWebhookMessage(data=data, state=state, channel=channel)
    @overload
    def send(
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
    ) -> SyncWebhookMessage:
        ...
    @overload
    def send(
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
    def send(
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
    ) -> Optional[SyncWebhookMessage]:
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
            thread_name=thread_name,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_mentions,
            flags=flags,
        ) as params:
            adapter: WebhookAdapter = _get_webhook_adapter()
            thread_id: Optional[int] = None
            if thread is not MISSING:
                thread_id = thread.id
            data = adapter.execute_webhook(
                self.id,
                self.token,
                session=self.session,
                payload=params.payload,
                multipart=params.multipart,
                files=params.files,
                thread_id=thread_id,
                wait=wait,
            )
        if wait:
            return self._create_message(data, thread=thread)
    def fetch_message(self, id: int, /, *, thread: Snowflake = MISSING) -> SyncWebhookMessage:
        if self.token is None:
            raise ValueError('This webhook does not have a token associated with it')
        thread_id: Optional[int] = None
        if thread is not MISSING:
            thread_id = thread.id
        adapter: WebhookAdapter = _get_webhook_adapter()
        data = adapter.get_webhook_message(
            self.id,
            self.token,
            id,
            session=self.session,
            thread_id=thread_id,
        )
        return self._create_message(data, thread=thread)
    def edit_message(
        self,
        message_id: int,
        *,
        content: Optional[str] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
        thread: Snowflake = MISSING,
    ) -> SyncWebhookMessage:
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
            adapter: WebhookAdapter = _get_webhook_adapter()
            data = adapter.edit_webhook_message(
                self.id,
                self.token,
                message_id,
                session=self.session,
                payload=params.payload,
                multipart=params.multipart,
                files=params.files,
                thread_id=thread_id,
            )
            return self._create_message(data, thread=thread)
    def delete_message(self, message_id: int, /, *, thread: Snowflake = MISSING) -> None:
        if self.token is None:
            raise ValueError('This webhook does not have a token associated with it')
        thread_id: Optional[int] = None
        if thread is not MISSING:
            thread_id = thread.id
        adapter: WebhookAdapter = _get_webhook_adapter()
        adapter.delete_webhook_message(
            self.id,
            self.token,
            message_id,
            session=self.session,
            thread_id=thread_id,
        )