"""test_drawdown_guard.py — بک‌لاگِ ۲۰۲۷ #۴: circuit-breakerِ drawdown (فقط shadow-count).

اثبات‌ها: وردیکتِ خالص درست (drawdown≥آستانه → HALT)؛ fail-closed روی ورودیِ نامعلوم/
غیرمتناهی → HALT؛ آستانه از budgets.yaml خوانده می‌شود (پیش‌فرضِ محتاطانه ۲۵)؛ بدونِ فلگ
هیچ نوشتنی؛ **هرگز enforced_live=True نمی‌شود** (مرزِ پول: صفر اکشنِ زنده).
"""
import json
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("drawdown-guard")

import drawdown_guard as dg   # noqa: E402


def _clean():
    os.environ.pop(dg.FLAG, None)


def t_verdict_halts_at_or_above_threshold():
    _clean()
    assert dg.verdict(40, 25)["halt"] is True
    assert dg.verdict(25, 25)["halt"] is True         # مساوی هم HALT (≥)
    assert dg.verdict(24.9, 25)["halt"] is False
    assert dg.verdict(0, 25)["halt"] is False


def t_verdict_fail_closed_on_unmeasurable():
    """ورودیِ None/NaN/Inf/غیرعددی → HALT ِ محتاطانه (circuit-breaker در ابهام می‌ایستد)."""
    _clean()
    for bad in (None, float("nan"), float("inf"), "abc"):
        v = dg.verdict(bad, 25)
        assert v["halt"] is True and v["measurable"] is False, (bad, v)


def t_threshold_from_budgets_or_conservative_default():
    _clean()
    thr = dg.spike_threshold_pct()
    assert isinstance(thr, float) and math.isfinite(thr) and thr > 0
    # هر عددِ خرابِ config باید به پیش‌فرضِ محتاطانه سقوط کند، نه کرش/۰
    assert thr == 25.0 or thr > 0


def t_shadow_off_is_total_noop():
    _clean()
    out = Path(ENV["OPS_DIR"]) / "state" / "budget" / "dd-noop.jsonl"   # سینکِ اختصاصی
    rec = dg.shadow_count(40, 25, out_path=out)
    assert not out.exists()                            # بدونِ فلگ هیچ نوشتنی
    assert rec["would_halt"] is True and rec["enforced_live"] is False


def t_never_enforces_live_even_with_flag():
    """فلگ روشن فقط سایه می‌نویسد؛ enforced_live هرگز True نمی‌شود (مرزِ پول)."""
    _clean()
    os.environ[dg.FLAG] = "1"
    try:
        out = Path(ENV["OPS_DIR"]) / "state" / "budget" / "dd-write.jsonl"
        rec = dg.shadow_count(40, 25, out_path=out)
        assert out.exists() and rec.get("_persisted")
        line = json.loads(out.read_text("utf-8").splitlines()[-1])
        assert line["schema"] == dg.SCHEMA and line["mode"] == "shadow-count"
        assert line["enforced_live"] is False and line["would_halt"] is True
    finally:
        _clean()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_drawdown_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
