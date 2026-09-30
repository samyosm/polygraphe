"""Operator sessions: whoever knows the operator password may control trials.

Tokens are stateless, ``<expiry>.<signature>``, signed with HMAC-SHA256: nothing to store,
and changing the secret key revokes every session.
"""

import hashlib
import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.domain.measurement import utc_now


@dataclass(frozen=True, slots=True)
class OperatorSession:
    token: str
    expires_at: datetime


class OperatorAuth:
    def __init__(
        self,
        password: str,
        secret_key: str,
        lifetime: timedelta,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._password = password.encode()
        self._key = secret_key.encode()
        self._lifetime = lifetime
        self._clock = clock

    def sign_in(self, password: str) -> OperatorSession | None:
        """A new session if ``password`` is right, None otherwise."""
        if not secrets.compare_digest(password.encode(), self._password):
            return None
        expires_at = self._clock() + self._lifetime
        expiry = str(int(expires_at.timestamp()))
        return OperatorSession(f"{expiry}.{self._sign(expiry)}", expires_at)

    def verify(self, token: str) -> bool:
        expiry, _, signature = token.partition(".")
        if not expiry.isdigit() or not secrets.compare_digest(signature, self._sign(expiry)):
            return False
        return datetime.fromtimestamp(int(expiry), UTC) > self._clock()

    def _sign(self, payload: str) -> str:
        return hmac.new(self._key, payload.encode(), hashlib.sha256).hexdigest()
