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


def _counting_ask(jsonstr, tier="think"):
    calls = {"n": 0}

    def f(p, s, max_tokens=700):
        calls["n"] += 1
        return (jsonstr, tier)
    f.calls = calls
    return f


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
        r1 = sk.run(persist=True)
        _seed_state(in_fear=[])          # تغییرِ معنادار → change-gate عبور می‌کند
        r2 = sk.run(persist=True)
        assert r1["version"] == 1 and r2["version"] == 2
        assert r2["trajectory"]["focus_stable"] is True, "focus پایدار → همگرایی"
        hist = sk._history_path().read_text("utf-8").strip().splitlines()
        assert len(hist) == 2
    finally:
        sk._ask_llm = _orig


# ── بهینه‌سازی: change-gate (صفر کال روی بی‌تغییر) ──────────────────────────────
def t_change_gate_skips_llm():
    _sandbox_paths(); _seed_state(in_fear=["legs"]); _clear_doctor()
    _orig = sk._ask_llm
    mock = _counting_ask('{"focus":"legs","confidence":0.6,"pathology":[{"severity":"high"}],"topic":"t"}')
    sk._ask_llm = mock
    try:
        r1 = sk.run(persist=True)
        n1 = mock.calls["n"]
        assert r1["version"] == 1 and r1["llm_calls"] >= 1 and n1 >= 1
        hist1 = len(sk._history_path().read_text("utf-8").strip().splitlines())
        r2 = sk.run(persist=True)   # همان state → change-gate
        assert mock.calls["n"] == n1, "روی بی‌تغییر نباید LLM صدا زده شود"
        assert r2["source"] == "cached:no-change" and r2["llm_calls"] == 0
        assert r2["version"] == r1["version"], "version روی no-change بالا نمی‌رود"
        assert r2["stable_cycles"] == 1
        hist2 = len(sk._history_path().read_text("utf-8").strip().splitlines())
        assert hist2 == hist1, "history روی no-change رشد نمی‌کند"
    finally:
        sk._ask_llm = _orig


def t_hash_ignores_clock():
    _sandbox_paths(); _seed_state(beat=8000)
    h1 = sk._snapshot_hash(sk.snapshot())
    _seed_state(beat=9999)                      # فقط beat عوض شد
    assert sk._snapshot_hash(sk.snapshot()) == h1, "تغییرِ beat نباید hash را عوض کند"
    _seed_state(beat=9999, in_fear=["legs"])    # تغییرِ معنادار
    assert sk._snapshot_hash(sk.snapshot()) != h1


# ── بهینه‌سازی: adaptive hop-2 ─────────────────────────────────────────────────
def t_should_deep_dive_logic():
    prev = {"focus": "legs", "deep_dive": {"x": 1}}
    assert sk._should_deep_dive({"focus": "money", "confidence": 0.9}, prev, "money") is True   # focusِ نو
    assert sk._should_deep_dive({"focus": "legs", "confidence": 0.9, "pathology": []}, prev, "legs") is False  # پایدار+مطمئن
    assert sk._should_deep_dive({"focus": "legs", "confidence": 0.5}, prev, "legs") is True     # کم‌اطمینان
    assert sk._should_deep_dive({"focus": "legs", "confidence": 0.9, "pathology": [{"severity": "critical"}]}, prev, "legs") is True
    assert sk._should_deep_dive({"focus": "legs"}, {"focus": "legs", "deep_dive": {}}, "legs") is True  # هرگز کاوش‌نشده


def t_adaptive_hop2_skips_when_stable():
    _sandbox_paths(); _seed_state(); _clear_doctor()
    _orig = sk._ask_llm
    sk._ask_llm = _fake_ask('{"focus":"legs","confidence":0.9,"pathology":[{"severity":"low"}],"topic":"t"}')
    try:
        r1 = sk.run(persist=True)                # اولین بار: hop-2 چون prev کاوش ندارد
        assert r1["deep_dive_ran"] is True
        _seed_state(legs={"mining": {"live": False}, "ziman": {"live": True}, "new": {"live": True}})
        r2 = sk.run(persist=True)                # تغییر، ولی focus پایدار + مطمئن → فقط hop-1
        assert r2["source"].startswith("llm") and r2["llm_calls"] == 1
        assert r2["deep_dive_ran"] is False and r2["deep_dive"] == r1["deep_dive"]
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



