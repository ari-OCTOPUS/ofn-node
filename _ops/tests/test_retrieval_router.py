#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_retrieval_router — حافظه در نقطهٔ تصمیم: فقط narrowing، هرگز مجوز.

سه ادعای ماژول که هرکدام سنجهٔ رفتاریِ خودش را دارد:
  ۱) فلگ خاموش = صفر تماس با DB (نه فقط خروجیِ خالی).
  ۲) veto فقط از owner_fact می‌آید و فقط می‌بندد — زنجیرهٔ goal→action با veto
     اجرا نمی‌کند (سنجه: جاسوس روی executor، نه ادعای دیکشنری).
  ۳) خطای router زنجیره را نمی‌خواباند — غیابِ حافظه منع نیست.
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("retrieval-router")

assert os.environ.get("OCTOPUS_STATE_DIR"), \
    "harness ِ این نسخه OCTOPUS_STATE_DIR را pin نمی‌کند — نشتِ حافظه به درختِ زنده"

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "memory") not in sys.path:
    sys.path.insert(0, str(_OPS / "memory"))

import goal_action_bridge as gab  # noqa: E402
import memory_store  # noqa: E402
import prereg  # noqa: E402
import retrieval_router as rr  # noqa: E402

NOW = 1_785_400_000.0
GK = "krtr"


class _Flag:
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


def _db_path() -> Path:
    return Path(os.environ["OCTOPUS_STATE_DIR"]) / "memory" / "memory.db"


def _seed_store() -> memory_store.MemoryStore:
    st = memory_store.MemoryStore()
    st.insert({"namespace": "episodic", "mkey": f"cycle:{GK}",
               "content": f"SGC cycle for {GK}: verdict=PASS",
               "trust": "DETERMINISTIC", "admission_state": "ADMITTED"})
    return st


# ── فلگ و مرزها ─────────────────────────────────────────────────────────────
def t_flag_off_touches_no_database_at_all():
    """سنجه روی یک state ِ بکرِ جدا — unlink ِ sqlite ِ باز روی ویندوز تله است."""
    probe = Path(os.environ["OCTOPUS_STATE_DIR"]) / "flag-off-probe"
    old = os.environ["OCTOPUS_STATE_DIR"]
    os.environ["OCTOPUS_STATE_DIR"] = str(probe)
    try:
        with _Flag(rr.FLAG, None):
            out = rr.route(goal_key=GK)
        assert out["mode"] == "off" and out["memories_used"] == [], out
        assert not (probe / "memory" / "memory.db").exists(), \
            "فلگ خاموش ولی DB ساخته شد!"
    finally:
        os.environ["OCTOPUS_STATE_DIR"] = old


def t_empty_goal_key_is_an_honest_no_op():
    st = _seed_store()
    try:
        with _Flag(rr.FLAG, "1"):
            out = rr.route(goal_key="", store=st)
    finally:
        st.close()
    assert out["mode"] == "none" and "no-goal-key" in out["reasons"], out
    assert out["veto"] is False, out


def t_citations_are_ref_shaped_never_raw_text():
    """قراردادِ as_memories_used: hash/ref، بدونِ متنِ خام."""
    st = _seed_store()
    try:
        with _Flag(rr.FLAG, "1"):
            out = rr.route(goal_key=GK, store=st)
    finally:
        st.close()
    assert "episodic" in out["mode"], out
    assert out["memories_used"], out
    m = out["memories_used"][0]
    assert set(m) >= {"memory_id", "content_sha256", "trust_grade"}, m
    assert "content" not in m, ("متنِ خام در citation نشت کرد", m)
    assert out["veto"] is False, out


def t_owner_fact_veto_narrows_and_cites():
    st = _seed_store()
    try:
        st.insert({"namespace": "owner_fact", "mkey": f"veto:{GK}",
                   "content": "مالک: این هدف فعلاً اجرا نشود",
                   "trust": "OWNER_CONFIRMED", "admission_state": "ADMITTED"})
        with _Flag(rr.FLAG, "1"):
            out = rr.route(goal_key=GK, store=st)
    finally:
        st.close()
    assert out["veto"] is True and out["veto_ref"], out
    assert "exact" in out["mode"], out
    assert "owner-veto" in out["reasons"], out


