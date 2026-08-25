"""Mandatory Memory Read gate.

A decision may proceed only after at least one successful episodic SELECT
whose timestamps are not in the future relative to decision_time.
Empty result sets count. The futures table is never episodic evidence.
Failed receipts are not persisted (CHECK future_use_count=0).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from ofn.organism.persistence.db import DB_LOCK

FORBIDDEN_EVIDENCE_TABLES = frozenset({"futures"})


class MemoryUnavailable(RuntimeError):
    """Memory cannot be read; fail closed."""


class MemoryGateClosed(RuntimeError):
    """Decision refused because the memory gate did not pass."""


@dataclass(frozen=True)
class MemoryQuery:
    purpose: str
    as_of: float
    event_type: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class MemoryReadReceipt:
    receipt_id: str
    purpose: str
    decision_time: float
    recorded_at: float
    occurred_at: float | None
    created_at: float | None
    rows_returned: int
    future_use_count: int
    ok: bool
    error: str | None
    query: dict[str, Any]
    episode_ids: tuple[str, ...] = ()
    event_ids: tuple[str, ...] = ()
    bitemporal_applied: bool = True

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["episode_ids"] = list(self.episode_ids)
        payload["event_ids"] = list(self.event_ids)
        return payload


@dataclass
class DecisionEvidenceBundle:
    decision_time: float
    purpose: str
    receipts: list[MemoryReadReceipt] = field(default_factory=list)

    @property
    def memory_reads_per_cycle(self) -> int:
        return len(self.receipts)

    @property
    def memory_future_use_total(self) -> int:
        return sum(item.future_use_count for item in self.receipts)

    def ok(self) -> bool:
        return (
            self.memory_reads_per_cycle >= 1
            and self.memory_future_use_total == 0
            and all(item.ok for item in self.receipts)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_time": self.decision_time,
            "purpose": self.purpose,
            "memory_reads_per_cycle": self.memory_reads_per_cycle,
            "memory_future_use_total": self.memory_future_use_total,
            "decision_without_memory_receipt_total": 0 if self.ok() else 1,
            "executable_total": 0,
            "ok": self.ok(),
            "receipts": [item.as_dict() for item in self.receipts],
        }


def _receipt_id(purpose: str, decision_time: float) -> str:
    material = f"{purpose}:{decision_time}:{time.time_ns()}".encode()
    return hashlib.sha256(material).hexdigest()[:32]


def _is_fake_id(episode_id: str) -> bool:
    if not episode_id or not isinstance(episode_id, str):
        return True
    lowered = episode_id.lower()
    return lowered.startswith("future:") or lowered.startswith("fake:") or lowered == "null"


def audit_future_use(
    rows: list[tuple[Any, ...]],
    decision_time: float,
) -> int:
    """Count evidence that is from the future or is a fake/future id.

    rows: (episode_id, created_at, event_type)
    """
    count = 0
    for episode_id, created_at, _event_type in rows:
        if _is_fake_id(str(episode_id) if episode_id is not None else ""):
            count += 1
            continue
        try:
            stamp = float(created_at)
        except (TypeError, ValueError):
            count += 1
            continue
        if stamp > decision_time:
            count += 1
    return count


def _persist_ok_receipt(con, receipt: MemoryReadReceipt) -> None:
    if not receipt.ok or receipt.future_use_count != 0:
        return
    with DB_LOCK:
        con.execute(
            """
            INSERT OR IGNORE INTO memory_read_receipts(
                receipt_id, purpose, decision_time, recorded_at,
                occurred_at, created_at, rows_returned, future_use_count,
                ok, error, query_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                receipt.receipt_id,
                receipt.purpose,
                receipt.decision_time,
                receipt.recorded_at,
                receipt.occurred_at,
                receipt.created_at,
                receipt.rows_returned,
                receipt.future_use_count,
                1 if receipt.ok else 0,
                receipt.error,
                json.dumps(receipt.query, sort_keys=True),
            ),
        )


def unavailable_payload(error: str) -> dict[str, Any]:
    return {
        "memory_status": "UNAVAILABLE",
        "confidence": "reduced",
        "external_action": "blocked",
        "executable": False,
        "error": error,
    }


def persist_evidence_bundle(con, bundle: DecisionEvidenceBundle) -> None:
    if not bundle.ok():
        return
    now = time.time()
    with DB_LOCK:
        for receipt in bundle.receipts:
            evidence_id = hashlib.sha256(
                f"{bundle.purpose}:{receipt.receipt_id}:{now}".encode()
            ).hexdigest()[:32]
            con.execute(
                """
                INSERT OR IGNORE INTO decision_evidence(
                    evidence_id, purpose, decision_time, receipt_id,
                    event_ids_json, episode_ids_json, created_at, executable
                ) VALUES (?,?,?,?,?,?,?,0)
                """,
                (
                    evidence_id,
                    bundle.purpose,
                    bundle.decision_time,
                    receipt.receipt_id,
                    json.dumps(list(receipt.event_ids)),
                    json.dumps(list(receipt.episode_ids)),
                    now,
                ),
            )


