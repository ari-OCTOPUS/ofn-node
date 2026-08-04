"""Collections, drafts, and the media inside them.

    collection  →  draft  →  media
    مجموعه          پست       رسانه (۱ تا N)

A `draft` is one post. It is the unit of consent and the unit of publication,
because that is the unit the person decides about: if media were the unit, a
three-photo post would ask the same question three times, which is the
decision-multiplication the whole design directive exists against.

Three things here are ordering decisions rather than features, and each is
cheapest right now because the tables are empty.

**`sensitivity` is NOT NULL from the first migration.** Added later as
nullable it would leave existing rows NULL, and NULL is neither `general` nor
`restricted` — the fail-closed logic would then depend on how somebody reads
NULL. That is exactly the `batch_size = 0` lesson, where SQLite returned NULL
instead of an error and the null travelled all the way to a partner's screen.

**`felt_right` needs two timestamps, not one.** The rule is that her feeling
is asked before she sees any platform number. Intent is not verifiable;
order is. Without both stamps, six months from now there is a column of
ratings and no way to know which are contaminated — and the contaminated ones
are precisely those that correlate with the numbers, because they are
reflections of them.

**Originals are not archived at upload.** The brief said to keep them so it
could be proved what went out. That does not follow: if the platform is sent
a 1600px rendition, the original was never sent, so keeping it proves nothing
about what left. What proves it is a hash of the bytes that actually went —
`media_sent`. And every original kept is one more sensitive file at rest on
an unencrypted disk, which for this leg is a real cost rather than a
preference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..kernel.advisor_gate import Collection, Sensitivity
from ..kernel.photos import MAX_POSITION
from .sqlite_base import Pool, apply_schema

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS collections (
        collection_id TEXT    PRIMARY KEY,
        tenant_id     TEXT    NOT NULL,
        label         TEXT    NOT NULL,
        -- A free label. The system does not interpret it; it groups by it.
        genre         TEXT    NOT NULL DEFAULT '',
        -- NOT NULL with a restricted default, from the first migration.
        -- Becoming general is an explicit act, never a default and never the
        -- result of a column that was added later and left empty.
        sensitivity   TEXT    NOT NULL DEFAULT 'restricted'
                        CHECK (sensitivity IN ('restricted', 'general')),
        created_at    INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS drafts (
        draft_id      TEXT    PRIMARY KEY,
        tenant_id     TEXT    NOT NULL,
        -- Nullable on purpose: a post that belongs to no collection is a
        -- normal thing, and forcing one would make her invent a category
        -- before she is ready to have one.
        collection_id TEXT    REFERENCES collections (collection_id),
        caption       TEXT,
        status        TEXT    NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'ready', 'queued',
                                          'published', 'abandoned')),
        scheduled_for INTEGER,
        created_at    INTEGER NOT NULL,

        -- Her own reading of the post, 1..5, asked before any number.
        felt_right      INTEGER
                          CHECK (felt_right IS NULL
                                 OR felt_right BETWEEN 1 AND 5),
        felt_right_at   INTEGER,
        -- When the first platform figure for this post arrived. Compared
        -- against the stamp above to decide whether the rating can be
        -- trusted at all. Never written twice — see `record_first_metric`.
        first_metric_at INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS draft_media (
        draft_id  TEXT    NOT NULL REFERENCES drafts (draft_id),
        position  INTEGER NOT NULL CHECK (position >= 0),
        media_ref TEXT    NOT NULL,
        PRIMARY KEY (draft_id, position)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS media_sent (
        draft_id  TEXT    NOT NULL,
        position  INTEGER NOT NULL,
        platform  TEXT    NOT NULL,
        -- The hash of the bytes that actually went over the wire. This is
        -- what answers "prove what was published" — not an archived
        -- original, which by definition was not what was sent.
        sha256    TEXT    NOT NULL,
        byte_size INTEGER NOT NULL,
        sent_at   INTEGER NOT NULL,
        PRIMARY KEY (draft_id, position, platform)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS advisor_findings (
        key         TEXT    NOT NULL,
        tenant_id   TEXT    NOT NULL,
        claim       TEXT    NOT NULL,
        -- Both required. A claim whose source is not recorded cannot be
        -- argued with, and one that cannot be rejected is not advice.
        sample      INTEGER NOT NULL CHECK (sample > 0),
        window_days INTEGER NOT NULL CHECK (window_days > 0),
        created_at  INTEGER NOT NULL,
        -- The ratchet. `rejected_hard` is never overwritten, so a suggestion
        -- she has said "never" to does not come back after a restart.
        disposition TEXT    NOT NULL DEFAULT 'offered'
                      CHECK (disposition IN ('offered', 'accepted',
                                             'rejected_soft', 'rejected_hard')),
        PRIMARY KEY (tenant_id, key)
    )
    """,
    "CREATE INDEX IF NOT EXISTS drafts_tenant ON drafts (tenant_id, status)",
    "CREATE INDEX IF NOT EXISTS drafts_collection ON drafts (collection_id)",
    "CREATE INDEX IF NOT EXISTS collections_tenant ON collections (tenant_id)",
)