# ═══ ۲۰۲۶-۰۷-۲۷ — قفلِ باورِ پول ═══════════════════════════════════════════
# اسکنِ خودآگاهی این را گرفت و راستی‌آزمایی شد: `physiology` به `money.musd` نگاه
# می‌کرد که **خرجِ خودِ ارگانیسم** است (telemetry.py:174 از جمعِ هزینه‌ها می‌سازدش).
# نتیجه: هر ۲۷ نسخه «درآمد>۰» در حالی که attribution.confirmed صفر بود — و همین
# جملهٔ غلط در promptِ مغزِ گران می‌رفت. برای ارگانیسمی که مأموریتش پول است، این
# بدترین باورِ ممکن بود. این سه تست اجازه نمی‌دهند برگردد.


def t_money_musd_is_never_read_as_revenue():
    snap = {"money": {"musd": 21295}, "revenue": 0.0, "legs": {}, "wire_on": []}
    u = sk._heuristic(snap, {})
    assert "درآمد صفر" in u["physiology"], u["physiology"]
    assert "درآمد>۰" not in u["physiology"], "خرج دوباره درآمد خوانده شد"


def t_real_revenue_is_reported_as_revenue():
    snap = {"money": {"musd": 21295}, "revenue": 12.5, "legs": {}, "wire_on": []}
    u = sk._heuristic(snap, {})
    assert "12.5" in u["physiology"], u["physiology"]
    assert "صفر" not in u["physiology"], u["physiology"]


def t_the_snapshot_separates_spend_from_revenue():
    s = sk.snapshot()
    assert "revenue" in s, "کلیدِ درآمد در snapshot نیست"
    assert isinstance(s["revenue"], float)
    assert "_note" in s["money"], "کلیدِ گمراه‌کنندهٔ money بدونِ هشدار ماند"
    # و تصحیح باید بتواند از پشتِ کشِ no-change بیرون بیاید
    assert "revenue" in sk._hash_digest(s),         "revenue در hash نیست — باورِ تصحیح‌شده تا تغییرِ بعدی یخ می‌ماند"


def t_the_self_model_sees_its_whole_body():
    """پرسشِ مالک ۲۰۲۶-۰۷-۲۷: «خودآگاهی‌مان با کلِ اختاپوس می‌خوانَد؟»

    اندازه‌گیریِ زنده گفت نه: خودآگاهی ۵ پا می‌دید و رجیستریِ رندر ۱۰ تا. پنج بازو
    نامرئی بودند — از جمله `ziman` که بازوی **زندهٔ** واقعی است (`money_link=active`).
    علت: snapshot فقط `business_legs` را می‌خواند، ولی `ziman`/`leg`/`cartographer`
    کلیدِ جدای خودشان را در ORGANISM-STATE دارند و هیچ‌کس جمعشان نمی‌کرد. یعنی
    «آناتومی» در هر پرامپتِ مغزِ گران نصفِ حقیقت بود.

    این تست خودبسنده است: بلوک‌ها را در سندباکس می‌کارد و می‌سنجد هر کدام سطحی
    می‌شوند — نه با درختِ زنده مقایسه می‌کند (نسخهٔ اولش همین اشتباه را کرد)."""
    _sandbox_paths()
    _seed_state()
    org = json.loads((_SB / "ORGANISM-STATE.json").read_text("utf-8"))
    org["ziman"] = {"leg_id": "ziman-gallery", "money_link": "active",
                    "propose_only": True}
    org["leg"] = {"leg_id": "lead-naghshi", "money_link": "active",
                  "propose_only": True}
    org["cartographer"] = {"leg_id": "vault-cartographer",
                           "money_link": "incubating", "propose_only": True}
    (_SB / "ORGANISM-STATE.json").write_text(json.dumps(org), "utf-8")
    (_SB / "cortex").mkdir(parents=True, exist_ok=True)
    (_SB / "cortex" / "part-loops-latest.json").write_text(
        json.dumps({"parts": [{"status": "🟢"}, {"status": "🔴"}]}), "utf-8")

    prev = os.environ.get("OCTOPUS_SELFKNOW_LEGS_UNWRAP")
    os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = "1"
    try:
        legs = sk.snapshot().get("legs") or {}
    finally:
        if prev is None:
            os.environ.pop("OCTOPUS_SELFKNOW_LEGS_UNWRAP", None)
        else:
            os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = prev

    for name in ("ziman", "lead", "cartographer", "system"):
        assert name in legs, f"خودآگاهی «{name}» را نمی‌بیند: {sorted(legs)}"
    assert legs["ziman"]["live"] is True, "بازوی زنده خاموش گزارش شد"
    assert legs["cartographer"]["live"] is False
    assert "بخشِ درونی" in str(legs["system"].get("note")), legs["system"]


