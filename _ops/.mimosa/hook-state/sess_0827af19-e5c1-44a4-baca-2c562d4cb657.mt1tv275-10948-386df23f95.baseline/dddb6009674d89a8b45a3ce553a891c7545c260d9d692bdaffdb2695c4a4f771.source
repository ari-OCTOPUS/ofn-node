#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_evolution_gate.py — تست‌های EvolutionGate (مورد ۳).

تست‌ها:
  ۱. flag off → no-op
  ۲. lesson extraction از trace واقعی
  ۳. evaluator مستقل: self-referential metric → REJECT
  ۴. gate: score پایین → REJECT بدون owner
  ۵. gate: score بالا + owner → PROMOTE + ledger
  ۶. revert → ledger entry
  ۷. health_metrics
"""
import json
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


@pytest.fixture
def isolated_evolution(tmp_path, monkeypatch):
    import seed.evolution_gate as eg
    monkeypatch.setattr(eg, "SKILLS_DIR", tmp_path / "skills")
    monkeypatch.setattr(eg, "CANDIDATES_DIR", tmp_path / "candidates")
    monkeypatch.setattr(eg, "LEDGER", tmp_path / "ledger.jsonl")
    return tmp_path


class TestFlagOff:
    def test_flag_off_extract_returns_empty(self, monkeypatch):
        monkeypatch.delenv("OCTOPUS_WIRE_EVOLUTION_GATE", raising=False)
        from seed.evolution_gate import extract_lessons_from_trace
        assert extract_lessons_from_trace(Path("nonexistent.jsonl")) == []


class TestLessonExtraction:
    def test_extract_from_trace(self, isolated_evolution, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import extract_lessons_from_trace
        trace = isolated_evolution / "trace.jsonl"
        trace.write_text(
            json.dumps({"err": "ConnectionError"}) + "\n" +
            json.dumps({"err": "ConnectionError"}) + "\n" +
            json.dumps({"ok": True}) + "\n",
            encoding="utf-8",
        )
        lessons = extract_lessons_from_trace(trace)
        assert len(lessons) >= 1
        assert "ConnectionError" in lessons[0].trigger


class TestEvaluator:
    def test_self_referential_rejected(self, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import CandidateSkill, evaluate_candidate
        c = CandidateSkill(
            skill_id="test1", lesson_ref="x", content="improve eval_score",
            skill_type="rule", producer="test",
        )
        score, reason = evaluate_candidate(c)
        assert score == 0.0
        assert "self_referential" in reason

    def test_short_content_rejected(self, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import CandidateSkill, evaluate_candidate
        c = CandidateSkill(
            skill_id="test2", lesson_ref="x", content="ab",
            skill_type="rule", producer="test",
        )
        score, reason = evaluate_candidate(c)
        assert score == 0.0
        assert "too_short" in reason


class TestGate:
    def test_low_score_rejected(self, isolated_evolution, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import CandidateSkill, gate
        c = CandidateSkill(
            skill_id="low1", lesson_ref="x", content="abc",  # خیلی کوتاه → score پایین
            skill_type="rule", producer="test",
        )
        record = gate(c, owner_approved=True)
        assert record.action == "REJECT"

    def test_high_score_promoted_with_owner(self, isolated_evolution, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import CandidateSkill, gate
        c = CandidateSkill(
            skill_id="high1", lesson_ref="x",
            content="A" * 80,  # طول کافی → score بالا
            skill_type="rule", producer="test",
        )
        record = gate(c, owner_approved=True)
        assert record.action == "PROMOTE"
        assert record.eval_score >= 0.5

    def test_high_score_pending_without_owner(self, isolated_evolution, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import CandidateSkill, gate
        c = CandidateSkill(
            skill_id="pending1", lesson_ref="x",
            content="A" * 80,
            skill_type="rule", producer="test",
        )
        record = gate(c, owner_approved=False)
        assert record.action == "PENDING"


class TestRevert:
    def test_revert_writes_ledger(self, isolated_evolution, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import revert
        record = revert("skill_test123", "test revert")
        assert record.action == "REVERT"
        # ledger باید نوشته شده باشد
        from seed.evolution_gate import LEDGER
        lines = LEDGER.read_text("utf-8").strip().split("\n")
        assert len(lines) >= 1
        data = json.loads(lines[-1])
        assert data["action"] == "REVERT"


class TestHealthMetrics:
    def test_empty_health(self, isolated_evolution):
        from seed.evolution_gate import health_metrics
        m = health_metrics()
        assert m["status"] == "empty"
        assert m["promotions"] == 0

    def test_health_after_operations(self, isolated_evolution, monkeypatch):
        monkeypatch.setenv("OCTOPUS_WIRE_EVOLUTION_GATE", "1")
        from seed.evolution_gate import CandidateSkill, gate, revert, health_metrics
        # یک promote + یک reject + یک revert
        c1 = CandidateSkill(skill_id="h1", lesson_ref="x", content="A"*80,
                            skill_type="rule", producer="t")
        gate(c1, owner_approved=True)
        c2 = CandidateSkill(skill_id="h2", lesson_ref="x", content="ab",
                            skill_type="rule", producer="t")
        gate(c2, owner_approved=True)
        revert("h1", "rollback test")
        m = health_metrics()
        assert m["promotions"] == 1
        assert m["rejections"] == 1
        assert m["reverts"] == 1
        assert m["rollback_rate"] == 1.0  # 1 revert / 1 promotion
