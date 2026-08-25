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

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["episode_ids"] = list(self.episode_ids)
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


def mandatory_memory_read(con, query: MemoryQuery) -> MemoryReadReceipt:
    """Successful empty SELECT counts. Futures table is never queried."""
    decision_time = float(query.as_of)
    recorded_at = time.time()
    receipt_id = _receipt_id(query.purpose, decision_time)
    query_dict = {
        "purpose": query.purpose,
        "as_of": decision_time,
        "event_type": query.event_type,
        "limit": query.limit,
        "table": "episodes",
        "forbidden_tables": sorted(FORBIDDEN_EVIDENCE_TABLES),
    }
    limit = max(0, int(query.limit))
    try:
        sql = """
            SELECT episode_id, created_at, event_type
            FROM episodes
            WHERE created_at <= ?
        """
        params: list[Any] = [decision_time]
        if query.event_type:
            sql += " AND event_type = ?"
            params.append(query.event_type)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with DB_LOCK:
            rows = list(con.execute(sql, params).fetchall())
        future_use = audit_future_use(rows, decision_time)
        created_values = [float(row[1]) for row in rows]
        occurred_at = max(created_values) if created_values else None
        created_at = min(created_values) if created_values else None
        if occurred_at is not None and occurred_at > decision_time:
            future_use += 1
        if created_at is not None and created_at > decision_time:
            future_use += 1
        ok = future_use == 0
        receipt = MemoryReadReceipt(
            receipt_id=receipt_id,
            purpose=query.purpose,
            decision_time=decision_time,
            recorded_at=recorded_at,
            occurred_at=occurred_at,
            created_at=created_at,
            rows_returned=len(rows),
            future_use_count=future_use,
            ok=ok,
            error=None if ok else "FUTURE_EPISODIC_EVIDENCE",
            query=query_dict,
            episode_ids=tuple(str(row[0]) for row in rows),
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
    return bundle
