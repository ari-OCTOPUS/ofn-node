#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ask_reasoning_preamble_strip — R27 (2026-08-16، جاروی بدهی).

باگ کیفیتِ مسیرِ ask: مدل‌های thinking گاهی زنجیرهٔ استدلالِ انگلیسی را داخلِ
content می‌آورند و پاسخِ فارسی بعدش؛ کاربر متنِ «The user is asking me…» را
می‌دید. شواهد: state/chat/chat-log.jsonl — 2026-08-13T00:57 و 2026-08-15T10:59.

فیکس: debate/client.py::_strip_reasoning_preamble — فقط وقتی خطِ اول با
نشانگرِ استدلال بخورد و پاراگرافِ فارسی پیدا شود، از آنجا به بعد؛ وگرنه
متن دست‌نخورده (fail-soft — پاکساز هرگز پاسخ را حذف نمی‌کند).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("ask-reasoning-strip")
sys.path.insert(0, str(ENV["ops"] / "debate"))

from client import _strip_reasoning_preamble  # noqa: E402

# نمونهٔ کوتاه‌شدهٔ واقعی از chat-log 2026-08-15T10:59:26
_LIVE_SAMPLE = (
    "The user is asking me to respond as \"Octopus\" — a multi-layered "
    "organism with gates and evidence. Let me parse what is being asked:\n\n"
    "The message says:\n"
    "- Context hint: clarify\n"
    "- Persian, direct, honest, conversational\n\n"
    "سلام! من اختاپوس هستم — مغزِ کنترل و همکارِ آرمین. "
    "وضعیت زنده: همهٔ پنج عضو بالا هستند و نبض می‌زنند."
)


def t_live_sample_strips_to_persian_answer():
    out = _strip_reasoning_preamble(_LIVE_SAMPLE)
    assert out.startswith("سلام"), out[:80]
    assert "The user" not in out.split("\n\n")[0]


def t_pure_persian_untouched():
    t = "سلام، این یک پاسخِ معمولیِ فارسی است.\n\nادامهٔ پاسخ."
    assert _strip_reasoning_preamble(t) == t


def t_english_only_failsoft_untouched():
    t = "The user asked something. Here is an English answer."
    assert _strip_reasoning_preamble(t) == t


def t_empty_and_none_safe():
    assert _strip_reasoning_preamble("") == ""
    assert _strip_reasoning_preamble(None) == ""


def t_multiple_reasoning_paragraphs_jump_to_first_persian():
    t = ("Let me think about this.\n\nstep one\n\nstep two\n\n"
         "حله — این جوابِ واقعی است.")
    out = _strip_reasoning_preamble(t)
    assert out.startswith("حله"), out[:40]


CHECKS = [
    ("نمونهٔ زندهٔ لاگ → پاسخ فارسی", t_live_sample_strips_to_persian_answer),
    ("متن فارسیِ خالص دست‌نخورده", t_pure_persian_untouched),
    ("انگلیسیِ خالص fail-soft", t_english_only_failsoft_untouched),
    ("خالی/None ایمن", t_empty_and_none_safe),
    ("چندپاراگراف استدلال → اولین فارسی", t_multiple_reasoning_paragraphs_jump_to_first_persian),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
