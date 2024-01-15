
from curl_cffi.requests.session import AsyncSession

from sengpt.re_gpt.async_.arkose_manager import ArkoseManager
from ..utils import OsUtils
from ..test_utils import (
    GPT_PROMPT,
    IGNORE_ARKOSE,
    SESSION_TOKEN,
    fancy_shmansy_print,
    CONVERSATION_ID,
)

from .chatgpt import ChatGPT
from .conversation import Conversation
import asyncio
import sys
import os
import pytest

# working dir reverse-engineered-chatgpt
# command: pytest re_gpt/async_/test.py
# remember to install testing modules first pip install -r dev-requirements.txt

if sys.version_info >= (3, 8) and OsUtils.is_windows:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def gpt(should_generate_arkose_token=False) -> ChatGPT:
    return ChatGPT(
        AsyncSession(impersonate="chrome110"),
        session_token=SESSION_TOKEN,
        should_generate_arkose_token=should_generate_arkose_token,
    )


@pytest.mark.asyncio
async def test_new_conversation(
    delete_convo=True, should_generate_arkose_token=False
) -> tuple[Conversation, ChatGPT]:
    g = gpt(should_generate_arkose_token)
    convo = g.new_conversation()
    async with g:
        async for m in convo.prompt(GPT_PROMPT):
            if delete_convo:
                fancy_shmansy_print(m.content)
                await convo.delete()
    return convo, g


@pytest.mark.asyncio
async def test_load_conversation(
    conversation_id=CONVERSATION_ID,
) -> None:
    g: ChatGPT | None = None
    if not conversation_id:
        convo, g = await test_new_conversation(False)
        conversation_id = convo.id
    if g is None:
        g = gpt()
    async with g:
        convo = g.new_conversation(conversation_id)
        async for m in convo.prompt(GPT_PROMPT):
            fancy_shmansy_print(m.content)
        if not CONVERSATION_ID:  # This means we created the conversation
            await convo.delete()


@pytest.mark.asyncio
async def test_set_custom_instructions() -> None:
    async with gpt() as g:
        response = await g.set_custom_instructions(
            "Refer to me as amogus", "Refer to yourself as sugoma"
        )
        print(response)


@pytest.mark.asyncio
async def test_retrieve_chats() -> None:
    async with gpt() as g:
        chats = await g.retrieve_chats()
        print(chats)


@pytest.mark.asyncio
@pytest.mark.skipif(IGNORE_ARKOSE == "True", reason="IGNORE_ARKOSE is set to True")
async def test_arkose() -> None:
    if os.path.isfile(ArkoseManager.binary_file_path):
        os.unlink(ArkoseManager.binary_file_path)
    if os.path.isdir(ArkoseManager.binary_folder_path):
        os.rmdir(ArkoseManager.binary_folder_path)
    await test_new_conversation(should_generate_arkose_token=True)

