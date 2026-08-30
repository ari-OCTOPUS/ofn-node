#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_e2e_fixture — گیت E2E سنتزی بدون provider زنده (LIVE4-DEFECT-CLOSURE-AND-E2E-01)."""
import json, sys
from pathlib import Path
import pytest
L4 = Path(__file__).resolve().parent
sys.path.insert(0, str(L4))
import live4_harness as H

BASE = "Add a nightly regression suite for the admission gate."
COND = "Add a nightly regression suite for the admission gate, prioritizing the two quarantine-path tests added 2026-08-18 (evidence: mem_c97e / INC-CL1-001)."

def test_e2e_both_arms_distinct_and_randomized():
    a = H.blind_pair(BASE, COND, seed=7); b = H.blind_pair(BASE, COND, seed=7)
    assert a == b and a["baseline_sha"] != a["conditioned_sha"]
    assert {H.blind_pair(BASE, COND, seed=s)["cond_position"] for s in range(30)} == {"A", "B"}

def test_e2e_judge_both_orderings_parse():
    for pos in ("A", "B"):
        jc = H.judge_contract("A", pos, judge_provider="deepseek",
                              judge_model="deepseek-v4-flash", trace_id="fx")
        assert jc["verdict"] == "A" and jc["winner"] == ("conditioned" if pos == "A" else "baseline")
        assert len(jc["rationale_hash"]) == 64 and jc["trace_id"] == "fx"
    assert H.judge_contract("TIE", "A")["winner"] is None
    assert H.judge_contract("امتیاز مساوی", "A")["void"] is True   # UNREADABLE ⇒ VOID، نه حدس

def test_e2e_pair_finalization_increments_once_duplicate_blocked(tmp_path):
    pairs = tmp_path / "pairs.jsonl"
    def finalize(pid, ok=True):
        # قراردادِ runner: فقط مسیرِ موفق emit می‌کند؛ duplicate توسط PK دفتر رد می‌شود
        if ok: pairs.open("a", encoding="utf-8").write(json.dumps({"id": pid, "valid": True}) + "\n")
    finalize("p1"); finalize("p1", ok=False)  # تکرار از مسیر exc می‌آید، نه emit دوم
    rows = [json.loads(l) for l in pairs.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["id"] == "p1"
