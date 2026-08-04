"""Who may appear in content, what they signed, and where they ended up.

Three tables, and the third is the one that cannot be added later.

`subjects` and `releases` describe agreement. They could be built any time —
if they were missing today, adding them next month would cost a migration and
nothing else.

`draft_subjects` is different. It records *who is in which draft*, and the
only moment that information exists is the moment somebody adds a person to a
draft. If it is not written down then, it is not recoverable from anything —
not from the image, not from the caption, not from the ledger. The day
somebody withdraws consent, the question is:

    everything already published that this person is in — which ones?

Without this table that question has no answer and never will. Every other
part of this leg can be redesigned later. This one has no second chance, which
is why it is built before the app that will use it.

`posts` lives here too, and only just enough of it: a published draft, its
platform, and the platform's own id for it. It is here rather than in the
studio store because `published_containing` has to join it against
`draft_subjects`, and a join across two SQLite files is either an ATTACH or a
loop in Python — both of which are ways to get a subtly wrong answer to the
one question that must not be answered wrongly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..kernel.consent import Release, Subject, parse_scope
from .sqlite_base import Pool, apply_schema

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id    TEXT    PRIMARY KEY,
        tenant_id     TEXT    NOT NULL,
        -- A label the person chose, not necessarily a legal name. Honouring
        -- somebody's decision does not require knowing who they are.
        display_label TEXT    NOT NULL,
        created_at    INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS releases (
        release_id      TEXT    PRIMARY KEY,
        subject_id      TEXT    NOT NULL REFERENCES subjects (subject_id),
        -- Platform ids, comma separated. Parsed by the kernel, never here.
        scope           TEXT    NOT NULL,
        signed_at       INTEGER NOT NULL,
        expires_at      INTEGER,
        -- Where the signed document is kept. It is NOT in this database: a
        -- database that holds the evidence of consent is a database whose
        -- corruption destroys the evidence.
        document_ref    TEXT    NOT NULL,
        -- So that "the document we checked" and "the document on disk today"
        -- can be shown to be the same one. Without it, a swapped file is
        -- undetectable and the whole record is worth nothing.
        document_sha256 TEXT    NOT NULL,
        recorded_by     TEXT    NOT NULL,
        revoked_at      INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS draft_subjects (
        draft_id   TEXT    NOT NULL,
        subject_id TEXT    NOT NULL REFERENCES subjects (subject_id),
        added_by   TEXT    NOT NULL,
        added_at   INTEGER NOT NULL,
        PRIMARY KEY (draft_id, subject_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS posts (
        post_id     TEXT    PRIMARY KEY,
        tenant_id   TEXT    NOT NULL,
        draft_id    TEXT    NOT NULL,
        platform    TEXT    NOT NULL,
        -- The platform's own id for the thing it created. Null until the
        -- outbox is actually drained, which today it never is.
        external_id TEXT,
        published_at INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS releases_subject ON releases (subject_id)",
    "CREATE INDEX IF NOT EXISTS draft_subjects_subject "
    "ON draft_subjects (subject_id)",
    "CREATE INDEX IF NOT EXISTS posts_draft ON posts (draft_id)",
    "CREATE INDEX IF NOT EXISTS subjects_tenant ON subjects (tenant_id)",
)


class ConsentError(Exception):
    """A consent record could not be written, with a reason a person can act on."""


@dataclass(frozen=True)
class Post:
    post_id: str
    tenant_id: str
    draft_id: str
    platform: str
    external_id: str | None
    published_at: int


class ConsentStore:
    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA)

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        """This thread's connection. See `Pool` for why it is per-thread."""
        return self._pool.conn

    # ── people ────────────────────────────────────────────────────────────
    def add_subject(self, tenant: str, subject_id: str, display_label: str,
                    *, now_epoch_s: int) -> Subject:
        subject = Subject(subject_id, display_label)   # validates the id
        if not display_label.strip():
            raise ConsentError("برچسب این شخص خالی است")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO subjects (subject_id, tenant_id, display_label, "
                "created_at) VALUES (?, ?, ?, ?)",
                (subject_id, tenant, display_label.strip(), now_epoch_s))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise ConsentError(f"شخصی با شناسهٔ «{subject_id}» از قبل هست")
        return subject

    def subjects(self, tenant: str) -> list[Subject]:
        return [Subject(r[0], r[1]) for r in self._conn.execute(
            "SELECT subject_id, display_label FROM subjects "
            "WHERE tenant_id = ? ORDER BY created_at", (tenant,))]

    # ── documents ─────────────────────────────────────────────────────────
    def record_release(self, release_id: str, subject_id: str, *, scope: str,
                       signed_at: int, document_ref: str,
                       document_sha256: str, recorded_by: str,
                       expires_at: int | None = None) -> Release:
        """Write down a signed document.

        The hash is required, not optional. A release row without one is a
        claim that somebody signed something, with no way to ever check which
        something — and a record that cannot be checked reads exactly like a
        record that can.
        """
        if len(document_sha256 or "") != 64:
            raise ConsentError("هش سند باید sha256 باشد (۶۴ کاراکتر)")
        if not (document_ref or "").strip():
            raise ConsentError("مرجع سند خالی است — سند کجا نگه داشته می‌شود؟")
        if not parse_scope(scope):
            raise ConsentError("دامنهٔ این رضایت‌نامه هیچ پلتفرم معتبری ندارد")
        row = self._conn.execute(
            "SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)
        ).fetchone()
        if row is None:
            raise ConsentError(f"شخصی با شناسهٔ «{subject_id}» ثبت نشده")

        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO releases (release_id, subject_id, scope, "
                "signed_at, expires_at, document_ref, document_sha256, "
                "recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (release_id, subject_id, scope, signed_at, expires_at,
                 document_ref, document_sha256.lower(), recorded_by))
            self._conn.execute("COMMIT")
        except ConsentError:
            self._conn.execute("ROLLBACK")
            raise
        except Exception:
            self._conn.execute("ROLLBACK")
            raise ConsentError(f"رضایت‌نامهٔ «{release_id}» از قبل ثبت شده")
        return self.release(release_id)

    def revoke(self, release_id: str, *, now_epoch_s: int) -> None:
        """Withdraw. Once, and it does not come back.

        The update refuses to touch a row that already has a revocation
        stamp. Re-revoking would move the date forward, and the date is what
        every judgement compares against — a second call would quietly widen
        the range of documents the withdrawal invalidates.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE releases SET revoked_at = ? "
                "WHERE release_id = ? AND revoked_at IS NULL",
                (now_epoch_s, release_id))
            if cur.rowcount == 0:
                self._conn.execute("ROLLBACK")
                raise ConsentError(
                    f"«{release_id}» یا وجود ندارد یا قبلاً پس گرفته شده")
            self._conn.execute("COMMIT")
        except ConsentError:
            raise
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def release(self, release_id: str) -> Release:
        row = self._conn.execute(
            "SELECT release_id, subject_id, scope, signed_at, expires_at, "
            "revoked_at FROM releases WHERE release_id = ?",
            (release_id,)).fetchone()
        if row is None:
            raise ConsentError(f"رضایت‌نامهٔ «{release_id}» پیدا نشد")
        return _to_release(row)

    def releases_for(self, subject_ids: Sequence[str]) -> list[Release]:
        if not subject_ids:
            return []
        marks = ", ".join("?" for _ in subject_ids)
        return [_to_release(r) for r in self._conn.execute(
            f"SELECT release_id, subject_id, scope, signed_at, expires_at, "
            f"revoked_at FROM releases WHERE subject_id IN ({marks})",
            tuple(subject_ids))]

    def document_digest(self, release_id: str) -> str:
        """The hash recorded when the document was filed.

        Kept separate from `release()` because the kernel's decision must not
        have it: a judgement that could look at the hash would eventually be
        written to compare it against something, and comparing a stored hash
        to itself proves nothing.
        """
        row = self._conn.execute(
            "SELECT document_sha256 FROM releases WHERE release_id = ?",
            (release_id,)).fetchone()
        if row is None:
            raise ConsentError(f"رضایت‌نامهٔ «{release_id}» پیدا نشد")
        return str(row[0])

    # ── who is in what ────────────────────────────────────────────────────
    def add_to_draft(self, draft_id: str, subject_id: str, *, added_by: str,
                     now_epoch_s: int) -> None:
        row = self._conn.execute(
            "SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)
        ).fetchone()
        if row is None:
            raise ConsentError(f"شخصی با شناسهٔ «{subject_id}» ثبت نشده")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO draft_subjects (draft_id, subject_id, "
                "added_by, added_at) VALUES (?, ?, ?, ?)",
                (draft_id, subject_id, added_by, now_epoch_s))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def remove_from_draft(self, draft_id: str, subject_id: str) -> None:
        """Take somebody out of a draft that has not gone out yet.

        Refused once the draft has been published, and this is the whole
        design rather than a cautious extra. `published_containing` answers
        by joining posts to `draft_subjects`, so deleting a row here after
        publication does not undo the publication — it deletes the *evidence*
        of it, and the withdrawal question starts returning a shorter,
        comfortable, wrong answer.

        Editing the plan is fine. Editing what already happened is not
        something this store offers.
        """
        published = self._conn.execute(
            "SELECT 1 FROM posts WHERE draft_id = ? LIMIT 1",
            (draft_id,)).fetchone()
        if published is not None:
            raise ConsentError(
                f"پیش‌نویس «{draft_id}» منتشر شده — چه کسی در آن بوده، دیگر "
                f"عوض نمی‌شود. برای پس گرفتن رضایت، رضایت‌نامه را revoke کنید.")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "DELETE FROM draft_subjects WHERE draft_id = ? "
                "AND subject_id = ?", (draft_id, subject_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def subjects_in_draft(self, draft_id: str) -> list[Subject]:
        return [Subject(r[0], r[1]) for r in self._conn.execute(
            "SELECT s.subject_id, s.display_label FROM draft_subjects d "
            "JOIN subjects s ON s.subject_id = d.subject_id "
            "WHERE d.draft_id = ? ORDER BY d.added_at", (draft_id,))]

    # ── publication ───────────────────────────────────────────────────────
    def record_post(self, tenant: str, post_id: str, draft_id: str, *,
                    platform: str, published_at: int,
                    external_id: str | None = None) -> Post:
        """A draft that actually went out.

        Nothing calls this today — no wire is connected and the outbox is
        never drained. It exists now because a post row that starts being
        written later leaves a gap in exactly the history this whole module
        is for.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO posts (post_id, tenant_id, draft_id, platform, "
                "external_id, published_at) VALUES (?, ?, ?, ?, ?, ?)",
                (post_id, tenant, draft_id, platform, external_id,
                 published_at))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise ConsentError(f"پستی با شناسهٔ «{post_id}» از قبل هست")
        return Post(post_id, tenant, draft_id, platform, external_id,
                    published_at)

    def published_containing(self, subject_id: str) -> list[Post]:
        """Everything already published that this person is in.

        The question that has to be answerable on the day somebody withdraws.
        It is a plain join, and it is a plain join only because
        `draft_subjects` was written from the first day.
        """
        return [Post(*r) for r in self._conn.execute(
            "SELECT p.post_id, p.tenant_id, p.draft_id, p.platform, "
            "p.external_id, p.published_at "
            "FROM posts p JOIN draft_subjects d ON d.draft_id = p.draft_id "
            "WHERE d.subject_id = ? ORDER BY p.published_at",
            (subject_id,))]


def _to_release(row) -> Release:
    return Release(
        release_id=row[0], subject_id=row[1], scope=parse_scope(row[2]),
        signed_at=int(row[3]),
        expires_at=None if row[4] is None else int(row[4]),
        revoked_at=None if row[5] is None else int(row[5]))
