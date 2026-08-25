from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from ofn.organism.cognition.voice import utc_now


ATTESTATION_PATH = Path("/opt/octopus/lab/state/ATTESTATION.json")


def read_attestation(path: Path = ATTESTATION_PATH) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def write_attestation(snapshot: dict[str, Any], path: Path = ATTESTATION_PATH) -> dict[str, Any]:
    body = {
        "organism_id": snapshot.get("organism_id"),
        "given_name": (snapshot.get("development") or {}).get("given_name"),
        "stage": (snapshot.get("development") or {}).get("stage"),
        "health_state": snapshot.get("health_state"),
        "identity_chain_valid": snapshot.get("identity_chain_valid"),
        "identity_chain_last_hash": snapshot.get("identity_chain_last_hash"),
        "identity_chain_scope": snapshot.get(
            "identity_chain_verification_scope",
            "INTERNAL_HASH_CHAIN_CONSISTENCY",
        ),
        "ipv4": (snapshot.get("place") or {}).get("ipv4"),
        "season_city": (snapshot.get("season") or {}).get("city"),
        "season_source": (snapshot.get("season") or {}).get("source"),
        "school_passed": (snapshot.get("school") or {}).get("all_passed"),
        "external_api": snapshot.get("external_api"),
        "updated_utc": utc_now(),
        "note": "Local attestation for other agents on this board. Not a public PKI anchor.",
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    body["attestation_hash"] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)
    return body
