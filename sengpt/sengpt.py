import asyncio
from typing import NoReturn, cast
from curl_cffi.requests.errors import RequestsError
from curl_cffi.requests.session import AsyncSession
from .re_gpt.async_.conversation import Conversation
from .re_gpt.models import Model
from .re_gpt.async_.chatgpt import ChatGPT
from .re_gpt.errors import InvalidSessionToken
import sys
import subprocess
from .utils import (
    REPO_TAGS_URL,
    GLOW_INSTALLATION_URL,
    V_VERSION,
    OsUtils,
    check_repo_print,
)
from .config import Config
from .argparser import ArgParser, SYS_ARGS
import pyperclip
import os

PRINT_WITH_GLOW = not (SYS_ARGS.is_set("no_glow") or Config.no_glow)
# isatty == is a teletypewriter == is a terminal == program invoked without piping input
INPUT_WAS_PIPED = not sys.stdin.isatty()
IS_QUERY_MODE = (
    SYS_ARGS.is_set("query")
    # Couldn't find a way to get piped inputs to work together with normal user inputs
    # cause stdin gets set to the piped input and but I couldn't find a way to set it to the terminal stdin
    or INPUT_WAS_PIPED
    or (Config.default_mode == "query" and not SYS_ARGS.is_set("interactive"))
)


def input_handler(msg: str) -> str:
    try:
        user_input = input(msg)
    except EOFError:  # When they press Ctrl + C while input is "waiting"
        print()  # Move out of the msg line onto the next line
        user_input = ""
    return user_input


def while_throws_errors(commands: tuple[str, ...]) -> bool:
    for c in commands:
        try:
            subprocess.run(c)
            return True
        except Exception:  # I can't be asked to catch all the specific errors that can arise from these commands
            continue
    return False


def try_installing_glow() -> bool:
    if OsUtils.is_windows:
        return while_throws_errors(
            (
                "winget install charmbracelet.glow",
                "choco install glow",
                "scoop install glow",
            )
        )
    elif OsUtils.is_linux:
        return while_throws_errors(
            (
                'sudo mkdir -p /etc/apt/keyrings && curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg && echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list && sudo apt update && sudo apt install glow',
                "pacman -S glow",
                "xbps-install -S glow",
                "nix-env -iA nixpkgs.glow",
                "pkg install glow",
                "eopkg install glow",
            )
        )
    return while_throws_errors(("brew install glow", "sudo port install glow"))


def get_piped_input() -> str:
    if not INPUT_WAS_PIPED:
        return ""
    full_input = ""
    try:
        while True:
            full_input = f"{full_input}\n{input()}"
    except EOFError:
        pass
    return full_input


def generate_prompt(args: ArgParser) -> str:
    args_prompt = " ".join(args.non_args)
    if args_prompt:
        args_prompt = f"{args_prompt}"
    preconfigured_prompt = " ".join(
        value for key, value in Config.preconfigured_prompts.items() if args.is_set(key)
    )
    if preconfigured_prompt:
        preconfigured_prompt = f"{preconfigured_prompt}\n\n"
    clipboard_text = f"{pyperclip.paste()}" if args.is_set("paste") else ""
    if clipboard_text:
        clipboard_text = f"{clipboard_text}\n\n"
    passed_input = get_piped_input() if IS_QUERY_MODE else ""
    passed_input = f"{passed_input}\n\n" if passed_input else ""
    return f"{passed_input}{clipboard_text}{preconfigured_prompt}{args_prompt}"


async def loading_animation(event: asyncio.Event) -> None:
    animation = (".   ", "..  ", ".. .", "    ")
    while not event.is_set():
        for a in animation:
            print(f"  Thinking {a}", end="\r")
            await asyncio.sleep(0.1)
    print(" " * (len("Thinking") + 8), end="\r")


def printer(text: str) -> None:
    if PRINT_WITH_GLOW:
        return glow_print(text)
    print(text)


def glow_print(text: str) -> None:
    try:
        subprocess.run("glow", input=text.encode())
    except FileNotFoundError:
        print("Glow is required to pretty print output!!!")
        user_choice = input_handler("Would you like to install it? [y/n]\n> ").lower()
        if user_choice == "y" or user_choice == "yes":
            installation_was_succesful = try_installing_glow()
            if installation_was_succesful:
                return glow_print(text)
            print("Automatic installation failed X(")
        print(
            f'Check {GLOW_INSTALLATION_URL} for an installation guide\nAlternatively you can set "no_glow" to true in your config file or pass the --no_glow flag to the program'
        )
        os._exit(
            1
        )  # os._exit instead of sys.exit to avoid asyncio errors leaking cause running tasks don't respect sys.exit


