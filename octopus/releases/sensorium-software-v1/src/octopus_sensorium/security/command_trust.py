"""Command-trust verify (Ed25519). Private keys never live on the board."""

from __future__ import annotations

import base64
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from octopus_sensorium.verify import SignatureError, content_hash, load_root_public_key

TRUST_DIR = pathlib.Path("/etc/octopus/trust")
BOUND_PATH = TRUST_DIR / "command_trust.json"
COMMAND_PUB_PATH = TRUST_DIR / "command.pub"

# Fields covered by the signature (exclude signature itself).
CANONICAL_FIELDS = (
    "sender_id",
    "role",
    "permission",
    "timestamp",
    "expiry",
    "nonce",
    "command",
    "request_id",
    "params",
)


def is_bound() -> bool:
    if not BOUND_PATH.exists():
        return False
    try:
        doc = json.loads(BOUND_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(doc.get("bound") is True)


def load_command_public_key() -> bytes:
    """Prefer command.pub; fall back to root.pub when binding says so."""
    if COMMAND_PUB_PATH.exists():
        data = COMMAND_PUB_PATH.read_bytes()
        if len(data) != 32:
            raise SignatureError(f"command.pub must be 32 raw bytes, got {len(data)}")
        return data
    return load_root_public_key()


def canonical_command_bytes(body: dict[str, Any]) -> bytes:
    payload: dict[str, Any] = {}
    for key in CANONICAL_FIELDS:
        if key == "request_id":
            payload[key] = body.get("request_id") or body.get("nonce") or ""
        elif key == "params":
            params = body.get("params") if isinstance(body.get("params"), dict) else {}
            payload[key] = params
        else:
            payload[key] = body.get(key, "")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _decode_signature(value: str | bytes) -> bytes:
    if isinstance(value, bytes):
        raw = value
    else:
        text = str(value).strip()
        if text.startswith("b64:"):
            raw = base64.b64decode(text[4:])
        elif text.startswith("hex:"):
            raw = bytes.fromhex(text[4:])
        else:
            # try base64 then hex
            try:
                raw = base64.b64decode(text, validate=True)
            except Exception:
                try:
                    raw = bytes.fromhex(text)
                except Exception as exc:
                    raise SignatureError("signature must be b64/hex of 64 raw bytes") from exc
    if len(raw) != 64:
        raise SignatureError(f"signature must be 64 raw bytes, got {len(raw)}")
    return raw


def _expiry_ok(body: dict[str, Any]) -> bool:
    try:
        raw = str(body.get("expiry") or "").strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        exp = datetime.fromisoformat(raw)
    except Exception:
        return False
    if exp.tzinfo is None:
        return False
    return datetime.now(timezone.utc) <= exp


def verify_command(body: dict[str, Any]) -> str:
    """Return VERIFIED or raise SignatureError / return status string for handler."""
    if not is_bound():
        return "UNVERIFIED_NO_COMMAND_TRUST_ROOT"
    if not _expiry_ok(body):
        raise SignatureError("command_expired")
    pub = load_command_public_key()
    sig = _decode_signature(body.get("signature") or "")
    msg = canonical_command_bytes(body)
    try:
        VerifyKey(pub).verify(msg, sig)
    except BadSignatureError as exc:
        raise SignatureError("command_signature_invalid") from exc
    return "VERIFIED"


def binding_info() -> dict[str, Any]:
    if not BOUND_PATH.exists():
        return {"bound": False}
    try:
        return json.loads(BOUND_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"bound": False, "error": "unreadable"}
