"""test_cortex_rich_think_heart.py — رفعِ باگِ dumpِ خامِ dict در rich-think (2026-08-07).

پیش‌زمینه: `_ops/cortex/cortex.py::think()` پشتِ `OCTOPUS_WIRE_CORTEX_RICH_THINK`
سیگنالِ زندهٔ قلب را به prompt می‌چسباند. تا امروز `_sig = shadow.get("signal")`
یک **dict** (HeartSignal.v1: beat_seq/period_s/sigma_now/baro_factor) برمی‌گرداند و
کد `q += f" قلب: {_sig}."` کلِ dict را stringify می‌کرد → خروجی:

    قلب: {'schema': 'HeartSignal.v1', 'beat_seq': 28231, 'period_s': 325.32, ...}.

این برای مدلِ زبانی نویز است، نه سیگنالِ مفهومی. فیکس: فیلدهایِ مفهومیِ
انسان‌خواندن (ریتم/σ/baro) را پارس کن. این تست فیکس را pin می‌کند و mutation-test
می‌گیرد: اگر کسی فیلد را به dumpِ خام برگرداند، قرمز می‌شود.

اجرا: python -X utf8 test_cortex_rich_think_heart.py
"""
import io
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("cortex")

import importlib  # noqa: E402
import cortex as cx  # noqa: E402
import model_router  # noqa: E402
import opslib  # noqa: E402
for _m in (cx, model_router):
    importlib.reload(_m)

STATE = Path(ENV["ops"]) / "state"
HEART = STATE / "pulse" / "heart-shadow-latest.json"


def _capture_prompt(q_text_contains: str) -> str:
    """think() را با mockـی فراخوانی کن که promptِ دریافت‌شده را ضبط می‌کند.
    فقط نگاه می‌دارد چه رشته‌ای بعد از «قلب:» نشست — جلویِ مدل نمی‌رود."""
    captured = {}

    def _fake_ask(kind, q, max_tokens=90):
        captured["q"] = q
        return {"ok": True, "tier": "test", "text": "ok"}

    orig = cx.model_router.ask
    cx.model_router.ask = _fake_ask
    try:
        sweep = {"coherence": 0.9, "stale_members": [], "n": 3}
        cx.think(sweep, cycle=10)
    finally:
        cx.model_router.ask = orig
    return captured.get("q", "")


def _setup_flag_on():
    HEART.parent.mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_WIRE_CORTEX_RICH_THINK"] = "1"


def _setup_flag_off():
    HEART.parent.mkdir(parents=True, exist_ok=True)
    os.environ.pop("OCTOPUS_WIRE_CORTEX_THINK_RICH", None)
    os.environ["OCTOPUS_WIRE_CORTEX_RICH_THINK"] = "0"


def t_a_flag_off_no_heart_append():
    """فلگ خاموش → هیچ «قلب:»ای به prompt نمی‌چسبد (byte-identical با پیش‌فیکس)."""
    _setup_flag_off()
    HEART.write_text(json.dumps({"signal": {"period_s": 100.0, "sigma_now": 0.5}}), "utf-8")
    q = _capture_prompt("قلب")
    assert "قلب:" not in q, f"فلگ خاموش نباید قلب بچسباند: {q!r}"


def t_b_dict_signal_renders_conceptual_not_raw():
    """قلبِ اصلیِ فیکس: signal dict باید به «ریتم=Xs, σ=Y, baro=Z» رندر شود،
    نه dumpِ خامِ `{'schema': ...}`. شاهد: نباید schema/beat_seq در prompt بیفتد."""
    _setup_flag_on()
    sig = {"schema": "HeartSignal.v1", "beat_seq": 28231,
           "period_s": 325.32, "sigma_now": 0.0, "baro_factor": 5.422}
    HEART.write_text(json.dumps({"signal": sig}), "utf-8")
    q = _capture_prompt("قلب")
    assert "قلب:" in q, f"باید قلب بچسباند: {q!r}"
    assert "schema" not in q, f"dumpِ خامِ dict نباید برود: {q!r}"
    assert "beat_seq" not in q, f"فیلدِ نویز不应 leak: {q!r}"
    assert "ریتم=325s" in q, f"period_s باید مفهومی رندر شود: {q!r}"
    assert "σ=0.00" in q, f"sigma_now باید مفهومی رندر شود: {q!r}"
    assert "baro=5.4" in q, f"baro_factor باید مفهومی رندر شود: {q!r}"


def t_c_partial_signal_still_safe():
    """signal dict با فقط period_s (نبودِ sigma/baro) → فقط ریتم می‌چسبد، نه crash."""
    _setup_flag_on()
    HEART.write_text(json.dumps({"signal": {"period_s": 42.0}}), "utf-8")
    q = _capture_prompt("قلب")
    assert "ریتم=42s" in q
    assert "σ" not in q and "baro" not in q, "فیلدِ نبود نباید fake بشود"


def t_d_missing_heart_file_no_crash():
    """فایلِ heart-shadow نبود → هیچ چیزی نمی‌چسبد، نه crash (fail-soft)."""
    _setup_flag_on()
    if HEART.exists():
        HEART.unlink()
    q = _capture_prompt("قلب")
    assert "قلب:" not in q, "بدونِ فایل نباید قلب بچسبد"


def t_e_backward_compat_string_signal():
    """اگر روزی signal رشته‌ شد (نه dict)، همان خام می‌چسبد (backward-compat)."""
    _setup_flag_on()
    HEART.write_text(json.dumps({"signal": "RED"}), "utf-8")
    q = _capture_prompt("قلب")
    assert "قلب: RED." in q, f"رشته باید مستقیم برود: {q!r}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_cortex_rich_think_heart: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
