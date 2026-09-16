"""Subscribers, the money they spend, and how much of the audience is owned.

One migration, three tables, and they arrive together on purpose.

`revenue_events` on its own answers "forty dollars came in". With a
subscriber behind it, the same row answers "this channel brings people worth
twice what that one does" — and that is the difference between a number and a
decision. Splitting them across two migrations would leave the first months
of rows without an owner, permanently, which is the same hole
`draft_subjects` exists to avoid one layer up.

All three can be created before there is a single subscriber, and that is the
reason to create them now. The month a business starts is the month churn is
decided, and a table added afterwards cannot describe it.

Money is `INTEGER` minor units. Never `REAL`: `0.1 + 0.2 != 0.3`, and a
year's total is where that finally shows.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from ..kernel.audience import Ownership, RevenueKind, Snapshot, Subscriber
from .sqlite_base import Pool, apply_schema

STATUSES = ("active", "lapsed", "blocked")

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS subscribers (
        sub_id         TEXT    PRIMARY KEY,
        tenant_id      TEXT    NOT NULL,
        first_seen_at  INTEGER NOT NULL,
        -- Where they came from. NOT NULL with a placeholder rather than
        -- nullable: "unknown" is a real answer that can be counted, and a
        -- NULL is one that quietly drops out of every GROUP BY.
        channel_source TEXT    NOT NULL DEFAULT 'unknown',
        status         TEXT    NOT NULL DEFAULT 'active'
                         CHECK (status IN ('active', 'lapsed', 'blocked')),
        last_contact_at   INTEGER,
        -- Stamped once, by the first purchase. Never moved: it is what the
        -- first-window conversion compares against.
        first_purchase_at INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS revenue_events (
        event_id     TEXT    PRIMARY KEY,
        tenant_id    TEXT    NOT NULL,
        occurred_at  INTEGER NOT NULL,
        kind         TEXT    NOT NULL
                       CHECK (kind IN ('subscription', 'ppv', 'tip', 'custom')),
        -- Minor units, integer. A REAL column here is a rounding error with
        -- a year to accumulate in.
        amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
        currency     TEXT    NOT NULL DEFAULT 'AUD',
        -- Both nullable and both meaningful: a tip belongs to no post, and
        -- money can arrive before anybody knows who sent it.
        sub_id       TEXT    REFERENCES subscribers (sub_id),
        post_id      TEXT,
        source_note  TEXT    NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audience_snapshot (
        taken_at  INTEGER NOT NULL,
        tenant_id TEXT    NOT NULL,
        channel   TEXT    NOT NULL,
        -- owned survives losing a platform; rented does not. Restricted by
        -- CHECK so a fourth value cannot appear and quietly count as owned.
        kind      TEXT    NOT NULL
                    CHECK (kind IN ('owned', 'semi_owned', 'rented')),
        count     INTEGER NOT NULL CHECK (count >= 0),
        PRIMARY KEY (taken_at, tenant_id, channel, kind)
    )
    """,
    "CREATE INDEX IF NOT EXISTS subs_tenant ON subscribers (tenant_id, status)",
    "CREATE INDEX IF NOT EXISTS subs_channel "
    "ON subscribers (tenant_id, channel_source)",
    "CREATE INDEX IF NOT EXISTS revenue_tenant "
    "ON revenue_events (tenant_id, occurred_at)",
    "CREATE INDEX IF NOT EXISTS revenue_sub ON revenue_events (sub_id)",
    "CREATE INDEX IF NOT EXISTS snapshot_tenant "
    "ON audience_snapshot (tenant_id, taken_at)",
)


class AudienceError(Exception):
    """A record could not be written, with a reason a person can act on."""