def mandatory_memory_read(con, query: MemoryQuery) -> MemoryReadReceipt:
    """Bitemporal SELECT on episodes+events. Empty result counts. Futures never queried."""
    decision_time = float(query.as_of)
    recorded_at = time.time()
    receipt_id = _receipt_id(query.purpose, decision_time)
    query_dict = {
        "purpose": query.purpose,
        "as_of": decision_time,
        "event_type": query.event_type,
        "limit": query.limit,
        "tables": ["episodes", "events"],
        "bitemporal": "created_at<=as_of AND event.created_at<=as_of",
        "forbidden_tables": sorted(FORBIDDEN_EVIDENCE_TABLES),
    }
    limit = max(0, int(query.limit))
    try:
        episode_sql = """
            SELECT ep.episode_id, ep.created_at, ep.event_type,
                   ev.created_at, ev.event_id
            FROM episodes AS ep
            LEFT JOIN events AS ev ON ev.event_id = ep.source_event_id
            WHERE ep.created_at <= ?
              AND (ev.event_id IS NULL OR ev.created_at <= ?)
        """
        episode_params: list[Any] = [decision_time, decision_time]
        if query.event_type:
            episode_sql += " AND ep.event_type = ?"
            episode_params.append(query.event_type)
        episode_sql += " ORDER BY ep.created_at DESC LIMIT ?"
        episode_params.append(limit)
        event_sql = """
            SELECT event_id, created_at, event_type
            FROM events
            WHERE created_at <= ?
        """
        event_params: list[Any] = [decision_time]
        if query.event_type:
            event_sql += " AND event_type = ?"
            event_params.append(query.event_type)
        event_sql += " ORDER BY created_at DESC LIMIT ?"
        event_params.append(limit)
        with DB_LOCK:
            episode_rows = list(con.execute(episode_sql, episode_params).fetchall())
            event_rows = list(con.execute(event_sql, event_params).fetchall())
        episode_audit = [(row[0], row[1], row[2]) for row in episode_rows]
        future_use = audit_future_use(episode_audit, decision_time)
        for _event_id, created_at, _event_type in event_rows:
            try:
                if float(created_at) > decision_time:
                    future_use += 1
            except (TypeError, ValueError):
                future_use += 1
        for row in episode_rows:
            event_created = row[3]
            if event_created is not None:
                try:
                    if float(event_created) > decision_time:
                        future_use += 1
                except (TypeError, ValueError):
                    future_use += 1
        stamps = [float(row[1]) for row in episode_rows] + [
            float(row[1]) for row in event_rows
        ]
        occurred_at = max(stamps) if stamps else None
        created_at = min(stamps) if stamps else None
        if occurred_at is not None and occurred_at > decision_time:
            future_use += 1
        if created_at is not None and created_at > decision_time:
            future_use += 1
        ok = future_use == 0
        episode_ids = tuple(str(row[0]) for row in episode_rows)
        event_ids = tuple(str(row[0]) for row in event_rows)
        receipt = MemoryReadReceipt(
            receipt_id=receipt_id,
            purpose=query.purpose,
            decision_time=decision_time,
            recorded_at=recorded_at,
            occurred_at=occurred_at,
            created_at=created_at,
            rows_returned=len(episode_rows) + len(event_rows),
            future_use_count=future_use,
            ok=ok,
            error=None if ok else "FUTURE_EPISODIC_EVIDENCE",
            query=query_dict,
            episode_ids=episode_ids,
            event_ids=event_ids,
            bitemporal_applied=True,
        )
        if ok:
            _persist_ok_receipt(con, receipt)
        return receipt
    except MemoryUnavailable:
        raise
    except Exception as exc:
        return MemoryReadReceipt(
            receipt_id=receipt_id,
            purpose=query.purpose,
            decision_time=decision_time,
            recorded_at=recorded_at,
            occurred_at=None,
            created_at=None,
            rows_returned=0,
            future_use_count=0,
            ok=False,
            error=f"MEMORY_UNAVAILABLE:{type(exc).__name__}:{exc}",
            query=query_dict,
            episode_ids=(),
            event_ids=(),
            bitemporal_applied=False,
        )


def require_memory_gate(con, purpose: str, decision_time: float | None = None) -> DecisionEvidenceBundle:
    as_of = time.time() if decision_time is None else float(decision_time)
    receipt = mandatory_memory_read(
        con,
        MemoryQuery(purpose=purpose, as_of=as_of, limit=20),
    )
    bundle = DecisionEvidenceBundle(
        decision_time=as_of,
        purpose=purpose,
        receipts=[receipt],
    )
    if not receipt.ok:
        raise MemoryUnavailable(receipt.error or "MEMORY_UNAVAILABLE")
    if not bundle.ok():
        raise MemoryGateClosed(
            f"memory_reads={bundle.memory_reads_per_cycle} "
            f"future_use={bundle.memory_future_use_total}"
        )
    persist_evidence_bundle(con, bundle)
    return bundle
