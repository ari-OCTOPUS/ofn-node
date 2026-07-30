#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mission_approval_and_receipt_critic — بستنِ دو پارگیِ حلقهٔ عملیاتی (۰۷-۳۱).

پارگیِ ۱: کارتِ OWNER_GATE ساخته می‌شد و دور ریخته می‌شد — mission برای همیشه
`needs_approval` می‌مانْد، هیچ سطحی به مالک نمی‌رسید، هیچ حکمی برنمی‌گشت.
پارگیِ ۲: `action-ledger.jsonl` صفر خواننده داشت — رسیدِ اجراکننده را هیچ
منتقدی قضاوت نمی‌کرد.

سنجه‌ها رفتاری‌اند: فایل/صف/دفتر واقعاً تغییر می‌کند یا نمی‌کند؛ گذارِ
غیرقانونی واقعاً رد می‌شود. همه‌چیز در tmp — صفر لمسِ درخت/state ِ زنده.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="mab-rc-")).resolve()
os.environ["ORG_ROOT"] = str(_TMP)
os.environ["OPS_DIR"] = str(_TMP / "_ops")
os.environ["OCTOPUS_STATE_DIR"] = str(_TMP / "_ops" / "state")
(_TMP / "_ops" / "state" / "test_cycle").mkdir(parents=True, exist_ok=True)

_HERE = Path(__file__).resolve().parent                      # _ops/tests
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                    # noqa: E402
import approval_store            # noqa: E402
import goal_action_bridge as gab  # noqa: E402
import mission_approval_bridge as mab  # noqa: E402
import mission_contract as mc    # noqa: E402
import receipt_critic as rc      # noqa: E402

assert str(opslib.STATE_DIR).startswith(str(_TMP)), opslib.STATE_DIR

# approval_store مسیرهایش را از __file__ می‌سازد نه env — به tmp پین می‌شوند.
approval_store._APPROVALS_JSON = _TMP / "_octopus" / "state" / "approvals.json"
approval_store._AUDIT_PATH = _TMP / "_octopus" / "logs" / "audit.log"
approval_store._LEGACY_DIR = _TMP / "_ops" / "state" / "telegram" / "approvals"

NOW = 1_785_400_000.0
ST = _TMP / "_ops" / "state" / "test_cycle"


def _flag(name: str, val: str):
    os.environ[name] = val


def _mk_env(action: str = "request_owner_decision", risk: str = "medium") -> dict:
    return mc.make_envelope(
        source="goal_action_bridge", target_leg="core", owner="octopus_core",
        action=action, risk=risk, intent="بررسیِ لیدهای آمادهٔ claim",
        payload={"k": 1}, task_id="2026-07-31#0",
        project_id="octopus-self-goal", status="needs_approval")


