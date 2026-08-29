from __future__ import annotations

import json

from octopus_sensorium.audit import AuditLog, verify_chain
from octopus_sensorium.snapshot import append_event, replay, replay_matches_current, state_hash


def test_audit_hash_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    head = tmp_path / "head.hash"
    log = AuditLog(path, head)
    log.append("a", n=1)
    log.append("b", n=2)
    ok, detail = verify_chain(path, head)
    assert ok, detail
    # Tamper with first payload without fixing hashes.
    lines = path.read_text(encoding="utf-8").splitlines()
    rec0 = lines[0].replace('"n":1', '"n":99')
    path.write_text(rec0 + "\n" + lines[1] + "\n", encoding="utf-8")
    ok, _detail = verify_chain(path, head)
    assert ok is False


def test_audit_delayed_fork_from_earlier_parent(tmp_path):
    path = tmp_path / "audit.jsonl"
    head = tmp_path / "head.hash"
    log = AuditLog(path, head)
    log.append("boot_gates", n=1)
    log.append("operator_note", n=2)
    first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    delayed = dict(json.loads(path.read_text(encoding="utf-8").splitlines()[1]))
    # Simulate a concurrent agent record that still parents the first line.
    from octopus_sensorium.audit import chain_hash, canonical_json, sha256_bytes

    body = {"event_type": "nats_disconnected", "sequence": 2, "n": 99}
    payload_hash = sha256_bytes(canonical_json(body))
    rec = {
        **body,
        "previous_hash": first["record_hash"],
        "payload_hash": payload_hash,
        "record_hash": chain_hash(first["record_hash"], payload_hash),
        "signature": None,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n")
    head.write_text(rec["record_hash"] + "\n", encoding="utf-8")
    ok, detail = verify_chain(path, head)
    assert ok, detail


def test_replay_hash_equality(tmp_path, monkeypatch):
    journal = tmp_path / "events.jsonl"
    monkeypatch.setattr("octopus_sensorium.snapshot.DEFAULT_JOURNAL", journal)
    append_event({"kind": "identity", "identity": {"board_id": "x"}}, journal)
    append_event({"kind": "health", "sensor_id": "OCT-SENSE-051", "status": "healthy"}, journal)
    append_event({"kind": "obs", "sensor_id": "OCT-SENSE-051", "content_hash": "sha256:abc"}, journal)
    reconstructed = replay(journal)
    current = {
        "identity": {"board_id": "x"},
        "health": {"OCT-SENSE-051": "healthy"},
        "observations_published": 1,
        "observation_hashes": ["sha256:abc"],
        "actuator_authority": "NONE",
        "leg_authority": "DENIED",
        "readiness_profile": "WAVE0_OBSERVE_ONLY",
    }
    current["state_hash"] = state_hash(current)
    current["journal_seq"] = 3
    ok, detail = replay_matches_current(current, journal)
    assert ok, detail
