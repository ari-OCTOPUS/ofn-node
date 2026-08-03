#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mission_card_seam — درزِ VQ-MISSION-CARD-001: mission ِ منتظرِ رأی → کارتِ ap:.

شکافِ ثبت‌شده در `13-ARMED-RUNTIME-EVIDENCE.md`: mission با `needs_approval`
در دفتر می‌نشیند ولی هیچ کارتی به صفِ تأییدِ موجود نمی‌رود — مالک فقط اگر
فایل را بخواند می‌بیند (روی درخت زنده امروز دو ردیفِ واقعیِ دیده‌نشده هست).

درز از صفِ تست‌شدهٔ موجود (`telegram_center/approval_store`) می‌گذرد؛ هیچ
poller/bot ِ تازه‌ای نیست و رأی‌گیری همان مسیرِ `ap:ok/ap:no` ِ center است.

ناوردی‌ها: فلگِ خاموش = دقیقاً هیچ · content-free (متنِ هدف هرگز واردِ کارت
نمی‌شود) · idempotent در برابرِ تکرارِ beat و رأی‌خوردنِ کارت · فقط آخرین
وضعِ هر mission ملاک است.
"""
import json
import os
import time
from pathlib import Path

import harness

ENV = harness.setup("mission-card-seam")

# صفِ تأیید هم باید داخلِ sandbox بنشیند (approval_store به _octopus/state ِ
# ریشهٔ repo می‌نویسد؛ loader ِ پل OCTOPUS_STATE_ROOT را honor می‌کند).
_OCT_STATE = Path(ENV["root"]) / "_octopus" / "state"
os.environ["OCTOPUS_STATE_ROOT"] = str(_OCT_STATE)

import goal_action_bridge as gab  # noqa: E402

NOW = 1_785_400_000.0
GOAL_MARKER = "متنِ-هدف-که-هرگز-نباید-واردِ-کارت-شود"


def _card_flag(on: bool):
    if on:
        os.environ[gab.CARD_FLAG] = "1"
    else:
        os.environ.pop(gab.CARD_FLAG, None)


def _mission(mid: str, status: str, *, approval: bool = True) -> dict:
    return {"mission_id": mid, "status": status, "requires_approval": approval,
            "action": "request_qualified_lead_review", "target_leg": "lead",
            "risk": "high", "trace_id": "trace:t" + mid[-4:],
            "intent": GOAL_MARKER, "source": "self-goal"}


def _seed(rows: list) -> None:
    p = gab._missions_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")


def _approvals() -> dict:
    p = _OCT_STATE / "approvals.json"
    if not p.exists():
        return {"pending": [], "approved": [], "rejected": [], "done": []}
    return json.loads(p.read_text("utf-8"))


def t_flag_off_is_exactly_nothing():
    _card_flag(False)
    _seed([_mission("mis:aaaa000000000000till", "needs_approval")])
    r = gab.emit_mission_cards()
    assert r.get("reason") == "flag-off" and r.get("emitted") == 0, r
    assert not (_OCT_STATE / "approvals.json").exists(), "فلگِ خاموش نوشت!"


def t_needs_approval_mission_becomes_one_content_free_card():
    _card_flag(True)
    _seed([_mission("mis:bbbb000000000000card", "needs_approval")])
    r = gab.emit_mission_cards()
    assert r.get("ok") and r.get("emitted") == 1, r
    st = _approvals()
    assert len(st["pending"]) == 1, st
    job = st["pending"][0]
    assert job["type"] == "mission_approval" and job["source"] == "goal_action_bridge", job
    assert job["id"].startswith("mis-"), job
    blob = (_OCT_STATE / "approvals.json").read_text("utf-8")
    assert GOAL_MARKER not in blob, "متنِ هدف واردِ صفِ تأیید شد — content-free شکست"


def t_idempotent_across_calls_and_after_verdict():
    _card_flag(True)
    _seed([_mission("mis:cccc000000000000idem", "needs_approval")])
    assert gab.emit_mission_cards().get("emitted") == 1
    assert gab.emit_mission_cards().get("emitted") == 0, "کارتِ تکراری ساخته شد"
    store = gab._load_approval_store()
    jid = next(j["id"] for j in _approvals()["pending"] if "cccc" in j["id"])
    assert store.approve(jid), "approve ِ صفِ واقعی شکست"
    assert gab.emit_mission_cards().get("emitted") == 0, \
        "کارتِ رأی‌خورده دوباره pending شد — چکِ همهٔ bucketها لازم است"


def t_only_latest_status_of_each_mission_counts():
    _card_flag(True)
    mid = "mis:dddd000000000000late"
    _seed([_mission(mid, "needs_approval"), _mission(mid, "done", approval=True)])
    assert gab.emit_mission_cards().get("emitted") == 0, \
        "mission ِ تمام‌شده هنوز کارت می‌گیرد — آخرین ردیف ملاک نیست"


def t_non_gated_missions_never_card():
    _card_flag(True)
    _seed([_mission("mis:eeee000000000000done", "done"),
           _mission("mis:ffff000000000000quee", "queued", approval=False),
           _mission("mis:0000111100000000fail", "failed", approval=False)])
    assert gab.emit_mission_cards().get("emitted") == 0


def t_beat_carries_the_seam_every_tick_not_only_on_slots():
    _card_flag(True)
    os.environ["OCTOPUS_WIRE_TEST_CYCLE"] = "1"
    try:
        _seed([_mission("mis:9999000000000000beat", "needs_approval")])
        import test_cycle as tc
        out = tc.beat(now=NOW)
        assert out.get("mission_cards") == 1, out
    finally:
        os.environ.pop("OCTOPUS_WIRE_TEST_CYCLE", None)


def t_loader_resolves_the_real_store_module():
    mod = gab._load_approval_store()
    for fn in ("add_pending", "get", "approve", "reject", "load_pending"):
        assert callable(getattr(mod, fn, None)), f"approval_store.{fn} غایب"


CHECKS = [(f.__name__, f) for f in (
    t_flag_off_is_exactly_nothing,
    t_needs_approval_mission_becomes_one_content_free_card,
    t_idempotent_across_calls_and_after_verdict,
    t_only_latest_status_of_each_mission_counts,
    t_non_gated_missions_never_card,
    t_beat_carries_the_seam_every_tick_not_only_on_slots,
    t_loader_resolves_the_real_store_module,
)]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    total = len(CHECKS)
    print(("✅" if not failed else "❌") + f" test_mission_card_seam: {total - failed}/{total}")
    raise SystemExit(1 if failed else 0)
