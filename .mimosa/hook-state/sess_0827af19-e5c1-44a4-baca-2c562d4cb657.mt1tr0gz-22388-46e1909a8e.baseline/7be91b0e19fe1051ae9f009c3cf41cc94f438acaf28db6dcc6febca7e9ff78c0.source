"""Read-only organism/pulse → Observation. Never writes _ops/state. No organism.py hook."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from shadow_homeostasis.observation import Observation, Quality, parse_dt

_OPS = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.exists():
        return None, "MISSING"
    try:
        return json.loads(path.read_text(encoding="utf-8")), "OK"
    except (OSError, json.JSONDecodeError):
        return None, "UNLOCATED"


def _aware(value: datetime | str | None, fallback: datetime) -> datetime:
    """Naive pulse/organism stamps are local UTC+10, not UTC."""
    if value is None:
        return fallback
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=10)))
        return dt.astimezone(timezone.utc)
    s = str(value).strip()
    if s.endswith("Z"):
        return parse_dt(s) or fallback
    if "+" in s[10:] or s.endswith("UTC"):
        return parse_dt(s) or fallback
    # no offset → owner-local +10
    return parse_dt(s + "+10:00") or fallback


def _obs(**kw: Any) -> Observation:
    return Observation(**kw)


def default_paths(ops: Path | None = None) -> dict[str, Path]:
    root = ops or _OPS
    return {
        "organism": root / "state" / "ORGANISM-STATE.json",
        "arbiter": root / "state" / "pulse" / "arbiter-latest.json",
        "life_currency": root / "state" / "pulse" / "life-currency-latest.json",
        "identities": root / "state" / "identities-latest.json",
        "inbox_task": root.parent / "00 - Inbox" / "2026-08-20 TASK — frontmatter debt independent.md",
    }


def read_live(
    decision_time: datetime,
    *,
    paths: dict[str, Path] | None = None,
    process_id: int | None = None,
) -> tuple[list[Observation], dict[str, Any]]:
    """Sidecar READ of live telemetry. Copies nothing back. latest.json is not historical proof."""
    dt = decision_time if decision_time.tzinfo else decision_time.replace(tzinfo=timezone.utc)
    rec = dt  # sidecar records at decision_time so recorded_at <= decision_time
    p = paths or default_paths()
    org, org_st = _load_json(p["organism"])
    arb, arb_st = _load_json(p["arbiter"])
    life, life_st = _load_json(p["life_currency"])
    ident, ident_st = _load_json(p["identities"])

    boot_id = None
    beat = None
    if org:
        boot_id = str(org.get("started") or "") or None
        beat = org.get("beat")
    if beat is None and arb:
        beat = arb.get("beat")
    if beat is None and life:
        beat = life.get("beat")

    meta: dict[str, Any] = {
        "schema": "full-loop-telemetry.v1",
        "read_only": True,
        "wrote_state": False,
        "organism_py_hooked": False,
        "boot_id": boot_id,
        "beat": beat,
        "source_hashes": {k: _sha(v) for k, v in p.items() if v.suffix in (".json", ".md")},
        "source_status": {
            "organism": org_st, "arbiter": arb_st,
            "life_currency": life_st, "identities": ident_st,
        },
        "latest_only": True,
        "historical_claim": False,
        "note": "latest.json snapshot is not historical proof; hashes recorded at read time",
    }
    obs: list[Observation] = []
    pid = process_id

    def add(oid: str, source_id: str, metric: str, value, unit: str, path: Path, occurred, quality: str, reasons: list[str]) -> None:
        sh = _sha(path)
        occ = _aware(occurred, dt)
        obs.append(_obs(
            observation_id=oid,
            source_id=source_id,
            metric=metric,
            value=value,
            unit=unit,
            occurred_at=occ,
            recorded_at=rec,
            decision_time=dt,
            beat=int(beat) if beat is not None else None,
            boot_id=boot_id,
            process_id=pid,
            provenance_path=str(path).replace("\\", "/"),
            source_hash=sh,
            quality=quality,
            quality_reasons=reasons,
            latest_only=True,
            historical_claim=False,
            window_n=None,
            window_ready=None,
        ))

    if arb and arb_st == "OK":
        ts = arb.get("ts")
        period = arb.get("effective_period_s")
        color = arb.get("color")
        reasons = ["latest_only", "sidecar_read"]
        q = Quality.VALID.value
        if arb.get("wire_open") is True and not arb.get("advisory_only"):
            reasons.append("wire_open_live_but_shadow_pipeline_advisory")
        add("live-period", "pulse.arbiter", "arbiter.period_s", period, "s", p["arbiter"], ts, q, reasons)
        add("live-color", "pulse.arbiter", "arbiter.color", color, "enum", p["arbiter"], ts, q, list(reasons))
    else:
        add("live-period", "pulse.arbiter", "arbiter.period_s", None, "s", p["arbiter"], dt, Quality.MISSING.value, [arb_st])

    if life and life_st == "OK":
        ts = life.get("ts")
        add("live-cap", "pulse.life_currency", "life_currency.daily_cap", life.get("daily_cap"), "life_credit", p["life_currency"], ts, Quality.VALID.value, ["latest_only", "unit=life_credit"])
        toks = ((life.get("members") or {}).get("organism") or {}).get("tokens")
        add("live-tok", "pulse.life_currency", "life_currency.tokens_min", toks, "life_credit", p["life_currency"], ts, Quality.VALID.value, ["latest_only"])
        add("live-unit", "pulse.life_currency", "life_currency.unit", life.get("unit") or "life_credit", "enum", p["life_currency"], ts, Quality.VALID.value, ["latest_only"])
    else:
        add("live-cap", "pulse.life_currency", "life_currency.daily_cap", None, "life_credit", p["life_currency"], dt, Quality.MISSING.value, [life_st])

    ih = None
    ih_src = p["organism"]
    ih_ts = None
    if org:
        ih = ((org.get("math_control") or {}).get("identity_health"))
        ih_ts = org.get("ts")
    if ih is None and ident:
        ih = ((ident.get("identities") or {}).get("learner") or {}).get("value")
        ih_src = p["identities"]
        ih_ts = ident.get("ts")
        ident_st_use = ident_st
    else:
        ident_st_use = org_st
    if ih is not None:
        add("live-id", "state.organism", "identity_health", ih, "ratio", ih_src, ih_ts, Quality.VALID.value, ["latest_only", ident_st_use])
    else:
        add("live-id", "state.organism", "identity_health", None, "ratio", p["identities"], dt, Quality.MISSING.value, ["MISSING"])

    meta["observation_ids"] = [o.observation_id for o in obs]
    return obs, meta


def load_real_task(paths: dict[str, Path] | None = None) -> dict[str, Any]:
    """Owner-visible real task from Inbox (cockpit/intake stand-in). Not fabricated."""
    p = (paths or default_paths())["inbox_task"]
    text = ""
    status = "OK"
    if not p.exists():
        status = "MISSING"
    else:
        text = p.read_text(encoding="utf-8")[:4000]
    return {
        "schema": "full-loop-task.v1",
        "task_id": "FRONTMATTER-DEBT-2026-08-20",
        "source": "00 - Inbox (owner task) + organism telemetry sidecar",
        "intake": "inbox_md",
        "cockpit": "UNLOCATED_DIRECT_API",
        "harmless": True,
        "external_action": False,
        "path": str(p).replace("\\", "/"),
        "source_hash": _sha(p),
        "status": status,
        "summary": "Vault frontmatter debt is OPEN and growing; propose a scheduling note only.",
        "excerpt": text[:800],
    }
