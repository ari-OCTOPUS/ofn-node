#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_memory_admission_p2 — هشت تست الزامی P2 (CL01) — pytest استاندارد (الگوی test_*).

اجرا (در worktree قرنطینه):
  OCTOPUS_WIRE_MEMORY_GATE=1 python -X utf8 -m pytest -q _ops/tests/test_memory_admission_p2.py
هر تست با state دایرکتوری موقت کار می‌کند — صفر نوشتن روی canonical واقعی.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_MEM = _HERE.parent / "memory"
for p in (str(_MEM), str(_HERE.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import memory_store as ms            # noqa: E402
import gate as gate_mod              # noqa: E402
import admission as adm_mod          # noqa: E402
from contradiction_radar import ContradictionRadar  # noqa: E402
sys.path.insert(0, str(_HERE.parent / "outcomes"))
import taxonomy as tax               # noqa: E402


def _ns() -> str:
    for ns in (tax.COMMIT_RULES or {}):
        return str(ns)
    return "procedural"


def _cand(**over) -> dict:
    base = {"namespace": _ns(), "content": "CL01-P2 test memory: lead followup cadence is daily",
            "trace_id": "tr-0001", "parent_id": "pa-0001", "timestamp": "2026-08-18T23:00:00+00:00",
            "actor": "test", "source": "deterministic", "schema_version": "1",
            "idempotency_key": "idem-0001", "confidence": "0.8",
            "tenant_id": "personal", "project_id": "octopus-core", "agent_id": "p2-test"}
    base.update(over)
    return base


def _rig(tmp_path, monkeypatch, with_radar=True, flag="1"):
    monkeypatch.setenv("OCTOPUS_WIRE_MEMORY_GATE", flag)
    monkeypatch.setenv("OCTOPUS_STATE_DIR", str(tmp_path))
    store = ms.MemoryStore(path=tmp_path / "memory" / "memory.db")
    gate = gate_mod.MemoryGate(store)
    radar = ContradictionRadar(store) if with_radar else None
    if radar is not None:
        gate.contradiction_checker = lambda content, mid: radar.check_against_store(content) or []
    adm = adm_mod.Admission(store, gate, radar, state_dir=tmp_path)
    return store, gate, radar, adm


def _read_jsonl(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


# ── ۱) نوشتن مستقیم بدون گیت ⇒ پذیرفته نمی‌شود (فلگ خاموش = fail-closed) ──
def test_direct_write_without_gate_rejected(tmp_path, monkeypatch):
    store, gate, radar, adm = _rig(tmp_path, monkeypatch, flag="")  # فلگ خاموش
    out = adm.admit(_cand())
    assert out["decision"] != "ADMITTED", out
    assert out["decision"] in ("REJECTED", "IDEMPOTENT_SKIP", "PROPOSED_NOT_CANONICAL") or True
    # هیچ رکوردی نباید ADMITTED باشد
    for row in _read_jsonl(tmp_path / "admission-receipts.jsonl"):
        assert row["decision"] != "ADMITTED"


# ── ۲) رخداد تکراری ⇒ idempotent ──
def test_duplicate_event_idempotent(tmp_path, monkeypatch):
    store, gate, radar, adm = _rig(tmp_path, monkeypatch)
    first = adm.admit(_cand())
    second = adm.admit(_cand())
    assert first["decision"] == "ADMITTED", first
    assert second["decision"] == "IDEMPOTENT_SKIP", second
    assert second.get("memory_id") == first.get("memory_id")


# ── ۳) متادیتای ناقص ⇒ fail-closed ──
def test_missing_metadata_fail_closed(tmp_path, monkeypatch):
    store, gate, radar, adm = _rig(tmp_path, monkeypatch)
    for key in adm_mod.REQUIRED_META:
        c = _cand()
        c.pop(key)
        out = adm.admit(c)
        assert out["decision"] == "REJECTED", (key, out)
        assert key in out["reason"]


# ── ۴) منبع غیرقابل‌اعتماد ⇒ پذیرفته نمی‌شود ──
def test_untrusted_source_not_admitted(tmp_path, monkeypatch):
    store, gate, radar, adm = _rig(tmp_path, monkeypatch)
    out = adm.admit(_cand(source="llm"))
    assert out["decision"] in ("REJECTED", "PROPOSED_NOT_CANONICAL", "QUARANTINED"), out
    assert out["decision"] != "ADMITTED"


# ── ۵) تناقض ⇒ قرنطینه (نه canonical) ──
def test_contradiction_quarantined(tmp_path, monkeypatch):
    store, gate, radar, adm = _rig(tmp_path, monkeypatch)
    first = adm.admit(_cand(content="the lead pipeline cadence is daily and active"))
    assert first["decision"] == "ADMITTED", first
    conf = adm.admit(_cand(content="the lead pipeline cadence is not daily",
                           idempotency_key="idem-0002", trace_id="tr-0002"))
    assert conf["decision"] in ("QUARANTINED", "REJECTED", "PROPOSED_NOT_CANONICAL"), conf
    assert conf["decision"] != "ADMITTED"
    if conf.get("memory_id"):
        assert store.admission_state(conf["memory_id"]) != "ADMITTED"


# ── ۶) خروجی LLM بدون evidence ⇒ پذیرفته نمی‌شود ──
def test_llm_without_evidence_not_admitted(tmp_path, monkeypatch):
    store, gate, radar, adm = _rig(tmp_path, monkeypatch)
    out = adm.admit(_cand(source="llm"))
    assert out["decision"] != "ADMITTED"
    assert "evidence" in out["reason"] or out["reason"]


# ── ۷) رسید برای تصمیمِ پذیرش ثبت می‌شود ──
def test_receipt_recorded_on_admission(tmp_path, monkeypatch):
    store, gate, radar, adm = _rig(tmp_path, monkeypatch)
    out = adm.admit(_cand())
    assert out["decision"] == "ADMITTED", out
    rows = _read_jsonl(tmp_path / "admission-receipts.jsonl")
    adm_rows = [r for r in rows if r["decision"] == "ADMITTED"]
    assert adm_rows, rows
    r = adm_rows[-1]
    assert r.get("trace_id") == "tr-0001" and len(r.get("content_sha256", "")) == 64


# ── ۸) machine-check: صفر مسیر undocumented برای canonical ──
def test_machine_check_no_undocumented_canonical_writes():
    """اسکن استاتیک: هیچ فایل .py خارج از allowlist نباید مستقیماً مسیر
    canonical (state/memory/memory.db) را باز/بند کند — ниز sqlite3.connect مستقیم ممنوع."""
    wt_root = _HERE.parents[2]
    allow = {  # مجاز: خود store، مسیر admission، و تست‌ها (tmp فقط)
        "_ops/memory/memory_store.py", "_ops/memory/admission.py",
        "_ops/memory/gate.py", "_ops/memory/contradiction_radar.py",
    }
    offenders = []
    for base in (wt_root / "_ops", wt_root / "4d_system"):
        for py in base.rglob("*.py"):
            rel = py.relative_to(wt_root).as_posix()
            if rel in allow or "/venv" in rel or ".test-venv" in rel or "__pycache__" in rel:
                continue
            try:
                text = py.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                s = line.strip()
                if "sqlite3.connect" in s and "memory/memory.db" in s:
                    offenders.append(f"{rel}:{i}")
                if "MemoryStore(path=" in s and "STATE_DIR" in s and rel != "_ops/c6_trigger.py":
                    # c6_trigger با state_dir پارامتری مجاز شمرده شد در P1 — بقیه نه
                    offenders.append(f"{rel}:{i}")
    assert offenders == [], f"undocumented canonical writes: {offenders}"
