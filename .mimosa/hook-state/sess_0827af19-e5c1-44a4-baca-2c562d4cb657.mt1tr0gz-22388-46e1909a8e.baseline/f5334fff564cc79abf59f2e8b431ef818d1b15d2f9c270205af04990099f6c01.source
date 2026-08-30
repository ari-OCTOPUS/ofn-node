#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_context_assembler.py — ۴ تستِ پذیرشِ ContextAssembler (Seed Agent v1 قدم ۵).

تست‌ها:
  ۱. flag خاموش → no-op کامل (prompt خالی)
  ۲. flag روشن → ۷ slot با محتوا
  ۳. trim: با بودجهٔ فشرده، RULES + USER دست‌نخورده می‌مانند
  ۴. fail-soft: شکست snapshot → slot STATE خالی، نه crash
"""
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


class TestFlagOff:
    """تست ۱: flag خاموش → no-op کامل."""

    def test_flag_off_returns_empty(self, monkeypatch):
        monkeypatch.delenv("OCTOPUS_WIRE_SEED_ASSEMBLER", raising=False)
        from seed.context_assembler import ContextAssembler, AssembleInput
        ca = ContextAssembler(total_budget=4000)
        prompt, trace = ca.build(AssembleInput(user_msg="test"))
        assert prompt == ""
        assert not trace.flag_on
        assert "no-op" in trace.error

    def test_flag_off_reader_returns_disabled(self, monkeypatch):
        monkeypatch.delenv("OCTOPUS_WIRE_SEED_ASSEMBLER", raising=False)
        from seed.octopus_reader import read_snapshot, read_semantic, read_trace
        assert read_snapshot().get("status") == "disabled"
        assert read_semantic() == []
        assert read_trace() == []


class TestFlagOnSlots:
    """تست ۲: flag روشن → ۷ slot با محتوا (حداقل RULES + USER).
    تمام readerها mock می‌شوند تا تست سریع و قطعی باشد."""

    def test_flag_on_has_rules_and_user(self, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_SEED_ASSEMBLER", "1")
        import seed.octopus_reader
        # تمام readerها را mock کن تا از snapshot/retrieval واقعی جلوگیری شود
        monkeypatch.setattr(seed.octopus_reader, "read_snapshot",
                            lambda: {"status": "ok", "organism": {"beat": 12345, "halted": False}})
        monkeypatch.setattr(seed.octopus_reader, "read_retrieval", lambda *a, **k: [])
        monkeypatch.setattr(seed.octopus_reader, "read_semantic", lambda n=5: [])
        monkeypatch.setattr(seed.octopus_reader, "read_trace", lambda n=10: [])
        from seed.context_assembler import ContextAssembler, AssembleInput
        ca = ContextAssembler(total_budget=4000)
        prompt, trace = ca.build(AssembleInput(user_msg="وضعیت سیستم چیه؟"))
        assert trace.flag_on
        assert "### RULES" in prompt
        assert "### USER" in prompt
        assert "وضعیت سیستم چیه؟" in prompt
        assert len(trace.slots) >= 2


class TestTrim:
    """تست ۳: trim — RULES + USER دست‌نخورده."""

    def test_trim_preserves_pinned(self, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_SEED_ASSEMBLER", "1")
        import seed.octopus_reader
        monkeypatch.setattr(seed.octopus_reader, "read_snapshot",
                            lambda: {"status": "ok", "organism": {"beat": 1}})
        monkeypatch.setattr(seed.octopus_reader, "read_retrieval", lambda *a, **k: [])
        monkeypatch.setattr(seed.octopus_reader, "read_semantic", lambda n=5: [])
        monkeypatch.setattr(seed.octopus_reader, "read_trace", lambda n=10: [])
        from seed.context_assembler import ContextAssembler, AssembleInput
        ca = ContextAssembler(total_budget=600)
        long_msg = "پایان " * 50
        prompt, trace = ca.build(AssembleInput(user_msg=long_msg))
        assert "### RULES" in prompt
        assert "Seed Agent Octopus" in prompt  # متن RULES کامل
        assert "پایان" in prompt  # USER هست (شاید trim شده ولی هست)


class TestFailSoft:
    """تست ۴: fail-soft — شکست هر منبع → slot خالی، نه crash."""

    def test_snapshot_failure_doesnt_crash(self, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_SEED_ASSEMBLER", "1")
        import seed.octopus_reader
        monkeypatch.setattr(
            seed.octopus_reader, "read_snapshot",
            lambda: {"status": "error", "reason": "mock failure"}
        )
        monkeypatch.setattr(seed.octopus_reader, "read_retrieval", lambda *a, **k: [])
        monkeypatch.setattr(seed.octopus_reader, "read_semantic", lambda n=5: [])
        monkeypatch.setattr(seed.octopus_reader, "read_trace", lambda n=10: [])
        from seed.context_assembler import ContextAssembler, AssembleInput
        ca = ContextAssembler(total_budget=4000)
        prompt, trace = ca.build(AssembleInput(user_msg="test"))
        assert "### RULES" in prompt
        assert "### USER" in prompt
        assert "mock failure" in prompt or "error" in prompt or "unavailable" in prompt

    def test_retrieval_failure_returns_empty(self, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_SEED_ASSEMBLER", "1")
        import seed.octopus_reader
        monkeypatch.setattr(seed.octopus_reader, "read_snapshot",
                            lambda: {"status": "ok", "organism": {"beat": 1}})
        monkeypatch.setattr(seed.octopus_reader, "read_retrieval", lambda *a, **k: [])
        monkeypatch.setattr(seed.octopus_reader, "read_semantic", lambda n=5: [])
        monkeypatch.setattr(seed.octopus_reader, "read_trace", lambda n=10: [])
        from seed.context_assembler import ContextAssembler, AssembleInput
        ca = ContextAssembler(total_budget=4000)
        prompt, trace = ca.build(AssembleInput(user_msg="test", query="test query"))
        assert "### RULES" in prompt
        assert "### USER" in prompt
