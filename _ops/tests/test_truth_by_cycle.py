"""test_truth_by_cycle.py — کلیدِ حقیقت = (پیشنهاد + دور) — WS-1 (۲۰۲۶-۰۷-۲۹).

مسئله‌ای که این تست قفل می‌کند: `_load_truth` قدیم `truth[k] = ...` می‌کرد، پس
۲۲۴ رکوردِ حقیقتِ لِجِرِ زنده به **۸ کلید** فرومی‌ریخت و مقدارِ نهایی به **ترتیبِ
نوشتن** وابسته می‌شد — یعنی «حقیقت» را می‌شد با جابه‌جا کردنِ دو خطِ فایل عوض کرد.

دندانِ تست (هر ادعا با بازسازیِ رفتارِ پیشا-فیکس سنجیده می‌شود):
  `_OLD_load_truth` دقیقاً الگوریتمِ دیروز است. هر تستی که ناوردیِ تازه را ادعا
  می‌کند، همان ورودی را به `_OLD_...` هم می‌دهد و **ثابت می‌کند آن‌جا می‌شکند**.
  تستی که پیش و پس از فیکس سبز باشد تست نیست.

ناوردی‌ها:
  • فلگ خاموش (پیش‌فرض) = بایت‌به‌بایتِ دیروز.
  • دورهای متفاوتِ یک پیشنهاد = ردیف‌های جدا.
  • دورِ خودمتناقض (هم y=0 هم y=1) → حذف، نه رأی‌گیری با ترتیبِ نوشتن.
  • ترتیبِ خطوطِ فایل هیچ اثری روی حقیقت ندارد (ناوردیِ اصلی).
  • جفت‌سازی هرگز به آینده نگاه نمی‌کند؛ هر ردیفِ حقیقت حداکثر یک بار گرید می‌شود.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("truth-by-cycle")

import opslib                      # noqa: E402
import calibration_probe as cp     # noqa: E402

_FLAG = cp.FLAG_BY_CYCLE


# ── بازسازیِ رفتارِ پیشا-فیکس (منبعِ «دندان») ────────────────────────────────────
def _OLD_load_truth() -> dict:
    """الگوریتمِ دقیقِ `_load_truth`ِ ۲۰۲۶-۰۷-۲۸: truth[k] = ... (آخرین نوشته برنده).
    هر تستِ زیر ثابت می‌کند این تابع روی همان ورودی **می‌شکند**."""
    truth: dict = {}
    for src, path in (("outcomes", cp.OUTCOMES), ("discoveries", cp.DISCOVERIES),
                      ("self_accuracy", cp.SELF_ACCURACY)):
        for rec in cp._read_jsonl(path):
            k = cp._key(rec)
            y = cp._binary(rec)
            if k is None or y is None:
                continue
            truth[k] = {"y": y, "source": src}
    return truth


# ── کمک‌ها ────────────────────────────────────────────────────────────────────
def _write(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _clear() -> None:
    for p in (cp.CLAIMS, cp.OUTCOMES, cp.DISCOVERIES, cp.SELF_ACCURACY,
              cp.LATEST, cp.HISTORY):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass
    os.environ.pop(_FLAG, None)


def _on() -> None:
    os.environ[_FLAG] = "1"


# ── ۱) فلگ خاموش = بایت‌به‌بایتِ دیروز ──────────────────────────────────────────
def t_a_flag_off_is_byte_identical_to_pre_fix():
    """پیش‌فرض (فلگ غایب) باید *دقیقاً* همان چیزی بدهد که الگوریتمِ دیروز می‌داد."""
    _clear()
    _write(cp.OUTCOMES, [
        {"ts": "2026-07-20T10:00:00", "key": "up-a", "moved": True},
        {"ts": "2026-07-21T10:00:00", "key": "up-a", "moved": False},
        {"ts": "2026-07-21T10:00:00", "key": "up-b", "moved": True},
    ])
    assert cp._load_truth() == _OLD_load_truth(), "فلگ خاموش رفتار را عوض کرد"
    assert len(cp._load_truth()) == 2


# ── ۲) دور، ردیف‌ها را جدا می‌کند (ادعای مرکزیِ WS-1) ───────────────────────────
def t_b_distinct_cycles_are_distinct_truth_rows():
    """یک پیشنهاد در سه دور = سه ردیفِ حقیقت. دیروز = یک ردیف (۶۷٪ داده دور ریخته)."""
    _clear()
    _write(cp.OUTCOMES, [
        {"ts": "2026-07-20T10:00:00", "key": "up-a", "moved": True},
        {"ts": "2026-07-21T10:00:00", "key": "up-a", "moved": False},
        {"ts": "2026-07-22T10:00:00", "key": "up-a", "moved": True},
    ])
    rows = cp._truth_rows()
    assert len(rows) == 3, f"باید ۳ ردیف باشد، شد {len(rows)}"
    assert {r["cycle"] for r in rows} == {"2026-07-20T10:00:00",
                                          "2026-07-21T10:00:00",
                                          "2026-07-22T10:00:00"}
    assert [r["y"] for r in sorted(rows, key=lambda x: x["cycle"])] == [1, 0, 1]
    # دندان: الگوریتمِ دیروز روی همین ورودی فقط ۱ ردیف می‌سازد و دو رأی را می‌بلعد.
    assert len(_OLD_load_truth()) == 1, "بازسازیِ پیشا-فیکس باید فرو بریزد"


# ── ۳) ناوردیِ اصلی: ترتیبِ نوشتن نباید حقیقت را عوض کند ────────────────────────
def t_c_write_order_cannot_change_truth():
    """همان رکوردها با ترتیبِ معکوس → حقیقتِ یکسان. این قلبِ خرابیِ دیروز است."""
    _clear()
    recs = [
        {"ts": "2026-07-20T10:00:00", "key": "up-a", "moved": True},
        {"ts": "2026-07-21T10:00:00", "key": "up-a", "moved": False},
    ]
    _write(cp.OUTCOMES, recs)
    fwd = cp._truth_rows()
    old_fwd = _OLD_load_truth()
    _write(cp.OUTCOMES, list(reversed(recs)))
    rev = cp._truth_rows()
    old_rev = _OLD_load_truth()
    key = lambda rs: sorted((r["key"], r["cycle"], r["y"]) for r in rs)   # noqa: E731
    assert key(fwd) == key(rev), f"حقیقت به ترتیبِ نوشتن وابسته ماند: {fwd} != {rev}"
    # دندان: الگوریتمِ دیروز روی همین دو ترتیب دو حقیقتِ **متفاوت** می‌دهد.
    assert old_fwd != old_rev, "بازسازیِ پیشا-فیکس باید به ترتیب وابسته باشد"
    assert old_fwd["up-a"]["y"] == 0 and old_rev["up-a"]["y"] == 1


# ── ۴) تناقضِ درون-دور: حذف، نه رأی‌گیری ────────────────────────────────────────
def t_d_contradiction_inside_one_cycle_is_dropped_not_voted():
    """یک دور که هم «جابه‌جا شد» و هم «نشد» گفته، حقیقتی ندارد → کنار می‌رود.
    (۴۱ جفت از ۱۸۳ جفتِ لِجِرِ زنده دقیقاً همین‌اند — زخمِ پیش از _dedupe_intents.)"""
    _clear()
    _write(cp.OUTCOMES, [
        {"ts": "2026-07-27T12:07:31", "key": "up-x", "moved": True},
        {"ts": "2026-07-27T12:07:31", "key": "up-x", "moved": False},   # همان دور، متناقض
        {"ts": "2026-07-27T13:00:00", "key": "up-x", "moved": False},   # دورِ سالم
    ])
    rows = cp._truth_rows()
    assert len(rows) == 1, f"دورِ متناقض باید حذف شود، rows={rows}"
    assert rows[0]["cycle"] == "2026-07-27T13:00:00" and rows[0]["y"] == 0
    assert cp._truth_contradictions() == 1
    # دندان: دیروز همین ورودی یک y می‌داد که فقط از ترتیبِ خطوط می‌آمد.
    assert len(_OLD_load_truth()) == 1 and _OLD_load_truth()["up-x"]["y"] == 0


# ── ۵) فیلدِ صریحِ cycle اگر روزی نوشته شود، مقدم است ────────────────────────────
def t_e_explicit_cycle_field_wins_over_ts():
    """امروز چنین فیلدی در لِجِر نیست (ts جایگزینِ صادق است)، ولی اگر بیاید مقدم شود."""
    _clear()
    _write(cp.OUTCOMES, [
        {"ts": "2026-07-20T10:00:00", "cycle": "c1", "key": "up-a", "moved": True},
        {"ts": "2026-07-20T10:00:01", "cycle": "c1", "key": "up-a", "moved": True},
        {"ts": "2026-07-20T10:00:02", "cycle": "c2", "key": "up-a", "moved": False},
    ])
    rows = cp._truth_rows()
    assert {r["cycle"] for r in rows} == {"c1", "c2"}, rows
    assert len(rows) == 2, "دو رکوردِ هم-دور باید یک ردیف شوند (نه سه)"


# ── ۶) جفت‌سازی: بدونِ نگاهِ به آینده ────────────────────────────────────────────
def t_f_claim_after_the_cycle_never_grades_it():
    """ادعایی که *بعد* از بسته‌شدنِ دور گفته شده حق ندارد آن دور را گرید کند."""
    _clear()
    _on()
    _write(cp.OUTCOMES, [{"ts": "2026-07-20T10:00:00", "key": "up-a", "moved": True}])
    _write(cp.CLAIMS, [{"ts": "2026-07-25T10:00:00", "key": "up-a", "confidence": 1.0}])
    r = cp.probe(within_h=24 * 365, persist=False)
    assert r["n"] == 0, f"نگاهِ به آینده رخ داد: {r['graded']}"
    assert r["truth_rows"] == 1 and r["truth_rows_ungraded"] == 1
    # و ادعایی که *پیش* از دور گفته شده، گرید می‌کند.
    _write(cp.CLAIMS, [{"ts": "2026-07-19T10:00:00", "key": "up-a", "confidence": 1.0}])
    r2 = cp.probe(within_h=24 * 365, persist=False)
    assert r2["n"] == 1 and r2["brier"] == 0.0, r2


def t_g_each_truth_row_is_graded_at_most_once():
    """۵ ادعای پیاپی برای یک پیشنهاد، یک دور → یک جفت (نه ۵). وگرنه وزنِ Brier
    با «چند بار ادعا کردم» جابه‌جا می‌شود، نه با «چقدر درست بودم»."""
    _clear()
    _on()
    _write(cp.OUTCOMES, [{"ts": "2026-07-20T12:00:00", "key": "up-a", "moved": False}])
    _write(cp.CLAIMS, [{"ts": f"2026-07-20T0{i}:00:00", "key": "up-a",
                        "confidence": 0.9} for i in range(1, 6)])
    r = cp.probe(within_h=24 * 365, persist=False)
    assert r["n"] == 1, f"یک ردیفِ حقیقت {r['n']} بار گرید شد"
    assert r["n_claims"] == 5 and r["ungraded"] == 4
    assert r["graded"][0]["confidence"] == 0.9   # آخرین ادعای پیش از دور


def t_h_latest_claim_before_the_cycle_is_the_one_graded():
    """ادعا می‌تواند به‌روز شود؛ آنکه در لحظهٔ بسته‌شدنِ دور «زنده» بود گرید می‌شود."""
    _clear()
    _on()
    _write(cp.OUTCOMES, [{"ts": "2026-07-20T12:00:00", "key": "up-a", "moved": True}])
    _write(cp.CLAIMS, [
        {"ts": "2026-07-20T01:00:00", "key": "up-a", "confidence": 0.1},
        {"ts": "2026-07-20T11:00:00", "key": "up-a", "confidence": 0.8},   # زنده
        {"ts": "2026-07-20T13:00:00", "key": "up-a", "confidence": 0.0},   # بعدِ دور
    ])
    r = cp.probe(within_h=24 * 365, persist=False)
    assert r["n"] == 1 and r["graded"][0]["confidence"] == 0.8, r["graded"]
    assert abs(r["brier"] - 0.04) < 1e-9, r["brier"]


# ── ۷) لنگرِ داده‌ی واقعی: شمارشِ لِجِرِ زندهٔ vault (فقط خوانده/کپی می‌شود) ──────
def t_i_real_ledger_row_counts():
    """عددِ پذیرشِ WS-1 روی لِجِرِ واقعی: ۸ ردیف (دیروز) → >۱۰۰ ردیف (امروز).
    فایلِ زنده فقط **خوانده** و به STATE_DIRِ موقت کپی می‌شود؛ هرگز نوشته نمی‌شود."""
    src = harness.REAL_VAULT / "_ops" / "state" / "cortex" / "outcomes.jsonl"
    if not src.exists():
        print(f"     ⏭  لِجِرِ واقعی غایب ({src}) — شمارشِ واقعی سنجیده نشد")
        return
    _clear()
    cp.OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    cp.OUTCOMES.write_bytes(src.read_bytes())
    before = len(_OLD_load_truth())
    after = len(cp._truth_rows())
    dropped = cp._truth_contradictions()
    print(f"     ↳ لِجِرِ واقعی: ردیفِ حقیقت {before} → {after} "
          f"(+{dropped} دورِ متناقضِ حذف‌شده)")
    assert before <= 12, f"انتظار ~۸ کلید در حالتِ دیروز، شد {before}"
    assert after > 100, f"کلیدِ دور-محور باید >۱۰۰ ردیف بدهد، شد {after}"
    assert after > before * 5, (before, after)
    # فلگ خاموش روی همین دادهٔ واقعی هم باید بایت‌به‌بایتِ دیروز بماند.
    os.environ.pop(_FLAG, None)
    assert cp._load_truth() == _OLD_load_truth()


def t_j_claims_absent_means_none_not_a_number():
    """بدونِ ادعا روی دیسک، Brier باید None باشد — نه صفر، نه حدس. این ناوردی
    همان چیزی است که سه گزارشِ جعلیِ پیشین را ممکن کرده بود."""
    _clear()
    _on()
    _write(cp.OUTCOMES, [{"ts": "2026-07-20T10:00:00", "key": "up-a", "moved": True}])
    assert not cp.CLAIMS.exists()
    r = cp.probe(within_h=24 * 365, persist=False)
    assert r["brier"] is None and r["n"] == 0, r
    assert r["truth_rows"] == 1, r          # حقیقت هست، ادعا نیست → None، نه عدد


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    assert len(checks) >= 10, f"شمارِ تست غیرمنتظره: {len(checks)}"
    failed = harness.run(checks)
    print(f"\n{'✅ PASS' if not failed else '❌ FAIL'} test_truth_by_cycle: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
