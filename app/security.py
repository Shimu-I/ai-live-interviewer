"""
Minimal, self-contained auth: password hashing + JWT session cookies.
No external auth provider — keeps the whole stack Python and dependency-light.

Uses the `bcrypt` library directly rather than going through `passlib`.
`passlib` is unmaintained and its bcrypt backend runs an internal self-test
that crashes on bcrypt 4.1+ (AttributeError: module 'bcrypt' has no attribute
'__about__'). Calling bcrypt's own hashpw/checkpw avoids that entirely.
"""
from datetime import datetime, timedelta

import bcrypt
import jwt

from app.config import settings

# bcrypt only uses the first 72 bytes of a password; truncate defensively so
# very long passwords don't raise instead of just being (safely) truncated.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    truncated = plain.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(truncated, hashed.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
