#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_capability_classifier — تست‌های WP-F: runtime capability classifier.

تست می‌کند که classifier درست تفکیک می‌کند:
  - flag-on ≠ executed
  - artifact-fresh ≠ consumed
  - consumed ≠ decision-changing
  - missing evidence => UNKNOWN، نه false/healthy
  - هر قابلیت همهٔ 9 فیلد evidence ladder را دارد
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("capability-classifier")

STATE_DIR = ENV["ops"] / "state"


def _reload_classifier():
    import capability_classifier as cc
    cc.STATE = STATE_DIR
    return cc


def _write_flags_loaded(name: str, flags: dict):
    f = STATE_DIR / f"flags-loaded-{name}.json"
    f.write_text(json.dumps({"schema": "flags-loaded.v1", "flags": flags}), "utf-8")


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), "utf-8")


# ─── TESTS ────────────────────────────────────────────────────────────────────

def t_all_capabilities_have_nine_fields():
    """هر قابلیت باید هر 9 فیلد evidence ladder را داشته باشد."""
    cc = _reload_classifier()
    r = cc.classify_all()
    required = [
        "implemented", "configured", "armed", "executed_recently",
        "artifact_fresh", "consumed", "decision_changing_evidence",
        "effect_evidence", "outcome_evidence",
    ]
    for name, cap in r["capabilities"].items():
        for field in required:
            assert field in cap, f"{name} missing field: {field}"


def t_flag_on_not_equal_executed():
    """flag روشن نباید executed_recently=True باشد بدون artifact."""
    cc = _reload_classifier()
    _write_flags_loaded("organism", {"OCTOPUS_WIRE_CORTEX_RICH_THINK": "1"})
    # No artifact present
    cap = cc.classify_capability("semantic_memory_rich_think",
                                  cc.CAPABILITIES["semantic_memory_rich_think"])
    assert cap["armed"] == "armed"
    assert cap["executed_recently"] != "fresh", \
        "flag-on نباید executed_recently=fresh بسازد بدون artifact"


def t_artifact_fresh_not_equal_consumed():
    """artifact تازه نباید consumed=yes باشد بدون reader audit."""
    cc = _reload_classifier()
    _write_flags_loaded("organism", {"OCTOPUS_WIRE_CORTEX_RICH_THINK": "1"})
    # Write a fresh artifact
    _write_json(STATE_DIR / "semantic_memory.jsonl",
                {"ts": "2099-01-01T00:00:00Z", "gist": "fresh"})
    # Actually need JSONL
    (STATE_DIR / "semantic_memory.jsonl").write_text(
        json.dumps({"ts": "2099-01-01T00:00:00Z", "gist": "fresh"}) + "\n", "utf-8")
    cap = cc.classify_capability("semantic_memory_rich_think",
                                  cc.CAPABILITIES["semantic_memory_rich_think"])
    assert cap["artifact_fresh"] == "fresh"
    # consumed should still be "claimed" with unknown reason, not definitively "yes"
    assert cap["consumed"] in ("claimed", "unknown"), \
        f"consumed باید claimed/unknown باشد نه قطعی: {cap['consumed']}"


def t_missing_evidence_is_unknown():
    """نبود evidence باید UNKNOWN باشد، نه false یا healthy."""
    cc = _reload_classifier()
    # Clean state to ensure no leakage from previous tests
    import shutil
    for f in STATE_DIR.glob("flags-loaded-*.json"):
        f.unlink()
    semantic = STATE_DIR / "semantic_memory.jsonl"
    if semantic.exists():
        semantic.unlink()
    cap = cc.classify_capability("semantic_memory_rich_think",
                                  cc.CAPABILITIES["semantic_memory_rich_think"])
    assert cap["armed"] == "unknown"
    assert cap["artifact_fresh"] == "missing"
    assert cap["effect_evidence"] == "unknown"
    assert cap["outcome_evidence"] == "unknown"


def t_unknown_reasons_explained():
    """هر UNKNOWN باید دلیل داشته باشد."""
    cc = _reload_classifier()
    cap = cc.classify_capability("semantic_memory_rich_think",
                                  cc.CAPABILITIES["semantic_memory_rich_think"])
    assert len(cap["unknown_reasons"]) > 0, "باید reasons داشته باشد"
    # effect and outcome must always have reasons
    assert any("effect" in r for r in cap["unknown_reasons"])
    assert any("outcome" in r for r in cap["unknown_reasons"])


