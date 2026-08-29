"""Exchange channel tests. Run: /opt/octopus/venv/bin/pytest tests/ -q
Uses a temp exchange root via env vars set before importing board_exchange.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))


@pytest.fixture()
def bx(tmp_path, monkeypatch):
    root = tmp_path / "inbound"
    (root / "TO-LAPTOP/exchange").mkdir(parents=True)
    (root / "FROM-LAPTOP/exchange").mkdir(parents=True)
    monkeypatch.setenv("OCTOPUS_EXCH_ROOT", str(root))
    monkeypatch.setenv("OCTOPUS_EXCH_TEST", "1")
    import board_exchange
    importlib.reload(board_exchange)
    board_exchange.HERE = HERE
    board_exchange.OUT_DIR = root / "TO-LAPTOP/exchange"
    board_exchange.IN_DIR = root / "FROM-LAPTOP/exchange"
    board_exchange.QUARANTINE = board_exchange.IN_DIR / "quarantine"
    board_exchange.PROCESSED = board_exchange.IN_DIR / "processed"
    board_exchange.LEDGER = tmp_path / "ledger.jsonl"
    return board_exchange


def valid_inbound(bx, **over):
    payload = over.pop("payload", {"topic": "gaps"})
    from validate_envelope import payload_sha
    msg = {
        "msg_id": "msg-20260817T1200Z-00000001", "run_id": "run-laptop-1",
        "from": "laptop", "to": "board", "type": "QUERY",
        "ts_utc": "2026-08-17T12:00:00Z", "boot_id": "laptop-boot-x",
        "evidence_refs": [], "payload": payload, "payload_hash": payload_sha(payload),
        "prev_msg_hash": None, "may_authorize": False,
    }
    msg.update(over)
    return msg


def test_validator_rejects_missing_field(bx):
    from validate_envelope import validate
    msg = valid_inbound(bx); msg.pop("boot_id")
    ok, errs = validate(msg, "inbound")
    assert not ok and any(e.startswith("X02") for e in errs)


def test_validator_rejects_wrong_direction(bx):
    from validate_envelope import validate
    ok, errs = validate(valid_inbound(bx, **{"from": "board", "to": "laptop"}), "inbound")
    assert not ok and any(e.startswith("X04") for e in errs)


def test_validator_rejects_bad_type(bx):
    from validate_envelope import validate
    ok, errs = validate(valid_inbound(bx, type="COMMAND"), "inbound")
    assert not ok and any(e.startswith("X05") for e in errs)


def test_validator_rejects_hash_mismatch(bx):
    from validate_envelope import validate
    ok, errs = validate(valid_inbound(bx, payload_hash="sha256:" + "0" * 64), "inbound")
    assert not ok and any(e.startswith("X09") for e in errs)


def test_validator_rejects_may_authorize(bx):
    from validate_envelope import validate
    ok, errs = validate(valid_inbound(bx, may_authorize=True), "inbound")
    assert not ok and any(e.startswith("X11") for e in errs)


def test_payload_scan_finds_command_key(bx):
    from validate_envelope import scan_inbound_payload
    v = scan_inbound_payload({"cmd": "systemctl restart octopus-sensorium"})
    assert any(x.startswith("P01") for x in v)


def test_payload_scan_finds_command_value(bx):
    from validate_envelope import scan_inbound_payload
    v = scan_inbound_payload({"note": "sudo reboot"})
    assert any(x.startswith("P01") for x in v)


def test_payload_scan_finds_credentials(bx):
    from validate_envelope import scan_inbound_payload
    v = scan_inbound_payload({"blob": "-----BEGIN OPENSSH PRIVATE KEY-----"})
    assert any(x.startswith("P02") for x in v)


def test_payload_scan_finds_authority_key(bx):
    from validate_envelope import scan_inbound_payload
    v = scan_inbound_payload({"enable_flag": "OBSERVATORY"})
    assert any(x.startswith("P03") for x in v)


def test_inbound_valid_query_gets_answer(bx):
    msg = valid_inbound(bx)
    (bx.IN_DIR / "in1.json").write_text(json.dumps(msg))
    s = bx.process_inbound("run-test-1")
    assert s == {"received": 1, "valid": 1, "dropped": 0, "blocked": 0, "answered": 1}
    outs = list((bx.OUT_DIR).glob("msg-*.json"))
    assert len(outs) == 1
    reply = json.loads(outs[0].read_text())
    assert reply["type"] == "REPORT" and reply["payload"]["in_reply_to"] == msg["msg_id"]
    assert not list(bx.IN_DIR.glob("*.json"))


def test_inbound_command_payload_blocked_and_quarantined(bx):
    msg = valid_inbound(bx, payload={"cmd": "reboot"}, type="REPORT")
    from validate_envelope import payload_sha
    msg["payload_hash"] = payload_sha(msg["payload"])
    (bx.IN_DIR / "bad.json").write_text(json.dumps(msg))
    s = bx.process_inbound("run-test-2")
    assert s["blocked"] == 1 and s["valid"] == 0
    assert len(list(bx.QUARANTINE.glob("*.json"))) == 1
    replies = [json.loads(p.read_text()) for p in bx.OUT_DIR.glob("msg-*.json")]
    blocked = [r for r in replies if r["payload"].get("status") == "BLOCKED_NEEDS_OWNER"]
    assert blocked and blocked[0]["payload"]["blocked_msg_id"] == msg["msg_id"]


def test_inbound_malformed_dropped(bx):
    (bx.IN_DIR / "broken.json").write_text("{nope")
    s = bx.process_inbound("run-test-3")
    assert s["dropped"] == 1 and len(list(bx.QUARANTINE.glob("*.json"))) == 1


def test_outbound_chain_integrity(bx):
    e1 = bx.build_envelope("REPORT", {"n": 1}, [], "run-test-4")
    e2 = bx.build_envelope("REPORT", {"n": 2}, [], "run-test-4")
    h1 = bx.msg_hash(e1)
    assert e1["prev_msg_hash"] is None
    assert e2["prev_msg_hash"] == h1


def test_inbound_ack_recorded_no_reply(bx):
    msg = valid_inbound(bx, type="ACK", payload={"ack_for": "msg-x"})
    from validate_envelope import payload_sha
    msg["payload_hash"] = payload_sha(msg["payload"])
    (bx.IN_DIR / "ack.json").write_text(json.dumps(msg))
    s = bx.process_inbound("run-test-5")
    assert s["answered"] == 0 and s["valid"] == 1
    assert not list((bx.OUT_DIR).glob("msg-*.json"))


# ---------- v1.1 Evidence Envelope (owner verification doctrine 2026-08-18) ----------

def test_v11_evidence_block_accepted_and_validated():
    from validate_envelope import validate
    base = {
        "msg_id": "msg-20260818T020000Z-abcdef12", "run_id": "run-t", "from": "board",
        "to": "laptop", "type": "EVIDENCE", "ts_utc": "2026-08-18T02:00:00Z",
        "boot_id": "b", "evidence_refs": [], "payload": {"x": 1},
        "payload_hash": None, "prev_msg_hash": None, "may_authorize": False,
    }
    from validate_envelope import payload_sha
    base["payload_hash"] = payload_sha(base["payload"])
    good = dict(base, claim="c", uncertainty="u", escalation="e", initiating_owner="Armin",
                reproduction=["echo hi"], raw_evidence=[{"desc": "d", "sha256": "x"}])
    ok, errors = validate(good, "outbound")
    assert ok, errors
    bad = dict(good, reproduction=["echo hi", 42])
    ok2, errors2 = validate(bad, "outbound")
    assert not ok2 and any(e.startswith("X12") for e in errors2)
    bad2 = dict(good, claim=7)
    ok3, errors3 = validate(bad2, "outbound")
    assert not ok3 and any(e.startswith("X12") for e in errors3)


def test_v11_absent_fields_still_valid_v1(bx):
    from validate_envelope import validate
    msg = {
        "msg_id": "msg-20260818T020001Z-abcdef12", "run_id": "run-t", "from": "laptop",
        "to": "board", "type": "ACK", "ts_utc": "2026-08-18T02:00:01Z",
        "boot_id": "b", "evidence_refs": [], "payload": {},
        "prev_msg_hash": None, "may_authorize": False,
    }
    from validate_envelope import payload_sha
    msg["payload_hash"] = payload_sha(msg["payload"])
    ok, errors = validate(msg, "inbound")
    assert ok, errors


def test_generate_emits_evidence_block(bx, monkeypatch):
    # generate() must attach the doctrine fields to the EVIDENCE message
    monkeypatch.setattr(bx, "sensorium_gauge", lambda *a, **k: {"service": "active"})
    monkeypatch.setattr(bx, "readiness_gauge", lambda: {"readiness_state": "READY"})
    monkeypatch.setattr(bx, "gaps_gauge", lambda: {})
    monkeypatch.setattr(bx, "changelog_tail", lambda *a, **k: [])
    monkeypatch.setattr(bx, "last_experiment", lambda: {})
    monkeypatch.setattr(bx, "cross_nodes_gauge", lambda: {})
    monkeypatch.setattr(bx, "authority_hashes", lambda: {})
    monkeypatch.setattr(bx, "senses_gauge", lambda: {"board_id": "sensorium-opi5pro-68e44cdf", "sensor_manifest_version": "6"})
    out = bx.generate("run-test-v11")
    files = sorted(bx.OUT_DIR.glob("msg-*.json"))
    evs = [json.loads(f.read_text()) for f in files if json.loads(f.read_text())["type"] == "EVIDENCE"]
    assert evs, "no EVIDENCE message generated"
    ev = evs[-1]
    for key in ("claim", "raw_evidence", "reproduction", "uncertainty", "escalation"):
        assert key in ev, f"missing {key}"
