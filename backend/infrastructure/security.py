import hashlib
import hmac
import os
import secrets
import time
from collections import defaultdict

from fastapi import Request

from backend.config import TESTING

_LOGIN_HITS: dict[str, list[float]] = defaultdict(list)


def normalize_username(value: str) -> str:
    return (value or "").strip().lower()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(derived.hex(), hash_hex)


def issue_csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(24)
        request.session["csrf_token"] = token
    return token


def csrf_ok(request: Request, token: str | None) -> bool:
    expected = request.session.get("csrf_token") or ""
    given = token or ""
    if not expected or not given:
        return False
    return hmac.compare_digest(expected, given)


def login_limited(ip: str, *, max_hits: int = 8, window: int = 600) -> bool:
    if TESTING:
        return False
    now = time.time()
    hits = [t for t in _LOGIN_HITS[ip] if now - t < window]
    _LOGIN_HITS[ip] = hits
    if len(hits) >= max_hits:
        return True
    _LOGIN_HITS[ip].append(now)
    return False


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:80] or "unknown"
    return (request.client.host if request.client else "unknown")[:80]
