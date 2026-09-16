"""Owner-authorization verifier for tests and read-only Doctor.

Live Wave 0 daemons must not import this module to grant authority.
A missing field, bad digest, expiry, host, or empty signature is DENY.
This module never signs and never writes private keys.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

REQUIRED_FIELDS = (
    "schema",
    "authorization_id",
    "issued_at",
    "expires_at",
    "current_wave",
    "target_wave",
    "scope",
    "allowed_actions",
    "forbidden_actions",
    "target_hosts",
    "config_digest",
    "checkpoint_digest",
    "rollback_digest",
    "max_duration_s",
    "max_actions",
    "owner_identity",
    "owner_signature",
    "root_key_id",
)

SCHEMA = "octopus.owner-authorization.v1"
LIVE_BOARD_ID = "sensorium-opi5pro-68e44cdf"
ROOT_KEY_ID = "root-v2"


def _parse_dt(value: str) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def verify_owner_authorization(
    artifact: dict[str, Any],
    *,
    now: datetime | None = None,
    expected_host: str = LIVE_BOARD_ID,
    expected_config_digest: str | None = None,
    expected_checkpoint_digest: str | None = None,
    expected_scope: list[str] | None = None,
    expected_current_wave: str = "WAVE0_OBSERVE_ONLY",
) -> tuple[bool, str]:
    """Fail-closed OA verification. Empty signature is always DENY."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(artifact, dict):
        return False, "artifact_not_object"
    for field in REQUIRED_FIELDS:
        if field not in artifact:
            return False, f"missing_field:{field}"
    if artifact.get("schema") != SCHEMA:
        return False, "schema_mismatch"
    if artifact.get("root_key_id") != ROOT_KEY_ID:
        return False, "root_key_id_mismatch"
    signature = artifact.get("owner_signature")
    if not signature:
        return False, "empty_or_missing_signature"
    if artifact.get("current_wave") != expected_current_wave:
        return False, "current_wave_mismatch"
    hosts = artifact.get("target_hosts") or []
    if expected_host not in hosts:
        return False, "target_host_mismatch"
    issued = _parse_dt(str(artifact.get("issued_at") or ""))
    expires = _parse_dt(str(artifact.get("expires_at") or ""))
    if issued is None or expires is None:
        return False, "invalid_datetime"
    if now < issued:
        return False, "not_yet_valid"
    if now >= expires:
        return False, "authorization_expired"
    if expected_config_digest and artifact.get("config_digest") != expected_config_digest:
        return False, "config_digest_mismatch"
    if expected_checkpoint_digest and artifact.get("checkpoint_digest") != expected_checkpoint_digest:
        return False, "checkpoint_digest_mismatch"
    if expected_scope is not None:
        scope = list(artifact.get("scope") or [])
        if scope != list(expected_scope):
            return False, "scope_mismatch"
    try:
        max_duration = int(artifact.get("max_duration_s"))
        max_actions = int(artifact.get("max_actions"))
    except (TypeError, ValueError):
        return False, "invalid_caps"
    if max_duration <= 0 or max_actions <= 0:
        return False, "caps_not_positive"
    if not artifact.get("owner_identity"):
        return False, "owner_identity_empty"
    if not artifact.get("rollback_digest"):
        return False, "rollback_digest_empty"
    return False, "signature_not_verified_on_board"
    # Board never holds root-v2 private key. Even a non-empty signature string
    # is not accepted here; laptop/offline verify is required. Fail closed.


def outcome_timestamp_ok(issued_at_ns: int, resolved_at_ns: int) -> tuple[bool, str]:
    if int(resolved_at_ns) < int(issued_at_ns):
        return False, "outcome_timestamp_before_prediction"
    return True, "ok"
