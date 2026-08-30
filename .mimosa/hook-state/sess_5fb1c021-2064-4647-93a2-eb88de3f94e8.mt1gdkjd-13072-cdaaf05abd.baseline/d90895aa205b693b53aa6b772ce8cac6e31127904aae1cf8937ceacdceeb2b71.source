#!/usr/bin/env python3
"""test_suite_delta_eval.py — up-1363aae4df: shadow-eval واقعی به‌جای stub.

گزارشِ deep-synth (۲۰۲۶-۰۸-۰۸ ۱۵:۴۹): «measured_lift._default_eval هنوز stub است؛
بنابراین وصل‌کردنِ apply_merge یا تکمیلِ self-analysis loop می‌تواند تغییرِ بدون
سنجشِ واقعی را ارتقا دهد.» این تست ادعا می‌کند:

  الف) _default_eval وقتی یک suite_fn قابل‌اجرا دریافت کند، suite-delta واقعی
     می‌سنجد: یک fixِ پس‌رونده (regression) → lift منفی/صفر → drop؛ یک fixِ
     بی‌تأثیر → lift ~0؛ یک fixِ بهبودیافته → lift > 0.
  ب) رفتارِ fallback (وقتی suite_fn نیست) همچنان severity-based است ولی صادقانه
     stub می‌گوید (نه ادعای «measured»).
  ج) measured_lift یک suite_fn پذیرفتنیِ inject شده را به eval_fn می‌رساند.
  د) production لمس نمی‌شود (evolution همچنان stdlib-only).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402

_DR = (harness.SELF_OPS / "doctor")
if str(_DR) not in sys.path:
    sys.path.insert(0, str(_DR))

from evolution import measured_lift, _default_eval  # noqa: E402


# ═══ الف) suite-delta واقعی ═══════════════════════════════════════════════════

def t_suite_delta_regression_detected():
    """یک suite_fn که پسِ اعمالِ fix تعدادِ pass کمتر می‌دهد → lift باید منفی/صفر
    باشد (regression). stubِ قدیمی به severity نگاه می‌کرد و این را نمی‌دید."""
    # suite_fn: (rfc) → dict با pass/total. این یک harness قابل‌تزریق است.
    def suite_fn(rfc):
        # شبیه‌سازی: fix حاویِ "break" → suite از ۱۰ به ۷ pass افت می‌کند
        if "break" in str(rfc.get("fix", "")).lower():
            return {"pass": 7, "total": 10, "baseline_pass": 10}
        # fixِ سالم → هیچ تغییر
        return {"pass": 10, "total": 10, "baseline_pass": 10}

    # regression: suite_fn نشان می‌دهد پس‌رفت
    rfc_bad = {"evidence": {"severity": "critical"}, "fix": "break the tests"}
    result = _default_eval(rfc_bad, {}, suite_fn=suite_fn)
    assert result["lift"] <= 0.0, (
        f"regression باید lift≤0 بدهد، نه {result['lift']} (stubِ قدیمی به severity نگاه می‌کرد)")


def t_suite_delta_neutral_is_zero():
    """fixِ بی‌تأثیر → lift ~0 (نه severity-based مثبتِ ساختگی)."""
    def suite_fn(rfc):
        return {"pass": 10, "total": 10, "baseline_pass": 10}

    rfc = {"evidence": {"severity": "critical"}, "fix": "innocuous comment"}
    result = _default_eval(rfc, {}, suite_fn=suite_fn)
    assert abs(result["lift"]) < 1e-9, (
        f"fixِ بی‌تأثیر باید lift=0 بدهد، نه {result['lift']} (severity=critical قبلاً 0.5ِ ساختگی می‌داد)")


def t_suite_delta_improvement_positive():
    """fix که suite را بهتر می‌کند → lift > 0."""
    def suite_fn(rfc):
        if "fix" in str(rfc.get("fix", "")).lower() and "real" in str(rfc.get("fix", "")).lower():
            return {"pass": 10, "total": 10, "baseline_pass": 8}
        return {"pass": 8, "total": 10, "baseline_pass": 8}

    rfc = {"evidence": {"severity": "low"}, "fix": "a real fix"}
    result = _default_eval(rfc, {}, suite_fn=suite_fn)
    assert result["lift"] > 0.0, (
        f"fixِ بهبودیافته باید lift>0 بدهد، نه {result['lift']}")


# ═══ ب) fallbackِ صادقانه ══════════════════════════════════════════════════════

def t_fallback_is_honestly_labeled():
    """وقتی suite_fn نیست، fallback severity-based است ولی detail صادقانه می‌گوید
    stub است (نه ادعای «measured»)."""
    rfc = {"evidence": {"severity": "high"}, "fix": "some fix"}
    result = _default_eval(rfc, {})
    assert "stub" in result.get("detail", "").lower() or "estimate" in result.get("detail", "").lower(), (
        f"fallback باید صادقانه بگوید stub/estimate است، نه: {result.get('detail')}")


# ═══ ج) measured_lift suite_fn را به eval_fn می‌رساند ══════════════════════════

def t_measured_lift_uses_injected_suite_fn():
    """measured_lift یک suite_fn می‌پذیرد و آن را به _default_eval می‌رساند.
    بدونِ این، doctor نمی‌تواند suite-runner واقعی تزریق کند."""
    def suite_fn(rfc):
        # همیشه regression → drop
        return {"pass": 0, "total": 10, "baseline_pass": 10}

    rfc = {"evidence": {"severity": "critical"}, "fix": "anything"}
    result = measured_lift(rfc, suite_fn=suite_fn)
    assert result["dropped"] is True, (
        f"regression باید drop شود، نه {result}")


def t_measured_lift_custom_eval_takes_precedence():
    """اگر هم eval_fn و هم suite_fn داده شوند، eval_fn ارجح است (تست‌های قدیمی)."""
    def custom(rfc, baseline):
        return {"lift": 0.9, "detail": "custom"}
    def suite_fn(rfc):
        return {"pass": 0, "total": 10, "baseline_pass": 10}

    rfc = {"evidence": {"severity": "low"}}
    result = measured_lift(rfc, eval_fn=custom, suite_fn=suite_fn)
    assert result["lift"] == 0.9, f"eval_fn باید ارجح باشد، نه {result}"


# ═══ د) production لمس نمی‌شود ═════════════════════════════════════════════════

def t_no_production_import():
    """evolution همچنان stdlib-only است."""
    import evolution
    src = open(evolution.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "subprocess"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


if __name__ == "__main__":
    failed = harness.run([
        ("[1] regression شناسایی می‌شود", t_suite_delta_regression_detected),
        ("[1] fixِ بی‌تأثیر lift=0", t_suite_delta_neutral_is_zero),
        ("[1] fixِ بهبودیافته lift>0", t_suite_delta_improvement_positive),
        ("[2] fallbackِ صادقانه", t_fallback_is_honestly_labeled),
        ("[3] suite_fn به eval می‌رسد", t_measured_lift_uses_injected_suite_fn),
        ("[3] eval_fn ارجح است", t_measured_lift_custom_eval_takes_precedence),
        ("[G] stdlib-only", t_no_production_import),
    ])
    sys.exit(1 if failed else 0)
