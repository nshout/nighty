from __future__ import annotations
from typing import Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired
class FormError(TypedDict):
    code: str
    message: str
class FormErrorWrapper(TypedDict):
    _errors: List[FormError]
FormErrors = Union[FormErrorWrapper, Dict[str, 'FormErrors']]
class Error(TypedDict):
    code: int
    message: str
    errors: NotRequired[FormErrors]
CaptchaService = Literal['hcaptcha', 'recaptcha']
class CaptchaRequired(TypedDict):
    captcha_key: List[str]
    captcha_service: CaptchaService
    captcha_sitekey: Optional[str]
    captcha_rqdata: NotRequired[str]
    captcha_rqtoken: NotRequired[str]