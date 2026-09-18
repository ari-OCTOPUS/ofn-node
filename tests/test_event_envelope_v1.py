"""F3 NATS_LEAF_MIRROR spine — EventEnvelope schema + empty leaf/mirror init."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.event_envelope_v1 import (  # noqa: E402
    MANDATORY_FIELDS, NODE_IDS, EventEnvelope,
)
from contracts.nats_leaf_mirror_init import (  # noqa: E402
    DEFAULT_INIT, EMPTY_INIT, open_or_create_empty, read_init,
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


def test_empty_init_creates_disabled_stub(tmp_path: Path) -> None:
    path = tmp_path / "spine" / "nats_leaf_mirror.init.json"
    got = open_or_create_empty(path)
    assert got == path
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == EMPTY_INIT["schema"]
    assert data["enabled"] is False
    assert data["mode"] == "leaf_mirror"


def test_empty_init_does_not_migrate(tmp_path: Path) -> None:
    path = tmp_path / "nats_leaf_mirror.init.json"
    planted = b'{"schema":"legacy","enabled":false}\n'
    path.write_bytes(planted)
    open_or_create_empty(path)
    assert path.read_bytes() == planted


def test_read_init_forbids_enabled_true(tmp_path: Path) -> None:
    path = tmp_path / "nats_leaf_mirror.init.json"
    path.write_text(json.dumps({**EMPTY_INIT, "enabled": True}), encoding="utf-8")
    with pytest.raises(ContractViolation):
        read_init(path)


def test_repo_init_is_disabled_durable() -> None:
    assert DEFAULT_INIT.is_file()
    data = read_init()
    assert data["enabled"] is False
