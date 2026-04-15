"""Security utilities – JWT handling, password hashing, rate limiting, and input sanitisation."""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

# ── Password hashing ────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify *plain_password* against *hashed_password*."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT tokens ───────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenData(BaseModel):
    """Payload extracted from a verified JWT."""

    username: str
    exp: datetime


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    data:
        Claims to embed in the token (must include ``"sub"``).
    expires_delta:
        Custom lifetime.  Falls back to the configured
        ``jwt_expiry_minutes`` when *None*.
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.jwt_expiry_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str) -> TokenData:
    """Decode and validate a JWT, returning its :class:`TokenData`.

    Raises
    ------
    HTTPException
        If the token is invalid or expired.
    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        username: Optional[str] = payload.get("sub")
        exp_timestamp = payload.get("exp")
        if username is None or exp_timestamp is None:
            raise credentials_exception
        return TokenData(
            username=username,
            exp=datetime.fromtimestamp(exp_timestamp, tz=timezone.utc),
        )
    except JWTError as exc:
        raise credentials_exception from exc


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """FastAPI dependency that extracts and validates the current user from the JWT."""
    return verify_token(token)


# ── Rate limiting middleware (in-memory token bucket) ────────────────────────

class _TokenBucket:
    """Simple per-key token-bucket tracker."""

    __slots__ = ("capacity", "refill_rate", "_buckets")

    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self._buckets: dict[str, tuple[float, float]] = {}

    def allow(self, key: str) -> bool:
        """Return *True* if a request from *key* should be allowed."""
        now = time.monotonic()
        tokens, last = self._buckets.get(key, (float(self.capacity), now))
        elapsed = now - last
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)
        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, now)
            return True
        self._buckets[key] = (tokens, now)
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that enforces per-IP rate limiting."""

    def __init__(self, app: object) -> None:  # noqa: D401
        super().__init__(app)  # type: ignore[arg-type]
        settings = get_settings()
        capacity = settings.rate_limit_per_minute
        refill_rate = capacity / 60.0
        self._bucket = _TokenBucket(capacity=capacity, refill_rate=refill_rate)

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001, ANN201
        """Check the token bucket before forwarding the request."""
        client_ip = request.client.host if request.client else "unknown"
        if not self._bucket.allow(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)


# ── Input sanitisation ───────────────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SQL_INJECTION_RE = re.compile(
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION|TRUNCATE|"
    r"DECLARE|CAST|CONVERT|INTO|FROM|WHERE|OR|AND)\b\s+"
    r".*?(;|--|\*|=))",
    re.IGNORECASE,
)
_PROMPT_INJECTION_RE = re.compile(
    r"(ignore\s+(previous|above|all)\s+instructions"
    r"|you\s+are\s+now"
    r"|system\s*:\s*"
    r"|<\|im_start\|>"
    r"|<\|im_end\|>"
    r"|\[INST\]"
    r"|\[/INST\])",
    re.IGNORECASE,
)


def sanitize_input(text: str) -> str:
    """Strip HTML tags, SQL-injection patterns, and prompt-injection patterns.

    Parameters
    ----------
    text:
        Raw user-supplied text.

    Returns
    -------
    str
        Sanitised text safe for downstream processing.
    """
    text = _HTML_TAG_RE.sub("", text)
    text = _SQL_INJECTION_RE.sub("", text)
    text = _PROMPT_INJECTION_RE.sub("", text)
    # Collapse excess whitespace left after removals
    return " ".join(text.split())
