# -*- coding: utf-8 -*-
"""Loop-closure closeout: instrument, seed registry, shadow, dry_run telegram.

Never unlocks Wave 1. Never live-sends Telegram. Never paid calls.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from loops import call_graph, decision_card, doctor_timeout, registry, telegram_organ  # noqa: E402

EVID = _ROOT / "06-EVIDENCE" / "LOOP-CLOSURE-2026-08-20"
STATE = _OPS / "state" / "loops"
SPINE = _OPS / "state" / "spine" / "spine.db"
MISSIONS = _ROOT / "OCTOPUS-DOCTOR" / "90-_meta" / "state" / "missions.json"
WAVE1_LOCK = _OPS / "state" / "wave1" / "lock.json"


def relock_wave1() -> dict:
    WAVE1_LOCK.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema": "wave1-lock/1",
        "wave1_unlocked": False,
        "verifier_pass": True,
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "activation": "locked-for-loop-closure",
        "prompt_injection": False,
        "memory_writes": False,
        "organism_hook": False,
        "note": (
            "Loop-closure mission requires wave1_unlocked=false. "
            "Read-only sidecar remains implemented but locked. "
            "wave0_governor.wave1_unlocked stays false."
        ),
    }
    WAVE1_LOCK.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def self_insight_shadow() -> dict:
    """Callable proof without a 46s production self_scan or production journal."""
    sys.path.insert(0, str(_OPS))
    import self_insight as si
    scan = {"checks": {
        "flags": {"defaults": {
            "OCTOPUS_ALPHA": [{"module": "m.py", "default": "1"}]}},
        "state": {}, "tests": {}, "markers": {}, "symbols": {},
    }}
    hyps = []
    errors = {}
    for rule in si.RULES:
        try:
            hyps.extend(rule(scan))
        except Exception as e:  # noqa: BLE001
            errors[rule.__name__] = type(e).__name__
    dest = EVID / "self-insight-shadow.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "schema": "self-insight-shadow/1",
        "journal": False,
        "n_hypotheses": len(hyps),
        "n_rules": len(si.RULES),
        "rule_errors": errors,
        "callable": True,
        "observed_production_cycle": False,
        "verified": False,
        "note": "SHADOW_CLOSED — full weekly cycle not claimed",
    }
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def run() -> dict:
    EVID.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    lock = relock_wave1()
    g = call_graph.write(EVID / "LOOP-CALL-GRAPH.json")
    insight = self_insight_shadow()

    organ = telegram_organ.TelegramOrgan(STATE, allowlist={1}, live=False, rate_s=1.0)
    u1 = {"update_id": 900001, "message": {"text": "hello", "chat": {"id": 1}, "from": {"id": 1}}}
    first = organ.ingest_update(u1)
    second = organ.ingest_update(u1)  # restart replay
    denied = organ.ingest_update({
        "update_id": 900002,
        "message": {"text": "x", "chat": {"id": 99}, "from": {"id": 99}},
    })
    leak = telegram_organ.redact("token <REDACTED-TELEGRAM-TOKEN>XXX")
    spine = organ.consume_spine_count(SPINE)
    digest = organ.enqueue_digest(
        [{"loop_id": "loop:S-T01", "class": "ORPHAN", "title": "telegram_events orphan"},
         {"loop_id": "loop:S-D01", "class": "DEADLOCK", "title": "doctor-pulse"}],
        chat_id=1,
        force=True,
    )

    q = doctor_timeout.quarantine_file(
        MISSIONS,
        now=time.time(),
        timeout_s=doctor_timeout.DEFAULT_TIMEOUT_S,
        backup=EVID / "missions.json.bak",
    )

    card = decision_card.make_card(
        loop_id="loop:S-T02",
        question="Arm live Telegram send to owner allowlist after safety tests?",
        options=["keep_dry_run", "arm_live"],
        safe_default="keep_dry_run",
        ttl_s=48 * 3600,
    )
    decision_card.write_ledger(EVID / "decision-cards.jsonl", card)

    degraded = {
        "schema": "degraded-local-only/1",
        "mode": "DECLARED",
        "reason": "S-B01 quota / S-B02 FX-pin — no paid calls this lane",
        "paid_calls": 0,
        "silent": False,
    }
    (EVID / "DEGRADED-LOCAL-ONLY.json").write_text(
        json.dumps(degraded, ensure_ascii=False, indent=2), encoding="utf-8")

    marks = {
        "S-A01": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": False, "verified": False},
                  "regression_test": "test_loop_closure.py::t_no_hardcoded_0_4",
                  "status": "shadow_closed"},
        "S-A02": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": False, "verified": False},
                  "regression_test": "test_loop_closure.py::t_self_insight_shadow",
                  "status": "shadow_closed"},
        "S-A03": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": False, "verified": False},
                  "regression_test": "test_loop_closure.py::t_improve_reads_calibration",
                  "status": "shadow_closed"},
        "S-A08": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": False, "verified": False},
                  "regression_test": "test_loop_closure.py::t_cockpit_self_knowledge_tier",
                  "status": "shadow_closed"},
        "S-D01": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": True, "verified": False},
                  "regression_test": "test_loop_closure.py::t_doctor_timeout",
                  "status": "tested_open"},
        "S-T01": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": bool(spine.get("n")),
                             "verified": False},
                  "regression_test": "test_loop_closure.py::t_telegram_idempotent",
                  "status": "shadow_closed"},
        "S-T02": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": False, "verified": False},
                  "telegram_card_id": card["card_id"],
                  "status": "shadow_closed"},
        "S-T03": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": True, "observed": False, "verified": False},
                  "regression_test": "test_loop_closure.py::t_digest_coalesces",
                  "status": "shadow_closed"},
        "S-B01": {"levels": {"declared": True, "implemented": True, "callable": True,
                             "tested": False, "observed": False, "verified": False},
                  "status": "implemented_open"},
    }
    reg = registry.write(EVID / "LOOP-REGISTRY.json", marks)
    registry.write(STATE / "LOOP-REGISTRY.json", marks)

    report = {
        "schema": "loop-closure-closeout/1",
        "wave1_unlocked": False,
        "wave1_lock": lock,
        "call_graph_parsed": g.get("parsed"),
        "registry_n": reg.get("n"),
        "self_insight_shadow": insight,
        "telegram": {
            "first": first, "replay": second, "denied": denied,
            "redact_ok": "[REDACTED_BOT_TOKEN]" in leak,
            "spine": spine, "digest": {k: digest.get(k) for k in
                                       ("status", "sent", "n_loops", "coalesced")},
            "live": False,
        },
        "doctor_quarantine": q,
        "decision_card": {"card_id": card["card_id"], "safe_default": card["safe_default"]},
        "degraded": degraded,
        "paid_calls": 0,
        "restarts": 0,
        "live_telegram": False,
    }
    (EVID / "CLOSEOUT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (EVID / "WAVE1-LOCK-COPY.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = run()
    print(json.dumps({
        "registry_n": r["registry_n"],
        "wave1_unlocked": r["wave1_unlocked"],
        "quarantined": (r.get("doctor_quarantine") or {}).get("quarantined"),
        "telegram_live": r["live_telegram"],
        "replay": (r.get("telegram") or {}).get("replay", {}).get("status"),
    }, ensure_ascii=False, indent=2))
