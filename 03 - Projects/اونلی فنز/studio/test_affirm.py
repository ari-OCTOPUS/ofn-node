#!/usr/bin/env python3
"""test_affirm.py — تست‌های لایهٔ تحسین‌گرِ استودیوی خالق (pure، content-free)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import affirm  # noqa: E402


def _content_free(s: str):
    low = s.lower()
    for banned in ("sydney", "harbour", "persian", "سیدنی", "onlyfans", "صبا"):
        assert banned not in low, f"leak: {banned}"


def test_all_renders_are_content_free_and_warm():
    outs = [
        affirm.welcome(),
        affirm.spotlight(0), affirm.spotlight(1), affirm.spotlight(5),
        affirm.streak_msg(0), affirm.streak_msg(2), affirm.streak_msg(9),
        affirm.thanks(0), affirm.thanks(4),
        affirm.celebrate_milestone("first_set"),
        affirm.celebrate_milestone("ten_sets"),
        affirm.home_card(sets_this_week=3, streak_days=5, pending_drafts=2),
    ]
    for s in outs:
        assert isinstance(s, str) and s.strip()
        _content_free(s)


def test_home_card_reflects_state():
    card = affirm.home_card(sets_this_week=3, streak_days=5, pending_drafts=2)
    assert "استودیو" in card
    assert "/halt" in card               # مرزِ خالق همیشه حاضر
    assert "2 درفت" in card


def test_spotlight_scales():
    assert "منتظر" in affirm.spotlight(0)
    assert "5" in affirm.spotlight(5)
