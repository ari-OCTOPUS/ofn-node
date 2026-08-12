#!/usr/bin/env python3
"""تستِ تعمیرهای truth-map 2026-07-17 (P3/P5/P6/P7/P8/P11 + ردِ box).

P3: عصبِ درد دیگر کور نیست — error_rate/partner_stress به measure می‌رسند و بحرانِ
    چندسیگنالی pain>0.7 می‌سازد (protective_halt قابلِ‌وصول)، سلامت pain پایین.
P5: بعد از depletion خرجِ «resting» (مجانی) — spent از سقف رد نمی‌شود.
P6: SLAی spine پویا از periodِ قلب — tickِ ۹۰۰s دیگر آرتیفکتِ «نقطهٔ مرده» نمی‌سازد؛
    حساسیت به مرگِ واقعی حفظ می‌شود.
P7/P8/P11/box: کلیدهای صادق‌سازِ additive (source-scan + رفتار).
$0 · sandbox · صفر شبکه · صفر دست‌زدن به stateِ زنده.
"""
import json
import os
import sys
import time
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("truthmap-fixes")
_OPS = (harness.SELF_OPS)
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "neural"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
from neural_driver import NeuralDriver  # noqa: E402
import wiring  # noqa: E402
import cardiac  # noqa: E402
import innervation  # noqa: E402
import registry  # noqa: E402

_SANDBOX = Path(ENV["ops"]) / "state"


# ── P3: عصبِ درد ─────────────────────────────────────────────────────────────
def t_pain_crisis_reaches_protective():
    """APPLY=0: بحران → pain>0.7 → protective_proposal (نه halt اجرایی)."""
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "0"
    d = NeuralDriver()
    r = d.evaluate(beat=1,
                   rhythm={"mode_color": "RED"},
                   sensory={"error_rate": 1.0, "afferent_ratio": 1.0,
                            "partner_stress": 0.0},
                   spectral={"sigma": 0.95},
                   budget={"pct": 0.0})
    assert r["pain"]["level"] > 0.7, r["pain"]
    assert r["pain"]["protective"] is True
    prot = wiring.protective_override(r)
    assert prot["override"] is False and prot["executable"] is False
    assert prot["action"] == "protective_proposal"
    assert prot.get("shadow_alert") is True


def t_pain_healthy_stays_low():
    """سلامت (بی‌خطا، GREEN، sigma پایین) → pain پایین، بدونِ override."""
    d = NeuralDriver()
    r = d.evaluate(beat=1, rhythm={"mode_color": "GREEN"},
                   sensory={"error_rate": 0.0, "afferent_ratio": 1.0},
                   spectral={"sigma": 0.2}, budget={"pct": 0.1})
    assert r["pain"]["level"] < 0.3, r["pain"]
    assert wiring.protective_override(r)["override"] is False


def t_error_rate_actually_forwarded():
    """قبل از P3، error_rate هرگز به measure نمی‌رسید — حالا در contributors می‌نشیند."""
    d = NeuralDriver()
    pain_sig = d.nociceptor.measure(error_rate=0.8)
    assert pain_sig.contributors.get("errors") == 0.8
    r_err = d.evaluate(beat=1, sensory={"error_rate": 0.8})
    r_no = d.evaluate(beat=1, sensory={"error_rate": 0.0})
    assert r_err["pain"]["level"] > r_no["pain"]["level"], \
        "error_rate باید pain را بالا ببرد (وگرنه هنوز drop می‌شود)"


def t_bad_error_rate_failsoft():
    """error_rateِ خراب (str/None/منفی/بزرگ) → clamp، بدونِ crash."""
    d = NeuralDriver()
    for bad in (None, "", -5, 99):
        r = d.evaluate(beat=1, sensory={"error_rate": bad})
        assert 0.0 <= r["pain"]["level"] <= 1.0


