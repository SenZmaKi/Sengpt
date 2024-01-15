from typing import Any


class TokenNotProvided(Exception):
    def __init__(self):
        self.message = "Token not provided. Please pass your '__Secure-next-auth.session-token' as an argument (e.g., ChatGPT.init(session_token=YOUR_TOKEN))."
        super().__init__(self.message)


class InvalidSessionToken(Exception):
    def __init__(self):
        self.message = "Invalid session token provided."
        super().__init__(self.message)


class RetryError(Exception):
    def __init__(self, website: str, message="Exceeded maximum retries"):
        self.website = website
        self.message = f"{message} for website: {website}"
        super().__init__(self.message)


class BackendError(Exception):
    def __init__(self, error_code: int):
        self.error_code = error_code
        self.message = f"An unexpected error occurred on the backend. Error code: {self.error_code}"
        super().__init__(self.message)


class UnexpectedError(Exception):
    def __init__(self, original_exception: Exception, server_response: str):
        self.original_exception = original_exception
        self.server_response = server_response
        self.message = f"An unexpected error occurred.\nError message: {self.original_exception}.\nThe server returned: {self.server_response}."
        super().__init__(self.message)


class UnexpectedJsonFormat(Exception):
    def __init__(self, expected_field: str, json: dict[str, Any]) -> None:
        self.json = json
        self.expected_field = expected_field
        self.message = f"Expected field: {expected_field} in \n{json}"
        super().__init__(self.message)

class InvalidConversationID(Exception):
    def __init__(self, id: str) -> None:
        self.message = f"\"{id}\" is not a valid conversation id"
        super().__init__(self.message)

class NoResponseChunksReceived(Exception):
    def __init__(self, server_response: str) -> None:
        self.message = f"Expected chunks of data from the server but instead got: \n{server_response}"
        self.server_response = server_response
        super().__init__(self.message)

