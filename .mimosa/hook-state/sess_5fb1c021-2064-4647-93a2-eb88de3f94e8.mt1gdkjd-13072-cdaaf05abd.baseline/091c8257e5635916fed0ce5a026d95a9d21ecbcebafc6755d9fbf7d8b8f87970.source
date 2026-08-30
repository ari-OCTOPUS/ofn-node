#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_incident1_metadata — regression برای INC1 (CORE-AUTO-DEBUG-01).

بازتولیدِ مسیرِ اصلی: فایل verdicts واقعی‌نما در state موقت →
تابعِ نویسنده → حافظهٔ کانونی موقت ⇒ ردیفِ ADMITTED باید confidence داشته باشد.
(پیش از وصله: confidence=None ⇒ همان نقصِ کشف‌شده در telemetry پنجرهٔ Live-3.)"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parent.parent
for p in (str(_OPS), str(_OPS / "memory"), str(_OPS / "outcomes")):
    if p not in sys.path:
        sys.path.insert(0, p)


def _rig(tmp_path, monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_MEMORY_GATE", "1")
    monkeypatch.setenv("OCTOPUS_WIRE_RECEIPT_CRITIC", "1")
    monkeypatch.setenv("OCTOPUS_STATE_DIR", str(tmp_path))
    st = tmp_path / "test_cycle"
    st.mkdir(parents=True, exist_ok=True)
    (st / "action-ledger.jsonl").write_text(json.dumps({
        "action_id": "act-test-1", "status": "EXECUTED",
        "classification": "A1", "ts": "2026-08-19T00:00:00+00:00"}) + "\n", encoding="utf-8")
    import receipt_critic
    monkeypatch.setattr(receipt_critic, "_state_dir", lambda: st)   # seam — نه state واقعی
    import memory_store as ms
    return ms.MemoryStore(path=tmp_path / "memory" / "memory.db")


def test_incident1_receipt_critic_writes_with_confidence(tmp_path, monkeypatch):
    store = _rig(tmp_path, monkeypatch)
    import receipt_critic
    out = receipt_critic.evaluate_new()
    assert out.get("ok"), out
    con_row = None
    import sqlite3
    con = sqlite3.connect(f"file:{tmp_path/'memory'/'memory.db'}?mode=ro", uri=True)
    row = con.execute("SELECT memory_id, confidence, admission_state, valid_to FROM memory "
                      "WHERE content LIKE '%act-test-1%'").fetchone()
    con.close()
    assert row is not None, "record not written"
    mid, conf, state, valid_to = row
    assert conf not in (None, ""), f"INC1 regression: confidence missing on {mid}"
    assert state == "ADMITTED" and valid_to, (state, valid_to)


def test_incident1_candidate_construction_static():
    """تضمینِ استاتیک: هر دو نویسنده در source، فیلد confidence را دارند."""
    src_gab = (_OPS / "goal_action_bridge.py").read_text(encoding="utf-8")
    src_rc = (_OPS / "receipt_critic.py").read_text(encoding="utf-8")
    assert '"confidence": "0.9"' in src_gab
    assert '"confidence": "0.9"' in src_rc
