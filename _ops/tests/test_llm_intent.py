#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for llm_intent — LLM understands & proposes, NEVER executes; gate can only be raised.
All LLM calls are mocked (no network); verifies parsing, validation, fail-safe, defense-in-depth."""
import os
import sys

_OPS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_OPS, "telegram_center"))
import llm_intent as li


def _brain(payload_text):
    return lambda task, prompt, system="", max_tokens=200: {"ok": True, "tier": "local", "text": payload_text}


def test_flag_default_off():
    os.environ.pop(li.FLAG, None)
    assert li.enabled() is False
    os.environ[li.FLAG] = "1"
    assert li.enabled() is True
    os.environ.pop(li.FLAG, None)


def test_empty_text_fails_safe():
    assert li.understand("", ask_fn=_brain("{}"))["ok"] is False


def test_parses_valid_proposal():
    out = li.understand("تست‌ها رو اجرا کن", ask_fn=_brain(
        '{"intent":"code","target_leg":"lead","action":"اجرای تست","risk":"low",'
        '"summary":"تست‌های تلگرام","needs_mission":true}'))
    assert out["ok"] is True
    assert out["intent"] == "code" and out["target_leg"] == "lead"
    assert out["needs_mission"] is True


def test_important_raises_gate_even_if_llm_says_low():
    # LLM claims low-risk, but text has a hard keyword -> autonomy_matrix forces high + mission
    out = li.understand("این فایل رو حذف کن", ask_fn=_brain(
        '{"intent":"leg_action","target_leg":null,"action":"حذف","risk":"low","summary":"حذف فایل","needs_mission":false}'))
    assert out["ok"] is True
    assert out["risk"] == "high"          # gate RAISED, never lowered
    assert out["needs_mission"] is True
    assert out["important"] is True and out["gate_reason"]


def test_unparseable_llm_output_fails_safe():
    out = li.understand("یه کاری کن", ask_fn=_brain("سلام، البته! چه کاری؟ (no json)"))
    assert out["ok"] is False and out["reason"] == "unparseable"


def test_llm_no_answer_fails_safe():
    out = li.understand("کاری کن", ask_fn=lambda *a, **k: {"ok": False, "reason": "budget-capped"})
    assert out["ok"] is False and out["reason"] == "llm-no-answer"


def test_llm_exception_never_crashes():
    def boom(*a, **k):
        raise RuntimeError("network down")
    out = li.understand("کاری کن", ask_fn=boom)
    assert out["ok"] is False and out["reason"].startswith("llm-error")


def test_invalid_fields_normalized():
    out = li.understand("وضعیت چطوره", ask_fn=_brain(
        '{"intent":"NONSENSE","target_leg":"marsians","action":"x","risk":"extreme","summary":"s","needs_mission":false}'))
    assert out["ok"] is True
    assert out["intent"] == "unknown"     # invalid -> unknown
    assert out["target_leg"] is None      # invalid leg -> None
    assert out["risk"] in ("low", "medium", "high")


# ─── ارتقا وقتی مغزِ محلی در پنجرهٔ انصافش است (2026-07-26) ──────────────────
def test_escalates_to_paid_only_when_local_is_unavailable():
    """اندازه‌گیریِ زنده: OLLAMA_MIN_INTERVAL_S=20s، پس پیامِ دومِ مالک در آن پنجره
    `local-llm-unavailable` می‌گیرد و به منوی ثابت سقوط می‌کند. یک انسانِ منتظر
    هم‌کلاسِ یک beatِ پس‌زمینه نیست. چهار پیامِ پشتِ‌سرِهم: ۲/۴ بدونِ ارتقا، ۴/۴ با آن."""
    calls = []

    def fake(task, prompt, system="", max_tokens=200, tier=None):
        calls.append(tier)
        if tier is None:
            return {"ok": False, "reason": "local-llm-unavailable"}
        return {"ok": True, "tier": "primary",
                "text": '{"intent":"status","risk":"low","summary":"س","needs_mission":false}'}

    os.environ.pop("OCTOPUS_TG_ASK_ESCALATE", None)
    calls.clear()
    r = li.understand("چه خبر؟", ask_fn=fake)
    assert r["ok"] is False and r["reason"] == "llm-no-answer", r
    assert calls == [None], f"با فلگِ خاموش نباید ارتقا بدهد: {calls}"

    os.environ["OCTOPUS_TG_ASK_ESCALATE"] = "1"
    try:
        calls.clear()
        r = li.understand("چه خبر؟", ask_fn=fake)
        assert r["ok"] is True and r["tier"] == "primary", r
        assert calls == [None, "primary"], f"باید دقیقاً یک‌بار ارتقا بدهد: {calls}"
        assert r.get("escalated_from") == "local-llm-unavailable"
    finally:
        os.environ.pop("OCTOPUS_TG_ASK_ESCALATE", None)


def test_a_healthy_local_answer_never_escalates():
    """ارتقا نباید مسیرِ سالم را گران/کند کند."""
    calls = []

    def fake(task, prompt, system="", max_tokens=200, tier=None):
        calls.append(tier)
        return {"ok": True, "tier": "local",
                "text": '{"intent":"status","risk":"low","summary":"س","needs_mission":false}'}

    os.environ["OCTOPUS_TG_ASK_ESCALATE"] = "1"
    try:
        r = li.understand("چه خبر؟", ask_fn=fake)
        assert r["ok"] is True and r["tier"] == "local"
        assert calls == [None], f"جوابِ سالمِ محلی نباید ارتقا بگیرد: {calls}"
        assert "escalated_from" not in r
    finally:
        os.environ.pop("OCTOPUS_TG_ASK_ESCALATE", None)


def test_a_failed_escalation_still_falls_back_not_crashes():
    def fake(task, prompt, system="", max_tokens=200, tier=None):
        if tier is None:
            return {"ok": False, "reason": "local-llm-unavailable"}
        raise RuntimeError("پولی هم مرد")

    os.environ["OCTOPUS_TG_ASK_ESCALATE"] = "1"
    try:
        r = li.understand("چه خبر؟", ask_fn=fake)
        assert r["ok"] is False and r["reason"] == "llm-no-answer", r
    finally:
        os.environ.pop("OCTOPUS_TG_ASK_ESCALATE", None)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ✓ {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} green")
