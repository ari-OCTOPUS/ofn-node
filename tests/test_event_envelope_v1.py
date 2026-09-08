"""F3 LOCAL_CRDT spine — EventEnvelope schema + empty store init."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.event_envelope_v1 import (  # noqa: E402
    MANDATORY_FIELDS, NODE_IDS, EventEnvelope,
)
from contracts.local_crdt_store import (  # noqa: E402
    DEFAULT_STORE, open_or_create_empty,
)
from contracts.runtime_truth_v1 import ContractViolation  # noqa: E402


def _valid(**over) -> dict:
    base = dict(
        trace_id="tr-001",
        source_node="138",
        trust_level="LOCAL",
        event_time="2026-09-08T00:00:00Z",
        record_time="2026-09-08T00:00:01Z",
    )
    base.update(over)
    return base


@pytest.mark.parametrize("field", MANDATORY_FIELDS)
def test_rejects_missing_mandatory_field(field: str) -> None:
    data = _valid()
    del data[field]
    with pytest.raises(ContractViolation):
        EventEnvelope.from_dict(data)


@pytest.mark.parametrize("field", MANDATORY_FIELDS)
def test_rejects_empty_mandatory_field(field: str) -> None:
    with pytest.raises(ContractViolation):
        EventEnvelope.from_dict(_valid(**{field: "   "}))


def test_accepts_valid_envelope() -> None:
    env = EventEnvelope.from_dict(_valid())
    d = env.as_dict()
    assert d["trace_id"] == "tr-001"
    assert d["source_node"] in NODE_IDS
    assert d["trust_level"] == "LOCAL"
    assert d["event_time"]
    assert d["record_time"]


def test_rejects_unknown_source_node_or_trust() -> None:
    with pytest.raises(ContractViolation):
        EventEnvelope.from_dict(_valid(source_node="190"))
    with pytest.raises(ContractViolation):
        EventEnvelope.from_dict(_valid(trust_level="GREEN"))


def test_empty_store_init_creates_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "spine" / "events.jsonl"
    got = open_or_create_empty(path)
    assert got == path
    assert path.is_file()
    assert path.read_bytes() == b""


def test_empty_store_init_does_not_migrate(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    planted = b'{"legacy":true}\n'
    path.write_bytes(planted)
    open_or_create_empty(path)
    assert path.read_bytes() == planted


def test_repo_spine_store_is_empty_durable() -> None:
    assert DEFAULT_STORE.is_file()
    before = DEFAULT_STORE.read_bytes()
    open_or_create_empty()
    assert DEFAULT_STORE.read_bytes() == before == b""
