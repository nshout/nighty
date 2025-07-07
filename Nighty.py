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
                    "header": "> # {title}",
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
        "commandsearch.py": """
def CustomSearchTabButton():

def UISearch(self):
ui.searchBox()

ui.create_tab_button(
ref="nighty_csearch",
title="Search for a command",
icon="https://static-00.iconduck.com/assets.00/search-icon-2048x2048-zik280t3.png",
func=UISearch
)
        CustomSearchTabButton()""",
        "openNightyFolder.py": """

def NightyFolderTab():
def openNightyFolder(self):
os.startfile(getNightyPath())

ui.create_tab_button(
ref="open_nighty_folder",
title="Open folder",
icon="https://cdn4.iconfinder.com/data/icons/small-n-flat/24/folder-blue-512.png",
func=openNightyFolder
)
        NightyFolderTab()""",
        "reloadscripts.py": """
def reloadScripts():
def updateUI(self):
ui.update()

ui.create_tab_button("nighty_custom_script_reload", "Reload Scripts", icon="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Flat_restart_icon.svg/2048px-Flat_restart_icon.svg.png", func=updateUI)
        reloadScripts()""",
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
    """
Scale bytes to its proper format
e.g.:
1253656 => '1.20MB'
1253656678 => '1.17GB'
    """
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
    lambda url: re.match(r"^(http|https)://[^\s/$.?#].[^\s]*$", url) is not None
)
getChannelInfo = (
    lambda channel: f"#{channel.name}, {channel.guild.name}"
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
    """
Get the current elapsed time of the program since it started in Unix timestamp format.
    """
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
        nighty_image = r"""data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAACCcAAAgmCAYAAADO0y2yAAGt5UlEQVR4nOzd25JcV3of+C9BAGSRbFWRTTVDbnWgJM8oZmLsQDlCtiPmBvUGxO1coebKl6x5AtY8QcNPQOgJRN/4wjGehsIR9hwUbihsy7LH7mar2XJTokiwQRJAHbDmYmdW5WEfM3PVzsPvx6hgYa+11147AYJVtf/5fYOUUgAAAAAAAAAA5HKj7w0AAAAAAAAAAJtNOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhKOAEAAAAAAAAAyEo4AQAAAAAAAADISjgBAAAAAAAAAMhK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AAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAAAAAFSlOAEAAAAAAAAAqEpxAgAAAAAAAABQleIEAAAAAAAAAKAqxQkAAAAAAAAAQFWKEwAAAAAAAACAqhQnAAAAAAAAAABVKU4AAAAAAAAAAKpSnAAAAAAAAAAAVKU4AQAAAAAAAACoSnECAAAAAAAAAFCV4gQAAAAAAAAAoCrFCQAAAAAAAABAVYoTAAAAAAAAAICqFCcAAAAAAAAAAFUpTgAAAAAAAAAAqlKcAAAAAAAAAABUpTgBAAAAAAAAAKhKcQIAAAAAAAAAUJXiBAAAAAAAAACgKsUJAAAAAAAAAEBVihMAAAAAAAAAgKoUJwAAAAAAAAAAVSlOAAAAAAAAAACqUpwAAAAAAADA/79dOxYAAAAAGORvPYp9xREArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsJITAAAAAAAAAICVnAAAAAAAAAAArOQEAAAAAAAAAGAlJwAAAAAAAAAAKzkBAAAAAAAAAFjJCQAAAAAAAADASk4AAAAAAAAAAFZyAgAAAAAAAACwkhMAAAAAAAAAgJWcAAAAAAAAAACs5AQAAAAAAAAAYCUnAAAAAAAAAAArOQEAAAAAAAAAWMkJAAAAAAAAAMBKTgAAAAAAAAAAVnICAAAAAAAAALCSEwAAAAAAAACAlZwAAAAAAAAAAKzkBAAAAAAAAABgJScAAAAAAAAAACs5AQAAAAAAAABYyQkAAAAAAAAAwEpOAAAAAAAAAABWcgIAAAAAAAAAsArlA7li6bpQDAAAAABJRU5ErkJggg=="""

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
                                ppfile = f"""# -*- coding: utf-8 -*-
                                    {pfile}"""
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
                        ppfile = f"""# -*- coding: utf-8 -*-
                            {pfile}"""
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
            self._window.evaluate_js(r"""
var token = (webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
pywebview.api.saveTokenToConfig(token)
function login(token) {
setInterval(() => {
document.body.appendChild(document.createElement `iframe`).contentWindow.localStorage.token = `"${token}"`
}, 50);
setTimeout(() => {
location.reload();
}, 2500);
}

login('PASTE TOKEN HERE')
setTimeout(function() {
pywebview.api.hide();
}, 2000);
            """)

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
            f"""<li class="ui-sidebar__list-item icon-type-fill"><a href="
"html.parser",
)
)

script_tag = soup.new_tag("script")
                script_tag.string = f"""
    function
    {func.__name__}()
    {{
        pywebview.api.
    {func.__name__}();
    }}
    """
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
                main_ui.evaluate_js(f"""
    document.getElementById("{self.ref}").textContent = `{code}`;
    Prism.highlightElement(document.getElementById("{self.ref}"))
    """)
if style:
self.style = style
try:
main_ui.evaluate_js(
                f"""
    document.getElementById("{self.ref}").style.cssText += `{style}`;
    """
)
except:
pass

def show(self):
main_ui.evaluate_js(
                f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                f"""
    document.getElementById("{self.ref}").style.display = none;
    """
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
                f"""
    document.getElementById("{self.ref}").textContent = "{text}";
    """
)
except:
pass
if text_size:
self.text_size = text_size
try:
main_ui.evaluate_js(
                f"""
    document.getElementById("{self.ref}").style.cssText.replace( / font - size: [ ^;] * / i, 'font-size: ' + {
        text_size});"""
)
except:
pass
if pos_x:
self.pos_x = pos_x
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('left', {pos_x});
    """
)
except:
pass
if pos_y:
self.pos_y = pos_y
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('top', {pos_y});
    """
)
except:
pass
if style:
self.style = style
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.cssText += "{style}";
    """
)
except:
pass

