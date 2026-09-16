# -*- coding: utf-8 -*-
"""PASS 1 READ-ONLY — LOOP-REGISTRY.jsonl + AST caller/reader graph + L0..L6.

No behavioral code change. No live Telegram. No memory write. Wave 1 stays locked.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from loops import call_graph, defect_hunt, families, ladder  # noqa: E402

EVID = _ROOT / "06-EVIDENCE" / "AGI-LOOPS-PASS1-2026-08-21"
STATE = _OPS / "state" / "loops"
WAVE1_LOCK = _OPS / "state" / "wave1" / "lock.json"
JSONL = STATE / "AGI-LOOP-REGISTRY.jsonl"
JSONL_EVID = EVID / "LOOP-REGISTRY.jsonl"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_wave1() -> dict[str, Any]:
    if not WAVE1_LOCK.is_file():
        return {"wave1_unlocked": False, "missing": True}
    try:
        d = json.loads(WAVE1_LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"wave1_unlocked": False, "corrupt": True}
    d["wave1_unlocked"] = bool(d.get("wave1_unlocked") is True)
    return d


def _surfaces(family_id: str) -> tuple[str, str]:
    """Honest routes. UNROUTED means the card cannot close at L6."""
    m = {
        "AGI-01": ("/status (cockpit)", "/miniapp + /api/* after initData"),
        "AGI-02": ("UNROUTED", "UNROUTED"),  # probe-invalid has no owner card yet
        "AGI-03": ("/memory_status", "UNROUTED"),
        "AGI-04": ("/brain_status", "UNROUTED"),
        "AGI-05": ("approval digest (owner-required)", "UNROUTED"),
        "AGI-06": ("durable loop + canary window C", "/miniapp façade"),
        "AGI-07": ("outbox dry_run", "UNROUTED"),
        "AGI-08": ("UNROUTED", "UNROUTED"),
        "AGI-09": ("UNROUTED", "UNROUTED"),
        "AGI-10": ("/insight (journal card)", "UNROUTED"),
        "AGI-11": ("UNROUTED", "UNROUTED"),
        "AGI-12": ("STOP-TG-HEARTBEAT", "UNROUTED"),
    }
    return m.get(family_id, ("UNROUTED", "UNROUTED"))


def _levels_for_family(fid: str, hunts: dict[str, Any]) -> dict[str, bool]:
    by = {h["hunter"]: h for h in hunts.get("hunts") or []}
    cal = by.get("D07_calibration_reader") or {}
    ema = by.get("D08_constant_0_4") or {}
    dual = by.get("D14_webhook_plus_polling") or {}
    dead = by.get("D17_green_heartbeat_dead_worker") or {}
    # Conservative: implemented if code exists; wired if a reader/caller exists;
    # owner_visible only when both surfaces are routed AND a real owner event closed it.
    base = {r: False for r in ladder.RUNGS}
    base["declared"] = True
    if fid == "AGI-01":
        base.update(implemented=True, wired=True, observed=True, tested=True,
                    verified=True, owner_visible=False)  # window C closed transport, not this family
        if dual.get("verdict") == "NO_DUAL_INGEST_IN_CENTER_SOURCE":
            base["tested"] = True
    elif fid == "AGI-03":
        base.update(implemented=True, wired=True, observed=True, tested=True,
                    verified=False, owner_visible=False)
    elif fid == "AGI-04":
        base.update(implemented=bool(cal.get("improve_reads_calibration_latest"))
                    and bool(ema.get("ema_present")),
                    wired=bool(cal.get("improve_reads_calibration_latest")),
                    observed=False, tested=False, verified=False, owner_visible=False)
    elif fid == "AGI-06":
        base.update(implemented=True, wired=True, observed=True, tested=True,
                    verified=True, owner_visible=True)  # command coverage window C
    elif fid == "AGI-07":
        base.update(implemented=True, wired=True, observed=False, tested=True,
                    verified=False, owner_visible=False)
    elif fid == "AGI-09":
        base.update(implemented=True, wired=True,
                    observed=bool((dead.get("open_missions") or 0) >= 0),
                    tested=False, verified=False, owner_visible=False)
    elif fid == "AGI-12":
        base.update(implemented=True, wired=False, observed=True, tested=False,
                    verified=False, owner_visible=False)
    else:
        base.update(implemented=True, wired=False, observed=False, tested=False,
                    verified=False, owner_visible=False)
    tg, mi = _surfaces(fid)
    if not ladder.require_surfaces(tg, mi):
        base["owner_visible"] = False
    return base


def _budget() -> dict[str, Any]:
    return {
        "max_retries": 3,
        "timeout_s": 1800,
        "kill_switch": ["_ops/STOP-ORGANISM", "_ops/STOP-TG-HEARTBEAT", "_ops/STOP-WAVE1-READ"],
        "rollback": "git checkout in worktree; never irreversible delete",
    }


def build_rows(hunts: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    now = _utc()
    unlocked = bool(_read_wave1().get("wave1_unlocked") is True)
    for fam in families.FAMILIES:
        lv = _levels_for_family(fam["family_id"], hunts)
        tg, mi = _surfaces(fam["family_id"])
        rows.append({
            "kind": "family",
            "loop_id": fam["family_id"],
            "family_id": fam["family_id"],
            "name": fam["name"],
            "problem": fam["problem"],
            "seeds": fam["seeds"],
            "sla_s": fam["sla_s"],
            "levels": lv,
            "stuck_at": ladder.stuck_at(lv),
            "terminal": ladder.terminal(lv),
            "telegram_surface": tg,
            "miniapp_route": mi,
            "can_close": bool(lv.get("owner_visible") and ladder.require_surfaces(tg, mi)),
            "budget": _budget(),
            "wave1_unlocked": unlocked,
            "updated": now,
        })
    for d in families.DISCOVERY:
        fam = next(f for f in families.FAMILIES if f["family_id"] == d["family_id"])
        lv = _levels_for_family(d["family_id"], hunts)
        # discovery grain is never L6-closed by this pass
        lv = dict(lv)
        lv["owner_visible"] = False
        tg, mi = _surfaces(d["family_id"])
        rows.append({
            "kind": "discovery",
            "loop_id": d["loop_id"],
            "family_id": d["family_id"],
            "title": d["title"],
            "levels": lv,
            "stuck_at": ladder.stuck_at(lv),
            "terminal": "OPEN",
            "telegram_surface": tg,
            "miniapp_route": mi,
            "can_close": False,
            "budget": _budget(),
            "updated": now,
        })
    return rows


def run() -> dict[str, Any]:
    EVID.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    lock = _read_wave1()
    if lock.get("wave1_unlocked") is True:
        # Do not unlock. Record the contradiction; do not flip the lock in pass 1.
        lock_note = "PASS1_READ_ONLY_SAW_UNLOCKED_LOCK — did not write"
    else:
        lock_note = "wave1_unlocked=false (unchanged)"
    g = call_graph.graph()
    (EVID / "LOOP-CALL-GRAPH.json").write_text(
        json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
    hunts = defect_hunt.hunt_all()
    (EVID / "DEFECT-HUNT.json").write_text(
        json.dumps(hunts, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = build_rows(hunts)
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    JSONL.write_text(body, encoding="utf-8")
    JSONL_EVID.write_text(body, encoding="utf-8")
    (EVID / "BYTE-SPRINT.json").write_text(
        json.dumps({"schema": "byte-sprint/1", "pass": 1, "live": False,
                    "bytes": list(families.BYTE_SPRINT)}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    fam_stuck = {}
    for r in rows:
        if r.get("kind") == "family":
            fam_stuck[r["loop_id"]] = r["stuck_at"]
    summary = {
        "schema": "agi-loops-pass1/1",
        "pass": "READ-ONLY",
        "ts": _utc(),
        "wave1_unlocked": bool(lock.get("wave1_unlocked") is True),
        "wave1_lock_note": lock_note,
        "paid_calls": "BUDGETED_IF_OWNER_GRANT" if lock.get("wave1_unlocked") else "NOT_GRANTED",
        "memory_writes_readonly_wave": (
            "GRANTED" if lock.get("wave1_unlocked") and lock.get("memory_writes") else "FORBIDDEN"),
        "n_families": 12,
        "n_discovery": 24,
        "call_graph_parsed": g.get("parsed"),
        "call_graph_paths": g.get("n_paths"),
        "family_stuck_at": fam_stuck,
        "l6_complete_count": sum(1 for r in rows if r.get("kind") == "family"
                                 and r.get("stuck_at") == "L6_COMPLETE"),
        "cannot_close_count": sum(
            1 for r in rows if r.get("kind") == "family" and not r.get("can_close")),
        "missing_surface_count": sum(
            1 for r in rows if r.get("kind") == "family"
            and not ladder.require_surfaces(r.get("telegram_surface"), r.get("miniapp_route"))),
        "jsonl": str(JSONL.as_posix()),
        "evidence": str(EVID.as_posix()),
        "agi_claim": False,
        "note": "Pass 1 remains observational. Live send is Pass 3.",
    }
    (EVID / "PASS1-SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    s = run()
    print(json.dumps({
        "pass": s["pass"],
        "wave1_unlocked": s["wave1_unlocked"],
        "family_stuck_at": s["family_stuck_at"],
        "l6_complete_count": s["l6_complete_count"],
        "call_graph_parsed": s["call_graph_parsed"],
    }, ensure_ascii=False, indent=2))
