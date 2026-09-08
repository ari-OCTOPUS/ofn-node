"""event_envelope_v1 — cross-node EventEnvelope (F3 LOCAL_CRDT spine).

Additive only. No writer/publisher/bus cutover. Not Graphiti.
stdlib-only dataclass + ContractViolation (same style as runtime_truth_v1).

Five mandatory fields — missing or empty is a ContractViolation:
  trace_id     correlation id for the fact
  source_node  NODE_IDS member (138 | 180 | 182 | laptop)
  trust_level  LOCAL | PEER | UNTRUSTED
  event_time   when the fact occurred (bitemporal)
  record_time  when this node recorded it (bitemporal)

FROZEN.lock pins runtime_truth_v1.py only — this file is new, not that pin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from .runtime_truth_v1 import NODE_IDS, ContractViolation

CONTRACT_SCHEMA = "event_envelope.v1"

MANDATORY_FIELDS: Tuple[str, ...] = (
    "trace_id", "source_node", "trust_level", "event_time", "record_time",
)

# LOCAL — first-hand on source_node
# PEER — relayed by another NODE_IDS member
# UNTRUSTED — recorded without peer attestation
TRUST_LEVELS: Tuple[str, ...] = ("LOCAL", "PEER", "UNTRUSTED")


@dataclass(frozen=True)
class EventEnvelope:
    trace_id: str
    source_node: str
    trust_level: str
    event_time: str
    record_time: str

    def __post_init__(self) -> None:
        for name in MANDATORY_FIELDS:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractViolation(f"{name} missing/empty")
        if self.source_node not in NODE_IDS:
            raise ContractViolation(
                f"source_node {self.source_node!r} not in {NODE_IDS}")
        if self.trust_level not in TRUST_LEVELS:
            raise ContractViolation(
                f"trust_level {self.trust_level!r} not in {TRUST_LEVELS}")

    @classmethod
    def from_dict(cls, data: Mapping) -> "EventEnvelope":
        if not isinstance(data, Mapping):
            raise ContractViolation("envelope must be a mapping")
        missing = [k for k in MANDATORY_FIELDS if k not in data]
        if missing:
            raise ContractViolation(f"missing mandatory fields: {missing}")
        return cls(**{k: data[k] for k in MANDATORY_FIELDS})

    def as_dict(self) -> dict:
        return {
            "schema": CONTRACT_SCHEMA,
            "trace_id": self.trace_id,
            "source_node": self.source_node,
            "trust_level": self.trust_level,
            "event_time": self.event_time,
            "record_time": self.record_time,
        }
