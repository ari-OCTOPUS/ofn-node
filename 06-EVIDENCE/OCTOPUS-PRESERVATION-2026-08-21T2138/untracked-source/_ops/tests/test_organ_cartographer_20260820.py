#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_organ_cartographer_20260820.py — agent_C organ map + afferent + loop breakers.

Registered in run_all.py (OWNER #16 A19, lease held by A/B). Unique name. Zero telegram writes.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from organs.contracts import INELIGIBLE, make_event  # noqa: E402
from organs.cognition_inbox import brains_hear  # noqa: E402
from organs.feedback import DEAD, assess_loop  # noqa: E402
from organs.knowledge_afferent import scan as knowledge_scan  # noqa: E402
from organs.loop_breakers import (  # noqa: E402
    DENY_BY_POLICY, QUARANTINED, UNKNOWN, autotune_card_gate, gate_tool_request,
    halt_record, merge_rfcs, metric_count,
)
from organs.organ_map import CLASSES, classify_organ  # noqa: E402
from organs.paths import is_telegram_lane  # noqa: E402
from organs.starvation import ROOT_CAUSES, diagnose as starve_diagnose  # noqa: E402
from organs.mapper_drift import _dead_imports  # noqa: E402
from organs.telemetry import per_minute_by_source  # noqa: E402


def _vault(tmp: Path) -> Path:
    (tmp / "07 - Knowledge").mkdir(parents=True)
    (tmp / "01 - Dashboard").mkdir()
    (tmp / "06 - Architecture Maps").mkdir()
    (tmp / "03 - Projects" / "Demo").mkdir(parents=True)
    note = tmp / "07 - Knowledge" / "hello.md"
    note.write_text(
        "---\ntype: knowledge\nstatus: active\ntags: [test]\ncreated: 2026-08-20\nupdated: 2026-08-20\n---\n\nbody\n",
        encoding="utf-8")
    (tmp / "07 - Knowledge" / "no-fm.md").write_text("no frontmatter\n", encoding="utf-8")
    (tmp / "01 - Dashboard" / "Home.md").write_text(
        "---\ntype: dashboard\nstatus: active\ntags: []\n---\n", encoding="utf-8")
    (tmp / "03 - Projects" / "Demo" / "PROJECT.md").write_text(
        "---\ntype: project\nstatus: active\ntags: [demo]\n---\n", encoding="utf-8")
    maps = tmp / "06 - Architecture Maps" / "MASTER-ARCHITECTURE-2026-07-09.md"
    maps.write_text("---\nupdated: 2026-07-09\n---\n", encoding="utf-8")
    return tmp


def test_starvation_root_cause_decided():
    d = starve_diagnose()
    assert d["starvation_root_cause"] in ROOT_CAUSES
    assert d["measurement"]["thresholds_compared_not_changed"]["hebbian"] == 0.1


def test_sentinel_negative_is_unknown():
    m = metric_count(-1)
    assert m["semantic"] == UNKNOWN and m["render"] == "نامعلوم" and m["value"] is None
    assert metric_count(3)["value"] == 3
    assert metric_count(None)["semantic"] == UNKNOWN


def test_tool_request_quarantine_and_policy():
    root = Path(tempfile.mkdtemp())
    a = gate_tool_request("n", "t", "file.read", state_root=root)
    b = gate_tool_request("n", "t", "file.read", reason_from_reject="no", state_root=root)
    c = gate_tool_request("n", "t", "file.read", reason_from_reject="no-2", state_root=root)
    assert a["status"] == "ALLOW_RECORD" and b["status"] == "ALLOW_RECORD"
    assert c["status"] == QUARANTINED
    assert "feedback_to_generator" in c
    deny = gate_tool_request("x", "y", "shell.full", state_root=root)
    assert deny["status"] == DENY_BY_POLICY
    already = gate_tool_request("x", "y", "file.read", allowed_registry={"file.read"}, state_root=root)
    assert already["status"] == "DENY_ALREADY_ALLOWED"


def test_rfc_merge_and_cap():
    rfcs = [{"rfc_id": f"RFC-{i}", "status": "draft", "bottleneck": "same bottleneck text here"} for i in range(5)]
    rfcs += [{"rfc_id": "RFC-x", "status": "draft", "bottleneck": "other issue"}]
    out = merge_rfcs(rfcs, open_cap=3)
    assert out["rfc_duplicates_merged"] is True
    assert out["open_before"] == 6
    assert len(out["open_kept"]) <= 3


def test_autotune_zero_evidence_once():
    store = {}
    first = autotune_card_gate("inc-1", 0.0, store=store)
    second = autotune_card_gate("inc-1", 0.0, store=store)
    assert first["emit"] is True
    assert second["emit"] is False


def test_halt_has_machine_cause_and_rfc(tmp_path: Path | None = None):
    d = Path(tempfile.mkdtemp())
    p = d / "halts.jsonl"
    r1 = halt_record("afferent_starved", log_path=p)
    r2 = halt_record("afferent_starved", log_path=p)
    assert r1["root_rfc_id"].startswith("RFC-halt-")
    assert r2["repeat_count"] == 2
    assert r1["cause_machine"] == "afferent_starved"


def test_bitemporal_no_future_no_fabricate():
    now = time.time()
    ok = make_event(source="k", path="a.md", occurred_at=now - 10, now=now, content_hash="aa")
    assert ok["status"] == "ok" and ok["fabricated_occurred_at"] is False
    missing = make_event(source="k", path="a.md", occurred_at=None, now=now)
    assert missing["status"] == INELIGIBLE
    future = make_event(source="k", path="a.md", occurred_at=now + 10_000, now=now)
    assert future["future_use"] is True and future["status"] == INELIGIBLE


def test_duplicate_event_idempotent():
    now = time.time()
    a = make_event(source="k", path="a.md", occurred_at=1000.0, now=now, content_hash="h")
    b = make_event(source="k", path="a.md", occurred_at=1000.0, now=now, content_hash="h")
    assert a["event_id"] == b["event_id"]


def test_knowledge_scan_empty_malformed_stale(monkeypatch=None):
    vault = _vault(Path(tempfile.mkdtemp()))
    state = Path(tempfile.mkdtemp())
    out = knowledge_scan(vault=vault, emit=True, state_root=state, now=time.time())
    assert out["ok"] is True
    assert out["n_events"] >= 3
    assert out["metrics"]["fabricated_occurred_at"] == 0
    assert out["metrics"]["frontmatter_valid_ratio"] < 1.0  # no-fm.md
    # empty source
    empty = Path(tempfile.mkdtemp())
    (empty / "07 - Knowledge").mkdir()
    z = knowledge_scan(vault=empty, emit=False, now=time.time())
    assert z["n_events"] == 0


def test_classify_and_classes():
    assert classify_organ({"unsafe": True}) == "UNSAFE_TO_WIRE"
    assert classify_organ({"duplicate_of": "x"}) == "DUPLICATE"
    assert classify_organ({"entrypoint_missing": True}) == "DEAD"
    assert classify_organ({"in_live_import_graph": True, "fresh_data": True,
                           "telemetry": True}) == "LIVE"
    assert classify_organ({"in_live_import_graph": True, "code_present": True}) == "SKELETON"
    assert classify_organ({"code_present": True}) == "ORPHAN"
    assert set(CLASSES) == {"LIVE", "SKELETON", "ORPHAN", "DEAD", "DUPLICATE", "UNSAFE_TO_WIRE"}


def test_dead_feedback_loop():
    r = assess_loop("knowledge", proposals=4, votes=0, effects=0, has_acceptance_criteria=True)
    assert r["label"] == DEAD
    r2 = assess_loop("x", proposals=0, votes=0, effects=0, has_acceptance_criteria=False)
    assert r2["label"] != DEAD


def test_cognition_inbox_receipts():
    st = Path(tempfile.mkdtemp())
    (st / "cortex").mkdir()
    (st / "cortex" / "cortex-state.json").write_text("{}", encoding="utf-8")
    inbox = st / "cognition_inbox"
    pack = brains_hear([{"event_id": "e1"}], state=st, inbox=inbox)
    assert pack["brains_receive_cognition_inbox"] >= 1
    assert all(r["executable"] is False for r in pack["receipts"])
    cortex = next(r for r in pack["receipts"] if r["brain"] == "cortex")
    assert cortex["heard"] is True
    bb = next(r for r in pack["receipts"] if r["brain"] == "business_brain")
    assert bb["status"] == "BRAIN_DEGRADED"


def test_telegram_lane_detector():
    assert is_telegram_lane("_ops/telegram_center/center.py") is True
    assert is_telegram_lane("_ops/state/telegram/tool-requests.jsonl") is True
    assert is_telegram_lane("_ops/organs/knowledge_afferent.py") is False


def test_mapper_dead_imports_skip_stdlib():
    tmp = Path(tempfile.mkdtemp())
    ops = tmp / "_ops"
    ops.mkdir()
    (ops / "user_mod.py").write_text("import hmac\nimport definitely_missing_local_xyz\n", encoding="utf-8")
    dead = _dead_imports([ops / "user_mod.py"], tmp)
    missing = {d["missing"] for d in dead}
    assert "hmac" not in missing
    assert "definitely_missing_local_xyz" in missing


def test_telemetry_by_source():
    now = time.time()
    ev = [
        {"source": "knowledge", "status": "ok", "ingested_at_unix": now - 30},
        {"source": "knowledge", "status": "ok", "ingested_at_unix": now},
    ]
    d = per_minute_by_source(ev, window_s=60, now=now)
    assert d["knowledge"] > 0


def main() -> int:
    failed = []
    tests = [
        test_starvation_root_cause_decided,
        test_sentinel_negative_is_unknown,
        test_tool_request_quarantine_and_policy,
        test_rfc_merge_and_cap,
        test_autotune_zero_evidence_once,
        test_halt_has_machine_cause_and_rfc,
        test_bitemporal_no_future_no_fabricate,
        test_duplicate_event_idempotent,
        test_knowledge_scan_empty_malformed_stale,
        test_classify_and_classes,
        test_dead_feedback_loop,
        test_cognition_inbox_receipts,
        test_telegram_lane_detector,
        test_mapper_dead_imports_skip_stdlib,
        test_telemetry_by_source,
    ]
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((fn.__name__, type(e).__name__, str(e)))
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