# ── P5: بودجهٔ صادقِ ضربان ────────────────────────────────────────────────────
def t_resting_after_depletion():
    """با فلگِ BIO روشن: بعد از سقف، خرجِ resting — spent ثابت، resting بالا می‌رود."""
    os.environ["OCTOPUS_WIRE_BIO"] = "1"
    try:
        b = cardiac.BeatBudget(daily_cap=3, path=_SANDBOX / "cardiac-test.json")
        _SANDBOX.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            st = b.spend("active")
        assert st["depleted"] is True
        # الگوی جدیدِ organism: بعد از depletion → resting
        for _ in range(4):
            b.spend("resting")
        d = json.loads((_SANDBOX / "cardiac-test.json").read_text("utf-8"))
        assert d["spent"] == 3, f"spent نباید از سقف رد شود: {d}"
        assert d["resting"] == 4, f"resting باید شمرده شود: {d}"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BIO", None)


def t_organism_source_spends_resting_when_depleted():
    """source-scan: organism.py بعد از depletion دیگر بی‌قیدوشرط active خرج نمی‌کند."""
    src = (_OPS / "organism.py").read_text("utf-8")
    assert 'spend("resting" if _depl else "active")' in src, \
        "الگوی خرجِ صادق (P5) در organism.py نیست"


# ── P6: SLAی پویا ────────────────────────────────────────────────────────────
def _age_file(p: Path, minutes: float):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{}", "utf-8")
    old = time.time() - minutes * 60
    os.utime(p, (old, old))


def t_spine_not_dead_at_900s_tick():
    """قلبِ باز با period=900s و سنِ ۱۵٫۲min → spine دیگر «نقطهٔ مرده» نیست (رفعِ U1)."""
    innervation.STATE = _SANDBOX
    _orig = innervation.heart_period_now
    innervation.heart_period_now = lambda: 900.0
    try:
        _age_file(_SANDBOX / "ORGANISM-STATE.json", 15.2)
        r = innervation.check()
        spine = next(o for o in r["organs"] if o["id"] == "spine")
        assert spine["connected"] is True, spine
        assert spine["sla_min"] >= 17, spine
        assert "pacemaker" not in " ".join(r["dead_spots"]), r["dead_spots"]
    finally:
        innervation.heart_period_now = _orig


def t_spine_still_detects_real_death():
    """حساسیت حفظ شود: سنِ ۶۰+ دقیقه حتی با SLAی پویا → نقطهٔ مردهٔ واقعی."""
    innervation.STATE = _SANDBOX
    _orig = innervation.heart_period_now
    innervation.heart_period_now = lambda: 900.0
    try:
        _age_file(_SANDBOX / "ORGANISM-STATE.json", 75.0)
        r = innervation.check()
        spine = next(o for o in r["organs"] if o["id"] == "spine")
        assert spine["connected"] is False, "مرگِ واقعی باید همچنان دیده شود"
    finally:
        innervation.heart_period_now = _orig


def t_spine_fallback_without_heart():
    """بدونِ فایلِ قلب (hp=None) → SLAی جدولی (رفتارِ قبلی، بدونِ crash)."""
    innervation.STATE = _SANDBOX
    _orig = innervation.heart_period_now
    innervation.heart_period_now = lambda: None
    try:
        _age_file(_SANDBOX / "ORGANISM-STATE.json", 2.0)
        r = innervation.check()
        spine = next(o for o in r["organs"] if o["id"] == "spine")
        assert spine["connected"] is True and spine["sla_min"] == 5
    finally:
        innervation.heart_period_now = _orig


# ── P8: registry خود-توصیف ───────────────────────────────────────────────────
def t_registry_self_describing():
    """هر دو شاخهٔ member_awareness فیلدهای source/watches را دارند (رفعِ U11)."""
    absent = registry.member_awareness(
        {"id": "x", "file": "does-not-exist.json", "sla_s": 10, "vital": 1},
        state_dir=_SANDBOX)
    assert absent["source"] == "file-freshness" and absent["watches"]
    f = _SANDBOX / "fresh.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("{}", "utf-8")
    present = registry.member_awareness(
        {"id": "y", "file": "fresh.json", "sla_s": 100, "vital": 1},
        state_dir=_SANDBOX)
    assert present["present"] is True and present["source"] == "file-freshness"


