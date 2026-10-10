"""
Install:  pip install fastapi uvicorn pyjwt bcrypt "pydantic[email]"
Run:      JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(64))") \
          uvicorn auth:app --reload
Env vars:
  JWT_SECRET      (required) long random string
  COOKIE_SECURE   "true" (default) / "false" -> set false ONLY for local http dev
"""
from fastapi import HTTPException, status, Response
import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

# ---------- config ----------
SECRET_KEY = os.environ.get("JWT_SECRET")
ALGORITHM = os.environ.get("ALGORITHM")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET env var is required")

ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=7)
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


# ---------- password helpers ----------
def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())


def verify_password(pw: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed)


# ---------- token helpers ----------
def create_token(user_id: str, token_type: str, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if payload.get("type") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    return payload


# ---------- cookie helpers ----------
def set_auth_cookies(response: Response, user_id: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        create_token(user_id, "access", ACCESS_TTL),
        max_age=int(ACCESS_TTL.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    # Refresh cookie only sent to /auth/* endpoints
    response.set_cookie(
        REFRESH_COOKIE,
        create_token(user_id, "refresh", REFRESH_TTL),
        max_age=int(REFRESH_TTL.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/auth")