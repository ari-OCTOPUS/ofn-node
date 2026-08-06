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
from .sqlite_base import Pool, add_column_if_absent, apply_schema

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
    # The library. A photo exists on its own, before and after any post.
    #
    # It used to exist only inside a draft, which meant a picture shot today
    # and used next month had nowhere to be in between — and a picture used
    # twice was two rows describing one file. An archive she can take
    # anywhere cannot be a by-product of posting.
    """
    CREATE TABLE IF NOT EXISTS media_items (
        media_id      TEXT    PRIMARY KEY,
        tenant_id     TEXT    NOT NULL,
        -- The album. NULL is a real answer: a photo she has not filed yet is
        -- a normal thing, and forcing a choice at upload makes her invent a
        -- category before she knows what it is.
        collection_id TEXT    REFERENCES collections (collection_id),
        mime          TEXT    NOT NULL DEFAULT 'image/jpeg',
        byte_size     INTEGER NOT NULL DEFAULT 0,
        -- Whether the untouched upload is on disk beside the renditions.
        has_original  INTEGER NOT NULL DEFAULT 0 CHECK (has_original IN (0, 1)),
        added_at      INTEGER NOT NULL,
        -- Archived photos leave the gallery and stay on disk. Deleting is a
        -- separate, louder act.
        archived_at   INTEGER,
        -- What she says about this shot, in her words. The closed vocabulary
        -- answers "which axis is this" and cannot answer "the light was
        -- coming through the blind and I want the next one like that". A
        -- library with no room for a sentence is an inventory.
        note          TEXT,
        -- Her own mark, 0 means unrated. Not a score the node computes: the
        -- only person who knows a shot is worth keeping is the one who took
        -- it, and that judgement is made once, while looking at it.
        rating        INTEGER NOT NULL DEFAULT 0
                      CHECK (rating BETWEEN 0 AND 5),
        -- When the photo was TAKEN, which is not when it was uploaded. Fifty
        -- photos filed on a Sunday all share one `added_at`, so ordering by
        -- it puts a shoot in whatever order the picker happened to hand them
        -- over. Nullable: unknown is a real answer and is not zero.
        taken_at      INTEGER,
        -- And where that number came from, recorded beside it rather than
        -- assumed. `file` is the picked file's own timestamp, which for a
        -- camera roll is usually the capture time and is occasionally the
        -- time it was copied off a card. `exif` would be authoritative and
        -- is not implemented — the renditions go through a canvas, which
        -- strips EXIF, and parsing the kept original needs a real camera
        -- photo to test against that this node does not have yet. Writing
        -- `exif` here without that would be a claim with no record behind it.
        taken_source  TEXT,
        category      TEXT    NOT NULL DEFAULT ''
    )
    """,
    # The highest number ever issued, per kind. Third time this shape has
    # been needed — `sku_high_water` in products was the first, and each time
    # the bug is identical: derive the next id from the rows that exist, and
    # a deleted row hands its id, and therefore its media directory, to a
    # different thing.
    """
    CREATE TABLE IF NOT EXISTS id_high_water (
        tenant_id TEXT    NOT NULL,
        kind      TEXT    NOT NULL,
        last      INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (tenant_id, kind)
    )
    """,
    # Labels belong to the photo, not the post.
    #
    # They were on the draft first, which was wrong in a way that only shows
    # up in her workflow: she tags a shot in the gallery weeks before it
    # becomes a post, and one photo used in two posts would have had two
    # separate sets of tags describing one image.
    """
    CREATE TABLE IF NOT EXISTS media_labels (
        media_id TEXT NOT NULL REFERENCES media_items (media_id),
        label    TEXT NOT NULL,
        PRIMARY KEY (media_id, label)
    )
    """,
    "CREATE INDEX IF NOT EXISTS media_labels_label ON media_labels (label)",
    "CREATE INDEX IF NOT EXISTS media_album ON media_items (tenant_id, collection_id)",
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
    """
    CREATE TABLE IF NOT EXISTS draft_labels (
        draft_id TEXT NOT NULL REFERENCES drafts (draft_id),
        label    TEXT NOT NULL,
        PRIMARY KEY (draft_id, label)
    )
    """,
    "CREATE INDEX IF NOT EXISTS draft_labels_label ON draft_labels (label)",
    "CREATE INDEX IF NOT EXISTS drafts_tenant ON drafts (tenant_id, status)",
    "CREATE INDEX IF NOT EXISTS drafts_collection ON drafts (collection_id)",
    "CREATE INDEX IF NOT EXISTS collections_tenant ON collections (tenant_id)",
)


