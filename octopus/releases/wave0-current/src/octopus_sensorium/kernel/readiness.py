"""Readiness is only taken from the deterministic verifier report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from octopus_sensorium.kernel.errors import ReadinessSourceError

DEFAULT_REPORT = Path("/var/lib/octopus/state/boot_report.json")
ALLOWED = {"READY", "DEGRADED", "UNVERIFIED", "FAILED_SAFE"}


def load_verifier_readiness(path: Path = DEFAULT_REPORT) -> tuple[str, list[str], dict[str, Any]]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReadinessSourceError("verifier report unreadable") from exc
    state = report.get("readiness_state")
    failed = report.get("gates_failed")
    if state not in ALLOWED or not isinstance(failed, list):
        raise ReadinessSourceError("verifier report missing readiness_state/gates_failed")
    return str(state), list(failed), report
