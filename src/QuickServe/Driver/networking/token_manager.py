import dataclasses
import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from collections import deque

if TYPE_CHECKING:
    from QuickServe.Database.users import UserModel
    from QuickServe.FileSystem.config import Config


@dataclasses.dataclass
class Token:
    user: "UserModel"
    token: str
    expiration: datetime
    consumed: bool = False

class WebsocketTokenManager:
    """
    Manages tokens for websocket authentication
    """
    _token_map: dict[str, "Token"]
    _token_list: deque["Token"]

    def __init__(self, config: "Config"):
        self._token_map = dict()
        self._token_list = deque()
        self.config_expiry: int = config.web.websocket_token_lifetime

    def generate_token(self, user: "UserModel") -> str:
        """
        Generates a new token
        :param user: The user to bind the token to.
        :return: The fresh token.
        """
        token = secrets.token_urlsafe(32)
        expiration = datetime.now() + timedelta(seconds=self.config_expiry)
        generated = Token(user=user, token=token, expiration=expiration)
        self._token_map[token] = generated
        self._token_list.append(generated)

        return token

    def get_user(self, token: str) -> "UserModel | None":
        """
        Gets a UserModel from the token
        :param token:
        :return:
        """
        tok = self._token_map.get(token)
        if tok is None:
            return None
        return tok.user

    def is_expired(self, token: str) -> bool:
        """
        Checks if a token is expired, or doesn't exist.
        :param token: The token to check
        :return: True if it is expired or not found, False if it is still valid.
        """
        tok = self._token_map.get(token)
        if tok is None:
            return True

        return datetime.now() > tok.expiration

    def get_unexpired_user(self, token: str) -> "UserModel | None":
        """
        Gets a user from a token, verifies that the token is not expired.
        :param token: The token to verify
        :return: the UserModel if the token is valid, else None.
        """
        if self.is_expired(token):
            return None

        return self.get_user(token)

    def consume_unexpired_user(self, token: str) -> "UserModel | None":
        """
        Gets a user from a token, verifies that the token is not expired, and is not consumed.
        :param token: The token to verify
        :return: the UserModel if the token is valid, and unconsumed, else None.
        """
        user = self.get_unexpired_user(token=token)
        if user is None:
            return None

        tok = self._token_map[token]
        if tok.consumed:
            return None
        tok.consumed = True
        return user


    def cleanup(self):
        while len(self._token_list) and self.is_expired(self._token_list[0].token):
            tok = self._token_list.popleft()
            self._token_map.pop(tok.token)