def show(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = none;
    """
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
                                                                                             f"""
    document.getElementById("{self.ref}").src = "{src}";
    """
)
except:
pass
if width:
self.width = width
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('width', {width});
    """
)
except:
pass
if height:
self.height = height
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('height', {height});
    """
)
except:
pass
if pos_x:
self.pos_x = pos_x
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('left', {pos_x});
    """
)
except:
pass
if pos_y:
self.pos_y = pos_y
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('top', {pos_y});
    """
)
except:
pass
if style:
self.style = style
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.cssText += "{style}";
    """
)
except:
pass

def show(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = none;
    """
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
                                                                                             f"""
    document.querySelector('label[for="' + "{self.ref}" + '"]').textContent = "{label}";
    """
)
except:
pass
if pos_x:
self.pos_x = pos_x
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('left', {pos_x});
    """
)
except:
pass
if pos_y:
self.pos_x = pos_x
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('top', {pos_y});
    """
)
except:
pass
if style:
self.style = style
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.cssText += "{style}";
    """
)
except:
pass

def updateCheckbox(self, checked: bool):
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").checked = {str(checked).lower()};
    """
)
except:
pass

def show(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = none;
    """
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
                                                                                             f"""
    document.getElementById("{self.ref}").textContent = "{label}";
    """
)
except:
pass
if pos_x:
self.pos_x = pos_x
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('left', {pos_x});
    """
)
except:
pass
if pos_y:
self.pos_y = pos_y
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('top', {pos_y});
    """
)
except:
pass
if style:
self.style = style
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.cssText += "{style}";
    """
)
except:
pass

def show(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = none;
    """
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
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('placeholder', '{placeholder}');
    """
)
except:
pass
if style:
self.style = style
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.cssText += "{style}";
    """
)
except:
pass