class AudienceStore:
    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA)

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        """This thread's connection. See `Pool` for why it is per-thread."""
        return self._pool.conn

    # ── subscribers ───────────────────────────────────────────────────────
    def add_subscriber(self, tenant: str, sub_id: str, *, first_seen_at: int,
                       channel_source: str = "unknown") -> Subscriber:
        if not sub_id.strip():
            raise AudienceError("شناسهٔ مشترک خالی است")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO subscribers (sub_id, tenant_id, first_seen_at, "
                "channel_source) VALUES (?, ?, ?, ?)",
                (sub_id, tenant, first_seen_at, channel_source or "unknown"))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise AudienceError(f"مشترکی با شناسهٔ «{sub_id}» از قبل هست")
        return self.subscriber(sub_id)

    def subscriber(self, sub_id: str) -> Subscriber:
        row = self._conn.execute(
            "SELECT s.sub_id, s.first_seen_at, s.channel_source, s.status, "
            "s.last_contact_at, s.first_purchase_at, "
            "COALESCE((SELECT SUM(amount_minor) FROM revenue_events r "
            "          WHERE r.sub_id = s.sub_id), 0) "
            "FROM subscribers s WHERE s.sub_id = ?", (sub_id,)).fetchone()
        if row is None:
            raise AudienceError(f"مشترکی با شناسهٔ «{sub_id}» پیدا نشد")
        return _to_subscriber(row)

    def subscribers(self, tenant: str) -> list[Subscriber]:
        """Lifetime value is summed from the events rather than stored.

        A stored total is a second copy of a fact, and the two disagree the
        first time a row is corrected. `recompute` in the products store
        exists because of the same trade; here the sum is cheap enough that
        the second copy is simply not made.
        """
        return [_to_subscriber(r) for r in self._conn.execute(
            "SELECT s.sub_id, s.first_seen_at, s.channel_source, s.status, "
            "s.last_contact_at, s.first_purchase_at, "
            "COALESCE((SELECT SUM(amount_minor) FROM revenue_events r "
            "          WHERE r.sub_id = s.sub_id), 0) "
            "FROM subscribers s WHERE s.tenant_id = ? "
            "ORDER BY s.first_seen_at", (tenant,))]

    def mark_contacted(self, sub_id: str, *, at: int) -> None:
        """Only ever forward. A message sent today does not make an older
        one more recent, and moving the stamp backwards would make somebody
        reappear on the quiet list who is not quiet."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE subscribers SET last_contact_at = ? WHERE sub_id = ? "
                "AND (last_contact_at IS NULL OR last_contact_at < ?)",
                (at, sub_id, at))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def set_status(self, sub_id: str, status: str) -> None:
        if status not in STATUSES:
            raise AudienceError(f"وضعیت نامعتبر: {status!r}")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute("UPDATE subscribers SET status = ? "
                               "WHERE sub_id = ?", (status, sub_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # ── money ─────────────────────────────────────────────────────────────
    def record_revenue(self, tenant: str, event_id: str, *, kind: str,
                       amount_minor: int, occurred_at: int,
                       currency: str = "AUD", sub_id: str | None = None,
                       post_id: str | None = None,
                       source_note: str = "") -> None:
        """One payment. Idempotent by `event_id`.

        Stamping `first_purchase_at` happens here and only here, and only if
        it is empty — the first purchase is a fact about a moment, and a
        later correction to an old row must not rewrite it.
        """
        if isinstance(amount_minor, bool) or not isinstance(amount_minor, int):
            raise AudienceError(f"مبلغ باید عدد صحیح سنت باشد: {amount_minor!r}")
        if amount_minor < 0:
            raise AudienceError("مبلغ منفی نمی‌شود")
        if kind not in {k.value for k in RevenueKind}:
            raise AudienceError(f"نوع درآمد نامعتبر: {kind!r}")
        if sub_id is not None:
            self.subscriber(sub_id)          # refuse an orphan loudly

        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO revenue_events (event_id, tenant_id, occurred_at, "
                "kind, amount_minor, currency, sub_id, post_id, source_note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event_id, tenant, occurred_at, kind, amount_minor, currency,
                 sub_id, post_id, source_note))
            if sub_id is not None:
                self._conn.execute(
                    "UPDATE subscribers SET first_purchase_at = ? "
                    "WHERE sub_id = ? AND first_purchase_at IS NULL",
                    (occurred_at, sub_id))
            self._conn.execute("COMMIT")
        except AudienceError:
            self._conn.execute("ROLLBACK")
            raise
        except Exception:
            self._conn.execute("ROLLBACK")
            raise AudienceError(f"رویداد «{event_id}» از قبل ثبت شده")

    def revenue_totals(self, tenant: str) -> Mapping[RevenueKind, int]:
        out = {kind: 0 for kind in RevenueKind}
        for kind, total in self._conn.execute(
                "SELECT kind, SUM(amount_minor) FROM revenue_events "
                "WHERE tenant_id = ? GROUP BY kind", (tenant,)):
            out[RevenueKind(kind)] = int(total or 0)
        return out

    # ── how much of it is hers ────────────────────────────────────────────
    def take_snapshot(self, tenant: str, *, taken_at: int,
                      counts: Iterable[tuple[str, str, int]]) -> None:
        """One reading of the whole audience, as (channel, kind, count).

        Written as a set rather than row by row, because a half-written
        snapshot has an ownership ratio and it is wrong.
        """
        rows = list(counts)
        for channel, kind, count in rows:
            if kind not in {o.value for o in Ownership}:
                raise AudienceError(f"نوع مالکیت نامعتبر: {kind!r}")
            if count < 0:
                raise AudienceError("تعداد منفی نمی‌شود")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            for channel, kind, count in rows:
                self._conn.execute(
                    "INSERT INTO audience_snapshot (taken_at, tenant_id, "
                    "channel, kind, count) VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(taken_at, tenant_id, channel, kind) "
                    "DO UPDATE SET count = excluded.count",
                    (taken_at, tenant, channel, kind, count))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def snapshots(self, tenant: str, *, since: int = 0) -> list[Snapshot]:
        return [Snapshot(int(r[0]), str(r[1]), Ownership(r[2]), int(r[3]))
                for r in self._conn.execute(
                    "SELECT taken_at, channel, kind, count FROM "
                    "audience_snapshot WHERE tenant_id = ? AND taken_at >= ? "
                    "ORDER BY taken_at", (tenant, since))]

    def latest_snapshot(self, tenant: str) -> list[Snapshot]:
        row = self._conn.execute(
            "SELECT MAX(taken_at) FROM audience_snapshot WHERE tenant_id = ?",
            (tenant,)).fetchone()
        if row is None or row[0] is None:
            return []
        return [s for s in self.snapshots(tenant) if s.taken_at == int(row[0])]


def _to_subscriber(row: Sequence) -> Subscriber:
    return Subscriber(
        sub_id=row[0], first_seen_at=int(row[1]), channel_source=row[2],
        status=row[3],
        last_contact_at=None if row[4] is None else int(row[4]),
        first_purchase_at=None if row[5] is None else int(row[5]),
        lifetime_minor=int(row[6] or 0))
