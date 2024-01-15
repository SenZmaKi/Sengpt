import json
import os
import platform
from typing import Any


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
CHATGPT_ENTRY_POINT = "https://chat.openai.com"
BACKEND_API_ENTRYPOINT = f"{CHATGPT_ENTRY_POINT}/backend-api/{{}}"
RETRIEVE_CHATS_ENDPOINT = BACKEND_API_ENTRYPOINT.format("conversations")
API_ENTRY_POINT = f"{CHATGPT_ENTRY_POINT}/api"
CUSTOM_INSTRUCTIONS_ENDPOINT = BACKEND_API_ENTRYPOINT.format("user_system_messages")
CONVERSATION_ENTRYPOINT = BACKEND_API_ENTRYPOINT.format("conversation")
AUTH_SESSION_ENDPOINT = f"{API_ENTRY_POINT}/auth/session"

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
RELEASES_ENDPOINT = (
    "https://api.github.com/repos/Zai-Kun/reverse-engineered-chatgpt/releases"
)


class OsUtils:
    """
    Os utility
    """

    os_name = platform.system()
    is_windows = os_name == "Windows"
    is_linux = os_name == "Linux"
    is_mac = os_name == "Darwin"


def decode_json_from_string(json_string: str) -> dict[str, Any] | None:
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return None

