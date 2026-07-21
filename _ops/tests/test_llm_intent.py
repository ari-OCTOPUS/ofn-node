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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ✓ {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} green")
