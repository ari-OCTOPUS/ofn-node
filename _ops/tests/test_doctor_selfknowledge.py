#!/usr/bin/env python3
"""تستِ حلقهٔ خودشناسیِ دکتر (2026-07-18): فعال از بوت، $0 محلی، ذخیره + بهبودِ نسخه‌ای،
fail-soft، غیرمسدودکننده، و مستقل از ترس (یادگیری ≠ تغییر). $0 · sandbox · صفر شبکه."""
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


def _seed_state(*, in_fear=None, legs=None, beat=8000):
    (_SB / "cortex").mkdir(parents=True, exist_ok=True)
    org = {"started": "2026-07-18T08:00:00", "chrono": {"beat": beat},
           "month": {"musd": 0},
           "wiring": {"wire_doctor": True, "wire_email": False},
           "business_legs": legs or {"mining": {"live": False}, "ziman": {"live": True}}}
    (_SB / "ORGANISM-STATE.json").write_text(json.dumps(org), "utf-8")
    (_SB / "cortex" / "stress-latest.json").write_text(
        json.dumps({"level": "🔴 ترس", "in_fear": in_fear or [], "organism_stress": 1.0}), "utf-8")


def _sandbox_paths():
    opslib.STATE_DIR = _SB
    opslib.STOP_ORGANISM = Path(ENV["ops"]) / "STOP-ORGANISM"


# ── snapshot ($0، read-only) ─────────────────────────────────────────────────
def t_snapshot_structure():
    _sandbox_paths(); _seed_state(in_fear=["legs"])
    snap = sk.snapshot()
    assert snap["beat"] == 8000
    assert "ziman" in snap["legs_alive"] and "mining" in snap["legs_dead"]
    assert snap["stress"]["in_fear"] == ["legs"]
    assert "wire_doctor" in snap["wire_on"]


# ── LLM routing: محلی پیش‌فرض ($0)، پولی فقط با پرچم ─────────────────────────────
def t_ask_llm_local_by_default():
    captured = {}
    fake = types.ModuleType("model_router")

    def _ask(task, prompt, system="", max_tokens=400, tier=None, opener=None):
        captured["task"] = task
        return {"ok": True, "text": '{"summary":"ok"}', "tier": task}
    fake.ask = _ask
    sys.modules["model_router"] = fake
    try:
        os.environ.pop(sk._PAID_FLAG, None)
        sk._ask_llm("p", "s")
        assert captured["task"] == "think", f"پیش‌فرض باید محلیِ $0 باشد: {captured}"
        os.environ[sk._PAID_FLAG] = "1"
        sk._ask_llm("p", "s")
        assert captured["task"] == "synthesize", "با پرچم باید tierِ پولیِ گیت‌دار شود"
    finally:
        sys.modules.pop("model_router", None)
        os.environ.pop(sk._PAID_FLAG, None)


# ── synthesize: JSONِ LLM parse می‌شود؛ نبودش → هیوریستیک ──────────────────────
def t_synthesize_parses_llm_json():
    _orig = sk._ask_llm
    sk._ask_llm = lambda p, s: ('اینم فهمم: {"summary":"خوبه","stuck":["x"],"confidence":0.7} تمام', "think")
    try:
        out = sk.synthesize({"legs_alive": []}, {})
        assert out["understanding"]["summary"] == "خوبه"
        assert out["source"] == "llm:think"
    finally:
        sk._ask_llm = _orig


def t_heuristic_when_no_llm():
    _orig = sk._ask_llm
    sk._ask_llm = lambda p, s: (None, "router-down")
    try:
        out = sk.synthesize({"legs_alive": [], "legs_dead": ["a"],
                             "stress": {"in_fear": ["legs"]}}, {})
        assert out["source"] == "heuristic"
        assert any("ترس" in x for x in out["understanding"]["stuck"])
    finally:
        sk._ask_llm = _orig


# ── run: ذخیره + بهبودِ نسخه‌ای («هی بهبود بده») ──────────────────────────────
def t_run_persists_and_improves():
    _sandbox_paths(); _seed_state(in_fear=["legs"])
    _orig = sk._ask_llm
    sk._ask_llm = lambda p, s: ('{"summary":"v","confidence":0.6}', "think")
    try:
        r1 = sk.run(persist=True)
        assert r1["version"] == 1
        assert sk._latest_path().exists()
        # دورِ دوم: نسخه +۱ و فهمِ قبلی به‌عنوان ورودی خوانده می‌شود (بهبودِ تدریجی)
        r2 = sk.run(persist=True)
        assert r2["version"] == 2, "version باید هر دور بالا برود"
        hist = sk._history_path().read_text("utf-8").strip().splitlines()
        assert len(hist) == 2, "تاریخچه باید هر دور یک خط اضافه کند"
    finally:
        sk._ask_llm = _orig


