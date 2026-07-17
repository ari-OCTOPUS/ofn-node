#!/usr/bin/env python3
"""تستِ حلقهٔ خودشناسیِ عمیقِ دکتر (2026-07-18): snapshotِ غنی، فهمِ لایه‌ای، کاوشِ
دو-مرحله‌ای (multi-hop)، trajectory/خود-تصحیح، $0 محلی، fail-soft، غیرمسدودکننده،
مستقل از ترس. $0 · sandbox · صفر شبکه."""
import json
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("doctor-selfknow")
_OPS = (harness.REAL_VAULT / r"_ops")
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import self_knowledge as sk  # noqa: E402
import wiring  # noqa: E402

_SB = Path(ENV["ops"]) / "state"


def _sandbox_paths():
    opslib.STATE_DIR = _SB
    opslib.STOP_ORGANISM = Path(ENV["ops"]) / "STOP-ORGANISM"


def _seed_state(*, in_fear=None, legs=None, beat=8000, lanes=True):
    (_SB / "cortex").mkdir(parents=True, exist_ok=True)
    (_SB / "pulse").mkdir(parents=True, exist_ok=True)
    org = {"started": "2026-07-18T08:00:00", "chrono": {"beat": beat},
           "month": {"musd": 0},
           "wiring": {"wire_doctor": True, "wire_email": False, "wire_lead": True},
           "proposal_metrics": {"proposal_outcomes": 0, "proposal_value_aud": 0},
           "business_legs": legs or {"mining": {"live": False, "money_link": "incubating"},
                                     "ziman": {"live": True, "money_link": "active"}}}
    (_SB / "ORGANISM-STATE.json").write_text(json.dumps(org), "utf-8")
    (_SB / "cortex" / "stress-latest.json").write_text(
        json.dumps({"level": "🔴 ترس", "in_fear": in_fear or [], "organism_stress": 1.0}), "utf-8")
    if lanes:
        (_SB / "pulse" / "work-log.jsonl").write_text(
            json.dumps({"lane": "llm_learn", "status": "ok", "cost_usd": 0}) + "\n"
            + json.dumps({"lane": "web_research", "status": "ok"}) + "\n", "utf-8")


def _fake_ask(jsonstr, tier="think"):
    return lambda p, s, max_tokens=700: (jsonstr, tier)


def _clear_doctor():
    """سندباکسِ _SB بینِ تست‌ها مشترک است؛ برای تست‌های version/count حالتِ دکتر را صفر کن."""
    import shutil
    shutil.rmtree(_SB / "doctor", ignore_errors=True)


# ── snapshotِ غنی ─────────────────────────────────────────────────────────────
def t_snapshot_richer():
    _sandbox_paths(); _seed_state(in_fear=["legs"])
    snap = sk.snapshot()
    assert snap["beat"] == 8000
    assert snap["legs"]["ziman"]["live"] is True and snap["legs"]["mining"]["live"] is False
    assert "wire_doctor" in snap["wire_on"] and "wire_email" in snap["wire_off"]
    assert "proposal_metrics" in snap["money"]
    assert isinstance(snap["recent_errors"], dict)         # fail-soft dict
    assert isinstance(snap["recent_lanes"], list) and snap["recent_lanes"], "لِین‌ها باید خوانده شوند"
    assert "rfcs" in snap["doctor_self"]


# ── LLM: محلیِ $0 پیش‌فرض، پولی فقط با پرچم ─────────────────────────────────────
def t_ask_llm_local_by_default():
    captured = {}
    fake = types.ModuleType("model_router")

    def _ask(task, prompt, system="", max_tokens=400, tier=None, opener=None):
        captured["task"] = task
        return {"ok": True, "text": '{"focus":"x"}', "tier": task}
    fake.ask = _ask
    sys.modules["model_router"] = fake
    try:
        os.environ.pop(sk._PAID_FLAG, None)
        sk._ask_llm("p", "s")
        assert captured["task"] == "think", f"پیش‌فرض باید محلیِ $0 باشد: {captured}"
        os.environ[sk._PAID_FLAG] = "1"
        sk._ask_llm("p", "s")
        assert captured["task"] == "synthesize"
    finally:
        sys.modules.pop("model_router", None)
        os.environ.pop(sk._PAID_FLAG, None)


# ── فهمِ لایه‌ای ───────────────────────────────────────────────────────────────
def t_synthesize_layered():
    _orig = sk._ask_llm
    sk._ask_llm = _fake_ask('{"anatomy":"a","pathology":[{"symptom":"s","root_cause":"r"}],"focus":"legs","confidence":0.7}')
    try:
        out = sk.synthesize({"legs": {}}, {}, [])
        u = out["understanding"]
        assert u["focus"] == "legs" and u["pathology"][0]["root_cause"] == "r"
        assert out["source"] == "llm:think"
    finally:
        sk._ask_llm = _orig


def t_heuristic_layered():
    _orig = sk._ask_llm
    sk._ask_llm = lambda p, s, max_tokens=700: (None, "router-down")
    try:
        out = sk.synthesize({"legs": {"a": {"live": False}}, "stress": {"in_fear": ["legs"]},
                             "recent_errors": {"PriceNotLocked": 5}}, {}, [])
        assert out["source"] == "heuristic"
        u = out["understanding"]
        assert isinstance(u["pathology"], list) and u["focus"]
        assert any("ترس" in p["symptom"] for p in u["pathology"])
    finally:
        sk._ask_llm = _orig


