#!/usr/bin/env python3
"""test_selfknow_calibration.py — WS-B: دو falsifier که هرگز یک ردیف تولید نکردند.

پیش از این: `calibration_probe` بی‌عیب ساخته شده بود (Brier، AURC، جست‌وجوی آستانهٔ
خودداری) و `self_accuracy` هم — ولی n=0 **ساختاری** بود، چون تنها ادعایی که
self_model صادر می‌کرد (`self_model.coherence`) در هیچ لِجِرِ حقیقتی وجود نداشت،
و `self_accuracy` فقط برابریِ فیلد را می‌سنجید و عددِ `confidence` را اصلاً نمره
نمی‌داد.

این تست سه چیز را اثبات می‌کند:
  ۱) **فضای نامِ مشترک**: ادعا و حقیقت هر دو زیرِ `selfknow.<field>` نوشته می‌شوند،
     پس `calibration_probe` می‌تواند جفت کند (n>0 به‌جای n=0 ابدی).
  ۲) **نمرهٔ عددِ اطمینان**: Brier روی `confidence` — نه فقط تطابقِ legs/revenue/wire_on.
  ۳) **ناوردیِ ضدِ خودگریدی با دندان**: عوض‌کردنِ `confidence` از ۰.۰۵ به ۰.۹۵
     بردارِ `correct` را ذره‌ای تکان نمی‌دهد؛ فقط Brier بدتر/بهتر می‌شود.

پذیرش: فلگ خاموش → **صفر ردیف** (نه فایلِ ادعا، نه ردیفِ حقیقت)، و یک عددِ
Brierِ واقعی از دادهٔ واقعیِ جفت‌شده.

صفر شبکه · $0 · sandbox (harness) · لِجِرِ زندهٔ vault فقط **خوانده** و کپی می‌شود.
اجرا: cd F:/backup/_ops/tests && python -X utf8 test_selfknow_calibration.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness                                        # noqa: E402
ENV = harness.setup("selfknow-calibration")           # اول از همه — قبل از هر importِ opslib

# قلابِ «اثباتِ دندان»: اسکریپتِ teeth نسخهٔ pre-fixِ ماژول‌ها را در یک پوشهٔ scratch
# می‌گذارد و این متغیر را ست می‌کند؛ آن‌وقت همین تست‌ها باید **قرمز** شوند.
_PREFIX_DIR = os.environ.get("WSB_PREFIX_DIR")
if _PREFIX_DIR:
    sys.path.insert(0, _PREFIX_DIR)
for _p in (str(harness.SELF_OPS / "cortex"), str(harness.SELF_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.append(_p)

import opslib                      # noqa: E402
import calibration_probe as cp     # noqa: E402
import goal_directed as gd         # noqa: E402
import self_accuracy as sa         # noqa: E402
import self_model as sm            # noqa: E402

_SB = Path(ENV["ops"]) / "state"
_MON = "CORTEX_SELF_MONITOR"

# ── فیکسچرِ معلوم ──────────────────────────────────────────────────────────────
# حقیقت: ۲ لِگ (mining, crypto) · درآمد ۰ · wire_on = {wire_doctor}
# ادعا  : ۱ لِگ (mining)          · درآمد ۰ · wire_on = [wire_doctor]
#   ⇒ y = [legs:0, revenue:1, wire_on:1]  ·  accuracy = 2/3
#   ⇒ با confidence=0.5 → Brier = ((.5-0)² + (.5-1)² + (.5-1)²)/3 = 0.75/3 = 0.25
_CLAIMED = {"legs": {"mining": {"live": False}}, "revenue": 0.0,
            "wire_on": ["wire_doctor"], "wire_off": []}
_EXPECT_CORRECT = {"selfknow.legs": 0, "selfknow.revenue": 1, "selfknow.wire_on": 1}


def _seed_truth() -> None:
    """منبعِ حقیقتِ مستقل (state واقعیِ سندباکس) — هرگز از خودِ ادعا ساخته نمی‌شود."""
    _SB.mkdir(parents=True, exist_ok=True)
    (_SB / "ORGANISM-STATE.json").write_text(json.dumps({
        "business_legs": {"business_legs": {"mining": {"live": False},
                                            "crypto": {"live": False}}, "beat": 7},
        "wiring": {"wire_doctor": True, "wire_email": False}}), "utf-8")
    (_SB / "fitness-latest.json").write_text(
        json.dumps({"attribution": {"confirmed": 0, "revenue_by_cell": {}}}), "utf-8")


def _seed_confidence(c) -> None:
    """اطمینانِ اعلام‌شدهٔ دورِ قبل — همان جایی که self_knowledge می‌نویسدش."""
    p = _SB / "doctor" / "self-knowledge-latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = {"understanding": {"confidence": c}} if c is not None else {"understanding": {}}
    p.write_text(json.dumps(body), "utf-8")


def _reset(*, confidence=0.5) -> None:
    # getattr: زیرِ WSB_PREFIX_DIR ماژولِ pre-fix این ثابت را ندارد — نمی‌خواهیم تست‌ها
    # روی یک AttributeError در کمک‌تابع بمیرند؛ هرکدام باید روی assertِ خودش قرمز شود.
    for p in (cp.CLAIMS, cp.OUTCOMES, cp.DISCOVERIES, cp.LATEST, cp.HISTORY,
              getattr(cp, "SELF_ACCURACY", None), sa._trail_path()):
        if p is None:
            continue
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass
    os.environ.pop(_MON, None)
    os.environ.pop(sa.FLAG_NAME, None)
    _seed_truth()
    _seed_confidence(confidence)


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text("utf-8").splitlines() if ln.strip()]


def _truth_rows() -> list[dict]:
    """ردیف‌های حقیقتِ per-field داخلِ trail (خلاصه‌ها key ندارند و شمرده نمی‌شوند)."""
    return [r for r in _rows(sa._trail_path()) if r.get("key")]


# ── ۱) پذیرش: فلگ خاموش = صفر ردیف ─────────────────────────────────────────────
def t_a_monitor_off_writes_zero_rows():
    """فلگِ واسنجی خاموش → هیچ ادعایی و هیچ ردیفِ حقیقتی نوشته نمی‌شود.
    سنجش هنوز کار می‌کند (خلاصه نوشته می‌شود) ولی لِجِرِ ادعا حتی ساخته نمی‌شود."""
    _reset()
    os.environ[sa.FLAG_NAME] = "1"          # سنجش روشن، واسنجی خاموش
    try:
        r = sa.run_from_snapshot(dict(_CLAIMED))
    finally:
        os.environ.pop(sa.FLAG_NAME, None)
    assert r.get("confidence") == 0.5, r
    assert r.get("confidence_brier") == 0.25, r
    assert "claims_emitted" not in r, r
    assert not cp.CLAIMS.exists(), "فلگ خاموش ولی لِجِرِ ادعا ساخته شد"
    assert _truth_rows() == [], f"فلگ خاموش ولی {len(_truth_rows())} ردیفِ حقیقت نوشته شد"
    assert len(_rows(sa._trail_path())) == 1, "فقط یک ردیفِ خلاصه انتظار می‌رفت"


def t_b_both_flags_off_is_absolute_noop():
    """هر دو خاموش → {} و هیچ فایلی؛ byte-identical با نبودِ ماژول."""
    _reset()
    assert sa.run_from_snapshot(dict(_CLAIMED)) == {}
    assert not sa._trail_path().exists() and not cp.CLAIMS.exists()


# ── ۲) فضای نامِ مشترک ──────────────────────────────────────────────────────────
def t_c_claim_and_truth_share_one_keyspace():
    """کلیدِ ادعا == کلیدِ حقیقت. این همان چیزی است که تا امروز نبود."""
    _reset()
    os.environ[sa.FLAG_NAME] = "1"
    os.environ[_MON] = "1"
    try:
        r = sa.run_from_snapshot(dict(_CLAIMED))
    finally:
        os.environ.pop(sa.FLAG_NAME, None)
        os.environ.pop(_MON, None)
    assert r.get("claims_emitted") == 3, r
    claim_keys = {c["key"] for c in _rows(cp.CLAIMS)}
    truth_keys = {t["key"] for t in _truth_rows()}
    assert claim_keys == set(_EXPECT_CORRECT), claim_keys
    assert claim_keys == truth_keys, (claim_keys, truth_keys)
    got = {t["key"]: t["correct"] for t in _truth_rows()}
    assert got == _EXPECT_CORRECT, got


def t_d_probe_pairs_and_brier_is_exact():
    """probe واقعاً جفت می‌کند: n=3، صفر گرید‌نشده، Brier دقیقاً ۰.۲۵."""
    _reset()
    os.environ[sa.FLAG_NAME] = "1"
    os.environ[_MON] = "1"
    try:
        sa.run_from_snapshot(dict(_CLAIMED))
        res = cp.probe(persist=False)
    finally:
        os.environ.pop(sa.FLAG_NAME, None)
        os.environ.pop(_MON, None)
    assert res["n"] == 3, f"probe هنوز کور است: {res['n']} (ungraded={res['ungraded']})"
    assert res["ungraded"] == 0, res["ungraded"]
    assert abs(res["brier"] - 0.25) < 1e-9, res["brier"]
    assert {g["source"] for g in res["graded"]} == {"self_accuracy"}, res["graded"]


# ── ۳) ناوردیِ ضدِ خودگریدی (دندانِ اصلی) ───────────────────────────────────────
def t_e_confidence_can_never_move_the_truth():
    """اطمینان را از ۰.۰۵ به ۰.۹۵ ببر: بردارِ `correct` بایت‌به‌بایت همان می‌ماند.
    یعنی نمی‌شود با اعلامِ اطمینانِ بیشتر، نمرهٔ حقیقت را خرید."""
    briers, truths = [], []
    for conf in (0.05, 0.95):
        _reset(confidence=conf)
        os.environ[sa.FLAG_NAME] = "1"
        os.environ[_MON] = "1"
        try:
            r = sa.run_from_snapshot(dict(_CLAIMED))
        finally:
            os.environ.pop(sa.FLAG_NAME, None)
            os.environ.pop(_MON, None)
        briers.append(r["confidence_brier"])
        truths.append({t["key"]: t["correct"] for t in _truth_rows()})
    assert truths[0] == truths[1] == _EXPECT_CORRECT, truths
    # ((.05-0)²+(.05-1)²·2)/3 = 1.8075/3 = 0.6025 · ((.95-0)²+(.95-1)²·2)/3 = 0.9075/3 = 0.3025
    assert abs(briers[0] - 0.602500) < 1e-5, briers
    assert abs(briers[1] - 0.302500) < 1e-5, briers
    assert briers[0] != briers[1], "اطمینان اصلاً نمره نگرفت"


def t_f_absent_confidence_fabricates_nothing():
    """اطمینانِ غایب → نه Brier، نه ادعا. نبودِ شاهد، شاهدِ نبود نیست."""
    _reset(confidence=None)
    os.environ[sa.FLAG_NAME] = "1"
    os.environ[_MON] = "1"
    try:
        r = sa.run_from_snapshot(dict(_CLAIMED))
    finally:
        os.environ.pop(sa.FLAG_NAME, None)
        os.environ.pop(_MON, None)
    assert r["confidence"] is None and r["confidence_brier"] is None, r
    assert not cp.CLAIMS.exists(), "بدونِ اطمینان ادعا جعل شد"
    assert _truth_rows() == []


def t_g_confidence_scale_is_normalised():
    """۰..۱۰۰ پذیرفته و نرمال می‌شود؛ bool/رشته رد می‌شوند (نه صفرِ ساختگی)."""
    _seed_confidence(85)
    assert sa._prior_confidence() == 0.85
    _seed_confidence(True)
    assert sa._prior_confidence() is None
    _seed_confidence("0.9")
    assert sa._prior_confidence() is None
    _seed_confidence(0.4)
    assert sa._prior_confidence() == 0.4


# ── ۴) یافتهٔ صادقانه: کلیدِ گرید‌ناپذیر باید *دیده* شود ───────────────────────
def t_h_unpairable_key_is_named_not_silent():
    """`self_model.coherence` هیچ لِجِرِ حقیقتی ندارد و نمی‌تواند داشته باشد.
    به‌جای بلعیده‌شدن در یک عددِ بی‌نام، حالا در `ungraded_keys` نام می‌آید."""
    _reset()
    os.environ[_MON] = "1"
    try:
        written = sm.emit_self_claims({"self_awareness_pct": 80.0})
        res = cp.probe(persist=False)
    finally:
        os.environ.pop(_MON, None)
    assert written == 1, written
    assert res["n"] == 0 and res["ungraded"] == 1, res
    assert "self_model.coherence" in res["ungraded_keys"], res["ungraded_keys"]
    rec = _rows(cp.CLAIMS)[0]
    assert rec.get("gradeable") is False, rec


def t_i_new_truth_source_is_inert_when_absent():
    """سومین منبعِ حقیقت وقتی فایلش نیست هیچ اثری ندارد — دقیقاً وضعیتِ امروزِ vault."""
    _reset()
    assert not cp.SELF_ACCURACY.exists()
    cp.OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    cp.OUTCOMES.write_text(json.dumps({"key": "k1", "correct": 1}) + "\n", "utf-8")
    cp.CLAIMS.write_text(json.dumps({"key": "k1", "confidence": 1.0,
                                     "ts": opslib.now_iso()}) + "\n", "utf-8")
    res = cp.probe(persist=False)
    assert res["n"] == 1 and res["brier"] == 0.0, res
    assert {k: v["source"] for k, v in cp._load_truth().items()} == {"k1": "outcomes"}


# ── ۵) تحویلِ اصلی: Brierِ واقعی از لِجِرِ واقعیِ vault ─────────────────────────
def t_j_real_brier_from_live_outcomes_ledger():
    """دادهٔ واقعی: لِجِرِ زندهٔ `cortex/outcomes.jsonl` (فقط **خوانده** و کپی می‌شود)
    + همان تولیدکنندهٔ ادعای production (`goal_directed.record_intent`).
    این عدد deliverableِ WS-B است."""
    src = harness.REAL_VAULT / "_ops" / "state" / "cortex" / "outcomes.jsonl"
    if not src.exists():
        print(f"     ⏭  لِجِرِ واقعی غایب ({src}) — عددِ واقعی سنجیده نشد")
        return
    _reset()
    real = [json.loads(ln) for ln in src.read_text("utf-8", errors="replace").splitlines()
            if ln.strip()]
    cp.OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    with cp.OUTCOMES.open("w", encoding="utf-8") as fh:
        for r in real:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    closed = {str(r["key"]) for r in real if "moved" in r and r.get("key")}
    intents: dict[str, float] = {}
    for r in real:
        rid = str(r.get("id") or "")
        if rid in closed and rid not in intents and r.get("impact") is not None:
            intents[rid] = float(r["impact"])
    assert intents, "هیچ نیتِ بسته‌شده‌ای در لِجِرِ واقعی نبود"
    top = [{"id": k, "title": "-", "serves_goal": "-", "impact": v}
           for k, v in intents.items()]
    os.environ[_MON] = "1"
    try:
        for i in range(0, len(top), 3):
            gd.record_intent(top[i:i + 3])       # مسیرِ واقعیِ production
        res = cp.probe(persist=False)
    finally:
        os.environ.pop(_MON, None)
    assert res["n"] >= 1, f"جفت‌سازی روی دادهٔ واقعی شکست خورد: {res}"
    assert isinstance(res["brier"], float), res
    ones = sum(1 for g in res["graded"] if g["y"] == 1)
    print(f"     📏 دادهٔ واقعی: {len(real)} ردیفِ لِجِر · {len(closed)} کلیدِ بسته‌شده · "
          f"n={res['n']} (y=1: {ones}) · BRIER={res['brier']} · AURC={res['aurc']} · "
          f"abstain_below={res['abstain_below']}")


if __name__ == "__main__":
    checks = [(n[4:], f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_selfknow_calibration: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