def t_run_readonly_only_writes_doctor_dir():
    """run فقط فایل‌های دانشِ خودش را می‌نویسد — نه ORGANISM-STATE و نه چیزِ دیگر."""
    _sandbox_paths(); _seed_state()
    before = (_SB / "ORGANISM-STATE.json").read_text("utf-8")
    _orig = sk._ask_llm
    sk._ask_llm = lambda p, s: (None, "x")   # heuristic path
    try:
        sk.run(persist=True)
        assert (_SB / "ORGANISM-STATE.json").read_text("utf-8") == before, "state نباید دست بخورد"
        assert sk._latest_path().exists() and sk._history_path().exists()
    finally:
        sk._ask_llm = _orig


# ── wiring beat: خاموش=no-op، STOP=no-op، و مستقل از ترس ────────────────────────
def t_beat_flag_off_noop():
    _sandbox_paths()
    os.environ.pop("OCTOPUS_WIRE_DOCTOR_SELFKNOW", None)
    assert wiring.doctor_selfknowledge_beat(beat=9000) is None


def t_beat_stop_noop():
    _sandbox_paths()
    os.environ["OCTOPUS_WIRE_DOCTOR_SELFKNOW"] = "1"
    wiring._EPOCH_STATE.pop("doctor_selfknow", None)
    try:
        opslib.STOP_ORGANISM.write_text("stop", "utf-8")
        assert wiring.doctor_selfknowledge_beat(beat=9000) is None
    finally:
        opslib.STOP_ORGANISM.unlink(missing_ok=True)
        os.environ.pop("OCTOPUS_WIRE_DOCTOR_SELFKNOW", None)


def t_beat_fires_under_fear():
    """با flag روشن و ترسِ فعال، beat همچنان شلیک می‌کند (یادگیری قفلِ ترس ندارد)."""
    _sandbox_paths(); _seed_state(in_fear=["legs"])
    os.environ["OCTOPUS_WIRE_DOCTOR_SELFKNOW"] = "1"
    wiring._EPOCH_STATE.pop("doctor_selfknow", None)
    called = {"n": 0}
    _orig = sk.run_async
    sk.run_async = lambda: called.__setitem__("n", called["n"] + 1) or True
    try:
        out = wiring.doctor_selfknowledge_beat(beat=9000)   # boot: epoch huge, last=0 → fires
        assert out == {"self_knowledge": "spawned"}, out
        assert called["n"] == 1, "با ترسِ فعال هم باید شلیک کند"
    finally:
        sk.run_async = _orig
        os.environ.pop("OCTOPUS_WIRE_DOCTOR_SELFKNOW", None)
        wiring._EPOCH_STATE.pop("doctor_selfknow", None)


# ── run_async: غیرمسدودکننده + گاردِ overlap ───────────────────────────────────
def t_run_async_guard_no_overlap():
    sk._running = True   # وانمود کن دورِ قبلی هنوز تمام نشده
    try:
        assert sk.run_async() is False, "با دورِ در حالِ اجرا نباید دومی spawn شود"
    finally:
        sk._running = False


if __name__ == "__main__":
    failed = harness.run([
        ("snapshot ساختار", t_snapshot_structure),
        ("LLM پیش‌فرض محلیِ $0", t_ask_llm_local_by_default),
        ("synthesize JSON را parse می‌کند", t_synthesize_parses_llm_json),
        ("بی‌LLM → هیوریستیک", t_heuristic_when_no_llm),
        ("run ذخیره + بهبودِ نسخه‌ای", t_run_persists_and_improves),
        ("run فقط‌خواندنی روی state", t_run_readonly_only_writes_doctor_dir),
        ("beat خاموش=no-op", t_beat_flag_off_noop),
        ("beat STOP=no-op", t_beat_stop_noop),
        ("beat در ترس هم شلیک می‌کند", t_beat_fires_under_fear),
        ("run_async گاردِ overlap", t_run_async_guard_no_overlap),
    ])
    sys.exit(1 if failed else 0)
