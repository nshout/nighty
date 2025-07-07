import asyncio
import platform
import subprocess
import bleach
import io
import json
import logging
import nightycore
import os
import pyperclip
import random
import re
import requests
import string
import sys
import time
import urllib.parse
import urllib.request
import uuid
import warnings
from GPUtil import getGPUs
from PIL import Image
from aiohttp import ClientSession
from art import text2art
from base64 import b64decode, b64encode
from bs4 import BeautifulSoup
from codecs import decode as codecs_decode, encode as codecs_encode
from datetime import datetime, timedelta, timezone
from difflib import get_close_matches
from fnmatch import fnmatch
from gtts import gTTS
from pathlib import Path
from platform import uname as uName
from playsound import playsound
from psutil import cpu_percent, virtual_memory, disk_partitions, disk_usage
from pygetwindow import getActiveWindow
from pystray import Icon, MenuItem
from qrcode import QRCode
from qrcode.constants import ERROR_CORRECT_L
from randomuser import RandomUser
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from signal import SIGTERM
from subprocess import check_output, Popen, run as Srun
from threading import Event as ThreadEvent
from threading import Thread, Lock
from tkinter import messagebox, Tk
from tls_client import Session as TLSSession
from types import MethodType
from typing import Union
from youtubesearchpython import SearchVideos
from zipfile import ZipFile
import discord
import discord_client
import webview
from discord.appinfo import ClientInfo
from discord.ext import commands, tasks
from discord.ext.commands.context import Context
from discord.ext.commands.view import StringView
UNSPECIFIED = object()
root = Tk()
root.withdraw()
logging.getLogger().setLevel(logging.CRITICAL + 1)
warnings.filterwarnings("ignore")
__version__ = "2.3"
SERVER_TO_USE = "15.204.5.83"
global main_ui
global main_api
global ui
main_ui = None
main_api = None
ui = None
start_time = time.time()
start_rpc_time = int(time.time() * 1000)
end_rpc_time = None
if platform.system() == "Windows":
    base_path = os.environ["APPDATA"]
else:
    base_path = os.path.expanduser("~/.config")
getNightyPath = lambda: f"{base_path}/Nighty Selfbot/"
getAuthPath = lambda: f"{base_path}/Nighty Selfbot/auth.json"
getConfigPath = lambda: f"{base_path}/Nighty Selfbot/config.json"
getDataPath = lambda: f"{base_path}/Nighty Selfbot/data"
getSoundsPath = lambda: f"{getDataPath()}/sounds"
getScriptsPath = lambda: f"{getDataPath()}/scripts"
getRPCPath = lambda: f"{getDataPath()}/rpc.json"
if platform.system() == "Windows":
    from ctypes import windll
    from win10toast_click import ToastNotifier
    getDisplayScale = lambda: windll.user32.GetDpiForSystem() / 100.0
    toaster = ToastNotifier()
else:
    from mac_notifications import client as toaster
if platform.system() == "Windows":
    base_path = os.environ["APPDATA"]
else:
    base_path = os.path.expanduser("~/.config")