# ── کاوشِ دو-مرحله‌ای (multi-hop) ───────────────────────────────────────────────
def t_deep_dive():
    _orig = sk._ask_llm
    sk._ask_llm = _fake_ask('{"topic":"legs","cause_chain":["a","b"],"smallest_fix":"x"}')
    try:
        d = sk.deep_dive("legs", {"legs": {}})
        assert d["topic"] == "legs" and d["cause_chain"] == ["a", "b"]
        assert sk.deep_dive(None, {}) == {}, "بدونِ focus کاوش نمی‌کند"
    finally:
        sk._ask_llm = _orig


def t_run_two_hop():
    _sandbox_paths(); _seed_state(in_fear=["legs"]); _clear_doctor()
    _orig = sk._ask_llm
    sk._ask_llm = _fake_ask('{"focus":"legs","pathology":[{"symptom":"a"}],"confidence":0.6,"topic":"legs","cause_chain":["c"]}')
    try:
        r = sk.run(persist=True)
        assert r["version"] == 1 and r["focus"] == "legs"
        assert r["deep_dive"], "مرحلهٔ ۲ (deep-dive) باید روی focus شلیک کند"
        assert "trajectory" in r
    finally:
        sk._ask_llm = _orig


def t_no_deepdive_on_heuristic():
    _sandbox_paths(); _seed_state()
    _orig = sk._ask_llm
    sk._ask_llm = lambda p, s, max_tokens=700: (None, "x")   # هیوریستیک → بدونِ hop2
    try:
        r = sk.run(persist=True)
        assert r["source"] == "heuristic"
        assert r["deep_dive"] == {}, "روی هیوریستیک نباید کاوشِ دومِ LLM بزند"
    finally:
        sk._ask_llm = _orig


# ── trajectory / خود-تصحیح ─────────────────────────────────────────────────────
def t_trajectory_converging():
    prev = {"focus": "legs", "understanding": {"confidence": 0.5}}
    u = {"focus": "legs", "confidence": 0.7}
    tj = sk._trajectory(prev, u)
    assert tj["focus_stable"] is True and tj["confidence_delta"] == 0.2 and tj["converging"] is True
    tj2 = sk._trajectory({"focus": "legs", "understanding": {"confidence": 0.6}},
                         {"focus": "money", "confidence": 0.6})
    assert tj2["focus_stable"] is False


def t_run_improves_versions():
    _sandbox_paths(); _seed_state(in_fear=["legs"]); _clear_doctor()
    _orig = sk._ask_llm
    sk._ask_llm = _fake_ask('{"focus":"legs","confidence":0.6}')
    try:
        r1 = sk.run(persist=True); r2 = sk.run(persist=True)
        assert r1["version"] == 1 and r2["version"] == 2
        assert r2["trajectory"]["focus_stable"] is True, "focus پایدار → همگرایی"
        hist = sk._history_path().read_text("utf-8").strip().splitlines()
        assert len(hist) == 2
    finally:
        sk._ask_llm = _orig


def t_run_readonly():
    _sandbox_paths(); _seed_state()
    before = (_SB / "ORGANISM-STATE.json").read_text("utf-8")
    _orig = sk._ask_llm
    sk._ask_llm = lambda p, s, max_tokens=700: (None, "x")
    try:
        sk.run(persist=True)
        assert (_SB / "ORGANISM-STATE.json").read_text("utf-8") == before
        assert sk._latest_path().exists()
    finally:
        sk._ask_llm = _orig


# ── wiring beat: خاموش/STOP/ترس ────────────────────────────────────────────────
def t_beat_flag_off_noop():
    _sandbox_paths()
    os.environ.pop("OCTOPUS_WIRE_DOCTOR_SELFKNOW", None)
    assert wiring.doctor_selfknowledge_beat(beat=9000) is None


def t_beat_fires_under_fear():
    _sandbox_paths(); _seed_state(in_fear=["legs"])
    os.environ["OCTOPUS_WIRE_DOCTOR_SELFKNOW"] = "1"
    wiring._EPOCH_STATE.pop("doctor_selfknow", None)
    called = {"n": 0}
    _orig = sk.run_async
    sk.run_async = lambda: called.__setitem__("n", called["n"] + 1) or True
    try:
        out = wiring.doctor_selfknowledge_beat(beat=9000)
        assert out == {"self_knowledge": "spawned"} and called["n"] == 1
    finally:
        sk.run_async = _orig
        os.environ.pop("OCTOPUS_WIRE_DOCTOR_SELFKNOW", None)
        wiring._EPOCH_STATE.pop("doctor_selfknow", None)


def t_run_async_guard():
    sk._running = True
    try:
        assert sk.run_async() is False
    finally:
        sk._running = False


if __name__ == "__main__":
    failed = harness.run([
        ("snapshotِ غنی", t_snapshot_richer),
        ("LLM محلیِ $0", t_ask_llm_local_by_default),
        ("فهمِ لایه‌ای", t_synthesize_layered),
        ("هیوریستیکِ لایه‌ای", t_heuristic_layered),
        ("deep-dive (hop2)", t_deep_dive),
        ("run دو-مرحله‌ای", t_run_two_hop),
        ("روی هیوریستیک بدونِ hop2", t_no_deepdive_on_heuristic),
        ("trajectory همگرایی", t_trajectory_converging),
        ("run بهبودِ نسخه‌ای", t_run_improves_versions),
        ("run فقط‌خواندنی", t_run_readonly),
        ("beat خاموش=no-op", t_beat_flag_off_noop),
        ("beat در ترس شلیک", t_beat_fires_under_fear),
        ("run_async گارد", t_run_async_guard),
    ])
    sys.exit(1 if failed else 0)
