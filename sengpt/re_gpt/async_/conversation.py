import asyncio
from typing import AsyncGenerator
import uuid
from typing import (
    Any,
)

from .arkose_manager import ArkoseManager
from ..utils import (
    CONVERSATION_ENTRYPOINT,
    decode_json_from_string,
)
from ..models import ModelsWrapper, Model
from ..prompt_response_chunk import PromptResponseChunk

from ..errors import (
    InvalidConversationID,
    InvalidSessionToken,
    NoResponseChunksReceived,
    UnexpectedJsonFormat,
)

from typing import TYPE_CHECKING

# To avoid circular imports errors
# https://stackoverflow.com/a/39757388/17193072
if TYPE_CHECKING:
    from .chatgpt import ChatGPT


class Conversation:
    def __init__(
        self,
        chatgpt: "ChatGPT",
        id: str | None = None,
        model=ModelsWrapper.gpt_3_5,
    ):
        self.chatgpt = chatgpt
        self.id = id
        self.parent_id: str | None = None
        self.model = model

    async def prompt(
        self, prompt_text: str
    ) -> AsyncGenerator[PromptResponseChunk, None]:
        """
        Prompt ChatGPT.
        @prompt_text: Text to prompt with.
        @returns: An asynchronous generator object that yields chatgpt's response as `PromptResponseChunk` s.
        @raises:
        - `UnexpectedJsonFormat` - if the JSON reponse is invalid.
        - `NoResponseChunksReceived` - if no response was received from the server.
        - `InvalidConversationID` - if the configured conversation id is invalid.

        @example::

            session_token = "__Secure-next-auth.session-token here"
            async with ChatGPT(session_token=session_token) as chatgpt:
                prompt_message = input("Enter your prompt: ")
                conversation = chatgpt.new_conversation()
                async for prompt_response_chunk in conversation.prompt(prompt_message):
                    print(prompt_response_chunk.content, flush=True, end="")
        """
        payload = await self._message_payload(prompt_text)
        # To store what the server returned for debugging in case of an error
        complete_server_response = ""
        got_response = False
        is_cut_off = False
        prev_chunk_resp_length = 0
        while True:
            async for chunk in self._fetch_response(payload):
                decoded_chunk = chunk.decode()
                complete_server_response += decoded_chunk
                (
                    prompt_response_chunks,
                    is_cut_off,
                ) = Conversation._process_decoded_chunk(decoded_chunk)
                if prompt_response_chunks:
                    prev_chunk_resp_length = (
                        Conversation._process_message_chunks_content(
                            prev_chunk_resp_length, prompt_response_chunks
                        )
                    )
                    self.id = prompt_response_chunks[-1].conversation_id
                    self.parent_id = prompt_response_chunks[-1].parent_id
                    got_response = True
                    for prc in prompt_response_chunks:
                        yield prc
            if not got_response:
                if "Your authentication token has expired" in complete_server_response:
                    raise InvalidSessionToken()
                raise NoResponseChunksReceived(complete_server_response)
            if is_cut_off:
                payload = await self._message_continuation_payload()
            else:
                break

    async def delete(self) -> None:
        """
        Deletes the conversation.
        """
        if self.id:
            await self.chatgpt.delete_conversation(self.id)
            self.id = None
            self.parent_id = None

    async def _configure_conversation(self) -> None:
        if not self.id:
            return
        url = Conversation._conversation_endpoint(self.id)
        response = await self.chatgpt.session.get(
            url=url, headers=self.chatgpt._request_headers()
        )
        conversation: dict[str, Any] = {}
        response_str = ""
        try:
            conversation = response.json()
            response_str = str(conversation)
            if (
                "Can't load conversation" in response_str
                or "Invalid conversation" in response_str
            ):
                raise InvalidConversationID(self.id)
            chat_mapping = conversation["mapping"]
            self.parent_id = list(chat_mapping.keys())[-1]
            self.model = Model.from_chat_mapping(chat_mapping)
        except Exception as e:
            if isinstance(e, InvalidConversationID):
                raise
            if "Your authentication token has expired" in response_str:
                raise InvalidSessionToken()
            raise UnexpectedJsonFormat("mapping", conversation)

    @staticmethod
    def _conversation_endpoint(conversation_id: str) -> str:
        return f"{CONVERSATION_ENTRYPOINT}/{conversation_id}"

    @staticmethod
    def _process_decoded_chunk(
        decoded_chunk: str,
    ) -> tuple[list[PromptResponseChunk], bool]:
        message_chunks: list[PromptResponseChunk] = []
        is_cut_off = False
        for line in decoded_chunk.splitlines():
            if not line.startswith("data: "):
                continue
            json_string = line[6:]
            decoded_json = decode_json_from_string(json_string)
            if result := PromptResponseChunk._from_decoded_json(decoded_json):
                (message_chunk, is_cut_off) = result
                message_chunks.append(message_chunk)
        return message_chunks, is_cut_off

    @staticmethod
    def _process_message_chunks_content(
        prev_chunk_resp_length: int, prompt_response_chunk: list[PromptResponseChunk]
    ) -> int:
        for prc in prompt_response_chunk:
            prev_chunk_resp_length, prc.content = (
                len(prc.content),
                prc.content[prev_chunk_resp_length:],
            )
        return prev_chunk_resp_length

    async def _fetch_response(
        self, payload: dict[str, Any]
    ) -> AsyncGenerator[bytes, None]:
        """
        Send a message payload to the server and receive the response.
        @param payload: Payload containing message information.
        @returns: A generator that yields the chunks of data received as a response.
        """
        response_queue = asyncio.Queue()

        async def perform_request():
            def enqueue_chunk(chunk: bytes):
                response_queue.put_nowait(chunk)

            headers = self.chatgpt._request_headers()
            await self.chatgpt.session.post(
                url=CONVERSATION_ENTRYPOINT,
                headers=headers,
                json=payload,
                content_callback=enqueue_chunk,
            )
            await response_queue.put(None)

        asyncio.create_task(perform_request())

        while chunk := await response_queue.get():
            yield chunk

    async def _message_payload(self, user_input: str) -> dict[str, Any]:
        payload = await self._generate_common_payload("next", user_input)
        return payload

    async def _message_continuation_payload(self) -> dict[str, Any]:
        payload = await self._generate_common_payload("continue", "")
        payload["timezone_offset_min"] = -300
        return payload

    async def _generate_common_payload(
        self, action: str, user_input: str
    ) -> dict[str, Any]:
        await self._configure_conversation()
        common_payload = {
            "conversation_mode": {"conversation_mode": {"kind": "primary_assistant"}},
            "conversation_id": self.id,
            "action": action,
            "arkose_token": await self._generate_arkose_token(),
            "force_paragen": False,
            "history_and_training_disabled": False,
            "model": self.model.slug,
            "parent_message_id": str(uuid.uuid4())
            if not self.parent_id
            else self.parent_id,
        }

        if action == "next":
            common_payload["messages"] = [
                {
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": [user_input]},
                    "id": str(uuid.uuid4()),
                    "metadata": {},
                }
            ]

        return common_payload

    async def _generate_arkose_token(self) -> str | None:
        if self.model.needs_arkose_token or self.chatgpt.should_generate_arkose_token:
            return await ArkoseManager.generate_arkose_token(self.chatgpt.session)

