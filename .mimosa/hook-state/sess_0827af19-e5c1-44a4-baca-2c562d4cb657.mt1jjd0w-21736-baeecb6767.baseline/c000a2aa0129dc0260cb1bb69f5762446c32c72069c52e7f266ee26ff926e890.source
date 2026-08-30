"""test_depth_guard.py — گاردِ ناوردیِ ضدِ جعبه‌سیاه (delegation depth<=2؛ no write بدونِ event).

SHADOW/مشاهده‌ای: هرگز block/mutate نمی‌کند — فقط برای هر نقض یک alert (fail-soft).
alert در تست monkeypatch می‌شود (no-op/recorder) تا هرگز به state واقعی دست نزند.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("depth_guard")

import depth_guard    # noqa: E402
import opslib         # noqa: E402

# ── monkeypatch: opslib.alert هرگز به state واقعی نرود (recorder/no-op) ──────────
_ALERTS: list = []
opslib.alert = lambda items: _ALERTS.append(items)   # depth_guard در call-time resolve می‌کند


def _reset():
    _ALERTS.clear()


def t_a_depth_2_ok():
    """عمق ۲ (چه int چه list) → بی‌نقض."""
    r = depth_guard.check_delegation(2)
    assert r["depth"] == 2 and r["ok"] is True
    r2 = depth_guard.check_delegation(["root", "A"])
    assert r2["depth"] == 2 and r2["ok"] is True


def t_b_depth_3_violation():
    """عمق ۳ (چه int چه list) → نقضِ delegation-depth."""
    r = depth_guard.check_delegation(3)
    assert r["depth"] == 3 and r["ok"] is False and "3" in r["reason"]
    r2 = depth_guard.check_delegation(["root", "A", "B"])
    assert r2["depth"] == 3 and r2["ok"] is False


def t_c_warn_depth_violation_one_alert():
    """warn روی عمق ۳ → دقیقاً یک violation و یک alert."""
    _reset()
    out = depth_guard.warn_if_violation([1, 2, 3])
    kinds = [v["kind"] for v in out["violations"]]
    assert kinds == ["delegation-depth"]
    assert len(_ALERTS) == 1                       # دقیقاً یک alert per violation


def t_d_write_without_event_violation():
    """wrote_without_event=True روی زنجیرهٔ مجاز → فقط نقضِ write-without-event."""
    _reset()
    out = depth_guard.warn_if_violation(1, wrote_without_event=True)
    kinds = [v["kind"] for v in out["violations"]]
    assert kinds == ["write-without-event"]
    assert len(_ALERTS) == 1


def t_e_both_violations_two_alerts():
    """هر دو نقض با هم → دو violation و دو alert (یک alert per violation)."""
    _reset()
    out = depth_guard.warn_if_violation([1, 2, 3], wrote_without_event=True)
    kinds = {v["kind"] for v in out["violations"]}
    assert kinds == {"delegation-depth", "write-without-event"}
    assert len(out["violations"]) == 2 and len(_ALERTS) == 2


def t_f_clean_case_no_violations_no_alert():
    """حالتِ تمیز (عمق مجاز، نوشتنِ رویداددار) → صفر violation، صفر alert."""
    _reset()
    out = depth_guard.warn_if_violation(["root", "A"], wrote_without_event=False)
    assert out["violations"] == [] and out["ok"] is True
    assert _ALERTS == []


def t_g_alert_is_fail_soft():
    """اگر خودِ opslib.alert بترکد، warn نباید crash کند (fail-soft) — و بی‌block ادامه دهد."""
    _reset()

    def _boom(_items):
        raise RuntimeError("alert sink down")

    saved = opslib.alert
    opslib.alert = _boom
    try:
        out = depth_guard.warn_if_violation([1, 2, 3], wrote_without_event=True)
        # با وجودِ شکستِ alert، violationها گزارش می‌شوند و caller نمی‌شکند
        assert len(out["violations"]) == 2 and out["ok"] is False
    finally:
        opslib.alert = saved


def t_h_fail_soft_bad_input():
    """ورودیِ نامفهوم (None/bool/str) → پیش‌فرضِ امنِ بی‌نقض، بدونِ crash."""
    assert depth_guard.check_delegation(None)["ok"] is True
    assert depth_guard.check_delegation(True)["depth"] == 0      # bool زنجیره نیست
    assert depth_guard.check_delegation("blackbox")["ok"] is True
    _reset()
    assert depth_guard.warn_if_violation(None)["violations"] == []
    assert _ALERTS == []


def t_i_containment_scrub_in_alert():
    """دفاعِ عمقی: اگر رشتهٔ ممنوع به مسیرِ alert برسد، redact شود (هیچ echoِ هویتِ Project-F)."""
    assert depth_guard._scrub("onlyfans creator") == "(redacted:containment)"
    assert depth_guard._scrub("اونلی") == "(redacted:containment)"
    assert depth_guard._scrub("normal delegation chain") == "normal delegation chain"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_depth_guard: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)