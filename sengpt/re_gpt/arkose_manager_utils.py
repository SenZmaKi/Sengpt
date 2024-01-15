import ctypes
import hashlib
from typing import Any

from .utils import ROOT_DIR, OsUtils
import os


# TODO: Properly support Mac
class ArkoseManagerUtils:
    """
    Arkose manager utility that's used in both sync and async
    """

    backup_token_generator_url = "https://arkose-token-generator.zaieem.repl.co/token"
    release_tag_name = "funcaptcha_bin"
    binary_folder_path = f"{ROOT_DIR}/{release_tag_name}"
    if OsUtils.is_windows:
        binary_file_name = "windows_arkose.dll"
    elif OsUtils.is_mac:
        binary_file_name = "mac_arkose.so"
    else:
        binary_file_name = "linux_arkose.so"
    binary_file_path = os.path.join(binary_folder_path, binary_file_name)
    arkose_dll: ctypes.CDLL | None = None

    @staticmethod
    def get_arkose_token() -> str | None:
        if ArkoseManagerUtils.arkose_dll is None:
            ArkoseManagerUtils.arkose_dll = ctypes.CDLL(
                ArkoseManagerUtils.binary_file_path
            )
            ArkoseManagerUtils.arkose_dll.GetToken.restype = ctypes.c_char_p
        result = ArkoseManagerUtils.arkose_dll.GetToken()
        return ctypes.string_at(result).decode()

    @staticmethod
    def calculate_binary_file_md5() -> str | None:
        if os.path.isfile(ArkoseManagerUtils.binary_file_path):
            with open(ArkoseManagerUtils.binary_file_path, "rb") as file:
                file_content = file.read()
                return hashlib.md5(file_content).hexdigest()

    @staticmethod
    def get_binary_download_url(releases: list[dict[str, Any]]) -> str | None:
        for rel in releases:
            if rel["tag_name"] == ArkoseManagerUtils.release_tag_name:
                for line in rel["body"].splitlines():
                    res = line.split("=")
                    if len(res) < 2:
                        continue
                    os_name, hash = res
                    if (
                        os_name == OsUtils.os_name
                        and hash != ArkoseManagerUtils.calculate_binary_file_md5()
                    ):
                        for asset in rel["assets"]:
                            if asset["name"] == ArkoseManagerUtils.binary_file_name:
                                return asset["browser_download_url"]
        return None

    @staticmethod
    def prepare_binary_folder():
        # Incase some weirdo has a file with the same name
        if os.path.isfile(ArkoseManagerUtils.binary_folder_path):
            os.unlink(ArkoseManagerUtils.binary_folder_path)
        if not os.path.exists(ArkoseManagerUtils.binary_folder_path):
            os.mkdir(ArkoseManagerUtils.binary_folder_path)