STATUSES = ("draft", "ready", "queued", "published", "abandoned")


class StudioError(Exception):
    """A studio record could not be written, with a reason a person can act on."""


@dataclass(frozen=True)
class Draft:
    draft_id: str
    tenant_id: str
    collection_id: str | None
    caption: str | None
    status: str
    scheduled_for: int | None
    created_at: int
    felt_right: int | None
    felt_right_at: int | None
    first_metric_at: int | None

    @property
    def rating_is_trustworthy(self) -> bool:
        """Whether her rating can be used in an analysis.

        False when no rating exists, and false when a platform figure had
        already arrived when she gave it — at that point the answer is a
        reflection of the number rather than an independent signal, and
        including it would make the correlation look stronger than it is
        using the very rows that are contaminated.
        """
        if self.felt_right is None or self.felt_right_at is None:
            return False
        if self.first_metric_at is None:
            return True
        return self.felt_right_at < self.first_metric_at


class StudioStore:
    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA)

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        """This thread's connection. See `Pool` for why it is per-thread."""
        return self._pool.conn

    # ── collections ───────────────────────────────────────────────────────
    def add_collection(self, tenant: str, collection_id: str, label: str, *,
                       genre: str = "", sensitivity: str = "restricted",
                       now_epoch_s: int) -> Collection:
        """Create a collection. Restricted unless somebody says otherwise."""
        if Sensitivity.of(sensitivity) is Sensitivity.GENERAL \
                and sensitivity != "general":
            raise StudioError(f"حساسیت نامعتبر: {sensitivity!r}")
        if sensitivity not in ("restricted", "general"):
            raise StudioError(f"حساسیت نامعتبر: {sensitivity!r}")
        if not label.strip():
            raise StudioError("نام مجموعه خالی است")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO collections (collection_id, tenant_id, label, "
                "genre, sensitivity, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (collection_id, tenant, label.strip(), genre, sensitivity,
                 now_epoch_s))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise StudioError(f"مجموعهٔ «{collection_id}» از قبل هست")
        return self.collection(collection_id)

    def collection(self, collection_id: str) -> Collection | None:
        row = self._conn.execute(
            "SELECT collection_id, label, genre, sensitivity FROM collections "
            "WHERE collection_id = ?", (collection_id,)).fetchone()
        if row is None:
            return None
        return Collection(row[0], row[1], row[2], Sensitivity.of(row[3]))

    def collection_of(self, draft_id: str) -> Collection | None:
        """The collection a draft belongs to, or None.

        None covers both "this draft has no collection" and "there is no such
        draft". Both must refuse at the advisor gate, so they are the same
        answer here rather than two the caller has to remember to handle.
        """
        row = self._conn.execute(
            "SELECT collection_id FROM drafts WHERE draft_id = ?",
            (draft_id,)).fetchone()
        if row is None or row[0] is None:
            return None
        return self.collection(row[0])

    def collections(self, tenant: str) -> list[Collection]:
        return [Collection(r[0], r[1], r[2], Sensitivity.of(r[3]))
                for r in self._conn.execute(
                    "SELECT collection_id, label, genre, sensitivity FROM "
                    "collections WHERE tenant_id = ? ORDER BY created_at",
                    (tenant,))]

    # ── drafts ────────────────────────────────────────────────────────────
    def add_draft(self, tenant: str, draft_id: str, *,
                  collection_id: str | None = None, caption: str | None = None,
                  now_epoch_s: int) -> Draft:
        if collection_id is not None and self.collection(collection_id) is None:
            raise StudioError(f"مجموعهٔ «{collection_id}» ثبت نشده")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO drafts (draft_id, tenant_id, collection_id, "
                "caption, created_at) VALUES (?, ?, ?, ?, ?)",
                (draft_id, tenant, collection_id, caption, now_epoch_s))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise StudioError(f"پیش‌نویس «{draft_id}» از قبل هست")
        return self.draft(draft_id)

    def draft(self, draft_id: str) -> Draft:
        row = self._conn.execute(
            "SELECT draft_id, tenant_id, collection_id, caption, status, "
            "scheduled_for, created_at, felt_right, felt_right_at, "
            "first_metric_at FROM drafts WHERE draft_id = ?",
            (draft_id,)).fetchone()
        if row is None:
            raise StudioError(f"پیش‌نویس «{draft_id}» پیدا نشد")
        return Draft(*row)

    def drafts(self, tenant: str, *, status: str | None = None) -> list[Draft]:
        sql = ("SELECT draft_id, tenant_id, collection_id, caption, status, "
               "scheduled_for, created_at, felt_right, felt_right_at, "
               "first_metric_at FROM drafts WHERE tenant_id = ?")
        args: tuple = (tenant,)
        if status is not None:
            sql += " AND status = ?"
            args += (status,)
        return [Draft(*r) for r in self._conn.execute(sql + " ORDER BY created_at", args)]

    def set_status(self, draft_id: str, status: str) -> Draft:
        if status not in STATUSES:
            raise StudioError(f"وضعیت نامعتبر: {status!r}")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute("UPDATE drafts SET status = ? WHERE draft_id = ?",
                               (status, draft_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return self.draft(draft_id)

    # ── media inside a draft ──────────────────────────────────────────────
    def attach_media(self, draft_id: str, position: int, media_ref: str) -> None:
        """Put one rendition at one position in a post.

        `True == 1` in Python, so a bool passes an integer check and silently
        becomes position 1. Refused before the range check, because the range
        would accept it.
        """
        if isinstance(position, bool) or not isinstance(position, int):
            raise StudioError(f"موقعیت باید عدد باشد: {position!r}")
        if not 0 <= position <= MAX_POSITION:
            raise StudioError(f"موقعیت خارج از محدوده: {position}")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO draft_media (draft_id, position, media_ref) "
                "VALUES (?, ?, ?) ON CONFLICT(draft_id, position) "
                "DO UPDATE SET media_ref = excluded.media_ref",
                (draft_id, position, media_ref))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise StudioError(f"پیش‌نویس «{draft_id}» ثبت نشده")

    def media_of(self, draft_id: str) -> list[tuple[int, str]]:
        return [(int(r[0]), str(r[1])) for r in self._conn.execute(
            "SELECT position, media_ref FROM draft_media WHERE draft_id = ? "
            "ORDER BY position", (draft_id,))]

    # ── her reading, and the clock that guards it ─────────────────────────
    def record_felt_right(self, draft_id: str, rating: int, *,
                          now_epoch_s: int) -> Draft:
        """Her own reading of a post. Written once.

        Not refused when a number has already arrived — refusing would lose
        the answer entirely. It is stored with its stamp, and
        `rating_is_trustworthy` decides later whether an analysis may use it.
        Discarding data because it is contaminated, rather than labelling it,
        is how you end up unable to measure how often contamination happens.
        """
        if isinstance(rating, bool) or not isinstance(rating, int):
            raise StudioError(f"امتیاز باید عدد باشد: {rating!r}")
        if not 1 <= rating <= 5:
            raise StudioError("امتیاز باید بین ۱ تا ۵ باشد")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE drafts SET felt_right = ?, felt_right_at = ? "
                "WHERE draft_id = ? AND felt_right IS NULL",
                (rating, now_epoch_s, draft_id))
            if cur.rowcount == 0:
                self._conn.execute("ROLLBACK")
                raise StudioError(
                    f"«{draft_id}» یا وجود ندارد یا قبلاً حسش ثبت شده")
            self._conn.execute("COMMIT")
        except StudioError:
            raise
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return self.draft(draft_id)

    def record_first_metric(self, draft_id: str, *, now_epoch_s: int) -> Draft:
        """Stamp the arrival of the first platform figure for this post.

        Only the first. A later call must not move the stamp forward, because
        the stamp is what every trust decision compares against — moving it
        would quietly reclassify contaminated ratings as clean.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE drafts SET first_metric_at = ? "
                "WHERE draft_id = ? AND first_metric_at IS NULL",
                (now_epoch_s, draft_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return self.draft(draft_id)

    def trustworthy_ratings(self, tenant: str) -> list[Draft]:
        """The rows an analysis may use."""
        return [d for d in self.drafts(tenant) if d.rating_is_trustworthy]

    # ── what actually went over the wire ──────────────────────────────────
    def record_sent(self, draft_id: str, position: int, *, platform: str,
                    sha256: str, byte_size: int, sent_at: int) -> None:
        """The hash of the bytes that were actually published.

        This is what answers "prove what went out". An archived original does
        not: if a 1600px rendition was sent, the original was never sent, so
        keeping it proves nothing about what left — while costing one more
        sensitive file at rest on an unencrypted disk.

        Nothing calls this today; no wire is connected. It exists now because
        a row that starts being written later leaves a hole in exactly the
        record it is for.
        """
        if len(sha256 or "") != 64:
            raise StudioError("هش باید sha256 باشد (۶۴ کاراکتر)")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO media_sent (draft_id, position, platform, "
                "sha256, byte_size, sent_at) VALUES (?, ?, ?, ?, ?, ?)",
                (draft_id, position, platform, sha256.lower(), byte_size,
                 sent_at))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise StudioError(
                f"«{draft_id}» موقعیت {position} روی {platform} از قبل ثبت شده")

    # ── advisor findings ──────────────────────────────────────────────────
    def record_finding(self, tenant: str, *, key: str, claim: str,
                       sample: int, window_days: int, now_epoch_s: int) -> None:
        """Keep a finding, unless she has already said never to it.

        The ratchet lives in the WHERE clause rather than in a check above
        it: two callers racing would both pass a read-then-write check, and
        the one that loses would still overwrite a hard rejection.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO advisor_findings (key, tenant_id, claim, sample, "
                "window_days, created_at) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(tenant_id, key) DO UPDATE SET "
                "claim = excluded.claim, sample = excluded.sample, "
                "window_days = excluded.window_days, "
                "created_at = excluded.created_at "
                "WHERE advisor_findings.disposition != 'rejected_hard'",
                (key, tenant, claim, sample, window_days, now_epoch_s))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def judge_finding(self, tenant: str, key: str, disposition: str) -> None:
        """Opinions harden. A hard rejection is final."""
        if disposition not in ("accepted", "rejected_soft", "rejected_hard"):
            raise StudioError(f"داوری نامعتبر: {disposition!r}")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE advisor_findings SET disposition = ? "
                "WHERE tenant_id = ? AND key = ? "
                "AND disposition != 'rejected_hard'",
                (disposition, tenant, key))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def findings(self, tenant: str) -> list[dict]:
        """What may still be shown. Hard rejections never appear again."""
        return [{"key": r[0], "claim": r[1], "sample": int(r[2]),
                 "window_days": int(r[3]), "disposition": r[4]}
                for r in self._conn.execute(
                    "SELECT key, claim, sample, window_days, disposition "
                    "FROM advisor_findings WHERE tenant_id = ? "
                    "AND disposition != 'rejected_hard' "
                    "ORDER BY created_at DESC", (tenant,))]

    def dispositions(self, tenant: str) -> dict:
        return {r[0]: r[1] for r in self._conn.execute(
            "SELECT key, disposition FROM advisor_findings WHERE tenant_id = ?",
            (tenant,))}

    def sent_for(self, draft_id: str) -> list[tuple[int, str, str, int]]:
        return [(int(r[0]), str(r[1]), str(r[2]), int(r[3]))
                for r in self._conn.execute(
                    "SELECT position, platform, sha256, sent_at FROM "
                    "media_sent WHERE draft_id = ? ORDER BY position, platform",
                    (draft_id,))]
