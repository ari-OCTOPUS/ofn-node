"""test_heart_fuel_wiring.py — reachabilityِ کانالِ «خون» قلب (2026-07-21).

اثبات می‌کند: هر call واقعیِ LLM از model_router.ask، سوخت را در استریمِ قلب ثبت می‌کند و
producers._count_fuel آن را می‌خواند — بستنِ orphanِ fuel_meter.record. flag خاموش = بایت‌به‌بایت
(هیچ ثبت)؛ callِ ناموفق (ok=False) هیچ ثبت نمی‌کند؛ هرگز prompt/محتوا ثبت نمی‌شود. بدونِ شبکه
(monkeypatchِ _ask_impl).
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "heart"))

import harness
ENV = harness.setup("heart-fuel-wiring")

import importlib                     # noqa: E402
import opslib                        # noqa: E402
importlib.reload(opslib)
import model_router as mr            # noqa: E402
importlib.reload(mr)
import fuel_meter as fm              # noqa: E402
importlib.reload(fm)
import heart.producers as producers  # noqa: E402
importlib.reload(producers)

_ORIG_IMPL = mr._ask_impl


def _fake_impl(ok=True, tier="local", model="qwen2.5:latest", cost=0.0):
    def _f(task, prompt, system="", max_tokens=400, tier=None, opener=None, quality=None):
        if not ok:
            return {"ok": False, "reason": "local-llm-unavailable"}
        return {"ok": True, "tier": tier, "model": model, "cost_usd": cost, "text": "SENSITIVE-CONTENT"}
    return _f


def _clear():
    os.environ.pop("OCTOPUS_WIRE_HEART_FUEL", None)


def t_a_flag_off_no_fuel_recorded():
    """flag خاموش → ask چیزی در استریمِ سوخت نمی‌نویسد (parity بایت‌به‌بایت)."""
    _clear()
    mr._ask_impl = _fake_impl(ok=True)
    try:
        r = mr.ask("think", "prompt")
    finally:
        mr._ask_impl = _ORIG_IMPL
    assert r["ok"] is True
    assert not fm.STREAM_PATH.exists(), "flag خاموش نباید سوخت ثبت کند"


def t_b_flag_on_records_fuel_and_producer_reads_it():
    """flag روشن → هر call موفق سوخت ثبت می‌کند و producers._count_fuel می‌خواند."""
    os.environ["OCTOPUS_WIRE_HEART_FUEL"] = "1"
    mr._ask_impl = _fake_impl(ok=True, tier="primary", model="fugu", cost=0.02)
    try:
        mr.ask("synthesize", "prompt-a")
        mr.ask("draft", "prompt-b")
    finally:
        mr._ask_impl = _ORIG_IMPL
        _clear()
    recs = [json.loads(l) for l in open(fm.STREAM_PATH, encoding="utf-8")]
    assert len(recs) >= 2, recs
    since = dt.datetime.now() - dt.timedelta(hours=1)
    calls, musd = producers._count_fuel(since)
    assert calls >= 2 and musd >= 20000, (calls, musd)   # 0.02 USD = 20000 micro-USD


def t_c_failed_call_records_no_fuel():
    """callِ ناموفق (ok=False) = صفر سوخت (فقط callِ واقعیِ موفق شمرده می‌شود)."""
    os.environ["OCTOPUS_WIRE_HEART_FUEL"] = "1"
    before = sum(1 for _ in open(fm.STREAM_PATH, encoding="utf-8")) if fm.STREAM_PATH.exists() else 0
    mr._ask_impl = _fake_impl(ok=False)
    try:
        r = mr.ask("think", "prompt")
    finally:
        mr._ask_impl = _ORIG_IMPL
        _clear()
    assert r["ok"] is False
    after = sum(1 for _ in open(fm.STREAM_PATH, encoding="utf-8")) if fm.STREAM_PATH.exists() else 0
    assert after == before, "callِ ناموفق نباید سوخت ثبت کند"


def t_d_never_records_content():
    """رکوردِ سوخت هرگز prompt/text/محتوا ندارد — فقط متادیتای مصرف."""
    os.environ["OCTOPUS_WIRE_HEART_FUEL"] = "1"
    mr._ask_impl = _fake_impl(ok=True)
    try:
        mr.ask("think", "SECRET-PROMPT-DO-NOT-LOG")
    finally:
        mr._ask_impl = _ORIG_IMPL
        _clear()
    body = fm.STREAM_PATH.read_text("utf-8")
    assert "SECRET-PROMPT" not in body and "SENSITIVE-CONTENT" not in body, "محتوا نباید ثبت شود"
    assert "prompt" not in body and "text" not in body


def t_e_wrapper_lazy_and_fail_soft():
    """ساختاری: wrapperِ ask، fuel را lazy import و در try/except صدا می‌زند (هرگز مسیرِ LLM را
    نمی‌کشد). گیتِ فلگ در خودِ fuel_meter.record است (t_a رفتاری اثبات کرد)."""
    src = Path(mr.__file__).read_text("utf-8")
    assert "def _ask_impl(" in src and "\ndef ask(" in src      # الگوی rename+wrapper
    seg = src.split("\ndef ask(")[-1]
    assert "import fuel_meter" in seg                           # lazy import در wrapper
    assert "except Exception" in seg                            # fail-soft
    assert fm.enabled() is False                                # flag پیش‌فرض خاموش


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_fuel_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
