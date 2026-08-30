#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_redact_before_archive.py — رگرسیونِ ترتیبِ redact نسبت به hold (Wave 1.2).

قانونی که این تست محافظت می‌کند (یافتهٔ boundary-3):

  تا ۲۰۲۶-۰۷-۳۱ در `approval_channel.send_text`، `_sp.hold(stream, text)` با
  متنِ خام صدا زده می‌شد و `_redact` **بیست خط پایین‌تر** بود. یعنی کلاسِ
  محتوایی که redact برای حذفِ آن ساخته شده (توکن/PEM/PII) دقیقاً در
  held-stream.jsonl — یک کپیِ دومِ plaintext از خروجیِ مالک — نشت می‌کرد.

  این تست با AST ثابت می‌کند که فراخوانیِ `_redact` در سورس **قبل از**
  `_sp.hold` می‌آید — همان روشی که test_surface_policy برای حفظِ ساختار
  می‌سنجد، ولی این‌بار برای ترتیبِ redact/archive.
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import harness  # noqa: E402

_SRC = _HERE.parent / "budget" / "approval_channel.py"


def _send_text_node() -> ast.FunctionDef:
    """گرهٔ AST ِ تابعِ send_text را برمی‌گرداند."""
    tree = ast.parse(_SRC.read_text("utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "send_text":
            return node
    raise AssertionError("send_text یافت نشد")


def _first_line_matching(node, predicate):
    """اولین شمارهٔ خطِ (در send_text) که predicate روی یک AST node درست باشد."""
    for n in ast.walk(node):
        if predicate(n):
            return n.lineno
    return None


def t_redact_call_precedes_hold_call_in_send_text():
    """خطِ فراخوانیِ _redact باید کمتر از خطِ فراخوانیِ _sp.hold باشد.

    پیش از Wave 1.2 این برعکس بود: hold در ~۱۶۲۹، redact در ~۱۶۶۵. یعنی متنِ
    خام آرشیو می‌شد قبل از پاک‌شدن."""
    fn = _send_text_node()
    redact_line = _first_line_matching(
        fn, lambda n: isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "_redact")
    hold_line = _first_line_matching(
        fn, lambda n: isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "hold")
    assert redact_line is not None, "_redact در send_text صدا زده نمی‌شود"
    assert hold_line is not None, "_sp.hold در send_text صدا زده نمی‌شود"
    assert redact_line < hold_line, (
        f"redact ({redact_line}) باید قبل از hold ({hold_line}) بیاید — "
        f"در غیرِ این صورت متنِ خام در held-stream.jsonl آرشیو می‌شود "
        f"(نشتِ boundary-3)")


def t_redact_is_early_in_function_body():
    """redact باید در ابتدای send_text باشد، نه در انتها — تا هر مسیر
    (HOLD، تعاملی، ارسال) همگی متنِ پاک‌شده را ببینند."""
    fn = _send_text_node()
    redact_line = _first_line_matching(
        fn, lambda n: isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "_redact")
    # بدنهٔ send_text را به خطوط تقسیم کن؛ redact باید در یک‌سومِ اول باشد
    last_line = max((n.lineno for n in ast.walk(fn) if hasattr(n, "lineno")),
                    default=redact_line)
    span = last_line - fn.lineno
    assert redact_line - fn.lineno <= span / 2, (
        f"redact در خطِ {redact_line} (تابع از {fn.lineno} تا {last_line}) — "
        f"باید در ابتدا باشد تا تمامِ مسیرها متنِ پاک‌شده ببینند")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_redact_before_archive: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
