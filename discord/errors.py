from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, Final, List, Optional, Tuple, Union
from .utils import _get_as_snowflake
if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientWebSocketResponse
    from requests import Response
    from typing_extensions import TypeGuard
    from .types.error import (
        CaptchaRequired as CaptchaPayload,
        CaptchaService,
        Error as ErrorPayload,
        FormErrors as FormErrorsPayload,
        FormErrorWrapper as FormErrorWrapperPayload,
    )
    _ResponseType = Union[ClientResponse, Response]
__all__ = (
    'DiscordException',
    'ClientException',
    'GatewayNotFound',
    'HTTPException',
    'RateLimited',
    'Forbidden',
    'NotFound',
    'DiscordServerError',
    'InvalidData',
    'AuthFailure',
    'LoginFailure',
    'ConnectionClosed',
    'CaptchaRequired',
)
class DiscordException(Exception):
    __slots__ = ()
class ClientException(DiscordException):
    __slots__ = ()
class GatewayNotFound(DiscordException):
    def __init__(self):
        message = 'The gateway to connect to Discord was not found.'
        super().__init__(message)
def _flatten_error_dict(d: FormErrorsPayload, key: str = '', /) -> Dict[str, str]:
    def is_wrapper(x: FormErrorsPayload) -> TypeGuard[FormErrorWrapperPayload]:
        return '_errors' in x
    items: List[Tuple[str, str]] = []
    if is_wrapper(d) and not key:
        items.append(('miscellaneous', ' '.join(x.get('message', '') for x in d['_errors'])))
        d.pop('_errors')
    for k, v in d.items():
        new_key = key + '.' + k if key else k
        if isinstance(v, dict):
            if is_wrapper(v):
                _errors = v['_errors']
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
            else:
                items.extend(_flatten_error_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)
class HTTPException(DiscordException):
    def __init__(self, response: _ResponseType, message: Optional[Union[str, Dict[str, Any]]]):
        self.response: _ResponseType = response
        self.status: int = response.status
        self.code: int = 0
        self.text: str
        self.json: ErrorPayload
        self.payment_id: Optional[int] = None
        if isinstance(message, dict):
            self.json = message
            self.code = message.get('code', 0)
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = base + '\n' + helpful
            else:
                self.text = base
            self.payment_id = _get_as_snowflake(message, 'payment_id')
        else:
            self.text = message or ''
            self.json = {'code': 0, 'message': message or ''}
        fmt = '{0.status} {0.reason} (error code: {1})'
        if len(self.text):
            fmt += ': {2}'
        super().__init__(fmt.format(self.response, self.code, self.text))
class RateLimited(DiscordException):
    __slots__ = ('retry_after',)
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f'Too many requests. Retry in {retry_after:.2f} seconds.')
class Forbidden(HTTPException):
    __slots__ = ()
class NotFound(HTTPException):
    __slots__ = ()
class DiscordServerError(HTTPException):
    __slots__ = ()
class CaptchaRequired(HTTPException):
    RECAPTCHA_SITEKEY: Final[str] = '6Lef5iQTAAAAAKeIvIY-DeexoO3gj7ryl9rLMEnn'
    __slots__ = ('errors', 'service', 'sitekey')
    def __init__(self, response: _ResponseType, message: CaptchaPayload):
        super().__init__(response, {'code': -1, 'message': 'Captcha required'})
        self.json: CaptchaPayload = message
        self.errors: List[str] = message['captcha_key']
        self.service: CaptchaService = message.get('captcha_service', 'hcaptcha')
        self.sitekey: str = message.get('captcha_sitekey') or self.RECAPTCHA_SITEKEY
        self.rqdata: Optional[str] = message.get('captcha_rqdata')
        self.rqtoken: Optional[str] = message.get('captcha_rqtoken')
class InvalidData(ClientException):
    __slots__ = ()
class LoginFailure(ClientException):
    __slots__ = ()
AuthFailure = LoginFailure
class ConnectionClosed(ClientException):
    __slots__ = ('code', 'reason')
    def __init__(self, socket: ClientWebSocketResponse, *, code: Optional[int] = None):
        self.code: int = code or socket.close_code or -1
        self.reason: str = ''
        super().__init__(f'WebSocket closed with {self.code}')