# ── P7 + P11 + box: source/behavior ──────────────────────────────────────────
def t_cortex_journal_keys():
    """journalِ کورتکس هر دو واقعیت را می‌نویسد (کلیدِ قدیمی هم می‌ماند)."""
    src = (_OPS / "cortex" / "cortex.py").read_text("utf-8")
    assert '"align_changed"' in src and '"align_reason"' in src, "P7 غایب"
    assert '"aligned"' in src, "کلیدِ سازگاری نباید حذف شود"


def _load_cortex():
    """cortex.py را مستقیم از فایل load کن (نه پکیجِ هم‌نامِ _ops/cortex/) — همان
    الگویِ test_cortex_shadow_wiring. harness.setup از قبل OPS_DIR را به sandbox
    برده، پس STATE_DIR/STOP_ORGANISM هم sandbox‌اند: صفر دست‌زدن به stateِ زنده."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cortex_w3", str(_OPS / "cortex" / "cortex.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_W3_PLAN = {"schema": "work-plan.v1", "templates": [
    {"kind": "health", "every_s": 21600, "paid": False},
    {"kind": "gap_report", "every_s": 43200, "paid": False},
    {"kind": "search", "every_s": 86400, "paid": True}]}


def t_w3_aligned_is_not_changed():
    """W3: «هم‌راستا بود» یعنی aligned=True — نه Falseِ changed. و مسیرهای blocked
    که همان changed=False دارند باید aligned=False بمانند (پس `not changed` غلط است)."""
    cx = _load_cortex()
    pulse = _SANDBOX / "pulse"
    pulse.mkdir(parents=True, exist_ok=True)
    plan_p = pulse / "work-plan.json"
    plan_p.write_text(json.dumps(_W3_PLAN, ensure_ascii=False), "utf-8")
    sweep = {"coherence": 0.94, "stale_members": [], "members": [], "n": 3}

    a = cx.align_work_plan(sweep)              # نقشه از قبل هم‌راستا
    assert a["changed"] is False and a["reason"] == "هم‌راستا بود", a
    assert a["aligned"] is True, f"«هم‌راستا بود» ولی aligned={a.get('aligned')}"

    plan_p.unlink()                            # plan غایب = هم‌راستا نیست
    b = cx.align_work_plan(sweep)
    assert b["changed"] is False and b["aligned"] is False, b


def t_w3_journal_aligned_matches_reason():
    """رکوردِ ژورنال دیگر خودش را نقض نمی‌کند: aligned=True کنارِ «هم‌راستا بود»."""
    cx = _load_cortex()
    d = _SANDBOX / "cortex-w3"
    d.mkdir(parents=True, exist_ok=True)
    cx.CORTEX_DIR = d
    cx.STATE_PATH = d / "cortex-state.json"
    cx.JOURNAL_PATH = d / "journal.jsonl"
    cx.registry = types.SimpleNamespace(
        sweep=lambda: {"coherence": 0.94, "stale_members": [], "members": [], "n": 3})
    cx.model_router = types.SimpleNamespace(
        keys_present=lambda: [], paid_gate=lambda: (False, "no-key"))
    cx.align_work_plan = lambda sweep: {"changed": False, "aligned": True,
                                        "reason": "هم‌راستا بود"}
    cx.heart_rhythm_period = lambda: (120.0, "test")
    cx.stress_tick = lambda cycle: None
    cx.innervation_tick = lambda cycle: None
    cx.think = lambda *a, **k: None
    cx.run_cycle(1)
    rec = json.loads(cx.JOURNAL_PATH.read_text("utf-8").splitlines()[-1])
    assert rec["align_reason"] == "هم‌راستا بود", rec
    assert rec["align_changed"] is False, rec
    assert rec["aligned"] is True, f"تناقضِ W3 برگشت: {rec}"


def t_wire_summary_complete():
    """بلاکِ wiring حالا لایه‌های قبلاً-کم‌شماری‌شده را گزارش می‌کند."""
    os.environ["OCTOPUS_WIRE_HEART"] = "1"
    os.environ.pop("OCTOPUS_WIRE_EMAIL", None)
    try:
        s = wiring.wire_summary()
        for k in ("wire_heart", "wire_bio", "wire_ziman", "wire_cartographer",
                  "wire_selfheal", "wire_pocketsmith", "wire_email", "wire_mining"):
            assert k in s, f"کلیدِ {k} در wire_summary نیست (P11)"
        assert s["wire_heart"] is True and s["wire_email"] is False
    finally:
        os.environ.pop("OCTOPUS_WIRE_HEART", None)


def t_box_trace_write_exists():
    """box حالا ردِ ماندگار دارد (box-latest.json) — «armed یا زنده» تصمیم‌پذیر شد."""
    src = (_OPS / "doctor" / "doctor.py").read_text("utf-8")
    assert "box-latest.json" in src, "ردِ ماندگارِ box غایب"
    assert src.index("box-latest.json") > src.index('result["box"] = box_report'), \
        "ردِ box باید بعد از ساختِ report نوشته شود"


# ── فیکس‌های بازبینیِ خصمانهٔ 37cebf2 ────────────────────────────────────────
def t_budget_pct_unit_fixed():
    """مینِ واحد: musd (میکرو-دلار) باید قبل از تقسیم بر سقفِ دلاری تبدیل شود.
    بدونِ این، اولین خرجِ paidِ ماه pain=1.0 و protective_halt دائمی می‌ساخت."""
    src = (_OPS / "organism.py").read_text("utf-8")
    assert src.count('opslib.usd(snap["month"].get("musd", 0))') == 2, \
        "هر دو سایتِ budget_pct باید مبدلِ usd داشته باشند"
    assert 'snap["month"].get("musd", 0) / max' not in src, "تقسیمِ خامِ میکرو-دلار باقی مانده"
    # صحتِ عددی: ۳ دلار از سقفِ ۳۰ → pct=0.1 (نه ۱۰۰هزار)
    assert abs(opslib.usd(3_000_000) / 30 - 0.1) < 1e-9


def t_innervation_inf_and_cap():
    """periodِ آلوده (inf/غول‌آسا) نه crash می‌کند نه مرگ را نامرئی."""
    innervation.STATE = _SANDBOX
    _orig = innervation.heart_period_now
    try:
        _age_file(_SANDBOX / "ORGANISM-STATE.json", 2.0)
        innervation.heart_period_now = lambda: float("inf")
        r = innervation.check()   # نباید OverflowError بدهد
        spine = next(o for o in r["organs"] if o["id"] == "spine")
        assert spine["sla_min"] == 5, "inf باید نادیده گرفته شود (fallbackِ جدولی)"
        innervation.heart_period_now = lambda: 86400.0   # یک شبانه‌روز!
        r = innervation.check()
        spine = next(o for o in r["organs"] if o["id"] == "spine")
        assert spine["sla_min"] == 5, "periodِ خارج از کران (>1800s) نباید SLA را باد کند"
        innervation.heart_period_now = lambda: 1800.0
        r = innervation.check()
        spine = next(o for o in r["organs"] if o["id"] == "spine")
        assert spine["sla_min"] <= 32, "سقفِ SLA=32min — کورتر از ۹۶min نمی‌شویم"
    finally:
        innervation.heart_period_now = _orig


def t_cardiac_corrupt_file_no_keyerror():
    """فایلِ دست‌کاری‌شده بدونِ spent → spend('resting') بدونِ KeyError."""
    os.environ["OCTOPUS_WIRE_BIO"] = "1"
    try:
        p = _SANDBOX / "cardiac-corrupt.json"
        _SANDBOX.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"date": opslib.today()}), "utf-8")   # بدونِ spent/resting
        b = cardiac.BeatBudget(daily_cap=3, path=p)
        st = b.spend("resting")
        assert st["depleted"] is False and st["remaining"] == 3
    finally:
        os.environ.pop("OCTOPUS_WIRE_BIO", None)


def t_cardiac_status_day_rollover():
    """روزِ نو: status دیگر depletedِ دیروز را گزارش نمی‌کند (اولین beat دوباره active)."""
    os.environ["OCTOPUS_WIRE_BIO"] = "1"
    try:
        p = _SANDBOX / "cardiac-rollover.json"
        p.write_text(json.dumps({"date": "2020-01-01", "spent": 999, "resting": 0}), "utf-8")
        b = cardiac.BeatBudget(daily_cap=3, path=p)
        st = b.status()
        assert st["depleted"] is False and st["spent"] == 0, st
    finally:
        os.environ.pop("OCTOPUS_WIRE_BIO", None)


def t_neural_nan_inf_neutralized():
    """NaN/inf در ورودی‌های حسی → defaultِ سالم، صفر crash، صفر مسمومیتِ sticky."""
    d = NeuralDriver()
    nan = float("nan")
    r = d.evaluate(beat=1, sensory={"afferent_ratio": nan, "error_rate": nan,
                                    "partner_stress": float("inf")},
                   spectral={"sigma": 0.0}, budget={"pct": 0.0})
    assert r["pain"]["level"] < 0.1, "NaN باید به defaultِ سالم بیفتد نه مقدارِ مسموم"
    r2 = d.evaluate(beat=1, sensory={"error_rate": 99})
    assert 0.0 <= r2["pain"]["level"] <= 1.0


if __name__ == "__main__":
    failed = harness.run([
        ("[P3] بحران → protective_proposal (ADR-034)", t_pain_crisis_reaches_protective),
        ("[P3] سلامت → pain پایین", t_pain_healthy_stays_low),
        ("[P3] error_rate واقعاً forward می‌شود", t_error_rate_actually_forwarded),
        ("[P3] ورودیِ خراب fail-soft", t_bad_error_rate_failsoft),
        ("[P5] بعد از depletion → resting", t_resting_after_depletion),
        ("[P5] organism الگوی صادق دارد", t_organism_source_spends_resting_when_depleted),
        ("[P6] tickِ ۹۰۰s دیگر آرتیفکت نمی‌سازد", t_spine_not_dead_at_900s_tick),
        ("[P6] مرگِ واقعی همچنان دیده می‌شود", t_spine_still_detects_real_death),
        ("[P6] بدونِ قلب → رفتارِ قبلی", t_spine_fallback_without_heart),
        ("[P8] registry خود-توصیف", t_registry_self_describing),
        ("[P7] کلیدهای journal", t_cortex_journal_keys),
        ("[W3] aligned ≠ changed", t_w3_aligned_is_not_changed),
        ("[W3] ژورنال خودش را نقض نمی‌کند", t_w3_journal_aligned_matches_reason),
        ("[P11] بلاکِ wiring کامل", t_wire_summary_complete),
        ("[box] ردِ ماندگار", t_box_trace_write_exists),
        ("[rev] واحدِ budget_pct درست شد", t_budget_pct_unit_fixed),
        ("[rev] inf/غول‌آسا در innervation", t_innervation_inf_and_cap),
        ("[rev] فایلِ خراب بدونِ KeyError", t_cardiac_corrupt_file_no_keyerror),
        ("[rev] rolloverِ روزِ status", t_cardiac_status_day_rollover),
        ("[rev] NaN/inf خنثی می‌شود", t_neural_nan_inf_neutralized),
    ])
    sys.exit(1 if failed else 0)