def show(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = none;
    """
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
                                                                                             f"""
    document.getElementById("{self.ref}").setAttribute('placeholder', '{placeholder}');
    """
)
except:
pass
if style:
self.style = style
try:
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.cssText += "{style}";
    """
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
                                                                                             main_ui.evaluate_js(f"""
    var
    select = document.getElementById("{self.ref}");
    while (select.options.length > 0) {{
    select.remove(0);}}
    {options_js}
    """)
except:
pass

def show(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = none;
    """
)

class TabCard:
def __init__(self, ref: str, style: str):
self.ref = bleach.clean(ref)
self.style = style

def show(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = block;
    """
)

def hide(self):
main_ui.evaluate_js(
                                                                                             f"""
    document.getElementById("{self.ref}").style.display = none;
    """
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
                                                                                                 self.html = f""" < div
    id = "{self.ref}"
    onclick = "toggleSidebar(false);"
    onhover = "moveUiSidebarMarker("
    {self.ref}
    ");"
    style = "display: none;"

    class ="animate__animated animate__fadeIn" > < div class ="custom-card" id="card_{self.ref}" > < div class ="custom_tab__hero" > < p class ="custom_tab__heading" > {self.title} < / p > < / div > < / div > < / div > """
else:
self.description = bleach.clean(description)
                                                                                                                                                                                                                                                                  self.html = f""" < div id="{self.ref}" onclick="toggleSidebar(false);" onhover="moveUiSidebarMarker("{self.ref}");" style="display: none;" class ="animate__animated animate__fadeIn" > < div class ="custom-card" id="card_{self.ref}" > < div class ="custom_tab__hero" > < p class ="custom_tab__heading" > {self.title} < / p > < p class ="custom_tab__subheading" > {self.description} < / p > < / div > < / div > < / div > """
else:
if description is None:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             self.html = f""" < div id="{self.ref}" onclick="toggleSidebar(false);" onhover="moveUiSidebarMarker("{self.ref}");" style="display: none;" class ="animate__animated animate__fadeIn" > < div class ="custom-card" id="card_{self.ref}" > < div class ="custom_tab__hero" > < / div > < / div > < / div > """
else:
self.description = bleach.clean(description)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   self.html = f""" < div id="{self.ref}" onclick="toggleSidebar(false);" onhover="moveUiSidebarMarker("{self.ref}");" style="display: none;" class ="animate__animated animate__fadeIn" > < div class ="custom-card" id="card_{self.ref}" > < div class ="custom_tab__hero" > < p class ="custom_tab__subheading" > {self.description} < / p > < / div > < / div > < / div > """

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
html = f"""

    < div
    id = "customtab-box"
    data - community - tab - selected = "{c_id}" >
    < ul
    id = "{self.ref}-switcher"

    class ="customtab_cl__switcher" > """
break
for column in columns:
c_id, c_text = column
                                                                                             html += f""" < li > < button class ="btn-customtabcl cl__tab-button" id="{c_id}-switcher" type="button" aria-expanded="true" aria-controls="{c_id}" > < span > {c_text} < / span > < / button > < / li > """
                                                                                             html += f""" < div aria-hidden="true" class ="switch-highlighter" > < / div > < / ul >

    < div

    class ="cl__tab__content" > """
for column in columns:
c_id, c_text = column
                                                                                             html += f""" < div class ="tab" id="{c_id}" aria-labelledby="{c_id}-switcher" > < / div > """
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
script_tag.string = f"""

    document.getElementById("{ref}").addEventListener("blur", function()
    {{
        Prism.highlightElement(document.getElementById("{ref}"));
    pywebview.api.
    {func.__name__}(document.getElementById("{ref}").textContent);
    }})
    document.getElementById("{ref}").addEventListener('keydown', function(event)
    {{
    if (event.key === 'Tab')
    {{
        event.preventDefault();
    document.execCommand('insertText', false, '\t');
    }}
    }});
    """
if style:
                                                                                                 html = f""" < div

    class ="customtab__preview-box" > < pre class ="py-code" style="overflow: auto; font-size: {text_size}px; left: {pos_x}px; top: {pos_y}px; {style}" > < code contenteditable="true" spellcheck="false" id="{ref}" class ="language-python" > {code}"""
else:
                                                                                                                                                                                                                                                                                                                                           html = f""" < div class ="customtab__preview-box" > < pre class ="py-code" style="overflow: auto; font-size: {text_size}px; left: {pos_x}px; top: {pos_y}px;" > < code contenteditable="true" spellcheck="false" id="{ref}" class ="language-python" > {code}"""
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   html += """ < / code > < / pre > < / div > """
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
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   html = f""" < div class ="customtab__preview-box" > < pre class ="py-code" style="overflow: auto; font-size: {text_size}px; left: {pos_x}px; top: {pos_y}px; {style}" > < code id="{ref}" class ="language-python" style="user-select: text;" > {code}"""
else:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    html = f""" < div class ="customtab__preview-box" > < pre class ="py-code" style="overflow: auto; font-size: {text_size}px; left: {pos_x}px; top: {pos_y}px;" > < code id="{ref}" class ="language-python" style="user-select: text;" > {code}"""
                                                                                             html += """ < / code > < / pre > < / div > """
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
script_tag.string = f"""

    function
    {func.__name__}(toggleState)
    {{
        pywebview.api.
    {func.__name__}(toggleState);
    }}
    """

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
                                                                                             script_tag.string = f"""
    function
    {func.__name__}()
    {{
        pywebview.api.
    {func.__name__}();
    }}
    """
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
                                                                                             script_tag.string = f"""
    function
    {func.__name__}()
    {{
        pywebview.api.
    {func.__name__}(document.getElementById('{ref}').value);
    }}
    """

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
                                                                                             script_tag.string = f"""
    function
    {func.__name__}(value)
    {{
        pywebview.api.
    {func.__name__}(value);
    }}
    """

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
                                                                                                 f""" < li

    class ="ui-sidebar__list-item icon-type-fill" > < a href="

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
        self._webview.evaluate_js("""showSearchBox();""")

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
                title="Dick size", content=f"{user}'s size:\n> ## 8{dong}D"
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
                        content=f"Definition #{pos + 1};\n> {result['list'][pos]['definition']}\n> Example: {result['list'][pos]['example']}",
                    )
                else:
                    await ctx.nighty_send(
                        title="Urban dictionary",
                        content="Your search terms gave no results",
                    )

            except IndexError:
                await ctx.nighty_send(
                    title="Urban dictionary",
                    content="There is no definition #{}".format(pos + 1),
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
                                                "header": "> # {title}",
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
                js_login = r"""
console.log(`injected`)
var previousUrl = window.location.href;
function checkUrlChange() {
var currentUrl = window.location.href;
if (currentUrl !== previousUrl) {
previousUrl = currentUrl;
console.log(`URL changed: ${currentUrl}`)
pywebview.api.url_change_callback(currentUrl);
}
setTimeout(checkUrlChange, 1000); // Check every 1 second
}

                                                                                                         checkUrlChange();"""
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
