"""test_cortex.py — جلسه ۴۶: مغزِ مرکزی (registry + router سه‌مغزی + alignment کران‌دار
+ ژورنالِ ماندگار + تبِ کابین). آفلاین: ollama با opener تزریقی fake می‌شود.
"""
import io
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("cortex")

import importlib               # noqa: E402
import registry                # noqa: E402
import local_llm               # noqa: E402
import model_router            # noqa: E402
import cortex as cx            # noqa: E402
import opslib                  # noqa: E402
for _m in (registry, local_llm, model_router, cx):
    importlib.reload(_m)

STATE = Path(ENV["ops"]) / "state"


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_opener(payload: dict):
    def _open(req, timeout=None):
        return _FakeResp(json.dumps(payload).encode("utf-8"))
    return _open


def t_a_registry_awareness_and_coherence():
    """عضوِ حاضرِ تازه → آگاهی بالا؛ غایب → صفر؛ coherence وزنی و کران‌دار."""
    (STATE / "pulse").mkdir(parents=True, exist_ok=True)
    (STATE / "ORGANISM-STATE.json").write_text("{}", "utf-8")
    (STATE / "telemetry-latest.json").write_text("{}", "utf-8")
    sw = registry.sweep()
    by_id = {r["id"]: r for r in sw["members"]}
    assert by_id["organism"]["present"] and by_id["organism"]["awareness"] > 0.9
    assert by_id["heart"]["present"] is False and by_id["heart"]["awareness"] == 0.0
    assert 0.0 <= sw["coherence"] <= 1.0
    assert "heart" in sw["stale_members"]


def t_b_local_llm_fake_and_rate_limit():
    """پاسخِ fake → dict با tier=local و cost=0؛ rate-limit پشتِ‌سرِهم را می‌بُرد."""
    ok = local_llm.ask("hi", opener=_fake_opener({"response": "سلام"}), force=True)
    assert ok and ok["tier"] == "local" and ok["cost_usd"] == 0.0
    assert ok["text"] == "سلام"
    local_llm._LAST_CALL["ts"] = time.time()
    assert local_llm.ask("hi", opener=_fake_opener({"response": "x"})) is None
    bad = local_llm.ask("hi", opener=_fake_opener({}), force=True)
    assert bad is None                            # پاسخِ خالی → fail-soft


def t_c_router_paid_closed_falls_back_local():
    """ردهٔ پولی امروز بسته (phase −1) → fallback به local با دلیلِ صادق."""
    ok, why = model_router.paid_gate()
    assert ok is False and "live locked" in why
    local_llm._LAST_CALL["ts"] = 0.0              # ریستِ rate-limit تستِ قبلی
    r = model_router.ask("orchestrate", "برنامه بده",
                         opener=_fake_opener({"response": "جواب محلی"}))
    assert r["ok"] is True and r["tier"] == "local", r
    assert "fallback_from" in r and "primary" in r["fallback_from"]
    # بدونِ local → ok=False با دلیل (نه کرش، نه سکوت)
    local_llm._LAST_CALL["ts"] = 0.0
    r2 = model_router.ask("classify", "x", opener=_fake_opener({}))
    assert r2["ok"] is False and "local-llm-unavailable" in r2["reason"]


def t_c2_research_early_lever_bypasses_date():
    """اهرمِ مالک: research-early + cortex-paid → گیت باز (سپرِ تاریخ دور)؛ بدونِ paid → بسته."""
    early = model_router.ACT_RESEARCH_EARLY
    paid = model_router.ACT_CORTEX_PAID
    early.parent.mkdir(parents=True, exist_ok=True)
    try:
        early.write_text("owner", "utf-8")
        # research-early ولی بدونِ paid-flag → همچنان بسته (نیازِ تصمیمِ دوم)
        ok, why = model_router.paid_gate()
        assert ok is False and "CORTEX-PAID" in why
        paid.write_text("owner", "utf-8")
        ok2, why2 = model_router.paid_gate()
        assert ok2 is True and "research-early" in why2
    finally:
        for f in (early, paid):
            if f.exists():
                f.unlink()
    # بدونِ اهرم → سپرِ تاریخِ عادی حاکم (امروز بسته)
    ok3, why3 = model_router.paid_gate()
    assert ok3 is False and "live locked" in why3


