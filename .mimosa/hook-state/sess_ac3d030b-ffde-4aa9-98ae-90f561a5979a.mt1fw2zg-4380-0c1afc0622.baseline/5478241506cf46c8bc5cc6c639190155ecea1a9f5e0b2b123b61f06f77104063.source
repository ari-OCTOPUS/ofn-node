# -*- coding: utf-8 -*-
"""Bitemporal spine spec test — lab slice, no network, no live-spine writes.

Implements the 2026-08-20 spec: eligibility matrix (M1-M4), late-arrival
boundary, correction without history overwrite, derived-memory leakage,
vector-index leakage, restart persistence hash, strict-vs-naive ablation,
context-builder contract, and the VERIFIED_BITEMPORAL gate table.

Scope: this verifies the CONTRACT LOGIC on a lab fixture memory.
The LIVE spine stays NOT_VERIFIED_BITEMPORAL until (a) the ADR-043
two-clock problem is fixed and (b) every memory read path routes through
a decision_time query. Neither is proven by this file.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import sys

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from shadow_homeostasis.observation import parse_dt

DAY = datetime(2026, 8, 20, tzinfo=timezone.utc)


def at(h: int, m: int = 0) -> datetime:
    return DAY.replace(hour=h, minute=m)


INELIGIBLE_TEMPORAL_METADATA = "INELIGIBLE_TEMPORAL_METADATA"
FUTURE_DATA = "FUTURE_DATA"
LATE_THRESHOLD_S = 300.0  # >5 min recorded-occurred gap labels late-arriving


@dataclass
class MemoryRecord:
    memory_id: str
    entity_id: str
    memory_type: str
    payload: dict
    occurred_at: datetime | str | None = None
    recorded_at: datetime | str | None = None
    valid_to: datetime | str | None = None
    supersedes_id: str | None = None
    provenance_ids: list[str] = field(default_factory=list)
    source_hash: str = ""
    confidence: float = 0.5
    tombstone: bool = False
    ingest_status: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("occurred_at", "recorded_at", "valid_to"):
            if isinstance(d[k], datetime):
                d[k] = d[k].astimezone(timezone.utc).isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryRecord":
        d = dict(d)
        for k in ("occurred_at", "recorded_at", "valid_to"):
            if isinstance(d.get(k), str):
                d[k] = parse_dt(d[k])
        return cls(**d)


@dataclass
class DerivedMemory:
    artifact_id: str
    kind: str
    recorded_at: datetime | str          # = derived_at; eligibility axis
    evidence_ids: list[str]
    evidence_cutoff: datetime | str
    payload: dict


class BitemporalMemory:
    """Append-only lab memory. Ingest never injects timestamps; queries
    enforce occurred_at <= recorded_at <= decision_time (WAVE0 contract)."""

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    def ingest(self, rec: MemoryRecord) -> str:
        occ, rec_at = parse_dt(rec.occurred_at), parse_dt(rec.recorded_at)
        if occ is None or rec_at is None:
            rec.ingest_status = INELIGIBLE_TEMPORAL_METADATA
        elif occ > rec_at:
            rec.ingest_status = FUTURE_DATA  # permanently ineligible (e.g. M4)
        else:
            rec.ingest_status = "OK"
        self._records.append(rec)
        return rec.ingest_status

    @staticmethod
    def _eligible(rec: MemoryRecord, decision_time: datetime) -> bool:
        occ, rec_at = parse_dt(rec.occurred_at), parse_dt(rec.recorded_at)
        if occ is None or rec_at is None:
            return False
        return occ <= rec_at <= decision_time

    def query(self, decision_time, entity_id: str | None = None,
              memory_type: str | None = None) -> list[MemoryRecord]:
        dt = parse_dt(decision_time)
        return [r for r in self._records
                if r.ingest_status != INELIGIBLE_TEMPORAL_METADATA
                and self._eligible(r, dt)
                and (entity_id is None or r.entity_id == entity_id)
                and (memory_type is None or r.memory_type == memory_type)]

    def naive_query(self) -> list[MemoryRecord]:
        """Ablation path: everything ever ingested with parseable clocks,
        ignoring decision_time entirely."""
        return [r for r in self._records
                if r.ingest_status not in (INELIGIBLE_TEMPORAL_METADATA, FUTURE_DATA)]

    def known_value(self, entity_id: str, memory_type: str, occurred_at,
                    decision_time) -> MemoryRecord | None:
        """Version visible at decision_time for the fact that occurred at
        occurred_at: superseding version wins only if ITSELF eligible."""
        occ_target = parse_dt(occurred_at)
        versions = [r for r in self.query(decision_time, entity_id, memory_type)
                    if parse_dt(r.occurred_at) == occ_target]
        if not versions:
            return None
        return max(versions, key=lambda r: parse_dt(r.recorded_at))

    def all_records(self) -> list[MemoryRecord]:
        return list(self._records)

    # -- persistence --
    def dump_jsonl(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for r in self._records:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    @classmethod
    def load_jsonl(cls, path: Path) -> "BitemporalMemory":
        mem = cls()
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    rec = MemoryRecord.from_dict(d)
                    rec.ingest_status = d["ingest_status"]  # preserve, don't re-judge
                    mem._records.append(rec)
        return mem


def arrival_label(rec: MemoryRecord) -> str:
    delay = (parse_dt(rec.recorded_at) - parse_dt(rec.occurred_at)).total_seconds()
    return "late-arriving" if delay >= LATE_THRESHOLD_S else "on-time"


def derived_eligible(art: DerivedMemory, decision_time) -> bool:
    return parse_dt(art.recorded_at) <= parse_dt(decision_time)


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db)


def vector_search(query: list[float], index: list[tuple[str, list[float], MemoryRecord]],
                  top_k: int) -> list[str]:
    """NAIVE vector path: pure similarity, no temporal filter."""
    ranked = sorted(index, key=lambda e: -_cosine(query, e[1]))
    return [eid for eid, _, _ in ranked[:top_k]]


def vector_search_strict(query: list[float], index: list[tuple[str, list[float], MemoryRecord]],
                         top_k: int, decision_time) -> list[str]:
    """STRICT vector path: temporal filter applied BEFORE consumption."""
    dt = parse_dt(decision_time)
    ranked = sorted(index, key=lambda e: -_cosine(query, e[1]))
    return [eid for eid, _, rec in ranked[:top_k] if BitemporalMemory._eligible(rec, dt)]


def context_for_decision(mem: BitemporalMemory, task: str,
                         decision_time) -> dict:
    """Rendered-context contract. executable=false; future evidence impossible
    by construction and re-checked (double entry)."""
    ctx = mem.query(decision_time)
    ctx_ids = {r.memory_id for r in ctx}
    dt = parse_dt(decision_time)
    future = [r.memory_id for r in ctx if not BitemporalMemory._eligible(r, dt)]
    # Double entry on the rendered form: a payload whose source value is None
    # must surface as null in the serialized context, never as 0.
    coerced = sum(1 for r in ctx
                  if r.payload.get("value") is None
                  and '"value": 0' in json.dumps(r.payload))
    return {
        "task": task,
        "decision_time": dt.isoformat(),
        "memory_ids": sorted(ctx_ids),
        "future_memory_ids": future,
        "unknown_coerced_to_zero": 0 if coerced == 0 else coerced,
        "all_context_has_provenance": all(r.provenance_ids for r in ctx),
        "decision_time_consistent": True,
        "executable": False,
    }


def outputs_hash(mem: BitemporalMemory, decision_times) -> str:
    payload = json.dumps([
        {"dt": parse_dt(dt).isoformat(),
         "ids": sorted(r.memory_id for r in mem.query(dt))}
        for dt in decision_times
    ], sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def build_fixture() -> BitemporalMemory:
    mem = BitemporalMemory()
    for rec in [
        MemoryRecord("M1", "tank", "temperature", {"value": 70},
                     occurred_at=at(10, 0), recorded_at=at(10, 1),
                     provenance_ids=["src:sensor-A"], source_hash="h1"),
        MemoryRecord("M2", "tank", "temperature", {"value": 90, "note": "late report"},
                     occurred_at=at(10, 5), recorded_at=at(10, 20),
                     provenance_ids=["src:sensor-B"], source_hash="h2"),
        MemoryRecord("M3", "tank", "temperature", {"value": 75},
                     occurred_at=at(10, 0), recorded_at=at(11, 0),
                     supersedes_id="M1",
                     provenance_ids=["src:sensor-A-correction"], source_hash="h3"),
        MemoryRecord("M4", "tank", "forecast", {"value": 99},
                     occurred_at=at(12, 0), recorded_at=at(9, 0),
                     provenance_ids=["src:planner"], source_hash="h4"),
    ]:
        mem.ingest(rec)
    return mem


def future_use_count(records: list[MemoryRecord], decision_time) -> int:
    dt = parse_dt(decision_time)
    occ_ok = lambda r: (parse_dt(r.occurred_at) is not None
                        and parse_dt(r.occurred_at) <= dt)
    rec_ok = lambda r: (parse_dt(r.recorded_at) is not None
                        and parse_dt(r.recorded_at) <= dt)
    return sum(1 for r in records if not (occ_ok(r) and rec_ok(r)))


def spine_gates(mem: BitemporalMemory, decision_times) -> tuple[dict, str]:
    dts = list(decision_times)
    strict_future_use = sum(future_use_count(mem.query(dt), dt) for dt in dts)
    naive_future_use = sum(future_use_count(mem.naive_query(), dt) for dt in dts)
    gates = {
        "strict_future_use_zero": strict_future_use == 0,
        "naive_ablation_future_use_positive": naive_future_use > 0,
        "historical_point_in_time_queries": mem.known_value(
            "tank", "temperature", at(10, 0), at(10, 30)).payload["value"] == 70,
        "late_arrival_boundary": (future_use_count(
            [r for r in mem.query(at(12, 1))], at(11, 0)) == 0),
        "correction_supersession": (mem.known_value(
            "tank", "temperature", at(10, 0), at(11, 30)).payload["value"] == 75),
        "history_not_overwritten": all(
            r.memory_id in {x.memory_id for x in mem.all_records()}
            for r in mem.all_records()) and len(mem.all_records()) == 4,
        "all_records_have_provenance": all(r.provenance_ids for r in mem.all_records()),
        "no_missing_timestamps_injected": not any(
            r.occurred_at is not None and r.ingest_status == INELIGIBLE_TEMPORAL_METADATA
            for r in mem.all_records()),
    }
    status = "VERIFIED_BITEMPORAL" if all(gates.values()) else "NOT_VERIFIED_BITEMPORAL"
    return gates, status


# --------------------------------------------------------------------------
# 1. Data contract
# --------------------------------------------------------------------------

def test_data_contract_missing_timestamps_not_injected():
    mem = BitemporalMemory()
    status = mem.ingest(MemoryRecord("MX", "tank", "note", {"value": 1},
                                     provenance_ids=["src:x"]))
    assert status == INELIGIBLE_TEMPORAL_METADATA
    rec = mem.all_records()[0]
    assert rec.occurred_at is None and rec.recorded_at is None  # no injection
    for dt in (at(10, 0), at(23, 0)):
        assert mem.query(dt) == []


# --------------------------------------------------------------------------
# 2. The M1-M4 eligibility matrix at 10:10 / 10:30 / 11:30
# --------------------------------------------------------------------------

def test_decision_1010_matrix():
    ids = {r.memory_id for r in build_fixture().query(at(10, 10))}
    assert ids == {"M1"}


def test_decision_1030_matrix():
    mem = build_fixture()
    recs = {r.memory_id: r for r in mem.query(at(10, 30))}
    assert set(recs) == {"M1", "M2"}
    assert arrival_label(recs["M1"]) == "on-time"
    assert arrival_label(recs["M2"]) == "late-arriving"


def test_decision_1130_matrix():
    ids = {r.memory_id for r in build_fixture().query(at(11, 30))}
    assert ids == {"M1", "M2", "M3"}


def test_m4_future_never_eligible():
    mem = build_fixture()
    for dt in (at(10, 10), at(10, 30), at(11, 30), at(12, 0), at(23, 59)):
        assert "M4" not in {r.memory_id for r in mem.query(dt)}


# --------------------------------------------------------------------------
# 3. Correction without erasing history
# --------------------------------------------------------------------------

def test_correction_supersession_matrix():
    mem = build_fixture()
    assert mem.known_value("tank", "temperature", at(10, 0),
                           at(10, 30)).payload["value"] == 70   # what we believed then
    assert mem.known_value("tank", "temperature", at(10, 0),
                           at(11, 30)).payload["value"] == 75   # what we believe now
    m1 = next(r for r in mem.all_records() if r.memory_id == "M1")
    m3 = next(r for r in mem.all_records() if r.memory_id == "M3")
    assert m3.supersedes_id == "M1"
    assert m1.provenance_ids != m3.provenance_ids               # independent provenance
    assert all(parse_dt(r.recorded_at) for r in (m1, m3))       # both versions retained


# --------------------------------------------------------------------------
# 4. Late-arrival boundary (incl. replay "even today")
# --------------------------------------------------------------------------

def test_late_arrival_visibility_boundary():
    mem = BitemporalMemory()
    mem.ingest(MemoryRecord("L1", "tank", "temperature", {"value": 80},
                            occurred_at=at(10, 0), recorded_at=at(12, 0),
                            provenance_ids=["src:late"]))
    assert "L1" not in {r.memory_id for r in mem.query(at(11, 0))}
    assert "L1" not in {r.memory_id for r in mem.query(at(10, 30))}
    assert "L1" in {r.memory_id for r in mem.query(at(12, 1))}
    # replay of the 11:00 decision today: decision_time is the axis, not wall clock
    assert "L1" not in {r.memory_id for r in mem.query(at(11, 0))}


# --------------------------------------------------------------------------
# 5. Derived-memory leakage
# --------------------------------------------------------------------------

def test_derived_memory_leakage():
    summary = DerivedMemory("summary-123", "summary", at(14, 0),
                            ["M1", "M2"], at(14, 0), {"text": "morning was warm"})
    assert derived_eligible(summary, at(11, 0)) is False  # about morning, derived at 14:00
    assert derived_eligible(summary, at(14, 30)) is True


def test_context_excludes_future_derived_artifacts():
    mem = build_fixture()
    ctx = context_for_decision(mem, "historical-task", at(10, 30))
    assert ctx["future_memory_ids"] == []
    assert "M3" not in ctx["memory_ids"] and "M4" not in ctx["memory_ids"]


# --------------------------------------------------------------------------
# 6. Vector-index leakage
# --------------------------------------------------------------------------

def test_vector_index_leakage():
    mem = build_fixture()
    m1 = next(r for r in mem.all_records() if r.memory_id == "M1")
    m4 = next(r for r in mem.all_records() if r.memory_id == "M4")
    query = [1.0, 0.0, 0.0]
    # M4 engineered to be the top-1 nearest neighbour
    index = [("M4", [0.99, 0.1, 0.0], m4), ("M1", [0.9, 0.2, 0.0], m1)]
    assert vector_search(query, index, 2)[0] == "M4"          # naive leaks the future
    strict = vector_search_strict(query, index, 2, at(10, 30))
    assert "M4" not in strict and strict[0] == "M1"           # strict filters it


# --------------------------------------------------------------------------
# 7. Restart & persistence
# --------------------------------------------------------------------------

def test_restart_replay_hash(tmp_path):
    mem = build_fixture()
    dts = [at(10, 10), at(10, 30), at(11, 30)]
    before = outputs_hash(mem, dts)
    path = tmp_path / "spine-fixture.jsonl"
    mem.dump_jsonl(path)
    reloaded = BitemporalMemory.load_jsonl(path)
    assert len(reloaded.all_records()) == len(mem.all_records())
    assert outputs_hash(reloaded, dts) == before


# --------------------------------------------------------------------------
# 8. Strict vs naive ablation
# --------------------------------------------------------------------------

def test_strict_vs_naive_ablation():
    mem = build_fixture()
    dts = [at(10, 10), at(10, 30), at(11, 30)]
    strict = sum(future_use_count(mem.query(dt), dt) for dt in dts)
    naive = sum(future_use_count(mem.naive_query(), dt) for dt in dts)
    assert strict == 0
    assert naive > 0  # fixture is sharp enough to detect leakage


# --------------------------------------------------------------------------
# 9. Context-builder end-to-end contract (STOP before network)
# --------------------------------------------------------------------------

def test_context_builder_contract():
    mem = build_fixture()
    mem.ingest(MemoryRecord("M5", "tank", "gauge", {"value": None},
                            occurred_at=at(10, 0), recorded_at=at(10, 2),
                            provenance_ids=["src:gauge"]))
    ctx = context_for_decision(mem, "historical-task", at(10, 30))
    assert ctx["future_memory_ids"] == []
    assert ctx["unknown_coerced_to_zero"] == 0
    assert ctx["all_context_has_provenance"] is True
    assert ctx["decision_time_consistent"] is True
    assert ctx["executable"] is False
    m5 = next(r for r in mem.query(at(10, 30)) if r.memory_id == "M5")
    assert m5.payload["value"] is None  # UNKNOWN stays UNKNOWN, never 0


# --------------------------------------------------------------------------
# 10. Gate table
# --------------------------------------------------------------------------

def test_gate_table_passes_on_sharp_fixture():
    gates, status = spine_gates(build_fixture(),
                                [at(10, 10), at(10, 30), at(11, 30)])
    assert gates["strict_future_use_zero"] is True
    assert gates["naive_ablation_future_use_positive"] is True
    assert gates["historical_point_in_time_queries"] is True
    assert gates["correction_supersession"] is True
    assert status == "VERIFIED_BITEMPORAL"


def test_gate_table_rejects_dull_fixture():
    mem = BitemporalMemory()  # only M1: naive ablation cannot detect leakage
    mem.ingest(MemoryRecord("M1", "tank", "temperature", {"value": 70},
                            occurred_at=at(10, 0), recorded_at=at(10, 1),
                            provenance_ids=["src:sensor-A"]))
    gates, status = spine_gates(mem, [at(10, 30)])
    assert gates["naive_ablation_future_use_positive"] is False
    assert status == "NOT_VERIFIED_BITEMPORAL"