def load_conversation(gpt: ChatGPT) -> tuple[Conversation, bool]:
    conversation_id = (
        Config.recent_conversation_id
        if SYS_ARGS.is_set("recent_conversation")
        else None
    )
    if conversation_id == "":
        conversation_id = None

    conversation = gpt.new_conversation(
        model=Model.from_name(Config.model), id=conversation_id
    )
    save_conversation = (
        conversation_id is not None or Config.save or SYS_ARGS.is_set("save")
    )
    return conversation, save_conversation


async def fetch_prompt_response(prompt: str, conversation: Conversation) -> str:
    prompt_response = ""
    event = asyncio.Event()
    loading_task = asyncio.create_task(loading_animation(event))
    async for prc in conversation.prompt(prompt):
        if PRINT_WITH_GLOW:
            prompt_response += prc.content
            continue
        if not event.is_set():
            event.set()
            await loading_task
        print(prc.content, end="", flush=True)
    if PRINT_WITH_GLOW:
        event.set()
        await loading_task
    return prompt_response


async def interactive_mode(
    args: ArgParser,
    conversation: Conversation,
    is_first_iteration=True,
) -> None:
    if is_first_iteration:
        prompt = prepare_prompt(args)
    else:
        prompt = generate_prompt(args)
        printer("\n# ChatGPT")
    prompt_response = await fetch_prompt_response(prompt, conversation)
    printer(f"{prompt_response}\n\n# {Config.username}")
    handle_coping_to_clip(args, prompt_response)
    if user_input := input_handler("> "):
        if user_input == "-d" or user_input == "--delete":
            return await conversation.delete()
        return await interactive_mode(
            ArgParser(user_input.split(" ")), conversation, False
        )
    if Config.delete:
        return await conversation.delete()
    await Config.update_json_async("recent_conversation_id", conversation.id)


def handle_coping_to_clip(args: ArgParser, prompt_response: str) -> None:
    if args.is_set("copy") or Config.copy:
        pyperclip.copy(prompt_response)


def prepare_prompt(args: ArgParser) -> str:
    prompt = generate_prompt(args)
    preprompt_text = f"# {Config.username}\n{prompt}\n\n# ChatGPT\n"
    printer(preprompt_text)
    return prompt


async def query_mode(
    args: ArgParser, conversation: Conversation, save_conversation: bool
) -> None:
    prompt = prepare_prompt(args)
    prompt_response = await fetch_prompt_response(prompt, conversation)
    if save_conversation:
        Config.recent_conversation_id = cast(str, conversation.id)
        task = asyncio.create_task(
            Config.update_json_async("recent_conversation_id", conversation.id)
        )
    else:
        task = asyncio.create_task(conversation.delete())
    printer(prompt_response)
    handle_coping_to_clip(args, prompt_response)
    await task


async def gpt_coroutine(session: AsyncSession) -> None:
    gpt = ChatGPT(session, Config.session_token)
    try:
        async with gpt:
            conversation, save_conversation = load_conversation(gpt)
            if IS_QUERY_MODE:
                return await query_mode(SYS_ARGS, conversation, save_conversation)
            await interactive_mode(SYS_ARGS, conversation)

    except InvalidSessionToken:
        check_repo_print(
            "Invalid session token, the current one may have expired you need to make a new one"
        )


async def update_check_coroutine(session: AsyncSession) -> bool:
    response = await session.get(REPO_TAGS_URL)
    tags = response.json()
    # Incase I delete all tags for whatever reason or the repo gets taken down
    if not tags or not isinstance(tags, list):
        return False
    latest_tag = tags[0]
    if latest_tag["name"] != V_VERSION:
        return True
    return False


async def async_main() -> None:
    session = AsyncSession(impersonate="chrome110")
    try:
        _, update_is_available = await asyncio.gather(
            gpt_coroutine(session), update_check_coroutine(session)
        )
        if update_is_available:
            print('\n\nUpdate available run "pip update sengpt" to install it')
    except RequestsError:
        print("Check your internet!!!")


def validate_session_token() -> None | NoReturn:
    if not Config.session_token:
        check_repo_print("Session token must be provided during initial configuration")


def handle_static_args() -> None | NoReturn:
    if SYS_ARGS.is_set("version"):
        print(ArgParser.version_info())
        sys.exit()
    if SYS_ARGS.is_set("help"):
        print(ArgParser.help_info())
        sys.exit()
    if SYS_ARGS.is_set("config_file"):
        print(Config.info())
        sys.exit()
    if SYS_ARGS.is_set("session_token"):
        Config.update_session_token()
        print("\nSuccessfully set session token")
        sys.exit()


def main():
    handle_static_args()
    validate_session_token()
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()

