#!/usr/bin/env python3
"""Reflex A0 advisory loop. Hash-chained ledger. Never executes privileged commands."""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/scripts")
from reflex_ledger import append, is_armed, lock_advisory_forever, verify  # noqa: E402

STABILITY = Path("/var/lib/octopus/state/stability/latest.json")
ENVELOPE = Path("/var/lib/octopus/state/stability/envelope.json")
DIR = Path("/var/lib/octopus/state/reflex")
OPEN = DIR / "open.json"
LATEST = DIR / "latest.json"
FIRED = DIR / "last_fired.json"
ARMING = Path("/etc/octopus/reflex_arming_criteria.yaml")
EVIDENCE = Path("/var/lib/octopus/state/evidence")

RULES = [
    {
        "name": "high_memory_usage",
        "axis": "memory_used",
        "op": "gt",
        "threshold": 0.90,
        "action": "clear_system_cache",
        "cooldown_s": 300,
        "min_sustained_s": 15,
        "evidence": ["last_OCT-SENSE-053_MEMORY.json"],
        "observe_only_reason": "drop_caches requires root; denied in WAVE0_OBSERVE_ONLY",
    },
    {
        "name": "high_cpu_temp",
        "axis": "soc_temperature",
        "op": "gt",
        "threshold": 75.0,
        "action": "throttle_cpu",
        "cooldown_s": 600,
        "min_sustained_s": 15,
        "evidence": ["last_OCT-SENSE-053_THERMAL.json"],
        "observe_only_reason": "cpufreq writes are actuator-class; denied in WAVE0_OBSERVE_ONLY",
    },
]
MAX_OPEN_S = 24 * 3600
BOOT_REPORT = Path("/var/lib/octopus/state/boot_report.json")
CLOSURE_REASONS = {
    "resolved_spontaneously",
    "resolved_after_owner_action",
    "resolved_unknown_cause",
    "expired_no_resolution",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()


def _envelope_meta() -> tuple[str, int]:
    doc = _load(ENVELOPE, {})
    return str(doc.get("profile") or "WAVE0_IDLE"), int(doc.get("version") or 1)


def _clock_trust(stability: dict[str, Any]) -> str:
    trust = stability.get("clock_trust")
    if trust:
        return str(trust)
    boot = _load(BOOT_REPORT, {})
    return str((boot.get("clock") or {}).get("clock_trust") or "UNKNOWN")


def _cmp(op: str, value: float, threshold: float) -> bool:
    return value > threshold if op == "gt" else value < threshold


def close_open(open_rows: dict[str, Any], reason: str, stability: dict[str, Any]) -> None:
    if reason not in CLOSURE_REASONS:
        reason = "resolved_unknown_cause"
    for rule_name, row in list(open_rows.items()):
        if row.get("closed_at"):
            continue
        row["closed_at"] = time.time()
        row["closure_reason"] = reason
        append(
            {
                "schema": "octopus.reflex-advisory.v1",
                "event": "advisory_closed",
                **row,
                "distance_at_close": stability.get("distance"),
            }
        )
        open_rows[rule_name] = row


def main() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    ok, seq, detail = verify()
    if not ok:
        lock_advisory_forever(f"ledger_break seq={seq} {detail}")
    if not Path("/var/lib/octopus/state/reflex/ARMED.json").exists():
        Path("/var/lib/octopus/state/reflex/ARMED.json").write_text(
            json.dumps(
                {
                    "armed": False,
                    "locked": False,
                    "owner_approval": "required",
                    "criteria": str(ARMING),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    last_fired = _load(FIRED, {})
    open_rows = _load(OPEN, {})
    pending_since: dict[str, float] = {k: float(v.get("opened_at") or time.time()) for k, v in open_rows.items() if not v.get("closed_at")}
    while True:
        ok, seq, detail = verify()
        if not ok:
            lock_advisory_forever(f"ledger_break seq={seq} {detail}")
        stability = _load(STABILITY, {})
        axes = stability.get("axes") or {}
        profile, env_ver = _envelope_meta()
        fired: list[dict[str, Any]] = []
        now = time.time()
        for rule in RULES:
            axis = axes.get(rule["axis"]) or {}
            value = axis.get("value")
            if value is None or axis.get("stale"):
                pending_since.pop(rule["name"], None)
                continue
            if not _cmp(rule["op"], float(value), float(rule["threshold"])):
                pending_since.pop(rule["name"], None)
                continue
            pending_since.setdefault(rule["name"], now)
            sustained = now - pending_since[rule["name"]]
            if sustained < float(rule.get("min_sustained_s") or 0):
                continue
            if now - float(last_fired.get(rule["name"]) or 0) < float(rule["cooldown_s"]):
                continue
            if open_rows.get(rule["name"]) and not open_rows[rule["name"]].get("closed_at"):
                continue
            body = {
                "schema": "octopus.reflex-advisory.v1",
                "advisory_id": f"adv-{uuid.uuid4()}",
                "boot_id": _boot_id(),
                "rule": rule["name"],
                "metric": rule["axis"],
                "value": value,
                "threshold": rule["threshold"],
                "sustained_s": round(sustained, 1),
                "envelope_profile": profile,
                "envelope_version": env_ver,
                "distance_at_trigger": stability.get("distance"),
                "would_execute": rule["action"],
                "decision": "denied_observe_only",
                "actuator_authority": "NONE",
                "clock_trust": _clock_trust(stability),
                "evidence_files": [str(EVIDENCE / name) for name in rule["evidence"]],
                "opened_at": now,
                "closed_at": None,
                "closure_reason": None,
                "armed": is_armed(),
                "reason": rule["observe_only_reason"],
            }
            append(body)
            open_rows[rule["name"]] = body
            last_fired[rule["name"]] = now
            fired.append(body)
        open_alive = {k: v for k, v in open_rows.items() if not v.get("closed_at")}
        host_ok = stability.get("host_in_range")
        if host_ok is None:
            host_ok = stability.get("in_envelope")
        if host_ok is True and open_alive:
            close_open(open_alive, "resolved_spontaneously", stability)
            open_rows.update(open_alive)
            for name in list(open_alive):
                pending_since.pop(name, None)
        elif open_alive:
            expired = {
                k: v
                for k, v in open_alive.items()
                if now - float(v.get("opened_at") or now) >= MAX_OPEN_S
            }
            if expired:
                close_open(expired, "expired_no_resolution", stability)
                open_rows.update(expired)
                for name in expired:
                    pending_since.pop(name, None)
        if fired or open_rows:
            OPEN.write_text(json.dumps(open_rows, indent=2) + "\n", encoding="utf-8")
            FIRED.write_text(json.dumps(last_fired, indent=2) + "\n", encoding="utf-8")
        chain_ok, _, chain_detail = verify()
        LATEST.write_text(
            json.dumps(
                {
                    "timestamp": _now().isoformat(),
                    "execute_enabled": False,
                    "armed": is_armed(),
                    "ledger_ok": chain_ok,
                    "ledger_detail": chain_detail,
                    "open": [k for k, v in open_rows.items() if not v.get("closed_at")],
                    "last_advisories": fired,
                    "distance": stability.get("distance"),
                    "in_envelope": stability.get("in_envelope"),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        time.sleep(5)


if __name__ == "__main__":
    raise SystemExit(main())