def t_a_non_admitted_veto_row_is_invisible():
    """PENDING دیده نمی‌شود — قاعدهٔ خودِ store؛ router نباید دورش بزند."""
    st = _seed_store()
    try:
        st.insert({"namespace": "owner_fact", "mkey": f"veto:{GK}",
                   "content": "هنوز تأیید نشده", "trust": "OWNER_CONFIRMED",
                   "admission_state": "PENDING"})
        with _Flag(rr.FLAG, "1"):
            out = rr.route(goal_key=GK, store=st)
    finally:
        st.close()
    assert out["veto"] is False, out


# ── مصرف در زنجیرهٔ زنده ────────────────────────────────────────────────────
def _proposal() -> dict:
    return {"goal": "هدفِ router", "goal_key": GK, "goal_source": "self",
            "direction": "جهتِ آزمون", "method": "روش", "method_index": 0,
            "metric_path": "state/neural/recall-trend.jsonl",
            "metric_key": "events", "baseline": 0.0,
            "target": {"op": ">", "value": 0.0},
            "candidate_key": "recall-events", "deadline_cycles": 2}


def _fresh_chain():
    for name in ("missions.jsonl", "action-ledger.jsonl", "used-nonces.json",
                 "prereg.jsonl"):
        try:
            (gab._state_dir() / name).unlink()
        except OSError:
            pass


def t_the_bridge_blocks_on_veto_and_the_executor_is_never_called():
    _fresh_chain()
    st = memory_store.MemoryStore()
    st.insert({"namespace": "owner_fact", "mkey": f"veto:{GK}",
               "content": "مالک: نگه دار", "trust": "OWNER_CONFIRMED",
               "admission_state": "ADMITTED"})
    st.close()
    sys.path.insert(0, str(_OPS / "action_bridge"))
    import executor as _ex
    calls = []
    real = _ex.execute
    _ex.execute = lambda *a, **k: (calls.append(1), real(*a, **k))[1]
    try:
        with _Flag(gab.FLAG, "1"), _Flag(rr.FLAG, "1"):
            cyc = "2026-07-31#11"
            p = prereg.register(_proposal(), cycle=cyc, now=NOW)
            assert p.get("ok"), p
            r = gab.run_for_cycle(cyc, now=NOW)
        assert r.get("ok") is False and r.get("status") == "MEMORY_VETO", r
        assert not calls, "veto ولی executor صدا خورد!"
        rows = [json.loads(x) for x in
                gab._missions_path().read_text("utf-8").splitlines()]
        assert rows[-1]["status"] == "blocked", rows[-1]
        assert any(str(ref).startswith("memory:")
                   for ref in rows[-1].get("input_refs") or []), \
            "veto بدونِ citation ثبت شد"
    finally:
        _ex.execute = real


def t_router_failure_never_stalls_the_chain():
    """حافظه مجوز نیست ⇒ غیاب/خطایش هم منع نیست: route ِ خراب = ادامهٔ اجرا."""
    _fresh_chain()
    real = rr.route

    def _boom(**kw):
        raise RuntimeError("router down")

    rr.route = _boom
    try:
        with _Flag(gab.FLAG, "1"), _Flag(rr.FLAG, "1"):
            cyc = "2026-07-31#12"
            p = prereg.register(_proposal(), cycle=cyc, now=NOW)
            assert p.get("ok"), p
            r = gab.run_for_cycle(cyc, now=NOW)
        assert r.get("ok") is True and r.get("receipt_status") == "EXECUTED", r
    finally:
        rr.route = real


def t_flag_off_bridge_attaches_nothing():
    _fresh_chain()
    with _Flag(gab.FLAG, "1"), _Flag(rr.FLAG, None):
        cyc = "2026-07-31#13"
        p = prereg.register(_proposal(), cycle=cyc, now=NOW)
        assert p.get("ok"), p
        r = gab.run_for_cycle(cyc, now=NOW)
    assert r.get("ok") is True, r
    assert "memories_used" not in r, ("فلگ خاموش ولی حافظه ضمیمه شد", r)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_retrieval_router: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
