"""test_speed_to_lead.py — D4 (فاز D): first-response draft card (LEG_P0-1).

اثبات می‌کند که:
  · flag خاموش = no-op مطلق (ت۱).
  · fallback template همیشه برمی‌گردد (هرگز 'هیچ') (ت۲).
  · urgency detection deterministic (ت۳).
  · quiet hours فقط scheduled-label می‌سازد، نه send (ت۴).
  · کارتِ خروجی HTML + فکت‌های لید دارد (ت۵).
  · lead_id غایب → no-op (ت۶).
  · LLM flag خاموش → fallback؛ روشن ولی خطا → fallback (fail-soft، ت۷).
  · SMS > 320 chars truncation (ت۸).

همه sandbox. flag/STOP/ACTIVATION زنده دست‌نخورده.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("speed-to-lead-d4")

import importlib                          # noqa: E402
import os                                 # noqa: E402
import speed_to_lead as stl               # noqa: E402
importlib.reload(stl)

FLAG = stl.FLAG
FLAG_LLM = stl.FLAG_LLM


def _lead(tag="L1", *, scope="repaint hallway", suburb="Mosman", name="Jane"):
    return {"lead_id": f"{tag}-uuid", "source": "telegram_manual",
            "applicant": name, "suburb": suburb,
            "request": {"scope_text": scope, "service_hint": "interior painting"},
            "contact": {"name": name, "preferred_channel": "sms"}}


def t1_flag_off_no_op():
    """flag خاموش = no-op مطلق (رفتارِ امروز)."""
    os.environ.pop(FLAG, None)
    r = stl.build_first_response(_lead("a"))
    assert r["ok"] is False and r["reason"] == "flag-off"


def t2_fallback_always_present():
    """flag روشن + LLM خاموش → fallback template همیشه برمی‌گردد (هرگز None/هیچ)."""
    os.environ[FLAG] = "1"
    os.environ.pop(FLAG_LLM, None)
    try:
        r = stl.build_first_response(_lead("b"))
        assert r["ok"] is True, f"got {r}"
        assert "draft" in r and r["draft"]["message"], "draft باید message داشته باشد"
        assert r["draft"]["source"] == "fallback"
        assert "STOP to opt out" in r["draft"]["message"], "fallback باید STOP line داشته باشد"
    finally:
        os.environ.pop(FLAG, None)


def t3_urgency_detection():
    """urgency deterministic از متن."""
    os.environ[FLAG] = "1"
    os.environ.pop(FLAG_LLM, None)
    try:
        # urgent keywords
        for kw in ("urgent", "water damage", "mould", "end of lease", "auction", "ASAP"):
            r = stl.build_first_response(_lead("u", scope=f"need painting, {kw}"))
            assert r["urgency"] == "urgent", f"keyword {kw} باید urgent باشد"
            assert r["draft"]["urgency"] == "urgent"
        # standard
        r = stl.build_first_response(_lead("s", scope="just wondering about repainting"))
        assert r["urgency"] == "standard"
    finally:
        os.environ.pop(FLAG, None)


def t4_quiet_hours_only_label():
    """quiet hours فقط scheduled-label می‌سازد، نه send. (ایمنی: self send وجود ندارد)."""
    os.environ[FLAG] = "1"
    os.environ.pop(FLAG_LLM, None)
    try:
        # یک timestamp داخلِ ساعتِ کاری (ظهرِ AEST)
        from datetime import datetime
        noon_aest = datetime(2026, 7, 21, 12, 0, tzinfo=stl._AEST)
        quiet, sched = stl._is_quiet_hours(noon_aest)
        assert quiet is False, "ظهر باید در پنجره باشد"
        # یک timestamp بیرون (شبِ AEST)
        night_aest = datetime(2026, 7, 21, 23, 0, tzinfo=stl._AEST)
        quiet2, sched2 = stl._is_quiet_hours(night_aest)
        assert quiet2 is True, "نیمه‌شب باید quiet باشد"
        assert sched2 is not None and "AEST" in sched2
        # build در حالتِ quiet: scheduled_at set می‌شود ولی draft هنوز ساخته می‌شود
        r = stl.build_first_response(_lead("q"), now=night_aest)
        assert r["ok"] is True
        assert r["scheduled_at"] is not None, "quiet باید scheduled_at set کند"
        assert "scheduled" in r["card"], "کارت باید scheduled label داشته باشد"
    finally:
        os.environ.pop(FLAG, None)


def t5_card_has_lead_facts_and_html():
    """کارتِ خروجی HTML + فکت‌های لید دارد (نام/محله/متن)."""
    os.environ[FLAG] = "1"
    os.environ.pop(FLAG_LLM, None)
    try:
        r = stl.build_first_response(_lead("c", name="Jane", suburb="Mosman",
                                            scope="repaint kitchen walls"))
        card = r["card"]
        assert "<b>" in card, "کارت باید HTML داشته باشد"
        assert "Jane" in card
        assert "Mosman" in card
        assert "repaint kitchen walls" in card
        assert "NEW LEAD" in card
        assert "Draft" in card
    finally:
        os.environ.pop(FLAG, None)


def t6_missing_lead_id_no_op():
    """lead_id غایب → no-op."""
    os.environ[FLAG] = "1"
    os.environ.pop(FLAG_LLM, None)
    try:
        bad = _lead("d")
        bad["lead_id"] = ""
        r = stl.build_first_response(bad)
        assert r["ok"] is False and r["reason"] == "no_lead_id"
    finally:
        os.environ.pop(FLAG, None)


def t7_llm_failure_falls_back():
    """LLM flag روشن ولی model_router خطا/نبود → fallback (fail-soft)."""
    os.environ[FLAG] = "1"
    os.environ[FLAG_LLM] = "1"
    try:
        # model_router احتمالاً در sandbox نصب نیست → خطا → fallback
        r = stl.build_first_response(_lead("e"))
        assert r["ok"] is True, "باید fallback کار کند"
        assert r["draft"]["source"] == "fallback", \
            f"خطای LLM باید به fallback بینجامد، got source={r['draft']['source']}"
    finally:
        os.environ.pop(FLAG, None)
        os.environ.pop(FLAG_LLM, None)


def t8_sms_truncation():
    """SMS > 320 chars truncation (Spam Act + provider limit)."""
    os.environ[FLAG] = "1"
    os.environ.pop(FLAG_LLM, None)
    try:
        # یک scope بسیار طولانی
        long_scope = "need painting " + ("very detailed " * 100)
        r = stl.build_first_response(_lead("long", scope=long_scope))
        assert r["ok"] is True
        assert len(r["draft"]["message"]) <= stl._SMS_MAX, \
            f"SMS باید ≤ {_SMS_MAX} باشد، got {len(r['draft']['message'])}"
    finally:
        os.environ.pop(FLAG, None)


def t9_card_never_contains_send_to_customer():
    """کارت به مالک است، نه به مشتری. هیچ مسیرِ send در این ماژول وجود ندارد.
    (تستِ ساختاری: build_first_response هیچ transport/telegram/smtp را صدا نمی‌زند.)"""
    os.environ[FLAG] = "1"
    os.environ.pop(FLAG_LLM, None)
    try:
        import inspect
        src = inspect.getsource(stl)
        forbidden = ["send_text(", "send_sms", "send_email", "requests.post",
                     "urllib.request", "twilio", "smtp.send", "bot.send_message"]
        for f in forbidden:
            assert f not in src, f"ماژول نباید {f} داشته باشد (R2: no send to customer)"
    finally:
        os.environ.pop(FLAG, None)


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t") and k[1:2].isdigit() and callable(v)
             and not k.startswith("test")]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, repr(e)))
            print(f"  ❌ {t.__name__}: {e!r}")
    print(f"\ntest_speed_to_lead: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
