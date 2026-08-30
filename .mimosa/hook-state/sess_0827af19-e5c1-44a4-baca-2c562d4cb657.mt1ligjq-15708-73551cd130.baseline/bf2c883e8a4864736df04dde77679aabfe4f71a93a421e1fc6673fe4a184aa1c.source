"""test_calibration_probe.py — واسنجیِ برخطِ بیرونی‌گرید (Brier/AURC؛ Kamoi TACL 2024).

اثباتِ ناوردی‌ها روی فیکسچرِ مصنوعیِ لِجِر زیرِ STATE_DIRِ موقت:
  • Brier روی دادهٔ معلوم = مقدارِ دقیق.
  • AURC (پروکسیِ ریسک-پوشش) روی همان داده = مقدارِ دقیق.
  • آستانهٔ abstain_below تنظیم می‌شود (زیرش خودداری).
  • ادعای بی‌جفتِ بیرونی = گرید‌نشده (از Brier کنار).
  • حقیقت فقط از لِجِرِ بیرونی (outcomes.jsonl / discoveries.jsonl) — هرگز خودگریدی.
  • لِجِرِ نبود/خالی → n=0 (بدونِ کرش).
  • بدونِ flag هیچ نوشتنی زیرِ STATE_DIR رخ نمی‌دهد؛ با flag رکورد نوشته می‌شود.
"""
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
ENV = harness.setup("calibration-probe")

import opslib             # noqa: E402
import calibration_probe as cp   # noqa: E402


# ── کمک‌ها: نوشتنِ فیکسچرِ لِجِر ────────────────────────────────────────────────
def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _clear():
    """همهٔ لِجِرها/خروجی‌ها را پاک کن تا هر تست از صفر شروع شود."""
    for p in (cp.CLAIMS, cp.OUTCOMES, cp.DISCOVERIES, cp.LATEST, cp.HISTORY):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass
    os.environ.pop(cp.FLAG, None)


# دادهٔ استانداردِ آزمون: ۴ ادعای گرید‌شده + ۱ ادعای بی‌جفت (گرید‌نشده).
#   a: conf 0.9, y 1  |  b: conf 0.8, y 1  |  c: conf 0.3, y 0  |  d: conf 0.2, y 0
#   e: conf 0.6, بدونِ حقیقتِ بیرونی → گرید‌نشده
# Brier = ((.9-1)²+(.8-1)²+(.3-0)²+(.2-0)²)/4 = (.01+.04+.09+.04)/4 = 0.045
def _seed_known():
    now = time.time()
    _write_jsonl(cp.CLAIMS, [
        {"ts": now, "key": "a", "confidence": 0.9},
        {"ts": now, "key": "b", "confidence": 0.8},
        {"ts": now, "key": "c", "confidence": 0.3},
        {"ts": now, "key": "d", "confidence": 0.2},
        {"ts": now, "key": "e", "confidence": 0.6},
    ])
    # حقیقتِ بیرونی: a,b در outcomes ؛ c,d در discoveries (اثباتِ خواندنِ هر دو لِجِر).
    _write_jsonl(cp.OUTCOMES, [
        {"ts": now, "key": "a", "correct": 1},
        {"ts": now, "key": "b", "hit": True},
        {"ts": now, "key": "z_no_key_claim", "correct": 1},   # حقیقتِ بی‌ادعا → بی‌اثر
    ])
    _write_jsonl(cp.DISCOVERIES, [
        {"ts": now, "key": "c", "resolved": 0},
        {"ts": now, "key": "d", "correct": "false"},
    ])


# ── تست‌ها ────────────────────────────────────────────────────────────────────
def t_a_brier_on_known_data():
    _clear()
    _seed_known()
    r = cp.probe()
    assert r["n"] == 4, f"باید ۴ ادعای گرید‌شده باشد، شد {r['n']}"
    assert r["ungraded"] == 1, f"ادعای e باید گرید‌نشده بماند، ungraded={r['ungraded']}"
    assert abs(r["brier"] - 0.045) < 1e-9, f"Brier باید 0.045 باشد، شد {r['brier']}"


def t_b_aurc_proxy_on_known_data():
    _clear()
    _seed_known()
    r = cp.probe()
    # مرتب بر حسبِ conf نزولی: a(y1),b(y1),c(y0),d(y0) → ریسکِ تجمعی 0,0,1/3,1/2
    # AURC = (0 + 0 + 0.3333.. + 0.5)/4 = 0.208333..
    assert abs(r["aurc"] - 0.208333) < 1e-4, f"AURC باید ~0.2083 باشد، شد {r['aurc']}"


def t_c_abstain_threshold_set():
    _clear()
    _seed_known()
    r = cp.probe()               # target_acc پیش‌فرض = 0.75
    # از صدر پایین: τ=0.9 (acc1)، τ=0.8 (acc1)، τ=0.3 (acc 2/3<0.75 → توقف) ⇒ 0.8
    assert abs(r["abstain_below"] - 0.8) < 1e-9, \
        f"آستانه باید 0.8 باشد (زیرش بی‌اعتماد)، شد {r['abstain_below']}"


def t_d_unpaired_claim_is_not_graded():
    """ادعای e (conf 0.6) هیچ حقیقتِ بیرونی ندارد → نه درست فرض می‌شود نه غلط."""
    _clear()
    _seed_known()
    r = cp.probe()
    keys = {g["key"] for g in r["graded"]}
    assert "e" not in keys, "ادعای بی‌جفت نباید گرید شود"
    assert keys == {"a", "b", "c", "d"}


