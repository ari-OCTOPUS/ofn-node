#!/usr/bin/env python3
"""test_deep_gate_authoritative.py — VQ-DEEP-GATE-AUTHORITATIVE-001 (رأیِ مالک ۰۸-۰۳).

بلایندسپات #۱۳۸، سنجیده‌شده در ممیزیِ ۰۸-۰۳: `autonomy_matrix.is_important` و
`auto_approve.classify` هر دو فقط سه کلیدِ **سطحِ اول** را می‌خوانند
(`title`/`action`/`suggested_action`). پس یک مبلغِ تودرتو مثلِ
`{"params": {"amount_aud": 500}}` برایشان یک بلابِ خالی است ⇒ «غیرمهم» ⇒
خودتصمیم، بدونِ گیتِ مالک.

`decision_gate` دقیقاً برای بستنِ همین سوراخ ساخته شده بود (با `flatten()` ِ
بازگشتی) — ولی فقط به‌عنوانِ **سایه** وصل بود و نتیجه‌اش دور ریخته می‌شد. یعنی
فیکس نوشته و تست‌شده بود و در عمل هیچ کاری نمی‌کرد.

قرارداد بعد از رفع:
  · فلگ خاموش  → رفتارِ بایت‌به‌بایتِ قبلی (هیچ رگرسیونی برای مسیرهای موجود).
  · فلگ روشن   → خوانندهٔ عمیق می‌تواند **فقط escalate** کند.
  · هرگز نمی‌تواند چیزی را که کم‌عمق مهم دانسته آزاد کند (یک‌جهته).
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("deep-gate-authoritative")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import auto_approve as aa  # noqa: E402
import decision_gate as dg  # noqa: E402

FLAG = dg.FLAG

#: مبلغِ واقعی، ولی **تودرتو** — دقیقاً شکلی که خوانندهٔ کم‌عمق نمی‌بیند.
NESTED_MONEY = {"id": "p-nested-1", "title": "تنظیمِ روتین",
                "params": {"amount_aud": 500}}


def _with_flag(value, fn):
    prev = os.environ.get(FLAG)
    if value is None:
        os.environ.pop(FLAG, None)
    else:
        os.environ[FLAG] = value
    try:
        return fn()
    finally:
        if prev is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = prev


def t_a_the_shallow_readers_really_are_blind():
    """پیش‌شرطِ کلِ این تست: اثبات کن سوراخ واقعی است، نه فرضی."""
    import autonomy_matrix as am
    imp, _why = am.is_important(NESTED_MONEY)
    assert imp is False, ("اگر این True شد یعنی خوانندهٔ کم‌عمق دیگر کور نیست و "
                          "این تست باید بازنویسی شود", imp)
    assert aa.classify(NESTED_MONEY) != "high", aa.classify(NESTED_MONEY)


def t_b_the_deep_reader_sees_it():
    """`decision_gate` با flatten ِ بازگشتی همان مبلغ را می‌بیند."""
    destroy, why = dg.destruction_risk(dg.flatten(NESTED_MONEY))
    assert destroy is True, ("خوانندهٔ عمیق مبلغِ تودرتو را ندید", why)


def t_c_flag_off_is_byte_identical_to_before():
    """فلگ خاموش ⇒ هیچ رگرسیونی. مسیرِ قبلی دست‌نخورده."""
    out = _with_flag(None, lambda: aa.decide(dict(NESTED_MONEY)))
    assert out["action"] != "escalate" or "عمیق" not in out.get("reason", ""), out


def t_d_flag_on_escalates_the_nested_amount():
    """قلبِ رفع: با فلگِ روشن، همان پیشنهاد به مالک می‌رود."""
    out = _with_flag("1", lambda: aa.decide(dict(NESTED_MONEY)))
    assert out["action"] == "escalate", (
        "مبلغِ تودرتو هنوز از گیت رد می‌شود — سوراخِ #۱۳۸ باز است", out)
    assert "عمیق" in out.get("reason", ""), out


def t_e_the_deep_gate_can_only_escalate_never_free():
    """یک‌جهته بودن: چیزی که کم‌عمق «مهم» دانسته، هرگز آزاد نمی‌شود."""
    money = {"id": "p-plain", "title": "پرداختِ صورتحساب", "action": "pay"}
    import autonomy_matrix as am
    assert am.is_important(money)[0] is True, "پیش‌شرط: این باید مهم باشد"
    for flag in (None, "1"):
        out = _with_flag(flag, lambda: aa.decide(dict(money)))
        assert out["action"] == "escalate", (flag, out)


def t_f_a_harmless_proposal_is_not_escalated_by_the_deep_gate():
    """ضدِ مثبتِ کاذب: پیشنهادِ بی‌خطر با فلگِ روشن هم به مالک نمی‌رود."""
    benign = {"id": "p-benign", "title": "کادنسِ نمونه‌برداری را نرم کن",
              "action": "HEART_SAMPLE_INTERVAL_S", "change_level": "tune"}
    off = _with_flag(None, lambda: aa.decide(dict(benign)))
    on = _with_flag("1", lambda: aa.decide(dict(benign)))
    assert on["action"] == off["action"], ("فلگ رفتارِ بی‌خطر را عوض کرد", off, on)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, repr(e)))
            print(f"  FAIL {t.__name__}: {e!r}")
    print(f"\ntest_deep_gate_authoritative: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