def _add_media_description_columns(conn) -> None:
    """Note, rating and capture time, added after media rows existed.

    `CREATE TABLE IF NOT EXISTS` never revisits a table it finds, so a file
    written before this change keeps the old shape and pre-flight reports the
    drift as CRITICAL. See `apply_schema` and `boot.MIGRATIONS`.
    """
    add_column_if_absent(conn, "media_items", "note", "TEXT")
    add_column_if_absent(conn, "media_items", "rating",
                         "INTEGER NOT NULL DEFAULT 0")
    add_column_if_absent(conn, "media_items", "taken_at", "INTEGER")
    add_column_if_absent(conn, "media_items", "taken_source", "TEXT")


def _add_media_category_column(conn) -> None:
    add_column_if_absent(conn, "media_items", "category",
                         "TEXT NOT NULL DEFAULT ''")


MIGRATIONS = (_add_media_description_columns, _add_media_category_column)

STATUSES = ("draft", "ready", "queued", "published", "abandoned")

# Her own mark on a shot. Zero is "not rated", which is different from bad —
# an unrated library must not read as a library of ones.
MAX_RATING = 5
MAX_NOTE = 500
MAX_CATEGORY = 40

# Where `taken_at` came from. Recorded rather than assumed, so that the day
# EXIF parsing lands the two can be compared instead of one silently
# replacing the other and nobody knowing which rows are which.
TAKEN_SOURCES = ("file", "exif", "manual")