def t_e_truth_only_from_external_ledger_never_self():
    """خودگریدی ممنوع: اگر خودِ ادعا فیلدِ نتیجه هم داشته باشد، نادیده گرفته می‌شود؛
    فقط لِجِرِ بیرونی حقیقت می‌سازد. ادعایی که در لِجِرِ بیرونی نیست → گرید‌نشده."""
    _clear()
    now = time.time()
    # ادعا خودش ادعا می‌کند correct=1، ولی هیچ حقیقتِ بیرونی ندارد.
    _write_jsonl(cp.CLAIMS, [{"ts": now, "key": "self", "confidence": 0.99, "correct": 1}])
    _write_jsonl(cp.OUTCOMES, [])
    _write_jsonl(cp.DISCOVERIES, [])
    r = cp.probe()
    assert r["n"] == 0, "ادعای خودگرید نباید شمرده شود (حقیقت فقط بیرونی)"
    assert r["ungraded"] == 1


def t_f_empty_and_missing_ledgers_give_n_zero():
    """لِجِرِ نبود یا خالی → n=0، بدونِ کرش، متریک‌ها None."""
    _clear()                     # هیچ فایلی وجود ندارد
    r = cp.probe()
    assert r["n"] == 0 and r["brier"] is None and r["aurc"] is None
    assert r["abstain_below"] is None and r["graded"] == []
    # فایل‌های خالی هم نباید کرش کنند
    _write_jsonl(cp.CLAIMS, [])
    _write_jsonl(cp.OUTCOMES, [])
    r2 = cp.probe()
    assert r2["n"] == 0


def t_g_no_write_without_flag():
    """بدونِ flag هیچ رکوردی زیرِ STATE_DIR نوشته نمی‌شود (additive/shadow)."""
    _clear()
    _seed_known()
    assert cp.FLAG not in os.environ
    cp.probe()
    assert not cp.LATEST.exists(), "بدونِ flag نباید calibration-latest.json ساخته شود"
    assert not cp.HISTORY.exists(), "بدونِ flag نباید calibration-log.jsonl ساخته شود"


def t_h_writes_record_only_with_flag():
    """با flagِ CORTEX_SELF_MONITOR رکوردِ فراشناختی زیرِ STATE_DIR نوشته می‌شود."""
    _clear()
    _seed_known()
    os.environ[cp.FLAG] = "1"
    try:
        cp.probe()
        assert cp.LATEST.exists(), "با flag باید calibration-latest.json نوشته شود"
        snap = json.loads(cp.LATEST.read_text("utf-8"))
        assert snap["n"] == 4 and abs(snap["brier"] - 0.045) < 1e-9
        assert "graded" not in snap, "اسنپ‌شات باید بدونِ فهرستِ graded (کوچک) باشد"
        assert cp.HISTORY.exists()
        # مسیرِ نوشته‌شده باید زیرِ STATE_DIRِ موقتِ همین تست باشد (نه vaultِ واقعی)
        assert str(opslib.STATE_DIR) in str(cp.LATEST)
    finally:
        os.environ.pop(cp.FLAG, None)


def t_i_all_correct_and_all_wrong_edges():
    """لبه‌ها: همه‌درست → خودداریِ حداقلی؛ همه‌غلط → به همه شک کن (بالای بیشینه)."""
    _clear()
    now = time.time()
    _write_jsonl(cp.CLAIMS, [
        {"ts": now, "key": "p", "confidence": 0.7},
        {"ts": now, "key": "q", "confidence": 0.4},
    ])
    _write_jsonl(cp.OUTCOMES, [
        {"ts": now, "key": "p", "correct": 1},
        {"ts": now, "key": "q", "correct": 1},
    ])
    r_all_ok = cp.probe()
    assert r_all_ok["brier"] == round((0.09 + 0.36) / 2, 6)   # (.7-1)²,(.4-1)²
    assert abs(r_all_ok["abstain_below"] - 0.4) < 1e-9        # همه‌درست → پایین‌ترین conf

    _clear()
    _write_jsonl(cp.CLAIMS, [
        {"ts": now, "key": "p", "confidence": 0.7},
        {"ts": now, "key": "q", "confidence": 0.4},
    ])
    _write_jsonl(cp.OUTCOMES, [
        {"ts": now, "key": "p", "correct": 0},
        {"ts": now, "key": "q", "correct": 0},
    ])
    r_all_wrong = cp.probe()
    assert r_all_wrong["abstain_below"] > 0.7   # حتی صدر هم غلط → بالای بیشینه


def t_j_recency_window_filters_old_claims():
    """ادعای کهنه‌تر از پنجره کنار می‌رود (فقط «اخیر» واسنجی می‌شود)."""
    _clear()
    now = time.time()
    _write_jsonl(cp.CLAIMS, [
        {"ts": now, "key": "fresh", "confidence": 0.9},
        {"ts": now - 100 * 24 * 3600, "key": "stale", "confidence": 0.9},   # ۱۰۰ روز پیش
    ])
    _write_jsonl(cp.OUTCOMES, [
        {"ts": now, "key": "fresh", "correct": 1},
        {"ts": now, "key": "stale", "correct": 1},
    ])
    r = cp.probe(within_h=cp.DEFAULT_WINDOW_H)   # پنجرهٔ ۳۰ روز
    keys = {g["key"] for g in r["graded"]}
    assert keys == {"fresh"}, f"ادعای کهنه باید فیلتر شود، graded={keys}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅ PASS' if not failed else '❌ FAIL'} test_calibration_probe: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)