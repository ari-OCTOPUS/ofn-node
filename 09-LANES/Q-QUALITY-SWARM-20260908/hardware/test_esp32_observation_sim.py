"""Simulated ESP32 observation — no serial, no GPIO, no LAN listener.

Builds a valid observation.v1 via the existing USGS parser and a draft
board_events envelope. Does NOT mark GAP-015 PASS.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "_ops"))
from observatory.observation_v1 import PARSE_DRIFT, SCHEMA, parse_body  # noqa: E402

ENVELOPE_SCHEMA = "board_events.envelope.v0"


def fake_usgs_body() -> bytes:
    return json.dumps(
        {
            "features": [
                {
                    "properties": {
                        "mag": 1.0,
                        "place": "sim-not-a-sensor",
                        "time": 1,
                    }
                }
            ]
        }
    ).encode("utf-8")


def draft_envelope(observation: dict) -> dict:
    return {
        "schema": ENVELOPE_SCHEMA,
        "board_id": "ESP-001",
        "firmware_hash": "UNSTATED",
        "event_id": "sim-001",
        "sequence": 1,
        "emitted_at": "2026-09-08T05:30:00Z",
        "payload": observation,
        "may_authorize": False,
        "applied": False,
        "powered_on": False,
        "transport": "in_process_sim",
        "gpio": False,
        "serial": False,
        "new_lan_listeners": 0,
    }


def test_valid_observation_v1_and_envelope() -> None:
    obs = parse_body(
        url="https://example.invalid/sim",
        fetched_at="2026-09-08T05:30:00Z",
        body=fake_usgs_body(),
    )
    assert obs["ok"] is True
    assert obs["schema"] == SCHEMA
    assert obs["feeds_organism_decision"] is False
    env = draft_envelope(obs)
    assert env["may_authorize"] is False
    assert env["applied"] is False
    assert env["new_lan_listeners"] == 0
    bad = parse_body(
        url="https://example.invalid/sim",
        fetched_at="2026-09-08T05:30:00Z",
        body=b"not-json",
    )
    assert bad["ok"] is False and bad["error"] == PARSE_DRIFT


if __name__ == "__main__":
    try:
        test_valid_observation_v1_and_envelope()
        print("PASS test_valid_observation_v1_and_envelope")
        print("GAP-015_STATUS=UNVALIDATED")
    except Exception as e:
        print("FAIL", e)
        raise SystemExit(1)
    raise SystemExit(0)
