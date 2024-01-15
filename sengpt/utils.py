import asyncio
from typing import NoReturn
import os
import sys
from appdirs import user_config_dir


GLOW_INSTALLATION_URL = (
    "https://github.com/charmbracelet/glow"
)
APP_NAME = "Sengpt"
APP_NAME_LOWER = "sengpt"
REPO_URL = "https://github.com/SenZmaKi/Sengpt"
DESCRIPTION = "ChatGPT in your terminal, no OpenAI API key required"
REPO_TAGS_URL = "https://api.github.com/repos/SenZmaKi/Sengpt/tags"
# FIXME: Update to False on push
DEBUG = False
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
VERSION = "0.1.0"
V_VERSION = f"v{VERSION}"


class OsUtils:
    is_windows = sys.platform == "win32"
    is_linux = sys.platform == "linux"
    is_mac = sys.platform == "mac"
    config_dir = ROOT_DIR if DEBUG else user_config_dir(APP_NAME)
    if is_windows:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def print_and_exit(text: str) -> NoReturn:
    print(text)
    sys.exit()


def check_repo_print(text: str, exit=True) -> None | NoReturn:
    check_repo_text = f"{text}\nCheck {REPO_URL} for help"
    if exit:
        print_and_exit(check_repo_text)
    print(check_repo_text)


def mkdir(path: str) -> None:
    # Incase some weirdo has a file with the same name as the folder
    if os.path.isfile(path):
        os.unlink(path)
    if not os.path.isdir(path):
        os.mkdir(path)

