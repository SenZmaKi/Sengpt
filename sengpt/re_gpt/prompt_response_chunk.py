from typing import Any


class PromptResponseChunk:
    """
    A ChatGPT prompt response chunk
    """

    def __init__(
        self,
        content: str,
        message_id: str,
        parent_id: str,
        conversation_id: str,
    ) -> None:
        self.content = content
        self.message_id = message_id
        self.parent_id = parent_id
        self.conversation_id = conversation_id

    @staticmethod
    def collect(prompt_response_chunks: list["PromptResponseChunk"]) -> str:
        """
        Collect a list of `PromptResponseChunk` s into a string by concatenating the `content`.
        """
        return "".join([str(prc) for prc in prompt_response_chunks])

    def __str__(self) -> str:
        return self.content

    @staticmethod
    def _from_decoded_json(
        decoded_json: dict[str, Any] | None,
    ) -> tuple["PromptResponseChunk", bool] | None:
        if decoded_json is None:
            return None
        message = decoded_json.get("message", None)
        if not message or message["author"]["role"] != "assistant":
            return None
        content = message["content"]["parts"][0]
        metadata = message["metadata"]
        parent_id = metadata["parent_id"]
        finish_details = metadata.get("finish_details", None)
        message_id = message["id"]
        conversation_id = decoded_json["conversation_id"]
        is_cut_off = (
            True
            if finish_details is not None and finish_details["type"] == "max_tokens"
            else False
        )
        prc = PromptResponseChunk(
            content,
            message_id,
            parent_id,
            conversation_id,
        )
        return (prc, is_cut_off)

