from typing import (
    Callable,
    Self,
    Awaitable,
    cast,
    Any,
)

from curl_cffi.requests import AsyncSession

from ..utils import (
    CUSTOM_INSTRUCTIONS_ENDPOINT,
    RETRIEVE_CHATS_ENDPOINT,
    USER_AGENT,
    AUTH_SESSION_ENDPOINT,
)
from ..errors import (
    InvalidSessionToken,
    TokenNotProvided,
)

from .conversation import Conversation
from ..models import ModelsWrapper


class ChatGPT:
    def __init__(
        self,
        session: AsyncSession,
        session_token: str | None = None,
        exit_callback: Callable[[Self], Awaitable[None]] | None = None,
        auth_token: str | None = None,
        should_generate_arkose_token=False,
    ):
        """
        @param session: An `AsyncSession`
        @param session_token: A valid session token.
        @param exit_callback: An asynchronous function to be called on exit, it must take in `ChatGPT` as a parameter.
        @param auth_token: A valid authentication token, this is automatically fetched using the `session_token` when `ChatGPT` is used in an `async with` block.
        @param should_generate_arkose_token: Toggle whether to generate and send arkose token in the prompt message payload.

        """
        self.session = session
        self.exit_callback = exit_callback
        self.arkose_token: str | None = None
        self.already_tried_downloading_binary = False
        self.should_generate_arkose_token = should_generate_arkose_token

        self.session_token = session_token
        self.auth_token = auth_token

    def new_conversation(
        self, id: str | None = None, model=ModelsWrapper.gpt_3_5
    ) -> Conversation:
        """
        Creates a new conversation. alias to `Conversation.__init__`.
        """
        return Conversation(self, id, model)

    async def set_custom_instructions(
        self,
        about_user="",
        about_model="",
        enable_for_new_chats: bool = True,
    ) -> dict[str, Any]:
        """
        Set custom instructions for ChatGPT.

        @param about_user: What would you like ChatGPT to know about you to provide better responses?
        @param about_model: How would you like ChatGPT to respond?
        @param enable_for_new_chats: Enable for new chats.
        @returns: Server response json.
        """
        data = {
            "about_user_message": about_user,
            "about_model_message": about_model,
            "enabled": enable_for_new_chats,
        }
        response = await self.session.post(
            url=CUSTOM_INSTRUCTIONS_ENDPOINT, headers=self._request_headers(), json=data
        )

        return response.json()

    async def retrieve_chats(self, offset=0, limit=28) -> dict[str, Any]:
        params = {
            "offset": offset,
            "limit": limit,
            "order": "updated",
        }
        response = await self.session.get(
            url=RETRIEVE_CHATS_ENDPOINT, params=params, headers=self._request_headers()
        )

        return response.json()

    async def delete_conversation(self, conversation_id: str) -> Any:
        """
        Delete a conversation.
        @param conversation_id: ID of the conversation to delete.
        @return: Server response json.
        """
        url = Conversation._conversation_endpoint(conversation_id)
        response = await self.session.patch(
            url=url, headers=self._request_headers(), json={"is_visible": False}
        )

        return response.json()

    async def __aenter__(self):
        if self.auth_token is None:
            if self.session_token is None:
                raise TokenNotProvided()
            self.auth_token = await self._fetch_auth_token()

        return self

    async def __aexit__(self, *_):
        try:
            if self.exit_callback:
                await self.exit_callback(self)
        finally:
            cast(AsyncSession, self.session).close()

    def _request_headers(self) -> dict[str, Any]:
        """
        Builds HTTP requests headers
        @return: Request headers
        """
        return {
            "User-Agent": USER_AGENT,
            "Accept": "text/event-stream",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}",
            "Origin": "https://chat.openai.com",
            "Alt-Used": "chat.openai.com",
            "Connection": "keep-alive",
        }

    async def _fetch_auth_token(self) -> str:
        """
        Fetches the authentication token for the session.
        @return: authentication token.
        @raise: @InvalidSessionToken If the session token is invalid.
        """
        cookies = {"__Secure-next-auth.session-token": self.session_token}

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Alt-Used": "chat.openai.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "Cookie": "; ".join(
                [
                    f"{cookie_key}={cookie_value}"
                    for cookie_key, cookie_value in cookies.items()
                ]
            ),
        }
        response = await self.session.get(url=AUTH_SESSION_ENDPOINT, headers=headers)
        response_json = response.json()
        accsss_token = response_json.get("accessToken", "")
        if not accsss_token:
            raise InvalidSessionToken()
        return accsss_token

