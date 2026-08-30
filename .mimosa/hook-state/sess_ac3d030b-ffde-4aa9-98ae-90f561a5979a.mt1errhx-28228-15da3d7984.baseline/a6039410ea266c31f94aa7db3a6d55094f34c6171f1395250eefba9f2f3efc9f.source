#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_dual_brain_veto.py — فاز ۶ دستورالعمل ۲۰۲۶-۰۸-۱۶: وتوی متقابل + consensus halt.

نامِ فایل عمداً `*_veto` است: `test_dual_brain.py` از قبل به dual_brain_v3 پروژهٔ
دیگری (مغزِ محتوا) تعلق دارد — تصادمِ نام، نه تصادمِ مفهوم.

قیودِ اثبات‌شده (D1/D2/D3):
  · دو تأیید → APPROVED؛ هر وتو → OWNER_DECISION (توقف + اعلان مالک)؛ mixed-pending → PENDING
  · halt فقط با consensus هر دو مغز — هیچ مغزی تنهایی halt نمی‌کند
  · دامنه‌ها بر اساس نوع تصمیم؛ safety/halt/architecture = هر دو
  · ثبت در events.jsonl با trace_id؛ spine از مسیرِ canonical decision-recorded
  · مالک فقط پشتِ فلگ اعلان می‌گیرد (W4)؛ صفِ _octopus/queue لمس نمی‌شود
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "control_plane"),
           str(_HERE.parent / "spine"), str(_HERE.parent / "outcomes"),
           str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("dual-brain-veto")

import dual_brain as db   # noqa: E402  (_ops/control_plane/dual_brain.py)
from dual_brain import BrainID, VetoResult   # noqa: E402
import events as _ev   # noqa: E402


# ── منطقِ وتوی متقابل (D2) ───────────────────────────────────────────────────

def test_mutual_veto_logic():
    A, V, P = VetoResult.APPROVED, VetoResult.VETOED, VetoResult.PENDING
    assert db.evaluate_veto(A, A) == VetoResult.APPROVED        # هر دو تأیید
    assert db.evaluate_veto(V, A) == VetoResult.OWNER_DECISION  # وتوی 4d
    assert db.evaluate_veto(A, V) == VetoResult.OWNER_DECISION  # وتوی NBB
    assert db.evaluate_veto(V, V) == VetoResult.OWNER_DECISION  # وتوی هر دو
    assert db.evaluate_veto(A, P) == VetoResult.PENDING         # منتظرِ مغزِ دوم
    assert db.evaluate_veto(P, A) == VetoResult.PENDING


def test_evaluate_records_with_trace_id(monkeypatch):
    monkeypatch.setenv(db.FLAG, "0")   # اعلان خاموش — ثبتِ داخلی کافی
    rec = db.evaluate("prop-101", VetoResult.VETOED, VetoResult.APPROVED,
                      domain="safety")
    assert rec.final == VetoResult.OWNER_DECISION
    assert rec.trace_id.startswith("veto-")
    # رویدادِ approval.required با همان trace در events.jsonl
    lines = [json.loads(x) for x in
             _ev.LOG.read_text("utf-8").splitlines()[-10:] if x.strip()]
    hit = [x for x in lines if x.get("trace_id") == rec.trace_id]
    assert hit and hit[0]["event_name"] == "approval.required"
    assert hit[0]["approval_state"] == "required"
    # اعلانِ مالک پشتِ فلگ خاموش نباید رفته باشد
    assert rec.owner_notified is False


def test_owner_notified_behind_flag(monkeypatch):
    monkeypatch.setenv(db.FLAG, "1")
    alerted = []
    import opslib
    monkeypatch.setattr(opslib, "alert", lambda lines: alerted.append(lines))
    rec = db.evaluate("prop-102", VetoResult.APPROVED, VetoResult.VETOED)
    assert rec.final == VetoResult.OWNER_DECISION
    assert rec.owner_notified is True and len(alerted) == 1
    assert "denied" in alerted[0][0].lower()   # واژگانِ critical برای push


