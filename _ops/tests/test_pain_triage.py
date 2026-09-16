# -*- coding: utf-8 -*-
"""تست‌های قابلیت نخست‌زاده (pain triage) — بخشی از گیت ماشینی فاز ۷."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "legs"))

from legs.pain_triage import triage, parse_pain_rows, signals_from_organism  # noqa: E402

ROWS = [
    {"ts": "2026-08-11T21:10:41", "pain": 0.25, "threshold": 0.35, "status": "OK",
     "reason_codes": ["all_clear"], "evidence_level": "SHADOW",
     "proposal": "none", "trace_id": "t1"},
    {"ts": "2026-08-11T21:14:04", "pain": 0.375, "threshold": 0.35, "status": "OK",
     "reason_codes": ["pain_above_threshold"], "evidence_level": "SHADOW",
     "proposal": "protective_proposal", "trace_id": "t2"},
    {"ts": "2026-08-11T21:15:15", "pain": 0.375, "threshold": 0.35, "status": "OK",
     "reason_codes": ["pain_above_threshold"], "evidence_level": "SHADOW",
     "proposal": "protective_proposal", "trace_id": "t3"},
]
STATE = {"cartographer": {"map_stale": True, "map_age_days": 21, "drift_files": 1163},
         "chrono": {"legs_diag": {"lead-naghshi": {"state": "alive"}}}}


def _write_fixture(tmp_path):
    p = tmp_path / "pain.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in ROWS) + "\n{bad json\n", encoding="utf-8")
    return p


def test_counts_and_priority(tmp_path):
    p = _write_fixture(tmp_path)
    out = triage(p, STATE)
    assert out["counts"]["rows"] == 3
    assert out["counts"]["malformed"] == 1
    assert out["counts"]["above_threshold"] == 2
    assert out["priority"] == "HIGH"
    assert out["triage"][0]["above"] is True


def test_signals_from_organism():
    sig = signals_from_organism(STATE)
    kinds = [s["signal"] for s in sig]
    assert "cartographer-map-stale" in kinds
    assert "leg:lead-naghshi" in kinds
    assert sig[0]["age_days"] == 21


def test_empty_file_graceful(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    out = triage(p, {})
    assert out["counts"]["rows"] == 0
    assert out["priority"] == "LOW"


def test_malformed_only(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text("not json\n{}", encoding="utf-8")
    out = triage(p, {})
    assert out["counts"]["malformed"] == 2


def test_read_only_by_default(tmp_path):
    from legs.pain_triage import main as _m  # noqa: F401
    src = Path(sys.path[1]) if False else None  # placeholder no-op
    # --write فقط با فلگ؛ خودِ تابع triage هیچ فایلی نمینویسد
    p = _write_fixture(tmp_path)
    before = set(tmp_path.iterdir())
    triage(p, STATE)
    after = set(tmp_path.iterdir())
    assert before == after
