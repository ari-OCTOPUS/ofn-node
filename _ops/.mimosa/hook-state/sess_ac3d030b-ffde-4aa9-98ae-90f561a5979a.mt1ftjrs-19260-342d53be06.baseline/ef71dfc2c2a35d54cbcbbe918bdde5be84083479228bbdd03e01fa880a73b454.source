#!/usr/bin/env python3
"""
test_extract_json_robust.py — blindspot #14: تستِ سختیِ extract_json
برای ورودی‌های fenceشده، بریده، نامعتبر، و نایاب.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("extract_json_robust")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "debate"))
from client import extract_json  # noqa: E402


# ── Valid JSON (normal cases) ──────────────────────────────────────────

def t_valid_json_plain():
    """JSON ساده بدون نویز — رفتارِ پایه باید حفظ شود."""
    assert extract_json('{"a": 1}') == {"a": 1}


def t_valid_json_with_surrounding_text():
    """JSON با نویزِ فارسی/انگلیسی اطراف."""
    r = extract_json('نویز قبل {"key": "value"} نویز بعد')
    assert r["key"] == "value"


def t_valid_json_nested():
    """JSON تودرتو."""
    r = extract_json('{"outer": {"inner": [1, 2, 3]}}')
    assert r["outer"]["inner"] == [1, 2, 3]


# ── Markdown-fenced JSON (open + close) ─────────────────────────────────

def t_fenced_json_complete():
    """حصارِ ```json ... ``` کامل — باید پارس شود."""
    r = extract_json('```json\n{"organ_pct": {"A": 1.0}, "reason": "x"}\n```')
    assert r["organ_pct"]["A"] == 1.0


def t_fenced_json_without_lang_tag():
    """حصارِ ``` ... ``` بدون زبان."""
    r = extract_json('```\n{"x": 42}\n```')
    assert r["x"] == 42


def t_fenced_json_with_extra_newlines():
    """حصار با خطوطِ خالی."""
    r = extract_json('```json\n\n{"status": "ok"}\n\n```')
    assert r["status"] == "ok"


# ── Markdown-fenced JSON (truncated — missing closing fence) ──────────
# وقتی مدل بریده شود، حصارِ پایانی ``` غایب است ولی JSON شروع شده.

def t_fenced_json_truncated_missing_close_fence_but_valid_json():
    """حصارِ شروع هست ولی حصارِ پایانی نیست — ولی خود JSON کامل است."""
    r = extract_json('```json\n{"done": true}')
    assert r["done"] is True


def t_fenced_json_truncated_and_json_truncated():
    """حصارِ پایانی غایب + JSON خودش هم بریده → باید خطا بدهد."""
    try:
        extract_json('```json\n{"key": "val')
        raise AssertionError("باید خطا می‌داد — JSON بریده")
    except ValueError as e:
        assert "truncated" in str(e).lower(), f"پیامِ خطا باید «truncated» بگوید: {e}"
    except json.JSONDecodeError:
        pass


# ── Truncated JSON (no fences) ─────────────────────────────────────────

def t_truncated_json_missing_close_brace():
    """JSON با آکولادِ باز ولی بدون آکولادِ بسته — پیامِ «truncated»."""
    try:
        extract_json('{\n "PROJECT_F": {\n  "status": "active",')
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "truncated" in str(e).lower(), f"پیام باید علتِ بریدگی را بگوید: {e}"


def t_truncated_json_partial_value():
    """JSON بریده در وسطِ یک مقدار."""
    try:
        extract_json('{"name": "hel')
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "truncated" in str(e).lower(), f"پیام باید علتِ بریدگی را بگوید: {e}"


def t_truncated_json_open_brace_at_end():
    """فقط یک آکولادِ باز."""
    try:
        extract_json('{')
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "truncated" in str(e).lower(), f"پیام باید علتِ بریدگی را بگوید: {e}"


# ── No JSON at all ─────────────────────────────────────────────────────

def t_no_json_at_all():
    """متنی بدون هیچ آکولادی."""
    try:
        extract_json("این فقط یک متن فارسی است")
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "no JSON" in str(e), f"پیام باید «no JSON» بگوید: {e}"


def t_empty_string():
    """رشتهٔ خالی."""
    try:
        extract_json("")
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "no JSON" in str(e), f"پیام باید «no JSON» بگوید: {e}"


def t_only_close_brace():
    """فقط آکولادِ بسته بدون باز."""
    try:
        extract_json("}")
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "no JSON" in str(e), f"پیام باید «no JSON» بگوید: {e}"


# ── Invalid JSON (syntactically broken but has braces) ──────────────────

def t_invalid_json_syntax():
    """JSON با آکولادِ باز و بسته ولی سینتکسِ خراب."""
    try:
        extract_json('{"a": }')
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "invalid JSON" in str(e), f"پیام باید «invalid JSON» بگوید: {e}"


def t_invalid_json_with_offset():
    """JSON نامعتبر — پیام باید محلِ خطا را بگوید."""
    try:
        extract_json('{"key": undefined}')
        raise AssertionError("باید خطا می‌داد")
    except ValueError as e:
        assert "offset" in str(e), f"پیام باید آفست را بگوید: {e}"


# ── Regression: fenced JSON was the original trigger ───────────────────

def t_governor_reply_style():
    """پاسخِ واقعیِ گاورنر با حصار."""
    r = extract_json(
        '```json\n'
        '{"organ_pct": {"ARCHITECT_SYS": 0.4, "TEACHER": 0.3, '
        '"HEARTBEAT": 0.2, "CONTROL_BRAIN": 0.1}, '
        '"reason": "balanced allocation"}\n'
        '```'
    )
    assert r["organ_pct"]["ARCHITECT_SYS"] == 0.4


# ── Fenced JSON with surrounding text ─────────────────────────────────

def t_fenced_json_with_surrounding_text():
    """حصارِ ```json وسط متن."""
    r = extract_json(
        'Here is the analysis:\n'
        '```json\n{"score": 0.95}\n```\n'
        'End of analysis.'
    )
    assert r["score"] == 0.95


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    sys.exit(1 if failed else 0)
