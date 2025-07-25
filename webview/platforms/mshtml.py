import json
import logging
import sys
import webbrowser
import winreg
from ctypes import windll
from threading import Semaphore
import clr
from webview import _settings
from webview.js import alert
from webview.js.css import disable_text_select
from webview.util import (DEFAULT_HTML, inject_base_uri, interop_dll_path, js_bridge_call,
                          parse_api_js)
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Collections')
clr.AddReference('System.Threading')
import System.Windows.Forms as WinForms
clr.AddReference(interop_dll_path('WebBrowserInterop.dll'))
from WebBrowserInterop import IWebBrowserInterop, WebBrowserEx
logger = logging.getLogger('pywebview')
settings = {}
def _set_ie_mode():
    import winreg
    def get_ie_mode():
        ie_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Internet Explorer')
        try:
            version, type = winreg.QueryValueEx(ie_key, 'svcVersion')
        except:
            version, type = winreg.QueryValueEx(ie_key, 'Version')
        winreg.CloseKey(ie_key)
        if version.startswith('11'):
            value = 0x2AF9
        elif version.startswith('10'):
            value = 0x2711
        elif version.startswith('9'):
            value = 0x270F
        elif version.startswith('8'):
            value = 0x22B8
        else:
            value = 0x2AF9
        return value
    try:
        browser_emulation = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION',
            0,
            winreg.KEY_ALL_ACCESS,
        )
    except WindowsError:
        browser_emulation = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION',
            0,
            winreg.KEY_ALL_ACCESS,
        )
    try:
        dpi_support = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_96DPI_PIXEL',
            0,
            winreg.KEY_ALL_ACCESS,
        )
    except WindowsError:
        dpi_support = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_96DPI_PIXEL',
            0,
            winreg.KEY_ALL_ACCESS,
        )
    mode = get_ie_mode()
    executable_name = sys.executable.split('\\')[-1]
    winreg.SetValueEx(browser_emulation, executable_name, 0, winreg.REG_DWORD, mode)
    winreg.CloseKey(browser_emulation)
    winreg.SetValueEx(dpi_support, executable_name, 0, winreg.REG_DWORD, 1)
    winreg.CloseKey(dpi_support)
class MSHTML:
    alert = None
    class JSBridge(IWebBrowserInterop):
        __namespace__ = 'MSHTML.JSBridge'
        window = None
        def call(self, func_name, param, value_id):
            return js_bridge_call(self.window, func_name, json.loads(param), value_id)
        def alert(self, message):
            MSHTML.alert(message)
        def console(self, message):
            print(message)
    def __init__(self, form, window, alert):
        self.pywebview_window = window
        self.web_view = WebBrowserEx()
        self.web_view.Dock = WinForms.DockStyle.Fill
        self.web_view.ScriptErrorsSuppressed = not _settings['debug']
        self.web_view.IsWebBrowserContextMenuEnabled = _settings['debug']
        self.web_view.WebBrowserShortcutsEnabled = False
        self.web_view.DpiAware = True
        MSHTML.alert = alert
        user_agent = _settings['user_agent'] or settings.get('user_agent')
        if user_agent:
            self.web_view.ChangeUserAgent(user_agent)
        self.web_view.ScriptErrorsSuppressed = not _settings['debug']
        self.web_view.IsWebBrowserContextMenuEnabled = _settings['debug']
        self.js_result_semaphore = Semaphore(0)
        self.js_bridge = MSHTML.JSBridge()
        self.js_bridge.window = window
        self.web_view.ObjectForScripting = self.js_bridge
        if window.background_color != '
            self.web_view.Visible = False
            self.first_load = True
        else:
            self.first_load = False
        self.cancel_back = False
        self.web_view.PreviewKeyDown += self.on_preview_keydown
        self.web_view.Navigating += self.on_navigating
        self.web_view.NewWindow3 += self.on_new_window
        self.web_view.DownloadComplete += self.on_download_complete
        self.web_view.DocumentCompleted += self.on_document_completed
        if window.real_url:
            self.web_view.Navigate(window.real_url)
        elif window.html:
            self.web_view.DocumentText = window.html
        else:
            self.web_view.DocumentText = DEFAULT_HTML
        self.form = form
        form.Controls.Add(self.web_view)
    def evaluate_js(self, script):
        result = self.web_view.Document.InvokeScript('eval', (script,))
        self.js_result = None if result is None or result == 'null' else json.loads(result)
        self.js_result_semaphore.release()
    def load_html(self, content, base_uri):
        self.web_view.DocumentText = inject_base_uri(content, base_uri)
        self.pywebview_window.events.loaded.clear()
    def load_url(self, url):
        self.web_view.Navigate(url)
    def on_preview_keydown(self, _, args):
        if args.KeyCode == WinForms.Keys.Back:
            self.cancel_back = True
        elif args.KeyCode == WinForms.Keys.Delete:
            self.web_view.Document.ExecCommand('Delete', False, None)
        elif args.Modifiers == WinForms.Keys.Control and args.KeyCode == WinForms.Keys.C:
            self.web_view.Document.ExecCommand('Copy', False, None)
        elif args.Modifiers == WinForms.Keys.Control and args.KeyCode == WinForms.Keys.X:
            self.web_view.Document.ExecCommand('Cut', False, None)
        elif args.Modifiers == WinForms.Keys.Control and args.KeyCode == WinForms.Keys.V:
            self.web_view.Document.ExecCommand('Paste', False, None)
        elif args.Modifiers == WinForms.Keys.Control and args.KeyCode == WinForms.Keys.Z:
            self.web_view.Document.ExecCommand('Undo', False, None)
        elif args.Modifiers == WinForms.Keys.Control and args.KeyCode == WinForms.Keys.A:
            self.web_view.Document.ExecCommand('selectAll', False, None)
    def on_new_window(self, sender, args):
        args.Cancel = True
        webbrowser.open(args.Url)
    def on_download_complete(self, *_):
        pass
    def on_navigating(self, _, args):
        if self.cancel_back:
            args.Cancel = True
            self.cancel_back = False
    def on_document_completed(self, _, args):
        document = self.web_view.Document
        document.InvokeScript('eval', (alert.src,))
        if _settings['debug']:
            document.InvokeScript(
                'eval',
                (
                    'window.console = { log: function(msg) { window.external.console(JSON.stringify(msg)) }}',
                ),
            )
        if self.first_load:
            self.web_view.Visible = True
            self.first_load = False
        self.url = None if args.Url.AbsoluteUri == 'about:blank' else str(args.Url.AbsoluteUri)
        document.InvokeScript('eval', (parse_api_js(self.pywebview_window, 'mshtml'),))
        if not self.pywebview_window.text_select:
            document.InvokeScript('eval', (disable_text_select,))
        self.pywebview_window.events.loaded.set()
        if self.pywebview_window.easy_drag:
            document.MouseMove += self.on_mouse_move
    def on_mouse_move(self, _, e):
        if e.MouseButtonsPressed == WinForms.MouseButtons.Left:
            WebBrowserEx.ReleaseCapture()
            windll.user32.SendMessageW(
                self.form.Handle.ToInt32(),
                WebBrowserEx.WM_NCLBUTTONDOWN,
                WebBrowserEx.HT_CAPTION,
                6,
            )