def t_d_router_kill_switch_and_key_presence_bool():
    opslib.STOP_ORGANISM.write_text("s", "utf-8")
    try:
        assert model_router.ask("daily", "x")["reason"] == "kill-switch"
    finally:
        opslib.STOP_ORGANISM.unlink()
    keys = model_router.keys_present()
    assert set(keys) == {"fugu", "glm", "deepseek"}
    assert all(isinstance(v, bool) for v in keys.values())   # فقط bool — هرگز مقدار


def t_e_alignment_bounded_never_touches_paid():
    """کران‌ها: فقط $0، فقط ترتیب/every_s در [۰.۵×..۲×]، paid بایت‌به‌بایت، plan غایب → هیچ."""
    assert cx.align_work_plan({"coherence": 0.3, "stale_members": []})["changed"] is False
    plan_path = STATE / "pulse" / "work-plan.json"
    plan = {"schema": "work-plan.v1", "templates": [
        {"kind": "health", "every_s": 21600, "paid": False},
        {"kind": "gap_report", "every_s": 43200, "paid": False},
        {"kind": "search", "every_s": 86400, "paid": True, "goal": "g"},
        {"kind": "llm_learn", "every_s": 86400, "paid": True},
    ]}
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False), "utf-8")
    out = cx.align_work_plan({"coherence": 0.3, "stale_members": ["school"]})
    assert out["changed"] is True, out
    newp = json.loads(plan_path.read_text("utf-8"))
    kinds = [t["kind"] for t in newp["templates"]]
    assert sorted(kinds) == sorted(["health", "gap_report", "search", "llm_learn"])
    assert kinds[0] == "gap_report"               # مدرسهٔ کهنه → جلوی صف
    paid = [t for t in newp["templates"] if t.get("paid")]
    assert paid == plan["templates"][2:]          # paid بایت‌به‌بایت دست‌نخورده
    h = next(t for t in newp["templates"] if t["kind"] == "health")
    assert 21600 * 0.5 <= h["every_s"] <= 21600 * 2   # کرانِ every_s
    # بدنِ STOP → مغز فقط تماشا می‌کند
    opslib.STOP_ORGANISM.write_text("s", "utf-8")
    try:
        assert cx.align_work_plan({"coherence": 0.1, "stale_members": []})["changed"] is False
    finally:
        opslib.STOP_ORGANISM.unlink()


def t_f_run_cycle_persists_state_and_journal():
    """چرخهٔ کامل: state + ژورنالِ append-only (حافظه‌ای که با خاموش/روشن نمی‌پرد)."""
    st = cx.run_cycle(cycle=1)
    assert st["schema"] == "cortex-state.v1"
    assert cx.STATE_PATH.exists() and cx.JOURNAL_PATH.exists()
    n1 = len(cx.JOURNAL_PATH.read_text("utf-8").splitlines())
    cx.run_cycle(cycle=2)
    n2 = len(cx.JOURNAL_PATH.read_text("utf-8").splitlines())
    assert n2 == n1 + 1                           # append-only، هیچ بازنویسی
    assert "brains" in st and "rhythm" in st


def t_g_rhythm_follows_heart_shadow():
    """ریتمِ مغز = ۲× قلبِ سایه (کران ۶۰..۶۰۰)؛ بدونِ قلب → پیش‌فرض."""
    p, src = cx.heart_rhythm_period()
    assert p == cx.DEFAULT_PERIOD_S
    shadow = STATE / "pulse" / "heart-shadow-latest.json"
    shadow.write_text(json.dumps({"period_s": 45.0}), "utf-8")
    p2, src2 = cx.heart_rhythm_period()
    assert p2 == 90.0 and "قلب" in src2
    shadow.write_text(json.dumps({"period_s": 900.0}), "utf-8")
    assert cx.heart_rhythm_period()[0] == 600.0   # سقف


def t_h_cockpit_cortex_tab():
    """تبِ «مغز مرکزی» کابین: بدونِ کورتکس 🟡؛ با state → coherence/فکر. بدونِ نشتِ کلید."""
    import approval_channel as ac

    class _FH:
        def get(self, url, timeout):
            return {"ok": True, "result": []}

        def post(self, url, body, timeout_s=10.0):
            return {"ok": True}

    fh = _FH()
    ch = ac.TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                    state_dir=str(STATE),
                                    http_get=fh.get, http_post=fh.post)
    assert "cortex" in ac.TelegramApprovalChannel.TAB_PAGES
    txt = ch.dispatch_callback("menu:cortex")["text"]
    assert "مغزِ مرکزی" in txt and "coherence" in txt   # state از t_f موجود است
    assert "123:abc" not in txt


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_cortex: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
