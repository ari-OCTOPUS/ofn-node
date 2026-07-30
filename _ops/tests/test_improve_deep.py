"""test_improve_deep.py — تستِ متخاصمِ لایهٔ عمیقِ حلقهٔ خودارتقایی.

پس‌زمینه (اندازه‌گیری ۲۰۲۶-۰۷-۲۷): فکرِ improve فقط ask("think") بود — مدلِ محلیِ
رایگان، سقفِ ۹۰ توکن. لایهٔ عمیقِ تازه flag-gated به مغزِ گران می‌رود. خطرها:
  · حلقه هر ~۷ دقیقه می‌دود؛ بدونِ سقفِ داخلیِ روزانه = ۲۰۰ تماسِ گران در روز.
  · بدونِ سوزاندنِ اسلات قبل از تماس، مغزِ خراب تا نیمه‌شب هر چرخه می‌سوزاند.
  · بدونِ پینِ tier=primary، لایه بی‌صدا به مدلِ رایگان می‌رود و نمایش می‌شود.
"""
import json
import os
import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("improve-deep")

import improve  # noqa: E402

FLAG = improve.FLAG_DEEP
TOP = [{"id": "up-1", "priority": "P0", "title": "گافِ نمونه",
        "suggested_action": "فیکس", "change_level": "code", "source": "audit"}]


def _flag(on):
    if on:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


def _reset():
    for p in (improve.DEEP_SLOTS_PATH, improve.DEEP_LEDGER_PATH):
        try:
            p.unlink()
        except OSError:
            pass


def _router(text="x" * 400, ok=True, boom=False):
    m = types.ModuleType("model_router")
    calls = []

    def ask(task, prompt, system="", max_tokens=400, tier=None, **kw):
        calls.append({"task": task, "prompt": prompt, "system": system,
                      "max_tokens": max_tokens, "tier": tier})
        if boom:
            raise RuntimeError("مغز در دسترس نیست")
        return {"ok": ok, "text": text, "model": "fugu", "tier": tier}

    m.ask = ask
    m._calls = calls
    sys.modules["model_router"] = m
    return m


def _ledger_rows():
    if not improve.DEEP_LEDGER_PATH.exists():
        return []
    return [json.loads(x) for x in
            improve.DEEP_LEDGER_PATH.read_text("utf-8").splitlines() if x.strip()]


# ─── گیت‌ها ─────────────────────────────────────────────────────────────────
def t_flag_off_is_none_and_zero_llm():
    _flag(False)
    _reset()
    m = _router()
    assert improve._deep_synth(TOP, 0.5, 40) is None
    assert not m._calls and not improve.DEEP_SLOTS_PATH.exists()


def t_empty_top_burns_no_slot():
    _flag(True)
    _reset()
    try:
        m = _router()
        assert improve._deep_synth([], 0.5, 40) is None
        assert not m._calls, "با صفِ خالی مغز صدا شد"
        assert not improve.DEEP_SLOTS_PATH.exists(), "با صفِ خالی اسلات سوخت"
    finally:
        _flag(False)


# ─── سقفِ روزانه (مهم‌ترین: حلقه ~۲۰۰ بار در روز می‌دود) ─────────────────────
def t_daily_cap_is_a_hard_ceiling():
    _flag(True)
    _reset()
    try:
        m = _router()
        n_ok = sum(1 for _ in range(10)
                   if improve._deep_synth(TOP, 0.5, 40) is not None)
        assert n_ok == improve._deep_daily_cap(), f"{n_ok} از ۱۰ رد شد"
        assert len(m._calls) == improve._deep_daily_cap(), "تماس بیش از سقف"
    finally:
        _flag(False)


def t_a_new_day_reopens_the_slots():
    _flag(True)
    _reset()
    try:
        _router()
        for _ in range(improve._deep_daily_cap()):
            improve._deep_synth(TOP, 0.5, 40)
        d = json.loads(improve.DEEP_SLOTS_PATH.read_text("utf-8"))
        improve.DEEP_SLOTS_PATH.write_text(
            json.dumps({**d, "date": "2000-01-01"}), "utf-8")
        assert improve._deep_synth(TOP, 0.5, 40) is not None, "روزِ نو باز نشد"
    finally:
        _flag(False)


def t_hostile_daily_env_is_clamped():
    for bad in ("0", "-3", "999", "abc", ""):
        os.environ["CORTEX_IMPROVE_DEEP_DAILY"] = bad
        n = improve._deep_daily_cap()
        assert 0 < n <= 8, f"CORTEX_IMPROVE_DEEP_DAILY={bad!r} → {n}"
    os.environ.pop("CORTEX_IMPROVE_DEEP_DAILY", None)


# ─── سوزاندنِ اسلات قبل از تماس ──────────────────────────────────────────────
def t_an_exploding_brain_still_burns_the_slot():
    _flag(True)
    _reset()
    try:
        _router(boom=True)
        assert improve._deep_synth(TOP, 0.5, 40) is None
        d = json.loads(improve.DEEP_SLOTS_PATH.read_text("utf-8"))
        assert d["used"] == 1, "اسلات بعد از انفجار نسوخت — تکرارِ بی‌پایانِ تماسِ گران"
        rows = _ledger_rows()
        assert rows and rows[-1]["ok"] is False, "شکست در دفتر ثبت نشد"
    finally:
        _flag(False)


# ─── قراردادِ فراخوان ────────────────────────────────────────────────────────
def t_the_call_is_pinned_to_primary_with_room_and_data():
    _flag(True)
    _reset()
    try:
        m = _router()
        improve._deep_synth(TOP, 0.42, 47)
        c = m._calls[0]
        assert c["tier"] == "primary", c["tier"]
        assert c["max_tokens"] >= 800, c["max_tokens"]
        assert "0.42" in c["prompt"] and "47" in c["prompt"], "داده‌ها در prompt نیستند"
        assert "گافِ نمونه" in c["prompt"], "صفِ واقعی در prompt نیست"
        assert c["system"], "بدونِ system جوابِ کلی می‌آید"
    finally:
        _flag(False)


def t_short_answer_is_ledgered_but_not_returned():
    _flag(True)
    _reset()
    try:
        _router(text="باشه.")
        assert improve._deep_synth(TOP, 0.5, 40) is None
        rows = _ledger_rows()
        assert rows and rows[-1].get("reason") == "empty-or-short"
    finally:
        _flag(False)


def t_good_answer_lands_in_ledger_with_text():
    """جلسه‌ای که فراموش شود خرج است نه سرمایه — متن باید بماند."""
    _flag(True)
    _reset()
    try:
        _router(text="تحلیلِ عمیقِ " + "واقعی " * 60)
        out = improve._deep_synth(TOP, 0.5, 40)
        assert out and out["text"].startswith("تحلیلِ عمیقِ"), out
        rows = _ledger_rows()
        assert rows[-1]["ok"] is True and "text" in rows[-1]
    finally:
        _flag(False)


def t_the_ambient_local_layer_is_untouched_by_the_flag():
    """flag روشن یا خاموش، لایهٔ محلیِ ۹۰-توکنی نباید عوض شود — فقط این را می‌سنجیم
    که _deep_synth هرگز TASK_TIERS یا مسیرِ think را دست نمی‌زند."""
    src = (Path(improve.__file__)).read_text("utf-8")
    deep_part = src[src.index("def _deep_synth"):src.index("def _deep_ledger")]
    assert 'ask("think"' not in deep_part, "لایهٔ عمیق مسیرِ think را لمس می‌کند"
    assert 'tier="primary"' in deep_part


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_improve_deep: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
