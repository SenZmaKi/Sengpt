from curl_cffi.curl import Any
from .errors import UnexpectedJsonFormat


class Model:
    def __init__(self, name: str, needs_arkose_token: bool, slug: str) -> None:
        self.name = name
        self.slug = slug
        self.needs_arkose_token = needs_arkose_token

    @staticmethod
    def from_chat_mapping(chat_mapping: dict[str, Any]) -> "Model":
        for mapping in chat_mapping.values():
            if message := mapping.get("message", None):
                role = message["author"]["role"]
                if role == "assistant":
                    slug = message["metadata"]["model_slug"]
                    for m in ModelsWrapper.models:
                        if m.slug == slug:
                            return m

        raise UnexpectedJsonFormat("model_slug", chat_mapping)

    @staticmethod
    def from_name(name: str) -> "Model":
        for m in ModelsWrapper.models:
            if m.name == name:
                return m
        raise InvalidModelName(name)


class ModelsWrapper:
    gpt_3_5 = Model("gpt-3.5", False, "text-davinci-002-render-sha")
    gpt_4 = Model("gpt-4", True, "gpt-4")
    models = (gpt_3_5, gpt_4)


# TODO: Move this to re_gpt/errors.py
class InvalidModelName(Exception):
    available_models = f"Available models: {[m.name for m in ModelsWrapper.models]}"

    def __init__(self, name: str):
        self.message = f'"{name}" is not a valid model. {self.available_models}'
        super().__init__(self.message)

