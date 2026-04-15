"""JWT authentication, password hashing, and rate limiting.

Provides security utilities for the Agricultural AI Platform including
token-based authentication via OAuth2 and a simple in-memory rate limiter.
"""

import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import Settings, get_settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# OAuth2 scheme
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Token(BaseModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded inside a JWT."""

    sub: Optional[str] = None
    exp: Optional[datetime] = None


class UserInDB(BaseModel):
    """User representation stored in the database."""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    hashed_password: str


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Return the bcrypt hash of *password*."""
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_access_token(
    data: dict,
    settings: Optional[Settings] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to encode in the token (must include ``sub``).
        settings: Application settings; uses cached settings when *None*.
        expires_delta: Custom expiry duration. Falls back to config default.

    Returns:
        Encoded JWT string.
    """
    settings = settings or get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.jwt_expiration_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_access_token(token: str, settings: Optional[Settings] = None) -> TokenData:
    """Decode and validate a JWT access token.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    settings = settings or get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        sub: Optional[str] = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return TokenData(sub=sub, exp=payload.get("exp"))
    except JWTError:
        raise credentials_exception


# ---------------------------------------------------------------------------
# FastAPI dependency – current user
# ---------------------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> TokenData:
    """FastAPI dependency that extracts and validates the current user from a JWT.

    Returns:
        TokenData with the authenticated user's identity.
    """
    return verify_access_token(token, settings)


# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per-client)
# ---------------------------------------------------------------------------
class RateLimiter:
    """Simple sliding-window rate limiter backed by an in-memory dictionary.

    Intended for single-process deployments or as a lightweight fallback.
    For distributed rate limiting, use Redis-backed alternatives.

    Args:
        requests_per_minute: Maximum allowed requests per 60-second window.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.rpm = requests_per_minute
        self._window: int = 60  # seconds
        self._clients: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    # Periodic cleanup -------------------------------------------------------
    def _cleanup(self) -> None:
        """Remove expired timestamps from all clients."""
        cutoff = time.monotonic() - self._window
        with self._lock:
            for client_id in list(self._clients):
                self._clients[client_id] = [
                    ts for ts in self._clients[client_id] if ts > cutoff
                ]
                if not self._clients[client_id]:
                    del self._clients[client_id]

    # Public API -------------------------------------------------------------
    def is_allowed(self, client_id: str) -> bool:
        """Return *True* if the client has not exceeded the rate limit."""
        now = time.monotonic()
        cutoff = now - self._window

        with self._lock:
            timestamps = self._clients.setdefault(client_id, [])
            # Prune expired entries for this client
            timestamps[:] = [ts for ts in timestamps if ts > cutoff]

            if len(timestamps) >= self.rpm:
                return False

            timestamps.append(now)
            return True

    def check(self, client_id: str) -> None:
        """Raise an HTTPException if the client has exceeded the rate limit."""
        if not self.is_allowed(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