getLicense = lambda: json.load(open(f"{base_path}/Nighty Selfbot/auth.json")).get(
    "license"
)
def get_system_uuid():
    if platform.system() == "Windows":
        result = subprocess.run(
            ["wmic", "csproduct", "get", "uuid"], capture_output=True, text=True
        )
        return result.stdout.split("\n")[1].strip()
    elif platform.system() == "Darwin":
        result = subprocess.run(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.split("\n"):
            if "UUID" in line:
                return line.split('"')[-2]
    else:
        return "Unsupported OS"
def getUUID():
    if platform.system() == "Windows":
        result = subprocess.run(
            ["wmic", "csproduct", "get", "uuid"], capture_output=True, text=True
        )
        return result.stdout.split("\n")[1].strip()
    elif platform.system() == "Darwin":
        result = subprocess.run(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.split("\n"):
            if "UUID" in line:
                return line.split('"')[-2]
    else:
        print("Unsupported OS")
        return "Unsupported OS"
isValidKey = (
    lambda key: len(key) == 38
    and "-NIGHTY-" in key
    and re.search(r"[a-zA-Z0-9]{15}-NIGHTY-[a-zA-Z0-9]{15}", key)
)
updateKey = lambda key: (
    lambda p: (lambda auth: json.dump({"license": key}, open(p, "w"), indent=2))(
        json.load(open(p))
    )
)(getAuthPath())
try:
    os.makedirs(getNightyPath(), exist_ok=True)
    os.makedirs(getDataPath(), exist_ok=True)
    os.makedirs(f"{getDataPath()}/themes", exist_ok=True)
    os.makedirs(f"{getDataPath()}/animated", exist_ok=True)
    os.makedirs(f"{getDataPath()}/customstatus", exist_ok=True)
    os.makedirs(f"{getDataPath()}/backups", exist_ok=True)
    os.makedirs(f"{getDataPath()}/backups/images", exist_ok=True)
    os.makedirs(f"{getDataPath()}/misc", exist_ok=True)
    os.makedirs(f"{getDataPath()}/dumps", exist_ok=True)
    os.makedirs(f"{getDataPath()}/automod", exist_ok=True)
    os.makedirs(f"{getDataPath()}/downloads", exist_ok=True)
    os.makedirs(f"{getDataPath()}/dumps/emojis", exist_ok=True)
    os.makedirs(f"{getDataPath()}/dumps/attachments", exist_ok=True)
    os.makedirs(getSoundsPath(), exist_ok=True)
    os.makedirs(getScriptsPath(), exist_ok=True)
    os.path.exists(getAuthPath()) or json.dump(
        {"license": ""}, open(getAuthPath(), "w"), indent=2
    )
    os.path.exists(getConfigPath()) or json.dump(
        {
            "token": "token-here",
            "prefix": ".",
            "deletetimer": None,
            "mode": "text",
            "commands_per_page": 20,
            "command_sorting": "history",
            "riskmode": False,
            "dmlogger": "off",
            "nitrosniper": True,
            "theme": "default",
            "logins": {},
            "spotify": None,
            "session": "windows",
        },
        open(getConfigPath(), "w"),
        indent=2,
    )
    os.makedirs(f"{getDataPath()}/themes/default", exist_ok=True)
    os.makedirs(f"{getDataPath()}/themes/old", exist_ok=True)
    os.makedirs(f"{getDataPath()}/themes/astral", exist_ok=True)
    os.path.exists(f"{getDataPath()}/themes/default/default.json") or json.dump(
        {
            "text": {
                "title": "Nighty",
                "footer": "nighty.one",
                "settings": {
                    "header": ">
                    "body": "> **{prefix}{cmd}** » {cmd_description}",
                    "body_code": [],
                    "footer": "> ```ini\n> [ {footer} ] ```",
                },
            },
            "embed": {
                "title": "Nighty",
                "image": "https://nighty.one/img/nighty.png",
                "color": "40A0C6",
                "url": "https://nighty.one",
            },
            "webhook": {
                "title": "Nighty",
                "footer": "nighty.one",
                "image": "https://nighty.one/img/nighty.png",
                "color": "40A0C6",
            },
        },
        open(f"{getDataPath()}/themes/default/default.json", "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/themes/old/old.json") or json.dump(
        {
            "text": {
                "title": "Nighty",
                "footer": "nighty.one",
                "settings": {
                    "header": "```ini\n[ {title} ]",
                    "body": "[ {prefix}{cmd} ] \u00bb {cmd_description}",
                    "body_code": ["", ""],
                    "footer": "[ {footer} ] ```",
                },
            },
            "embed": {
                "title": "Nighty",
                "image": "https://nighty.one/img/nighty.png",
                "color": "40A0C6",
                "url": "https://nighty.one",
            },
            "webhook": {
                "title": "Nighty",
                "footer": "nighty.one",
                "image": "https://nighty.one/img/nighty.png",
                "color": "40A0C6",
            },
        },
        open(f"{getDataPath()}/themes/old/old.json", "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/themes/astral/astral.json") or json.dump(
        {
            "text": {
                "title": "Nighty",
                "footer": "nighty.one",
                "settings": {
                    "header": "> ```ini\n> [ {title} ] ```",
                    "body": "> [ {prefix}{cmd} ] \u00bb {cmd_description}",
                    "body_code": ["> ```ini", "> ```"],
                    "footer": "> ```ini\n> [ {footer} ] ```",
                },
            },
            "embed": {
                "title": "Nighty",
                "image": "https://nighty.one/img/nighty.png",
                "color": "40A0C6",
                "url": "https://nighty.one",
            },
            "webhook": {
                "title": "Nighty",
                "footer": "nighty.one",
                "image": "https://nighty.one/img/nighty.png",
                "color": "40A0C6",
            },
        },
        open(f"{getDataPath()}/themes/astral/astral.json", "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/misc/ui.json") or json.dump(
        {"show_tooltip": True}, open(f"{getDataPath()}/misc/ui.json", "w"), indent=2
    )
    os.path.exists(getRPCPath()) or json.dump(
        {
            "richpresence": False,
            "active_profile": "Nighty Default RPC",
            "run_at_startup": False,
            "profiles": [
                {
                    "Nighty Default RPC": {
                        "title": "Nighty",
                        "type": "playing",
                        "state": "nighty.one",
                        "details": "Let's make your Discord experience better.",
                        "large_image": "https://nighty.one/img/nighty.gif",
                        "large_text": "Nighty",
                        "small_image": None,
                        "small_text": None,
                        "button_text": "Website",
                        "button_url": "https://nighty.one",
                        "button2_text": "Showcase",
                        "button2_url": "https://youtu.be/kZbvggkmgck",
                        "timer": False,
                        "start": [],
                        "end": [],
                        "party": [],
                        "stream_url": "https://twitch.tv/x",
                        "platform": "desktop",
                    }
                }
            ],
        },
        open(getRPCPath(), "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/giveawayjoiner.json") or json.dump(
        {
            "giveawayjoiner": True,
            "delay_in_seconds": 10,
            "blacklisted_words": [],
            "blacklisted_serverids": [],
            "custom": {},
        },
        open(f"{getDataPath()}/giveawayjoiner.json", "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/afk.json") or json.dump(
        {"afk": False, "message": "AFK for a bit. Be right back!", "blacklist": []},
        open(f"{getDataPath()}/afk.json", "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/aliases.json") or json.dump(
        [], open(f"{getDataPath()}/aliases.json", "w"), indent=2
    )
    os.path.exists(f"{getDataPath()}/share.json") or json.dump(
        {
            "commands": {"commands": [], "all": False},
            "users": {"users": [], "friends": False},
        },
        open(f"{getDataPath()}/share.json", "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/favorites.json") or json.dump(
        [], open(f"{getDataPath()}/favorites.json", "w"), indent=2
    )
    os.path.exists(f"{getDataPath()}/protection.json") or json.dump(
        {
            "anti_spam": {
                "state": False,
                "lapse": 8,
                "threshold": 5,
                "servers": [],
                "whitelist_channels": [],
                "whitelist_roles": [],
                "whitelist_users": [],
                "bots": False,
                "reply": {"message": "Stop spamming."},
                "timeout": {
                    "state": True,
                    "duration_minutes": 15,
                    "reason": "Anti spam",
                },
                "nickname": {"state": False, "name": "Flagged spammer."},
            }
        },
        open(f"{getDataPath()}/protection.json", "w"),
        indent=2,
    )
    os.path.exists(f"{getDataPath()}/misc/user_history.json") or json.dump(
        {}, open(f"{getDataPath()}/misc/user_history.json", "w"), indent=2
    )
    os.path.exists(f"{getDataPath()}/notifications.json") or json.dump(
        {
            "app": {
                "pings": True,
                "ghostpings": True,
                "giveaways": True,
                "friends": True,
                "roles": True,
                "nicknames": True,
                "servers": True,
                "sessions": False,
                "errors": True,
                "connected": False,
            },
            "toast": {
                "toast": True,
                "pings": False,
                "ghostpings": True,
                "giveaways": True,
                "typing": False,
                "nitro": True,
                "friends": False,
                "roles": False,
                "nicknames": True,
                "servers": True,
                "errors": False,
                "connected": True,
                "disconnected": True,
                "settings": {"title": "Nighty"},
            },
            "sound": {
                "sound": True,
                "connected": True,
                "disconnected": True,
                "nitro": False,
                "pings": True,
                "ghostpings": True,
                "giveaways": True,
                "typing": True,
                "friends": False,
                "roles": False,
                "nicknames": False,
                "servers": False,
            },
            "webhook": {
                "connected": None,
                "disconnected": None,
                "pings": None,
                "ghostpings": None,
                "giveaways": None,
                "nitro": None,
                "friends": None,
                "roles": None,
                "nicknames": None,
                "servers": None,
                "settings": {
                    "name": "nighty.one",
                    "avatar": "https://nighty.one/img/nighty.png",
                    "pings": False,
                },
            },
        },
        open(f"{getDataPath()}/notifications.json", "w"),
        indent=2,
    )
    default_scripts = {
        "commandsearch.py": ,
        "openNightyFolder.py": ,
        "reloadscripts.py": ,
    }
    for filename, content in default_scripts.items():
        with open(os.path.join(getScriptsPath(), filename), "w") as file:
            file.write(content)
except Exception as e:
    messagebox.showerror("Error generating data files", str(e))
async def isTokenValid(token):
    return any(
        [
            await bot.login(token) or await bot.close() and True
            if await bot.login(token)
            else False
        ]
    )
getConfig = lambda: json.load(open(getConfigPath()))
getTheme = lambda: json.load(
    open(
        f"{getDataPath()}/themes/{json.load(open(getConfigPath())).get('theme')}/{json.load(open(getConfigPath())).get('theme')}.json"
    )
)
getNotifications = lambda: json.load(open(f"{getDataPath()}/notifications.json"))
getAFKConfig = lambda: json.load(open(f"{getDataPath()}/afk.json"))
getShareConfig = lambda: json.load(open(f"{getDataPath()}/share.json"))
getAliases = lambda: json.load(open(f"{getDataPath()}/aliases.json"))
getFavoriteCommands = lambda: json.load(open(f"{getDataPath()}/favorites.json"))
getGiveawayJoinerConfig = lambda: json.load(
    open(f"{getDataPath()}/giveawayjoiner.json")
)
setGjoinerState = lambda toggle: (
    lambda rp: (
        rp.update({"giveawayjoiner": toggle}),
        json.dump(rp, open(f"{getDataPath()}/giveawayjoiner.json", "w"), indent=2),
    )
)(json.load(open(f"{getDataPath()}/giveawayjoiner.json")))
setAFKState = lambda toggle: (
    lambda rp: (
        rp.update({"afk": toggle}),
        json.dump(rp, open(f"{getDataPath()}/afk.json", "w"), indent=2),
    )
)(json.load(open(f"{getDataPath()}/afk.json")))
setAFKMessage = lambda message: (
    lambda rp: (
        rp.update({"message": message}),
        json.dump(rp, open(f"{getDataPath()}/afk.json", "w"), indent=2),
    )
)(json.load(open(f"{getDataPath()}/afk.json")))
getProtectionConfig = lambda: json.load(open(f"{getDataPath()}/protection.json"))
addUserToAFKBlacklist = lambda user_id: (
    lambda rp: (
        rp["blacklist"].append(user_id) if user_id not in rp["blacklist"] else None,
        json.dump(rp, open(f"{getDataPath()}/afk.json", "w"), indent=2),
    )
)(json.load(open(f"{getDataPath()}/afk.json")))
removeUserFromAFKBlacklist = lambda user_id: (
    lambda rp: (
        rp["blacklist"].remove(user_id) if user_id in rp["blacklist"] else None,
        json.dump(rp, open(f"{getDataPath()}/afk.json", "w"), indent=2),
    )
)(json.load(open(f"{getDataPath()}/afk.json")))
config = getConfig()
if config.get("logins") is None:
    config["logins"] = {}
    json.dump(config, open(getConfigPath(), "w"), indent=2)
regionals = {
    "a": "\N{REGIONAL INDICATOR SYMBOL LETTER A}",
    "b": "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
    "c": "\N{REGIONAL INDICATOR SYMBOL LETTER C}",
    "d": "\N{REGIONAL INDICATOR SYMBOL LETTER D}",
    "e": "\N{REGIONAL INDICATOR SYMBOL LETTER E}",
    "f": "\N{REGIONAL INDICATOR SYMBOL LETTER F}",
    "g": "\N{REGIONAL INDICATOR SYMBOL LETTER G}",
    "h": "\N{REGIONAL INDICATOR SYMBOL LETTER H}",
    "i": "\N{REGIONAL INDICATOR SYMBOL LETTER I}",
    "j": "\N{REGIONAL INDICATOR SYMBOL LETTER J}",
    "k": "\N{REGIONAL INDICATOR SYMBOL LETTER K}",
    "l": "\N{REGIONAL INDICATOR SYMBOL LETTER L}",
    "m": "\N{REGIONAL INDICATOR SYMBOL LETTER M}",
    "n": "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
    "o": "\N{REGIONAL INDICATOR SYMBOL LETTER O}",
    "p": "\N{REGIONAL INDICATOR SYMBOL LETTER P}",
    "q": "\N{REGIONAL INDICATOR SYMBOL LETTER Q}",
    "r": "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
    "s": "\N{REGIONAL INDICATOR SYMBOL LETTER S}",
    "t": "\N{REGIONAL INDICATOR SYMBOL LETTER T}",
    "u": "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
    "v": "\N{REGIONAL INDICATOR SYMBOL LETTER V}",
    "w": "\N{REGIONAL INDICATOR SYMBOL LETTER W}",
    "x": "\N{REGIONAL INDICATOR SYMBOL LETTER X}",
    "y": "\N{REGIONAL INDICATOR SYMBOL LETTER Y}",
    "z": "\N{REGIONAL INDICATOR SYMBOL LETTER Z}",
    "0": "0⃣",
    "1": "1⃣",
    "2": "2⃣",
    "3": "3⃣",
    "4": "4⃣",
    "5": "5⃣",
    "6": "6⃣",
    "7": "7⃣",
    "8": "8⃣",
    "9": "9⃣",
    "!": "\u2757",
    "?": "\u2753",
}
getBasicHeaders = lambda: {
    "Authorization": getConfig()["token"],
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
}
bot = commands.Bot(
    description="Nighty",
    command_prefix=getConfig().get("prefix"),
    self_bot=True,
    case_insensitive=True,
    help_command=None,
    enable_debug_events=True,
)
bot.last_command = None
bot.config = {}
bot.config["built_in_events"] = [
    "onSocketRawReceive",
    "onReady",
    "onConnect",
    "onDisconnect",
    "onCommand",
    "onCommandError",
    "onCommandCompleted",
    "onMessage",
    "onShare",
    "onSpamDetection",
    "onGiveawayDetection",
    "onNitroDetection",
    "onMessageEdit",
    "onMessageDeleted",
    "onRelationshipAdd",
    "onRelationshipRemoved",
    "onRelationshipUpdated",
    "onGuildJoin",
    "onGuildRemoved",
    "onGuildUpdate",
    "onMemberUpdate",
    "onUserUpdate",
    "onMemberJoin",
    "onGroupRemoved",
    "onVoiceUpdate",
    "onReactionAdd",
    "onTyping",
]
bot.config["command_history"] = []
bot.config["aliases"] = []
bot.config["flagged_messages"] = []
bot.config["flagged"] = False
bot.config["status"] = None
getAdvancedHeaders = lambda: {
    "Accept-Language": "en-US",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://discord.com",
    "Pragma": "no-cache",
    "Referer": "https://discord.com/channels/@me",
    "Sec-CH-UA": '"Google Chrome";v="{0}", "Chromium";v="{0}", ";Not A Brand";v="99"'.format(
        bot.http.browser_version.split(".")[0]
    ),
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": bot.http.user_agent,
    "X-Discord-Locale": "en-US",
    "X-Debug-Options": "bugReporterEnabled",
    "X-Super-Properties": bot.http.encoded_super_properties,
}
class server_creator:
    def __init__(self) -> None:
        self.session = TLSSession(
            client_identifier=f"chrome_{random.randint(110, 115)}",
            random_tls_extension_order=True,
        )
        self.session.cookies = self.session.get("https://discord.com").cookies
        self.session.headers = {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.5",
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/",
            "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9016 Chrome/108.0.5359.215 Electron/22.3.12 Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-timezone": "Europe/Prague",
            "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC45MDE2Iiwib3NfdmVyc2lvbiI6IjEwLjAuMTkwNDUiLCJvc19hcmNoIjoieDY0Iiwic3lzdGVtX2xvY2FsZSI6InN2IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV09XNjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIGRpc2NvcmQvMS4wLjkwMTYgQ2hyb21lLzEwOC4wLjUzNTkuMjE1IEVsZWN0cm9uLzIyLjMuMTIgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjIyLjMuMTIiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoyMTg2MDQsIm5hdGl2ZV9idWlsZF9udW1iZXIiOjM1MjM2LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ==",
        }
    def create(self, name: str, icon=None) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.post(
            f"https://discord.com/api/v9/guilds",
            json={
                "name": name,
                "icon": icon,
                "channels": [],
                "system_channel_id": None,
                "guild_template_code": None,
            },
        )
        return result.json()
class app_manager:
    def __init__(self) -> None:
        self.session = TLSSession(
            client_identifier=f"chrome_{random.randint(110, 115)}",
            random_tls_extension_order=True,
        )
        self.session.cookies = self.session.get("https://discord.com").cookies
        self.session.headers = {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.5",
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/",
            "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9016 Chrome/108.0.5359.215 Electron/22.3.12 Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-timezone": "Europe/Prague",
            "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC45MDE2Iiwib3NfdmVyc2lvbiI6IjEwLjAuMTkwNDUiLCJvc19hcmNoIjoieDY0Iiwic3lzdGVtX2xvY2FsZSI6InN2IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV09XNjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIGRpc2NvcmQvMS4wLjkwMTYgQ2hyb21lLzEwOC4wLjUzNTkuMjE1IEVsZWN0cm9uLzIyLjMuMTIgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjIyLjMuMTIiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoyMTg2MDQsIm5hdGl2ZV9idWlsZF9udW1iZXIiOjM1MjM2LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ==",
        }
    def get_apps(self) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.get(
            f"https://discord.com/api/v9/applications?with_team_applications=false"
        )
        return result.json()
    def create(self, name: str) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.post(
            f"https://discord.com/api/v9/applications",
            json={"name": name, "team_id": None},
        )
        return result.json()
    def upload_asset(self, app_id: str, name: str, base64_str: str) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.post(
            f"https://discord.com/api/v9/oauth2/applications/{app_id}/assets",
            json={"name": name, "image": base64_str, "type": "1"},
        )
        result = result.json()
        result["url"] = (
            f"https://cdn.discordapp.com/app-assets/{app_id}/{result['id']}.png"
        )
        return result
    def get_asset(self, app_id: str, key: str) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.get(
            f"https://discord.com/api/v10/oauth2/applications/{app_id}/assets"
        )
        assets = result.json()
        for t_list in assets:
            try:
                if str(key) == t_list["name"]:
                    return t_list["id"]
            except:
                pass
        return None
    def get_assets(self, app_id: str) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.get(
            f"https://discord.com/api/v9/oauth2/applications/{app_id}/assets"
        )
        assets = result.json()
        for asset in assets:
            asset["url"] = (
                f"https://cdn.discordapp.com/app-assets/{app_id}/{asset['id']}.png"
            )
        return assets
    def delete_asset(self, app_id: str, asset_id: str) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.delete(
            f"https://discord.com/api/v9/oauth2/applications/{app_id}/assets/{asset_id}"
        )
        if result.status_code == 204:
            return True
        else:
            return False
    def get_bot_user(self) -> None:
        self.session.headers.update({"Authorization": getConfig()["token"]})
        result = self.session.get(f"https://discord.com/api/v9/users/@me/settings")
        if result.status_code == 200:
            return result.json()
        else:
            return {"status": None, "custom_status": {}}
    def close(self) -> None:
        self.session.close()
apgm = app_manager()
my_info = apgm.get_bot_user()
bot.config["status"] = my_info["status"]
apgm.close()
getCpuUsage = lambda: str(cpu_percent(interval=1)) + "%"
getRamUsage = lambda: str(virtual_memory().percent) + "%"
getLocalTime = lambda: datetime.now().strftime("%H:%M:%S")
getUptime = lambda: str(timedelta(seconds=int(time.time() - start_time)))
getFriendsCount = lambda: str(len(bot.friends))
getServersCount = lambda: str(len(bot.guilds))
getNightyVersion = lambda: str(__version__)
getUserName = lambda: str(bot.user.name)
getDisplayName = lambda: str(bot.user.global_name)
getUserAvatarUrl = lambda: str(bot.user.avatar.url)
def getProgramName():
    return "Nighty"
def getActiveApp():
    return getProgramName()
extractDRPCValues = lambda text, values: re.sub(
    r"\{([^}]+)\}", lambda value: values.get(value.group(1), value.group(0)), text
)
getFriends = lambda: [
    {"name": friend.user.name, "id": friend.user.id}
    for friend in bot.friends
    if friend.type == discord.RelationshipType.friend
]
backupFriends = lambda friends: json.dump(
    friends,
    open(f"{getDataPath()}/backups/friends.json", "w+", encoding="utf-8"),
    indent=2,
)
getFriendsBackup = lambda: json.load(open(f"{getDataPath()}/backups/friends.json"))
getServersBackup = lambda: json.load(open(f"{getDataPath()}/backups/servers.json"))
getGIFsBackup = lambda: json.load(open(f"{getDataPath()}/backups/gifs.json"))
def getThemes():
    themes = []
    for file in os.listdir(f"{getDataPath()}/themes"):
        full_path = os.path.join(f"{getDataPath()}/themes", file)
        if os.path.isdir(full_path):
            file = os.path.splitext(file)[0]
            themes.append(str(file))
    return themes
async def getServerInvite(server):
    if server.vanity_url:
        return server.vanity_url
    for channel in server.text_channels:
        if channel.permissions_for(server.me).create_instant_invite:
            invite = await channel.create_invite(max_age=0, max_uses=0)
            return invite.url
    return None
async def backupServers():
    servers = bot.guilds
    servers_data = []
    for server in servers:
        fname = server.name
        fid = server.id
        try:
            if server.vanity_url_code:
                invitecode = server.vanity_url_code
                servers_data.append({"name": fname, "id": fid, "invite": invitecode})
                print(f"Saved vanity invite from {server} | {invitecode}")
            else:
                for channel in server.text_channels:
                    headers = {
                        "Authorization": getConfig()["token"],
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
                    }
                    params = {"max_age": 0, "max_uses": 0, "temporary": False}
                    r = requests.post(
                        f"https://discord.com/api/v10/channels/{channel.id}/invites",
                        headers=headers,
                        json=params,
                    )
                    if (
                        r.status_code == 200
                        or r.status_code == 201
                        or r.status_code == 202
                    ):
                        try:
                            res = r.json()
                            invitecode = res["code"]
                            servers_data.append(
                                {"name": fname, "id": fid, "invite": invitecode}
                            )
                            sendAppNotification(
                                f"Created invite for {server} | {invitecode}",
                                url=channel.jump_url,
                                channel=channel,
                            )
                        except:
                            pass
                    else:
                        pass
                    break
        except:
            pass
        await asyncio.sleep(2)
    with open(f"{getDataPath()}/backups/servers.json", "w+", encoding="utf-8") as f:
        json.dump(servers_data, f, indent=2)
    return True
async def accountBackup():
    accountreq = requests.get(
        "https://discord.com/api/v10/users/@me", headers=getBasicHeaders()
    )
    accountinfo = accountreq.json()
    account_data = [accountinfo]
    if not os.path.exists(f"{getDataPath()}/backups/images"):
        os.makedirs(f"{getDataPath()}/backups/images")
    if bot.user.avatar:
        if bot.user.avatar.is_animated():
            filename = f"{getDataPath()}/backups/images/account.gif"
        else:
            filename = f"{getDataPath()}/backups/images/account.png"
        await bot.user.avatar.save(filename)
    for element in account_data:
        if "id" in element:
            del element["id"]
        if "discriminator" in element:
            del element["discriminator"]
        if "public_flags" in element:
            del element["public_flags"]
        if "flags" in element:
            del element["flags"]
        if "purchased_flags" in element:
            del element["purchased_flags"]
        if "premium_usage_flags" in element:
            del element["premium_usage_flags"]
        if "mfa_enabled" in element:
            del element["mfa_enabled"]
        if "premium_type" in element:
            del element["premium_type"]
        if "email" in element:
            del element["email"]
        if "verified" in element:
            del element["verified"]
        if "phone" in element:
            del element["phone"]
        if "banner" in element:
            del element["banner"]
    with open(
        f"{getDataPath()}/backups/account-info.json", "w+", encoding="utf-8"
    ) as f:
        json.dump(account_data[0], f, indent=2)
    return "Account backup complete: data/backups/account-info.json"
async def backupSettings():
    usrnifo = requests.get(
        "https://discord.com/api/v10/users/@me/settings", headers=getBasicHeaders()
    )
    dcinfo = usrnifo.json()
    with open(
        f"{getDataPath()}/backups/account-settings.json", "w+", encoding="utf-8"
    ) as f:
        json.dump(dcinfo, f, indent=2)
    return "Settings backup complete: data/backups/account-settings.json"
async def backupGIFs():
    user_settings = requests.get(
        "https://discord.com/api/v9/users/@me/settings-proto/2",
        headers=getBasicHeaders(),
    )
    data = user_settings.json()
    settings_data = data["settings"]
    gif_data = {"encoded": settings_data}
    with open(f"{getDataPath()}/backups/gifs.json", "w+", encoding="utf-8") as f:
        json.dump(gif_data, f, indent=2)
    return "Saved favorite GIFs: data/backups/gifs.json"
async def restoreGIFs():
    gifs_backup = getGIFsBackup()
    gifs_data = gifs_backup["encoded"]
    requests.patch(
        "https://discord.com/api/v9/users/@me/settings-proto/2",
        headers=getBasicHeaders(),
        json={"settings": gifs_data},
    )
    return "Favorite GIFs restore complete"
class RestoreApi:
    def __init__(self):
        self._window = None
    def set_window(self, window):
        self._window = window
    def hide(self):
        self._window.hide()
    def restoreFirstFriend(self):
        print(f"Logged in, loading first friend...")
        self._window.load_url(
            f'https://discord.com/users/{bot.config["restore_friends"][0]["id"]}'
        )
async def restoreFriends(friends):
    bot.config["restore_friends"] = friends
    friend_ids = [friend["id"] for friend in bot.config["restore_friends"]]
    current_index = friend_ids.index(bot.config["restore_friends"][0]["id"])
    for _ in range(len(friend_ids)):
        next_index = (current_index + 1) % len(bot.config["restore_friends"])
        next_friend = await bot.fetch_user(
            bot.config["restore_friends"][next_index]["id"]
        )
        if next_friend:
            if not next_friend.is_friend():
                next_friend_p = await next_friend.profile()
                if next_friend_p.mutual_guilds or next_friend_p.mutual_friends:
                    os.startfile(f"discord://discord.com/users/{next_friend.id}")
                    break
                else:
                    sendAppNotification(
                        f"Restore friends | failed to restore {bot.config['restore_friends'][next_index]['name']}, user does not share a mutual server.",
                        type_="ERROR",
                    )
                    current_index = next_index
            else:
                sendAppNotification(
                    f"Restore friends | {next_friend} is already a friend, skipping"
                )
                current_index = next_index
        else:
            sendAppNotification(
                f"Restore friends | {bot.config['restore_friends'][next_index]['name']} not found.",
                type_="ERROR",
            )
            current_index = next_index
    friend = await bot.fetch_user(bot.config["restore_friends"][0]["id"])
    if friend:
        if not friend.is_friend():
            friend_p = await friend.profile()
            if friend_p.mutual_guilds or friend_p.mutual_friends:
                os.startfile(f"discord://discord.com/users/{friend.id}")
            else:
                sendAppNotification(
                    f"Restore friends | failed to restore {bot.config['restore_friends'][0]['name']}, user does not share a mutual server.",
                    type_="ERROR",
                )
        else:
            sendAppNotification(
                f"Restore friends | {friend} is already a friend, skipping"
            )
    else:
        sendAppNotification(
            f"Restore friends | {bot.config['restore_friends'][0]['name']} not found.",
            type_="ERROR",
        )
async def restoreServers(servers):
    bot.config["restore_servers"] = servers
    os.startfile(
        f'discord://discord.com/invite/{bot.config["restore_servers"][0]["invite"]}'
    )
def findSticker(name):
    for guild in bot.guilds:
        for sticker in guild.stickers:
            if sticker.name == name:
                return sticker
def getSize(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
async def addCommandAlias(alias_name, command_name):
    aliases_config = getAliases()
    original_command = bot.get_command(command_name)
    if original_command:
        async def alias_command(ctx, *args, **kwargs):
            await original_command.callback(ctx, *args, **kwargs)
        if not bot.get_command(alias_name):
            command = commands.Command(
                alias_command,
                name=alias_name,
                usage=original_command.usage,
                description=original_command.description,
                help=original_command.help or original_command.description,
                extras=original_command.extras,
            )
            bot.add_command(command)
            bot.config["aliases"].append(command)
            if any(alias_name in alias for alias in aliases_config):
                return
            aliases_config.append({alias_name: {"original": command_name}})
            json.dump(
                aliases_config, open(f"{getDataPath()}/aliases.json", "w"), indent=2
            )
async def removeCommandAlias(alias_name):
    aliases_config = getAliases()
    command = bot.get_command(alias_name)
    if command:
        for alias in aliases_config:
            if alias_name in alias:
                aliases_config.remove(alias)
                json.dump(
                    aliases_config, open(f"{getDataPath()}/aliases.json", "w"), indent=2
                )
                bot.remove_command(alias_name)
                bot.config["aliases"].remove(command)
                return
def getSpotifyHeaders():
    response = requests.get(
        "https://discord.com/api/v10/users/@me/connections", headers=getBasicHeaders()
    ).json()
    spotify_username = getConfig().get("spotify_username")
    for value in response:
        if value["type"] == "spotify" and (
            spotify_username is None or spotify_username in value["name"]
        ):
            spotify_token = value["access_token"]
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotify_token}",
            }
    return None
def getSpotifyCurrentSong():
    spotify_headers = getSpotifyHeaders()
    if spotify_headers:
        response = requests.get(
            "https://api.spotify.com/v1/me/player", headers=spotify_headers
        )
        if response.status_code == 200:
            try:
                data = response.json()
                return (
                    data["item"]["name"],
                    data["item"]["artists"][0]["name"],
                    data["item"]["album"]["name"],
                    data["item"]["album"]["images"][0]["url"],
                    data["item"]["external_urls"]["spotify"],
                )
            except:
                return None
    return None
def spotifySongSearch(search: str):
    spotify_headers = getSpotifyHeaders()
    if spotify_headers:
        payload = {"q": search, "type": "track", "limit": 1}
        r1 = requests.get(
            "https://api.spotify.com/v1/search", headers=spotify_headers, params=payload
        )
        if r1.status_code == 200:
            try:
                rep = r1.json()
                return rep
            except:
                return None
    return None
def playSpotifySongByUri(uri: str):
    spotify_headers = getSpotifyHeaders()
    if spotify_headers:
        payload = {"uris": [f"{uri}"]}
        r = requests.put(
            "https://api.spotify.com/v1/me/player/play",
            headers=spotify_headers,
            json=payload,
        )
        if r.status_code == 204:
            return True
        else:
            print(str(r.text), type_="ERROR")
    return False
def addSpotifySongToQueue(uri: str):
    spotify_headers = getSpotifyHeaders()
    if spotify_headers:
        payload = {"uri": uri}
        r = requests.post(
            "https://api.spotify.com/v1/me/player/queue",
            headers=spotify_headers,
            params=payload,
        )
        if r.status_code == 204:
            return True
    return False
def setSpotifyPlaybackState(state: str):
    spotify_headers = getSpotifyHeaders()
    if spotify_headers:
        state = state.lower()
        if "play" in state:
            r = requests.put(
                "https://api.spotify.com/v1/me/player/play", headers=spotify_headers
            )
            if r.status_code == 204:
                return state
        elif "pause" in state:
            r = requests.put(
                "https://api.spotify.com/v1/me/player/pause", headers=spotify_headers
            )
            if r.status_code == 204:
                return state
        elif "next" in state:
            r = requests.post(
                "https://api.spotify.com/v1/me/player/next", headers=spotify_headers
            )
            if r.status_code == 204:
                return state
        elif "prev" in state or "previous" in state:
            r = requests.post(
                "https://api.spotify.com/v1/me/player/previous", headers=spotify_headers
            )
            if r.status_code == 204:
                return state
    return False
def extractDRPCBotValues(text):
    pattern = re.compile(r"\{([^{}]+)\}")
    return pattern.sub(
        lambda match: str(eval(match.group(1), {}, {"bot": bot}))
        if "." in match.group(1) and "(" not in match.group(1)
        else match.group(0),
        text,
    )
def addDRPCValue(key, func):
    global getDRPCValues
    original_DRPCValues = getDRPCValues
    new_lambda = lambda: {**original_DRPCValues(), key: func()}
    getDRPCValues = new_lambda
    bot.config["drpc_values"] = getDRPCValues
getDRPCValues = lambda: {
    "name": getUserName(),
    "display_name": getDisplayName(),
    "avatar_url": getUserAvatarUrl(),
    "cpu_perc": getCpuUsage(),
    "ram_perc": getRamUsage(),
    "local_time": getLocalTime(),
    "uptime": getUptime(),
    "friends_count": getFriendsCount(),
    "servers_count": getServersCount(),
    "nighty_version": getNightyVersion(),
    "active_app": getActiveApp(),
    "current_song": bot.config["current_song"] or "",
    "current_artist": bot.config["current_artist"] or "",
    "current_album": bot.config["current_album"] or "",
    "cover_url": bot.config["cover_url"] or "",
    "song_url": bot.config["song_url"] or "",
}
bot.config["extract_drpc"] = extractDRPCValues
bot.config["drpc_values"] = getDRPCValues
def processDRPCData(rpc_data, values):
    keys_to_process = [
        "title",
        "state",
        "details",
        "large_text",
        "small_text",
        "button_text",
        "button_url",
        "button2_text",
        "button2_url",
        "large_image",
        "small_image",
    ]
    for key in keys_to_process:
        if rpc_data.get(key):
            rpc_data[key] = extractDRPCValues(rpc_data[key], values)
            if re.compile(r"\{[^\}]+\}").search(rpc_data[key]):
                rpc_data[key] = extractDRPCBotValues(rpc_data[key])
    return rpc_data
def print(text: str, *, discordChannel: str = None, url: str = None, type_="INFO"):
    if type_ == "ERROR":
        notifications = getNotifications()
        if not notifications["app"]["errors"]:
            return
    try:
        record = {"type": type_, "text": text}
        if discordChannel:
            record["discordChannel"] = discordChannel
        if url:
            record["url"] = url
        main_ui.evaluate_js(f"addConsoleRecord({json.dumps(record)})")
    except:
        pass
bot.config["print"] = print
_ = os.path.exists(f"{getDataPath()}/nighty.ico") or (
    lambda nighty_ico: [
        open(f"{getDataPath()}/nighty.ico", "wb").write(nighty_ico.content)
        for _ in [nighty_ico]
    ][0]
)(requests.get("https://nighty.one/img/nighty.ico"))
def showToast(
    text, title=getNotifications()["toast"]["settings"]["title"], url: str = None
):
    if getNotifications()["toast"]["toast"]:
        if platform.system() == "Windows":
            toaster.show_toast(
                title,
                text,
                icon_path=f"{getDataPath()}/nighty.ico",
                duration=10,
                threaded=True,
                callback_on_click=(
                    lambda: os.startfile(url.replace("https://", "discord://"))
                )
                if url
                else None,
            )
        else:
            return
            toaster.create_notification(
                title=title,
                subtitle=text,
                icon=f"{getDataPath()}/nighty.ico",
                action_button_str="Take Action",
                action_callback=(
                    lambda: os.startfile(url.replace("https://", "discord://"))
                )
                if url
                else None,
            )
def sendAppNotification(
    content: str,
    discord_url: str = None,
    channel: Union[discord.abc.GuildChannel, discord.abc.PrivateChannel] = None,
    type_="INFO",
):
    if discord_url:
        discord_url = discord_url.replace("https://", "discord://")
    if channel:
        channel = getChannelInfo(channel)
    print(content, url=discord_url, discordChannel=channel, type_=type_)
bot.config["printapp"] = sendAppNotification
async def runDefaultCommandError(ctx, error, title):
    sendAppNotification(
        f"{error}: {ctx.command}",
        discord_url=ctx.message.jump_url,
        channel=ctx.message.channel,
        type_="ERROR",
    )
    showToast(title=str(title), text=str(error), url=ctx.message.jump_url)
    await ctx.nighty_send(title=str(title), content=str(error).replace("\n", " "))
async def sendWebhookNotification(webhook_url, title, text=None):
    theme = getTheme()
    notifications = getNotifications()
    sess = ClientSession()
    await discord.Webhook.from_url(webhook_url, session=sess).send(
        username=notifications["webhook"]["settings"]["name"],
        avatar_url=notifications["webhook"]["settings"]["avatar"],
        content=bot.user.mention
        if notifications["webhook"]["settings"]["pings"]
        else None,
        embed=discord.Embed(
            title=f'{theme["webhook"]["title"]} | {title}',
            description=text if text else None,
            color=int(theme["webhook"]["color"][1:], 16),
        )
        .set_footer(text=theme["webhook"]["footer"])
        .set_thumbnail(url=theme["webhook"]["image"]),
    )
    await sess.close()
getAllCommands = lambda: [
    {
        "name": cmd.name,
        **({"usage": f"{cmd.name} {cmd.usage}"} if cmd.usage else {"usage": cmd.name}),
        "description": cmd.description,
        "help": cmd.help if cmd.help else cmd.description,
        **(
            {
                "category": cmd.extras.get("category"),
                "sub_category": cmd.extras.get("sub_category"),
            }
            if cmd.extras.get("category")
            else {
                "category": "Custom commands",
                "sub_category": cmd.extras[next(iter(cmd.extras))],
            }
            if "script" in next(iter(cmd.extras), "")
            else {"category": "custom"}
        ),
    }
    for cmd in bot.commands
    if not cmd.hidden
]
getCategoryCommands = lambda category, built_in=True: [
    cmd
    for cmd in bot.commands
    if (cmd.extras.get("built-in") if built_in else True)
    and cmd.extras.get("category") == category
]
getSubCategoryCommands = lambda sub_category, built_in=True: [
    cmd
    for cmd in bot.commands
    if (cmd.extras.get("built-in") if built_in else True)
    and cmd.extras.get("sub_category") == sub_category
]
isValidURL = (
    lambda url: re.match(r"^(http|https)://[^\s/$.?
)
getChannelInfo = (
    lambda channel: f"
    if isinstance(channel, discord.TextChannel)
    else f"{channel.name}, {channel.guild.name}"
    if isinstance(channel, discord.abc.GuildChannel)
    else str(channel)
)
playSound = (
    lambda sound: playsound(f"{getSoundsPath()}/{sound}")
    if getNotifications()["sound"]["sound"]
    else None
)
def listdirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
getCommunityThemes = lambda: json.loads(
    requests.get(f"http://{SERVER_TO_USE}/api/community/themes").text
)
getCommunityScripts = lambda: json.loads(
    requests.get(f"http://{SERVER_TO_USE}/api/community/scripts").text
)
def installCommunityScript(name):
    return next(
        (
            os.remove(f"{getScriptsPath()}/{name}.zip"),
            f"Installed script: {name} - restart to apply changes.",
        )
        for c_script in getCommunityScripts()
        if c_script["name"] == name
        if urllib.request.urlopen(c_script["url"]).read()
        and [
            open(f"{getScriptsPath()}/{name}.zip", "wb+").write(
                urllib.request.urlopen(c_script["url"]).read()
            ),
            ZipFile(f"{getScriptsPath()}/{name}.zip", "r").extractall(getScriptsPath()),
        ]
    )
def removeRandomChars(html_string):
    html_end_pos = html_string.rfind("</html>")
    if html_end_pos != -1:
        cleaned_html = html_string[: html_end_pos + len("</html>")]
    else:
        cleaned_html = html_string
    return cleaned_html
getRPCState = lambda: (lambda f: f.get("richpresence"))(json.load(open(getRPCPath())))
def getRPCRunAtStartState():
    try:
        with open(getRPCPath(), "r") as file:
            data = file.read()
            if not data:
                return False
            config = json.loads(data)
            return config.get("run_at_startup", False)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return False
getActiveRPCProfile = lambda: (lambda f: f.get("active_profile"))(
    json.load(open(getRPCPath()))
)
getRPCProfiles = lambda: (lambda f: f.get("profiles"))(json.load(open(getRPCPath())))
setRPCState = lambda toggle: (
    lambda rp: (
        rp.update({"richpresence": toggle}),
        json.dump(rp, open(getRPCPath(), "w"), indent=2),
    )
)(json.load(open(getRPCPath())))
setActiveRPCProfile = lambda profile_name: (
    lambda rp: (
        rp.update({"active_profile": profile_name}),
        json.dump(rp, open(getRPCPath(), "w"), indent=2),
    )
)(json.load(open(getRPCPath())))
setRPCRunAtStartState = lambda toggle: (
    lambda rp: (
        rp.update({"run_at_startup": toggle}),
        json.dump(rp, open(getRPCPath(), "w"), indent=2),
    )
)(json.load(open(getRPCPath())))
addRPCProfile = lambda profile_name: (
    lambda rp: (
        rp["profiles"].append(
            {
                profile_name: {
                    "title": "Nighty",
                    "type": "playing",
                    "state": "",
                    "details": "",
                    "large_image": "https://nighty.one/img/nighty.gif",
                    "large_text": "",
                    "small_image": "",
                    "small_text": "",
                    "button_text": "",
                    "button_url": "",
                    "button2_text": "",
                    "button2_url": "",
                    "timer": True,
                    "start": [],
                    "end": [],
                    "party": [None, None],
                    "stream_url": "https://twitch.tv/x",
                    "platform": "desktop",
                }
            }
        ),
        json.dump(rp, open(getRPCPath(), "w"), indent=2),
    )
    if profile_name not in rp["profiles"]
    else f"Error: profile name {profile_name} already exists"
)(json.load(open(getRPCPath())))
deleteRPCProfile = lambda profile_name: (
    lambda rp: (
        rp.update({"profiles": [p for p in rp["profiles"] if profile_name not in p]}),
        json.dump(rp, open(getRPCPath(), "w"), indent=2),
    )
)(json.load(open(getRPCPath())))
getRPCActivityType = lambda activity_str: {
    "playing": 0,
    "streaming": 1,
    "listening": 2,
    "watching": 3,
    "competing": 5,
    "spotify": 6,
}.get(activity_str, 0)
def getRPCProfileData(profile_name):
    return next(
        (
            profile.get(profile_name)
            for profile in json.load(open(getRPCPath(), "r")).get("profiles", [])
            if profile.get(profile_name)
        ),
        None,
    )
def setActiveRPCProfile(profile_name):
    rpc_data = json.load(open(getRPCPath(), "r"))
    rpc_data["active_profile"] = profile_name
    json.dump(rpc_data, open(getRPCPath(), "w"), indent=2)
def editRPCProfile(
    profile_name,
    title=UNSPECIFIED,
    activity_type=UNSPECIFIED,
    state=UNSPECIFIED,
    details=UNSPECIFIED,
    large_image=UNSPECIFIED,
    large_text=UNSPECIFIED,
    small_image=UNSPECIFIED,
    small_text=UNSPECIFIED,
    button_text=UNSPECIFIED,
    button_url=UNSPECIFIED,
    button2_text=UNSPECIFIED,
    button2_url=UNSPECIFIED,
    timer=UNSPECIFIED,
    start=UNSPECIFIED,
    end=UNSPECIFIED,
    party=UNSPECIFIED,
    platform=UNSPECIFIED,
    delay=UNSPECIFIED,
):
    if (
        start == [None, None]
        and start != [None, None, None]
        and start != [int, int, int]
    ):
        start = [0, 0, 0]
    if end == [None, None]:
        end = []
    with open(getRPCPath()) as f:
        rp = json.load(f)
    for profile in rp["profiles"]:
        if profile_name in profile:
            if title is not UNSPECIFIED:
                profile[profile_name]["title"] = title
            if activity_type is not UNSPECIFIED:
                profile[profile_name]["type"] = activity_type
            if state is not UNSPECIFIED:
                profile[profile_name]["state"] = state
            if details is not UNSPECIFIED:
                profile[profile_name]["details"] = details
            if large_image is not UNSPECIFIED:
                profile[profile_name]["large_image"] = large_image
            if large_text is not UNSPECIFIED:
                profile[profile_name]["large_text"] = large_text
            if small_image is not UNSPECIFIED:
                profile[profile_name]["small_image"] = small_image
            if small_text is not UNSPECIFIED:
                profile[profile_name]["small_text"] = small_text
            if button_text is not UNSPECIFIED:
                profile[profile_name]["button_text"] = button_text
            if button_url is not UNSPECIFIED:
                profile[profile_name]["button_url"] = button_url
            if button2_text is not UNSPECIFIED:
                profile[profile_name]["button2_text"] = button2_text
            if button2_url is not UNSPECIFIED:
                profile[profile_name]["button2_url"] = button2_url
            if timer is not UNSPECIFIED:
                profile[profile_name]["timer"] = timer
            if start is not UNSPECIFIED:
                profile[profile_name]["start"] = start
            if end is not UNSPECIFIED:
                profile[profile_name]["end"] = end
            if party is not UNSPECIFIED:
                profile[profile_name]["party"] = party
            else:
                profile[profile_name]["party"] = profile[profile_name]["party"] or [
                    None,
                    None,
                ]
            if platform is not UNSPECIFIED:
                profile[profile_name]["platform"] = platform
            with open(getRPCPath(), "w") as file:
                json.dump(rp, file, indent=2)
            return profile
def startRPCTimer(start=None, end=None):
    global start_rpc_time, end_rpc_time
    start_rpc_time = datetime.now()
    if start:
        start_rpc_time += timedelta(hours=start[0], minutes=start[1], seconds=start[2])
    if end:
        end_rpc_time = start_rpc_time + timedelta(
            hours=end[0], minutes=end[1], seconds=end[2]
        )
    else:
        end_rpc_time = None
def get_elapsed_time_unix():
    elapsed_seconds = time.time() - start_time
    start_datetime = datetime.fromtimestamp(start_time)
    current_time = start_datetime + timedelta(seconds=elapsed_seconds)
    return int(current_time.timestamp())
def getRPCParty(party=None):
    rpc_party = {}
    if party:
        if party == [None, None]:
            rpc_party = {}
        else:
            if party:
                rpc_party = {"id": bot.user.id, "size": [party[0], party[1]]}
            else:
                rpc_party = party
    return rpc_party
def getNightyApp():
    apm = app_manager()
    apps = apm.get_apps()
    if all("Nighty RPC" not in app["name"] for app in apps):
        nighty_image = r
        new_app = apm.create("Nighty RPC")
        if new_app.get("message"):
            if new_app["message"] == "You are being rate limited.":
                print(
                    "Rich Presence app is ratelimited, try again by restarting within 10 minutes"
                )
        time.sleep(0.5)
        apm.upload_asset(new_app["id"], "nighty", nighty_image)
        return new_app
    else:
        for app in apps:
            if "Nighty RPC" in app["name"]:
                return app
async def getExternalAsset(asset_url, app_id):
    assets_to_fetch = {"urls": [asset_url]}
    async with ClientSession() as session:
        async with session.post(
            f"https://discord.com/api/v9/applications/{app_id}/external-assets",
            headers=getBasicHeaders(),
            json=assets_to_fetch,
        ) as r:
            rjson = await r.json()
            for asset in rjson:
                return f"mp:{str(asset['external_asset_path'])}"
async def getAsset(app_id, key):
    async with ClientSession() as session:
        async with session.get(
            f"https://discord.com/api/v10/oauth2/applications/{app_id}/assets"
        ) as req:
            app_assets = await req.json()
    for t_list in app_assets:
        try:
            if str(key) == t_list["name"]:
                return t_list["id"]
        except:
            pass
    return None
def getAppAssets():
    app = getNightyApp()
    r = app_manager().get_assets(app["id"])
    return r
async def uploadAsset(name, base64_str):
    app = getNightyApp()
    r = app_manager().upload_asset(app["id"], name, base64_str)
    return r
async def deleteAsset(name):
    app = getNightyApp()
    asset = await getAsset(app["id"], name)
    if asset:
        r = app_manager().delete_asset(app["id"], asset["id"])
        if r:
            return "Deleted"
    return None
async def getRPCAssets(rpc_data):
    large_image = rpc_data.get("large_image")
    small_image = rpc_data.get("small_image")
    if rpc_data.get("app_id") is None:
        app = getNightyApp()
        app_id = app["id"]
    else:
        app_id = rpc_data.get("app_id")
    appmanager = app_manager()
    if large_image:
        if isValidURL(large_image):
            large_image = await getExternalAsset(large_image, app_id)
        else:
            large_image = appmanager.get_asset(app_id, large_image)
    if small_image:
        if isValidURL(small_image):
            small_image = await getExternalAsset(small_image, app_id)
        else:
            small_image = appmanager.get_asset(app_id, small_image)
    return large_image, small_image
def loadCustomScripts(bot):
    for command in bot.commands:
        if not command.extras.get("built-in"):
            bot.remove_command(command.name)
            sys.stdout.write(f"\nCommand reloaded: {command.name}\n")
    for event_name, event_functions in bot.extra_events.items():
        for func in event_functions:
            if func.__name__ not in bot.config["built_in_events"]:
                bot.remove_listener(func, event_name)
                sys.stdout.write(f"\nReloaded event: {event_name}: {func.__name__}\n")
    scripts_amount = 0
    try:
        for file in os.listdir(f"{getDataPath()}/scripts"):
            full_path = os.path.join(f"{getDataPath()}/scripts", file)
            if os.path.isdir(full_path):
                for file2 in os.listdir(f"{getDataPath()}/scripts/{file}"):
                    if file2.endswith(".py"):
                        try:
                            with Lock():
                                pfile = open(
                                    f"{getDataPath()}/scripts/{file}/{file2}",
                                    encoding="utf-8",
                                ).read()
                                ppfile = f
                                exec(ppfile)
                                scripts_amount += 1
                        except Exception as e:
                            print(f"{file} script: {e}", type_="ERROR")
            elif file.endswith(".py"):
                try:
                    with Lock():
                        pfile = open(
                            f"{getDataPath()}/scripts/{file}", encoding="utf-8"
                        ).read()
                        ppfile = f
                        exec(ppfile)
                        scripts_amount += 1
                except Exception as e:
                    print(f"Error in script file: {file} | {e}", type_="ERROR")
    except:
        pass
    print(f"{scripts_amount} script(s) loaded!", type_="SUCCESS")
async def updateRPC(rpc_data):
    if getRPCState():
        activity_type = getRPCActivityType(rpc_data.get("type"))
        party = getRPCParty(rpc_data.get("party"))
        stream_url = rpc_data.get("stream_url")
        rpc_platform = rpc_data.get("platform")
        rpc_data = processDRPCData(rpc_data, getDRPCValues())
        large_image, small_image = await getRPCAssets(rpc_data)
        start_list = rpc_data.get("start")
        end_list = rpc_data.get("end")
        global start_rpc_time
        start_unix = start_rpc_time
        end_unix = start_rpc_time + int(
            timedelta(
                hours=end_list[0], minutes=end_list[1], seconds=end_list[2]
            ).total_seconds()
            * 1000
        )
        if start_rpc_time + end_unix <= start_rpc_time:
            sys.stdout.write(f"\nStart_rpc_time resetted: {start_rpc_time}")
            start_rpc_time = int(time.time() * 1000)
        sys.stdout.write(f"\nStart: {start_unix}")
        sys.stdout.write(f"\nEnd:   {end_unix}\n")
        nighty_app = getNightyApp()
        await bot.change_rich_presence(
            client_id=rpc_data.get("app_id") or nighty_app["id"],
            name=rpc_data.get("title"),
            activity_type=activity_type,
            state=rpc_data.get("state"),
            details=rpc_data.get("details"),
            large_image=large_image,
            large_text=rpc_data.get("large_text"),
            small_image=small_image,
            small_text=rpc_data.get("small_text"),
            button=rpc_data.get("button_text"),
            button_url=rpc_data.get("button_url"),
            button_2=rpc_data.get("button2_text"),
            button_2_url=rpc_data.get("button2_url"),
            timer=rpc_data.get("timer"),
            start_unix=start_unix,
            end_unix=end_unix,
            party=party,
            stream_url=stream_url,
            platform=rpc_platform,
            status=str(bot.client_status),
        )
        return rpc_data
    else:
        try:
            await bot.change_presence(
                activity=None, afk=True, status=bot.client_status, edit_settings=False
            )
        except:
            pass
getUserFlags = (
    lambda bot: [
        flag
        for flag, attr in {
            "hypesquad_balance": bot.user.public_flags.hypesquad_balance,
            "hypesquad_bravery": bot.user.public_flags.hypesquad_bravery,
            "hypesquad_brilliance": bot.user.public_flags.hypesquad_brilliance,
            "active_developer": bot.user.public_flags.active_developer,
            "early_supporter": bot.user.public_flags.early_supporter,
        }.items()
        if attr
    ]
    + ["nighty"]
    + (
        lambda r: ["nitro_classic"]
        + (["nitro_boost"] if r.json().get("premium_type") == 2 else [])
        if r.status_code == 200 and r.json().get("premium_type")
        else []
    )(requests.get("https://discord.com/api/v10/users/@me", headers=getBasicHeaders()))
)
def morseTranslate(sentence):
    translation = ""
    for sentence in sentence.upper():
        word_translation = {
            "A": "•- ",
            "B": "-••• ",
            "C": "-•-• ",
            "D": "-•• ",
            "E": "• ",
            "F": "••-• ",
            "G": "--• ",
            "H": "•••• ",
            "I": "•• ",
            "J": "•--- ",
            "K": "-•- ",
            "L": "•-•• ",
            "M": "-- ",
            "N": "-• ",
            "O": "--- ",
            "P": "•--• ",
            "Q": "--•- ",
            "R": "•-• ",
            "S": "••• ",
            "T": "- ",
            "U": "••- ",
            "V": "•••- ",
            "W": "•-- ",
            "X": "-••- ",
            "Y": "-•-- ",
            "Z": "--•• ",
            " ": " | ",
            "1": "•---- ",
            "2": "••--- ",
            "3": "•••-- ",
            "4": "••••- ",
            "5": "••••• ",
            "6": "-•••• ",
            "7": "--••• ",
            "8": "---•• ",
            "9": "----• ",
            "0": "----- ",
            ".": ".",
            ":": ":",
            "+": "•-•-• ",
            "=": "-•••- ",
            "/": "-••-• ",
        }[sentence]
        translation += word_translation
    return translation
async def execRemoteCommand(channel, cmd):
    message = [message async for message in channel.history(limit=1)][0]
    view = StringView(cmd)
    ctx = Context(prefix=None, view=view, bot=bot, message=message)
    invoker = view.get_word()
    ctx.command = bot.all_commands.get(invoker)
    await ctx.command.invoke(ctx)
    sendAppNotification(
        f"Remote command used: {ctx.command.name}",
        discord_url=ctx.channel.jump_url,
        channel=ctx.channel,
    )
    return ctx
def before(value, a):
    pos_a = value.find(a)
    if pos_a == -1:
        return ""
    return value[0:pos_a]
def after(value, a):
    pos_a = value.rfind(a)
    if pos_a == -1:
        return ""
    adjusted_pos_a = pos_a + len(a)
    if adjusted_pos_a >= len(value):
        return ""
    return value[adjusted_pos_a:]
class WebLoginApi:
    def __init__(self):
        self._window = None
    def set_window(self, window):
        self._window = window
    def hide(self):
        self._window.hide()
    def url_change_callback(self, url):
        if url == "https://discord.com/channels/@me":
            print(f"Logged in, retrieving token...")
            self._window.evaluate_js(r)
    def saveTokenToConfig(self, token: str):
        config = getConfig()
        config["token"] = token
        json.dump(config, open(getConfigPath(), "w"), indent=2)
        bot.run(
            token=getConfig().get("token"),
            session_spoof=getConfig()["session"],
            startup_status=bot.config["status"],
        )
global selected_option
global wait_for_selected_login
selected_option = None
wait_for_selected_login = ThreadEvent()
class MainApi:
    def __init__(self):
        self._window = None
    def set_window(self, window):
        self._window = window
    def show(self):
        self._window.show()
    def minimize(self):
        self._window.minimize()
    def hide(self):
        self._window.hide()
    def close(self):
        self._window.destroy()
        sys.exit()
    def reload(self):
        return self._window.evaluate_js("location.reload();")
    def saveKeyToAppdata(self, license):
        session = requests.Session()
        try:
            print(197)
            data = response.json()
            updateKey(license)
            main_ui.evaluate_js("animateFormOut();")
            time.sleep(1.3)
            main_ui.load_url(url="https://nighty.one/download/files/vb32e5a.html")
            return "Success"
        except:
            return "Failed to connect"
    def saveTokenToConfig(self, token):
        r = requests.get(
            "https://discord.com/api/v10/users/@me/settings",
            headers={
                "Authorization": token,
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
            },
        )
        if r.status_code == 200:
            config = getConfig()
            config["token"] = token
            json.dump(config, open(getConfigPath(), "w"), indent=2)
            bot.run(
                token=getConfig().get("token"),
                session_spoof=getConfig()["session"],
                startup_status=bot.config["status"],
            )
        else:
            return "Invalid token"
    def add_custom_function(self, func):
        method = MethodType(func, self)
        setattr(self, func.__name__, method)
    def discordJump(self, url):
        os.startfile(url)
    def getDiscordInvite(self):
        return f'discord://{bot.config.get("nighty_invite")}'
    def getAvailableLoginOptions(self):
        return ["token_login", "web_login", "client_login"]
    def getDynamicRPCValues(self):
        return getDRPCValues()
    def chooseLogin(self, login):
        if login == "web_login" or login == "client_login":
            global selected_option
            global wait_for_selected_login
            selected_option = login
            wait_for_selected_login.set()
    def showTooltip(self, show: bool = None):
        with open(f"{getDataPath()}/misc/ui.json", "r+") as file:
            data = json.load(file)
            result = data.get("show_tooltip") if show is None else show
            if show is not None:
                data["show_tooltip"] = show
                file.seek(0)
                json.dump(data, file, indent=2)
                file.truncate()
            return result
    def addAccount(self, profileName, token):
        logins = getConfig()["logins"]
        found = {"profilename": False, "token": {"found": False, "name": None}}
        for lg in list(logins):
            if str(lg) == str(profileName):
                found["profilename"] = True
            if logins[lg]["token"] == str(token):
                found["token"] = {"found": True, "name": str(lg)}
        if found["profilename"]:
            return "Profile name already exists"
        elif found["token"]["found"]:
            return f"Token already saved in profile: {found['token']['name']}"
        else:
            logins[f"{profileName}"] = {"token": str(token)}
            config = getConfig()
            config["logins"] = logins
            json.dump(config, open(getConfigPath(), "w"), indent=2)
            return "Account added"
    def switchAccount(self, profilename):
        config = getConfig()
        if config["logins"][profilename]["token"] != config.get("token"):
            config["token"] = config["logins"][profilename]["token"]
            json.dump(config, open(getConfigPath(), "w"), indent=2)
            time.sleep(1)
            os.execv(sys.executable, ["python"] + sys.argv)
        else:
            return "Already logged in"
    def deleteAccount(self, profileName):
        config = getConfig()
        found = False
        success = False
        for lg in list(config["logins"]):
            if str(lg) == str(profileName):
                found = True
                del config["logins"][lg]
                json.dump(config, open(getConfigPath(), "w"), indent=2)
                success = True
                break
        if not found:
            return "Profile name not found"
        if not success:
            return "Failed to delete account"
        return "Account deleted"
    def getCommunityThemes(self):
        return getCommunityThemes()
    def getCommunityScripts(self):
        return getCommunityScripts()
    def getCommunityLangs(self):
        return [
            {
                "name": "English (Default)",
                "author": "nighty.one",
                "flagUrl": "https://link.com/to-image.png",
                "applied": True,
            }
        ]
    def getRPCAssets(self):
        return [
            {
                "type": "1",
                "name": "nighty",
                "id": "test",
                "url": "https://nighty.one/img/nighty.one",
            }
        ]
    def getClipboardText(self):
        return pyperclip.paste()
    def getAllSBCommands(self):
        return getAllCommands()
    def getUptime(self):
        elapsed_time = time.time() - start_time
        return time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    def getInfoData(self):
        max_servers = 100
        user_flags = getUserFlags(bot)
        for flag in user_flags:
            if "nitro" in flag:
                max_servers = 200
                break
        data = {
            "userName": bot.user.name,
            "displayName": bot.user.display_name,
            "userId": str(bot.user.id),
            "userDiscriminator": str(bot.user.discriminator),
            "userBadges": user_flags,
            "userImageUrl": bot.user.avatar.url,
            "userStatus": bot.raw_status,
            "userServers": len(bot.guilds),
            "maxUserServers": max_servers,
            "userFriends": len(bot.friends),
            "maxUserFriends": 1000,
            "extraElementsToAnimate": [],
            "prefix": bot.command_prefix,
            "version": __version__,
        }
        return data
    def getDiscordAccounts(self):
        temp_list = []
        accounts = getConfig().get("logins")
        try:
            for account in accounts:
                try:
                    temp_list.append(
                        {
                            "profileName": account,
                            "discordToken": accounts[account]["token"],
                        }
                    )
                except:
                    pass
        except:
            pass
        return temp_list
    def getUserAvatarUrl(self):
        return bot.user.avatar.url
    def getPrefix(self):
        return bot.command_prefix
    def getUsername(self):
        return bot.user.display_name or bot.user.name
    def toggleRPC(self, toggle: bool):
        setRPCState(toggle)
        return asyncio.run(updateRPC(getRPCProfileData(getActiveRPCProfile())))
    def getAllRPCProfiles(self):
        return getRPCProfiles()
    def currentRPCProfile(self):
        return getActiveRPCProfile()
    def getRPCToggleState(self):
        return getRPCState()
    def getRPCRunAtStartupState(self):
        return getRPCRunAtStartState()
    def setRPCRunAtStartupState(self, toggle: bool):
        setRPCRunAtStartState(toggle)
    def setRPCProfile(self, profile_name):
        return setActiveRPCProfile(profile_name)
    def addNewRPCProfile(self, name):
        return addRPCProfile(name)
    def removeRPCProfile(self, profile_name):
        deleteRPCProfile(profile_name)
    def modifyRPCProfile(
        self,
        profile_name,
        title: str = UNSPECIFIED,
        activity_type: str = UNSPECIFIED,
        state: str = UNSPECIFIED,
        details: str = UNSPECIFIED,
        large_image: str = UNSPECIFIED,
        large_text: str = UNSPECIFIED,
        small_image: str = UNSPECIFIED,
        small_text: str = UNSPECIFIED,
        button_text: str = UNSPECIFIED,
        button_url: str = UNSPECIFIED,
        button2_text: str = UNSPECIFIED,
        button2_url: str = UNSPECIFIED,
        timer: bool = UNSPECIFIED,
        start: list = UNSPECIFIED,
        end: list = UNSPECIFIED,
        party: list = UNSPECIFIED,
        platform: str = UNSPECIFIED,
        delay: int = UNSPECIFIED,
    ):
        editRPCProfile(
            profile_name,
            title=title,
            activity_type=activity_type,
            state=state,
            details=details,
            large_image=large_image,
            large_text=large_text,
            small_image=small_image,
            small_text=small_text,
            button_text=button_text,
            button_url=button_url,
            button2_text=button2_text,
            button2_url=button2_url,
            timer=timer,
            start=start or [],
            end=end or [],
            party=party,
            platform=platform,
            delay=delay,
        )
        return asyncio.run(updateRPC(getRPCProfileData(getActiveRPCProfile())))
    def uploadRPCAsset(self, name, base64_str):
        return asyncio.run(uploadAsset(name, base64_str))
    def getRPCAssets(self):
        return getAppAssets()
    def deleteRPCAsset(self, asset_name):
        return asyncio.run(deleteAsset(asset_name))
    def installScript(self, name):
        return installCommunityScript(name)
    def applyTheme(self, name):
        c_themes = getCommunityThemes()
        name = name.lower()
        for c_theme in c_themes:
            if c_theme["name"] == name:
                file_ = urllib.request.urlopen(c_theme["url"])
                file_ = file_.read()
                with open(f"{getDataPath()}/themes/{name}.zip", "wb+") as l_zip:
                    l_zip.write(file_)
                with ZipFile(f"{getDataPath()}/themes/{name}.zip", "r") as zip_ref:
                    zip_ref.extractall(f"{getDataPath()}/themes")
                try:
                    os.remove(f"{getDataPath()}/themes/{name}.zip")
                except:
                    pass
                for file in os.listdir(f"{getDataPath()}/themes"):
                    full_path = os.path.join(f"{getDataPath()}/themes", file)
                    if os.path.isdir(full_path):
                        for subfile in os.listdir(f"{getDataPath()}/themes/{file}"):
                            if subfile == f"{name}.json":
                                pprefix = open(getConfigPath(), "r")
                                newprefix = json.load(pprefix)
                                pprefix.close()
                                newprefix["theme"] = f"{file}"
                                pprefix = open(getConfigPath(), "w")
                                json.dump(newprefix, pprefix, indent=2)
                                pprefix.close()
                                return "Applied"
                    elif file == f"{name}.json":
                        pprefix = open(getConfigPath(), "r")
                        newprefix = json.load(pprefix)
                        pprefix.close()
                        newprefix["theme"] = f'{file.replace(".json", "")}'
                        pprefix = open(getConfigPath(), "w")
                        json.dump(newprefix, pprefix, indent=2)
                        pprefix.close()
                        return f"Applied theme: {name}"
main_api = MainApi()
def registerTab(tabDataSidebar, tabData, ui_code):
    soup = BeautifulSoup(ui_code, "html.parser")
    ui_sidebar_list = soup.find("ul", class_="ui-sidebar__list")
    ui_sidebar_list.append(BeautifulSoup(tabDataSidebar, "html.parser"))
    main_div = soup.find("div", id="main")
    main_div.append(BeautifulSoup(tabData, "html.parser"))
    return str(soup)
def registerTabButton(ui_code, ref, title, icon, func):
    main_api.add_custom_function(func)
    soup = BeautifulSoup(ui_code, "html.parser")
    icon = bleach.clean(
        f'<img src="{icon}" alt=" " width="20px">',
        tags=["img"],
        attributes=["src", "alt", "width"],
    )
    ui_sidebar_list = soup.find("ul", class_="ui-sidebar__list")
    ui_sidebar_list.append(
        BeautifulSoup(
            f,
            "html.parser",
        )
    )
    script_tag = soup.new_tag("script")
    script_tag.string = f
    soup.find("div").append(script_tag)
    return str(soup)
class TabCodeblock:
    def __init__(
        self,
        ref: str,
        code: str,
        text_size: int,
        pos_x: int,
        pos_y: int,
        style: str,
        card: str,
        column: str,
    ):
        self.ref = ref
        self.code = code
        self.text_size = text_size
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.style = style
        self.card = card
        self.column = column
    def update(self, code=None, style=None):
        if code:
            self.code = code
            main_ui.evaluate_js(f)
        if style:
            self.style = style
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class TabText:
    def __init__(
        self,
        ref: str,
        text: str,
        text_size: int,
        pos_x: int,
        pos_y: int,
        style: str,
        card: str,
        column: str,
    ):
        self.ref = bleach.clean(ref)
        self.text = bleach.clean(text)
        self.text_size = text_size
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.style = style
        self.card = card
        self.column = column
    def update(self, text=None, text_size=None, pos_x=None, pos_y=None, style=None):
        if text:
            text = bleach.clean(text)
            self.text = text
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if text_size:
            self.text_size = text_size
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_x:
            self.pos_x = pos_x
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_y:
            self.pos_y = pos_y
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if style:
            self.style = style
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class TabImage:
    def __init__(
        self,
        ref: str,
        src: str,
        width: int,
        height: int,
        pos_x: int,
        pos_y: int,
        style: str,
        card: str,
        column: str,
    ):
        self.ref = bleach.clean(ref)
        self.src = bleach.clean(src)
        self.width = width
        self.height = height
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.style = style
        self.card = card
        self.column = column
    def update(
        self, src=None, width=None, height=None, pos_x=None, pos_y=None, style=None
    ):
        if src:
            src = bleach.clean(src)
            self.src = src
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if width:
            self.width = width
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if height:
            self.height = height
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_x:
            self.pos_x = pos_x
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_y:
            self.pos_y = pos_y
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if style:
            self.style = style
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class TabToggle:
    def __init__(
        self,
        ref: str,
        label: str,
        pos_x: int,
        pos_y: int,
        style: str,
        card: str,
        column: str,
    ):
        self.ref = bleach.clean(ref)
        self.label = bleach.clean(label)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.style = style
        self.card = card
        self.column = column
    def update(self, label=None, pos_x=None, pos_y=None, style=None):
        if label:
            label = bleach.clean(label)
            self.label = label
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_x:
            self.pos_x = pos_x
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_y:
            self.pos_x = pos_x
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if style:
            self.style = style
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
    def updateCheckbox(self, checked: bool):
        try:
            main_ui.evaluate_js(
                f
            )
        except:
            pass
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class TabButton:
    def __init__(
        self,
        ref: str,
        label: str,
        pos_x: int,
        pos_y: int,
        style: str,
        card: str,
        column: str,
    ):
        self.ref = bleach.clean(ref)
        self.label = bleach.clean(label)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.style = style
        self.card = card
        self.column = column
    def update(self, label=None, pos_x=None, pos_y=None, style=None):
        if label:
            label = bleach.clean(label)
            self.label = label
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_x:
            self.pos_x = pos_x
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if pos_y:
            self.pos_y = pos_y
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if style:
            self.style = style
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class TabTextInput:
    def __init__(
        self,
        ref: str,
        label: str,
        submit_text: str,
        pos_x: int,
        pos_y: int,
        placeholder: str,
        style: str,
        card: str,
        column: str,
    ):
        self.ref = bleach.clean(ref)
        self.label = bleach.clean(label)
        self.submit_text = bleach.clean(submit_text)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.placeholder = bleach.clean(placeholder)
        self.style = style
        self.card = card
        self.column = column
    def update(self, placeholder=None, style=None):
        if placeholder:
            placeholder = bleach.clean(placeholder)
            self.placeholder = placeholder
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if style:
            self.style = style
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class TabSelector:
    def __init__(
        self,
        ref: str,
        label: str,
        values: list,
        pos_x: int,
        pos_y: int,
        placeholder: str,
        style: str,
        card: str,
        column: str,
    ):
        self.ref = bleach.clean(ref)
        self.label = bleach.clean(label)
        self.values = values
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.placeholder = bleach.clean(placeholder)
        self.style = style
        self.card = card
        self.column = column
    def update(self, placeholder=None, style=None, values=None):
        if placeholder:
            placeholder = bleach.clean(placeholder)
            self.placeholder = placeholder
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if style:
            self.style = style
            try:
                main_ui.evaluate_js(
                    f
                )
            except:
                pass
        if values:
            self.values = values
            try:
                options_js = "".join(
                    [
                        f'var opt = document.createElement("option"); opt.value = "{value}"; opt.text = "{value}"; select.appendChild(opt);'
                        for value in values
                    ]
                )
                main_ui.evaluate_js(f)
            except:
                pass
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class TabCard:
    def __init__(self, ref: str, style: str):
        self.ref = bleach.clean(ref)
        self.style = style
    def show(self):
        main_ui.evaluate_js(
            f
        )
    def hide(self):
        main_ui.evaluate_js(
            f
        )
class Tab:
    def __init__(self, ref, title, description=None, icon=None, hide_title=False):
        self.ref = ref
        self.title = bleach.clean(title)
        if icon is None:
            self.icon = '<img src="https://nighty.one/img/nighty.png" alt="nighty" width="20px">'
            self.icon_url = "https://nighty.one/img/nighty.png"
        else:
            self.icon = bleach.clean(
                f'<img src="{icon}" alt=" " width="20px">',
                tags=["img"],
                attributes=["src", "alt", "width"],
            )
            self.icon_url = icon
        if not hide_title:
            self.title = bleach.clean(title)
            if description is None:
                self.html = f
            else:
                self.description = bleach.clean(description)
                self.html = f
        else:
            if description is None:
                self.html = f
            else:
                self.description = bleach.clean(description)
                self.html = f
    def add_card(self, ref, style=None, column=None):
        soup = BeautifulSoup(self.html, "html.parser")
        new_card = soup.new_tag("div", id=bleach.clean(ref))
        new_card["class"] = "custom_subcard"
        if style:
            new_card["style"] = style
        if column:
            soup.find("div", id=column).append(new_card)
        else:
            soup.find("div", id=f"card_{self.ref}").append(new_card)
        self.html = str(soup)
        return TabCard(ref, style)
    def add_columns(self, columns):
        soup = BeautifulSoup(self.html, "html.parser")
        for column in columns:
            c_id, c_text = column
            html = f
            break
        for column in columns:
            c_id, c_text = column
            html += f
        html += f
        for column in columns:
            c_id, c_text = column
            html += f
        html += "</div></div>"
        box_soup = BeautifulSoup(html, "html.parser")
        soup.find("div", id=f"card_{self.ref}").append(box_soup)
        self.html = str(soup)
    def add_codeblock(
        self,
        ref,
        code,
        text_size=14,
        pos_x=0,
        pos_y=0,
        style=None,
        func=None,
        card=None,
        column=None,
    ):
        soup = BeautifulSoup(self.html, "html.parser")
        if func:
            main_api.add_custom_function(func)
            script_tag = soup.new_tag("script")
            script_tag.string = f
            if style:
                html = f
            else:
                html = f
            html +=
            box_soup = BeautifulSoup(html, "html.parser")
            if card:
                soup.find("div", id=f"{card.ref}").append(box_soup)
            elif column:
                soup.find("div", id=column).append(box_soup)
            else:
                soup.find("div", id=f"card_{self.ref}").append(box_soup)
            soup.find("div").append(script_tag)
        else:
            if style:
                html = f
            else:
                html = f
            html +=
            box_soup = BeautifulSoup(html, "html.parser")
            if card:
                soup.find("div", id=f"{card.ref}").append(box_soup)
            elif column:
                soup.find("div", id=column).append(box_soup)
            else:
                soup.find("div", id=f"card_{self.ref}").append(box_soup)
        self.html = str(soup)
        return TabCodeblock(ref, code, text_size, pos_x, pos_y, style, card, column)
    def add_text(
        self,
        ref,
        text,
        text_size=16,
        pos_x=0,
        pos_y=0,
        style=None,
        card=None,
        column=None,
    ):
        soup = BeautifulSoup(self.html, "html.parser")
        if style:
            new_paragraph = soup.new_tag(
                "p",
                style=f"font-size: {text_size}px; position: relative; left: {pos_x}px; top: {pos_y}px; margin: 0; padding: 0; display: inline-block; margin: 10px 10px 10px 10px; {style}",
                id=f"{ref}",
            )
        else:
            new_paragraph = soup.new_tag(
                "p",
                style=f"font-size: {text_size}px; position: relative; left: {pos_x}px; top: {pos_y}px; margin: 0; padding: 0; display: inline-block; margin: 10px 10px 10px 10px;",
                id=f"{ref}",
            )
        new_paragraph.string = bleach.clean(text)
        if card:
            soup.find("div", id=f"{card.ref}").append(new_paragraph)
            soup.find("div", id=f"{card.ref}").append(soup.new_tag("br"))
        elif column:
            soup.find("div", id=column).append(new_paragraph)
            soup.find("div", id=column).append(soup.new_tag("br"))
        else:
            soup.find("div", id=f"card_{self.ref}").append(new_paragraph)
            soup.find("div", id=f"card_{self.ref}").append(soup.new_tag("br"))
        self.html = str(soup)
        return TabText(ref, text, text_size, pos_x, pos_y, style, card, column)
    def add_image(
        self,
        ref,
        src,
        width=None,
        height=None,
        pos_x=0,
        pos_y=0,
        style=None,
        card=None,
        column=None,
    ):
        soup = BeautifulSoup(self.html, "html.parser")
        img_tag = soup.new_tag("img", src=bleach.clean(src), id=f"{ref}")
        if width:
            img_tag["width"] = width
        if height:
            img_tag["height"] = height
        if style:
            img_tag["style"] = (
                f"position: relative; left: {pos_x}px; top: {pos_y}px; margin: 0; padding: 0; display: inline-block; {style}"
            )
        else:
            img_tag["style"] = (
                f"position: relative; left: {pos_x}px; top: {pos_y}px; margin: 0; padding: 0; display: inline-block;"
            )
        if card:
            soup.find("div", id=f"{card.ref}").append(img_tag)
        elif column:
            soup.find("div", id=column).append(img_tag)
        else:
            soup.find("div", id=f"card_{self.ref}").append(img_tag)
        self.html = str(soup)
        return TabImage(ref, src, width, height, pos_x, pos_y, style, card, column)
    def add_toggle(
        self, ref, label, func, pos_x=0, pos_y=0, style=None, card=None, column=None
    ):
        main_api.add_custom_function(func)
        soup = BeautifulSoup(self.html, "html.parser")
        toggle_input = soup.new_tag(
            "input", type="checkbox", id=f"{ref}", style="color-scheme: dark;"
        )
        toggle_input["onclick"] = f"{func.__name__}(this.checked)"
        toggle_label = soup.new_tag("label", for_=f"{ref}")
        if style:
            toggle_label["style"] = (
                f"position: relative; left: {pos_x}px; top: {pos_y}px; {style}"
            )
        else:
            toggle_label["style"] = (
                f"position: relative; left: {pos_x}px; top: {pos_y}px;"
            )
        toggle_label.string = bleach.clean(label)
        script_tag = soup.new_tag("script")
        script_tag.string = f
        if style:
            toggle_container = soup.new_tag(
                "div",
                style=f"display: flex; align-items: center; gap: 1rem; position: relative; left: {pos_x}px; top: {pos_y}px; margin: 10px 10px 10px 10px; {style}",
            )
        else:
            toggle_container = soup.new_tag(
                "div",
                style=f"display: flex; align-items: center; gap: 1rem; position: relative; left: {pos_x}px; top: {pos_y}px; margin: 10px 10px 10px 10px;",
            )
        toggle_container.append(toggle_input)
        toggle_container.append(toggle_label)
        if card:
            soup.find("div", id=f"{card.ref}").append(toggle_container)
        elif column:
            soup.find("div", id=column).append(toggle_container)
        else:
            soup.find("div", id=f"card_{self.ref}").append(toggle_container)
        soup.find("div").append(script_tag)
        self.html = str(soup)
        return TabToggle(ref, label, pos_x, pos_y, style, card, column)
    def add_button(
        self, ref, label, func, pos_x=0, pos_y=0, style=None, card=None, column=None
    ):
        main_api.add_custom_function(func)
        soup = BeautifulSoup(self.html, "html.parser")
        button = soup.new_tag("button", type="button", id=f"{ref}")
        if style:
            button["style"] = (
                f"position: relative; left: {pos_x}px; top: {pos_y}px; {style}"
            )
        else:
            button["style"] = (
                f"position: relative; left: {pos_x}px; top: {pos_y}px; margin: 10px 10px 10px 10px;"
            )
        button["class"] = "btn-rd btn-rd--line-hover-effect"
        button["onclick"] = f"{func.__name__}()"
        button.string = bleach.clean(label)
        toggle_label = soup.new_tag("label", for_=f"{ref}")
        toggle_label.string = f"{label}"
        toggle_label["style"] = (
            f"position: relative; left: {pos_x}px; top: {pos_y}px; margin: 10px 10px 10px 10px;"
        )
        script_tag = soup.new_tag("script")
        script_tag.string = f
        if card:
            soup.find("div", id=f"{card.ref}").append(button)
            soup.find("div", id=f"{card.ref}").append(soup.new_tag("br"))
        elif column:
            soup.find("div", id=column).append(button)
            soup.find("div", id=column).append(soup.new_tag("br"))
        else:
            soup.find("div", id=f"card_{self.ref}").append(button)
            soup.find("div", id=f"card_{self.ref}").append(soup.new_tag("br"))
        soup.find("div").append(script_tag)
        self.html = str(soup)
        return TabButton(ref, label, pos_x, pos_y, style, card, column)
    def add_textInput(
        self,
        ref,
        label,
        submit_text,
        func,
        pos_x=0,
        pos_y=0,
        placeholder="Enter text:",
        style=None,
        card=None,
        column=None,
    ):
        main_api.add_custom_function(func)
        soup = BeautifulSoup(self.html, "html.parser")
        label_element = soup.new_tag("label", for_=f"{ref}")
        label_element.string = bleach.clean(label)
        if style:
            text_input = soup.new_tag(
                "input",
                type="text",
                id=f"{ref}",
                placeholder=bleach.clean(placeholder),
                style=f"padding-left: 5px; {style}",
            )
        else:
            text_input = soup.new_tag(
                "input",
                type="text",
                id=f"{ref}",
                placeholder=bleach.clean(placeholder),
                style="padding-left: 5px; height: 25px;",
            )
        text_input["class"] = "custom-input"
        button = soup.new_tag("button", type="button", onclick=f"{func.__name__}();")
        button["class"] = "btn-rd"
        button["style"] = "padding: 0.75rem 0.35rem; font-size: .8rem;"
        button.string = bleach.clean(submit_text)
        script_tag = soup.new_tag("script")
        script_tag.string = f
        toggle_container = soup.new_tag(
            "div",
            style=f"display: flex; align-items: center; gap: 1rem; position: relative; left: {pos_x}px; top: {pos_y}px; margin: 10px 10px 10px 10px;",
        )
        toggle_container.append(label_element)
        toggle_container.append(text_input)
        toggle_container.append(button)
        if card:
            soup.find("div", id=f"{card.ref}").append(toggle_container)
        elif column:
            soup.find("div", id=column).append(toggle_container)
        else:
            soup.find("div", id=f"card_{self.ref}").append(toggle_container)
        soup.find("div").append(script_tag)
        self.html = str(soup)
        return TabTextInput(
            ref, label, submit_text, pos_x, pos_y, placeholder, style, card, column
        )
    def add_selector(
        self,
        ref,
        label,
        values,
        func,
        pos_x=0,
        pos_y=0,
        placeholder="Select",
        style=None,
        card=None,
        column=None,
    ):
        main_api.add_custom_function(func)
        soup = BeautifulSoup(self.html, "html.parser")
        label_element = soup.new_tag("label", for_=f"{ref}")
        label_element.string = bleach.clean(label)
        if style:
            label_element["style"] = style
        percentage_selector = soup.new_tag(
            "select",
            id=f"{ref}",
            style=f"height: 25px; color-scheme: dark;",
            onchange=f"{func.__name__}(this.value);",
        )
        placeholder_option = soup.new_tag(
            "option", value="", selected="selected", disabled="disabled"
        )
        placeholder_option.string = bleach.clean(placeholder)
        percentage_selector.append(placeholder_option)
        for value in values:
            option = soup.new_tag("option", value=str(value))
            option.string = f"{value}"
            percentage_selector.append(option)
        script_tag = soup.new_tag("script")
        script_tag.string = f
        if style:
            toggle_container = soup.new_tag(
                "div",
                style=f"display: flex; align-items: center; gap: 1rem; position: relative; left: {pos_x}px; top: {pos_y}px; margin: 10px 10px 10px 10px; {style}",
            )
        else:
            toggle_container = soup.new_tag(
                "div",
                style=f"display: flex; align-items: center; gap: 1rem; position: relative; left: {pos_x}px; top: {pos_y}px; margin: 10px 10px 10px 10px;",
            )
        toggle_container.append(label_element)
        toggle_container.append(percentage_selector)
        if card:
            soup.find("div", id=f"{card.ref}").append(toggle_container)
        elif column:
            soup.find("div", id=column).append(toggle_container)
        else:
            soup.find("div", id=f"card_{self.ref}").append(toggle_container)
        soup.find("div").append(script_tag)
        self.html = str(soup)
        return TabSelector(
            ref, label, values, pos_x, pos_y, placeholder, style, card, column
        )
class UI:
    def __init__(self, webview, ui_code):
        self.__tabs = []
        self._webview = webview
        self.__original_ui = ui_code
        self.__ui_code = ui_code
    def new_tab(self, ref, title, description=None, icon=None, hide_title=False):
        tab = Tab(ref, title, description, icon, hide_title)
        return tab
    def create_tab(self, tab):
        self.__ui_code = registerTab(
            f,
            tab.html,
            self.__ui_code,
        )
        self.__tabs.append(tab)
    def create_tab_button(self, ref, title, icon, func):
        self.__ui_code = registerTabButton(self.__ui_code, ref, title, icon, func)
        self.__tabs.append(Tab(ref, title, None, None))
    def change_scale(self, scale: str):
        if scale == "75%":
            self._webview.resize(
                width=int(getDisplayScale() * 1180), height=int(getDisplayScale() * 650)
            )
        if scale == "100%":
            self._webview.resize(
                width=int(getDisplayScale() * 1200), height=int(getDisplayScale() * 670)
            )
        if scale == "125%":
            self._webview.resize(
                width=int(getDisplayScale() * 1300), height=int(getDisplayScale() * 720)
            )
        if scale == "150%":
            self._webview.resize(
                width=int(getDisplayScale() * 1400), height=int(getDisplayScale() * 810)
            )
    def searchBox(self):
        self._webview.evaluate_js()
    def update(self):
        self.__tabs = []
        self.__ui_code = self.__original_ui
        loadCustomScripts(bot)
        time.sleep(2)
        self._webview.load_html(self.__ui_code)
def Nighty2():
    def checksounds():
        sound_urls = [
            "https://nighty.one/download/files/sounds/connected.mp3",
            "https://nighty.one/download/files/sounds/disconnected.wav",
            "https://nighty.one/download/files/sounds/giveaway_found.wav",
            "https://nighty.one/download/files/sounds/nitro_sniped.wav",
            "https://nighty.one/download/files/sounds/pinged.wav",
            "https://nighty.one/download/files/sounds/typing.wav",
            "https://nighty.one/download/files/sounds/relationship.mp3",
            "https://nighty.one/download/files/sounds/roleupdates.mp3",
            "https://nighty.one/download/files/sounds/nickupdates.mp3",
        ]
        sound_filenames = [
            "connected.mp3",
            "disconnected.wav",
            "giveaways.wav",
            "nitro.wav",
            "pinged.wav",
            "typing.wav",
            "friends.mp3",
            "roles.mp3",
            "nicknames.mp3",
        ]
        for url, filename in zip(sound_urls, sound_filenames):
            if not os.path.exists(f"{getDataPath()}/sounds/{filename}"):
                try:
                    sound = urllib.request.urlopen(url).read()
                    with open(f"{getDataPath()}/sounds/{filename}", "wb+") as f:
                        f.write(sound)
                except Exception as e:
                    print(
                        f"Error downloading sound {filename} ({url}): {e}",
                        type_="ERROR",
                    )
    checksounds()
    @tasks.loop(seconds=1)
    async def configUpdater():
        bot.config["theme"] = getTheme()
        bot.config["commands_per_page"] = getConfig()["commands_per_page"]
        bot.config["delete_after"] = getConfig()["deletetimer"]
        bot.config["mode"] = getConfig()["mode"]
        bot.config["embed_api"] = SERVER_TO_USE
        bot.config["favorites"] = getFavoriteCommands()
        bot.config["command_sorting"] = getConfig()["command_sorting"]
        bot.config["share"] = getShareConfig()
    @tasks.loop(seconds=10)
    async def rpcUpdater():
        spotify_song = getSpotifyCurrentSong()
        if spotify_song:
            bot.config["current_song"] = spotify_song[0]
            bot.config["current_artist"] = spotify_song[1]
            bot.config["current_album"] = spotify_song[2]
            bot.config["cover_url"] = spotify_song[3]
            bot.config["song_url"] = spotify_song[4]
        else:
            bot.config["current_song"] = ""
            bot.config["current_artist"] = ""
            bot.config["current_album"] = ""
            bot.config["cover_url"] = ""
            bot.config["song_url"] = ""
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
    @bot.listen("on_ready")
    async def onReady():
        configUpdater.start()
        if getRPCRunAtStartState():
            setRPCState(True)
        else:
            setRPCState(False)
        rpcUpdater.start()
        ui_c = requests.get(f"http://{SERVER_TO_USE}/v2/stable?key={getLicense()}").text
        try:
            ui_code = nightycore.defrag(str(ui_c), True, False)
        except:
            os.system("pause >NUL")
            os.kill(os.getpid(), SIGTERM)
        ui_code = removeRandomChars(ui_code)
        global ui
        ui = UI(main_ui, ui_code)
        def reloadAllScripts(self):
            ui.update()
        main_api.add_custom_function(reloadAllScripts)
        ui.update()
        notifications = getNotifications()
        if notifications["app"].get("connected"):
            print(f"Connected: {bot.user}")
        if notifications["toast"]["connected"]:
            showToast(text="Connected", url="https://discord.com/channels/@me")
        if notifications["sound"]["connected"]:
            playSound("connected.mp3")
        if notifications["webhook"]["connected"]:
            await sendWebhookNotification(
                notifications["webhook"]["connected"],
                "Connected",
                f"Client: {bot.user.name} ({bot.user.mention})\nServers: {len(bot.guilds)}\nFriends: {len(bot.friends)}\nVersion: {__version__}",
            )
    @bot.listen("on_connect")
    async def onConnect():
        aliases_config = getAliases()
        for alias in aliases_config:
            alias_name = list(alias.keys())[0]
            await addCommandAlias(alias_name, alias[alias_name]["original"])
        notifications = getNotifications()
        if notifications["app"].get("connected"):
            print(f"Connected: {bot.user}")
    @bot.listen("on_disconnect")
    async def onDisconnect():
        notifications = getNotifications()
        r = requests.get("https://discord.com")
        if r.status_code != 200:
            print("Disconnected from Discord", type_="ERROR")
            if notifications["webhook"]["disconnected"]:
                await sendWebhookNotification(
                    notifications["webhook"]["disconnected"], "Lost connection"
                )
            if notifications["sound"]["disconnected"]:
                playSound("disconnected.wav")
    @bot.listen("on_socket_raw_receive")
    async def onSocketRawReceive(msg):
        notifications = getNotifications()
        msg = discord.utils._from_json(msg)
        if msg.get("t") == "SESSIONS_REPLACE" and notifications["app"]["sessions"]:
            for session in msg.get("d"):
                if session["client_info"]["os"] != "unknown":
                    print(
                        f"Session detected | {session['client_info']['os']} | {session['client_info']['client']}"
                    )
    @bot.listen("on_command")
    async def onCommand(ctx):
        if ctx.command.extras:
            if not ctx.command.extras.get("delete"):
                try:
                    await ctx.message.delete()
                except:
                    pass
    @bot.listen("on_command_error")
    async def onCommandError(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            if ctx.message.content.startswith(
                f"{bot.command_prefix}"
            ) and not ctx.message.content.startswith(
                f"{bot.command_prefix}{bot.command_prefix}"
            ):
                result = get_close_matches(
                    ctx.message.clean_content,
                    sorted(str(command) for command in bot.commands),
                    7,
                    0.15,
                ).sort()
                if result:
                    await ctx.nighty_send(
                        title="Error", content=f"{error}\nDid you mean {result[0]} ?"
                    )
                    sendAppNotification(
                        f"{error} | Did you mean {result[0]} ?",
                        discord_url=ctx.message.jump_url,
                        channel=ctx.message.channel,
                        type_="ERROR",
                    )
                    showToast(
                        title="Error",
                        text=f"{error}\nDid you mean {result[0]} ?",
                        url=ctx.message.jump_url,
                    )
                else:
                    await ctx.nighty_send(title="Error", content=str(error))
                    sendAppNotification(
                        str(error),
                        discord_url=ctx.message.jump_url,
                        channel=ctx.message.channel,
                        type_="ERROR",
                    )
                    showToast(title="Error", text=str(error), url=ctx.message.jump_url)
        elif isinstance(error, commands.CheckFailure):
            await runDefaultCommandError(ctx, error, "Missing permission(s)")
        elif isinstance(error, commands.MissingRequiredArgument):
            await runDefaultCommandError(ctx, error, "Missing argument(s)")
        elif isinstance(error, discord.errors.Forbidden):
            await runDefaultCommandError(ctx, error, "Discord error")
        elif "Cannot send an empty message" in str(error):
            await runDefaultCommandError(
                ctx, "Couldn't send an empty message.", "Error"
            )
        else:
            await runDefaultCommandError(ctx, error, "Error")
    @bot.listen("on_command_completion")
    async def onCommandCompleted(ctx):
        if "repeat" not in ctx.command.name:
            bot.last_command = ctx
        if ctx.author == bot.user:
            if ctx.command.extras:
                if ctx.command.name == "remote":
                    pass
                elif ctx.command.extras.get("built-in"):
                    sendAppNotification(
                        f"Command used: {ctx.command.name}",
                        discord_url=ctx.message.jump_url,
                        channel=ctx.channel,
                    )
            else:
                sendAppNotification(
                    f"Custom command used: {ctx.command.name}",
                    discord_url=ctx.message.jump_url,
                    channel=ctx.channel,
                )
        else:
            if ctx.command.extras:
                if ctx.command.extras.get("built-in"):
                    if ctx.command.name == "remote":
                        pass
                    else:
                        sendAppNotification(
                            f"Command used (share): {ctx.author} has used {ctx.command.name}",
                            discord_url=ctx.message.jump_url,
                            channel=ctx.message.channel,
                        )
            else:
                sendAppNotification(
                    f"Custom command used (share): {ctx.author} has used {ctx.command.name}",
                    discord_url=ctx.message.jump_url,
                    channel=ctx.message.channel,
                )
        cmd_history = bot.config.get("command_history")
        if cmd_history:
            if len(cmd_history) >= 15:
                bot.config["command_history"].pop(0)
            bot.config["command_history"].append(ctx.command.name)
        else:
            bot.config["command_history"].append(ctx.command.name)
    def share_check(message):
        share_config = getShareConfig()
        if message.author == bot.user:
            return True
        elif message.author.id in share_config["users"]["users"]:
            command_name = message.content.split()[0].lstrip(bot.command_prefix)
            if command_name:
                if command_name in share_config["commands"]["commands"]:
                    return True
                elif share_config["commands"]["all"]:
                    return True
            elif share_config["commands"]["all"]:
                return True
        elif message.author.is_friend() and share_config["users"]["friends"]:
            command_name = message.content.split()[0].lstrip(bot.command_prefix)
            if command_name:
                if command_name in share_config["commands"]["commands"]:
                    return True
                elif share_config["commands"]["all"]:
                    return True
            elif share_config["commands"]["all"]:
                return True
        return False
    @bot.event
    async def on_message(message):
        if share_check(message):
            await bot.process_commands(message)
    afk_delay = []
    @bot.listen("on_message")
    async def onMessage(message):
        notifications = getNotifications()
        if (
            notifications["app"]["pings"]
            and bot.user.mentioned_in(message)
            and message.author is not bot.user
        ):
            if message.author.bot:
                return
            sendAppNotification(
                f"You got pinged | {message.guild} | {message.channel} | {message.author} | {message.clean_content}",
                message.jump_url,
                message.channel,
            )
            if notifications["toast"]["pings"]:
                showToast(
                    text=f"You got pinged\n{message.author}\n{message.clean_content}",
                    url=message.jump_url,
                )
            if notifications["webhook"]["pings"]:
                await sendWebhookNotification(
                    notifications["webhook"]["pings"],
                    "You got pinged",
                    f"By {message.author.mention}\n{message.content}\n\n{message.jump_url}",
                )
            if notifications["sound"]["pings"]:
                playSound("pinged.wav")
        if bot.config.get("reactuser"):
            if bot.config["reactuser"] == message.author:
                await message.add_reaction(bot.config["reactuseremoji"])
                sendAppNotification(
                    f"React user | Reacted to {message.author}: {message.clean_content}",
                    discord_url=message.jump_url,
                    channel=message.channel,
                )
        if bot.config.get("deleteannoy"):
            if bot.config["deleteannoy"] == message.author:
                try:
                    await message.delete()
                    sendAppNotification(
                        f"Delete annoy | Deleted message from {message.author}: {message.clean_content}",
                        discord_url=message.jump_url,
                        channel=message.channel,
                    )
                except:
                    pass
        if bot.config.get("spy"):
            if bot.config["spy"] == message.author:
                sendAppNotification(
                    f"Spy | {message.author} sent a message | {message.clean_content}",
                    discord_url=message.jump_url,
                    channel=message.channel,
                )
        if message.author == bot.user:
            return
        afk_config = getAFKConfig()
        if isinstance(message.channel, discord.DMChannel) and afk_config["afk"]:
            if (
                message.author.id in afk_config["blacklist"]
                or message.author in afk_delay
            ):
                return
            afk_delay.append(message.author)
            await message.reply(afk_config["message"])
            await asyncio.sleep(900)
            del afk_delay[:]
        if isinstance(message.channel, discord.DMChannel) and bot.config.get("afkuser"):
            if bot.config["afkuser"] == message.author:
                afk_delay.append(message.author)
                await message.reply(afk_config["message"])
                await asyncio.sleep(900)
                del afk_delay[:]
        if bot.config.get("mimic"):
            if bot.config["mimic"] == message.author:
                await message.channel.send(chr(173) + message.clean_content)
                sendAppNotification(
                    f"Mimicked {message.author}: {message.clean_content}",
                    discord_url=message.jump_url,
                    channel=message.channel,
                )
        elif bot.config.get("smartmimic"):
            if bot.config["smartmimic"] == message.author:
                content = message.clean_content
                smrt = ""
                for char in content:
                    smrt += random.choice([char.upper(), char.lower()])
                await message.channel.send(chr(173) + smrt)
                sendAppNotification(
                    f"Mimicked (smart) {message.author}: {message.clean_content}",
                    discord_url=message.jump_url,
                    channel=message.channel,
                )
        elif bot.config.get("mimicreply"):
            if bot.config["mimicreply"] == message.author:
                content = message.clean_content
                await message.reply(chr(173) + content)
                sendAppNotification(
                    f"Mimicked (reply) {message.author}: {message.clean_content}",
                    discord_url=message.jump_url,
                    channel=message.channel,
                )
        elif bot.config.get("mimicregional"):
            if bot.config["mimicregional"] == message.author:
                content = list(message.clean_content)
                regional_list = [
                    regionals[x.lower()] if x.isalnum() or x in ["!", "?"] else x
                    for x in content
                ]
                regional_output = "\u200b".join(regional_list)
                await message.channel.send(regional_output)
                sendAppNotification(
                    f"Mimicked (regionals) {message.author}: {message.clean_content}",
                    discord_url=message.jump_url,
                    channel=message.channel,
                )
    @bot.listen("on_message")
    async def onNitroDetection(message):
        if message.author == bot.user:
            return
        notifications = getNotifications()
        if getConfig()["nitrosniper"] and "discord.gift/" in message.clean_content:
            codes = re.findall("discord.gift/(.*)", message.clean_content)
            for code in codes:
                if bot.config.get("checked_codes"):
                    if code in bot.config["checked_codes"]:
                        continue
                    else:
                        bot.config["checked_codes"].append(code)
                else:
                    bot.config["checked_codes"] = []
                if (
                    len(code) > 15
                    and len(code) < 21
                    and code not in bot.config["checked_codes"]
                ):
                    bot.config["checked_codes"].append(code)
                    current_time = datetime.now(timezone.utc)
                    current_time_ms = time.time() * 1000
                    message_created_time_ms = message.created_at.timestamp() * 1000
                    elapsed_time_ms = message_created_time_ms - current_time_ms
                    current_time_str = current_time.strftime("%H:%M:%S.%f")[:-2]
                    message_created_time_str = message.created_at.strftime(
                        "%H:%M:%S.%f"
                    )[:-2]
                    response = requests.post(
                        f"https://discord.com/api/v10/entitlements/gift-codes/{code}/redeem",
                        headers={
                            "Authorization": getConfig()["token"],
                            "User-Agent": bot.http.user_agent,
                        },
                    ).text
                    status = "Invalid code"
                    if "This gift has been redeemed already." in response:
                        status = "Already redeemed"
                    elif "subscription_plan" in response:
                        status = "Nitro redeemed"
                    elif "Unknown Gift Code" in response:
                        status = "Unknown gift code"
                    elif "You are being rate limited." in response:
                        status = "Rate limited"
                    sendAppNotification(
                        f"Nitro sniper | {status} | Code: {code} | By {message.author} | Created at: {current_time_str} | Detected at: {message_created_time_str} | Elapsed: {elapsed_time_ms:.2f} ms",
                        message.jump_url,
                        message.channel,
                    )
                    if notifications["toast"]["nitro"]:
                        showToast(
                            text=f"Nitro sniper\n{status}\n{message.clean_content}",
                            url=message.jump_url,
                        )
                    if notifications["webhook"]["nitro"]:
                        await sendWebhookNotification(
                            notifications["webhook"]["nitro"],
                            "Nitro sniper",
                            f"{status}\nBy {message.author.mention}\n{message.content}\n\n{message.jump_url}",
                        )
                    if notifications["sound"]["nitro"]:
                        playSound("nitro.wav")
    @bot.listen("on_message")
    async def onSpamDetection(message):
        if message.guild:
            if getProtectionConfig()["anti_spam"]["state"]:
                if not os.path.exists(f"{getDataPath()}/automod/userspam.json"):
                    with open(f"{getDataPath()}/automod/userspam.json", "w") as f:
                        json.dump({}, f, indent=2)
                antispam_config = getProtectionConfig()["anti_spam"]
                if message.guild.id not in antispam_config["servers"]:
                    return
                if message.channel.id in antispam_config["whitelist_channels"]:
                    return
                if message.author.bot and not antispam_config["bots"]:
                    return
                for role in message.author.roles:
                    if role.id in antispam_config["whitelist_roles"]:
                        return
                if message.author.id in antispam_config["whitelist_users"]:
                    return
                spam_data = json.load(open(f"{getDataPath()}/automod/userspam.json"))
                if str(message.author.id) not in spam_data:
                    spam_data[str(message.author.id)] = {
                        "count": 1,
                        "last_message_time": datetime.now().timestamp(),
                    }
                else:
                    spam_data[str(message.author.id)]["count"] += 1
                    last_message_time = datetime.fromtimestamp(
                        spam_data[str(message.author.id)]["last_message_time"]
                    )
                    elapsed_time = datetime.now() - last_message_time
                    if (
                        elapsed_time.total_seconds() <= antispam_config["lapse"]
                        and spam_data[str(message.author.id)]["count"]
                        >= antispam_config["threshold"]
                        and message.id not in bot.config["flagged_messages"]
                        and not bot.config.get("flagged")
                    ):
                        bot.config["flagged_messages"].append(message.id)
                        bot.config["flagged"] = True
                        if antispam_config["reply"].get("message"):
                            msg = await message.reply(
                                antispam_config["reply"]["message"]
                            )
                            sendAppNotification(
                                f"Automod (anti spam) | Warned {message.author} for spamming ({spam_data[str(message.author.id)]['count']} messages in {round(elapsed_time.total_seconds(), 2)}s).",
                                discord_url=msg.jump_url,
                                channel=msg.channel,
                            )
                        if antispam_config["timeout"]["state"]:
                            await message.author.timeout(
                                timedelta(
                                    minutes=antispam_config["timeout"][
                                        "duration_minutes"
                                    ]
                                ),
                                reason=antispam_config["timeout"].get("reason"),
                            )
                            sendAppNotification(
                                f"Automod (anti spam) | Timed out {message.author} for {antispam_config['timeout']['duration_minutes']} minutes. ({spam_data[str(message.author.id)]['count']} messages in {round(elapsed_time.total_seconds(), 2)}s).",
                                discord_url=message.jump_url,
                                channel=message.channel,
                            )
                        if antispam_config["nickname"]["state"]:
                            await message.author.edit(
                                nick=antispam_config["nickname"]["name"]
                            )
                            sendAppNotification(
                                f"Automod (anti spam) | Added nickname to {message.author}: {antispam_config['nickname']['name']}. ({spam_data[str(message.author.id)]['count']} messages in {round(elapsed_time.total_seconds(), 2)}s).",
                                discord_url=message.jump_url,
                                channel=message.channel,
                            )
                    if elapsed_time.total_seconds() >= antispam_config["lapse"]:
                        with open(f"{getDataPath()}/automod/userspam.json", "w") as f:
                            json.dump({}, f, indent=2)
                            bot.config["flagged"] = False
                            return
                with open(f"{getDataPath()}/automod/userspam.json", "w") as f:
                    json.dump(spam_data, f, indent=2)
                return
    @bot.listen("on_message_edit")
    async def onMessageEdit(before, after):
        if before.author == bot.user or before.clean_content == after.clean_content:
            return
        if bot.config.get("spy"):
            if bot.config["spy"] == before.author:
                sendAppNotification(
                    f"Spy | {before.author} edited a message | Before: {before.clean_content} | After: {after.clean_content}",
                    discord_url=after.jump_url,
                    channel=after.channel,
                )
        if getConfig()["dmlogger"]:
            if (
                isinstance(before.channel, discord.GroupChannel)
                or isinstance(before.channel, discord.DMChannel)
                and getConfig()["dmlogger"] == "group"
            ):
                sendAppNotification(
                    f"DM logger | {before.author} edited a message | Before: {before.clean_content} | After: {after.clean_content}",
                    before.jump_url,
                    before.channel,
                )
            elif (
                isinstance(before.channel, discord.DMChannel)
                and getConfig()["dmlogger"] == "on"
            ):
                sendAppNotification(
                    f"DM logger | {before.author} edited a message | Before: {before.clean_content} | After: {after.clean_content}",
                    before.jump_url,
                    before.channel,
                )
        if bot.config.get("editsend"):
            if bot.config["editsend"] == before.author:
                new_msg = await before.channel.send(
                    content=f"{before.author.mention} edited a message:\nBefore: {before.content}\nAfter: {after.content}"
                )
                sendAppNotification(
                    f"Edit send | Resent edited message from {before.author} | {before.clean_content}",
                    discord_url=new_msg.jump_url,
                    channel=new_msg.channel,
                )
    @bot.listen("on_message_delete")
    async def onMessageDeleted(message):
        if not bot.config.get("snipe"):
            bot.config["snipe"] = []
        if message.author == bot.user:
            return
        bot.config["snipe"].append(message)
        if getConfig()["dmlogger"]:
            if (
                isinstance(message.channel, discord.GroupChannel)
                and getConfig()["dmlogger"] == "group"
            ):
                sendAppNotification(
                    f"DM logger | {message.author} deleted a message: {message.clean_content}",
                    message.jump_url,
                    message.channel,
                )
            elif (
                isinstance(message.channel, discord.DMChannel)
                and getConfig()["dmlogger"] == "on"
            ):
                sendAppNotification(
                    f"DM logger | {message.author} deleted a message: {message.clean_content}",
                    message.jump_url,
                    message.channel,
                )
        if bot.config.get("spy"):
            if bot.config["spy"] == message.author:
                sendAppNotification(
                    f"Spy | {message.author} deleted a message | {message.clean_content}",
                    discord_url=message.jump_url,
                    channel=message.channel,
                )
        if bot.config.get("deletesend"):
            if bot.config["deletesend"] == message.author:
                new_msg = await message.channel.send(
                    content=f"{message.author.mention} deleted a message: {message.content}"
                )
                sendAppNotification(
                    f"Delete send | Resent deleted message from {message.author} | {message.clean_content}",
                    discord_url=new_msg.jump_url,
                    channel=new_msg.channel,
                )
        notifications = getNotifications()
        if (
            notifications["app"]["ghostpings"]
            and bot.user.mentioned_in(message)
            and message.author is not bot.user
        ):
            sendAppNotification(
                f"You got ghostpinged | {message.guild} | {message.channel} | {message.author} | {message.clean_content}",
                message.jump_url,
                message.channel,
            )
            if notifications["toast"]["ghostpings"]:
                showToast(
                    text=f"You got ghostpinged\n{message.author}\n{message.clean_content}",
                    url=message.jump_url,
                )
            if notifications["webhook"]["ghostpings"]:
                await sendWebhookNotification(
                    notifications["webhook"]["ghostpings"],
                    "You got ghostpinged",
                    f"By {message.author.mention}\n{message.content}\n\n{message.jump_url}",
                )
            if notifications["sound"]["ghostpings"]:
                playSound("pinged.wav")
    @bot.listen("on_message")
    async def onGiveawayDetection(message):
        notifications = getNotifications()
        config = getGiveawayJoinerConfig()
        join_giveaway = False
        if config["giveawayjoiner"] or notifications["app"]["giveaways"]:
            if message.author.id == 294882584201003009:
                print(f"Giveaway detected: {str(message.content)}")
                for embed in message.embeds:
                    print(f"embeds: {str(embed.to_dict())}")
                    if (
                        "Ends:" in embed.to_dict()["description"]
                        or "GIVEAWAY" in message.clean_content
                    ):
                        join_giveaway = True
                        sendAppNotification(
                            f"Giveaway found | Prize: {embed.to_dict()['title']}",
                            discord_url=message.jump_url,
                            channel=message.channel,
                        )
                        if notifications["toast"]["giveaways"]:
                            showToast(
                                text=f"Giveaway found\nPrize: {embed.to_dict()['title']}",
                                url=message.jump_url,
                            )
                        if notifications["webhook"]["giveaways"]:
                            await sendWebhookNotification(
                                notifications["webhook"]["giveaways"],
                                "Giveaway found",
                                f"By {message.author}\nPrize: {embed.to_dict()['title']}\n{message.content}\n\n{message.jump_url}",
                            )
                        if notifications["sound"]["giveaways"]:
                            playSound("giveaways.wav")
                        for x in config["blacklisted_words"]:
                            if (
                                x.lower() in f'{embed.to_dict().get("title")}'.lower()
                                or x.lower() in message.clean_content.lower()
                            ):
                                sendAppNotification(
                                    f"Giveaway blacklisted | Trigger: {x} | Prize: {embed.to_dict()['title']}",
                                    discord_url=message.jump_url,
                                    channel=message.channel,
                                )
                                if notifications["toast"]["giveaways"]:
                                    showToast(
                                        text=f"Giveaway blacklisted\nTrigger: {x}\nPrize: {embed.to_dict()['title']}",
                                        url=message.jump_url,
                                    )
                                if notifications["webhook"]["giveaways"]:
                                    await sendWebhookNotification(
                                        notifications["webhook"]["giveaways"],
                                        "Giveaway blacklisted",
                                        f"By {message.author}\nTrigger: {x}\nPrize: {embed.to_dict()['title']}\n{message.content}\n\n{message.jump_url}",
                                    )
                                join_giveaway = False
                                break
                        if message.guild.id in config["blacklisted_serverids"]:
                            join_giveaway = False
                            sendAppNotification(
                                f"Giveaway blacklisted | Blacklisted server | Prize: {embed.to_dict()['title']}",
                                discord_url=message.jump_url,
                                channel=message.channel,
                            )
                            if notifications["toast"]["giveaways"]:
                                showToast(
                                    text=f"Giveaway blacklisted\nBlacklisted server\nPrize: {embed.to_dict()['title']}",
                                    url=message.jump_url,
                                )
                            if notifications["webhook"]["giveaways"]:
                                await sendWebhookNotification(
                                    notifications["webhook"]["giveaways"],
                                    "Giveaway blacklisted",
                                    f"By {message.author}\nBlacklisted server\nPrize: {embed.to_dict()['title']}\n{message.content}\n\n{message.jump_url}",
                                )
                    if join_giveaway and config["giveawayjoiner"]:
                        for component in message.components:
                            if "action_row" in component.type:
                                for child in component.children:
                                    if "button" in child.type:
                                        if child.custom_id == "enter-giveaway":
                                            seconds = config["delay_in_seconds"]
                                            await asyncio.sleep(seconds)
                                            sendAppNotification(
                                                f"Giveaway joined",
                                                discord_url=message.jump_url,
                                                channel=message.channel,
                                            )
                                            if notifications["toast"]["giveaways"]:
                                                showToast(
                                                    text=f"Giveaway joined",
                                                    url=message.jump_url,
                                                )
                                            if notifications["webhook"]["giveaways"]:
                                                await sendWebhookNotification(
                                                    notifications["webhook"][
                                                        "giveaways"
                                                    ],
                                                    "Giveaway joined",
                                                    f"By {message.author}\n{message.content}\n\n{message.jump_url}",
                                                )
                                            if notifications["sound"]["giveaways"]:
                                                playSound("giveaways.wav")
                                            await child.click()
                                            join_giveaway = False
                                            return
                                return
    @bot.listen("on_relationship_add")
    async def onRelationshipAdd(relation):
        if bot.config.get("restore_friends"):
            friend_ids = [friend["id"] for friend in bot.config["restore_friends"]]
            if relation.user.id in friend_ids:
                sendAppNotification(f"Restore friends | Added {relation.user}")
                current_index = friend_ids.index(relation.user.id)
                for _ in range(len(friend_ids)):
                    next_index = (current_index + 1) % len(
                        bot.config["restore_friends"]
                    )
                    next_friend = await bot.fetch_user(
                        bot.config["restore_friends"][next_index]["id"]
                    )
                    if next_friend:
                        if not next_friend.is_friend():
                            next_friend_p = await next_friend.profile()
                            if (
                                next_friend_p.mutual_guilds
                                or next_friend_p.mutual_friends
                            ):
                                os.startfile(
                                    f"discord://discord.com/users/{next_friend.id}"
                                )
                                break
                            else:
                                sendAppNotification(
                                    f"Restore friends | failed to restore {bot.config['restore_friends'][next_index]['name']}, user does not share a mutual server.",
                                    type_="ERROR",
                                )
                                current_index = next_index
                        else:
                            sendAppNotification(
                                f"Restore friends | {next_friend} is already a friend, skipping"
                            )
                            current_index = next_index
                    else:
                        sendAppNotification(
                            f"Restore friends | {bot.config['restore_friends'][next_index]['name']} not found.",
                            type_="ERROR",
                        )
                        current_index = next_index
        notifications = getNotifications()
        if notifications["app"]["friends"]:
            sendAppNotification(
                f"New relationship | {relation.user} | {relation.type}",
                discord_url=f"https://discord.com/users/{relation.user.id}",
            )
            if notifications["toast"]["friends"]:
                showToast(
                    text=f"New relationship\n{relation.user}\n{relation.type}",
                    url=f"https://discord.com/users/{relation.user.id}",
                )
            if notifications["webhook"]["friends"]:
                await sendWebhookNotification(
                    notifications["webhook"]["friends"],
                    "New Relationship",
                    f"User: {relation.user.mention}\nType: {relation.type}\n\n[User Profile](https://discord.com/users/{relation.user.id})",
                )
            if notifications["sound"]["friends"]:
                playSound("friends.mp3")
    @bot.listen("on_relationship_remove")
    async def onRelationshipRemoved(relation):
        notifications = getNotifications()
        if notifications["app"]["friends"]:
            sendAppNotification(
                f"Removed relationship | {relation.user} | {relation.type}",
                discord_url=f"https://discord.com/users/{relation.user.id}",
            )
            if notifications["toast"]["friends"]:
                showToast(
                    text=f"Removed relationship\n{relation.user}\n{relation.type}",
                    url=f"https://discord.com/users/{relation.user.id}",
                )
            if notifications["webhook"]["friends"]:
                await sendWebhookNotification(
                    notifications["webhook"]["friends"],
                    "Removed Relationship",
                    f"User: {relation.user.mention}\nType: {relation.type}\n\n[User Profile](https://discord.com/users/{relation.user.id})",
                )
            if notifications["sound"]["friends"]:
                playSound("friends.mp3")
    @bot.listen("on_relationship_update")
    async def onRelationshipUpdated(before, after):
        notifications = getNotifications()
        if notifications["app"]["friends"]:
            sendAppNotification(
                f"Updated relationship | {before.user} | {after.type}",
                discord_url=f"https://discord.com/users/{before.user.id}",
            )
            if notifications["toast"]["friends"]:
                showToast(
                    text=f"Updated relationship\n{before.user}\n{after.type}",
                    url=f"https://discord.com/users/{before.user.id}",
                )
            if notifications["webhook"]["friends"]:
                await sendWebhookNotification(
                    notifications["webhook"]["friends"],
                    "Updated Relationship",
                    f"User: {before.user.mention}\nType: {after.type}\n\n[User Profile](https://discord.com/users/{before.user.id})",
                )
            if notifications["sound"]["friends"]:
                playSound("friends.mp3")
    @bot.listen("on_guild_join")
    async def onGuildJoin(guild):
        if bot.config.get("restore_servers"):
            server_ids = [server["id"] for server in bot.config["restore_servers"]]
            if guild.id in server_ids:
                sendAppNotification(f"Restore servers | Joined {guild.name}")
                current_index = server_ids.index(guild.id)
                for _ in range(len(server_ids)):
                    new_index = (current_index + 1) % len(bot.config["restore_servers"])
                    next_server = bot.config["restore_servers"][new_index]
                    if next_server["invite"]:
                        os.startfile(
                            f'discord://discord.com/invite/{next_server["invite"]}'
                        )
                        break
                    else:
                        current_index = new_index
        notifications = getNotifications()
        if notifications["app"]["servers"]:
            sendAppNotification(f"Joined new server: {guild}")
            if notifications["toast"]["servers"]:
                showToast(text=f"Joined new server: {guild}")
            if notifications["webhook"]["servers"]:
                await sendWebhookNotification(
                    notifications["webhook"]["servers"],
                    f"Joined server",
                    text=f"Server: {guild}",
                )
    @bot.listen("on_guild_remove")
    async def onGuildRemoved(guild):
        notifications = getNotifications()
        if notifications["app"]["servers"] and guild not in bot.guilds:
            sendAppNotification(f"Left/kicked from server: {guild}")
            if notifications["toast"]["servers"]:
                showToast(text=f"Left/kicked from server: {guild}")
            if notifications["webhook"]["servers"]:
                await sendWebhookNotification(
                    notifications["webhook"]["servers"],
                    f"Left/kicked from server",
                    text=f"Server: {guild}",
                )
    @bot.listen("on_guild_update")
    async def onGuildUpdate(before, after):
        notifications = getNotifications()
        if before.name != after.name:
            if notifications["app"]["servers"] and before not in bot.guilds:
                sendAppNotification(f"Server renamed from {before} to {after}")
                if notifications["toast"]["servers"]:
                    showToast(text=f"Server renamed\nFrom {before}\nTo {after}")
                if notifications["webhook"]["servers"]:
                    await sendWebhookNotification(
                        notifications["webhook"]["servers"],
                        f"Server renamed",
                        text=f"Server: {before}\nFrom: {before.name}\nTo: {after.name}",
                    )
    @bot.listen("on_user_update")
    async def onUserUpdate(before, after):
        if before.name != after.name:
            with open(
                f"{getDataPath()}/misc/user_history.json", "r+", encoding="utf-8"
            ) as f:
                logs = json.load(f)
                user_history = logs.setdefault("user_history", {})
                user_data = user_history.setdefault(str(before.id), {"usernames": []})
                user_data["usernames"].append(
                    f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | {before}'
                )
                f.seek(0)
                json.dump(logs, f, indent=2)
                f.truncate()
    @bot.listen("on_member_update")
    async def onMemberUpdate(before, after):
        if bot.config.get("forcenick"):
            if before.nick != after.nick:
                if bot.config["forcenick"].get("user"):
                    if (
                        before.id == bot.config["forcenick"]["user"]
                        and before.guild.id == bot.config["forcenick"]["server"]
                    ):
                        print(
                            f"Force nick | {before.name} changed their nickname to {after.nick}",
                            discordChannel=before.guild.name,
                        )
                        await after.edit(nick=bot.config["forcenick"]["name"])
                        print(
                            f"Force nick | Changed {before.name}'s nickname to {bot.config['forcenick']['name']}",
                            discordChannel=before.guild.name,
                        )
        if bot.config.get("spy"):
            if bot.config["spy"] == before:
                if before.nick != after.nick:
                    print(
                        f"Spy | {before.name} changed nickname to: {after.nick} in {before.guild.name}",
                        discordChannel=before.guild.name,
                    )
                    if before.roles != after.roles:
                        rlss = ""
                    for role in before.roles[1:]:
                        rlss += f"| {role} "
                    rlsaa = ""
                    for role in after.roles[1:]:
                        rlsaa += f"| {role} "
                    rlsss = ""
                    for role in before.roles[1:]:
                        rlsss += f"| {role} "
                    rlsaaa = ""
                    for role in after.roles[1:]:
                        rlsaaa += f"| {role} "
                    print(
                        f"Spy | {before.name}'s roles updated in {before.guild.name} | {rlsaa}",
                        discordChannel=before.guild.name,
                    )
        notifications = getNotifications()
        if before.id == bot.user.id:
            if notifications["app"]["nicknames"] and before.nick != after.nick:
                print(
                    f"Nickname changed from {before.nick} to {after.nick} in {before.guild}",
                    discordChannel=before.guild.name,
                )
                if notifications["toast"]["nicknames"]:
                    showToast(
                        title="Nickname changed",
                        text=f"From: {before.nick}\nTo: {after.nick}\nServer: {before.guild}",
                    )
                if notifications["webhook"]["nicknames"]:
                    await sendWebhookNotification(
                        notifications["webhook"]["nicknames"],
                        f"Nickname changed",
                        text=f"From: {before.nick}\nTo: {after.nick}\nServer: {before.guild}",
                    )
                if notifications["sound"]["nicknames"]:
                    playSound("nicknames.mp3")
            if notifications["app"]["roles"] and before.roles != after.roles:
                added_roles = [
                    role.name for role in set(after.roles) - set(before.roles)
                ]
                removed_roles = [
                    role.name for role in set(before.roles) - set(after.roles)
                ]
                roleUpdated = False
                temp_data = {}
                if added_roles:
                    roleUpdated = True
                    temp_data["title"] = f"Added roles | {before.guild}"
                    temp_data["content"] = ", ".join(added_roles)
                if removed_roles:
                    roleUpdated = True
                    temp_data["title"] = f"Removed roles | {before.guild}"
                    temp_data["content"] = ", ".join(removed_roles)
                if roleUpdated:
                    sendAppNotification(f"{temp_data['title']}: {temp_data['content']}")
                    if notifications["toast"]["roles"]:
                        showToast(title=temp_data["title"], text=temp_data["content"])
                    if notifications["webhook"]["roles"]:
                        await sendWebhookNotification(
                            notifications["webhook"]["roles"],
                            temp_data["title"],
                            text=temp_data["content"],
                        )
                    if notifications["sound"]["nicknames"]:
                        playSound("roles.mp3")
    @bot.listen("on_group_remove")
    async def onGroupRemoved(channel, user):
        if bot.config.get("noleave"):
            if user == bot.config["noleave"] and bot.user is not user:
                await channel.add_recipients(user)
                sendAppNotification(
                    f"No leave | Added {user} back to group: {channel.name}",
                    discord_url=channel.jump_url,
                    channel=channel,
                )
    @bot.listen("on_voice_state_update")
    async def onVoiceUpdate(member, before, after):
        if bot.config.get("forcedisconnect"):
            if bot.config["forcedisconnect"] == member:
                await member.edit(voice_channel=None)
                sendAppNotification(
                    f"Force disconnect | Removed {member} from voice channel: {after.channel} ",
                    channel=after.channel,
                )
        if bot.config.get("spy"):
            if bot.config["spy"] == member:
                if before.channel and after.channel:
                    if before.channel != after.channel:
                        sendAppNotification(
                            f"Spy | {member} moved from {before.channel} to {after.channel}",
                            channel=before.channel,
                        )
                elif not before.channel and after.channel:
                    sendAppNotification(
                        f"Spy | {member} connected to voice channel: {after.channel} to {after.channel}",
                        channel=after.channel,
                    )
                elif before.channel and not after.channel:
                    sendAppNotification(
                        f"Spy | {member} disconnected from voice channel: {before.channel}",
                        channel=before.channel,
                    )
    @bot.listen("on_reaction_add")
    async def onReactionAdd(reaction, user):
        if user == bot.user:
            return
        if bot.config.get("unreact"):
            if bot.config["unreact"] == user:
                try:
                    await reaction.remove(user)
                    sendAppNotification(
                        f"Unreact | Removed reaction from {reaction.author}: {reaction.emoji}",
                        discord_url=reaction.message.jump_url,
                        channel=reaction.message.channel,
                    )
                except:
                    pass
        if bot.config.get("spy"):
            if bot.config["spy"] == user:
                sendAppNotification(
                    f"Spy | {user.name} added a reaction to a message from {reaction.message.author} with {reaction.emoji}",
                    discord_url=reaction.message.jump_url,
                    channel=reaction.message.channel,
                )
    @bot.listen("on_member_join")
    async def onMemberJoin(member):
        if bot.config.get("forcekick"):
            if bot.config["forcekick"] == member:
                await member.kick(reason="Force kicked")
                return sendAppNotification(
                    f"Force kick | Kicked {member} from {member.guild}"
                )
    @bot.listen("on_typing")
    async def onTyping(channel, user, when):
        if user.id == bot.user.id:
            return
        notifications = getNotifications()
        if isinstance(channel, discord.DMChannel):
            if notifications["toast"]["typing"]:
                showToast(
                    title=f"Direct Messages",
                    text=f"{user} is typing ...",
                    url=channel.jump_url,
                )
            if notifications["sound"]["typing"]:
                playSound("typing.wav")
    @bot.command(
        name="help",
        usage="[command]",
        description="Get help with a command",
        extras={"built-in": True, "category": "Help"},
    )
    async def help(ctx, command=None):
        if not command:
            await ctx.nighty_help(commands=getCategoryCommands("Help"))
        else:
            cmd = bot.get_command(command)
            if cmd:
                await ctx.nighty_command_help(command=cmd)
            else:
                await ctx.nighty_send(
                    title="Help", content=f"Command `{command}` not found"
                )
    @bot.command(
        name="admin",
        description="Administration commands",
        extras={"built-in": True, "category": "Help"},
    )
    async def admin(ctx):
        await ctx.nighty_help(title="Admin", commands=getCategoryCommands("Admin"))
    @bot.command(
        name="animated",
        description="Animated messages",
        extras={"built-in": True, "category": "Help"},
    )
    async def animated(ctx):
        await ctx.nighty_help(
            title="Animated", commands=getCategoryCommands("Animated")
        )
    @bot.command(
        name="text",
        description="Text messages",
        extras={"built-in": True, "category": "Help"},
    )
    async def text(ctx):
        await ctx.nighty_help(title="Text", commands=getCategoryCommands("Text"))
    @bot.command(
        name="image",
        description="Image commands",
        extras={"built-in": True, "category": "Help"},
    )
    async def image(ctx):
        await ctx.nighty_help(title="Image", commands=getCategoryCommands("Image"))
    @bot.command(
        name="troll",
        description="Trolling commands",
        extras={"built-in": True, "category": "Help"},
    )
    async def troll(ctx):
        await ctx.nighty_help(title="Trolling", commands=getCategoryCommands("Troll"))
    @bot.command(
        name="fun",
        description="Funny commands",
        extras={"built-in": True, "category": "Help"},
    )
    async def fun(ctx):
        await ctx.nighty_help(title="Fun", commands=getCategoryCommands("Fun"))
    @bot.command(
        name="tools",
        description="General tools",
        extras={"built-in": True, "category": "Help"},
    )
    async def tools(ctx):
        await ctx.nighty_help(title="Tools", commands=getCategoryCommands("Tools"))
    @bot.command(
        name="utils",
        description="Utilities",
        extras={"built-in": True, "category": "Help"},
    )
    async def utils(ctx):
        await ctx.nighty_help(title="Utilities", commands=getCategoryCommands("Utils"))
    @bot.command(
        name="recovery",
        description="Backup & restores",
        extras={"built-in": True, "category": "Help"},
    )
    async def recovery(ctx):
        await ctx.nighty_help(
            title="Recovery", commands=getCategoryCommands("Recovery")
        )
    @bot.command(
        name="protection",
        description="Protection",
        extras={"built-in": True, "category": "Help"},
    )
    async def protection(ctx):
        await ctx.nighty_help(
            title="Protection", commands=getCategoryCommands("Protection")
        )
    @bot.command(
        name="rpc",
        aliases=["richpresence"],
        usage="[on/off]",
        description="Rich Presence",
        extras={"built-in": True, "category": "Help"},
    )
    async def rpc(ctx, toggle=None):
        if not toggle:
            await ctx.nighty_help(
                title="Rich Presence", commands=getCategoryCommands("RPC")
            )
        else:
            toggle = toggle.lower()
            if toggle == "on":
                setRPCState(True)
                await updateRPC(getRPCProfileData(getActiveRPCProfile()))
                await ctx.nighty_send(title="Rich Presence", content=f"RPC: {toggle}")
            elif toggle == "off":
                setRPCState(False)
                await bot.change_presence(
                    activity=None,
                    afk=True,
                    status=bot.client_status,
                    edit_settings=False,
                )
                await ctx.nighty_send(title="Rich Presence", content=f"RPC: {toggle}")
    @bot.command(
        name="misc",
        description="Miscellaneous",
        extras={"built-in": True, "category": "Help"},
    )
    async def misc(ctx):
        await ctx.nighty_help(
            title="Miscellaneous", commands=getCategoryCommands("Misc")
        )
    @bot.command(
        name="settings",
        description="Settings",
        extras={"built-in": True, "category": "Help"},
    )
    async def settings(ctx):
        await ctx.nighty_help(
            title="Settings", commands=getCategoryCommands("Settings")
        )
    @bot.command(
        name="spotify",
        description="Spotify controls",
        extras={"built-in": True, "category": "Help"},
    )
    async def spotify(ctx):
        await ctx.nighty_help(title="Spotify", commands=getCategoryCommands("Spotify"))
    @bot.command(
        name="customhelp",
        aliases=["customcommands"],
        description="Custom commands",
        extras={"built-in": True, "category": "Help"},
    )
    async def customhelp(ctx):
        custom_commands = []
        for command in bot.commands:
            if not command.extras.get("built-in"):
                custom_commands.append(command)
        if custom_commands:
            await ctx.nighty_help(title="Custom commands", commands=custom_commands)
        else:
            await ctx.nighty_send(
                title="Custom commands", content="No custom commands installed."
            )
    @bot.command(
        name="search",
        usage="<command>",
        description="Search for a command",
        extras={"built-in": True, "category": "Help"},
    )
    async def search(ctx, command_name):
        commandslist = sorted(
            str(command) for command in bot.commands if not command.hidden
        )
        matched_command_names = get_close_matches(command_name, commandslist, 7, 0.15)
        matched_commands = [bot.get_command(name) for name in matched_command_names]
        matched_commands = [cmd for cmd in matched_commands if cmd is not None]
        await ctx.nighty_help(title="Search results", commands=matched_commands)
    @bot.command(
        name="repeat",
        usage="[channel]",
        description="Repeat last used command",
        extras={"built-in": True, "category": "Help"},
    )
    async def repeat(
        ctx, channel: Union[discord.abc.GuildChannel, discord.abc.PrivateChannel] = None
    ):
        if bot.last_command:
            if channel is None:
                await ctx.invoke(
                    bot.last_command.command,
                    *bot.last_command.args[1:],
                    **bot.last_command.kwargs,
                )
            else:
                message = [message async for message in channel.history(limit=1)][0]
                temp_ctx = await bot.get_context(message)
                await temp_ctx.invoke(
                    bot.last_command.command,
                    *bot.last_command.args[1:],
                    **bot.last_command.kwargs,
                )
    @bot.command(
        name="remote",
        usage="<channel> <cmd>",
        description="Remote command execution",
        extras={"built-in": True, "category": "Help"},
    )
    async def remote(
        ctx,
        channel: Union[discord.abc.GuildChannel, discord.abc.PrivateChannel],
        *,
        cmd: str,
    ):
        ctx = await execRemoteCommand(channel, cmd)
    @bot.command(
        name="textchannel",
        usage='<"name">',
        description="Create text channel",
        extras={"built-in": True, "category": "Admin"},
    )
    async def textchannel(ctx, name):
        channel = await ctx.guild.create_text_channel(name)
        await ctx.nighty_send(
            title="Text channel", content=f"Created channel: {channel}"
        )
    @bot.command(
        name="voicechannel",
        usage='<"name">',
        description="Create voice channel",
        extras={"built-in": True, "category": "Admin"},
    )
    async def voicechannel(ctx, name):
        channel = await ctx.guild.create_voice_channel(name)
        await ctx.nighty_send(
            title="Voice channel", content=f"Created channel: {channel}"
        )
    @bot.command(
        name="stagechannel",
        usage='<"name">',
        description="Create stage channel",
        extras={"built-in": True, "category": "Admin"},
    )
    async def stagechannel(ctx, name):
        channel = await ctx.guild.create_stage_channel(name)
        await ctx.nighty_send(
            title="Stage channel", content=f"Created channel: {channel}"
        )
    @bot.command(
        name="timeout",
        usage='<member> <minutes> ["reason"]',
        description="Timeout member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def timeout(ctx, member: discord.Member, minutes: float, reason: str = None):
        await member.timeout(
            datetime.now().astimezone() + timedelta(minutes=minutes), reason=reason
        )
        await ctx.nighty_send(
            title="Timeout", content=f"Timed out {member} for {minutes} minute(s)"
        )
    @bot.command(
        name="removetimeout",
        usage='<member> ["reason"]',
        description="Remove timeout",
        extras={"built-in": True, "category": "Admin"},
    )
    async def removetimeout(ctx, member: discord.Member, reason: str = None):
        await member.timeout(None, reason=reason)
        await ctx.nighty_send(title="Timeout", content=f"Removed timeout from {member}")
    @bot.command(
        name="kick",
        usage='<member> ["reason"]',
        description="Kick member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def kick(ctx, member: discord.Member, reason: str = None):
        await member.kick(reason=reason)
        await ctx.nighty_send(title="Kick", content=f"Kicked: {member}")
    @bot.command(
        name="ban",
        usage='<member> ["reason"]',
        description="Ban member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def ban(ctx, member: discord.Member, reason: str = None):
        await member.ban(reason=reason)
        await ctx.nighty_send(title="Ban", content=f"Banned: {member}")
    @bot.command(
        name="unban",
        usage='<member> ["reason"]',
        description="Unban member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def unban(ctx, member: discord.Member, reason: str = None):
        await member.unban(reason=reason)
        await ctx.nighty_send(title="Ban", content=f"Unbanned: {member}")
    @bot.command(
        name="softban",
        usage='<member> ["reason"]',
        description="Softban member",
        help="Bans & unbans the member in order to kick and delete their messages.",
        extras={"built-in": True, "category": "Admin"},
    )
    async def softban(ctx, member: discord.Member, reason: str = None):
        await member.ban(reason=reason, delete_message_days=7)
        await member.unban(reason=reason)
        await ctx.nighty_send(title="Softban", content=f"Softbanned: {member}")
    @bot.command(
        name="hackban",
        usage='<user_id> ["reason"]',
        description="Ban member outside of the server",
        help="Can be used when you want to ban someone who is not in your server.",
        extras={"built-in": True, "category": "Admin"},
    )
    async def hackban(ctx, user_id: int, reason: str = None):
        await ctx.guild.ban(
            discord.Object(user_id), reason=reason, delete_message_days=7
        )
        await ctx.nighty_send(title="Hackban", content=f"Banned: {user_id}")
    @bot.command(
        name="banned",
        description="Banned users in the server",
        extras={"built-in": True, "category": "Admin"},
    )
    async def banned(ctx):
        bans = [entry async for entry in ctx.guild.bans(limit=None)]
        if bans:
            await ctx.nighty_send(
                title=f"Server bans ({len(bans)})",
                content=f"{', '.join([str(b.user.name) for b in bans])}",
            )
        else:
            await ctx.nighty_send(title="Server bans", content="0 banned members")
    @bot.command(
        name="savebans",
        description="Save bans in a file",
        extras={"built-in": True, "category": "Admin"},
    )
    async def savebans(ctx):
        banned_text = ""
        for ban in [entry async for entry in ctx.guild.bans(limit=None)]:
            banned_text += (
                f"User: {ban.user}\nUser ID: {ban.user.id}\nReason: {ban.reason}\n\n"
            )
        if banned_text == "" or banned_text == None:
            banned_text = "No one has been banned in that server or you do not have the right permissions."
        await ctx.nighty_send(
            title=f"Save bans",
            content="Bans saved in attachment",
            file=discord.File(
                io.StringIO(banned_text), filename=f"{ctx.guild.name}-bans.txt"
            ),
        )
    @bot.command(
        name="exportbans",
        usage="<server>",
        description="Export bans from server into current.",
        extras={"built-in": True, "category": "Admin"},
    )
    async def exportbans(ctx, server: discord.Guild):
        await ctx.nighty_send(
            title=f"Export bans", content=f"Exporting bans from {server}"
        )
        for ban in [entry async for entry in server.bans(limit=None)]:
            await ctx.guild.ban(discord.Object(int(ban.user.id)), reason=ban.reason)
            await asyncio.sleep(1.5)
        await ctx.nighty_send(
            title=f"Export bans", content=f"Successfully exported bans from {server}"
        )
    @bot.command(
        name="addrole",
        usage="<member> <role>",
        description="Add role to member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def addrole(ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await ctx.nighty_send(
            title="Add role", content=f"Added role {role} to {member}"
        )
    @bot.command(
        name="removerole",
        usage="<member> <role>",
        description="Remove role from member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def removerole(ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await ctx.nighty_send(
            title="Remove role", content=f"Removed role {role} from {member}"
        )
    @bot.command(
        name="removeallroles",
        usage="<member>",
        description="Remove all roles from member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def removeallroles(ctx, member: discord.Member):
        for role in member.roles:
            try:
                await member.remove_roles(role)
            except:
                pass
        await ctx.nighty_send(
            title="Remove all roles", content=f"Removed all roles from {member}"
        )
    @bot.command(
        name="addallrole",
        usage="<member>",
        description="Add all roles to member",
        extras={"built-in": True, "category": "Admin"},
    )
    async def addallrole(ctx, member: discord.Member):
        for role in ctx.guild.roles:
            try:
                await member.add_roles(role)
            except:
                pass
        await ctx.nighty_send(
            title="Add all role", content=f"Added all roles to {member}"
        )
    @bot.command(
        name="makerole",
        usage="<name>",
        description="Create new role",
        extras={"built-in": True, "category": "Admin"},
    )
    async def makerole(ctx, name: str):
        role = await ctx.guild.create_role(name=name, colour=discord.Colour(0xFFFFFF))
        await ctx.nighty_send(title="Create role", content=f"Created: {role}")
    @bot.command(
        name="rainbow",
        usage="<role>",
        description="Rainbow role color",
        extras={"built-in": True, "category": "Admin"},
    )
    async def rainbow(ctx, role: discord.Role):
        global cycling
        cycling = True
        await ctx.nighty_send(
            title="Rainbow role",
            content=f"Rainbow color started on role: {role}, use {bot.command_prefix}stop to abort the looping.",
        )
        while cycling:
            await role.edit(color=discord.Colour(random.randint(0, 0xFFFFFF)))
            await asyncio.sleep(2.5)
    @bot.command(
        name="nick",
        usage='<member> ["name"]',
        description="Edit nickname",
        extras={"built-in": True, "category": "Admin"},
    )
    async def nick(ctx, member: discord.Member, name: str = None):
        await member.edit(nick=name)
        await ctx.nighty_send(
            title="Nickname", content=f"Changed {member}'s nickname to: {name}"
        )
    @bot.command(
        name="purge",
        usage="<amount> [member]",
        description="Purge chat messages",
        help="manage_messages permission is required for this command.",
        extras={"built-in": True, "category": "Admin"},
    )
    async def purge(ctx, amount: int, member: discord.Member = None):
        amount = amount + 1
        def is_member(m):
            if member:
                return m.author == member
            return True
        await ctx.channel.purge(limit=amount, check=is_member)
    @bot.command(
        name="nuke",
        description="Nuke the chat",
        help="Clones the channel & deletes old for an empty chat.",
        extras={"built-in": True, "category": "Admin"},
    )
    async def nuke(ctx):
        messages = [
            "Nuke incoming..",
            "Nuke incoming...",
            "Nuke incoming...3",
            "Nuke incoming...2",
            "Nuke incoming...1",
            "https://media1.tenor.com/images/a6afb6d7aed6c2fa1d0834ae2265dc49/tenor.gif",
        ]
        delays = [2, 1, 1, 1, 1, 5]
        for message, delay in zip(messages, delays):
            await ctx.send(message)
            await asyncio.sleep(delay)
        await ctx.channel.clone()
        await ctx.channel.delete()
    @bot.command(
        name="instanuke",
        description="Nuke the chat (instant)",
        help="Clones the channel & deletes old for an empty chat.",
        extras={"built-in": True, "category": "Admin"},
    )
    async def instanuke(ctx):
        await ctx.channel.clone()
        await ctx.channel.delete()
    @bot.command(
        name="slowmode",
        usage="[seconds]",
        description="Set slowmode",
        extras={"built-in": True, "category": "Admin"},
    )
    async def slowmode(ctx, seconds: int = None):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.nighty_send(
            title="Slowmode", content=f"Slowmode set to: {seconds} second(s)"
        )
    @bot.command(
        name="addemoji",
        usage='<"name"> <url/emoji>',
        description="Add emoji to server",
        extras={"built-in": True, "category": "Admin"},
    )
    async def addemoji(ctx, name, emoji: Union[str, discord.Emoji]):
        if isinstance(emoji, discord.Emoji):
            image = requests.get(emoji.url).content
        else:
            image = requests.get(emoji).content
        new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image)
        await ctx.nighty_send(
            title="Add emoji", content=f"Emoji added: {new_emoji.name}"
        )
    @bot.command(
        name="editemoji",
        usage='<emoji> <"newname">',
        description="Edit emoji name",
        extras={"built-in": True, "category": "Admin"},
    )
    async def editemoji(ctx, emoji: discord.Emoji, newname):
        oldname = emoji.name
        await emoji.edit(name=newname)
        await ctx.nighty_send(
            title="Edit emoji name", content=f"Old: {oldname}\n> New: {newname}"
        )
    @bot.command(
        name="emojidelete",
        usage="<emoji>",
        description="Delete emoji",
        extras={"built-in": True, "category": "Admin"},
    )
    async def emojidelete(ctx, emoji: discord.Emoji):
        name = emoji.name
        await emoji.delete()
        await ctx.nighty_send(title="Delete emoji", content=f"Deleted: {name}")
    @bot.command(
        name="customanimation",
        description="Custom animations",
        extras={"built-in": True, "category": "Animated"},
    )
    async def customanimation(ctx):
        message = ""
        for file in os.listdir(f"{getDataPath()}/animated"):
            if file.endswith(".txt"):
                with open(os.path.join(f"{getDataPath()}/animated", file)) as f:
                    file = os.path.splitext(file)[0]
                    message += f"\n{bot.command_prefix}anim {file} [delay]"
        await ctx.nighty_send(title="Custom animations", content=message)
    @bot.command(
        name="anim",
        usage='<"file.txt"> [seconds]',
        description="Custom animation from file",
        extras={"built-in": True, "category": "Animated"},
    )
    async def anim(ctx, txtfile, delay: int = 1):
        global cycling
        cycling = True
        for file in os.listdir(f"{getDataPath()}/animated"):
            if file.endswith(".txt"):
                with open(os.path.join(f"{getDataPath()}/animated", file)) as f:
                    file = os.path.splitext(file)[0]
                    if fnmatch(file, f"{txtfile}"):
                        try:
                            anims = f.readlines()
                        except:
                            print(f"Wrong syntax on .txt file.", type_="ERROR")
                        message = await ctx.send(anims[0])
                        for x in anims[1:]:
                            if cycling:
                                try:
                                    await message.edit(content=x.rstrip())
                                    await asyncio.sleep(delay)
                                except:
                                    print(
                                        f"Unknown error, check if your syntax is correct.",
                                        type_="ERROR",
                                    )
    @bot.command(
        name="textanim",
        usage='<"text">',
        description="Animated message",
        extras={"built-in": True, "category": "Animated"},
    )
    async def textanim(ctx, text):
        name = ""
        first_passed = False
        for letter in text:
            name = name + letter
            if not first_passed:
                ms = await ctx.send(name)
                first_passed = True
            else:
                await ms.edit(content=name)
            await asyncio.sleep(1)
    @bot.command(
        name="virus",
        usage='["type"]',
        description="Injecting virus",
        extras={"built-in": True, "category": "Animated"},
    )
    async def virus(ctx, virus_type: str = "trojan"):
        global cycling
        cycling = True
        steps = (
            f"``[▓▓▓                    ] / {virus_type}.exe Packing files.``",
            f"``[▓▓▓▓▓▓▓                ] - {virus_type}.exe Packing files..``",
            f"``[▓▓▓▓▓▓▓▓▓▓▓▓           ] \ {virus_type}.exe Packing files..``",
            f"``[▓▓▓▓▓▓▓▓▓▓▓▓▓▓         ] | {virus_type}.exe Packing files..``",
            f"``[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      ] / {virus_type}.exe Packing files..``",
            f"``[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ] - {virus_type}.exe Packing files..``",
            f"``[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ] \ {virus_type}.exe Packing files..``",
            f"``Successfully downloaded {virus_type}.exe``",
            f"``Injecting {virus_type}.exe.   |``",
            f"``Injecting {virus_type}.exe..  /``",
            f"``Injecting {virus_type}.exe... -``",
            f"``Successfully Injected {virus_type}.exe``",
        )
        message = await ctx.send(
            f"``[                       ] / {virus_type}.exe Packing files.``"
        )
        for step in steps:
            if cycling:
                await asyncio.sleep(0.8)
                await message.edit(content=step)
    @bot.command(
        name="warning",
        description="Warning. System overload",
        extras={"built-in": True, "category": "Animated"},
    )
    async def warning(ctx):
        global cycling
        cycling = True
        steps = (
            "`OAD !! WARNING !! SYSTEM OVERL`",
            "`AD !! WARNING !! SYSTEM OVERLO`",
            "`D !! WARNING !! SYSTEM OVERLOA`",
            "`! WARNING !! SYSTEM OVERLOAD !`",
            "`WARNING !! SYSTEM OVERLOAD !!`",
            "`ARNING !! SYSTEM OVERLOAD !! W`",
            "`RNING !! SYSTEM OVERLOAD !! WA`",
            "`NING !! SYSTEM OVERLOAD !! WAR`",
            "`ING !! SYSTEM OVERLOAD !! WARN`",
            "`NG !! SYSTEM OVERLOAD !! WARNI`",
            "`G !! SYSTEM OVERLOAD !! WARNIN`",
            "`!! SYSTEM OVERLOAD !! WARNING`",
            "`! SYSTEM OVERLOAD !! WARNING !`",
            "`SYSTEM OVERLOAD !! WARNING !!`",
            "`IMMINENT SHUT-DOWN IN 0.5 SEC!`",
            "`WARNING !! SYSTEM OVERLOAD !!`",
            "`IMMINENT SHUT-DOWN IN 0.3 SEC!`",
            "`SYSTEM OVERLOAD !! WARNING !!`",
            "`IMMINENT SHUT-DOWN IN 0.01 SEC!`",
            "`SHUT-DOWN EXIT ERROR ¯\\(｡･益･)/¯`",
            "`CTRL + R FOR MANUAL OVERRIDE..`",
        )
        message = await ctx.send("`LOAD !! WARNING !! SYSTEM OVER`")
        for step in steps:
            if cycling:
                await asyncio.sleep(0.8)
                await message.edit(content=step)
    @bot.command(
        name="abc",
        description="The alphabet",
        extras={"built-in": True, "category": "Animated"},
    )
    async def abc(ctx):
        global cycling
        cycling = True
        steps = list("abcdefghijklmnopqrstuvwxyz")
        message = await ctx.send(steps[0])
        for step in steps[1:]:
            if cycling:
                await asyncio.sleep(0.8)
                await message.edit(content=step)
    @bot.command(
        name="100",
        description="Count from 0 to 100",
        extras={"built-in": True, "category": "Animated"},
    )
    async def _100(ctx):
        global cycling
        cycling = True
        message = await ctx.send("\u200b")
        for number in range(100):
            if cycling:
                await message.edit(content=str(number))
                await asyncio.sleep(2)
    @bot.command(
        name="bomb",
        description="Animated bomb message",
        extras={"built-in": True, "category": "Animated"},
    )
    async def bomb(ctx):
        global cycling
        cycling = True
        steps = [
            ":bomb: --------------- :fire:",
            ":bomb: -------------- :fire:",
            ":bomb: ------------- :fire:",
            ":bomb: ------------ :fire:",
            ":bomb: ----------- :fire:",
            ":bomb: ---------- :fire:",
            ":bomb: --------- :fire:",
            ":bomb: -------- :fire:",
            ":bomb: ------- :fire:",
            ":bomb: ------ :fire:",
            ":bomb: ----- :fire:",
            ":bomb: ---- :fire:",
            ":bomb: --- :fire:",
            ":bomb: -- :fire:",
            ":bomb: - :fire:",
            ":bomb:  :fire:",
            ":boom:",
        ]
        message = await ctx.send(":bomb: ---------------- :fire:")
        for step in steps:
            if cycling:
                await message.edit(content=step)
                await asyncio.sleep(1)
    @bot.command(
        name="readrules",
        usage="[user]",
        description="Read the f\*cking rules!",
        extras={"built-in": True, "category": "Animated"},
    )
    async def readrules(ctx, user: discord.User = None):
        global cycling
        cycling = True
        steps = [
            "READ",
            "THE",
            "FUCKING",
            "RULES",
            "READ",
            "READ THE",
            "READ THE FUCKING",
            "READ THE FUCKING RULES",
            "READ THE FUCKING RULES",
            "READ THE FUCKING RULES",
            "READ THE FUCKING RULES :man_facepalming:",
        ]
        if user:
            steps = [f"{user}, {step}" for step in steps]
        message = await ctx.send(f"``{steps[0]}``")
        for step in steps[1:]:
            if cycling:
                await asyncio.sleep(1)
                await message.edit(
                    content=f"``{step}``"
                    if "READ THE FUCKING RULES" not in step
                    else step
                )
    @bot.command(
        name="fuckyou",
        description='Animated "fuck you"',
        extras={"built-in": True, "category": "Animated"},
    )
    async def fuckyou(ctx):
        global cycling
        cycling = True
        steps = ["F", "FU", "FUC", "FUCK", "FUCK ", "FUCK Y", "FUCK YO", "FUCK YOU"]
        message = await ctx.send(steps[0])
        for step in steps:
            if cycling:
                await message.edit(content=step)
                await asyncio.sleep(0.1)
    @bot.command(
        name="regional",
        usage='<"text">',
        description="Text in emojis",
        extras={"built-in": True, "category": "Text"},
    )
    async def regional(ctx, text):
        await ctx.send(
            "\u200b".join(
                [
                    regionals[x.lower()] if x.isalnum() or x in ["!", "?"] else x
                    for x in list(text)
                ]
            )
        )
    @bot.command(
        name="space",
        usage='<"text">',
        description="Spaced message",
        extras={"built-in": True, "category": "Text"},
    )
    async def space(ctx, text):
        await ctx.send(" ".join(text) + " ")
    @bot.command(
        name="vape",
        usage='<"text">',
        description="Vapored message",
        extras={"built-in": True, "category": "Text"},
    )
    async def vape(ctx, text):
        vaped = "".join(
            "\u3000"
            if c == " "
            else chr(ord(c) + 0xFEE0)
            if 0x21 <= ord(c) <= 0x7E
            else c
            for c in text
        )
        await ctx.send(vaped)
    @bot.command(
        name="smart",
        usage='<"text">',
        description="SmArT TaLkEr",
        extras={"built-in": True, "category": "Text"},
    )
    async def smart(ctx, text):
        await ctx.send(
            "".join(random.choice([char.upper(), char.lower()]) for char in text)
        )
    @bot.command(
        name="spoiler",
        usage='<"text">',
        description="Spoil every character",
        extras={"built-in": True, "category": "Text"},
    )
    async def spoiler(ctx, text):
        await ctx.send("".join(f"||{letter}||" for letter in text))
    @bot.command(
        name="ascii",
        usage='<"text">',
        description="Text to ASCII Art",
        extras={"built-in": True, "category": "Text"},
    )
    async def ascii(ctx, message):
        ascii_art = text2art(message)
        await ctx.send(f"```\n{ascii_art}```")
    @bot.command(
        name="reverse",
        usage='<"text">',
        description="Reverse text",
        extras={"built-in": True, "category": "Text"},
    )
    async def reverse(ctx, text):
        await ctx.send(text[::-1])
    @bot.command(
        name="upsidedown",
        usage='<"text">',
        description="Upside down text",
        extras={"built-in": True, "category": "Text"},
    )
    async def upsidedown(ctx, text):
        upside_down = {
            "a": "ɐ",
            "b": "q",
            "c": "ɔ",
            "d": "p",
            "e": "ǝ",
            "f": "ɟ",
            "g": "ɓ",
            "h": "ɥ",
            "i": "ı",
            "j": "ɾ",
            "k": "ʞ",
            "l": "l",
            "m": "ɯ",
            "n": "u",
            "o": "o",
            "p": "d",
            "q": "b",
            "r": "ɹ",
            "s": "s",
            "t": "ʇ",
            "u": "n",
            "v": "ʌ",
            "w": "ʍ",
            "x": "x",
            "y": "ʎ",
            "z": "z",
            "0": "0",
            "1": "⇂",
            "2": "ᄅ",
            "3": "Ɛ",
            "4": "ㄣ",
            "5": "ގ",
            "6": "9",
            "7": "ㄥ",
            "8": "8",
            "9": "6",
            "!": "¡",
            "?": "¿",
        }
        await ctx.send(
            "\u200b".join(
                [
                    upside_down[x.lower()] if x.isalnum() or x in ["!", "?"] else x
                    for x in list(text)
                ]
            )
        )
    @bot.command(
        name="italic",
        usage='<"text">',
        description="Italic text",
        extras={"built-in": True, "category": "Text"},
    )
    async def italic(ctx, text):
        italics = {
            "a": "𝙖",
            "b": "𝙗",
            "c": "𝙘",
            "d": "𝙙",
            "e": "𝙚",
            "f": "𝙛",
            "g": "𝙜",
            "h": "𝙝",
            "i": "𝙞",
            "j": "𝙟",
            "k": "𝙠",
            "l": "𝙡",
            "m": "𝙢",
            "n": "𝙣",
            "o": "𝙤",
            "p": "𝙥",
            "q": "𝙦",
            "r": "𝙧",
            "s": "𝙨",
            "t": "𝙩",
            "u": "𝙪",
            "v": "𝙫",
            "w": "𝙬",
            "x": "𝙭",
            "y": "𝙮",
            "z": "𝙯",
            "0": "*0*",
            "1": "*1*",
            "2": "*2*",
            "3": "*3*",
            "4": "*4*",
            "5": "*5*",
            "6": "*6*",
            "7": "*7*",
            "8": "*8*",
            "9": "*9*",
            "!": "*!*",
            "?": "*?*",
        }
        await ctx.send(
            "\u200b".join(
                [
                    italics[x.lower()] if x.isalnum() or x in ["!", "?"] else x
                    for x in list(text)
                ]
            )
        )
    @bot.command(
        name="1337",
        usage='<"text">',
        description="1337 style message",
        extras={"built-in": True, "category": "Text"},
    )
    async def _1337(ctx, text):
        text = (
            text.replace("a", "4")
            .replace("A", "4")
            .replace("e", "3")
            .replace("E", "3")
            .replace("i", "!")
            .replace("I", "!")
            .replace("o", "0")
            .replace("O", "0")
            .replace("u", "u")
            .replace("U", "U")
        )
        await ctx.send(f"`{text}`")
    @bot.command(
        name="owo",
        usage='<"text">',
        description="Owoify text",
        extras={"built-in": True, "category": "Text"},
    )
    async def owo(ctx, text):
        response = requests.get(f"https://nekos.life/api/v2/owoify?text={text}").json()
        await ctx.send(response["owo"])
    @bot.command(
        name="encode",
        usage='<"text">',
        description="Encode text (base64)",
        extras={"built-in": True, "category": "Text"},
    )
    async def encode(ctx, text: str):
        await ctx.send(b64encode(text.encode("ascii")).decode("ascii"))
    @bot.command(
        name="decode",
        usage='<"text">',
        description="Decode base64",
        extras={"built-in": True, "category": "Text"},
    )
    async def decode(ctx, text: str):
        await ctx.send(b64decode(text.encode("ascii")).decode("ascii"))
    @bot.command(
        name="encrypt",
        usage='<"text">',
        description="Encrypt text (rot13)",
        extras={"built-in": True, "category": "Text"},
    )
    async def encrypt(ctx, text: str):
        await ctx.send(codecs_encode(text, "rot_13"))
    @bot.command(
        name="decrypt",
        usage='<"text">',
        description="Decrypt rot13",
        extras={"built-in": True, "category": "Text"},
    )
    async def decrypt(ctx, text: str):
        await ctx.send(codecs_decode(text, "rot_13"))
    @bot.command(
        name="zalgo",
        usage='<"text">',
        description="Zalgo text",
        extras={"built-in": True, "category": "Text"},
    )
    async def zalgo(ctx, text: str):
        zalgos = {
            "a": "a̸̛̳̥̩̾̿̕̕��̞͉̗̫͇͉",
            "b": "b̶͇̰̘̪̹̾̍̋̔̽͊̎͑͑",
            "c": "c̵̝̮͚̖̫̘̓̊͜ͅ",
            "d": "d̷̙̪̩̄̿̿̊̀͝",
            "e": "e̷̲͎͐͋̀͗͋̐̽",
            "f": "f̸̥͊̀̃̏̽̓͂́̕̚",
            "g": "g̶̨̧͓͕͕̟̱̜͉͇͌̆͌̒͝",
            "h": "h̴͔̻̚",
            "i": "i̴̧͔̰͇̪̣͗́̓̈́̏̎͂̚͠",
            "j": "j̷̢͕̩̭̟͊̄͝",
            "k": "k̷̾̓͜",
            "l": "l̵̹̼̤͙͛́̾̀͒̀̐̀͐",
            "m": "m̶͍̱̮͇͉̄̅͊͛̐͆̈́̏",
            "n": "n̶̡̖̤͓̝̯̽",
            "o": "ỏ̷͈̝͍̳͇͎̯͈̞̼̋͋̃̽͑",
            "p": "p̵̤͖̝̺̳͉̙̹̏̌̓̿̆̂̈́͜͝",
            "q": "q̵̘̈́̐̌̾̊̋͐̃͘",
            "r": "ȑ̸̭͙̀̊̕",
            "s": "s̷̡̜̣̦̞͖͍̬̅̂̆̂̍̒̄͠",
            "t": "ţ̴͖̜̲̱̋̉̍̾͐̒͌͝ͅ",
            "u": "u̷̡̪͂͗̑̉̽̀̍",
            "v": "ṿ̷̙̩̰̪̭̜͔̿͐̋̇̌",
            "w": "w̶̥̅̈́",
            "x": "x̷̨͇̩̥̄̎͂͆̌̅̀͊͠",
            "y": "y̴̫̋̕",
            "z": "ẕ̸̡̺͖̔̌̀̒͝",
            "0": "0̶̺̖̘͎͙̊̇̀̓͆̐͑̈́̈́͝",
            "1": "1̵͙͎̄̽",
            "2": "2̸͓̇̒̓͑͆́̆͊̾̚ͅ",
            "3": "3̵̣̀̍̅̕͠",
            "4": "4̷̡̲̙̲͎̲̰͕͌̓̑̍͆̾",
            "5": "5̵̨͕̽͑̽̂̏̽͛̈́̌͝",
            "6": "6̶̯̤̈̉̽͝",
            "7": "7̸͖͈̝͈́͋̈́̎͛̈́̊͌̌",
            "8": "8̶̘̽̋",
            "9": "9̷̰̮͙͔̝̌͒́̈",
            "!": "!̴̖̠̄̆́",
            "?": "?̵̢̢̧̢̼͚̼͙̟͊͋̆̎̊̈́̈̇̕͜͝",
        }
        await ctx.send(
            "\u200b".join(
                [
                    zalgos[x.lower()] if x.isalnum() or x in ["!", "?"] else x
                    for x in list(text)
                ]
            )
        )
    @bot.command(
        name="morse",
        usage='<"text">',
        description="Translate text to morse code",
        extras={"built-in": True, "category": "Text"},
    )
    async def morse(ctx, text: str):
        await ctx.send(morseTranslate(text))
    @bot.command(
        name="semoji",
        usage='<emoji> <"text">',
        description="Emoji between each word",
        extras={"built-in": True, "category": "Text"},
    )
    async def semoji(ctx, emoji, text):
        await ctx.send(" ".join([f"{split} {emoji}" for split in text.split()]))
    @bot.command(
        name="codeblock",
        usage='<code> <"text">',
        description="Codeblock",
        extras={"built-in": True, "category": "Text"},
    )
    async def codeblock(ctx, code, text):
        codes = [
            "blockquote",
            "cpp",
            "cs",
            "cs",
            "java",
            "python",
            "js",
            "lua",
            "php",
            "html",
            "css",
            "yaml",
            "ini",
            "ascii",
        ]
        code = code.lower()
        if code in codes:
            return await ctx.send(f"```{code}\n{text}```")
        return await ctx.nighty_send(
            title="Codeblock",
            content=f"Markup not found, available markups: {str(codes)}",
        )
    @bot.command(
        name="text2bin",
        usage='<"text">',
        description="Text to binary",
        extras={"built-in": True, "category": "Text"},
    )
    async def text2bin(ctx, text: str):
        await ctx.send(" ".join(format(ord(x), "b") for x in text))
    @bot.command(
        name="bin2text",
        usage='<"text">',
        description="Binary to text",
        extras={"built-in": True, "category": "Text"},
    )
    async def bin2text(ctx, text: str):
        await ctx.send(
            "".join(chr(int(binary_value, 2)) for binary_value in text.split())
        )
    @bot.command(
        name="text2hex",
        usage='<"text">',
        description="Text to hexadecimal",
        extras={"built-in": True, "category": "Text"},
    )
    async def text2hex(ctx, text: str):
        await ctx.send(codecs_encode(text, "hex"))
    @bot.command(
        name="hex2text",
        usage='<"text">',
        description="Hexadecimal to text",
        extras={"built-in": True, "category": "Text"},
    )
    async def hex2text(ctx, text: str):
        await ctx.send(codecs_decode(text, "hex"))
    @bot.command(
        name="avatar",
        usage="<user>",
        description="User avatar",
        extras={"built-in": True, "category": "Image"},
    )
    async def avatar(ctx, user: discord.User):
        await ctx.send(user.avatar.url)
    @bot.command(
        name="userbanner",
        usage="<user>",
        description="User banner",
        extras={"built-in": True, "category": "Image"},
    )
    async def userbanner(ctx, user: discord.User):
        await ctx.send(user.banner.url)
    @bot.command(
        name="serverlogo",
        usage="[server_id]",
        description="Server logo",
        extras={"built-in": True, "category": "Image"},
    )
    async def serverlogo(ctx, server_id: int = None):
        server = bot.get_guild(server_id) if server_id else ctx.guild
        await ctx.send(server.icon.url)
    @bot.command(
        name="serverbanner",
        usage="[server_id]",
        description="Server banner",
        extras={"built-in": True, "category": "Image"},
    )
    async def serverbanner(ctx, server_id: int = None):
        server = bot.get_guild(server_id) if server_id else ctx.guild
        await ctx.send(server.banner.url)
    @bot.command(
        name="grouplogo",
        description="Group logo",
        extras={"built-in": True, "category": "Image"},
    )
    async def grouplogo(ctx):
        await ctx.send(ctx.channel.icon.url)
    @bot.command(
        name="dog",
        description="Random dog image",
        extras={"built-in": True, "category": "Image"},
    )
    async def dog(ctx):
        response = requests.get("https://random.dog/woof.json")
        await ctx.send(response.json()["url"])
    @bot.command(
        name="cat",
        description="Random cat image",
        extras={"built-in": True, "category": "Image"},
    )
    async def cat(ctx):
        response = requests.get("https://thecatapi.com/api/images/get")
        await ctx.send(response.url)
    @bot.command(
        name="fox",
        description="Random fox image",
        extras={"built-in": True, "category": "Image"},
    )
    async def fox(ctx):
        response = requests.get("https://randomfox.ca/floof/")
        await ctx.send(response.json()["image"])
    @bot.command(
        name="meme",
        description="Random meme",
        extras={"built-in": True, "category": "Image"},
    )
    async def meme(ctx):
        response = requests.get("https://meme-api.com/gimme")
        await ctx.send(response.json()["postLink"])
    @bot.command(
        name="wasted",
        usage="<user>",
        description="GTAV wasted overlay",
        extras={"built-in": True, "category": "Image"},
    )
    async def wasted(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/wasted?avatar={user.avatar.url}"
        )
    @bot.command(
        name="pornhub",
        usage='<"word"> <"word">',
        description="Custom P\*rnhub logo",
        extras={"built-in": True, "category": "Image"},
    )
    async def pornhub(ctx, word, word_2):
        await ctx.send(
            f"https://api.alexflipnote.dev/pornhub?text={word}&text2={word_2}"
        )
    @bot.command(
        name="img",
        usage='<"search">',
        description="Search image",
        extras={"built-in": True, "category": "Image"},
    )
    async def img(ctx, search):
        image_search = requests.get(
            f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(search)}",
            headers={
                "Authorization": "Client-ID BcFH673Etlx--mxdrFemwPerbbOgd91scp8_DVgtH4k"
            },
        )
        if image_search.status_code == 200:
            first_result = image_search.json()["results"][0]["urls"]["raw"]
            await ctx.send(first_result)
        else:
            await runDefaultCommandError(ctx, "Image search", "API down.")
    @bot.command(
        name="pride",
        usage="<user>",
        description="Pride overlay",
        extras={"built-in": True, "category": "Image"},
    )
    async def pride(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/gay?avatar={user.avatar.url}"
        )
    @bot.command(
        name="triggered",
        usage="<user>",
        description="Triggered GIF overlay",
        extras={"built-in": True, "category": "Image"},
    )
    async def triggered(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/triggered?avatar={user.avatar.url}"
        )
    @bot.command(
        name="respect",
        usage="<user>",
        description="Pay respects",
        extras={"built-in": True, "category": "Image"},
    )
    async def respect(ctx, user: discord.User):
        await ctx.send(
            content=f"{user.mention} earned respect\nhttps://media1.tenor.com/images/59d49eae6bef50f741531c561fac1f3a/tenor.gif"
        )
    @bot.command(
        name="drake",
        usage='<"no, yes">',
        description="Drake meme",
        extras={"built-in": True, "category": "Image"},
    )
    async def drake(ctx, choices):
        choices = choices.split(", ")
        await ctx.send(
            f"https://api.alexflipnote.dev/drake?top={choices[0]}&bottom={choices[1]}"
        )
    @bot.command(
        name="didyoumean",
        usage='<"search, did you mean">',
        description="Google did you mean search",
        extras={"built-in": True, "category": "Image"},
    )
    async def didyoumean(ctx, choices):
        choices = choices.split(", ")
        await ctx.send(
            f"https://api.alexflipnote.dev/didyoumean?top={choices[0]}&bottom={choices[1]}"
        )
    @bot.command(
        name="tweet",
        usage='<"name"> <"message">',
        description="Fake tweet",
        extras={"built-in": True, "category": "Image"},
    )
    async def tweet(ctx, name, message):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=tweet&username={name}&text={message}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="trumptweet",
        usage='<"message">',
        description="Fake Donald Trump tweet",
        extras={"built-in": True, "category": "Image"},
    )
    async def trumptweet(ctx, message):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=trumptweet&text={message}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="changemymind",
        usage='<"text">',
        description="Change my mind",
        extras={"built-in": True, "category": "Image"},
    )
    async def changemymind(ctx, text):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=changemymind&text={text}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="ship",
        usage="<user> <user>",
        description="Ship two users",
        extras={"built-in": True, "category": "Image"},
    )
    async def ship(ctx, user: discord.User, user_2: discord.User):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=ship&user1={user.avatar.url}&user2={user_2.avatar.url}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="facts",
        usage='<"text">',
        description="Facts book",
        extras={"built-in": True, "category": "Image"},
    )
    async def facts(ctx, text):
        await ctx.send(f"https://api.alexflipnote.dev/facts?text={text}")
    @bot.command(
        name="clyde",
        usage='<"text">',
        description="Discord Clyde message",
        extras={"built-in": True, "category": "Image"},
    )
    async def clyde(ctx, text):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=clyde&text={text}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="kannagen",
        usage='<"text">',
        description="Kannagen message",
        extras={"built-in": True, "category": "Image"},
    )
    async def kannagen(ctx, text):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=kannagen&text={text}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="trash",
        usage="<user>",
        description="Trash user",
        extras={"built-in": True, "category": "Image"},
    )
    async def trash(ctx, user: discord.User):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=trash&url={user.avatar.url}"
        ).json()
        await ctx.send(response["message"])
    @bot.command(
        name="whowouldwin",
        usage="<user> <user>",
        description="Who would win",
        extras={"built-in": True, "category": "Image"},
    )
    async def whowouldwin(ctx, user: discord.User, user_2: discord.User):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=whowouldwin&user1={user.avatar.url}&user2={user_2.avatar.url}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="qrcode",
        usage='<"text">',
        description="Generate QR code",
        extras={"built-in": True, "category": "Image"},
    )
    async def qrcode_(ctx, text):
        qr = QRCode(
            version=1,
            error_correction=ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(text)
        img = qr.make_image(fill_color="white", back_color="black").save("QR.png")
        await ctx.send(file=discord.File("QR.png"))
        os.remove("QR.png")
    @bot.command(
        name="phcomment",
        usage='<user> <"text">',
        description="P\*rnhub comment",
        extras={"built-in": True, "category": "Image"},
    )
    async def phcomment(ctx, user: discord.User, text):
        response = requests.get(
            f"https://nekobot.xyz/api/imagegen?type=phcomment&username={user.name}&text={text}&image={user.avatar.url}"
        )
        await ctx.send(response.json()["message"])
    @bot.command(
        name="pikachu",
        description="Pikachu",
        extras={"built-in": True, "category": "Image"},
    )
    async def pikachu(ctx):
        response = requests.get("https://some-random-api.com/img/pikachu")
        await ctx.send(response.json()["link"])
    @bot.command(
        name="panda",
        description="Random panda",
        extras={"built-in": True, "category": "Image"},
    )
    async def panda(ctx):
        response = requests.get("https://some-random-api.com/img/panda")
        await ctx.send(response.json()["link"])
    @bot.command(
        name="redpanda",
        description="Random red panda",
        extras={"built-in": True, "category": "Image"},
    )
    async def redpanda(ctx):
        response = requests.get("https://some-random-api.com/img/red_panda")
        await ctx.send(response.json()["link"])
    @bot.command(
        name="duck",
        description="Random duck",
        extras={"built-in": True, "category": "Image"},
    )
    async def duck(ctx):
        response = requests.get("https://random-d.uk/api/random")
        await ctx.send(response.json()["url"])
    @bot.command(
        name="bird",
        description="Random bird",
        extras={"built-in": True, "category": "Image"},
    )
    async def bird(ctx):
        response = requests.get("https://some-random-api.com/img/bird")
        await ctx.send(response.json()["link"])
    @bot.command(
        name="koala",
        description="Random koala",
        extras={"built-in": True, "category": "Image"},
    )
    async def koala(ctx):
        response = requests.get("https://some-random-api.com/img/koala")
        await ctx.send(response.json()["link"])
    @bot.command(
        name="kangaroo",
        description="Random kangaroo",
        extras={"built-in": True, "category": "Image"},
    )
    async def kangaroo(ctx):
        response = requests.get("https://some-random-api.com/img/kangaroo")
        await ctx.send(response.json()["link"])
    @bot.command(
        name="raccoon",
        description="Random raccoon",
        extras={"built-in": True, "category": "Image"},
    )
    async def raccoon(ctx):
        response = requests.get("https://some-random-api.com/animal/raccoon")
        await ctx.send(response.json()["image"])
    @bot.command(
        name="whale",
        description="Random whale",
        extras={"built-in": True, "category": "Image"},
    )
    async def whale(ctx):
        response = requests.get("https://some-random-api.com/img/whale")
        await ctx.send(response.json()["link"])
    @bot.command(
        name="anymore",
        usage='<"text"> <"text">',
        description="Yall got any more of that ..",
        extras={"built-in": True, "category": "Image"},
    )
    async def anymore(ctx, top, bottom):
        await ctx.send(
            f"https://www.apimeme.com/meme?meme=Yall-Got-Any-More-Of-That&top={top}&bottom={bottom}"
        )
    @bot.command(
        name="yaoming",
        usage='<"text"> <"text">',
        description="Yao Ming",
        extras={"built-in": True, "category": "Image"},
    )
    async def yaoming(ctx, top, bottom):
        await ctx.send(
            f"https://www.apimeme.com/meme?meme=Yao-Ming&top={top}&bottom={bottom}"
        )
    @bot.command(
        name="putin",
        usage='<"text"> <"text">',
        description="Vladimir Putin",
        extras={"built-in": True, "category": "Image"},
    )
    async def putin(ctx, top, bottom):
        await ctx.send(
            f"https://www.apimeme.com/meme?meme=Vladimir-Putin&top={top}&bottom={bottom}"
        )
    @bot.command(
        name="goodguy",
        usage='<"text"> <"text">',
        description="Good guy",
        extras={"built-in": True, "category": "Image"},
    )
    async def goodguy(ctx, top, bottom):
        await ctx.send(
            f"https://www.apimeme.com/meme?meme=Good-Guy-Putin&top={top}&bottom={bottom}"
        )
    @bot.command(
        name="yakuza",
        usage='<"text"> <"text">',
        description="Yakuza",
        extras={"built-in": True, "category": "Image"},
    )
    async def yakuza(ctx, top, bottom):
        await ctx.send(
            f"https://www.apimeme.com/meme?meme=Yakuza&top={top}&bottom={bottom}"
        )
    @bot.command(
        name="sus",
        usage='<"text"> <"text">',
        description="Futurama sus",
        extras={"built-in": True, "category": "Image"},
    )
    async def sus(ctx, top, bottom):
        await ctx.send(
            f"https://www.apimeme.com/meme?meme=Futurama-Fry&top={top}&bottom={bottom}"
        )
    @bot.command(
        name="think",
        usage='<"text"> <"text">',
        description="Think",
        extras={"built-in": True, "category": "Image"},
    )
    async def think(ctx, top, bottom):
        await ctx.send(
            f"https://www.apimeme.com/meme?meme=Think&top={top}&bottom={bottom}"
        )
    @bot.command(
        name="simpcard",
        usage="<user>",
        description="Simp card",
        extras={"built-in": True, "category": "Image"},
    )
    async def simpcard(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/simpcard?avatar={user.avatar.url}"
        )
    @bot.command(
        name="horny",
        usage="<user>",
        description="Horny card",
        extras={"built-in": True, "category": "Image"},
    )
    async def horny(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/horny?avatar={user.avatar.url}"
        )
    @bot.command(
        name="lolice",
        usage="<user>",
        description="Lolicon police",
        extras={"built-in": True, "category": "Image"},
    )
    async def lolice(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/lolice?avatar={user.avatar.url}"
        )
    @bot.command(
        name="heart",
        usage="<user>",
        description="Heart",
        extras={"built-in": True, "category": "Image"},
    )
    async def heart(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/misc/heart?avatar={user.avatar.url}"
        )
    @bot.command(
        name="jail",
        usage="<user>",
        description="Jail user",
        extras={"built-in": True, "category": "Image"},
    )
    async def jail(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/overlay/jail?avatar={user.avatar.url}"
        )
    @bot.command(
        name="soviet",
        usage="<user>",
        description="Soviet comrade",
        extras={"built-in": True, "category": "Image"},
    )
    async def soviet(ctx, user: discord.User):
        await ctx.send(
            f"https://some-random-api.com/canvas/overlay/comrade?avatar={user.avatar.url}"
        )
    def isNSFW(channel):
        config = getConfig()
        if channel.guild:
            if config["riskmode"] or channel.is_nsfw():
                return True
            else:
                return False
        else:
            return True
    @bot.command(
        name="nsfw",
        description="NSFW commands",
        help=f"To use NSFW commands in regular channels, enable riskmode using {bot.command_prefix}riskmode on",
        extras={"built-in": True, "category": "Image"},
    )
    async def nsfw(ctx):
        if isNSFW(ctx.channel):
            await ctx.nighty_help(title="NSFW", commands=getCategoryCommands("NSFW"))
        else:
            await ctx.nighty_send(
                title="NSFW",
                content=f"NSFW is disabled, please use this command in a NSFW channel or use `{bot.command_prefix}riskmode on`.",
            )
    @bot.command(
        name="ass",
        description="Ass image (+18)",
        help=f"To use NSFW commands in regular channels, enable riskmode using {bot.command_prefix}riskmode on",
        extras={"built-in": True, "category": "NSFW"},
    )
    async def ass(ctx):
        if isNSFW(ctx.channel):
            response = requests.get("https://nekobot.xyz/api/image?type=ass").json()
            await ctx.send(response["message"])
        else:
            await ctx.nighty_send(
                title="NSFW",
                content=f"NSFW is disabled, please use this command in a NSFW channel or use `{bot.command_prefix}riskmode on`.",
            )
    @bot.command(
        name="boobs",
        description="Boobs image (+18)",
        help=f"To use NSFW commands in regular channels, enable riskmode using {bot.command_prefix}riskmode on",
        extras={"built-in": True, "category": "NSFW"},
    )
    async def boobs(ctx):
        if isNSFW(ctx.channel):
            response = requests.get("https://nekobot.xyz/api/image?type=boobs").json()
            await ctx.send(response["message"])
        else:
            await ctx.nighty_send(
                title="NSFW",
                content=f"NSFW is disabled, please use this command in a NSFW channel or use `{bot.command_prefix}riskmode on`.",
            )
    @bot.command(
        name="pussy",
        description="Pussy image (+18)",
        help=f"To use NSFW commands in regular channels, enable riskmode using {bot.command_prefix}riskmode on",
        extras={"built-in": True, "category": "NSFW"},
    )
    async def pussy(ctx):
        if isNSFW(ctx.channel):
            response = requests.get("https://nekobot.xyz/api/image?type=pussy").json()
            await ctx.send(response["message"])
        else:
            await ctx.nighty_send(
                title="NSFW",
                content=f"NSFW is disabled, please use this command in a NSFW channel or use `{bot.command_prefix}riskmode on`.",
            )
    @bot.command(
        name="hentai",
        description="Hentai image (+18)",
        help=f"To use NSFW commands in regular channels, enable riskmode using {bot.command_prefix}riskmode on",
        extras={"built-in": True, "category": "NSFW"},
    )
    async def hentai(ctx):
        if isNSFW(ctx.channel):
            response = requests.get("https://nekobot.xyz/api/image?type=hentai").json()
            await ctx.send(response["message"])
        else:
            await ctx.nighty_send(
                title="NSFW",
                content=f"NSFW is disabled, please use this command in a NSFW channel or use `{bot.command_prefix}riskmode on`.",
            )
    @bot.command(
        name="pgif",
        description="+18 GIF",
        help=f"To use NSFW commands in regular channels, enable riskmode using {bot.command_prefix}riskmode on",
        extras={"built-in": True, "category": "NSFW"},
    )
    async def pgif(ctx):
        if isNSFW(ctx.channel):
            response = requests.get("https://nekobot.xyz/api/image?type=pgif").json()
            await ctx.send(response["message"])
        else:
            await ctx.nighty_send(
                title="NSFW",
                content=f"NSFW is disabled, please use this command in a NSFW channel or use `{bot.command_prefix}riskmode on`.",
            )
    @bot.command(
        name="noleave",
        usage="[user]",
        description="Force user in group",
        help="Adds the user back to the group chat as soon as they leave, the user needs to be in your friends for you to add them back.\n> To stop adding them back, use the command without arguments.",
        extras={"built-in": True, "category": "Troll"},
    )
    async def noleave(ctx, user: discord.User = None):
        bot.config["noleave"] = user
        await ctx.nighty_send(title="No leave", content=f"No leave: {user}")
    @bot.command(
        name="forcenick",
        usage='<user> ["name"]',
        description="Force nickname to user",
        help="You need the manage_nicknames permission for this, forces a nickname onto someone regardless of them changing it.\n> To stop forcing, use the command without giving a name.",
        extras={"built-in": True, "category": "Troll"},
    )
    async def forcenick(ctx, user: discord.Member, name=None):
        if name is None:
            bot.config["forcenick"] = None
        else:
            bot.config["forcenick"] = {
                "user": user.id,
                "name": name,
                "server": ctx.guild.id,
            }
        await user.edit(nick=name)
        await ctx.nighty_send(
            title="Force nick", content=f"Force: {user}\n> Nick: {name}"
        )
    @bot.command(
        name="spy",
        usage="[user]",
        description="Spy user",
        help="Get notified about as much possible regarding events related to the user. To stop, use the command without giving an user.",
        extras={"built-in": True, "category": "Troll"},
    )
    async def spy(ctx, user: discord.User = None):
        bot.config["spy"] = user
        await ctx.nighty_send(title="Spy", content=f"Spy: {user}")
    @bot.command(
        name="empty",
        description="Send empty message",
        extras={"built-in": True, "category": "Troll"},
    )
    async def empty(ctx):
        await ctx.send(chr(173))
    @bot.command(
        name="ghostping",
        usage="<user>",
        description="Ghostping user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def ghostping(ctx, user: discord.User):
        return
    @bot.command(
        name="gprole",
        usage="<role>",
        description="Ghostping role",
        extras={"built-in": True, "category": "Troll"},
    )
    async def gprole(ctx, role: discord.Role):
        return
    @bot.command(
        name="hiddeninvite",
        usage='<url> <"text">',
        description="Hide invite in message",
        extras={"built-in": True, "category": "Troll"},
    )
    async def hiddeninvite(ctx, url, text):
        vanity = (
            text
            + "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||"
            + url
        )
        await ctx.send(vanity)
    @bot.command(
        name="hiddenping",
        usage='<user> <"text">',
        description="Hide ping in message",
        extras={"built-in": True, "category": "Troll"},
    )
    async def hiddenping(ctx, user: discord.User, text):
        vanity = (
            text
            + "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||"
            + user.mention
        )
        await ctx.send(vanity)
    @bot.command(
        name="purgehack",
        description="Flood chat with invisible message",
        extras={"built-in": True, "category": "Troll"},
    )
    async def purgehack(ctx):
        await ctx.send("ﾠﾠ" + "\n" * 400 + "ﾠﾠ")
    @bot.command(
        name="fakenitro",
        usage="<url>",
        description="Hide a link behind nitro gift link",
        extras={"built-in": True, "category": "Troll"},
    )
    async def fakenitro(ctx, url):
        await ctx.send(f"[Free Nitro!]({url})")
    @bot.command(
        name="hyperlink",
        usage='<url> <"text">',
        description="Create a link out of your text",
        extras={"built-in": True, "category": "Tools"},
    )
    async def hyperlink(ctx, url, text):
        await ctx.send(f"[{text}]({url})")
    @bot.command(
        name="mimic",
        usage="[user]",
        description="Copy every user's messages",
        help="Use the command without any user to stop mimicking current user.",
        extras={"built-in": True, "category": "Troll"},
    )
    async def mimic(ctx, user: discord.User = None):
        bot.config["mimic"] = user
        await ctx.nighty_send(title="Mimic", content=f"Now copying: {user}")
    @bot.command(
        name="smartmimic",
        usage="[user]",
        description="Copy every user's messages (ThE SmArT wAy)",
        help="Use the command without any user to stop mimicking current user.",
        extras={"built-in": True, "category": "Troll"},
    )
    async def smartmimic(ctx, user: discord.User = None):
        bot.config["smartmimic"] = user
        await ctx.nighty_send(title="Mimic (SmArT)", content=f"Now copying: {user}")
    @bot.command(
        name="mimicreply",
        usage="[user]",
        description="Copy every user's messages (in replies)",
        help="Use the command without any user to stop mimicking current user.",
        extras={"built-in": True, "category": "Troll"},
    )
    async def mimicreply(ctx, user: discord.User = None):
        bot.config["mimicreply"] = user
        await ctx.nighty_send(title="Mimic (reply)", content=f"Now copying: {user}")
    @bot.command(
        name="mimicregional",
        usage="[user]",
        description="Copy every user's messages (in letter emojis)",
        help="Use the command without any user to stop mimicking current user.",
        extras={"built-in": True, "category": "Troll"},
    )
    async def mimicregional(ctx, user: discord.User = None):
        bot.config["mimicregional"] = user
        await ctx.nighty_send(title="Mimic (emojis)", content=f"Now copying: {user}")
    @bot.command(
        name="afk",
        usage="[toggle]",
        description="AFK mode",
        help="Use the command without arguments to display afk menu.",
        extras={"built-in": True, "category": "Utils"},
    )
    async def afk(ctx, toggle=None):
        if toggle is None:
            await ctx.nighty_help(title="AFK", commands=getCategoryCommands("AFK"))
        elif toggle:
            toggle = toggle.lower()
            if toggle == "on":
                setAFKState(True)
            elif toggle == "off":
                setAFKState(False)
            else:
                return
            await ctx.nighty_send(title="AFK", content=f"AFK: {toggle}")
    @bot.command(
        name="afkblacklist",
        usage="[add/remove] [user]",
        description="AFK Blacklist",
        extras={"built-in": True, "category": "AFK"},
    )
    async def afkblacklist(ctx, method: str = None, user: discord.User = None):
        if method:
            method = method.lower()
            if user:
                if method == "add":
                    if user.id not in getAFKConfig()["blacklist"]:
                        addUserToAFKBlacklist(user.id)
                        return await ctx.nighty_send(
                            title="AFK blacklist", content=f"Added: {user}"
                        )
                    else:
                        return await ctx.nighty_send(
                            title="AFK blacklist",
                            content=f"Already blacklisted: {user}",
                        )
                elif method == "remove" or method == "delete":
                    if user in getAFKConfig()["blacklist"]:
                        removeUserFromAFKBlacklist(user.id)
                        return await ctx.nighty_send(
                            title="AFK blacklist", content=f"Removed: {user}"
                        )
        await ctx.nighty_send(
            title="AFK blacklist",
            content=", ".join([user.name for user in getAFKConfig()["blacklist"]]),
        )
    @bot.command(
        name="afkuser",
        usage="[user]",
        description="AFK for one user",
        extras={"built-in": True, "category": "AFK"},
    )
    async def afkuser(ctx, user: discord.User = None):
        bot.config["afkuser"] = user
        await ctx.nighty_send(title="AFK user", content=f"AFK for: {user.name}")
    @bot.command(
        name="afkmessage",
        usage="<message>",
        description="Message to send when AFK",
        extras={"built-in": True, "category": "AFK"},
    )
    async def afkmessage(ctx, message):
        setAFKMessage(message)
        await ctx.nighty_send(title="AFK", content=f"Message: {message}")
    @bot.command(
        name="voicemove",
        usage="<amount>",
        description="Move from one voice channel to another in the server",
        extras={"built-in": True, "category": "Troll"},
    )
    async def voicemove(ctx, amount: int):
        global cycling
        cycling = True
        for x in range(amount):
            if cycling:
                channel = random.choice(ctx.guild.voice_channels)
                await channel.connect()
                await asyncio.sleep(0.5)
                for y in bot.voice_clients:
                    if y.guild == ctx.guild:
                        await y.disconnect()
    @bot.command(
        name="deletesend",
        usage="[user]",
        description="Send every message the user deletes",
        help="Use the command without arguments to stop with the current user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def deletesend(ctx, user: discord.User = None):
        bot.config["deletesend"] = user
        await ctx.nighty_send(title="Delete send", content=f"User: {user}")
    @bot.command(
        name="editsend",
        usage="[user]",
        description="Send every message the user edits",
        help="Use the command without arguments to stop with the current user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def editsend(ctx, user: discord.User = None):
        bot.config["editsend"] = user
        await ctx.nighty_send(title="Edit send", content=f"User: {user}")
    @bot.command(
        name="forcekick",
        usage="[user]",
        description="Kick user on server joins (where possible)",
        help="Use the command without arguments to stop with the current user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def forcekick(ctx, user: discord.Member = None):
        bot.config["forcekick"] = user
        await ctx.nighty_send(title="Force kick", content=f"User: {user}")
    @bot.command(
        name="forcedisconnect",
        usage="[user]",
        description="Disconnect user from voice channel (where possible)",
        help="Use the command without arguments to stop with the current user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def forcedisconnect(ctx, user: discord.User = None):
        bot.config["forcedisconnect"] = user
        await ctx.nighty_send(title="Force disconnect", content=f"User: {user}")
    @bot.command(
        name="reactuser",
        usage="[user] [emoji]",
        description="React every message the user sends",
        help="Use the command without arguments to stop with the current user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def reactuser(ctx, user: discord.User = None, emoji=None):
        bot.config["reactuser"] = user
        bot.config["reactuseremoji"] = emoji
        await ctx.nighty_send(
            title="React user", content=f"User: {user}\n> Emoji: {emoji}"
        )
    @bot.command(
        name="deleteannoy",
        usage="[user]",
        description="Delete every message the user sends",
        help="Use the command without arguments to stop with the current user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def deleteannoy(ctx, user: discord.User = None):
        bot.config["deleteannoy"] = user
        await ctx.nighty_send(title="Delete annoy", content=f"User: {user}")
    @bot.command(
        name="unreact",
        usage="[user]",
        description="Delete every reaction the user makes",
        help="Use the command without arguments to stop with the current user",
        extras={"built-in": True, "category": "Troll"},
    )
    async def unreact(ctx, user: discord.User = None):
        bot.config["unreact"] = user
        await ctx.nighty_send(title="Un react", content=f"User: {user}")
    @bot.command(
        name="dick",
        usage="<user>",
        description="Dick size measurement",
        extras={"built-in": True, "category": "Fun"},
    )
    async def dick(ctx, user: discord.User):
        size_ = random.randint(1, 15)
        dong = "=" * size_
        await ctx.nighty_send(
            title="Dick size", content=f"{user}'s size:\n>
        )
    @bot.command(
        name="gay",
        usage="<user>",
        description="How gay",
        extras={"built-in": True, "category": "Fun"},
    )
    async def gay(ctx, user: discord.User):
        size = random.randint(1, 100)
        await ctx.nighty_send(title="How gay", content=f"{user} is {size}% gay")
    @bot.command(
        name="iq",
        usage="<user>",
        description="IQ test",
        extras={"built-in": True, "category": "Fun"},
    )
    async def iq(ctx, user: discord.User):
        size = random.randint(-3, 150)
        await ctx.nighty_send(title="IQ test", content=f"{user}' IQ: {size}")
    @bot.command(
        name="insult",
        usage="<user>",
        description="Insult user",
        extras={"built-in": True, "category": "Fun"},
    )
    async def insult(ctx, user: discord.User):
        r = requests.get("https://insult.mattbas.org/api/insult").text
        await ctx.send(f"{user.mention}, {r}")
    @bot.command(
        name="hug",
        usage="<user>",
        description="Hug user",
        extras={"built-in": True, "category": "Fun"},
    )
    async def hug(ctx, user: discord.User):
        r = requests.get("https://nekos.life/api/v2/img/hug").json()
        await ctx.send(f"{user.mention}")
        await ctx.send(r["url"])
    @bot.command(
        name="kiss",
        usage="<user>",
        description="Kiss user",
        extras={"built-in": True, "category": "Fun"},
    )
    async def kiss(ctx, user: discord.User):
        r = requests.get("https://nekos.life/api/v2/img/kiss").json()
        await ctx.send(f"{user.mention}")
        await ctx.send(r["url"])
    @bot.command(
        name="slap",
        usage="<user>",
        description="Slap user",
        extras={"built-in": True, "category": "Fun"},
    )
    async def slap(ctx, user: discord.User):
        r = requests.get("https://nekos.life/api/v2/img/slap").json()
        await ctx.send(f"{user.mention}")
        await ctx.send(r["url"])
    @bot.command(
        name="pat",
        usage="<user>",
        description="Pat user",
        extras={"built-in": True, "category": "Fun"},
    )
    async def pat(ctx, user: discord.User):
        r = requests.get("https://nekos.life/api/v2/img/pat").json()
        await ctx.send(f"{user.mention}")
        await ctx.send(r["url"])
    @bot.command(
        name="feed",
        usage="<user>",
        description="Feed user",
        extras={"built-in": True, "category": "Fun"},
    )
    async def feed(ctx, user: discord.User):
        r = requests.get("https://nekos.life/api/v2/img/feed").json()
        await ctx.send(f"{user.mention}")
        await ctx.send(r["url"])
    @bot.command(
        name="wink",
        usage="<user>",
        description="Wink user",
        extras={"built-in": True, "category": "Fun"},
    )
    async def wink(ctx, user: discord.User):
        r = requests.get("https://some-random-api.com/animu/wink").json()
        await ctx.send(f"{user.mention}")
        await ctx.send(r["link"])
    @bot.command(
        name="triggertyping",
        usage="<seconds> [channel_id]",
        description="Start typing in the chat",
        extras={"built-in": True, "category": "Fun"},
    )
    async def triggertyping(ctx, seconds: int, channel_id: int = None):
        channel = bot.get_channel(channel_id) or ctx.channel
        async with channel.typing():
            await asyncio.sleep(seconds)
    @bot.command(
        name="tts",
        usage='<"text">',
        description="Text to speech message",
        extras={"built-in": True, "category": "Fun"},
    )
    async def tts(ctx, text: str):
        file = io.BytesIO()
        tts = gTTS(text=text.lower(), lang="en")
        tts.write_to_fp(file)
        file.seek(0)
        await ctx.send(file=discord.File(file, f"{text.replace(' ', '_')}.mp3"))
    @bot.command(
        name="8ball",
        usage='<"question">',
        description="Get an answer to your question",
        extras={"built-in": True, "category": "Fun"},
    )
    async def eightball(ctx, question: str):
        responses = [
            "How can i know that lol",
            "Yeah",
            "Mhm",
            "Go for it!",
            "I don't think so",
            "Too hard to tell",
            "Thats possible",
            "You may rely on it.",
            "Sure",
            "My reply is no.",
            "Don't count on it.",
            "Doubt.",
            "Concentrate and ask again.",
            "Maybe",
            "Better not tell you now..",
            "It might be true",
            "Don't count on it",
            "dafuq?",
            "What are you talking about ?",
            "I don't know",
            "I don't get you",
            "Absolutetly!",
        ]
        await ctx.nighty_send(
            title="8 Ball", content=f"{question}:\n> {random.choice(responses)}"
        )
    @bot.command(
        name="coinflip",
        description="Flip a coin",
        extras={"built-in": True, "category": "Fun"},
    )
    async def coinflip(ctx):
        flip = random.choice(("Heads", "Tails"))
        if "Heads" in flip:
            return await ctx.send("https://i.dlpng.com/static/png/6736940_preview.png")
        elif "Tails" in flip:
            return await ctx.send(
                "https://www.nicepng.com/png/full/146-1464848_quarter-tail-png-tails-on-a-coin.png"
            )
    @bot.command(
        name="wyr",
        description="Would you rather",
        extras={"built-in": True, "category": "Fun"},
    )
    async def wyr(ctx):
        r = requests.get("https://www.conversationstarters.com/wyrqlist.php").text
        soup = BeautifulSoup(r, "html.parser")
        qa = soup.find(id="qa").text
        qor = soup.find(id="qor").text
        qb = soup.find(id="qb").text
        await ctx.nighty_send(
            title="Would you rather", content=f"{qa}\n> {qor}\n> {qb}"
        )
    @bot.command(
        name="advice",
        description="Get an advice",
        extras={"built-in": True, "category": "Fun"},
    )
    async def advice(ctx):
        meme = requests.get("https://api.adviceslip.com/advice").json()
        await ctx.nighty_send(title="Advice", content=meme["slip"]["advice"])
    @bot.command(
        name="topic",
        description="Get a random topic",
        extras={"built-in": True, "category": "Fun"},
    )
    async def topic(ctx):
        r = requests.get("https://www.conversationstarters.com/generator.php").text
        soup = BeautifulSoup(r, "html.parser")
        topic = soup.find(id="random").text
        await ctx.nighty_send(title="Random topic", content=topic)
    @bot.command(
        name="mreact",
        usage="<emoji> <amount>",
        description="React on messages in the channel",
        extras={"built-in": True, "category": "Fun"},
    )
    async def mreact(ctx, emoji, amount: int):
        for message in [
            message async for message in ctx.message.channel.history(limit=amount)
        ]:
            try:
                await message.add_reaction(emoji)
            except:
                pass
    @bot.command(
        name="spamreact",
        usage='<"emojis">',
        description="Spam reactions on last message",
        extras={"built-in": True, "category": "Fun"},
    )
    async def spamreact(ctx, emojis):
        emojis = emojis.split()
        for message in [
            message async for message in ctx.message.channel.history(limit=1)
        ]:
            for reaction in emojis:
                try:
                    await message.add_reaction(reaction)
                except:
                    pass
    @bot.command(
        name="choose",
        usage='<"choice1, choice2, ..">',
        description="Let the bot choose",
        extras={"built-in": True, "category": "Fun"},
    )
    async def choose(ctx, choices: commands.clean_content):
        choices = choices.split(",")
        choices[0] = " " + choices[0]
        await ctx.nighty_send(title="I choose", content=str(random.choice(choices))[1:])
    @bot.command(
        name="numberfact",
        usage="<number>",
        description="Get fact about a number",
        extras={"built-in": True, "category": "Fun"},
    )
    async def numberfact(ctx, number: int):
        r = requests.get(f"http://numbersapi.com/{number}").text
        await ctx.nighty_send(title="Number fact", content=r)
    @bot.command(
        name="catfact",
        description="Random cat fact",
        extras={"built-in": True, "category": "Fun"},
    )
    async def catfact(ctx):
        r = requests.get(f"https://catfact.ninja/fact").json()
        await ctx.nighty_send(title="Cat fact", content=r["fact"])
    @bot.command(
        name="dogfact",
        description="Random dog fact",
        extras={"built-in": True, "category": "Fun"},
    )
    async def dogfact(ctx):
        r = requests.get(f"https://some-random-api.com/facts/dog").json()
        await ctx.nighty_send(title="Dog fact", content=r["fact"])
    @bot.command(
        name="joke",
        description="Random joke",
        extras={"built-in": True, "category": "Fun"},
    )
    async def joke(ctx):
        r = requests.get(
            f"https://icanhazdadjoke.com", headers={"Accept": "application/json"}
        ).json()
        await ctx.nighty_send(title="Random joke", content=r["joke"])
    @bot.command(
        name="rickroll",
        description="Send rick roll",
        extras={"built-in": True, "category": "Fun"},
    )
    async def rickroll(ctx):
        lyrics = "We're no strangers to love\nYou know the rules and so do I\nA full commitment's what I'm thinking of\nYou wouldn't get this from any other guy\nI just wanna tell you how I'm feeling\nGotta make you understand\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nWe've known each other for so long\nYour heart's been aching but you're too shy to say it\nInside we both know what's been going on\nWe know the game and we're gonna play it\nAnd if you ask me how I'm feeling\nDon't tell me you're too blind to see\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give, never gonna give\n(Give you up)\n(Ooh) Never gonna give, never gonna give\n(Give you up)\nWe've known each other for so long\nYour heart's been aching but you're too shy to say it\nInside we both know what's been going on\nWe know the game and we're gonna play it\nI just wanna tell you how I'm feeling\nGotta make you understand\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry"
        await ctx.send(lyrics)
    @bot.command(
        name="tronald",
        description="Random Donald Trump tweet",
        extras={"built-in": True, "category": "Fun"},
    )
    async def tronald(ctx):
        r = requests.get(f"https://api.tronalddump.io/random/quote").json()
        response = r["value"]
        url = r["_embedded"]["source"][0]["url"]
        await ctx.nighty_send(title="Tronald Dump", content=f"{response}\n> {url}")
    @bot.command(
        name="emojireact",
        usage='<"text"> [channel_id]',
        description="",
        extras={"built-in": True, "category": "Fun"},
    )
    async def emojireact(ctx, text, channel_id: int = None):
        channel = bot.get_channel(channel_id) or ctx.channel
        for message in [message async for message in channel.history(limit=1)]:
            for r in [
                regionals[x.lower()] if x.isalnum() or x in ["!", "?"] else x
                for x in list(text)
            ]:
                try:
                    await message.add_reaction(r)
                    await asyncio.sleep(0.25)
                except:
                    pass
    @bot.command(
        name="kanye",
        description="Kanye quote",
        extras={"built-in": True, "category": "Fun"},
    )
    async def kanye(ctx):
        r = requests.get("https://api.kanye.rest").json()
        await ctx.nighty_send(title="Kanye", content=r["quote"])
    @bot.command(
        name="question",
        description="Random question",
        extras={"built-in": True, "category": "Fun"},
    )
    async def question(ctx):
        r = requests.get("https://nekos.life/api/v2/why").json()
        await ctx.nighty_send(title="Kanye", content=r["why"])
    @bot.command(
        name="cyclechannel",
        usage='<"text"> [channel_id]',
        description="Cycle channel name",
        extras={"built-in": True, "category": "Fun"},
    )
    async def cyclechannel(ctx, text, channel_id: int = None):
        channel = bot.get_channel(channel_id) or ctx.channel
        global cycling
        cycling = True
        await ctx.nighty_send(
            title="Cycle channel name", content=f"Started cycling: {channel}"
        )
        while cycling:
            for t in range(1, len(text) + 1):
                if cycling:
                    await channel.edit(name=text[:t])
                    await asyncio.sleep(1.5)
    @bot.command(
        name="cyclerole",
        usage='<role> <"text">',
        description="Cycle role name",
        extras={"built-in": True, "category": "Fun"},
    )
    async def cyclerole(ctx, role: discord.Role, text):
        global cycling
        cycling = True
        await ctx.nighty_send(
            title="Cycle role name", content=f"Started cycling: {role}"
        )
        while cycling:
            for t in range(1, len(text) + 1):
                if cycling:
                    await role.edit(name=text[:t])
                    await asyncio.sleep(1.5)
    @bot.command(
        name="cyclenick",
        usage='<member> <"nick">',
        description="Cycle nick name",
        extras={"built-in": True, "category": "Fun"},
    )
    async def cyclenick(ctx, member: discord.Member, text):
        global cycling
        cycling = True
        await ctx.nighty_send(
            title="Cycle nick name", content=f"Started cycling: {member}"
        )
        while cycling:
            for t in range(1, len(text) + 1):
                if cycling:
                    await member.edit(name=text[:t])
                    await asyncio.sleep(1.5)
    @bot.command(
        name="rps",
        description="Rock, paper & scissors",
        extras={"built-in": True, "category": "Fun"},
    )
    async def rps(ctx):
        await ctx.nighty_send(
            title="Rock, paper & scissors",
            content=str(random.choice(["Rock", "Paper", "Scissors"])),
        )
    @bot.command(
        name="dice",
        description="Roll a dice",
        extras={"built-in": True, "category": "Fun"},
    )
    async def dice(ctx):
        await ctx.nighty_send(title="Dice", content=str(random.randint(1, 12)))
    @bot.command(
        name="randomnumber",
        usage="[min] [max]",
        description="Random number",
        extras={"built-in": True, "category": "Fun"},
    )
    async def randomnumber(ctx, min: int = 0, max: int = 100):
        await ctx.nighty_send(
            title="Random number", content=str(random.randint(min, max))
        )
    @bot.command(
        name="deathdate",
        usage="<user>",
        description="Predicted death date",
        extras={"built-in": True, "category": "Fun"},
    )
    async def deathdate(ctx, user: discord.User):
        start = datetime(datetime.now().year, 1, 1, 00, 00, 00)
        end = start + timedelta(days=365 * (2077 - datetime.now().year + 1))
        rd = start + (end - start) * random.random()
        await ctx.nighty_send(
            title="Death date", content=f"{user}'s death: {rd.day}/{rd.month}/{rd.year}"
        )
    @bot.command(
        name="adminservers",
        description="Check permissions on your servers",
        extras={"built-in": True, "category": "Tools"},
    )
    async def adminservers(ctx):
        permissions_map = {
            "Admin": ("administrator", []),
            "Manage server": ("manage_guild", []),
            "Ban": ("ban_members", []),
            "Kick": ("kick_members", []),
            "Mention everyone": ("mention_everyone", []),
            "Manage messages": ("manage_messages", []),
        }
        for guild in bot.guilds:
            for perm_name, (perm, servers) in permissions_map.items():
                if getattr(guild.me.guild_permissions, perm):
                    servers.append(discord.utils.escape_markdown(guild.name))
        def format_message(title, servers):
            return f"{title} ({len(servers)}): {', '.join(servers)}"
        await ctx.nighty_send(
            title="Admin servers",
            content="\n> ".join(
                format_message(title, servers)
                for title, (_, servers) in permissions_map.items()
            ),
        )
    @bot.command(
        name="admingroups",
        description="Group channels you are owner of",
        extras={"built-in": True, "category": "Tools"},
    )
    async def admingroups(ctx):
        message = ""
        recips = ""
        for channel in bot.private_channels:
            if isinstance(channel, discord.GroupChannel):
                if bot.user.id == channel.owner.id:
                    for recip in channel.recipients:
                        recips += f"{recip}, "
                    message += f"Name: {channel.name}\n> ID: {channel.id}\n> Created at: {channel.created_at}\n> Recipients: {recips[:-1]}\n> \n> "
        await ctx.nighty_send(title="Groups you are owner of", content=message)
    @bot.command(
        name="channels",
        usage="[serverid]",
        description="View server channels",
        extras={"built-in": True, "category": "Tools"},
    )
    async def channels(ctx, serverid: int = None):
        server = ctx.guild
        if serverid:
            server = bot.get_guild(serverid)
        voice = ""
        text = ""
        categories = ""
        for channel in server.voice_channels:
            voice += f"\U0001f508 {channel}\n> "
        for channel in server.categories:
            categories += f"\U0001f4da {channel}\n> "
        for channel in server.text_channels:
            text += f"\U0001f4dd {channel}\n> "
        await ctx.nighty_send(
            title=server.name,
            content=f"Categories\n> {categories}\n> Text channels\n> {text}\n> Voice channels\n> {voice}",
        )
    @bot.command(
        name="roles",
        usage="[serverid]",
        description="View server roles",
        extras={"built-in": True, "category": "Tools"},
    )
    async def roles(ctx, serverid: int = None):
        server = bot.get_guild(serverid) or ctx.guild
        await ctx.nighty_send(
            title=server.name,
            content=f'Roles:\n> {", ".join([role.name for role in server.roles])}',
        )
    @bot.command(
        name="roleperms",
        usage="<role>",
        description="View role permissions",
        extras={"built-in": True, "category": "Tools"},
    )
    async def roleperms(ctx, role: discord.Role):
        msg = ""
        for perm in role.permissions:
            if "False" not in str(perm):
                permission = re.search("('(.*)', True)", f"{perm}")
                permission = permission.group(1)
                permission = re.search("'(.*)', True", f"{permission}")
                permission = permission.group(1)
                msg += f"\n> {permission}"
        await ctx.nighty_send(
            title="Role permissions", content=f"Role: {role.name} ({role.id}){msg}"
        )
    @bot.command(
        name="channelinfo",
        usage="<channel>",
        description="Channel information",
        help="This only works for server channels, not for private channels",
        extras={"built-in": True, "category": "Tools"},
    )
    async def channelinfo(ctx, channel: discord.abc.GuildChannel):
        await ctx.nighty_send(
            title="Channel info",
            content=f"{channel.name}\n> ID: {channel.id}\n> Server: {channel.guild}\n> Type: {channel.type}\n> NSFW: {channel.is_nsfw()}\n> Position: {channel.position}\n> Created at: {channel.created_at}\n> Category: {channel.category}\n> Synced perms: {channel.permissions_synced}",
        )
    @bot.command(
        name="roleinfo",
        usage="<role>",
        description="Role information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def roleinfo(ctx, role: discord.Role):
        created_on = "{} ({} days ago)".format(
            role.created_at.strftime("%d %b %Y %H:%M"),
            (ctx.message.created_at - role.created_at).days,
        )
        await ctx.nighty_send(
            title=f"Role info: {role.name}",
            content=f"@{role.name}\n> Members: {len(role.members)}\n> Server: {role.guild}\n> Color: {role.color}\n> Creation: {created_on}\n> Admin: {role.permissions.administrator}",
        )
    @bot.command(
        name="serverinfo",
        usage="[serverid]",
        description="Server information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def serverinfo(ctx, serverid: int = None):
        server = bot.get_guild(serverid) or ctx.guild
        if server.mfa_level == 1:
            mfalvl = "2FA required for administrative members"
        else:
            mfalvl = "2FA not required"
        await ctx.nighty_send(
            title="Server information",
            content=f"{server.name}\n> ID: {server.id}\n> Owner: {server.owner}\n> Owner ID: {server.owner_id}\n> Member count: {server.member_count}\n> Roles: {len(server.roles)}\n> Total boosts: {str(server.premium_subscription_count)}\n> Boost level: {str(server.premium_tier)}\n> Text channels: {len(server.text_channels)}\n> Voice channels: {len(server.voice_channels)}\n> Categories: {len(server.categories)}\n> Verification level: {str(server.verification_level)}\n> MFA: {mfalvl}",
        )
    @bot.command(
        name="memberinfo",
        usage="<member>",
        description="Member information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def memberinfo(ctx, member: discord.Member):
        rolenames = (
            ", ".join(
                [
                    r.name
                    for r in sorted(member.roles, key=lambda c: c.position)
                    if r.name != "@everyone"
                ]
            )
            or "None"
        )
        voice_state = None if not member.voice else member.voice.channel
        await ctx.nighty_send(
            title="Member information",
            content=f"Member: {member.name}\n> Status: {member.status}\n> Avatar url: {member.avatar.url}\n> Roles: {rolenames}\n> Voice state: {voice_state}",
        )
    @bot.command(
        name="userinfo",
        usage="<userid>",
        description="User information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def userinfo(ctx, user_id: int):
        user = await bot.fetch_user(user_id)
        await ctx.nighty_send(
            title="User information",
            content=f"User: {user.name}\n> ID: {user.id}\n> Avatar url: {user.avatar.url}\n> Banner: {user.banner.url}\n> Created at: {user.created_at}\n> Is friend: {user.is_friend()}",
        )
    @bot.command(
        name="tokeninfo",
        usage="<token>",
        description="Token information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def tokeninfo(ctx, token: str):
        r = requests.get(
            "https://discord.com/api/v10/users/@me",
            headers={
                "Authorization": token,
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
            },
        )
        if r.status_code == 200:
            data = r.json()
            await ctx.nighty_send(
                title="Token information",
                content=f"User: {data['username']}\n> ID: {data['id']}\n> Avatar: https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}\n> Phone: {data['phone']}\n> Email: {data['email']}\n> MFA: {data['mfa_enabled']}\n> Locale: {data['locale']}\n> Verified: {data['verified']}",
            )
        elif r.status_code == 401:
            await ctx.nighty_send(title="Token information", content=f"Invalid token")
        else:
            await ctx.nighty_send(title="Token information", content=f"Unknown error")
    @bot.command(
        name="inviteinfo",
        usage="<user>",
        description="Invite information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def inviteinfo(ctx, invite: discord.Invite):
        max_age = invite.max_age
        revoked = invite.revoked
        created_at = invite.created_at
        temporary = invite.temporary
        uses = invite.uses
        maxuses = invite.max_uses
        attributes = [
            "max_age",
            "revoked",
            "created_at",
            "temporary",
            "uses",
            "max_uses",
        ]
        values = {
            attr: getattr(invite, attr, "Missing permission") for attr in attributes
        }
        max_age = values["max_age"]
        revoked = values["revoked"]
        created_at = values["created_at"]
        temporary = values["temporary"]
        uses = values["uses"]
        maxuses = values["max_uses"]
        await ctx.nighty_send(
            title="Invite information",
            content=f"{invite}\n> ID: {invite.id}\n> Inviter: {invite.inviter}\n> Server: {invite.guild.name}\n> Channel: {invite.channel}\n> Code: {invite.code}\n> Created at: {created_at}\n> Max age: {max_age}\n> Max uses: {maxuses}\n> Uses: {uses}\n> Revoked: {revoked}\n> Temporary: {temporary}",
        )
    @bot.command(
        name="emoteinfo",
        usage="<emoji>",
        description="Emoji information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def emoteinfo(ctx, emoji: discord.Emoji):
        await ctx.nighty_send(
            title="Emoji information",
            content=f"{emoji.name}\n> ID: {emoji.id}\n> Server: {emoji.guild}\n> Animated: {emoji.animated}\n> Managed: {emoji.managed}\n> Available: {emoji.available}\n> Added by {emoji.user}\n> Created at: {emoji.created_at}\n> URL: {emoji.url}",
        )
    @bot.command(
        name="webhookinfo",
        usage="<url>",
        description="Webhook information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def webhookinfo(ctx, url: str):
        r = requests.get(url)
        if r.status_code == 200:
            r = r.json()
            await ctx.nighty_send(
                title="Webhook information",
                content=f"{r['name']}\n> ID: {r['id']}\n> Avatar: {r['avatar']}\n> Channel ID: {r['channel_id']}\n> Server ID: {r['guild_id']}\n> Token: {r['token']}",
            )
        else:
            await ctx.nighty_send(
                title="Webhook information", content="Invalid webhook"
            )
    @bot.command(
        name="stickerinfo",
        usage='<"name">',
        description="Sticker information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def stickerinfo(ctx, name):
        sticker = findSticker(name)
        await ctx.nighty_send(
            title="Sticker information",
            content=f"{sticker.name}\n> Description: {sticker.description}\n> Emoji: {sticker.emoji}\n> ID: {sticker.id}\n> Server: {sticker.guild}\n> Available: {sticker.available}\n> Added by {sticker.user}\n> Created at: {sticker.created_at}\n> URL: {sticker.url}",
        )
    @bot.command(
        name="mutualinfo",
        usage="<user>",
        description="Mutual information",
        extras={"built-in": True, "category": "Tools"},
    )
    async def mutualinfo(ctx, user: discord.User):
        profile = await user.profile()
        await ctx.nighty_send(
            title="Mutual information",
            content=f"User: {user}\n> Servers: {profile.mutual_guilds}\n> Friends: {profile.mutual_friends}",
        )
    @bot.command(
        name="snipe",
        usage="[amount]",
        description="Show last deleted message(s) in the chat",
        extras={"built-in": True, "category": "Tools"},
    )
    async def snipe(ctx, amount=1):
        counter = 0
        if bot.config.get("snipe"):
            if len(bot.config["snipe"]) > 0:
                for message in bot.config["snipe"]:
                    if message.channel.id == ctx.channel.id:
                        await ctx.nighty_send(
                            title="Sniped message",
                            content=f"By: {message.author}\n> Sent at: {message.created_at.strftime('%d %b %Y %H:%M')}\n> Content: {message.clean_content}",
                        )
                        counter += 1
                        if counter >= amount:
                            break
            else:
                await ctx.nighty_send(title="Snipe", content="Nothing found in cache")
    @bot.command(
        name="weather",
        usage='<"city">',
        description="Current weather",
        extras={"built-in": True, "category": "Tools"},
    )
    async def weather(ctx, city):
        api_address = "http://api.openweathermap.org/data/2.5/weather?appid=3e6826fb716810018759216195531995&q="
        url = api_address + city
        data = requests.get(url).json()
        if data["cod"] == "404":
            await ctx.nighty_send(title="Weather", content=data["message"])
        else:
            temperature = round(float(data["main"]["temp"]) - 273.15, 2)
            ftemperature = (temperature * 9 / 5) + 32
            feels_like = round(float(data["main"]["feels_like"]) - 273.15, 2)
            ffeels_like = (feels_like * 9 / 5) + 32
            humidity = data["main"]["humidity"]
            await ctx.nighty_send(
                title="Weather",
                content=f"City: {data['name']}\n> Country: {data['sys']['country']}\n> {data['weather'][0]['description']}\n> Temp: {temperature}°C/{ftemperature}°F\n> Feels like: {feels_like}°C/{ffeels_like}°F\n> Humidity: {humidity}%",
            )
    @bot.command(
        name="tinyurl",
        usage="<url>",
        description="URL shortener",
        extras={"built-in": True, "category": "Tools"},
    )
    async def tinyurl(ctx, url):
        r = requests.get(f"http://tinyurl.com/api-create.php?url={url}").text
        await ctx.nighty_send(
            title="URL shortener", content=f"URL: {url}\n> Shortened: {r}"
        )
    @bot.command(
        name="chatdump",
        usage="<amount> [channel_id]",
        description="Dump chat to .txt file",
        extras={"built-in": True, "category": "Tools"},
    )
    async def chatdump(ctx, amount: int, channel_id: int = None):
        channel = bot.get_channel(channel_id) or ctx.channel
        dumplist = []
        f = open(
            f"{getDataPath()}/dumps/{channel}.txt",
            "w+",
            encoding="UTF-8",
            errors="ignore",
        )
        total = amount
        print(f"Dumping {amount} messages to dumps/{channel}.txt")
        async for message in channel.history(limit=amount):
            attachments = [
                attachment.url
                for attachment in message.attachments
                if message.attachments
            ]
            try:
                if attachments:
                    try:
                        realatt = attachments[0]
                        dumplist.append(
                            f"({message.created_at}) {message.author}: {message.clean_content} ({realatt})\n"
                        )
                    except:
                        dumplist.append(
                            f"({message.created_at}) {message.author}: {message.clean_content} (Failed to dump attachment)\n"
                        )
                embeds = message.embeds
                if embeds:
                    for embed in embeds:
                        try:
                            e = str(embed.to_dict()).encode("utf-8")
                            dumplist.append(
                                f"({message.created_at}) {message.author}: {e}\n"
                            )
                        except:
                            pass
                if message.clean_content:
                    dumplist.append(
                        f"({message.created_at}) {message.author}: {message.clean_content}\n"
                    )
            except Exception as e:
                print(f"Dump failed: {e}", type_="ERROR")
                total = total - 1
        dumplist.reverse()
        for dump in dumplist:
            f.write(dump)
        print(
            f"Successfully dumped {total} messages to data/dumps/{channel}.txt",
            type_="SUCCESS",
        )
        f.close()
        f = Path(f"{getDataPath()}/dumps/{channel}.txt")
        await ctx.send(file=discord.File(f))
    @bot.command(
        name="checktoken",
        usage="<token>",
        description="Check Discord token",
        extras={"built-in": True, "category": "Tools"},
    )
    async def checktoken(ctx, token):
        r = requests.get(
            "https://discord.com/api/v10/users/@me",
            headers={
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
            },
        )
        if r.status_code == 200:
            return await ctx.nighty_send(title="Check token", content="Token is valid")
        else:
            await ctx.nighty_send(title="Check token", content="Invalid token")
    @bot.command(
        name="urban",
        usage='<"search">',
        description="Urban dictionary lookup",
        extras={"built-in": True, "category": "Tools"},
    )
    async def urban(ctx, search):
        search_terms = search_terms.split(" ")
        try:
            if len(search_terms) > 1:
                pos = int(search_terms[-1]) - 1
                search_terms = search_terms[:-1]
            else:
                pos = 0
            if pos not in range(0, 11):
                pos = 0
        except ValueError:
            pos = 0
        search_terms = "+".join(search_terms)
        try:
            r = requests.get(
                f"http://api.urbandictionary.com/v0/define?term={search_terms}"
            )
            result = r.json()
            if result["list"]:
                await ctx.nighty_send(
                    title="Urban dictionary",
                    content=f"Definition
                )
            else:
                await ctx.nighty_send(
                    title="Urban dictionary",
                    content="Your search terms gave no results",
                )
        except IndexError:
            await ctx.nighty_send(
                title="Urban dictionary",
                content="There is no definition
            )
        except:
            await ctx.nighty_send(title="Urban dictionary", content="Unknown error.")
    @bot.command(
        name="google",
        usage='<"search">',
        description="Google search",
        extras={"built-in": True, "category": "Tools"},
    )
    async def google(ctx, search: str):
        await ctx.nighty_send(
            title=f"Google search",
            content=f"https://www.google.com/search?q={urllib.parse.quote(search)}",
        )
    @bot.command(
        name="youtube",
        usage='<"search">',
        description="YouTube search",
        extras={"built-in": True, "category": "Tools"},
    )
    async def youtube(ctx, search):
        ytb_search = SearchVideos(search, offset=1, mode="json", max_results=1)
        result = json.loads(ytb_search.result())
        await ctx.nighty_send(
            title="YouTube search",
            content=f"Search: {search}\n> Results:\n> Title: {result['search_result'][0]['title']}\n> Channel: {result['search_result'][0]['channel']}\n> URL: {result['search_result'][0]['link']}\n> Duration: {result['search_result'][0]['duration']}\n> Views: {result['search_result'][0]['views']}",
        )
    @bot.command(
        name="songlookup",
        usage='<"search">',
        description="Song lookup",
        extras={"built-in": True, "category": "Tools"},
    )
    async def songlookup(ctx, search):
        r = requests.get(f"https://some-random-api.com/lyrics?title={search}").json()
        await ctx.nighty_send(
            title="Song lookup",
            content=f"> Title: {r['title']}\n> Author: {r['author']}",
        )
    @bot.command(
        name="revavatar",
        usage="<user>",
        description="Reverse user avatar",
        extras={"built-in": True, "category": "Tools"},
    )
    async def revavatar(ctx, user: discord.User):
        await ctx.send(
            f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote(user.avatar.url)}"
        )
    @bot.command(
        name="nitrogen",
        usage="[amount]",
        description="Generate fake nitro codes",
        extras={"built-in": True, "category": "Tools"},
    )
    async def nitrogen(ctx, amount: int = 1):
        nitro = "https://discord.gift/"
        for i in range(amount):
            code = "".join(random.choices(string.ascii_letters + string.digits, k=16))
            await ctx.send(nitro + code)
            await asyncio.sleep(1)
    @bot.command(
        name="tokengen",
        description="Generate fake discord token",
        extras={"built-in": True, "category": "Tools"},
    )
    async def tokengen(ctx):
        r = requests.get(f"https://some-random-api.com/bottoken").json()
        await ctx.nighty_send(title="Fake discord token", content=r["token"])
    @bot.command(
        name="passgen",
        usage="[length]",
        description="Generate random password",
        extras={"built-in": True, "category": "Tools"},
    )
    async def passgen(ctx, length: int = 14):
        code = "".join(random.choices(string.ascii_letters + string.digits, k=length))
        await ctx.nighty_send(title="Generated password", content=code)
    @bot.command(
        name="usergen",
        description="Generate random user",
        extras={"built-in": True, "category": "Tools"},
    )
    async def usergen(ctx):
        user = RandomUser()
        await ctx.nighty_send(
            title="Random user",
            content=f"Name: {user.get_full_name()}\n> Gender: {user.get_gender()}\n> Age: {user.get_age()}\n> Email: {user.get_email()}\n> Phone: {user.get_phone()}\n> Street: {user.get_street()}\n> City: {user.get_city()}\n> State: {user.get_state()}\n> ZIP: {user.get_zipcode()}",
        )
    @bot.command(
        name="nickscan",
        description="Show servers you have a nickname in",
        extras={"built-in": True, "category": "Tools"},
    )
    async def nickscan(ctx):
        message = "\n"
        for guild in bot.guilds:
            if guild.me.nick != None:
                message += f"\n> {guild.name}: {guild.me.nick}"
        await ctx.nighty_send(title="Servers you have a nickname in", content=message)
    @bot.command(
        name="emojidump",
        usage="<serverid>",
        description="Download emojis from server",
        extras={"built-in": True, "category": "Tools"},
    )
    async def emojidump(ctx, server_id: int):
        guild = bot.get_guild(server_id)
        emojiNum = len(guild.emojis)
        if emojiNum > 0:
            print(
                f"Dumping emojis from {guild.name}...",
                discordChannel=f"Amount: {emojiNum}",
            )
            folderName = f"{getDataPath()}/dumps/emojis/" + guild.name.translate(
                {ord(c): None for c in '/<>:"\\|?*'}
            )
            if not os.path.exists(folderName):
                os.makedirs(folderName)
            for emoji in guild.emojis:
                if emoji.animated == True:
                    fileName = folderName + "/" + emoji.name + ".gif"
                else:
                    fileName = folderName + "/" + emoji.name + ".png"
                if not os.path.exists(fileName):
                    with open(fileName, "wb") as outFile:
                        req = urllib.request.Request(
                            emoji.url, headers={"User-Agent": "Mozilla/5.0"}
                        )
                        data = urllib.request.urlopen(req).read()
                        outFile.write(data)
            print(f"Dumped {emojiNum} emojis: {folderName}", discordChannel=guild.name)
        else:
            return await ctx.nighty_send(
                title="Emoji dump", content="Server has no emojis"
            )
    @bot.command(
        name="addemojis",
        usage='<"folder">',
        description="Add emojis from folder",
        extras={"built-in": True, "category": "Tools"},
    )
    async def addemojis(ctx, folder=None):
        if folder is not None:
            if os.path.isdir(f"{getDataPath()}/dumps/emojis/{folder}"):
                await ctx.nighty_send(
                    title="Add emojis", content=f"Adding emojis from {folder}"
                )
                for file in os.listdir(f"{getDataPath()}/dumps/emojis/{folder}"):
                    if (
                        file.endswith(".png")
                        or file.endswith(".gif")
                        or file.endswith(".jpg")
                    ):
                        with open(
                            f"{getDataPath()}/dumps/emojis/{folder}/{file}", "rb"
                        ) as emote:
                            for ext in [".png", ".gif", ".jpg"]:
                                file = file.replace(ext, "")
                            await ctx.guild.create_custom_emoji(
                                name=f"{file}", image=emote.read()
                            )
                            print(f"Added emoji: {file}", discordChannel=ctx.guild.name)
                await ctx.nighty_send(
                    title="Add emojis",
                    content=f"Successfully added emojis from {folder}",
                )
        else:
            folders = listdirs(f"{getDataPath()}/dumps/emojis")
            output = ""
            for foldr in folders:
                output += f"> {bot.command_prefix}addemojis {foldr}\n"
            await ctx.nighty_send(title="Add emojis", content=output)
    @bot.command(
        name="crypto",
        usage="<currency_code>",
        description="Crypto price lookup",
        extras={"built-in": True, "category": "Tools"},
    )
    async def crypto(ctx, currency_code):
        currency = currency_code.upper()
        try:
            data = requests.get(
                f"https://min-api.cryptocompare.com/data/price?fsym={currency}&tsyms=USD,EUR,CAD,GBP,CHF,NZD,AUD,JPY,BRL"
            ).json()
            await ctx.nighty_send(
                title=f"Crypto lookup ({currency})",
                content=f"USD: {data['USD']}\n> EUR: {data['EUR']}\n> GBP: {data['GBP']}\n> CAD: {data['CAD']}\n> CHF: {data['CHF']}\n> NZD: {data['NZD']}\n> AUD: {data['AUD']}\n> JPY: {data['JPY']}\n> BRL: {data['BRL']}",
            )
        except Exception as e:
            return await ctx.nighty_send(
                title="Crypto lookup", content=f"Lookup failed: {e}."
            )
    @bot.command(
        name="mcserver",
        usage="<address>",
        description="Minecraft server lookup",
        extras={"built-in": True, "category": "Tools"},
    )
    async def mcserver(ctx, address):
        r = requests.get(f"https://api.mcsrvstat.us/2/{address}")
        if r.status_code == 200:
            res = r.json()
            if res.get("online"):
                await ctx.nighty_send(
                    title="Minecraft server lookup",
                    content=f'{res["hostname"]}\n> {res["ip"]}:{res["port"]}\n> Players online: {res["players"]["online"]}\n> Max players: {res["players"]["max"]}',
                )
            else:
                await ctx.nighty_send(
                    title="Minecraft server lookup",
                    content=f'Status: offline\n> {res.get("hostname")}',
                )
        else:
            await ctx.nighty_send(
                title="Minecraft server lookup", content="Server not found."
            )
    @bot.command(
        name="createtemplate",
        usage='<"name"> ["description"]',
        description="Create server template",
        extras={"built-in": True, "category": "Tools"},
    )
    async def createtemplate(ctx, name, description=None):
        r = requests.post(
            f"https://discord.com/api/v10/guilds/{ctx.guild.id}/templates",
            headers=getBasicHeaders(),
            json={"name": name, "description": description},
        )
        if r.status_code == 200:
            res = r.json()
            await ctx.nighty_send(
                title="Create server template",
                content=f'https://discord.new/{res["code"]}',
            )
        elif r.status_code == 400:
            res = r.json()
            await ctx.nighty_send(
                title="Create server template", content=res["message"]
            )
    @bot.command(
        name="dumpattachments",
        usage="<amount> [channel_id]",
        description="Dump message attachments from chat",
        extras={"built-in": True, "category": "Tools"},
    )
    async def dumpattachments(ctx, amount, channel_id: int = None):
        channel = bot.get_channel(channel_id) or ctx.channel
        global cycling
        cycling = True
        file = open(
            f"{getDataPath()}/dumps/attachments/{channel.name}.txt",
            "w",
            errors="ignore",
        )
        counter = 0
        dumpcount = 0
        async for message in channel.history(limit=None):
            if cycling:
                if message.attachments:
                    for attachment in message.attachments:
                        attachment_url = f"({message.created_at}) {message.author}: {attachment.url}\n"
                        try:
                            file.write(attachment_url)
                            dumpcount += 1
                        except:
                            pass
                    counter += 1
                if counter >= amount:
                    file.close()
        print(
            f"Saved {dumpcount} attachments to data/dumps/attachments/{channel.name}.txt",
            url=f"file://{getDataPath}/dumps/attachments/",
            discordChannel=getChannelInfo(channel),
        )
    @bot.command(
        name="downloadattachments",
        usage="<amount> [channel_id]",
        description="Download attachments from chat",
        extras={"built-in": True, "category": "Tools"},
    )
    async def downloadattachments(ctx, amount, channel_id: int = None):
        channel = bot.get_channel(channel_id) or ctx.channel
        global cycling
        cycling = True
        counter = 0
        dumpcount = 0
        async for message in channel.history(limit=None):
            if cycling:
                if message.attachments:
                    for attachment in message.attachments:
                        key = "".join(random.choices(string.ascii_letters.upper(), k=6))
                        await attachment.save(
                            f"{getDataPath()}/dumps/attachments/{attachment.filename}_{channel.name}_{key}"
                        )
                        dumpcount += 1
                    counter += 1
                if counter >= amount:
                    break
        print(
            f"Saved {dumpcount} attachments to data/dumps/attachments/",
            url=f"file://{getDataPath}/dumps/attachments/",
            discordChannel=getChannelInfo(channel),
        )
    @bot.command(
        name="userbio",
        usage="<user>",
        description="User bio",
        extras={"built-in": True, "category": "Tools"},
    )
    async def userbio(ctx, user: discord.User):
        profile = await user.profile()
        await ctx.nighty_send(title="User bio", content=f"{profile.bio}")
    @bot.command(
        name="spam",
        usage='<delay> <amount> <"message">',
        description="Spam messages",
        help=f"Requires riskmode enabled, {bot.command_prefix}riskmode on",
        extras={"built-in": True, "category": "Tools"},
    )
    async def spam(ctx, delay: float, amount: int, message: str):
        config = getConfig()
        if config["riskmode"]:
            global cycling
            cycling = True
            for _i in range(amount):
                if cycling:
                    await ctx.send(message)
                    await asyncio.sleep(delay)
        else:
            await ctx.nighty_send(
                title="Error",
                content=f"Risk mode disabled, enable it with {bot.command_prefix}riskmode on",
            )
    @bot.command(
        name="nettools",
        description="Networking commands",
        extras={"built-in": True, "category": "Tools"},
    )
    async def nettools(ctx):
        await ctx.nighty_help(
            title="Nettools", commands=getCategoryCommands("Nettools")
        )
    @bot.command(
        name="ping",
        description="Discord latency",
        extras={"built-in": True, "category": "Nettools"},
    )
    async def ping(ctx):
        latency = bot.latency * 1000
        await ctx.nighty_send(title="Ping", content=f"Pong: {latency:.2f} ms")
    @bot.command(
        name="iplookup",
        usage="<address>",
        description="IP address lookup",
        extras={"built-in": True, "category": "Nettools"},
    )
    async def iplookup(ctx, ip):
        data = requests.get("https://json.geoiplookup.io/" + ip).json()
        if data.get("success"):
            return await ctx.nighty_send(
                title="IP lookup",
                content=f'{data.get("ip")}\n> ISP: {data.get("isp")}\n> Host name: {data.get("hostname")}\n> City: {data.get("city")}\n> Region: {data.get("region")}\n> Country: {data.get("country_name")}\n> Type: {data.get("connection_type")}\n> ASN: {data.get("asn")}',
            )
        await ctx.nighty_send(title="IP lookup", content="No results found.")
    @bot.command(
        name="domainresolve",
        usage="<ip>",
        description="Get domain from IP",
        extras={"built-in": True, "category": "Nettools"},
    )
    async def domainresolve(ctx, ip):
        data = requests.get("https://json.geoiplookup.io/" + ip).json()
        if data.get("success"):
            return await ctx.nighty_send(
                title="Domain resolve", content=f'Domain: {data.get("ip")}'
            )
        await ctx.nighty_send(title="Domain resolve", content="No results found.")
    @bot.command(
        name="autoslash",
        usage="<seconds> <app_id> <command>",
        description="Slash command executor",
        extras={"built-in": True, "category": "Utils"},
    )
    async def autoslash(ctx, seconds: int, app_id: int, cmd: str):
        global cycling
        app_commands = await ctx.application_commands()
        app_cmds = ""
        for appcmd in app_commands:
            if isinstance(appcmd, discord.SlashCommand):
                if appcmd.options:
                    skip_command = False
                    for option in appcmd.options:
                        if option.required:
                            skip_command = True
                            break
                    if skip_command:
                        continue
            app_cmds += f"> {appcmd.name} | {appcmd.application_id}\n"
        if cmd.startswith("/"):
            cmd = cmd.replace("/", "")
        command = [
            command
            for command in app_commands
            if command.name == cmd and command.application_id == app_id
        ]
        if command:
            command = command[0]
            await ctx.nighty_send(
                title="Auto slash",
                content=f"Running /{command.name} every {seconds} second(s)",
            )
            cycling = True
            while cycling:
                await command(ctx.channel)
                sendAppNotification(
                    f"Auto slash | /{command.name}",
                    discord_url=ctx.channel.jump_url,
                    channel=ctx.channel,
                )
                await asyncio.sleep(seconds)
        else:
            await ctx.nighty_send(
                title="Auto slash",
                content=f"Command: `{cmd}` not found, make sure you have permission to use this command.\n> Available app commands:\n{app_cmds}",
            )
    @bot.command(
        name="firstmessage",
        usage="[channel_id]",
        description="Get first message from chat",
        extras={"built-in": True, "category": "Utils"},
    )
    async def firstmessage(ctx, channel_id: int = None):
        channel = bot.get_channel(channel_id) or ctx.channel
        first_message = [
            message async for message in channel.history(limit=1, oldest_first=True)
        ][0]
        await ctx.nighty_send(
            title="First message", content=f"{first_message.jump_url}"
        )
    @bot.command(
        name="clean",
        usage="<amount> [channel_id]",
        description="Delete your messages",
        help="Due to a Discord limitation, you can not delete messages older than 14 days.",
        extras={"built-in": True, "category": "Utils"},
    )
    async def clean(ctx, amount: int, channel_id: int = None):
        amount = amount + 1
        channel = bot.get_channel(channel_id) or ctx.channel
        deleted = 0
        async for message in channel.history(limit=None):
            if message.author == bot.user:
                try:
                    await message.delete()
                    deleted += 1
                except:
                    pass
                if deleted >= amount:
                    break
                await asyncio.sleep(0.30)
    @bot.command(
        name="statusloop",
        description="Loop through statuses (online/dnd/idle)",
        extras={"built-in": True, "category": "Utils"},
    )
    async def statusloop(ctx):
        global cycling
        cycling = True
        while cycling:
            if cycling:
                await bot.change_presence(
                    status=discord.Status.online, afk=True, edit_settings=False
                )
                await asyncio.sleep(2.5)
            if cycling:
                await bot.change_presence(
                    status=discord.Status.idle, afk=True, edit_settings=False
                )
                await asyncio.sleep(2.5)
            if cycling:
                await bot.change_presence(
                    status=discord.Status.dnd, afk=True, edit_settings=False
                )
                await asyncio.sleep(2.5)
    @bot.command(
        name="cstatusloop",
        usage='<"text, text 2, ..">',
        description="Custom status loop",
        help=f'Loop through different texts. Use a comma to separate your statuses.\n> Example usage: {bot.command_prefix}cstatusloop "hello world, this is my custom status, another status here"',
        extras={"built-in": True, "category": "Utils"},
    )
    async def cstatusloop(ctx, text):
        texts = text.split(", ")
        await ctx.nighty_send(
            title="Custom status loop", content=f"Started looping: {texts}"
        )
        global cycling
        cycling = True
        for split in texts:
            if cycling:
                content = {"custom_status": {"text": split}}
                headers = {
                    "Authorization": getConfig()["token"],
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
                }
                requests.patch(
                    "https://discord.com/api/v10/users/@me/settings",
                    headers=headers,
                    json=content,
                )
                await asyncio.sleep(3.5)
    @bot.command(
        name="cstatusfile",
        usage='<delay> <"filename">',
        description="Custom status loop from file",
        help=f"Loop through different statuses through a file. Each new line will be your custom status.",
        extras={"built-in": True, "category": "Utils"},
    )
    async def cstatusfile(ctx, delay: float, filename: str):
        global cycling
        cycling = True
        for file in os.listdir(f"{getDataPath()}/customstatus"):
            if file.endswith(".txt"):
                with open(
                    f"{getDataPath()}/customstatus/{file}", encoding="utf-8"
                ) as f:
                    file = os.path.splitext(file)[0]
                    if fnmatch(file, f"{filename}"):
                        try:
                            anims = f.readlines()
                        except:
                            print(f"Wrong syntax on .txt file.", type_="ERROR")
                        for x in anims:
                            if cycling:
                                try:
                                    content = {"custom_status": {"text": x}}
                                    headers = {
                                        "Authorization": getConfig()["token"],
                                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
                                    }
                                    requests.patch(
                                        "https://discord.com/api/v10/users/@me/settings",
                                        headers=headers,
                                        json=content,
                                    )
                                    await asyncio.sleep(delay)
                                except:
                                    print(
                                        f"Unknown error, check if your syntax is correct.",
                                        type_="ERROR",
                                    )
    @bot.command(
        name="rpctitle",
        usage='<"text">',
        description="Title text",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpctitle(ctx, text):
        editRPCProfile(getActiveRPCProfile(), title=text)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Title: {text}")
    @bot.command(
        name="rpctype",
        usage="<activity>",
        description="Activity type",
        help="Activity type can be: [playing, watching, listening, competing, streaming, spotify]",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpctype(ctx, activity):
        editRPCProfile(getActiveRPCProfile(), activity_type=activity)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Type: {activity}")
    @bot.command(
        name="rpcdetails",
        usage='<"text">',
        description="Details text",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcdetails(ctx, text):
        editRPCProfile(getActiveRPCProfile(), details=text)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Details: {text}")
    @bot.command(
        name="rpcstate",
        usage='<"text">',
        description="State text",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcstate(ctx, text):
        editRPCProfile(getActiveRPCProfile(), state=text)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"State: {text}")
    @bot.command(
        name="rpcplatform",
        usage="<desktop/ps4/ps5/xbox/samsung>",
        description="Presence platform",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcplatform(ctx, platform):
        editRPCProfile(getActiveRPCProfile(), platform=platform)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Platform: {platform}")
    @bot.command(
        name="rpcdelay",
        usage="<seconds>",
        description="RPC Update delay",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcdelay(ctx, seconds: int):
        editRPCProfile(getActiveRPCProfile(), delay=seconds)
        await ctx.nighty_send(
            title="Rich Presence", content=f"Update delay: {seconds} seconds"
        )
    @bot.command(
        name="rpclargeimage",
        usage="<url>",
        description="Large image url",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpclargeimage(ctx, url):
        editRPCProfile(getActiveRPCProfile(), large_image=url)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Large image: {url}")
    @bot.command(
        name="rpclargetext",
        usage='<"text">',
        description="Large image text",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpclargetext(ctx, text):
        editRPCProfile(getActiveRPCProfile(), large_text=text)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(
            title="Rich Presence", content=f"Large image text: {text}"
        )
    @bot.command(
        name="rpcsmallimage",
        usage="<url>",
        description="Small image url",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcsmallimage(ctx, url):
        editRPCProfile(getActiveRPCProfile(), small_image=url)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Small image: {url}")
    @bot.command(
        name="rpcsmalltext",
        usage='<"text">',
        description="Small image text",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcsmalltext(ctx, text):
        editRPCProfile(getActiveRPCProfile(), small_text=text)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(
            title="Rich Presence", content=f"Small image text: {text}"
        )
    @bot.command(
        name="rpcbuttontext",
        usage='<"text">',
        description="Button text",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcbuttontext(ctx, text):
        editRPCProfile(getActiveRPCProfile(), button_text=text)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Button text: {text}")
    @bot.command(
        name="rpcbuttonurl",
        usage="<url>",
        description="Button url",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcbuttonurl(ctx, url):
        editRPCProfile(getActiveRPCProfile(), button_url=url)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Button url: {url}")
    @bot.command(
        name="rpcbutton2text",
        usage='<"text">',
        description="Button 2 text",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcbutton2text(ctx, text):
        editRPCProfile(getActiveRPCProfile(), button2_text=text)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Button 2 text: {text}")
    @bot.command(
        name="rpcbutton2url",
        usage="<url>",
        description="Button 2 url",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcbutton2url(ctx, url):
        editRPCProfile(getActiveRPCProfile(), button2_url=url)
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Button 2 url: {url}")
    @bot.command(
        name="rpctimer",
        usage="<on/off>",
        description="Toggle timer",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpctimer(ctx, toggle):
        toggle = toggle.lower()
        if toggle == "on" or toggle == "off":
            if toggle == "on":
                editRPCProfile(getActiveRPCProfile(), timer=True)
            elif toggle == "off":
                editRPCProfile(getActiveRPCProfile(), timer=False)
            await updateRPC(getRPCProfileData(getActiveRPCProfile()))
            await ctx.nighty_send(title="Rich Presence", content=f"Timer: {toggle}")
    @bot.command(
        name="rpcstart",
        usage="<hours> <minutes> <seconds>",
        description="Start timer",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcstart(ctx, hours: int, minutes: int, seconds: int):
        editRPCProfile(getActiveRPCProfile(), start=[hours, minutes, seconds])
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(
            title="Rich Presence",
            content=f"Start time: {hours} hours, {minutes} minutes and {seconds} seconds",
        )
    @bot.command(
        name="rpcend",
        usage="<hours> <minutes> <seconds>",
        description="End timer",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcend(ctx, hours: int, minutes: int, seconds: int):
        editRPCProfile(getActiveRPCProfile(), end=[hours, minutes, seconds])
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(
            title="Rich Presence",
            content=f"End time: {hours} hours, {minutes} minutes and {seconds} seconds",
        )
    @bot.command(
        name="rpcparty",
        usage="<min> <max>",
        description="Party",
        extras={"built-in": True, "category": "RPC"},
    )
    async def rpcparty(ctx, min: int, max: int):
        editRPCProfile(getActiveRPCProfile(), party=[min, max])
        await updateRPC(getRPCProfileData(getActiveRPCProfile()))
        await ctx.nighty_send(title="Rich Presence", content=f"Party: {min} on {max}")
    @bot.command(
        name="sysinfo",
        description="Basic system information",
        extras={"built-in": True, "category": "Utils"},
    )
    async def sysinfo(ctx):
        uname = uName()
        svmem = virtual_memory()
        total_ram = getSize(svmem.total)
        gpus = getGPUs()
        gpu_name = gpus[0].name if gpus else "No GPU found"
        partitions = disk_partitions()
        total_storage = getSize(
            sum(disk_usage(partition.mountpoint).total for partition in partitions)
        )
        await ctx.nighty_send(
            title="System info",
            content=f"CPU {uname.processor}\n> GPU: {gpu_name}\n> Total RAM: {total_ram}\n> Total storage: {total_storage}",
        )
    @bot.command(
        name="leaveallgroups",
        description="Leave all group chats",
        extras={"built-in": True, "category": "Utils"},
    )
    async def leaveallgroups(ctx):
        for channel in bot.private_channels:
            if isinstance(channel, discord.GroupChannel):
                await channel.leave()
        print("Left all group chats")
    @bot.command(
        name="savepfp",
        description="Save user avatar",
        extras={"built-in": True, "category": "Utils"},
    )
    async def savepfp(ctx, user: discord.User):
        if user.avatar.is_animated():
            filename = f"{getDataPath()}/downloads/{user.name}.gif"
        else:
            filename = f"{getDataPath()}/downloads/{user.name}.png"
        await user.avatar.save(filename)
        await ctx.nighty_send(
            title="Save pfp", content=f"Saved {user.name}'s avatar to data/downloads/"
        )
    @bot.command(
        name="deletewebhook",
        usage="<url>",
        description="Delete webhook",
        extras={"built-in": True, "category": "Utils"},
    )
    async def deletewebhook(ctx, url):
        requests.delete(url)
        await ctx.nighty_send(title="Delete webhook", content=f"Webhook deleted")
    @bot.command(
        name="calc",
        description="Open calculator",
        extras={"built-in": True, "category": "Utils"},
    )
    async def calc(ctx):
        Popen(["calc.exe"])
    @bot.command(
        name="hypesquad",
        usage="<house>",
        description="Hypesquad badge",
        extras={"built-in": True, "category": "Utils"},
    )
    async def hypesquad(ctx, house):
        house = house.lower()
        houses = {
            "bravery": discord.HypeSquadHouse.bravery,
            "brilliance": discord.HypeSquadHouse.brilliance,
            "balance": discord.HypeSquadHouse.balance,
        }
        if house in houses:
            await bot.user.edit(hypesquad=houses[house])
            await ctx.nighty_send(title="Hypesquad", content=f"New house: {house}")
        else:
            await ctx.nighty_send(
                title="Hypesquad",
                content="Available houses: bravery, brilliance & balance",
            )
    @bot.command(
        name="cloneserver",
        usage="<server_id>",
        description="Create a clone of the server",
        extras={"built-in": True, "category": "Utils"},
    )
    async def cloneserver(ctx, server_id: int):
        server = bot.get_guild(server_id)
        image = None
        if server.icon:
            try:
                image = await server.icon.read()
                image = discord.utils._bytes_to_base64_data(image)
            except:
                image = None
        r = server_creator().create(server.name, image)
        new_server = await bot.fetch_guild(int(r["id"]))
        print(f"Clone server | Creating channels...", discordChannel=new_server.name)
        await asyncio.sleep(2)
        for category in new_server.categories:
            for channel in category.channels:
                await channel.delete()
                await asyncio.sleep(1.5)
        for channel in new_server.channels:
            await channel.delete()
            await asyncio.sleep(1.5)
        for category in server.categories:
            x = await new_server.create_category(category.name)
            for channel in category.channels:
                if isinstance(channel, discord.TextChannel):
                    await x.create_text_channel(
                        channel.name,
                        topic=channel.topic,
                        nsfw=channel.is_nsfw(),
                        slowmode_delay=channel.slowmode_delay,
                        position=channel.position,
                        overwrites=channel.overwrites,
                    )
                elif isinstance(channel, discord.VoiceChannel):
                    await x.create_voice_channel(
                        channel.name,
                        position=channel.position,
                        overwrites=channel.overwrites,
                    )
                await asyncio.sleep(2)
        for channel in server.channels:
            if channel.category is None:
                if isinstance(channel, discord.TextChannel):
                    await new_server.create_text_channel(
                        channel.name,
                        topic=channel.topic,
                        nsfw=channel.is_nsfw(),
                        slowmode_delay=channel.slowmode_delay,
                        position=channel.position,
                        overwrites=channel.overwrites,
                    )
                elif isinstance(channel, discord.VoiceChannel):
                    await x.create_voice_channel(
                        channel.name,
                        position=channel.position,
                        overwrites=channel.overwrites,
                    )
                await asyncio.sleep(2)
        print(f"Clone server | Creating roles...", discordChannel=new_server.name)
        for role in server.roles[::-1]:
            if role.name != "@everyone":
                await new_server.create_role(
                    name=role.name,
                    permissions=role.permissions,
                    color=role.color,
                    hoist=role.hoist,
                    mentionable=role.mentionable,
                )
                await asyncio.sleep(2)
        print(f"Clone server | Setting up AFK channel", discordChannel=new_server.name)
        if server.afk_channel:
            try:
                new_afk_channel = discord.utils.get(
                    new_server.voice_channels, name=server.afk_channel.name
                )
                await new_server.edit(
                    afk_channel=new_afk_channel, afk_timeout=server.afk_timeout
                )
            except:
                pass
        print(f"Clone server | Cloning emojis", discordChannel=new_server.name)
        try:
            emojis = server.emojis
            if not emojis:
                pass
            else:
                for emoji in emojis:
                    if emoji.animated:
                        continue
                    try:
                        req = urllib.request.Request(
                            emoji.url, headers={"User-Agent": "Mozilla/5.0"}
                        )
                        data = urllib.request.urlopen(req).read()
                        await new_server.create_custom_emoji(
                            name=emoji.name, image=data
                        )
                    except:
                        pass
                    await asyncio.sleep(2)
        except:
            pass
    @bot.command(
        name="pastescript",
        usage='<url> <"name">',
        description="Paste script from raw url",
        extras={"built-in": True, "category": "Utils"},
    )
    async def pastescript(ctx, url, name):
        rawscript = requests.get(f"{url}").text
        with open(f"{getDataPath()}/scripts/{name}.py", "a") as f:
            f.write(rawscript)
        await ctx.nighty_send(
            title="Paste script", content=f"Saved script: data/scripts/{name}.py"
        )
    @bot.command(
        name="userhistory",
        usage="<user>",
        description="Get user's previous saved usernames",
        extras={"built-in": True, "category": "Utils"},
    )
    async def userhistory(ctx, user: discord.User):
        with open(f"{getDataPath()}/misc/user_history.json", encoding="utf-8") as file:
            logs = json.load(file)
        if logs.get("user_history"):
            for log in logs["user_history"]:
                if str(user.id) == str(log):
                    message = f"Previous logged username(s):\n"
                    usernames = logs["user_history"][log]["usernames"]
                    for name in usernames:
                        message += f"> {name}\n"
                    return await ctx.nighty_send(title="User history", content=message)
        await ctx.nighty_send(
            title="User history", content="No previous usernames found for this user."
        )
    @bot.command(
        name="getchannel",
        usage="[user]",
        description="Get DM channel id",
        extras={"built-in": True, "category": "Utils"},
    )
    async def getchannel(ctx, user: discord.User = None):
        channel = user.dm_channel or ctx.channel
        await ctx.nighty_send(title="DM channel id", content=str(channel.id))
    @bot.command(
        name="stealpfp",
        usage="<user>",
        description="Steal user avatar",
        extras={"built-in": True, "category": "Utils"},
    )
    async def stealpfp(ctx, user: discord.User):
        await bot.user.edit(avatar=await user.avatar.read())
        await ctx.nighty_send(title="Steal pfp", content=f"Stole {user}'s avatar.")
    @bot.command(
        name="backupfriends",
        description="Backup your friends",
        help="Save your friends to a file (data/backups/friends.json)",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def backupfriends(ctx):
        backupFriends(getFriends())
        await ctx.nighty_send(
            title="Backup friends", content=f"Saved friends (data/backups/friends.json)"
        )
    @bot.command(
        name="backupaccountinfo",
        description="Backup your account information",
        help="Save your account information to a file (data/backups/account-info.json.json)",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def backupaccountinfo(ctx):
        result = await accountBackup()
        await ctx.nighty_send(title="Backup account info", content=result)
    @bot.command(
        name="backupaccountsettings",
        description="Backup your account settings",
        help="Save your account settings to a file (data/backups/account-settings.json.json)",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def backupaccountsettings(ctx):
        result = await backupSettings()
        await ctx.nighty_send(title="Backup account settings", content=result)
    @bot.command(
        name="backupservers",
        description="Backup your servers",
        help="Save your friends to a file (data/backups/servers.json)",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def backupservers(ctx):
        if await backupServers():
            await ctx.nighty_send(
                title="Backup servers",
                content=f"Saved servers (data/backups/servers.json)",
            )
    @bot.command(
        name="backupgifs",
        description="Backup your favorite GIFs",
        help="Save your favorite GIFS to a file (data/backups/gifs.json)",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def backupgifs(ctx):
        result = await backupGIFs()
        await ctx.nighty_send(title="Backup GIFs", content=result)
    @bot.command(
        name="restoregifs",
        description="Restore favorite GIFs from backup",
        help="Restore your favorite GIFs from saved backup (data/backups/gifs.json)",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def restoregifs(ctx):
        result = await restoreGIFs()
        await ctx.nighty_send(title="Restore GIFs", content=result)
    @bot.command(
        name="restorefriends",
        description="Restore friends from backup",
        help="Semi automatic friends restoring using a webview window.",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def restorefriends(ctx):
        await restoreFriends(getFriendsBackup())
    @bot.command(
        name="restoreservers",
        description="Restore servers from backup",
        help="Semi automatic server restoring.",
        extras={"built-in": True, "category": "Recovery"},
    )
    async def restoreservers(ctx):
        await restoreServers(getServersBackup())
    @bot.command(
        name="antispam",
        usage="<on/off>",
        description="Prevent users from spamming",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispam(ctx, toggle):
        toggle = toggle.lower()
        data = getProtectionConfig()
        if toggle == "on":
            data["anti_spam"]["state"] = True
        elif toggle == "off":
            data["anti_spam"]["state"] = False
        else:
            return
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"State: {toggle}")
    @bot.command(
        name="antispamlapse",
        usage="<seconds>",
        description="Amount of seconds before check",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamlapse(ctx, seconds: int):
        data = getProtectionConfig()
        data["anti_spam"]["lapse"] = seconds
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"Lapse: {seconds} seconds")
    @bot.command(
        name="antispamthreshold",
        usage="<amount>",
        description="Amount of messages within lapse",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamthreshold(ctx, amount: int):
        data = getProtectionConfig()
        data["anti_spam"]["threshold"] = amount
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Anti spam", content=f"Threshold: {amount} messages"
        )
    @bot.command(
        name="antispambots",
        usage="<on/off>",
        description="Check for bots",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispambots(ctx, toggle):
        toggle = toggle.lower()
        data = getProtectionConfig()
        if toggle == "on":
            data["anti_spam"]["bots"] = True
        elif toggle == "off":
            data["anti_spam"]["bots"] = False
        else:
            return
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"Bots: {toggle}")
    @bot.command(
        name="antispamreply",
        usage='["message"]',
        description="Reply to flagged spammer",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamreply(ctx, message=None):
        data = getProtectionConfig()
        data["anti_spam"]["reply"]["message"] = message
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"Reply: {message}")
    @bot.command(
        name="antispamtimeout",
        usage="<on/off>",
        description="Timeout flagged spammer",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamtimeout(ctx, toggle):
        toggle = toggle.lower()
        data = getProtectionConfig()
        if toggle == "on":
            data["anti_spam"]["timeout"]["state"] = True
        elif toggle == "off":
            data["anti_spam"]["timeout"]["state"] = False
        else:
            return
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"Timeout: {toggle}")
    @bot.command(
        name="antispamtimeoutduration",
        usage="<minutes>",
        description="Timeout duration",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamtimeoutduration(ctx, minutes: int):
        data = getProtectionConfig()
        data["anti_spam"]["timeout"]["duration_minutes"] = minutes
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"Timeout: {minutes} minutes")
    @bot.command(
        name="antispamtimeoutreason",
        usage='["reason"]',
        description="Timeout reason",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamtimeoutreason(ctx, reason=None):
        data = getProtectionConfig()
        data["anti_spam"]["timeout"]["reason"] = reason
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"Timeout reason: {reason}")
    @bot.command(
        name="antispamnick",
        usage='["name"]',
        description="Set nickname for flagged spammers",
        help="Leave blank for disabling nickname changes",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamnick(ctx, name: str = None):
        data = getProtectionConfig()
        if name:
            data["anti_spam"]["nickname"]["state"] = True
            data["anti_spam"]["nickname"]["name"] = name
        else:
            data["anti_spam"]["nickname"]["state"] = False
        json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(title="Anti spam", content=f"Nickname: {name}")
    @bot.command(
        name="antispamservers",
        usage="[add/remove] [serverid]",
        description="Servers to have anti spam active on",
        help="Use the command without arguments to see current settings.",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamservers(ctx, method=None, *server_id: int):
        data = getProtectionConfig()
        if method:
            method = method.lower()
            if method == "add":
                for server in server_id:
                    if server not in data["anti_spam"]["servers"]:
                        data["anti_spam"]["servers"].append(server)
            elif method == "remove" or method == "delete":
                for server in server_id:
                    if server in data["anti_spam"]["servers"]:
                        data["anti_spam"]["servers"].remove(server)
            json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Anti spam", content=f'Servers: {data["anti_spam"]["servers"]}'
        )
    @bot.command(
        name="antispamwhitechannels",
        usage="[add/remove] [channel_id]",
        description="Whitelisted channels from anti spam",
        help="Use the command without arguments to see current settings.",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamwhitechannels(ctx, method=None, *channel_id: int):
        data = getProtectionConfig()
        if method:
            method = method.lower()
            if method == "add":
                for channel in channel_id:
                    if channel not in data["anti_spam"]["whitelist_channels"]:
                        data["anti_spam"]["whitelist_channels"].append(channel)
            elif method == "remove" or method == "delete":
                for channel in channel_id:
                    if channel in data["anti_spam"]["whitelist_channels"]:
                        data["anti_spam"]["whitelist_channels"].remove(channel)
            json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Anti spam",
            content=f'Whitelisted channels: {data["anti_spam"]["whitelist_channels"]}',
        )
    @bot.command(
        name="antispamwhiteroles",
        usage="[add/remove] [role_id]",
        description="Whitelisted roles from anti spam",
        help="Use the command without arguments to see current settings.",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamwhiteroles(ctx, method=None, *role_id: int):
        data = getProtectionConfig()
        if method:
            method = method.lower()
            if method == "add":
                for role in role_id:
                    if role not in data["anti_spam"]["whitelist_roles"]:
                        data["anti_spam"]["whitelist_roles"].append(role)
            elif method == "remove" or method == "delete":
                for role in role_id:
                    if role in data["anti_spam"]["whitelist_roles"]:
                        data["anti_spam"]["whitelist_roles"].remove(role)
            json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Anti spam",
            content=f'Whitelisted roles: {data["anti_spam"]["whitelist_roles"]}',
        )
    @bot.command(
        name="antispamwhiteusers",
        usage="[add/remove] [user_id]",
        description="Whitelisted users from anti spam",
        help="Use the command without arguments to see current settings.",
        extras={"built-in": True, "category": "Protection"},
    )
    async def antispamwhiteusers(ctx, method=None, *user_id: int):
        data = getProtectionConfig()
        if method:
            method = method.lower()
            if method == "add":
                for user in user_id:
                    if user not in data["anti_spam"]["whitelist_users"]:
                        data["anti_spam"]["whitelist_users"].append(user)
            elif method == "remove" or method == "delete":
                for user in user_id:
                    if user in data["anti_spam"]["whitelist_users"]:
                        data["anti_spam"]["whitelist_users"].remove(user)
            json.dump(data, open(f"{getDataPath()}/protection.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Anti spam",
            content=f'Whitelisted users: {data["anti_spam"]["whitelist_users"]}',
        )
    @bot.command(
        name="share",
        usage="[add/remove] [user/friends]",
        description="Share commands with users",
        help=f"For more advanced usage on what to share, use {bot.command_prefix}help sharecommand",
        extras={"built-in": True, "category": "Misc"},
    )
    async def share(ctx, method: str = None, *users: Union[discord.User, str]):
        config = getShareConfig()
        if method and users:
            method = method.lower()
            if method == "add":
                for user in users:
                    if isinstance(user, discord.User):
                        if user not in config["users"].get("users"):
                            config["users"]["users"].append(user.id)
                    elif isinstance(user, str):
                        if user == "friends":
                            config["users"]["friends"] = True
            elif method == "remove":
                for user in users:
                    if isinstance(user, discord.User):
                        if user in config["users"].get("users"):
                            config["users"]["users"].remove(user.id)
                    elif isinstance(user, str):
                        if user == "friends":
                            config["users"]["friends"] = False
            json.dump(config, open(f"{getDataPath()}/share.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Share",
            content=f'Friends: {config["users"]["friends"]}\n> Users: {config["users"]["users"]}',
        )
    @bot.command(
        name="sharecommand",
        aliases=["sharecommands"],
        usage="[add/remove] [command/all]",
        description="Choose what commands you are sharing",
        help=f"{chr(173)}\n> Example usage: {bot.command_prefix}sharecommand add Help",
        extras={"built-in": True, "category": "Misc"},
    )
    async def sharecommand(ctx, method: str = None, *commands: str):
        config = getShareConfig()
        if method and commands:
            method = method.lower()
            if method == "add":
                for cmdd in commands:
                    if cmdd == "all":
                        config["commands"]["all"] = True
                    elif bot.get_command(cmdd):
                        if cmdd not in config["commands"].get("commands"):
                            config["commands"]["commands"].append(cmdd)
            elif method == "remove":
                for cmdd in commands:
                    if cmdd == "all":
                        config["commands"]["all"] = False
                    else:
                        if cmdd in config["commands"].get("commands"):
                            config["commands"]["commands"].remove(cmdd)
            json.dump(config, open(f"{getDataPath()}/share.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Share commands",
            content=f'All: {config["commands"]["all"]}\n> Commands: {config["commands"]["commands"]}',
        )
    @bot.command(
        name="history",
        aliases=["commandhistory"],
        usage="[clear]",
        description="Command history",
        extras={"built-in": True, "category": "Misc"},
    )
    async def history(ctx, clear=None):
        if clear is not None:
            if clear.lower() == "clear":
                bot.config["command_history"] = []
                return await ctx.nighty_send(
                    title="Command history", content="History cleared."
                )
        else:
            message = ""
            cmd_history = bot.config.get("command_history")
            if cmd_history:
                cmd_history.reverse()
                for cmd in cmd_history:
                    message += f"\n> {cmd}"
            if message == "":
                message = "No commands used."
            await ctx.nighty_send(title="Command history", content=message)
    @bot.command(
        name="dmlogger",
        usage="<on/off/group>",
        description="Log edited & deleted messages from DM",
        extras={"built-in": True, "category": "Misc"},
    )
    async def dmlogger(ctx, toggle):
        toggle = toggle.lower()
        if toggle not in ["on", "off", "group"]:
            return
        config = getConfig()
        config["dmlogger"] = toggle
        json.dump(config, open(getConfigPath(), "w"), indent=2)
        await ctx.nighty_send(title="DM logger", content=f"State: {toggle}")
    @bot.command(
        name="riskmode",
        usage="<on/off>",
        description="Toggle risk mode",
        extras={"built-in": True, "category": "Misc"},
    )
    async def riskmode(ctx, toggle):
        toggle = toggle.lower()
        if toggle not in ["on", "off"]:
            return
        config = getConfig()
        config["riskmode"] = toggle == "on"
        json.dump(config, open(getConfigPath(), "w"), indent=2)
        await ctx.nighty_send(title="Risk mode", content=f"State: {toggle}")
    @bot.command(
        name="folder",
        description="Open Nighty folder",
        extras={"built-in": True, "category": "Misc"},
    )
    async def folder(ctx):
        os.startfile(getNightyPath())
    @bot.command(
        name="reloadscripts",
        description="Reload Nighty (scripts)",
        extras={"built-in": True, "category": "Misc"},
    )
    async def reloadscripts(ctx):
        global ui
        ui.update()
        await ctx.nighty_send(title="Reload scripts", content="Reloaded all scripts")
    @bot.command(
        name="restart",
        aliases=["reboot"],
        description="Restart Nighty",
        extras={"built-in": True, "category": "Misc"},
    )
    async def restart(ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        os.execv(sys.executable, ["python"] + sys.argv)
    @bot.command(
        name="shutdown",
        description="Shutdown Nighty",
        extras={"built-in": True, "category": "Misc"},
    )
    async def shutdown(ctx):
        os.kill(os.getpid(), SIGTERM)
    @bot.command(
        name="nitrosniper",
        usage="<on/off>",
        description="Toggle nitro sniper",
        extras={"built-in": True, "category": "Misc"},
    )
    async def nitrosniper(ctx, toggle):
        toggle = toggle.lower()
        if toggle not in ["on", "off"]:
            return
        config = getConfig()
        config["nitrosniper"] = toggle == "on"
        json.dump(config, open(getConfigPath(), "w"), indent=2)
        await ctx.nighty_send(title="Nitro sniper", content=f"State: {toggle}")
    @bot.command(
        name="gjoiner",
        usage="[on/off]",
        description="Giveaway joiner",
        extras={"built-in": True, "category": "Misc"},
    )
    async def gjoiner(ctx, toggle=None):
        if toggle is None:
            await ctx.nighty_help(
                title="Giveaway joiner", commands=getCategoryCommands("Giveaway joiner")
            )
        else:
            toggle = toggle.lower()
            if toggle not in ["on", "off"]:
                return
            config = getGiveawayJoinerConfig()
            config["giveawayjoiner"] = toggle == "on"
            json.dump(
                config, open(f"{getDataPath()}/giveawayjoiner.json", "w"), indent=2
            )
            await ctx.nighty_send(title="Giveaway joiner", content=f"State: {toggle}")
    @bot.command(
        name="gjoinerdelay",
        usage="<seconds>",
        description="Delay before joining giveaway",
        extras={"built-in": True, "category": "Giveaway joiner"},
    )
    async def gjoinerdelay(ctx, seconds: int):
        config = getGiveawayJoinerConfig()
        config["delay_in_seconds"] = seconds
        json.dump(config, open(f"{getDataPath()}/giveawayjoiner.json", "w"), indent=2)
        await ctx.nighty_send(
            title="Giveaway joiner", content=f"Delay: {seconds} seconds"
        )
    @bot.command(
        name="gjoinerblacklist",
        usage='[add/remove] ["text"]',
        description="Blacklist giveaways containing specific text",
        help="Use the command without arguments to see current settings.",
        extras={"built-in": True, "category": "Giveaway joiner"},
    )
    async def gjoinerblacklist(ctx, method=None, *text: str):
        config = getGiveawayJoinerConfig()
        if method:
            method = method.lower()
            if method == "add":
                for t in text:
                    if t not in config["blacklisted_words"]:
                        config["blacklisted_words"].append(t)
            elif method == "remove" or method == "delete":
                for t in text:
                    if t in config["blacklisted_words"]:
                        config["blacklisted_words"].remove(t)
            json.dump(
                config, open(f"{getDataPath()}/giveawayjoiner.json", "w"), indent=2
            )
        await ctx.nighty_send(
            title="Giveaway joiner",
            content=f'Blacklisted giveaways containing: {config["blacklisted_words"]}',
        )
    @bot.command(
        name="gjoinerblacklistserver",
        usage="[add/remove] [serverid]",
        description="Blacklist giveaways from servers",
        help="Use the command without arguments to see current settings.",
        extras={"built-in": True, "category": "Giveaway joiner"},
    )
    async def gjoinerblacklistserver(ctx, method=None, *server_id: int):
        config = getGiveawayJoinerConfig()
        if method:
            method = method.lower()
            if method == "add":
                for server in server_id:
                    if server not in config["blacklisted_serverids"]:
                        config["blacklisted_serverids"].append(server)
            elif method == "remove" or method == "delete":
                for server in server_id:
                    if server in config["blacklisted_serverids"]:
                        config["blacklisted_serverids"].remove(server)
            json.dump(
                config, open(f"{getDataPath()}/giveawayjoiner.json", "w"), indent=2
            )
        await ctx.nighty_send(
            title="Giveaway joiner",
            content=f'Blacklisted servers: {config["blacklisted_serverids"]}',
        )
    @bot.command(
        name="uptime",
        description="Uptime",
        extras={"built-in": True, "category": "Misc"},
    )
    async def uptime_(ctx):
        await ctx.nighty_send(title="Uptime", content=getUptime())
    @bot.command(
        name="createcommand",
        usage='<name> <"reply">',
        description="Create custom command",
        extras={"built-in": True, "category": "Misc"},
    )
    async def createcommand(ctx, name: str, reply: str):
        with open(f"{getDataPath()}/scripts/{name}.py", "w", encoding="utf-8") as file:
            file.write(f)
        await ctx.nighty_send(
            title="Create command", content=f"Command created: {name}\n> Reply: {reply}"
        )
    @bot.command(
        name="togglecommand",
        usage="<command> <on/off>",
        description="Toggle command",
        extras={"built-in": True, "category": "Misc"},
    )
    async def togglecommand(ctx, cmd: str, toggle: str):
        toggle = toggle.lower()
        command = bot.get_command(cmd)
        command.update(enabled=(toggle == "on"))
        await ctx.nighty_send(
            title="Toggle command", content=f"{command.name}: {toggle}"
        )
    @bot.command(
        name="commandalias",
        aliases=["commandaliases"],
        usage="[command] [add/remove] [alias]",
        description="Command aliases",
        help="Use the command without arguments to see your current aliases.",
        extras={"built-in": True, "category": "Misc"},
    )
    async def commandalias(
        ctx, command: str = None, method: str = None, alias: str = None
    ):
        if not command or not method or not alias:
            aliases = [cmd for cmd in bot.config["aliases"] if cmd is not None]
            return await ctx.nighty_help(
                title="Command aliases", commands=aliases or [ctx.command]
            )
        method = method.lower()
        if method == "add":
            await addCommandAlias(alias, command)
            await ctx.nighty_send(
                title="Command aliases", content=f"Added: {alias} for {command}"
            )
        elif method == "remove" or method == "delete":
            await removeCommandAlias(alias)
            await ctx.nighty_send(
                title="Command aliases", content=f"Removed: {alias} for {command}"
            )
    @bot.command(
        name="stop",
        description="Abort running commands",
        extras={"built-in": True, "category": "Misc"},
    )
    async def stop_(ctx):
        global cycling
        cycling = False
        await ctx.nighty_send(title="Stop", content="Stopped running commands.")
    @bot.command(
        name="credits",
        description="Credits & more",
        extras={"built-in": True, "category": "Misc"},
    )
    async def credits(ctx):
        await ctx.nighty_send(
            title="Credits & more",
            content=f"https://nighty.one\n> Version: {__version__}\n> Prefix: {bot.command_prefix}\n> Commands: {len(bot.commands)}\n> Uptime: {getUptime()}\n> MOTD: {bot.config.get('motd')}",
        )
    @bot.command(
        name="favorites",
        usage="[add/remove] [command]",
        description="Favorite commands",
        extras={"built-in": True, "category": "Misc"},
    )
    async def favorites(ctx, method=None, *commands):
        favs = getFavoriteCommands()
        if method:
            method = method.lower()
            if method == "add":
                for cmd in commands:
                    if cmd not in favs:
                        bot_command = bot.get_command(cmd)
                        if bot_command is None:
                            return
                        favs.append(cmd)
            elif method == "remove" or method == "delete":
                for cmd in commands:
                    if cmd in favs:
                        favs.remove(cmd)
            json.dump(favs, open(f"{getDataPath()}/favorites.json", "w"), indent=2)
        bot.config["favorites"] = favs
        await ctx.nighty_send(title="Favorite commands", content=f"{favs}")
    @bot.command(
        name="prefix",
        usage="<new_prefix>",
        description="Change prefix",
        extras={"built-in": True, "category": "Settings"},
    )
    async def prefix(ctx, new_prefix: str):
        new_prefix = new_prefix.replace(" ", "")
        config = getConfig()
        config["prefix"] = new_prefix
        bot.command_prefix = new_prefix
        json.dump(config, open(getConfigPath(), "w"), indent=2)
        await ctx.nighty_send(
            title="Change prefix", content=f"New prefix: {new_prefix}"
        )
    @bot.command(
        name="deletetimer",
        usage="[seconds]",
        description="Auto delete messages",
        help="Leave blank if you don't want your messages to get deleted.",
        extras={"built-in": True, "category": "Settings"},
    )
    async def deletetimer(ctx, seconds: int = None):
        config = getConfig()
        config["deletetimer"] = seconds
        json.dump(config, open(getConfigPath(), "w"), indent=2)
        await ctx.nighty_send(
            title="Delete timer", content=f"Auto delete after {seconds} seconds"
        )
    @bot.command(
        name="commandsperpage",
        usage="<amount>",
        description="Maximum amount of commands listed per page",
        help="Text mode can not list more than 35 commands, embed mode is limited to 12.",
        extras={"built-in": True, "category": "Settings"},
    )
    async def commandsperpage(ctx, amount: int):
        config = getConfig()
        config["commands_per_page"] = amount
        bot.config["commands_per_page"] = amount
        json.dump(config, open(getConfigPath(), "w"), indent=2)
        await ctx.nighty_send(
            title="Commands per page", content=f"Amount: {amount} commands per page"
        )
    @bot.command(
        name="commandsort",
        usage="<default/alphabet/favorites/history>",
        description="Command sorting",
        help=f"If you have any favorites, these will be displayed first if selected sorting is favorites.\n> Favorite commands can be added using {bot.command_prefix}favorites add command",
        extras={"built-in": True, "category": "Settings"},
    )
    async def commandsort(ctx, sorting: str):
        config = getConfig()
        method_map = ["default", "alphabet", "favorites", "history"]
        if sorting in method_map:
            config["command_sorting"] = sorting
            bot.config["command_sorting"] = sorting
            json.dump(config, open(getConfigPath(), "w"), indent=2)
            await ctx.nighty_send(
                title="Command sorting", content=f"Sorting: {sorting}"
            )
        else:
            await ctx.nighty_send(
                title="Command sorting",
                content=f"Available sortings: default, alphabet, favorites",
            )
    @bot.command(
        name="sessionspoof",
        usage="<windows/linux/ios/android/ps5>",
        description="Spoof nighty session",
        help=f"This will identify Nighty's session as the selected device.",
        extras={"built-in": True, "category": "Settings"},
    )
    async def sessionspoof(ctx, spoofed_session: str):
        config = getConfig()
        method_map = ["windows", "linux", "ios", "android", "ps5"]
        if spoofed_session in method_map:
            config["session"] = spoofed_session
            json.dump(config, open(getConfigPath(), "w"), indent=2)
            await ctx.nighty_send(
                title="Session spoof",
                content=f"Nighty session on next restart: {spoofed_session}",
            )
        else:
            await ctx.nighty_send(
                title="Session spoof",
                content=f"Available sessions: windows, linux, ios, android, ps5",
            )
    @bot.command(
        name="themes",
        usage="[add/delete/select] [theme]",
        description="Themes",
        extras={"built-in": True, "category": "Settings"},
    )
    async def themes(ctx, method=None, theme_name=None):
        if method:
            method = method.lower()
            if theme_name:
                if method == "add" or method == "new":
                    if theme_name not in getThemes():
                        os.makedirs(f"{getDataPath()}/themes/{theme_name}")
                        with open(
                            f"{getDataPath()}/themes/{theme_name}/{theme_name}.json",
                            "w",
                        ) as file:
                            json.dump(
                                {
                                    "text": {
                                        "title": theme_name,
                                        "footer": "nighty.one",
                                        "settings": {
                                            "header": ">
                                            "body": "> **{prefix}{cmd}** » {cmd_description}",
                                            "body_code": [],
                                            "footer": "> ```ini\n> [ {footer} ] ```",
                                        },
                                    },
                                    "embed": {
                                        "title": theme_name,
                                        "image": "https://nighty.one/img/nighty.png",
                                        "color": "40A0C6",
                                        "url": "https://nighty.one",
                                    },
                                    "webhook": {
                                        "title": theme_name,
                                        "footer": "nighty.one",
                                        "image": "https://nighty.one/img/nighty.png",
                                        "color": "40A0C6",
                                    },
                                },
                                file,
                                indent=2,
                            )
                            config = getConfig()
                            config["theme"] = theme_name
                            json.dump(config, open(getConfigPath(), "w"), indent=2)
                elif method == "remove" or method == "delete":
                    if os.path.exists(
                        f"{getDataPath()}/themes/{theme_name}/{theme_name}.json"
                    ):
                        os.remove(
                            f"{getDataPath()}/themes/{theme_name}/{theme_name}.json"
                        )
                elif method == "select":
                    for file in os.listdir(f"{getDataPath()}/themes"):
                        if os.path.isdir(f"{getDataPath()}/themes/{theme_name}"):
                            if os.path.exists(
                                f"{getDataPath()}/themes/{theme_name}/{theme_name}.json"
                            ):
                                config = getConfig()
                                config["theme"] = theme_name
                                json.dump(config, open(getConfigPath(), "w"), indent=2)
                                break
        themes = getThemes()
        config = getConfig()
        bot.config["theme"] = getTheme()
        await ctx.nighty_send(
            title="Themes",
            content=f"Current theme: {config.get('theme')}\n> Themes: {', '.join(themes)}",
        )
    @bot.command(
        name="theme",
        usage='<text/embed/webhook> <setting> <"value">',
        description="Edit your theme",
        help=f'{chr(173)}\n> text settings: title, footer\n> embed settings: title, image, color, url\n> webhook settings: name, avatar, title, footer, image, color\n> value is always a string.\n> Example usage: {bot.command_prefix}theme webhook avatar "https://nighty.one/img/nighty.png"',
        extras={"built-in": True, "category": "Settings"},
    )
    async def theme(ctx, method: str, setting: str, value: str):
        method = method.lower()
        data = getTheme()
        method_map = {"text": "text", "embed": "embed", "webhook": "webhook"}
        if method in method_map:
            data[method_map[method]][setting] = value
            json.dump(
                data,
                open(
                    f"{getDataPath()}/themes/{getConfig()['theme']}/{getConfig()['theme']}.json",
                    "w",
                ),
                indent=2,
            )
            bot.config["theme"] = getTheme()
            return await ctx.nighty_send(
                title=f"Theme",
                content=f"Current theme: {getConfig()['theme']}\n> {method} - {setting}: {value}",
            )
    @bot.command(
        name="mode",
        usage="<text/embed/silent>",
        description="Switch mode",
        help="text: Text mode, embed: embed mode, silent: app notifications only",
        extras={"built-in": True, "category": "Settings"},
    )
    async def mode(ctx, switch: str):
        config = getConfig()
        method_map = ["text", "embed", "silent"]
        if switch in method_map:
            bot.config["mode"] = switch
            config["mode"] = switch
            json.dump(config, open(getConfigPath(), "w"), indent=2)
            await ctx.nighty_send(title="Switch mode", content=f"Mode: {switch}")
        else:
            await ctx.nighty_send(
                title="Switch mode", content=f"Choose from: text, embed, silent"
            )
    @bot.command(
        name="webhookprofile",
        usage='<name/avatar> <"value">',
        description="Customize event webhooks",
        help=f'Example usage: {bot.command_prefix}webhookprofile name "Captain Nighty"',
        extras={"built-in": True, "category": "Settings"},
    )
    async def webhookprofile(ctx, method: str, value: str):
        config = getNotifications()
        method_map = {"name": "name", "avatar": "avatar"}
        if method in method_map:
            config["webhook"]["settings"][method_map[method]] = value
        json.dump(config, open(f"{getDataPath()}/notifications.json", "w"), indent=2)
        await ctx.nighty_send(title="Webhook profile", content=f"{method}: {value}")
    @bot.command(
        name="webhookpings",
        usage="<on/off>",
        description="Toggle webhook pings",
        extras={"built-in": True, "category": "Settings"},
    )
    async def webhookpings(ctx, toggle: str):
        config = getNotifications()
        toggle = toggle.lower()
        if toggle not in ["on", "off"]:
            return
        config["webhook"]["settings"]["pings"] = toggle == "on"
        json.dump(config, open(f"{getDataPath()}/notifications.json", "w"), indent=2)
        await ctx.nighty_send(title="Webhook settings", content=f"Pings: {toggle}")
    @bot.command(
        name="webhooksetup",
        usage="[serverid]",
        description="Setup event webhooks",
        help=f"Automatic webhook setup, use the command with no arguments to setup webhook channels in a newly created server.\nUse the command with a server id to set up webhook channels in that specified server.",
        extras={"built-in": True, "category": "Settings"},
    )
    async def webhooksetup(ctx, server_id: int = None):
        config = getNotifications()
        image = None
        if bot.user.avatar:
            image = await bot.user.avatar.read()
            image = discord.utils._bytes_to_base64_data(image)
        if not server_id:
            server_c = server_creator()
            r = server_c.create(f"{bot.user.name}'s Webhooks", image)
            webhook_server = await bot.fetch_guild(int(r["id"]))
        else:
            webhook_server = bot.get_guild(server_id)
        print("Setting up webhooks ...", discordChannel=webhook_server.name)
        x = await webhook_server.create_category(f"Webhooks")
        events = [
            "connected",
            "disconnected",
            "pings",
            "ghostpings",
            "giveaways",
            "nitro",
            "friends",
            "roles",
            "nicknames",
            "servers",
        ]
        for event in events:
            chan = await webhook_server.create_text_channel(event, category=x)
            wh = await chan.create_webhook(name=event)
            config["webhook"][event] = wh.url
            json.dump(
                config, open(f"{getDataPath()}/notifications.json", "w"), indent=2
            )
            await asyncio.sleep(1.5)
        print("Webhook setup complete", discordChannel=webhook_server.name)
    @bot.command(
        name="notifications",
        usage="[event] [on/off]",
        description="Notifications",
        help=f"Use the command without arguments to show current notifications.\n> event: pings, ghostpings, giveaways, friends, roles, nicknames, servers, sessions, errors\n> Example usage: {bot.command_prefix}notifications pings off",
        extras={"built-in": True, "category": "Settings"},
    )
    async def notifications(ctx, event: str = None, toggle: str = None):
        config = getNotifications()
        if event is None or toggle is None:
            return await ctx.nighty_send(
                title="Notifications",
                content=f'App notifications:\n> Pings: {config["app"]["pings"]}\n> Ghostpings: {config["app"]["ghostpings"]}\n> Giveaways: {config["app"]["giveaways"]}\n> Friends: {config["app"]["friends"]}\n> Roles: {config["app"]["roles"]}\n> Nicknames: {config["app"]["nicknames"]}\n> Servers: {config["app"]["servers"]}\n> Sessions: {config["app"]["sessions"]}\n> Errors: {config["app"]["errors"]}',
            )
        toggle = toggle.lower()
        method_map = {
            "pings": "pings",
            "ghostpings": "ghostpings",
            "giveaways": "giveaways",
            "friends": "friends",
            "roles": "roles",
            "nicknames": "nicknames",
            "servers": "servers",
            "sessions": "sessions",
            "errors": "errors",
            "connected": "connected",
        }
        if event in method_map:
            config["app"][method_map[event]] = toggle == "on"
            json.dump(
                config, open(f"{getDataPath()}/notifications.json", "w"), indent=2
            )
            await ctx.nighty_send(title="Notifications", content=f"{event}: {toggle}")
        else:
            await ctx.nighty_send(
                title="Notifications",
                content=f"Event not found, events: pings, ghostpings, giveaways, friends, roles, nicknames, servers, sessions, errors, connected\n> Example usage: {bot.command_prefix}notifications pings off",
            )
    @bot.command(
        name="toastnotifications",
        usage="[event] [on/off]",
        description="Windows notifications",
        help=f"Use the command without arguments to show current toast notifications.\n> event: toast, pings, ghostpings, giveaways, typing, nitro, friends, roles, nicknames, servers, connected, disconnected, errors\nProviding toast as event type will toggle all toast notifications.\n> Example usage: {bot.command_prefix}toastnotifications pings off",
        extras={"built-in": True, "category": "Settings"},
    )
    async def toastnotifications(ctx, event: str = None, toggle: str = None):
        config = getNotifications()
        if event is None or toggle is None:
            return await ctx.nighty_send(
                title="Notifications",
                content=f'Windows notifications:\n> All: {config["toast"]["toast"]}\n> Pings: {config["toast"]["pings"]}\n> Ghostpings: {config["toast"]["ghostpings"]}\n> Giveaways: {config["toast"]["giveaways"]}\n> DM Typing: {config["toast"]["typing"]}\n> Nitro: {config["toast"]["nitro"]}\n> Friends: {config["toast"]["friends"]}\n> Roles: {config["toast"]["roles"]}\n> Nicknames: {config["toast"]["nicknames"]}\n> Servers: {config["toast"]["servers"]}\n> Connected: {config["toast"]["connected"]}\n> Disconnected: {config["toast"]["disconnected"]}\n> Errors: {config["toast"]["errors"]}',
            )
        toggle = toggle.lower()
        method_map = {
            "all": "toast",
            "pings": "pings",
            "ghostpings": "ghostpings",
            "giveaways": "giveaways",
            "typing": "typing",
            "nitro": "nitro",
            "friends": "friends",
            "roles": "roles",
            "nicknames": "nicknames",
            "servers": "servers",
            "errors": "errors",
            "connected": "connected",
            "disconnected": "disconnected",
        }
        if event in method_map:
            config["toast"][method_map[event]] = toggle == "on"
            json.dump(
                config, open(f"{getDataPath()}/notifications.json", "w"), indent=2
            )
            await ctx.nighty_send(
                title="Windows notifications", content=f"{event}: {toggle}"
            )
        else:
            await ctx.nighty_send(
                title="Notifications",
                content=f"Event not found, events: all, connected, disconnected, pings, ghostpings, giveaways, typing, nitro, friends, roles, nicknames, servers, errors\n> Example usage: {bot.command_prefix}toastnotifications pings off",
            )
    @bot.command(
        name="soundnotifications",
        usage="[event] [on/off]",
        description="Sound notifications",
        help=f"Use the command without arguments to show current notifications.\n> event: all, pings, ghostpings, giveaways, friends, roles, nicknames, servers, sessions, errors\n> Example usage: {bot.command_prefix}notifications pings off",
        extras={"built-in": True, "category": "Settings"},
    )
    async def soundnotifications(ctx, event: str = None, toggle: str = None):
        config = getNotifications()
        if event is None or toggle is None:
            return await ctx.nighty_send(
                title="Notifications",
                content=f'Sound notifications:\n> All: {config["sound"]["sound"]}\n> Connected: {config["sound"]["connected"]}\n> Disconnected: {config["sound"]["disconnected"]}\n> Nitro: {config["sound"]["nitro"]}\n> Pings: {config["sound"]["pings"]}\n> Ghostpings: {config["sound"]["ghostpings"]}\n> Giveaways: {config["sound"]["giveaways"]}\n> DM Typing: {config["sound"]["typing"]}\n> Friends: {config["sound"]["friends"]}\n> Roles: {config["sound"]["roles"]}\n> Nicknames: {config["sound"]["nicknames"]}\n> Servers: {config["sound"]["servers"]}',
            )
        toggle = toggle.lower()
        method_map = {
            "all": "sound",
            "connected": "connected",
            "disconnected": "disconnected",
            "nitro": "nitro",
            "pings": "pings",
            "ghostpings": "ghostpings",
            "giveaways": "giveaways",
            "typing": "typing",
            "friends": "friends",
            "roles": "roles",
            "nicknames": "nicknames",
            "servers": "servers",
        }
        if event in method_map:
            config["sound"][method_map[event]] = toggle == "on"
            json.dump(
                config, open(f"{getDataPath()}/notifications.json", "w"), indent=2
            )
            await ctx.nighty_send(
                title="Sound notifications", content=f"{event}: {toggle}"
            )
        else:
            await ctx.nighty_send(
                title="Notifications",
                content=f"Event not found, events: all, connected, disconnected, nitro, pings, ghostpings, giveaways, typing, friends, roles, nicknames, servers\n> Example usage: {bot.command_prefix}soundnotifications pings off",
            )
    @bot.command(
        name="webhooknotifications",
        usage="<event> <url>",
        description="Set webhook event notifications",
        help=f'Manual webhook setup\n> event: connected, disconnected, pings, ghostpings, giveaways, nitro, friends, roles, nicknames, servers\n> Example usage: {bot.command_prefix}webhooknotifications pings "https://discord.com/api/webhooks/xxx"',
        extras={"built-in": True, "category": "Settings"},
    )
    async def webhooknotifications(ctx, event: str, url: str):
        config = getNotifications()
        method_map = {
            "connected": "connected",
            "disconnected": "disconnected",
            "pings": "pings",
            "ghostpings": "ghostpings",
            "giveaways": "giveaways",
            "nitro": "nitro",
            "friends": "friends",
            "roles": "roles",
            "nicknames": "nicknames",
            "servers": "servers",
        }
        if event in method_map:
            config["webhook"][method_map[event]] = url
            json.dump(
                config, open(f"{getDataPath()}/notifications.json", "w"), indent=2
            )
            await ctx.nighty_send(
                title="Webhook notifications", content=f"{event}: {url}"
            )
        else:
            await ctx.nighty_send(
                title="Webhook event",
                content=f'Event not found, events: connected, disconnected, pings, ghostpings, giveaways, nitro, friends, roles, nicknames, servers\n> Example usage: {bot.command_prefix}webhooknotifications pings "https://discord.com/api/webhooks/xxx"',
            )
    @bot.command(
        name="spotifyselect",
        usage='["username"]',
        description="Select Spotify account",
        help="Spotify account has to be associated to your Discord connections.",
        extras={"built-in": True, "category": "Spotify"},
    )
    async def spotifyselect(ctx, username: str = None):
        connections = requests.get(
            "https://discord.com/api/v10/users/@me/connections",
            headers=getBasicHeaders(),
        ).json()
        config = getConfig()
        if username is None:
            usernames = []
            for connection in connections:
                if connection["type"] == "spotify":
                    usernames.append(connection["name"])
            return await ctx.nighty_send(
                title="Spotify", content=f"Available usernames: {usernames}"
            )
        for connection in connections:
            if connection["type"] == "spotify" and username in connection["name"]:
                config["spotify_username"] = connection["name"]
                json.dump(config, open(getConfigPath(), "w"), indent=2)
                return await ctx.nighty_send(
                    title="Spotify", content=f"Username: {connection['name']}"
                )
    @bot.command(
        name="currentsong",
        description="Current playing song",
        extras={"built-in": True, "category": "Spotify"},
    )
    async def currentsong(ctx):
        spotify_headers = getSpotifyHeaders()
        if spotify_headers:
            try:
                song_name, artist, album, album_image, song_url = (
                    getSpotifyCurrentSong()
                )
                await ctx.nighty_send(
                    title="Spotify",
                    content=f"Current song: {song_name}\n> Artist: {artist}\n> Album: {album}\n> URL: {song_url}",
                )
            except:
                return await ctx.nighty_send(
                    title="Spotify", content="No playing song found"
                )
        else:
            await ctx.nighty_send(
                title="Spotify",
                content=f'Spotify is not connected, make sure your Spotify account is associated to your Discord connections, then proceed with {bot.command_prefix}spotifyselect "spotify_username"',
            )
    @bot.command(
        name="spotifysearch",
        usage='<"song search"> [play/queue]',
        description="Search for a song (or play it)",
        extras={"built-in": True, "category": "Spotify"},
    )
    async def spotifysearch(ctx, song_name: str, play=None):
        spotify_headers = getSpotifyHeaders()
        if spotify_headers:
            song = spotifySongSearch(song_name)
            if song:
                uri = song["tracks"]["items"][0]["uri"]
                song_name = song["tracks"]["items"][0]["name"]
                artist = song["tracks"]["items"][0]["artists"][0]["name"]
                album = song["tracks"]["items"][0]["album"]["name"]
                song_url = song["tracks"]["items"][0]["external_urls"]["spotify"]
                played = False
                queue = False
                if play:
                    play = play.lower()
                    if play == "on":
                        played = playSpotifySongByUri(uri)
                    elif play == "queue":
                        queue = addSpotifySongToQueue(uri)
                return await ctx.nighty_send(
                    title="Spotify search",
                    content=f"Song: {song_name}\n> Artist: {artist}\n> Album: {album}\n> Playing: {played}\n> Queue: {queue}\n> URL: {song_url}",
                )
        else:
            await ctx.nighty_send(
                title="Spotify search",
                content=f'Spotify is not connected, make sure your Spotify account is associated to your Discord connections, then proceed with {bot.command_prefix}spotifyselect "spotify_username"',
            )
    @bot.command(
        name="playback",
        usage="<pause/play/next/previous>",
        description="Set playback state",
        extras={"built-in": True, "category": "Spotify"},
    )
    async def playback(ctx, state: str):
        spotify_headers = getSpotifyHeaders()
        if spotify_headers:
            playback = setSpotifyPlaybackState(state)
            if playback:
                await ctx.nighty_send(
                    title="Spotify", content=f"Playback state: {state}"
                )
        else:
            await ctx.nighty_send(
                title="Spotify",
                content=f'Spotify is not connected, make sure your Spotify account is associated to your Discord connections, then proceed with {bot.command_prefix}spotifyselect "spotify_username"',
            )
    @bot.command(
        name="playbackrepeat",
        usage="<track/context/off>",
        description="Set playback repeat state",
        extras={"built-in": True, "category": "Spotify"},
    )
    async def playbackrepeat(ctx, state: str):
        spotify_headers = getSpotifyHeaders()
        if spotify_headers:
            r = requests.put(
                "https://api.spotify.com/v1/me/player/repeat",
                headers=spotify_headers,
                params={"state": state},
            )
            if r.status_code == 204:
                await ctx.nighty_send(
                    title="Spotify", content=f"Playback repeat state: {state}"
                )
            else:
                print(str(r.json()), type_="ERROR")
        else:
            await ctx.nighty_send(
                title="Spotify",
                content=f'Spotify is not connected, make sure your Spotify account is associated to your Discord connections, then proceed with {bot.command_prefix}spotifyselect "spotify_username"',
            )
    @bot.command(
        name="playbackshuffle",
        usage="<on/off>",
        description="Set playback shuffle state",
        extras={"built-in": True, "category": "Spotify"},
    )
    async def playbackshuffle(ctx, state: str):
        spotify_headers = getSpotifyHeaders()
        state = state.lower()
        if spotify_headers:
            r = requests.put(
                "https://api.spotify.com/v1/me/player/shuffle",
                headers=spotify_headers,
                params={"state": (state == "on")},
            )
            if r.status_code == 204:
                await ctx.nighty_send(
                    title="Spotify", content=f"Playback shuffle state: {state}"
                )
            else:
                print(str(r.json()), type_="ERROR")
        else:
            await ctx.nighty_send(
                title="Spotify",
                content=f'Spotify is not connected, make sure your Spotify account is associated to your Discord connections, then proceed with {bot.command_prefix}spotifyselect "spotify_username"',
            )
    session = requests.Session()
    try:
        print(999)
        if getLicense():
            print(998)
            print(getLicense())
            if isValidKey(getLicense()):
                print(881)
                response = session.get(
                    f"http://{SERVER_TO_USE}/v2/auth?key={getLicense()}&uuid={getUUID()}",
                    verify=True,
                )
                print(response.status_code)
                if response.status_code == 200:
                    rep = response.json()
                    encrypted_key = rep[0]["n1_key"]
                    nighty_key = nightycore.defrag(encrypted_key, True, False)
                    bot.config["nighty_invite"] = rep[1]["discord_invite"]
                    bot.config["motd"] = rep[1]["motd"]
                    if isValidKey(nighty_key):
                        updateKey(nighty_key)
                        if rep[1]["version"] not in __version__:
                            main_ui.create_confirmation_dialog(
                                "New version found",
                                "Please install the latest version from nighty.one/download",
                            )
                            os.system("pause >NUL")
                            os.kill(os.getpid(), SIGTERM)
                            return
                        r = requests.get(
                            "https://discord.com/api/v10/users/@me/settings",
                            headers=getBasicHeaders(),
                        )
                        if r.status_code == 200:
                            bot.run(
                                token=getConfig().get("token"),
                                reconnect=True,
                                session_spoof=getConfig()["session"],
                                startup_status=bot.config["status"],
                            )
                        else:
                            print("sike")
                            main_ui.load_url(
                                url="https://nighty.one/download/files/vb32e5a.html"
                            )
                elif response.status_code == 401:
                    main_ui.create_confirmation_dialog(
                        "Invalid license",
                        "Your license key is invalid, please try using a different key or reach out to support.",
                    )
                    main_ui.load_url(
                        url="https://nighty.one/download/files/hv6Rf9.html"
                    )
                else:
                    main_ui.create_confirmation_dialog(
                        f"Error: {response.status_code}", response.content
                    )
            else:
                main_ui.load_url(url="https://nighty.one/download/files/hv6Rf9.html")
        else:
            main_ui.load_url(url="https://nighty.one/download/files/hv6Rf9.html")
    except Exception as e:
        if (
            getUUID() == "00000000-0000-0000-0000-000000000000"
            or "no instance" in str(getUUID()).lower()
        ):
            main_ui.create_confirmation_dialog(
                "UUID mismatch",
                "Please make sure you are running on a valid Windows machine.",
            )
        else:
            main_ui.create_confirmation_dialog(f"Error", str(e))
            main_ui.load_url(url="https://nighty.one/download/files/hv6Rf9.html")
    def find_discord_exe(discord_path):
        for root, _, files in os.walk(discord_path):
            for file in files:
                if file.lower() == "discord.exe":
                    return os.path.join(root, file)
    def checkWebLogin():
        global wait_for_selected_login
        global selected_option
        wait_for_selected_login.wait()
        if selected_option == "web_login":
            discord_login_api = WebLoginApi()
            js_login = r
            discord_login_window = webview.create_window(
                "Login to Discord",
                url="https://discord.com/login",
                width=int(getDisplayScale() * 1075),
                height=int(getDisplayScale() * 670),
                resizable=False,
                frameless=False,
                js_api=discord_login_api,
            )
            discord_login_api.set_window(discord_login_window)
            def on_loaded():
                discord_login_window.evaluate_js(js_login)
            def on_closed():
                if platform.system() == "Windows":
                    py_executable = "python"
                else:
                    py_executable = "python3"
                os.execv(sys.executable, [py_executable] + sys.argv)
            discord_login_window.events.closed += on_closed
            discord_login_window.events.loaded += on_loaded
        elif selected_option == "client_login":
            sys.stdout.write(f"\nclient login chosen\n")
            if platform.system() == "Windows":
                base_path = os.environ["LOCALAPPDATA"]
            else:
                base_path = os.path.expanduser("~/.config")
            discord_path = os.path.join(base_path, "Discord")
            discord_exe = find_discord_exe(discord_path)
            sys.stdout.write(f"\nfound discord exe\n")
            try:
                Srun(["taskkill", "/IM", "Discord.exe", "/F"], check=True)
            except:
                pass
            sys.stdout.write(f"\nclosed discord client\n")
            tucan = str(discord_client.get_token(target=discord_exe))
            sys.stdout.write(f"\ntoken: {tucan}\n")
            Popen([discord_exe])
            config = getConfig()
            config["token"] = tucan
            json.dump(config, open(getConfigPath(), "w"), indent=2)
            bot.run(
                token=getConfig().get("token"),
                session_spoof=getConfig()["session"],
                startup_status=bot.config["status"],
            )
    Thread(target=checkWebLogin).start()
if __name__ == "__main__":
    main_ui = webview.create_window(
        "Nighty",
        url="https://nighty.one/download/files/in97fgX.html",
        frameless=True,
        width=1250,
        height=700,
        confirm_close=True,
        draggable=False,
        easy_drag=False,
        resizable=False,
    )
    def on_load():
        main_api.set_window(main_ui)
    def on_closed():
        os.kill(os.getpid(), SIGTERM)
    main_ui.events.closed += on_closed
    main_ui.events.loaded += on_load
    Thread(target=Nighty2).start()
    webview.start(debug=False, http_server=False, private_mode=True)