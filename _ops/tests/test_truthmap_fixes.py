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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("truthmap-fixes")
_OPS = (harness.REAL_VAULT / r"_ops")
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
    """بحرانِ چندسیگنالی (خطا+RED+sigma بالا) → pain>0.7 → protective_halt."""
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
    assert prot["override"] is True and prot["action"] == "protective_halt"
    assert prot["suppressible"] is False, "protective باید غیرقابل‌سرکوب باشد"


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


if __name__ == "__main__":
    failed = harness.run([
        ("[P3] بحران → protective_halt", t_pain_crisis_reaches_protective),
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
        ("[P11] بلاکِ wiring کامل", t_wire_summary_complete),
        ("[box] ردِ ماندگار", t_box_trace_write_exists),
    ])
    sys.exit(1 if failed else 0)
