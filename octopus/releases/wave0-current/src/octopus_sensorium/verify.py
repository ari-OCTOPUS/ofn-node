"""Ed25519 verify-only loader. The agent never holds a signing key."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

TRUST_DIR = pathlib.Path("/etc/octopus/trust")
ROOT_PUB_PATH = TRUST_DIR / "root.pub"
REVOKED_PATH = TRUST_DIR / "revoked.json"


class SignatureError(Exception):
    pass


class ConfigValidityError(Exception):
    pass


def content_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _revoked_fingerprints(revoked: dict) -> set[str]:
    found = set(revoked.get("revoked_key_fingerprints") or [])
    extra = revoked.get("public_key_fingerprint")
    if extra:
        found.add(str(extra))
    return {str(item) for item in found if item}


def load_root_public_key(path: pathlib.Path = ROOT_PUB_PATH) -> bytes:
    data = path.read_bytes()
    if len(data) != 32:
        raise SignatureError(f"root.pub must be 32 raw bytes, got {len(data)}")
    revoked = load_revoked()
    fingerprint = content_hash(data)
    if fingerprint in _revoked_fingerprints(revoked):
        raise SignatureError(f"current root public key is revoked: {fingerprint}")
    return data


def load_revoked(path: pathlib.Path = REVOKED_PATH) -> dict:
    if not path.exists():
        return {"revoked_key_ids": [], "revoked_key_fingerprints": [], "revoked_config_hashes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_signed(path: pathlib.Path, pub: bytes) -> bytes:
    payload = path.read_bytes()
    signature = path.with_suffix(path.suffix + ".sig").read_bytes()
    if len(signature) != 64:
        raise SignatureError(f"signature must be 64 raw bytes, got {len(signature)}")
    digest = content_hash(payload)
    revoked = load_revoked()
    if digest in revoked.get("revoked_config_hashes", []):
        raise SignatureError(f"payload hash is revoked: {digest}")
    if content_hash(pub) in _revoked_fingerprints(revoked):
        raise SignatureError("signature public key is revoked")
    try:
        VerifyKey(pub).verify(payload, signature)
    except BadSignatureError as exc:
        raise SignatureError("Ed25519 signature verification failed") from exc
    return payload


def assert_validity_window(doc: dict, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    not_before = datetime.fromisoformat(doc["not_before"])
    not_after = datetime.fromisoformat(doc["not_after"])
    if not_before.tzinfo is None or not_after.tzinfo is None:
        raise ConfigValidityError("not_before/not_after must include timezone")
    if now < not_before:
        raise ConfigValidityError("config not yet valid")
    if now > not_after:
        raise ConfigValidityError("config expired")