# The floor for a capture time. Deliberately NOT `boot.MIN_PLAUSIBLE_EPOCH`,
# which is 2026-01-01 and answers a different question: that one asks whether
# THIS BOARD's clock has heard from NTP yet, and a board reporting 1970 is
# broken. A photograph taken in 2025 is not broken, it is last year. What is
# not credible is a phone photo from before digital cameras existed, so the
# floor is set there and the ceiling is now — a file dated in the future sorts
# above everything she owns, for ever.
EARLIEST_PLAUSIBLE_EPOCH_S = 946_684_800     # 2000-01-01


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
        apply_schema(self._conn, SCHEMA, MIGRATIONS)

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
            tail = collection_id.rsplit("-", 1)[-1]
            if tail.isdigit():
                # In the same transaction as the row, for the same reason as
                # media: a deleted album must not hand its id to the next one.
                self._claim_id(tenant, "collection", int(tail))
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

    def collection_in(self, tenant: str, collection_id: str) -> Collection | None:
        """The same lookup, but scoped to one business.

        `collection` matches on the id alone, which is fine where the id came
        from this tenant's own listing and wrong anywhere the id came from a
        request. An album id is short and guessable, so an unscoped check is
        how one leg's photo ends up filed under another leg's album — and
        separating the three legs is the point of the tenant column.
        """
        row = self._conn.execute(
            "SELECT collection_id, label, genre, sensitivity FROM collections "
            "WHERE collection_id = ? AND tenant_id = ?",
            (collection_id, tenant)).fetchone()
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
    def delete_collection(self, tenant: str, collection_id: str) -> int:
        if self.collection_in(tenant, collection_id) is None:
            raise StudioError(f"آلبومی به نام «{collection_id}» نیست")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            moved = self._conn.execute("UPDATE media_items SET collection_id = NULL WHERE tenant_id = ? AND collection_id = ?", (tenant, collection_id)).rowcount
            self._conn.execute("UPDATE drafts SET collection_id = NULL WHERE tenant_id = ? AND collection_id = ?", (tenant, collection_id))
            self._conn.execute("DELETE FROM collections WHERE tenant_id = ? AND collection_id = ?", (tenant, collection_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK"); raise
        return int(moved)

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
            tail = draft_id.rsplit("-", 1)[-1]
            if tail.isdigit():
                self._claim_id(tenant, "draft", int(tail))
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
    # ── the library ───────────────────────────────────────────────────────
    def _next_id(self, tenant: str, kind: str, prefix: str,
                 present: Sequence[str]) -> str:
        """The next id of a kind, from the high-water mark.

        The rows still act as a floor: if the high-water row were ever lost,
        ids plainly in use must not be handed out again. But the mark is what
        makes deletion safe, because a deleted row is exactly the one the
        rows can no longer show.
        """
        row = self._conn.execute(
            "SELECT last FROM id_high_water WHERE tenant_id = ? AND kind = ?",
            (tenant, kind)).fetchone()
        top = int(row[0]) if row else 0
        for value in present:
            tail = str(value).rsplit("-", 1)[-1]
            if tail.isdigit():
                top = max(top, int(tail))
        return f"{prefix}-{top + 1:04d}"

    def _claim_id(self, tenant: str, kind: str, number: int) -> None:
        """Spend a number so nothing can ever issue it again."""
        self._conn.execute(
            "INSERT INTO id_high_water (tenant_id, kind, last) "
            "VALUES (?, ?, ?) ON CONFLICT(tenant_id, kind) "
            "DO UPDATE SET last = MAX(last, excluded.last)",
            (tenant, kind, number))

    def next_media_id(self, tenant: str) -> str:
        return self._next_id(tenant, "media", "shot", [
            r[0] for r in self._conn.execute(
                "SELECT media_id FROM media_items WHERE tenant_id = ?",
                (tenant,))])

    def next_collection_id(self, tenant: str) -> str:
        return self._next_id(tenant, "collection", "album", [
            r[0] for r in self._conn.execute(
                "SELECT collection_id FROM collections WHERE tenant_id = ?",
                (tenant,))])

    def next_draft_id(self, tenant: str) -> str:
        return self._next_id(tenant, "draft", "post", [
            r[0] for r in self._conn.execute(
                "SELECT draft_id FROM drafts WHERE tenant_id = ?", (tenant,))])

    def describe_media(self, tenant: str, media_id: str, *,
                       note: str | None = None,
                       rating: int | None = None,
                       category: str | None = None) -> dict:
        """Her words and her mark on one shot. Either, both, or neither.

        `None` means "leave this alone" and is not the same as clearing it —
        a screen that saves a rating must not wipe a note it never showed.
        Clearing is an empty string and a zero, both of which are explicit.

        The range is enforced here and not only in the schema. SQLite cannot
        attach a CHECK to a column added by ALTER TABLE, so the constraint in
        `SCHEMA` protects a file created after this change and does nothing
        for one migrated into it. Two files, one rule, and the rule has to
        live where both of them pass through.
        """
        if self.media_in(tenant, media_id) is None:
            raise StudioError("این عکس پیدا نشد")
        sets, args = [], []
        if note is not None:
            text = str(note).strip()
            if len(text) > MAX_NOTE:
                raise StudioError(f"یادداشت از {MAX_NOTE} نویسه بلندتر است")
            sets.append("note = ?")
            args.append(text or None)
        if rating is not None:
            if isinstance(rating, bool) or not isinstance(rating, int):
                raise StudioError("امتیاز باید عدد باشد")
            if not 0 <= rating <= MAX_RATING:
                raise StudioError(f"امتیاز باید بین ۰ و {MAX_RATING} باشد")
            sets.append("rating = ?")
            args.append(rating)
        if category is not None:
            cat = str(category).strip()
            if len(cat) > MAX_CATEGORY:
                raise StudioError(f"دسته‌بندی از {MAX_CATEGORY} نویسه بلندتر است")
            sets.append("category = ?")
            args.append(cat)
        if not sets:
            return self.media_in(tenant, media_id)
        args += [tenant, media_id]
        self._conn.execute(
            f"UPDATE media_items SET {', '.join(sets)} "
            f"WHERE tenant_id = ? AND media_id = ?", tuple(args))
        return self.media_in(tenant, media_id)

    def media_in(self, tenant: str, media_id: str) -> dict | None:
        """One photo, scoped to its tenant.

        Scoped because an id alone is not authorisation — the same shape of
        leak that had to be closed once already when an album id was looked
        up without asking whose album it was.
        """
        row = self._conn.execute(
            "SELECT media_id, collection_id, mime, byte_size, has_original, "
            "added_at, archived_at, note, rating, taken_at, taken_source, category "
            "FROM media_items WHERE tenant_id = ? AND media_id = ?",
            (tenant, media_id)).fetchone()
        if row is None:
            return None
        return {"media_id": row[0], "collection_id": row[1], "mime": row[2],
                "byte_size": int(row[3]), "has_original": bool(row[4]),
                "added_at": int(row[5]), "archived_at": row[6],
                "note": row[7] or "", "rating": int(row[8] or 0),
                "taken_at": row[9], "taken_source": row[10] or "",
                "category": row[11] or "",
                "labels": [r[0] for r in self._conn.execute(
                    "SELECT label FROM media_labels WHERE media_id = ? "
                    "ORDER BY label", (media_id,))]}

    def add_media(self, tenant: str, media_id: str, *, mime: str,
                  byte_size: int, has_original: bool, now_epoch_s: int,
                  taken_at: int | None = None, taken_source: str = "",
                  collection_id: str | None = None) -> None:
        # Scoped: an album id arriving in a request must be one of this
        # tenant's own, not merely one that exists somewhere.
        if collection_id is not None \
                and self.collection_in(tenant, collection_id) is None:
            raise StudioError(f"آلبومی به نام «{collection_id}» نیست")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            # An unrecognised source is stored as unknown rather than as
            # itself: the column exists to say what the number is worth, so a
            # value nobody defined would defeat the only thing it is for.
            source = taken_source if taken_source in TAKEN_SOURCES else ""
            self._conn.execute(
                "INSERT INTO media_items (media_id, tenant_id, collection_id, "
                "mime, byte_size, has_original, added_at, "
                "taken_at, taken_source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (media_id, tenant, collection_id, mime, int(byte_size),
                 1 if has_original else 0, now_epoch_s,
                 int(taken_at) if taken_at else None, source or None))
            tail = media_id.rsplit("-", 1)[-1]
            if tail.isdigit():
                # In the same transaction as the row: a crash between the two
                # would leave an id issued but not recorded.
                self._claim_id(tenant, "media", int(tail))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise StudioError(f"عکسی با شناسهٔ «{media_id}» از قبل هست")

    def gallery(self, tenant: str, *, collection_id: str | None = None,
                include_archived: bool = False) -> list[dict]:
        """What is in the library, newest first.

        `collection_id=None` means every album *and* the unfiled ones —
        which is what a gallery opens on. Filtering to unfiled only is a
        different question and would need its own argument rather than
        overloading this one.
        """
        sql = ("SELECT media_id, collection_id, mime, byte_size, "
               "has_original, added_at, archived_at, note, rating, "
               "taken_at, taken_source, category FROM media_items "
               "WHERE tenant_id = ? ")
        args: tuple = (tenant,)
        if collection_id is not None:
            sql += "AND collection_id = ? "
            args += (collection_id,)
        if not include_archived:
            sql += "AND archived_at IS NULL "
        # Ordered by when it was TAKEN where that is known, falling back to
        # when it arrived. Fifty photos uploaded in one sitting share a single
        # `added_at`, so ordering by that alone hands a shoot back in whatever
        # order the picker happened to iterate — which is not an order at all.
        rows = [{"media_id": r[0], "collection_id": r[1], "mime": r[2],
                 "byte_size": int(r[3]), "has_original": bool(r[4]),
                 "added_at": int(r[5]), "archived_at": r[6],
                 "note": r[7] or "", "rating": int(r[8] or 0),
                 "taken_at": r[9], "taken_source": r[10] or "",
                 "category": r[11] or "", "labels": []}
                for r in self._conn.execute(
                    sql + "ORDER BY COALESCE(taken_at, added_at) DESC, "
                          "media_id DESC", args)]
        # Labels fetched in one query rather than per row: a gallery of two
        # hundred photos would otherwise be two hundred round trips to the
        # same file.
        if rows:
            marks = ", ".join("?" for _ in rows)
            by_id = {r["media_id"]: r for r in rows}
            for mid, label in self._conn.execute(
                    f"SELECT media_id, label FROM media_labels "
                    f"WHERE media_id IN ({marks}) ORDER BY label",
                    tuple(by_id)):
                by_id[mid]["labels"].append(label)
        return rows

    def set_media_collection(self, tenant: str, media_id: str,
                             collection_id: str | None) -> str | None:
        """Move a photo into an album, or out of every album.

        Filing was only possible at upload time, which assumed she knows
        where a photo belongs at the moment she picks it. She does not — that
        is what an archiving session is *for*, and a photo already on the
        board had no way to be moved.

        `None` is a real value here, not a missing one: taking a photo out of
        an album has to be as available as putting it in, or the first
        mistake is permanent.
        """
        if collection_id is not None \
                and self.collection_in(tenant, collection_id) is None:
            raise StudioError(f"آلبومی به نام «{collection_id}» نیست")
        # Scoped by tenant in the UPDATE itself rather than checked first:
        # a check followed by a write is two statements that can disagree.
        changed = self._conn.execute(
            "UPDATE media_items SET collection_id = ? "
            "WHERE media_id = ? AND tenant_id = ?",
            (collection_id, media_id, tenant)).rowcount
        if not changed:
            raise StudioError(f"عکسی با شناسهٔ «{media_id}» نیست")
        self._conn.commit()
        return collection_id

    def set_media_labels(self, tenant: str, media_id: str,
                         labels: Sequence[str], *,
                         allowed: Sequence[str]) -> list[str]:
        """Tag a photo. Replaces the whole set.

        Replacing rather than adding: a tag set describes one photo, and a
        half-updated description is worse than either version — she unticks
        `close` and ticks `wide`, and both surviving would make that photo
        evidence for both sides of the same axis.
        """
        known = {r["media_id"] for r in self.gallery(tenant,
                                                     include_archived=True)}
        if media_id not in known:
            raise StudioError(f"عکسی با شناسهٔ «{media_id}» نیست")
        permitted = set(allowed)
        chosen: list[str] = []
        for raw in labels:
            text = str(raw)
            if text not in permitted:
                raise StudioError(f"برچسب ناشناخته: {text!r}")
            if text not in chosen:
                chosen.append(text)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute("DELETE FROM media_labels WHERE media_id = ?",
                               (media_id,))
            for label in chosen:
                self._conn.execute(
                    "INSERT INTO media_labels (media_id, label) VALUES (?, ?)",
                    (media_id, label))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return chosen

    def media_label_counts(self, tenant: str) -> dict[str, int]:
        return {str(r[0]): int(r[1]) for r in self._conn.execute(
            "SELECT l.label, COUNT(*) FROM media_labels l "
            "JOIN media_items m ON m.media_id = l.media_id "
            "WHERE m.tenant_id = ? GROUP BY l.label", (tenant,))}

    def file_media(self, tenant: str, media_id: str,
                   collection_id: str | None) -> None:
        """Move a photo into an album, or out of every album."""
        if collection_id is not None and self.collection(collection_id) is None:
            raise StudioError(f"آلبومی به نام «{collection_id}» نیست")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE media_items SET collection_id = ? "
                "WHERE tenant_id = ? AND media_id = ?",
                (collection_id, tenant, media_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def archive_media(self, tenant: str, media_id: str, *,
                      now_epoch_s: int) -> None:
        """Out of the gallery, still on disk. Deleting is louder."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE media_items SET archived_at = ? WHERE tenant_id = ? "
                "AND media_id = ? AND archived_at IS NULL",
                (now_epoch_s, tenant, media_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def drop_media(self, tenant: str, media_id: str) -> dict | None:
        """Remove the record and say what it was.

        Refused while any draft still uses it: a post pointing at a photo
        that no longer exists is a post that renders as a gap, and she would
        have no way to tell that from a photo that failed to load.
        """
        used = self._conn.execute(
            "SELECT COUNT(*) FROM draft_media WHERE media_ref = ?",
            (media_id,)).fetchone()
        if used and int(used[0]) > 0:
            raise StudioError(
                f"«{media_id}» در {int(used[0])} پست استفاده شده — "
                f"اول از آن پست‌ها بردارش")
        rows = self.gallery(tenant, include_archived=True)
        found = next((r for r in rows if r["media_id"] == media_id), None)
        if found is None:
            return None
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "DELETE FROM media_items WHERE tenant_id = ? AND media_id = ?",
                (tenant, media_id))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return found

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

    # ── style labels ──────────────────────────────────────────────────────
    def set_labels(self, draft_id: str, labels: Sequence[str], *,
                   allowed: Sequence[str]) -> list[str]:
        """Tag a post with what it is. Replaces the whole set.

        Replacing rather than adding, because tagging is a description of one
        post and a half-updated description is worse than either version —
        she unticks `close` and ticks `wide`, and both surviving would make
        the post count as evidence for both.

        Anything outside the pack's vocabulary is refused rather than stored.
        A label written once and never matched again looks exactly like a
        style that never worked.
        """
        permitted = set(allowed)
        chosen = []
        for raw in labels:
            text = str(raw)
            if text not in permitted:
                raise StudioError(f"برچسب ناشناخته: {text!r}")
            if text not in chosen:
                chosen.append(text)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute("DELETE FROM draft_labels WHERE draft_id = ?",
                               (draft_id,))
            for label in chosen:
                self._conn.execute(
                    "INSERT INTO draft_labels (draft_id, label) VALUES (?, ?)",
                    (draft_id, label))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return chosen

    def labels_of(self, draft_id: str) -> list[str]:
        return [str(r[0]) for r in self._conn.execute(
            "SELECT label FROM draft_labels WHERE draft_id = ? ORDER BY label",
            (draft_id,))]

    def label_counts(self, tenant: str, *, statuses: Sequence[str] = ()
                     ) -> dict[str, int]:
        """How many posts carry each label.

        Restricted to the statuses asked for, because "what have I tried" and
        "what have I published" are different questions and answering the
        first when the second was asked overstates what has actually been
        tested in public.
        """
        sql = ("SELECT l.label, COUNT(*) FROM draft_labels l "
               "JOIN drafts d ON d.draft_id = l.draft_id "
               "WHERE d.tenant_id = ? ")
        args: tuple = (tenant,)
        if statuses:
            sql += "AND d.status IN (" + ",".join("?" * len(statuses)) + ") "
            args += tuple(statuses)
        return {str(r[0]): int(r[1]) for r in
                self._conn.execute(sql + "GROUP BY l.label", args)}

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
