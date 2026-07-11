"""test_live_cockpit.py — جلسه ۴۶: اتاقِ کنترلِ زنده (8773).

تجمیعِ fail-soft از state، صداقتِ new_code_live، اقدام‌های مالک در vault موقت
(هرگز بدنِ واقعی را لمس نمی‌کند — مسیرها از opslib.OPS)، و بدونِ نشتِ secret.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "live"))

import harness
ENV = harness.setup("live-cockpit")

import importlib      # noqa: E402
import server as live  # noqa: E402
importlib.reload(live)
import opslib          # noqa: E402

STATE = Path(ENV["ops"]) / "state"


def t_a_aggregate_fail_soft_empty_vault():
    """vault موقتِ خالی: هیچ کرش؛ صداقت: heart/cortex غایب، کدِ نو false."""
    d = live.aggregate(probe=lambda p: False)
    assert d["processes"] == {"organism": False, "cortex": False,
                              "ollama": False, "dashboard": False}
    assert d["new_code_live"] is False
    assert d["heart"]["present"] is False
    assert d["cortex"]["present"] is False
    assert isinstance(d["needs"]["items"], list)
    assert d["stops"]["organism"] is False


def t_b_aggregate_reads_all_sections():
    """با state ساختگی: بدن/قلب/مغز/پمپ همه در خروجی — و new_code_live=true."""
    (STATE / "pulse").mkdir(parents=True, exist_ok=True)
    (STATE / "cortex").mkdir(parents=True, exist_ok=True)
    (STATE / "ORGANISM-STATE.json").write_text(json.dumps(
        {"month": {"aud": 1.5}, "chrono": {"beat": 42},
         "wiring": {"wire_doctor": True, "profile": "paper-full"},
         "heart": {"period_shadow_s": 60}}), "utf-8")
    (STATE / "pulse" / "heart-shadow-latest.json").write_text(json.dumps(
        {"period_s": 60.0, "gate0_live_producer": False,
         "production_wire": {"open": False, "reasons": ["a", "b"]}}), "utf-8")
    (STATE / "cortex" / "cortex-state.json").write_text(json.dumps(
        {"coherence": 0.8, "stale_members": [], "thought": "خوبم",
         "rhythm": {"period_s": 120}, "brains": {"keys": {"fugu": False}}}), "utf-8")
    (STATE / "pulse" / "work-plan.json").write_text(json.dumps(
        {"schema": "work-plan.v1",
         "templates": [{"kind": "health", "paid": False}]}), "utf-8")
    # جلسه ۴۶ — لایهٔ فراشناختی: تحقیق/خودمدل/سنتز هم بخشِ پنل‌اند
    (STATE / "pulse" / "research-latest.json").write_text(json.dumps(
        {"schema": "research-latest.v1", "n_topics": 2,
         "findings": [{"topic": "rl", "n": 3, "hits": [{"title": "RL intro"}]}]}), "utf-8")
    (STATE / "cortex" / "self-model.json").write_text(json.dumps(
        {"schema": "self-model.v1", "n_modules": 109, "total_lines": 23107,
         "self_awareness_pct": 100.0, "n_wire_flags": 12}), "utf-8")
    (STATE / "cortex" / "synthesis-latest.json").write_text(json.dumps(
        {"schema": "synthesis.v1", "tier": "secondary", "cost_usd": 0.0,
         "proposals": [{"title": "سایه‌زنی", "first_step": "flag"}]}), "utf-8")
    d = live.aggregate(probe=lambda p: p == 8771)
    assert d["processes"]["organism"] is True and d["processes"]["cortex"] is False
    assert d["new_code_live"] is True
    assert d["body"]["beat"] == 42 and d["body"]["month_aud"] == 1.5
    assert d["heart"]["present"] is True and d["heart"]["period_shadow_s"] == 60.0
    assert len(d["heart"]["wire_reasons"]) == 2
    assert d["cortex"]["coherence"] == 0.8
    assert d["pump"]["plan"][0]["kind"] == "health"
    assert d["research"]["n_topics"] == 2 and d["research"]["topics"][0]["topic"] == "rl"
    assert d["self_model"]["n_modules"] == 109 and d["self_model"]["awareness_pct"] == 100.0
    assert d["synthesis"]["tier"] == "secondary" and d["synthesis"]["proposals"][0]["title"] == "سایه‌زنی"


def t_c_actions_isolated_to_env_ops():
    """restart-organism فقط دو فایلِ flag در OPSِ تست می‌سازد (بدنِ واقعی امن)؛
    stop-cortex همان‌جا؛ اقدامِ ناشناخته رد."""
    ops = Path(ENV["ops"])
    r = live.do_action("restart-organism")
    assert r["ok"] is True
    assert (ops / "STOP-ORGANISM").exists()
    assert (ops / "RESTART-REQUESTED").exists()
    # (ایزولاسیون با OPS=tmp در همین دو asserт بالا اثبات است — به state واقعی وابسته نشو)
    (ops / "STOP-ORGANISM").unlink()
    (ops / "RESTART-REQUESTED").unlink()
    r2 = live.do_action("stop-cortex")
    assert r2["ok"] is True and (ops / "STOP-CORTEX").exists()
    (ops / "STOP-CORTEX").unlink()
    assert live.do_action("bogus")["ok"] is False
    # start-cortex: اگر مغزِ واقعی روی 8772 زنده باشد «از قبل زنده» (بدونِ Popen)؛
    # وگرنه در vault تست batی نیست → ردِ صادق. هر دو مسیر بدونِ side-effectِ کور.
    r3 = live.do_action("start-cortex")
    assert isinstance(r3, dict) and "note" in r3
    if r3["ok"]:
        assert "زنده" in r3["note"]


def t_d_no_secret_leak_and_hologram_page():
    """خروجیِ تجمیعی از پاسِ redaction می‌گذرد؛ صفحهٔ هولوگرام: قلبِ تپنده +
    گره‌های اعضا + چت + اقدام — و members برای رنگِ گره‌ها در API هست."""
    out = live._redact(json.dumps(live.aggregate(probe=lambda p: False),
                                  ensure_ascii=False))
    assert "TELEGRAM" not in out.upper() or "TOKEN" not in out.upper()
    for marker in ("هولوگرام", "heartG", "cohRing", "nodePos", "LABELS",
                   "/api/live", "/api/ask", "restart-organism"):
        assert marker in live.PAGE, marker
    d = live.aggregate(probe=lambda p: False)
    assert "members" in d["cortex"]              # خوراکِ رنگِ گره‌ها


def t_e_registry_card_fail_soft():
    """کارتِ registry در /ops: _registry_summary همیشه dict ِ fail-soft می‌دهد،
    و OPS_PAGE کارت + خواندنِ d.registry را دارد. (vault موقت خالی → present با total=0)."""
    reg = live._registry_summary()
    assert isinstance(reg, dict) and "present" in reg
    if reg.get("present"):
        assert "counts" in reg and isinstance(reg.get("entities"), list)
    st = live.ops_state()
    assert "registry" in st                                # در خروجیِ /api/ops هست
    for marker in ("regCard", "رجیستری", "d.registry"):
        assert marker in live.OPS_PAGE, marker


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_live_cockpit: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
