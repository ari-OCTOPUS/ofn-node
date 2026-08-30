#!/usr/bin/env python3
"""test_recall_loop_distant.py — فیکس حلقهٔ recall دور (2026-08-16).

پوشش: hash متناهی · انتخاب دور+نزدیک · UNION بدون حذف · NaN-query تهی.
ثبت در run_all.py نشده (WORKLOCK) — این فایل را جدا اجرا کن.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "neural"))
import harness
ENV = harness.setup("recall-loop-distant")

from neural.encoders import encode_rfc, encode_observation, _hash_project
from neural.latent_space import SharedLatentSpace
from neural.consolidation import (
    select_recall_keys, union_similar_keys, recall_reach, _key_cycle,
)


def t_hash_project_never_nan():
    """C-019: هیچ ورودی‌ای NaN/Inf نمی‌سازد — ۱۰۰ نمونهٔ متنوع."""
    for i in range(100):
        v = _hash_project(f"archive-{i}", dim=32)
        assert v.shape == (32,)
        assert np.isfinite(v).all(), f"NaN/Inf at archive-{i}"
        assert abs(np.linalg.norm(v) - 1.0) < 1e-6


def t_rfc_same_n_approved_identical():
    """دو سیکل با n_approved یکسان — بردار یکی (encoding پایدار)."""
    a = encode_rfc("archive", "3 approved", "medium")
    b = encode_rfc("archive", "3 approved", "medium")
    assert np.allclose(a, b)
    assert np.isfinite(a).all()


def t_select_prefers_far_when_scores_tie():
    """امتیاز برابر → far_slots کلیدِ دور را نگه می‌دارد."""
    hits = [
        ("cycle-100:school_awareness", 0.99),
        ("cycle-99:school_awareness", 0.99),
        ("cycle-10:school_awareness", 0.99),
        ("cycle-3:school_awareness", 0.99),
    ]
    got = select_recall_keys(hits, "cycle-101", limit=5, far_slots=3)
    assert any("cycle-3" in k or "cycle-10" in k for k in got), got
    assert not any(k.startswith("cycle-101") for k in got)


def t_select_keeps_near_for_existing_test():
    """نزدیک هم می‌ماند — رگرسیون test_consolidation_latent."""
    hits = [
        ("cycle-1:acquisition:rev", 0.95),
        ("cycle-1", 0.94),
    ]
    got = select_recall_keys(hits, "cycle-2", limit=5, far_slots=3)
    assert any("cycle-1" in k for k in got), got


def t_union_never_deletes():
    prev = ["cycle-90", "cycle-91"]
    incoming = ["cycle-3", "cycle-90"]
    merged = union_similar_keys(prev, incoming)
    assert "cycle-90" in merged and "cycle-91" in merged and "cycle-3" in merged
    assert merged.index("cycle-90") < merged.index("cycle-3")


def t_similar_nan_query_empty():
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "lv.json"))
    v = encode_observation("acquisition", "x", dim=32)
    ls.embed("cycle-1", v, layer="t")
    q = np.full(32, np.nan)
    assert ls.similar(q, top_k=5) == []


def t_recall_reach_rises_with_far_union():
    near = [{"cycle": 100, "similar_keys": ["cycle-99", "cycle-101"]}]
    warmed = [{"cycle": 100,
               "similar_keys": union_similar_keys(
                   ["cycle-99", "cycle-101"], ["cycle-3", "cycle-7"])}]
    a, b = recall_reach(near), recall_reach(warmed)
    assert a["reach_median"] == 1.0
    assert b["reach_median"] > a["reach_median"]
    assert b["keys"] == 4
    assert _key_cycle("cycle-3:school_awareness") == 3


def t_4d_insight_recall_fires():
    """جاکارد insight در 4d — بدون TCB — سیکل دوم کلید دور می‌سازد."""
    sys.path.insert(0, r"F:\backup\4d_system")
    from brain.consolidation import ConsolidationCycle
    td = tempfile.mkdtemp()
    p = Path(td) / "c.json"
    cyc = ConsolidationCycle(data_path=p)
    src = {"frontier": {"cells": 27},
           "experiments": [{"verdict": "ok"}],
           "reflections": [{"score": 3}]}
    r1 = cyc.run(src)          # degraded + سطح
    r2 = cyc.run(src)          # delta-zero
    r3 = cyc.run(src)          # delta-zero دوباره → جاکارد ۱ با r2
    assert r1.cycle == 1
    assert r3.similar_keys, r3.similar_keys
    assert any(k.startswith("cycle-") for k in r3.similar_keys), r3.similar_keys


if __name__ == "__main__":
    failed = harness.run([
        ("hash never NaN", t_hash_project_never_nan),
        ("rfc stable identical", t_rfc_same_n_approved_identical),
        ("select prefers far", t_select_prefers_far_when_scores_tie),
        ("select keeps near", t_select_keeps_near_for_existing_test),
        ("union never deletes", t_union_never_deletes),
        ("NaN query empty", t_similar_nan_query_empty),
        ("reach rises with far union", t_recall_reach_rises_with_far_union),
        ("4d insight recall fires", t_4d_insight_recall_fires),
    ])
    sys.exit(1 if failed else 0)
