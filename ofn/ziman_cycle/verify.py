"""Artifact verification: sha match, receipt binding, tamper detect."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .atomic_io import read_json, sha256_file
from .schema import OUTCOME_SCHEMA, migrate_schema


class VerifyError(ValueError):
    pass


def verify_artifact(
    artifact_path: str | Path,
    *,
    expected_previous_sha: str | None = None,
    receipt_path: str | Path | None = None,
    refuse_prior_as_new: bool = True,
    expected_cycle: str | int | None = "4",
) -> dict[str, Any]:
    path = Path(artifact_path)
    if not path.exists():
        raise VerifyError(f"artifact_missing:{path}")
    current_sha = sha256_file(path)
    try:
        doc = read_json(path)
    except Exception as exc:
        raise VerifyError(f"malformed_json:{exc}") from exc
    doc = migrate_schema(doc)
    if doc.get("schema") != OUTCOME_SCHEMA:
        raise VerifyError("schema_mismatch")

    prior = doc.get("consumed_prior") or {}
    previous_sha = prior.get("sha256") or doc.get("previous_sha")
    if expected_previous_sha and previous_sha != expected_previous_sha:
        raise VerifyError(
            f"previous_sha_mismatch:expected={expected_previous_sha}:got={previous_sha}"
        )

    cycle = str(doc.get("cycle"))
    if expected_cycle is not None and cycle != str(expected_cycle):
        if refuse_prior_as_new:
            raise VerifyError(
                f"refuse_consuming_prior_cycle_as_new:got={cycle}:expected={expected_cycle}"
            )

    receipt_ok = None
    if receipt_path:
        receipt = read_json(receipt_path)
        receipt_sha = receipt.get("artifact_sha256") or receipt.get("current_sha")
        if receipt_sha != current_sha:
            raise VerifyError("receipt_artifact_sha_mismatch")
        if receipt.get("previous_sha") and previous_sha and receipt.get("previous_sha") != previous_sha:
            raise VerifyError("receipt_previous_sha_mismatch")
        receipt_ok = True

    sidecar = path.with_suffix(path.suffix + ".sha256")
    if sidecar.exists():
        expected = sidecar.read_text(encoding="utf-8").strip().split()[0]
        if expected != current_sha:
            raise VerifyError("tamper_detected_sidecar_mismatch")

    return {
        "ok": True,
        "artifact_path": str(path),
        "current_sha": current_sha,
        "previous_sha": previous_sha,
        "cycle": cycle,
        "receipt_ok": receipt_ok,
        "schema": doc.get("schema"),
        "verdict": (doc.get("review") or {}).get("verdict") or doc.get("verdict"),
    }


def refuse_prior_cycle_as_new(artifact_path: str | Path, claimed_cycle: str | int = "4") -> None:
    doc = migrate_schema(read_json(artifact_path))
    if str(doc.get("cycle")) != str(claimed_cycle):
        raise VerifyError(
            f"refuse_consuming_prior_cycle_as_new:got={doc.get('cycle')}:claimed={claimed_cycle}"
        )
