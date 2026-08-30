"""Bi-temporal fact store. Facts are superseded, never overwritten.

Two independent time axes, because they answer different questions:

    valid_from / valid_to   when the fact was true *in the world*
    observed_at             when we were *told* it

Keeping both is what lets the node answer "what did we believe last Tuesday,
and were we right?" — which is the question that matters when a partner says
a number changed and nobody can remember when.

The write policy is supersede-not-delete. A corrected fact closes the old row
(`valid_to` set) and inserts a new one. Nothing is ever removed, so a wrong
decision made on an old fact remains explicable rather than mysterious.

The one exception is `forget()`, reserved for deletion requests and
compliance. It is deliberately separate, deliberately loud, and deliberately
not reachable from the normal correction path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Sequence

from ..kernel.domain import Confidence
from ..kernel.errors import FailClosedError
from ..kernel.tenancy import TenantScope
from .sqlite_base import Pool, apply_schema

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS facts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant      TEXT    NOT NULL,
        subject     TEXT    NOT NULL,
        predicate   TEXT    NOT NULL,
        value       TEXT    NOT NULL,
        confidence  TEXT    NOT NULL,
        source      TEXT    NOT NULL DEFAULT '',
        valid_from  TEXT    NOT NULL,
        valid_to    TEXT,
        observed_at TEXT    NOT NULL,
        superseded_by INTEGER,
        FOREIGN KEY (superseded_by) REFERENCES facts (id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS facts_lookup "
    "ON facts (tenant, subject, predicate, valid_to)",
    "CREATE INDEX IF NOT EXISTS facts_observed ON facts (tenant, observed_at)",
)


@dataclass(frozen=True)
class Fact:
    id: int
    tenant: str
    subject: str
    predicate: str
    value: object
    confidence: Confidence
    source: str
    valid_from: str
    valid_to: str | None
    observed_at: str
    superseded_by: int | None

    @property
    def active(self) -> bool:
        return self.valid_to is None

    @property
    def key(self) -> str:
        return f"{self.subject}.{self.predicate}"


class FactStore:
    """Tenant-scoped, bi-temporal, append-mostly."""

    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA)

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        """This thread's connection. See `Pool` for why it is per-thread."""
        return self._pool.conn

    # ── writing ───────────────────────────────────────────────────────────
    def assert_fact(
        self,
        scope: TenantScope,
        subject: str,
        predicate: str,
        value: object,
        confidence: Confidence,
        *,
        observed_at: str,
        valid_from: str | None = None,
        source: str = "",
    ) -> Fact:
        """Record a fact, superseding any active one with the same key.

        Supersession happens in the same transaction as the insert: a crash
        between the two would otherwise leave either two active rows for one
        key (ambiguous reads) or none (a fact that silently vanished).
        """
        if not subject or not predicate:
            raise FailClosedError("subject and predicate are required")
        tenant = scope.tenant.value
        vf = valid_from or observed_at
        payload = json.dumps(value, ensure_ascii=False)

        self._conn.execute("BEGIN IMMEDIATE")
        try:
            prior = self._conn.execute(
                "SELECT id FROM facts WHERE tenant = ? AND subject = ? "
                "AND predicate = ? AND valid_to IS NULL",
                (tenant, subject, predicate)).fetchall()
            cur = self._conn.execute(
                "INSERT INTO facts (tenant, subject, predicate, value, confidence,"
                " source, valid_from, valid_to, observed_at, superseded_by)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL)",
                (tenant, subject, predicate, payload, confidence.value,
                 source, vf, observed_at))
            new_id = int(cur.lastrowid)
            for row in prior:
                self._conn.execute(
                    "UPDATE facts SET valid_to = ?, superseded_by = ? WHERE id = ?",
                    (observed_at, new_id, row["id"]))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

        return Fact(new_id, tenant, subject, predicate, value, confidence,
                    source, vf, None, observed_at, None)

    def forget(self, scope: TenantScope, subject: str, predicate: str) -> int:
        """Hard-delete every version of a fact. Compliance path only.

        Separate from supersession on purpose: erasure destroys the audit
        trail, so it must be an explicit act with its own name, not something
        a correction can turn into by accident.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "DELETE FROM facts WHERE tenant = ? AND subject = ? AND predicate = ?",
                (scope.tenant.value, subject, predicate))
            self._conn.execute("COMMIT")
            return cur.rowcount
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # ── reading ───────────────────────────────────────────────────────────
    def current(self, scope: TenantScope, subject: str, predicate: str) -> Fact | None:
        """The fact as believed right now."""
        row = self._conn.execute(
            "SELECT * FROM facts WHERE tenant = ? AND subject = ? AND predicate = ?"
            " AND valid_to IS NULL ORDER BY id DESC LIMIT 1",
            (scope.tenant.value, subject, predicate)).fetchone()
        return self._to_fact(row) if row else None

    def as_of(self, scope: TenantScope, subject: str, predicate: str,
              when: str) -> Fact | None:
        """What we believed at a past moment — the bi-temporal question.

        Selects on `observed_at`, not `valid_from`: this answers "what did the
        system know then", which is what you need to judge a decision it made
        then. Asking what was *true* then is a different query.
        """
        row = self._conn.execute(
            "SELECT * FROM facts WHERE tenant = ? AND subject = ? AND predicate = ?"
            " AND observed_at <= ? ORDER BY observed_at DESC, id DESC LIMIT 1",
            (scope.tenant.value, subject, predicate, when)).fetchone()
        return self._to_fact(row) if row else None

    def history(self, scope: TenantScope, subject: str,
                predicate: str) -> Sequence[Fact]:
        rows = self._conn.execute(
            "SELECT * FROM facts WHERE tenant = ? AND subject = ? AND predicate = ?"
            " ORDER BY id ASC",
            (scope.tenant.value, subject, predicate)).fetchall()
        return [self._to_fact(r) for r in rows]

    def all_active(self, scope: TenantScope) -> Sequence[Fact]:
        rows = self._conn.execute(
            "SELECT * FROM facts WHERE tenant = ? AND valid_to IS NULL"
            " ORDER BY subject, predicate",
            (scope.tenant.value,)).fetchall()
        return [self._to_fact(r) for r in rows]

    def evidence(self, scope: TenantScope,
                 keys: Sequence[str]) -> Mapping[str, Confidence]:
        """Confidence map shaped for `Action.evidence`.

        Keys are `subject.predicate`. Absent facts are simply missing from the
        result — the gate treats absence and weakness differently, so this
        must not paper over the difference with a default.
        """
        out: dict[str, Confidence] = {}
        for key in keys:
            subject, _, predicate = key.partition(".")
            if not predicate:
                continue
            fact = self.current(scope, subject, predicate)
            if fact is not None:
                out[key] = fact.confidence
        return out

    @staticmethod
    def _to_fact(row) -> Fact:
        return Fact(
            id=row["id"], tenant=row["tenant"], subject=row["subject"],
            predicate=row["predicate"], value=json.loads(row["value"]),
            confidence=Confidence(row["confidence"]), source=row["source"],
            valid_from=row["valid_from"], valid_to=row["valid_to"],
            observed_at=row["observed_at"], superseded_by=row["superseded_by"],
        )
