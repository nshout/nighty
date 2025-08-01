from __future__ import annotations
import inspect
import logging
import os
from collections.abc import Mapping, Sequence
from enum import Flag, auto
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar
from urllib.parse import urljoin
from uuid import uuid1
from typing_extensions import Concatenate, ParamSpec, TypeAlias
import webview.http as http
from webview.event import Event
from webview.localization import original_localization
from webview.util import (WebViewException, base_uri, escape_string, is_app, is_local_url,
                          parse_file_type)
from .screen import Screen
from .js import css
if TYPE_CHECKING:
    from typing import type_check_only
P = ParamSpec('P')
T = TypeVar('T')
logger = logging.getLogger('pywebview')
def _api_call(function: WindowFunc[P, T], event_type: str) -> WindowFunc[P, T]:
    @wraps(function)
    def wrapper(self: Window, *args: P.args, **kwargs: P.kwargs) -> T:
        event = self.events.loaded if event_type == 'loaded' else self.events.shown
        try:
            if self.gui is None:
                raise WebViewException('GUI is not initialized')
            return function(self, *args, **kwargs)
        except NameError:
            raise WebViewException('Create a web view window first, before invoking this function')
    return wrapper
def _shown_call(function: Callable[P, T]) -> Callable[P, T]:
    return _api_call(function, 'shown')
def _loaded_call(function: Callable[P, T]) -> Callable[P, T]:
    return _api_call(function, 'loaded')
class FixPoint(Flag):
    NORTH = auto()
    WEST = auto()
    EAST = auto()
    SOUTH = auto()
class EventContainer:
    if TYPE_CHECKING:
        @type_check_only
        def __getattr__(self, __name: str) -> Event:
            ...
        @type_check_only
        def __setattr__(self, __name: str, __value: Event) -> None:
            ...
