from __future__ import annotations
import datetime
import logging
import os
import re
import tempfile
import threading
from collections.abc import Iterable, Mapping
from typing import Any, Callable
from uuid import uuid4
from proxy_tools import module_property
import webview.http as http
from webview.event import Event
from webview.guilib import initialize, GUIType
from webview.localization import original_localization
from webview.menu import Menu
from webview.screen import Screen
from webview.util import (_TOKEN, WebViewException, base_uri, escape_line_breaks, escape_string,
                          is_app, is_local_url, parse_file_type)
from webview.window import Window
__all__ = (
    'start',
    'create_window',
    'token',
    'screens',
    'Event',
    '_TOKEN',
    'base_uri',
    'parse_file_type',
    'escape_string',
    'escape_line_breaks',
    'WebViewException',
    'Screen',
    'Window',
)
logger = logging.getLogger('pywebview')
handler = logging.StreamHandler()
formatter = logging.Formatter('[pywebview] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
log_level = logging.DEBUG if os.environ.get('PYWEBVIEW_LOG') == 'debug' else logging.INFO
logger.setLevel(log_level)
OPEN_DIALOG = 10
FOLDER_DIALOG = 20
SAVE_DIALOG = 30
DRAG_REGION_SELECTOR = '.pywebview-drag-region'
DEFAULT_HTTP_PORT = 42001
guilib = None
_settings = {
    'debug': False,
    'storage_path': None,
    'private_mode': True,
    'user_agent': None,
    'http_server': False
}
token = _TOKEN
windows: list[Window] = []
menus: list[Menu] = []
def start(
    func: Callable[..., None] | None = None,
    args: Iterable[Any] | None = None,
    localization: dict[str, str] = {},
    gui: GUIType | None = None,
    debug: bool = False,
    http_server: bool = False,
    http_port: int | None = None,
    user_agent: str | None = None,
    private_mode: bool = True,
    storage_path: str | None = None,
    menu: list[Menu] = [],
    server: type[http.ServerType] = http.BottleServer,
    server_args: dict[Any, Any] = {},
    ssl: bool = False,
):
    global guilib
    def _create_children(other_windows):
        if not windows[0].events.shown.wait(10):
            raise WebViewException('Main window failed to load')
        for window in other_windows:
            guilib.create_window(window)
    _settings['debug'] = debug
    _settings['user_agent'] = user_agent
    _settings['http_server'] = http_server
    _settings['private_mode'] = private_mode
    _settings['storage_path'] = storage_path
    if debug:
        logger.setLevel(logging.DEBUG)
    if _settings['storage_path'] and _settings['private_mode'] and not os.path.exists(_settings['storage_path']):
        os.makedirs(_settings['storage_path'])
    original_localization.update(localization)
    if threading.current_thread().name != 'MainThread':
        raise WebViewException('pywebview must be run on a main thread.')
    if len(windows) == 0:
        raise WebViewException('You must create a window first before calling this function.')
    guilib = initialize(gui)
    if ssl:
        keyfile, certfile = generate_ssl_cert()
        server_args['keyfile'] = keyfile
        server_args['certfile'] = certfile
    else:
        keyfile, certfile = None, None
    urls = [w.original_url for w in windows]
    has_local_urls = not not [w.original_url for w in windows if is_local_url(w.original_url)]
    if (http.global_server is None) and (http_server or has_local_urls):
        if not _settings['private_mode'] and not http_port:
            http_port = DEFAULT_HTTP_PORT
        *_, server = http.start_global_server(
            http_port=http_port, urls=urls, server=server, **server_args
        )
    for window in windows:
        window._initialize(guilib)
    if ssl:
        for window in windows:
            window.gui.add_tls_cert(certfile)
    if len(windows) > 1:
        thread = threading.Thread(target=_create_children, args=(windows[1:],))
        thread.start()
    if func:
        if args is not None:
            if not hasattr(args, '__iter__'):
                args = (args,)
            thread = threading.Thread(target=func, args=args)
        else:
            thread = threading.Thread(target=func)
        thread.start()
    if menu:
        guilib.set_app_menu(menu)
    guilib.create_window(windows[0])
    if certfile:
        os.unlink(certfile)
def create_window(
    title: str,
    url: str | None = None,
    html: str | None = None,
    js_api: Any = None,
    width: int = 800,
    height: int = 600,
    x: int | None = None,
    y: int | None = None,
    screen: Screen = None,
    resizable: bool = True,
    fullscreen: bool = False,
    min_size: tuple[int, int] = (200, 100),
    hidden: bool = False,
    frameless: bool = False,
    easy_drag: bool = True,
    focus: bool = True,
    minimized: bool = False,
    maximized: bool = False,
    on_top: bool = False,
    confirm_close: bool = False,
    background_color: str = '
    transparent: bool = False,
    text_select: bool = False,
    zoomable: bool = False,
    draggable: bool = False,
    vibrancy: bool = False,
    localization: Mapping[str, str] | None = None,
    server: type[http.ServerType] = http.BottleServer,
    http_port: int | None = None,
    server_args: http.ServerArgs = {},
) -> Window:
    valid_color = r'^
    if not re.match(valid_color, background_color):
        raise ValueError('{0} is not a valid hex triplet color'.format(background_color))
    uid = 'master' if len(windows) == 0 else 'child_' + uuid4().hex[:8]
    window = Window(
        uid,
        title,
        url,
        html,
        width,
        height,
        x,
        y,
        resizable,
        fullscreen,
        min_size,
        hidden,
        frameless,
        easy_drag,
        focus,
        minimized,
        maximized,
        on_top,
        confirm_close,
        background_color,
        js_api,
        text_select,
        transparent,
        zoomable,
        draggable,
        vibrancy,
        localization,
        server=server,
        http_port=http_port,
        server_args=server_args,
        screen=screen,
    )
    windows.append(window)
    if threading.current_thread().name != 'MainThread' and guilib:
        if is_app(url) or is_local_url(url) and not server.is_running:
            url_prefix, common_path, server = http.start_server([url], server=server, **server_args)
        else:
            url_prefix, common_path, server = None, None, None
        window._initialize(gui=guilib, server=server)
        guilib.create_window(window)
    return window
def generate_ssl_cert():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    with tempfile.NamedTemporaryFile(prefix='keyfile_', suffix='.pem', delete=False) as f:
        keyfile = f.name
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        f.write(key_pem)
    with tempfile.NamedTemporaryFile(prefix='certfile_', suffix='.pem', delete=False) as f:
        certfile = f.name
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, 'US'),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'California'),
                x509.NameAttribute(NameOID.LOCALITY_NAME, 'San Francisco'),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'pywebview'),
                x509.NameAttribute(NameOID.COMMON_NAME, '127.0.0.1'),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName('localhost')]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        f.write(cert_pem)
    return keyfile, certfile
def active_window() -> Window | None:
    if guilib:
        return guilib.get_active_window()
    return None
@module_property
def screens() -> list[Screen]:
    guilib = initialize()
    screens = guilib.get_screens()
    return screens