def _append_mission_row(env: dict) -> None:
    with open(ST / "missions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(env, ensure_ascii=False) + "\n")


def _req_for(env: dict) -> dict:
    return {"action_id": f"act-{env['mission_id']}", "action_type": "request_owner_decision",
            "intent": env["intent"], "target": "", "prereg_id": "pre-x",
            "allowed_scope": [], "expected_effect": "کارت به مالک برسد",
            "rollback": "none", "falsifier": "مالک رد کند"}


def _plan_for(req: dict) -> dict:
    return {"classification": "A3", "decision": "OWNER_GATE",
            "reason": "base:A3", "owner_gate": {
                "card": {"schema": "owner-action-card.v1",
                         "action_id": req["action_id"],
                         "intent": req["intent"], "target": ""}}}


# ── پارگیِ ۱: stage → صف → حکم → دفتر ───────────────────────────────────────
def t_a_owner_gate_card_is_staged_to_disk_not_discarded():
    env = _mk_env()
    req = _req_for(env)
    ok = gab._stage_owner_card(env, req, _plan_for(req), now=NOW)
    assert ok is True
    files = list((ST / "owner_cards").glob("*.json"))
    assert files, "کارت stage نشد"
    rec = json.loads([p for p in files if env["mission_id"] in p.name][0]
                     .read_text("utf-8"))
    assert rec["mission_id"] == env["mission_id"]
    assert rec["request"]["action_id"] == req["action_id"], "request ِ دقیق حفظ نشد"
    assert rec["card"].get("intent"), "کارتِ planner حمل نشد"
    # idempotent — بارِ دوم فایل را دوباره نمی‌سازد و خطا نمی‌دهد
    assert gab._stage_owner_card(env, req, _plan_for(req), now=NOW + 5) is True


def t_b_flag_off_bridge_does_nothing():
    _flag(mab.FLAG, "0")
    r = mab.beat(now=NOW)
    assert r.get("ok") is False and r.get("reason") == "flag-off", r


def t_c_sweep_puts_card_in_owner_queue_and_transitions_mission():
    _flag(mab.FLAG, "1")
    env = _mk_env()
    req = _req_for(env)
    assert gab._stage_owner_card(env, req, _plan_for(req), now=NOW)
    _append_mission_row(env)
    r = mab.sweep(now=NOW)
    assert r.get("staged") == 1, r
    jid = f"{mab.JOB_PREFIX}-{env['mission_id']}"
    job = approval_store.get(jid)
    assert job and job["status"] == "pending", job
    latest = mab._latest_missions()[env["mission_id"]]
    assert latest["status"] == "running", latest
    assert any("approval-job" in str(x) for x in latest["output_refs"]), latest


def t_d_owner_approve_closes_mission_done():
    _flag(mab.FLAG, "1")
    env = _mk_env()
    req = _req_for(env)
    gab._stage_owner_card(env, req, _plan_for(req), now=NOW)
    _append_mission_row(env)
    mab.sweep(now=NOW)
    jid = f"{mab.JOB_PREFIX}-{env['mission_id']}"
    assert approval_store.approve(jid) is True
    r = mab.collect(now=NOW + 10)
    assert r.get("settled", 0) >= 1, r
    latest = mab._latest_missions()[env["mission_id"]]
    assert latest["status"] == "done", latest
    assert any("owner-verdict:approved" in str(x)
               for x in latest["output_refs"]), latest


def t_e_owner_reject_closes_mission_failed_with_reason():
    _flag(mab.FLAG, "1")
    env = _mk_env()
    req = _req_for(env)
    gab._stage_owner_card(env, req, _plan_for(req), now=NOW)
    _append_mission_row(env)
    mab.sweep(now=NOW)
    jid = f"{mab.JOB_PREFIX}-{env['mission_id']}"
    assert approval_store.reject(jid) is True
    r = mab.collect(now=NOW + 10)
    assert r.get("settled", 0) >= 1, r
    latest = mab._latest_missions()[env["mission_id"]]
    assert latest["status"] == "failed", latest
    assert latest.get("failure_reason") == "owner-rejected", latest


def t_f_illegal_transition_is_refused_not_forced():
    """کارتِ یتیم (mission از قبل done) هرگز دفتر را جلو نمی‌برد."""
    _flag(mab.FLAG, "1")
    env = _mk_env()
    req = _req_for(env)
    gab._stage_owner_card(env, req, _plan_for(req), now=NOW)
    done_env = dict(env)
    done_env["status"] = "done"          # append-only: آخرین ردیف حاکم است
    _append_mission_row(done_env)
    before = (ST / "missions.jsonl").read_text("utf-8")
    r = mab.sweep(now=NOW)
    assert any(e.get("mission_id") == env["mission_id"]
               for e in (r.get("errors") or [])), r
    assert (ST / "missions.jsonl").read_text("utf-8") == before, \
        "گذارِ غیرقانونی نوشته شد"


# ── پارگیِ ۲: منتقدِ رسید ───────────────────────────────────────────────────
def _receipt(status="EXECUTED", **kw) -> dict:
    base = {"action_id": kw.pop("action_id", f"act-r-{time.time_ns()}"),
            "status": status, "classification": kw.pop("classification", "A0"),
            "external_effects": [], "cost": 0,
            "steps_completed": [{"op": "observe", "result": "read"}],
            "artifacts": [], "rollback_available": False, "evidence": [],
            "errors": []}
    base.update(kw)
    return base


def t_g_clean_receipt_passes():
    env = _mk_env(risk="low")
    aid = "act-clean-1"
    env2 = dict(env)
    env2["status"] = "done"
    env2["output_refs"] = [f"receipt:{aid}"]
    j = rc.judge(_receipt(action_id=aid), {env2["mission_id"]: env2})
    assert j["verdict"] == "PASS", j


def t_h_broken_invariants_fail_with_named_checks():
    j1 = rc.judge(_receipt(external_effects=[{"kind": "http"}]), {})
    assert "C1-external-effects-nonempty" in j1["checks_failed"], j1
    j2 = rc.judge(_receipt(cost=3), {})
    assert "C2-cost-nonzero" in j2["checks_failed"], j2
    j3 = rc.judge(_receipt(steps_completed=[]), {})
    assert "C3-executed-without-steps" in j3["checks_failed"], j3
    j4 = rc.judge(_receipt(artifacts=[{"path": "x", "written": True}],
                           rollback_available=False), {})
    assert "C4-written-artifact-without-rollback" in j4["checks_failed"], j4
    j5 = rc.judge(_receipt(), {})
    assert "C5-executed-without-mission-row" in j5["checks_failed"], j5


def t_i_evaluate_new_is_flag_gated_and_idempotent():
    _flag(rc.FLAG, "0")
    assert rc.evaluate_new(now=NOW).get("reason") == "flag-off"
    _flag(rc.FLAG, "1")
    led = ST / "action-ledger.jsonl"
    with open(led, "a", encoding="utf-8") as f:
        f.write(json.dumps(_receipt(action_id="act-idem-1")) + "\n")
        f.write(json.dumps(_receipt(action_id="act-idem-2",
                                    external_effects=[{"k": 1}])) + "\n")
    r1 = rc.evaluate_new(now=NOW)
    assert r1.get("evaluated") == 2 and r1.get("fails") >= 1, r1
    r2 = rc.evaluate_new(now=NOW + 5)
    assert r2.get("evaluated") == 0, ("idempotency شکست", r2)
    rows = [json.loads(x) for x in
            (ST / "receipt-verdicts.jsonl").read_text("utf-8").splitlines()]
    assert {r["action_id"] for r in rows} >= {"act-idem-1", "act-idem-2"}, rows


def t_j_beat_wiring_present_in_test_cycle_source():
    """صداکننده باید در beat ِ موجود باشد (poller ِ نو ممنوع) — سنجهٔ منبع
    روی هر دو بلوکِ جدید + گاردِ flag-check (وصلِ بی‌گارد = فلگِ تزئینی)."""
    src = (_OPS / "test_cycle.py").read_text("utf-8")
    assert "mission_approval_bridge" in src and "_mab.enabled()" in src, \
        "پلِ تأیید به beat وصل نیست"
    assert "receipt_critic" in src and "_rcx.enabled()" in src, \
        "منتقدِ رسید به beat وصل نیست"
    i_stage = (_OPS / "goal_action_bridge.py").read_text("utf-8")
    assert "_stage_owner_card" in i_stage and \
        i_stage.count("_stage_owner_card") >= 2, "stage در مسیرِ OWNER_GATE نیست"


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")
    print(f"\n{'✅' if not failed else '❌'} test_mission_approval_and_receipt_critic: "
          f"{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(1 if failed else 0)