class Window:
    def __init__(
        self,
        uid: str,
        title: str,
        url: str | None,
        html: str = '',
        width: int = 800,
        height: int = 600,
        x: int | None = None,
        y: int | None = None,
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
        js_api: Any = None,
        text_select: bool = False,
        transparent: bool = False,
        zoomable: bool = False,
        draggable: bool = False,
        vibrancy: bool = False,
        localization: Mapping[str, str] | None = None,
        http_port: int | None = None,
        server: type[http.ServerType] | None = None,
        server_args: http.ServerArgs = {},
        screen: Screen = None
    ) -> None:
        self.uid = uid
        self._title = title
        self.original_url = None if html else url
        self.real_url = None
        self.html = html
        self.initial_width = width
        self.initial_height = height
        self.initial_x = x
        self.initial_y = y
        self.resizable = resizable
        self.fullscreen = fullscreen
        self.min_size = min_size
        self.confirm_close = confirm_close
        self.background_color = background_color
        self.text_select = text_select
        self.frameless = frameless
        self.easy_drag = easy_drag
        self.focus = focus
        self.hidden = hidden
        self.on_top = on_top
        self.minimized = minimized
        self.maximized = maximized
        self.transparent = transparent
        self.zoomable = zoomable
        self.draggable = draggable
        self.localization_override = localization
        self.vibrancy = vibrancy
        self.screen = screen
        self._http_port = http_port
        self._server = server
        self._server_args = server_args
        self._url_prefix = None
        self._common_path = None
        self._server = None
        self._js_api = js_api
        self._functions: dict[str, Callable[..., Any]] = {}
        self._callbacks: dict[str, Callable[..., Any] | None] = {}
        self.events = EventContainer()
        self.events.closed = Event()
        self.events.closing = Event(True)
        self.events.loaded = Event()
        self.events.shown = Event()
        self.events.minimized = Event()
        self.events.maximized = Event()
        self.events.restored = Event()
        self.events.resized = Event()
        self.events.moved = Event()
        self.gui = None
    def _initialize(self, gui, server: http.BottleServer | None = None):
        self.gui = gui
        self.localization = original_localization.copy()
        if self.localization_override:
            self.localization.update(self.localization_override)
        if is_app(self.original_url) and (server is None or server == http.global_server):
            *_, server = http.start_server(
                urls=[self.original_url],
                http_port=self._http_port,
                server=self._server,
                **self._server_args,
            )
        elif server is None:
            server = http.global_server
        self._url_prefix = server.address if not server is None else None
        self._common_path = server.common_path if not server is None else None
        self._server = server
        self.js_api_endpoint = (
            http.global_server.js_api_endpoint if not http.global_server is None else None
        )
        self.real_url = self._resolve_url(self.original_url)
    @property
    def width(self) -> int:
        self.events.shown.wait(15)
        width, _ = self.gui.get_size(self.uid)
        return width
    @property
    def height(self) -> int:
        self.events.shown.wait(15)
        _, height = self.gui.get_size(self.uid)
        return height
    @property
    def title(self) -> str:
        return self._title
    @title.setter
    def title(self, title: str) -> None:
        self.events.loaded.wait(15)
        self._title = title
        self.gui.set_title(title, self.uid)
    @property
    def x(self) -> int:
        self.events.shown.wait(15)
        x, _ = self.gui.get_position(self.uid)
        return x
    @property
    def y(self) -> int:
        self.events.shown.wait(15)
        _, y = self.gui.get_position(self.uid)
        return y
    @property
    def on_top(self) -> bool:
        return self.__on_top
    @on_top.setter
    def on_top(self, on_top: bool) -> None:
        self.__on_top = on_top
        if hasattr(self, 'gui') and self.gui != None:
            self.gui.set_on_top(self.uid, on_top)
    @_loaded_call
    def get_elements(self, selector: str) -> Any:
        code = (
            % selector
        )
        return self.evaluate_js(code)
    @_shown_call
    def load_url(self, url: str) -> None:
        if ((self._server is None) or (not self._server.running)) and (
            (is_app(url) or is_local_url(url))
        ):
            self._url_prefix, self._common_path, self.server = http.start_server([url])
        self.real_url = self._resolve_url(url)
        self.gui.load_url(self.real_url, self.uid)
    @_shown_call
    def load_html(self, content: str, base_uri: str = base_uri()) -> None:
        self.gui.load_html(content, base_uri, self.uid)
    @_loaded_call
    def load_css(self, stylesheet: str) -> None:
        code = css.src % stylesheet.replace('\n', '').replace('\r', '').replace('"', "'")
        self.gui.evaluate_js(code, self.uid)
    @_shown_call
    def set_title(self, title: str) -> None:
        self._title = title
        self.gui.set_title(title, self.uid)
    @_loaded_call
    def get_cookies(self):
        return self.gui.get_cookies(self.uid)
    @_loaded_call
    def get_current_url(self) -> str | None:
        return self.gui.get_current_url(self.uid)
    @_loaded_call
    def destroy(self) -> None:
        self.gui.destroy_window(self.uid)
    @_shown_call
    def show(self) -> None:
        self.gui.show(self.uid)
    @_shown_call
    def hide(self) -> None:
        self.gui.hide(self.uid)
    @_shown_call
    def set_window_size(self, width: int, height: int) -> None:
        logger.warning(
            'This function is deprecated and will be removed in future releases. Use resize() instead'
        )
        self.resize(width, height)
    @_shown_call
    def resize(
        self, width: int, height: int, fix_point: FixPoint = FixPoint.NORTH | FixPoint.WEST
    ) -> None:
        self.gui.resize(width, height, self.uid, fix_point)
    @_shown_call
    def minimize(self) -> None:
        self.gui.minimize(self.uid)
    @_shown_call
    def restore(self) -> None:
        self.gui.restore(self.uid)
    @_shown_call
    def toggle_fullscreen(self) -> None:
        self.gui.toggle_fullscreen(self.uid)
    @_shown_call
    def move(self, x: int, y: int) -> None:
        self.gui.move(x, y, self.uid)
    @_loaded_call
    def evaluate_js(self, script: str, callback: Callable[..., Any] | None = None) -> Any:
        unique_id = uuid1().hex
        self._callbacks[unique_id] = callback
        if self.gui.renderer == 'cef':
            sync_eval = 'window.external.return_result(JSON.stringify(value), "{0}");'.format(
                unique_id,
            )
        else:
            sync_eval = 'JSON.stringify(value);'
        if callback:
            escaped_script = .format(
                escape_string(script), unique_id, sync_eval
            )
        else:
            escaped_script = f
        if self.gui.renderer == 'cef':
            return self.gui.evaluate_js(escaped_script, self.uid, unique_id)
        else:
            return self.gui.evaluate_js(escaped_script, self.uid)
    @_shown_call
    def create_confirmation_dialog(self, title: str, message: str) -> bool:
        return self.gui.create_confirmation_dialog(title, message, self.uid)
    @_shown_call
    def create_file_dialog(
        self,
        dialog_type: int = 10,
        directory: str = '',
        allow_multiple: bool = False,
        save_filename: str = '',
        file_types: Sequence[str] = tuple(),
    ) -> Sequence[str] | None:
        for f in file_types:
            parse_file_type(f)
        if not os.path.exists(directory):
            directory = ''
        return self.gui.create_file_dialog(
            dialog_type, directory, allow_multiple, save_filename, file_types, self.uid
        )
    def expose(self, *functions: Callable[..., Any]) -> None:
        if not all(map(callable, functions)):
            raise TypeError('Parameter must be a function')
        func_list: list[dict[str, Any]] = []
        for func in functions:
            name = func.__name__
            self._functions[name] = func
            params = list(inspect.getfullargspec(func).args)
            func_list.append({'func': name, 'params': params})
        if self.events.loaded.is_set():
            self.evaluate_js(f'window.pywebview._createApi({func_list})')
    def _resolve_url(self, url: str) -> str | None:
        if is_app(url):
            return self._url_prefix
        if is_local_url(url) and self._url_prefix and self._common_path is not None:
            filename = os.path.relpath(url, self._common_path)
            return urljoin(self._url_prefix, filename)
        else:
            return url
WindowFunc: TypeAlias = Callable[Concatenate[Window, P], T]