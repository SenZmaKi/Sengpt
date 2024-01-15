"""
Utility shared in both sync and async tests
"""

import os
from typing import Any
from .utils import ROOT_DIR


class Env:
    @staticmethod
    def get(key: str, default: Any) -> str:
        gotten = Env.loaded_env.get(key, default)
        if gotten == default:
            gotten = os.environ.get(key, default)
        return gotten

    @staticmethod
    def load_env() -> dict[str, str]:
        env: dict[str, str] = {}
        env_file = os.path.join(ROOT_DIR, ".env")
        if not os.path.isfile(env_file):
            return env
        with open(env_file) as f:
            for line in f.read().splitlines():
                if line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                env[key] = value.strip()
        return env

    loaded_env = load_env()


SESSION_TOKEN = Env.get("SESSION_TOKEN", None)
CONVERSATION_ID = Env.get("CONVERSATION_ID", None)
GPT_PROMPT = Env.get("GPT_PROMPT", "what is 2 + 2")
IGNORE_ARKOSE = Env.get("IGNORE_ARKOSE", False)


def fancy_shmansy_print(text: str) -> None:
    print(text, end="", flush=True)