def t_display_only_is_not_decision_changing():
    """display-only قابلیت نباید decision-changing باشد."""
    cc = _reload_classifier()
    cap = cc.classify_capability("doctor_self_knowledge",
                                  cc.CAPABILITIES["doctor_self_knowledge"])
    assert cap["decision_changing_evidence"] == "no", \
        f"display-only نباید decision-changing باشد: {cap['decision_changing_evidence']}"


def t_context_injection_is_proposal_or_context():
    """context-injection نباید 'decision' نامیده شود."""
    cc = _reload_classifier()
    cap = cc.classify_capability("semantic_memory_rich_think",
                                  cc.CAPABILITIES["semantic_memory_rich_think"])
    assert cap["decision_changing_evidence"] in ("no", "unknown"), \
        f"context injection نباید decision باشد: {cap['decision_changing_evidence']}"


def t_proposal_wired_classified_correctly():
    """proposal-wired قابلیت باید proposal-wired نامیده شود."""
    cc = _reload_classifier()
    cap = cc.classify_capability("c6_hypothesis_producer",
                                  cc.CAPABILITIES["c6_hypothesis_producer"])
    assert cap["decision_changing_evidence"] == "proposal-wired"


def t_read_only_does_not_write_state():
    """classifier نباید هیچ state canonical را بنویسد."""
    cc = _reload_classifier()
    before = {}
    for f in STATE_DIR.iterdir():
        try:
            before[str(f)] = f.stat().st_mtime
        except OSError:
            pass
    cc.classify_all()
    after = {}
    for f in STATE_DIR.iterdir():
        try:
            after[str(f)] = f.stat().st_mtime
        except OSError:
            pass
    # No file should have been modified
    modified = [k for k in after if k in before and before[k] != after[k]]
    # Allow new files (classifier doesn't create any, but just in case)
    assert len(modified) == 0, f"classifier نباید فایل تغییر دهد: {modified}"


def t_summary_counts_present():
    """report باید summary با شمارش‌ها داشته باشد."""
    cc = _reload_classifier()
    r = cc.classify_all()
    assert "summary" in r
    assert "armed" in r["summary"]
    assert "artifact_fresh" in r["summary"]
    assert isinstance(r["summary"]["armed"], int)


def t_freshness_threshold_configurable():
    """threshold باید قابل تنظیم باشد."""
    cc = _reload_classifier()
    assert hasattr(cc, "FRESH_THRESHOLD_H")
    assert isinstance(cc.FRESH_THRESHOLD_H, (int, float))


def t_stale_artifact_detected():
    """artifact قدیمی باید stale باشد."""
    cc = _reload_classifier()
    _write_flags_loaded("organism", {"OCTOPUS_WIRE_CORTEX_RICH_THINK": "1"})
    # Write a stale artifact
    (STATE_DIR / "semantic_memory.jsonl").write_text(
        json.dumps({"ts": "2020-01-01T00:00:00Z", "gist": "stale"}) + "\n", "utf-8")
    cap = cc.classify_capability("semantic_memory_rich_think",
                                  cc.CAPABILITIES["semantic_memory_rich_think"])
    assert cap["artifact_fresh"] == "stale"


# ─── RUN ──────────────────────────────────────────────────────────────────────

CHECKS = [
    ("all-capabilities-have-nine-fields", t_all_capabilities_have_nine_fields),
    ("flag-on-not-equal-executed", t_flag_on_not_equal_executed),
    ("artifact-fresh-not-equal-consumed", t_artifact_fresh_not_equal_consumed),
    ("missing-evidence-is-unknown", t_missing_evidence_is_unknown),
    ("unknown-reasons-explained", t_unknown_reasons_explained),
    ("display-only-not-decision-changing", t_display_only_is_not_decision_changing),
    ("context-injection-is-context", t_context_injection_is_proposal_or_context),
    ("proposal-wired-classified", t_proposal_wired_classified_correctly),
    ("read-only-does-not-write-state", t_read_only_does_not_write_state),
    ("summary-counts-present", t_summary_counts_present),
    ("freshness-threshold-configurable", t_freshness_threshold_configurable),
    ("stale-artifact-detected", t_stale_artifact_detected),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
