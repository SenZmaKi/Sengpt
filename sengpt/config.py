import sys

from sengpt.argparser import SYS_ARGS
from .utils import APP_NAME, mkdir, OsUtils, check_repo_print
from appdirs import user_config_dir
import os
from typing import Any, NoReturn, TypeVar
import json

T = TypeVar("T")


class Config:
    @staticmethod
    def update_session_token():
        if len(SYS_ARGS.non_args) != 1:
            check_repo_print(
                "Invalid usage!!!\nUsage: --session_token <your-session-token-goes-here>"
            )
        session_token = SYS_ARGS.non_args[0]
        Config.session_token = session_token
        Config.update_json("session_token", session_token)

    @staticmethod
    def setup_config_file_path() -> str:
        config_dir = user_config_dir(APP_NAME)
        if OsUtils.is_windows:
            # On windows it resolves the config directory to Sengpt/Sengpt
            config_dir = os.path.dirname(config_dir)
        mkdir(config_dir)
        return os.path.join(config_dir, "config.json")

    @staticmethod
    def info() -> str:
        with open(Config.file_path, "r") as f:
            return f"{f.read()}\n\nConfig file location: {Config.file_path}"

    @staticmethod
    def update_json(key: str, value: str | None | bool) -> None:
        Config.json[key] = value
        Config.dump()

    @staticmethod
    async def update_json_async(key: str, value: str | None | bool) -> None:
        Config.update_json(key, value)

    @staticmethod
    def dump() -> None:
        with open(Config.file_path, "w") as f:
            json.dump(Config.json, f, indent=4)

    @staticmethod
    def get_from_json_config(
        key: str, default: T, json_config: dict[str, Any]
    ) -> T | NoReturn:
        value = json_config.get(key, default)
        val_type = type(value)
        def_type = type(default)
        if val_type == def_type:
            return value
        print(
            f'Error loading config: Expected value at "{key}" to be of type {def_type} but instead got "{value}" which is of type {val_type}'
        )
        sys.exit()

    @staticmethod
    def load_json_config(
        config_file_path: str,
    ) -> NoReturn | dict[str, Any]:
        try:
            with open(config_file_path) as f:
                contents = f.read()
                try:
                    return json.loads(contents)
                except json.JSONDecodeError:
                    last_2_chars = contents.replace(" ", "").replace("\n", "")[-2:]
                    info_to_add = (
                        '\nRemove the "," before the last "}"'
                        if ",}" == last_2_chars
                        else ""
                    )
                    check_repo_print(
                        f'Your config file at: "{config_file_path}" is invalid!!!{info_to_add}'
                    )
        except FileNotFoundError:
            pass
        return {}  # This is here instead of in the except block to avoid type errors

    file_path = setup_config_file_path()

    json = load_json_config(file_path)
    username = get_from_json_config("username", "You", json)
    session_token = get_from_json_config("session_token", "", json)
    model = get_from_json_config("model", "gpt-3.5", json)
    recent_conversation_id = get_from_json_config("recent_conversation_id", "", json)
    preconfigured_prompts = get_from_json_config("preconfigured_prompts", {}, json)
    no_glow = get_from_json_config("no_glow", False, json)
    save = get_from_json_config("save", False, json)
    delete = get_from_json_config("delete", False, json)
    copy = get_from_json_config("copy", False, json)
    default_mode = get_from_json_config("default_mode", "interactive", json)

