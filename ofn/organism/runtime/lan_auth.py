"""LAN token authentication. Token never belongs in URLs, argv, or logs."""
from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time
from pathlib import Path

TOKEN_HEADER = "X-Octopus-Token"
DEFAULT_TOKEN_FILE = Path("/etc/octopus/lan-token")
MIN_TOKEN_BYTES = 32
FAILURE_WINDOW_S = 60.0
FAILURE_BURST = 8
FAILURE_COOLDOWN_S = 2.0

_CACHE_LOCK = threading.Lock()
_cached_token = ""
_cached_mtime = -1.0
_failures: dict[str, list[float]] = {}
_fail_lock = threading.Lock()


class LanTokenConfigError(RuntimeError):
    pass


def token_file_path() -> Path:
    raw = os.environ.get("OCTOPUS_LAN_TOKEN_FILE")
    if raw:
        return Path(raw)
    return DEFAULT_TOKEN_FILE


def lan_token_required() -> bool:
    return os.environ.get("OCTOPUS_REQUIRE_LAN_TOKEN", "0") == "1"


def _read_token_file(path: Path) -> str:
    if not path.is_file():
        return ""
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        raise LanTokenConfigError("lan_token_must_be_0600")
    text = path.read_text(encoding="utf-8").strip()
    if text.encode("utf-8").__len__() < MIN_TOKEN_BYTES:
        raise LanTokenConfigError("lan_token_too_short")
    return text


def load_lan_token() -> str:
    """Prefer file. OCTOPUS_LAN_TOKEN is test-only and must not be systemd Environment."""
    env = os.environ.get("OCTOPUS_LAN_TOKEN", "")
    if env:
        return env
    path = token_file_path()
    mtime = path.stat().st_mtime if path.is_file() else -1.0
    with _CACHE_LOCK:
        global _cached_token, _cached_mtime
        if mtime == _cached_mtime and _cached_token:
            return _cached_token
        token = _read_token_file(path) if path.is_file() else ""
        _cached_token = token
        _cached_mtime = mtime
        return token


def tokens_match(offered: str, expected: str) -> bool:
    offered_digest = hashlib.sha256(offered.encode("utf-8")).digest()
    expected_digest = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(offered_digest, expected_digest)


def failure_cooled(peer: str, now: float | None = None) -> bool:
    now = time.monotonic() if now is None else now
    with _fail_lock:
        stamps = [t for t in _failures.get(peer, []) if now - t <= FAILURE_WINDOW_S]
        _failures[peer] = stamps
        if len(stamps) >= FAILURE_BURST:
            return True
        if stamps and now - stamps[-1] < FAILURE_COOLDOWN_S:
            return True
        return False


def record_failure(peer: str, now: float | None = None) -> None:
    now = time.monotonic() if now is None else now
    with _fail_lock:
        _failures.setdefault(peer, []).append(now)


def record_success(peer: str) -> None:
    with _fail_lock:
        _failures.pop(peer, None)


def reset_failures_for_tests() -> None:
    with _fail_lock:
        _failures.clear()
    with _CACHE_LOCK:
        global _cached_token, _cached_mtime
        _cached_token = ""
        _cached_mtime = -1.0