def t_a_live_arm_is_reported_live():
    """زیمان با money_link=active باید live دیده شود، نه خاموش."""
    import os as _os
    _prev = _os.environ.get("OCTOPUS_SELFKNOW_LEGS_UNWRAP")
    _os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = "1"
    try:
        legs = sk.snapshot().get("legs") or {}
    finally:
        if _prev is None:
            _os.environ.pop("OCTOPUS_SELFKNOW_LEGS_UNWRAP", None)
        else:
            _os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = _prev
    z = legs.get("ziman")
    if z is not None:      # فقط وقتی بلوکِ زیمان در state هست
        assert z.get("live") is (z.get("money_link") == "active"), z


def t_the_venture_entry_is_content_free():
    """ونچر باید در آناتومی شمرده شود ولی هرگز نام/هویت/محتوا لو ندهد."""
    import os as _os, re as _re
    _prev = _os.environ.get("OCTOPUS_SELFKNOW_LEGS_UNWRAP")
    _os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = "1"
    try:
        legs = sk.snapshot().get("legs") or {}
    finally:
        if _prev is None:
            _os.environ.pop("OCTOPUS_SELFKNOW_LEGS_UNWRAP", None)
        else:
            _os.environ["OCTOPUS_SELFKNOW_LEGS_UNWRAP"] = _prev
    v = legs.get("studio_pf")
    if v is not None:
        blob = json.dumps(v, ensure_ascii=False)
        for banned in ("فنز", "OnlyFans", "onlyfans", "feet", "creator"):
            assert banned not in blob, f"نشتِ هویتِ ونچر: {banned}"

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
        ("change-gate صفر کال", t_change_gate_skips_llm),
        ("hash کلاک را نادیده", t_hash_ignores_clock),
        ("منطقِ adaptive hop-2", t_should_deep_dive_logic),
        ("hop-2 روی پایدار رد", t_adaptive_hop2_skips_when_stable),
        ("run فقط‌خواندنی", t_run_readonly),
        ("beat خاموش=no-op", t_beat_flag_off_noop),
        ("beat در ترس شلیک", t_beat_fires_under_fear),
        ("run_async گارد", t_run_async_guard),
        # ۲۰۲۶-۰۷-۲۷ — قفلِ باورِ پول. این فایل لیستِ صریح دارد نه جمع‌آوریِ
        # خودکار، پس تستِ ثبت‌نشده بی‌صدا نمی‌دود و سوییت سبز گزارش می‌شود.
        ("خرج هرگز درآمد خوانده نشود", t_money_musd_is_never_read_as_revenue),
        ("درآمدِ واقعی درآمد گزارش شود", t_real_revenue_is_reported_as_revenue),
        ("snapshot خرج و درآمد را جدا کند", t_the_snapshot_separates_spend_from_revenue),
        ("خودآگاهی کلِ بدنش را ببیند", t_the_self_model_sees_its_whole_body),
        ("بازوی زنده live گزارش شود", t_a_live_arm_is_reported_live),
        ("مدخلِ ونچر content-free بماند", t_the_venture_entry_is_content_free),
    ])
    sys.exit(1 if failed else 0)
