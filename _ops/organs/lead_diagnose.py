# -*- coding: utf-8 -*-
"""T70 — lead diagnosis only. No activation, no outbound, no PII fields."""
from __future__ import annotations

import json
from pathlib import Path

from .flags import enabled
from .paths import STATE

FAILURE_CLASSES = ("DEPENDENCY", "NETWORK", "CONFIG", "CODE", "ACK_TIMEOUT", "PHI_MISCALIBRATED")


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def diagnose(*, state: Path | None = None) -> dict:
    """Read last-failure + live chrono. Never enables revenue paths."""
    # Diagnose always. Activation flag must remain false — recorded, never executed.
    activation_off = not enabled("lead_activation", False)
    state = Path(state) if state is not None else STATE
    fail = _read(state / "legs" / "lead-naghshi-last-failure.json") or {}
    org = _read(state / "ORGANISM-STATE.json") or {}
    diag = (((org.get("chrono") or {}).get("legs_diag") or {}).get("lead-naghshi") or {})
    reason = str(fail.get("reason") or "")
    phi_fail = fail.get("phi")
    phi_live = diag.get("phi")
    phi_dead = fail.get("phi_dead") or diag.get("phi_dead")
    silence = fail.get("silence_ms")

    failure_class = "ACK_TIMEOUT"
    if "phi-timeout" in reason or "no-ack" in reason:
        failure_class = "ACK_TIMEOUT"
    comparable = False
    try:
        if phi_fail is not None and phi_live is not None:
            comparable = abs(float(phi_fail) - float(phi_live)) < 5.0
    except (TypeError, ValueError):
        comparable = False

    # Restart hiding: last-failure note already says restart does not fix cause.
    restart_hides = True
    if silence is not None and float(silence) > (float(phi_dead or 16) * 60_000):
        restart_hides = False  # genuine long silence, not poisoned window

    rfc = {
        "rfc_id": "RFC-lead-phi-ack-20260820",
        "status": "draft",
        "bottleneck": "lead-naghshi phi-timeout:no-ack with incomparable phi across samples",
        "fix": (
            "Keep activation off. Log ack age and silence_ms with a single unit. "
            "Treat phi as diagnostic only until scale is documented. Do not auto-restart."
        ),
        "expected_lift": "distinguish real silence from poisoned ack history",
        "rollback": "no code change this session — diagnosis only",
        "evidence": {
            "last_failure_reason": reason,
            "phi_at_failure": phi_fail,
            "phi_live": phi_live,
            "phi_dead_threshold": phi_dead,
            "silence_ms_at_failure": silence,
            "phi_values_comparable": comparable,
        },
        "executable": False,
        "activation_forbidden": True,
    }
    return {
        "ok": True,
        "failure_class": failure_class,
        "phi_calibration": "NOT_COMPARABLE" if not comparable else "COMPARABLE",
        "restart_hides_cause": restart_hides,
        "live_state": diag.get("state"),
        "rfc": rfc,
        "note": fail.get("note"),
        "activation": "FORBIDDEN",
        "activation_flag_off": activation_off,
    }