# ── consensus halt (D3) ──────────────────────────────────────────────────────

def test_consensus_halt_requires_both():
    assert db.consensus_halt(True, True) is True
    assert db.consensus_halt(True, False) is False   # هیچ مغزی تنهایی halt نمی‌کند
    assert db.consensus_halt(False, True) is False
    assert db.consensus_halt(False, False) is False
    out = db.halt_organism(True, False)
    assert out["consensus"] is False and out["action"] == "no-halt-single-brain"
    out2 = db.halt_organism(True, True)
    assert out2["consensus"] is True and out2["trace_id"].startswith("halt-")


# ── دامنه‌ها بر اساس نوع تصمیم ──────────────────────────────────────────────

def test_decision_domains():
    assert db.domain_brain("research") == BrainID.FOURD
    assert db.domain_brain("analysis") == BrainID.FOURD
    assert db.domain_brain("operations") == BrainID.NBB
    assert db.domain_brain("budget") == BrainID.NBB
    assert db.domain_brain("safety") is None        # هر دو — وتوی متقابل
    assert db.domain_brain("halt") is None          # consensus
    assert db.domain_brain("architecture") is None  # هر دو + مالک
    assert db.domain_brain("whatever-new") is None  # ناشناخته = محافظه‌کارانه هر دو


# ── ثبتِ canonical در spine ─────────────────────────────────────────────────

def test_dual_veto_recorded_spine_adapter():
    import spine_adapters as sa
    import event_spine as es
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        old = os.environ.get(es.FLAG)
        os.environ[es.FLAG] = "1"
        try:
            spine = es.EventSpine(path=Path(td) / "spine.db")
            r = sa.dual_veto_recorded(proposal_id="prop-201",
                                      fourd_verdict="approved",
                                      nbb_verdict="vetoed",
                                      final="owner_decision",
                                      spine=spine)
            assert r["published"] is True, r
            rows = spine.events(correlation_id="veto_prop-201")
            assert len(rows) == 1
            assert rows[0]["event_type"] == "decision-recorded"
            assert rows[0]["domain"] == "governance"
            # idempotent روی همان رأی؛ تغییرِ رأی = رویدادِ نو
            r2 = sa.dual_veto_recorded(proposal_id="prop-201",
                                       fourd_verdict="approved",
                                       nbb_verdict="vetoed",
                                       final="owner_decision", spine=spine)
            assert r2["published"] is False and r2["reason"] == "duplicate"
            r3 = sa.dual_veto_recorded(proposal_id="prop-201",
                                       fourd_verdict="approved",
                                       nbb_verdict="vetoed",
                                       final="approved", spine=spine)
            assert r3["published"] is True
            spine.close()
        finally:
            if old is None:
                os.environ.pop(es.FLAG, None)
            else:
                os.environ[es.FLAG] = old


# ── مرزها: صف لمس نمی‌شود، فایل STOP نمی‌سازد ───────────────────────────────

def test_no_queue_or_stop_file_writes(monkeypatch):
    monkeypatch.setenv(db.FLAG, "1")
    before = set(Path(_ev.LOG.parent).glob("STOP-*"))
    db.evaluate("prop-300", VetoResult.VETOED, VetoResult.VETOED)
    db.halt_organism(True, True)
    after = set(Path(_ev.LOG.parent).glob("STOP-*"))
    assert before == after   # فایلِ STOP فقط از رأیِ مالک می‌آید


def test_supervisor_constitution_untouched():
    """انحرافِ مستند: supervisor.py فقط snapshot می‌نویسد (منشورِ خودش) —
    ادغامِ وتو در مسیرِ اجرا در فاز ۸e (action_bridge) انجام می‌شود."""
    src = (_HERE.parent / "control_plane" / "supervisor.py").read_text("utf-8")
    assert "dual_brain" not in src   # منشورِ فضای‌نامِ انحصاری حفظ شد


def test_owner_verdict_registered():
    assert "OCTOPUS_WIRE_DUAL_VETO" in \
        (_HERE.parent / "owner-verdicts.yaml").read_text("utf-8")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
