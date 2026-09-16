#!/usr/bin/env python3
"""Fixture tests for epistemics.readers — fail-closed, non-null samples.

Uses a temp OPS tree (no live send, no center touch). Reversible: does not
mutate production state.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

_OPS = harness.SELF_OPS
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


def _write(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        p.write_text(obj, encoding="utf-8")
    else:
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _fixture_ops() -> Path:
    root = Path(tempfile.mkdtemp(prefix="epi-readers-"))
    # uniqueness latest
    _write(
        root / "state" / "doctor" / "poller-uniqueness-latest.json",
        {
            "schema": "poller-uniqueness-receipt/1",
            "ok": True,
            "fail_closed": True,
            "beat": 1,
            "checked_at_unix": 1.0,
            "checks": {
                "one_center_pid": True,
                "one_active_lease": True,
                "one_tg_poller_lock": True,
                "pids_agree": True,
            },
        },
    )
    # uniqueness jsonl (second receipt, fail)
    (root / "state" / "doctor" / "poller-uniqueness.jsonl").write_text(
        json.dumps(
            {
                "schema": "poller-uniqueness-receipt/1",
                "ok": False,
                "beat": 2,
                "checked_at_unix": 2.0,
                "checks": {
                    "one_center_pid": True,
                    "one_active_lease": False,
                    "one_tg_poller_lock": True,
                    "pids_agree": False,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    # outbox
    for i, st in enumerate(
        ["CONFIRMED", "CONFIRMED", "NEEDS_RECONCILIATION", "DRY_RUN_NO_SEND"]
    ):
        _write(
            root / "state" / "telegram" / "loop" / "outbox" / f"{i:04d}.json",
            {"schema": "telegram-outbox/1", "state": st, "message_key": f"k{i}"},
        )
    # self_audit matrix
    _write(
        root / "state" / "cortex" / "audit-matrix.json",
        {
            "schema": "audit-matrix.v1",
            "n": 4,
            "tally": {"Done": 2, "Partial": 1, "Missing": 1, "Unknown": 0},
            "items": [
                {"item": "a", "status": "Done", "evidence_bound": True},
                {"item": "b", "status": "Done", "evidence_bound": False},
                {"item": "c", "status": "Partial"},
                {"item": "d", "status": "Missing"},
            ],
        },
    )
    # self_accuracy
    lines = [
        json.dumps({"ts": "t1", "accuracy": 1.0, "fields_checked": 3}),
        json.dumps({"ts": "t2", "accuracy": 0.5, "fields_checked": 2}),
        json.dumps({"ts": "t3", "accuracy": 0.0, "fields_checked": 1}),
    ]
    p = root / "state" / "doctor" / "self-accuracy.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def t_fail_closed_empty_ops():
    from epistemics import readers

    empty = Path(tempfile.mkdtemp(prefix="epi-empty-"))
    assert readers.read_uniqueness_receipts(empty) == []
    assert readers.read_outbox_counts(empty) == {}
    assert readers.read_self_audit(empty) is None
    assert readers.read_topology(empty) is None
    assert readers.read_self_vs_twin(empty) is None
    assert readers.read_state_labels(empty) == []
    assert readers.read_channel_pairs(empty) == []


def t_fixture_non_null_samples():
    from epistemics import readers

    ops = _fixture_ops()
    labels = readers.read_state_labels(ops)
    pairs = readers.read_channel_pairs(ops)
    topo = readers.read_topology(ops)
    sv = readers.read_self_vs_twin(ops)
    counts = readers.read_outbox_counts(ops)

    assert len(labels) > 0, "state_labels must be non-empty on fixture"
    assert len(pairs) > 0, "channel_pairs must be non-empty on fixture"
    assert topo is not None and len(topo) == 3  # uniqueness-only fixture
    assert sum(sum(row) for row in topo) > 0, "triangle edges expected when checks pass"
    assert sv is not None
    assert len(sv["err_self"]) > 0 and len(sv["err_other"]) > 0
    assert counts.get("CONFIRMED") == 2
    assert counts.get("NEEDS_RECONCILIATION") == 1
    assert "NOT a consciousness" in sv["note"]


def t_compute_all_non_null_values():
    from epistemics.run_offloop import compute_all

    ops = _fixture_ops()
    results = compute_all(ops)
    by = {r["metric"]: r for r in results}
    assert by["identifiability"]["value"] is not None
    assert by["identifiability"]["sample_size"] > 0
    assert by["channel"]["value"] is not None
    assert by["channel"]["sample_size"] > 0
    assert by["levels"]["value"] is not None
    assert by["levels"]["sample_size"] >= 3
    assert by["self_reference"]["value"] is not None
    assert by["self_reference"]["sample_size"] > 0
    assert "NOT a consciousness" in by["self_reference"]["notes"] or "NOT" in by["self_reference"]["notes"]
    assert by["method"]["value"]["phenomenal_claim"] is False
    assert by["method"]["value"]["unconditional_claim"] is False
    # small fixture => not authoritative
    assert by["identifiability"]["authoritative"] is False
    assert by["channel"]["authoritative"] is False


def t_corrupt_json_fail_closed():
    from epistemics import readers

    root = Path(tempfile.mkdtemp(prefix="epi-corrupt-"))
    p = root / "state" / "cortex" / "audit-matrix.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not-json", encoding="utf-8")
    assert readers.read_self_audit(root) is None


def t_no_write_side_effects():
    """readers must not create files under ops fixture."""
    from epistemics import readers

    ops = _fixture_ops()
    before = {str(p): p.stat().st_mtime for p in ops.rglob("*") if p.is_file()}
    readers.read_state_labels(ops)
    readers.read_channel_pairs(ops)
    readers.read_topology(ops)
    readers.read_self_vs_twin(ops)
    after = {str(p): p.stat().st_mtime for p in ops.rglob("*") if p.is_file()}
    assert before.keys() == after.keys()
    for k in before:
        assert before[k] == after[k]


def t_live_ops_non_null_if_evidence_present():
    """Against real F:\\backup\\_ops — soft assert only when evidence files exist."""
    from epistemics import readers

    ops = _OPS
    uniq = ops / "state" / "doctor" / "poller-uniqueness-latest.json"
    outbox = ops / "state" / "telegram" / "loop" / "outbox"
    audit = ops / "state" / "cortex" / "audit-matrix.json"
    if not (uniq.is_file() and audit.is_file() and outbox.is_dir()):
        return  # skip soft
    labels = readers.read_state_labels(ops)
    pairs = readers.read_channel_pairs(ops)
    topo = readers.read_topology(ops)
    sv = readers.read_self_vs_twin(ops)
    assert len(labels) > 0
    assert len(pairs) > 0
    assert topo is not None
    assert sv is not None and len(sv["err_self"]) > 0


def _enriched_topology_ops() -> Path:
    """Backup-shaped tree: _ops + CURRENT-HARDWARE + Board2 legs + wave dirs + box."""
    backup = Path(tempfile.mkdtemp(prefix="epi-topo-backup-"))
    ops = backup / "_ops"
    # uniqueness under ops
    _write(
        ops / "state" / "doctor" / "poller-uniqueness-latest.json",
        {
            "schema": "poller-uniqueness-receipt/1",
            "ok": True,
            "beat": 1,
            "checked_at_unix": 1.0,
            "checks": {
                "one_center_pid": True,
                "one_active_lease": True,
                "one_tg_poller_lock": True,
                "pids_agree": True,
            },
        },
    )
    # doctor box-latest
    _write(
        ops / "state" / "doctor" / "box-latest.json",
        {"ts": "t", "beat": 1, "report": {"stepped": True, "tick": 1}},
    )
    # registry live organs
    _write(
        ops / "state" / "registry" / "registry-latest.json",
        {
            "schema": "registry.v0",
            "entities": [
                {
                    "logical_id": "urn:octopus:organ:cortex",
                    "entity_type": "Organ",
                    "live_state": "live",
                },
                {
                    "logical_id": "urn:octopus:organ:doctor",
                    "entity_type": "Organ",
                    "live_state": "live",
                },
                {
                    "logical_id": "urn:octopus:organ:money",
                    "entity_type": "Organ",
                    "live_state": "live",
                },
                {
                    "logical_id": "urn:octopus:organ:heart",
                    "entity_type": "Organ",
                    "live_state": "shadow",
                },
            ],
        },
    )
    # hardware pointer
    hw = backup / "07 - Knowledge" / "octopus" / "CURRENT-HARDWARE.md"
    hw.parent.mkdir(parents=True, exist_ok=True)
    hw.write_text(
        "# CURRENT HARDWARE\n| **Laptop** | SoT |\n| **Orange Pi** | Sensorium |\n| **Board2 DietPi** | M4 Legs |\n",
        encoding="utf-8",
    )
    # boards legs map
    _write(
        backup / "06-EVIDENCE" / "BOARD2-LEGS-VERIFY-MAP-2026-08-22" / "RESULT.json",
        {
            "mapping": {
                "lead": "Master Painting",
                "studio": "Studio",
                "ziman": "GiftMesh",
                "panel": "owner panel",
            }
        },
    )
    # wave evidence dirs (non-empty)
    for name in [
        "OCTOPUS-WAVE0-SOFT-ESTOP-UNLOCK-2026-08-23",
        "OCTOPUS-ORANGEPI-MQTT-1883-ENABLE-ABD-2026-08-22",
        "OCTOPUS-ORANGEPI-ESP32-INET-DATA-START-2026-08-22",
        "OCTOPUS-ORANGEPI-TORCH-EXECUTE-2026-08-22",
        "OCTOPUS-CKPT348-OWNER-SIGN-2026-08-22",
        "BOARD2-STATUS-REFRESH-2026-08-23",
        "BOARD2-CANONICAL-MAP-2026-08-22",
    ]:
        d = backup / "06-EVIDENCE" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "RESULT.json").write_text("{\"ok\": true}\n", encoding="utf-8")
    return ops


def t_enriched_topology_min_samples_8():
    """levels gate MIN_SAMPLES=8: enriched on-disk sources must yield >=8 nodes."""
    from epistemics import readers
    from epistemics import contracts as C

    ops = _enriched_topology_ops()
    topo = readers.read_topology(ops)
    meta = readers.read_topology_meta(ops)
    assert topo is not None
    n = len(topo)
    assert n >= C.MIN_SAMPLES[C.LEVELS], f"expected >=8 topology nodes, got {n}; meta={meta}"
    assert meta["n_nodes"] == n
    assert meta["n_edges"] > 0
    # fail-closed: missing wave dir must not invent that capability node
    missing = Path(tempfile.mkdtemp(prefix="epi-topo-miss-"))
    ops2 = missing / "_ops"
    _write(
        ops2 / "state" / "doctor" / "poller-uniqueness-latest.json",
        {
            "ok": True,
            "checks": {
                "one_center_pid": True,
                "one_active_lease": True,
                "one_tg_poller_lock": True,
                "pids_agree": True,
            },
        },
    )
    # no hardware / no waves -> uniqueness-only 3
    topo2 = readers.read_topology(ops2)
    assert topo2 is not None and len(topo2) == 3


def t_live_topology_gate_or_document():
    """Live F:\\backup\\_ops: assert >=8 when sources present, else soft-skip."""
    from epistemics import readers
    from epistemics import contracts as C
    from epistemics import metrics

    ops = _OPS
    meta = readers.read_topology_meta(ops)
    topo = readers.read_topology(ops)
    if topo is None:
        return
    n = len(topo)
    lvl = metrics.levels(topo)
    # Soft: if live sources exist for hardware+waves, require gate.
    probed = meta.get("sources_probed") or {}
    rich = probed.get("hardware_pointer") and probed.get("boards_legs_map")
    if rich:
        assert n >= C.MIN_SAMPLES[C.LEVELS], f"live topology below gate: n={n} meta={meta}"
        assert lvl["sample_size"] >= C.MIN_SAMPLES[C.LEVELS]
        assert lvl["authoritative"] is True



if __name__ == "__main__":
    failed = harness.run(
        [
            ("fail-closed empty ops", t_fail_closed_empty_ops),
            ("fixture non-null samples", t_fixture_non_null_samples),
            ("compute_all non-null values", t_compute_all_non_null_values),
            ("corrupt json fail-closed", t_corrupt_json_fail_closed),
            ("no write side effects", t_no_write_side_effects),
            ("live ops non-null if evidence", t_live_ops_non_null_if_evidence_present),
            ("enriched topology >=8", t_enriched_topology_min_samples_8),
            ("live topology gate or soft", t_live_topology_gate_or_document),
        ]
    )
    sys.exit(1 if failed else 0)
