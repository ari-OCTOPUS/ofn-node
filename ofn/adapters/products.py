"""Product records — one row per piece Maliheh makes.

Every piece is unique. There is no batch, no stock count, and no runway: a
one-off either exists, is for sale, has sold, or was given away. Counting
"units left" on a thing there is exactly one of produces a number that is
always 1 or 0 and never tells anybody anything.

Separate database file from facts/ledger/outbox, same durability policy. A
product is not a fact: facts are what the business knows about itself and
carry validity over time, while a piece is a row with a life.

Three rules here, all of which are cheap now and expensive later:

  * `hourly_rate_aud` is COPIED into the row at save time, never read live
    from the business's current rate. When she raises her rate from $25 to
    $35, last month's piece must not silently become loss-making. It was
    profitable at the rate that applied, and the record has to keep saying so.

  * `cogs_aud` is written by this module from the formula the pack declares,
    and callers may never set it. It used to be a SQLite generated column,
    which made disagreement impossible — moving the formula into the pack
    costs that guarantee, so `recompute_cogs` exists to prove it back.

  * A platform's cut is NOT part of cost. Cost is a property of the piece;
    a fee is a property of where it sold. Folding the fee into COGS would
    make the same piece cost different amounts depending on who bought it.

  * There are two prices, and every profit judgement uses the LOWER one that
    exists. Listed at $100, floor $60, cost $80: a warning that looks only at
    the listed price says "healthy" while she sells at a stall for $60 and
    loses $20 on every piece. A warning computed against the optimistic price
    is a warning that reassures and is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Mapping, Sequence

from .sqlite_base import Pool, add_column_if_absent, apply_schema

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS products (
        id                  INTEGER PRIMARY KEY,
        tenant_id           TEXT    NOT NULL DEFAULT 'ziman',
        sku                 TEXT    NOT NULL,
        name                TEXT    NOT NULL,
        category            TEXT,
        description         TEXT,

        materials_cost_aud  REAL    NOT NULL DEFAULT 0,
        labour_hours        REAL    NOT NULL DEFAULT 0,
        -- Copied from the business's rate at save time, deliberately not a
        -- lookup. See the module docstring.
        hourly_rate_aud     REAL    NOT NULL DEFAULT 0,
        packaging_cost_aud  REAL    NOT NULL DEFAULT 0,
        -- Written by this module from the pack's formula. Never by a caller.
        cogs_aud            REAL    NOT NULL DEFAULT 0,

        -- Two prices, both nullable. Nobody, including this system, invents
        -- either one.
        --   primary   what it is listed at — Instagram, Etsy
        --   secondary the floor she will actually take — a market stall, cash
        -- Every judgement about profit uses the SECOND one where it exists.
        -- See the module docstring.
        price_primary_aud   REAL,
        price_secondary_aud REAL,

        state               TEXT    NOT NULL DEFAULT 'in_progress'
                              CHECK (state IN ('in_progress', 'for_sale',
                                     'sold', 'gifted')),
        -- Where it sold. Null until it does.
        channel             TEXT
                              CHECK (channel IS NULL OR channel IN
                                     ('instagram', 'market', 'etsy', 'direct', 'shopify')),
        listed_at           TEXT,
        sold_at             TEXT,

        marketing_status    TEXT    NOT NULL DEFAULT 'not_started'
                              CHECK (marketing_status IN ('not_started',
                                     'photo_done', 'caption_done', 'posted')),
        marketing_notes     TEXT,

        environment         TEXT    NOT NULL DEFAULT 'legacy_unknown'
                              CHECK (environment IN ('production', 'seed',
                                     'test', 'demo', 'legacy_unknown')),
        source              TEXT    NOT NULL DEFAULT 'legacy_unknown',
        created_by          TEXT    NOT NULL DEFAULT 'legacy_unknown',
        created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at          TEXT,

        -- Archiving is a separate axis from state, not a fifth value of it.
        -- A piece that is archived was still `sold` or `in_progress` when it
        -- was put away, and folding the two would lose that. It is also the
        -- only shape SQLite allows without rewriting the table: `state` has
        -- a CHECK constraint, and a CHECK cannot be altered in place.
        archived_at         TEXT
    )
    """,
    # Photos land tomorrow, but the table is created tonight so that evening
    # is a feature and not a migration. Three sizes because the same photo
    # has three jobs: the archive copy that can never be retaken, the one
    # Instagram gets, and the small one a list of forty pieces scrolls with.
    """
    CREATE TABLE IF NOT EXISTS product_photos (
        id            INTEGER PRIMARY KEY,
        product_id    INTEGER NOT NULL
                        REFERENCES products (id) ON DELETE CASCADE,
        original_path TEXT    NOT NULL,   -- exactly as her phone produced it
        display_path  TEXT    NOT NULL,   -- long edge 1600
        thumb_path    TEXT    NOT NULL,   -- long edge 320
        mime          TEXT    NOT NULL DEFAULT 'image/jpeg',
        byte_size     INTEGER NOT NULL DEFAULT 0,
        position      INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    # The highest piece number ever issued, per business — which is not the
    # same as the highest one currently on the shelf. Deriving the next code
    # from the rows that exist means deleting a piece hands its code to the
    # next one, and the ledger then holds two different pieces called
    # ZM-0001. A number that has been spoken out loud on a phone call is
    # spent for ever, whatever happens to the row.
    """
    CREATE TABLE IF NOT EXISTS sku_high_water (
        tenant_id TEXT    PRIMARY KEY,
        last      INTEGER NOT NULL DEFAULT 0
    )
    """,
    # Which photo slots a piece has. The paths are NOT stored: they are
    # derived from (tenant, slug, position, edge) by `kernel/photos.py`, so
    # there is one place that decides where a file lives. A stored path is a
    # second copy of that decision, and the two disagree the first time the
    # layout changes.
    #
    # `product_photos` above is left alone and unused. It was built for three
    # sizes including an archived original, which D-A settled against: the
    # original stays on her phone. Dropping it would rewrite the table for no
    # gain, and an unread table costs nothing.
    """
    CREATE TABLE IF NOT EXISTS product_media (
        sku       TEXT    NOT NULL,
        tenant_id TEXT    NOT NULL,
        position  INTEGER NOT NULL CHECK (position >= 0),
        mime      TEXT    NOT NULL DEFAULT 'image/jpeg',
        byte_size INTEGER NOT NULL DEFAULT 0,
        added_at  TEXT    NOT NULL,
        PRIMARY KEY (tenant_id, sku, position)
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS products_sku "
    "ON products (tenant_id, sku)",
    "CREATE INDEX IF NOT EXISTS products_tenant ON products (tenant_id)",
    "CREATE INDEX IF NOT EXISTS products_tenant_state "
    "ON products (tenant_id, state)",
    "CREATE UNIQUE INDEX IF NOT EXISTS product_photos_slot "
    "ON product_photos (product_id, position)",
    "CREATE INDEX IF NOT EXISTS product_photos_product "
    "ON product_photos (product_id)",
    # Real sale events. Amount and fee are known or explicitly unknown;
    # customer PII is forbidden in this and every commerce table below.
    """
    CREATE TABLE IF NOT EXISTS product_sale_events (
        event_id       TEXT PRIMARY KEY,
        tenant_id      TEXT NOT NULL,
        sku            TEXT NOT NULL,
        gross_cents    INTEGER,
        amount_unknown INTEGER NOT NULL DEFAULT 0
                       CHECK (amount_unknown IN (0, 1)),
        channel        TEXT NOT NULL,
        fee_cents      INTEGER,
        fee_unknown    INTEGER NOT NULL DEFAULT 0
                       CHECK (fee_unknown IN (0, 1)),
        sold_at        TEXT NOT NULL,
        evidence_digest TEXT NOT NULL DEFAULT '',
        environment    TEXT NOT NULL DEFAULT 'legacy_unknown'
                       CHECK (environment IN ('production', 'seed', 'test',
                              'demo', 'legacy_unknown')),
        source         TEXT NOT NULL DEFAULT 'legacy_unknown',
        created_by     TEXT NOT NULL DEFAULT 'legacy_unknown',
        created_at     TEXT NOT NULL,
        UNIQUE (tenant_id, event_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS product_sale_sku "
    "ON product_sale_events (tenant_id, sku, sold_at)",
    """
    CREATE TABLE IF NOT EXISTS product_listing_events (
        listing_id          TEXT PRIMARY KEY,
        tenant_id           TEXT NOT NULL,
        sku                 TEXT NOT NULL,
        channel             TEXT NOT NULL,
        packet_sha256       TEXT NOT NULL,
        external_ref_digest TEXT NOT NULL DEFAULT '',
        published_at        TEXT NOT NULL,
        environment         TEXT NOT NULL CHECK (environment IN
                            ('production', 'seed', 'test', 'demo',
                             'legacy_unknown')),
        source              TEXT NOT NULL,
        created_by          TEXT NOT NULL,
        created_at          TEXT NOT NULL,
        FOREIGN KEY (tenant_id, sku) REFERENCES products (tenant_id, sku)
    )
    """,
    "CREATE INDEX IF NOT EXISTS product_listing_piece "
    "ON product_listing_events (tenant_id, sku, published_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS product_listing_external_ref "
    "ON product_listing_events (tenant_id, channel, external_ref_digest) "
    "WHERE external_ref_digest <> ''",
    """
    CREATE TABLE IF NOT EXISTS product_inquiries (
        inquiry_id       TEXT PRIMARY KEY,
        tenant_id        TEXT NOT NULL,
        sku              TEXT NOT NULL,
        listing_id       TEXT NOT NULL,
        channel          TEXT NOT NULL,
        source_ref_digest TEXT NOT NULL DEFAULT '',
        received_at      TEXT NOT NULL,
        status           TEXT NOT NULL,
        environment      TEXT NOT NULL CHECK (environment IN
                         ('production', 'seed', 'test', 'demo',
                          'legacy_unknown')),
        source           TEXT NOT NULL,
        created_by       TEXT NOT NULL,
        created_at       TEXT NOT NULL,
        FOREIGN KEY (tenant_id, sku) REFERENCES products (tenant_id, sku),
        FOREIGN KEY (listing_id) REFERENCES product_listing_events (listing_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS product_inquiry_piece "
    "ON product_inquiries (tenant_id, sku, received_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS product_inquiry_source_ref "
    "ON product_inquiries (tenant_id, channel, source_ref_digest) "
    "WHERE source_ref_digest <> ''",
    """
    CREATE TABLE IF NOT EXISTS product_orders (
        order_id       TEXT PRIMARY KEY,
        tenant_id      TEXT NOT NULL,
        sku            TEXT NOT NULL,
        listing_id     TEXT,
        inquiry_id     TEXT,
        status         TEXT NOT NULL CHECK (status IN
                       ('reserved', 'expired', 'cancelled', 'paid')),
        reserved_at    TEXT NOT NULL,
        expires_at     TEXT NOT NULL,
        environment    TEXT NOT NULL CHECK (environment IN
                       ('production', 'seed', 'test', 'demo',
                        'legacy_unknown')),
        source         TEXT NOT NULL,
        created_by     TEXT NOT NULL,
        created_at     TEXT NOT NULL,
        updated_at     TEXT,
        FOREIGN KEY (tenant_id, sku) REFERENCES products (tenant_id, sku),
        FOREIGN KEY (listing_id) REFERENCES product_listing_events (listing_id),
        FOREIGN KEY (inquiry_id) REFERENCES product_inquiries (inquiry_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS product_order_piece "
    "ON product_orders (tenant_id, sku, reserved_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS product_one_active_order "
    "ON product_orders (tenant_id, sku) WHERE status = 'reserved'",
    """
    CREATE TABLE IF NOT EXISTS product_payments (
        payment_id          TEXT PRIMARY KEY,
        tenant_id           TEXT NOT NULL,
        order_id            TEXT NOT NULL,
        amount_cents        INTEGER NOT NULL,
        fee_cents           INTEGER,
        currency            TEXT NOT NULL,
        status              TEXT NOT NULL CHECK (status IN
                            ('pending', 'confirmed', 'settled', 'failed',
                             'refunded', 'reversed')),
        provider            TEXT NOT NULL,
        provider_event_digest TEXT NOT NULL DEFAULT '',
        confirmation_source TEXT NOT NULL,
        evidence_digest     TEXT NOT NULL DEFAULT '',
        confirmed_at        TEXT,
        environment         TEXT NOT NULL CHECK (environment IN
                            ('production', 'seed', 'test', 'demo',
                             'legacy_unknown')),
        source              TEXT NOT NULL,
        created_by          TEXT NOT NULL,
        created_at          TEXT NOT NULL,
        updated_at          TEXT,
        FOREIGN KEY (order_id) REFERENCES product_orders (order_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS product_payment_order "
    "ON product_payments (tenant_id, order_id, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS product_payment_provider_event "
    "ON product_payments (provider, provider_event_digest) "
    "WHERE provider_event_digest <> ''",
)

def _add_sale_events(conn) -> None:
    """Sale-events table for files created before it shipped."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS product_sale_events ("
        " event_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL,"
        " sku TEXT NOT NULL, gross_cents INTEGER,"
        " amount_unknown INTEGER NOT NULL DEFAULT 0,"
        " channel TEXT NOT NULL, fee_cents INTEGER,"
        " fee_unknown INTEGER NOT NULL DEFAULT 0,"
        " sold_at TEXT NOT NULL, created_at TEXT NOT NULL,"
        " UNIQUE (tenant_id, event_id))")


def _add_provenance(conn) -> None:
    """Add provenance without relabelling historical rows as production."""
    for table in ("products", "product_sale_events"):
        add_column_if_absent(
            conn, table, "environment",
            "TEXT NOT NULL DEFAULT 'legacy_unknown' CHECK (environment IN "
            "('production','seed','test','demo','legacy_unknown'))")
        add_column_if_absent(
            conn, table, "source", "TEXT NOT NULL DEFAULT 'legacy_unknown'")
        add_column_if_absent(
            conn, table, "created_by", "TEXT NOT NULL DEFAULT 'legacy_unknown'")
    add_column_if_absent(
        conn, "product_sale_events", "evidence_digest", "TEXT NOT NULL DEFAULT ''")
    # Defensive repair for databases manually altered with nullable columns.
    for table in ("products", "product_sale_events"):
        conn.execute(
            f"UPDATE {table} SET environment = 'legacy_unknown' "
            "WHERE environment IS NULL OR environment NOT IN "
            "('production','seed','test','demo','legacy_unknown')")
        conn.execute(
            f"UPDATE {table} SET source = 'legacy_unknown' "
            "WHERE source IS NULL OR trim(source) = ''")
        conn.execute(
            f"UPDATE {table} SET created_by = 'legacy_unknown' "
            "WHERE created_by IS NULL OR trim(created_by) = ''")

def _split_price_into_two(conn) -> None:
    """One `price_aud` becomes `price_primary_aud` + `price_secondary_aud`.

    The two-price model landed as an edit to `SCHEMA` alone. Files created
    before it kept a single `price_aud`, and because every create is
    `IF NOT EXISTS` nothing ever told us: the node booted clean, the tests
    passed against fresh in-memory files, and the mismatch waited in the one
    place no test looks — the real file on this board. It surfaced as a 500
    on the partner's first list, seconds after her first successful login.

    The old value carries to `primary`, which is what it meant: the listed
    price. `secondary` — the floor she will actually take — stays NULL,
    because nobody, including this migration, knows it. `price_aud` is left
    in place; dropping a column rewrites the table, and an inert column costs
    nothing.
    """
    add_column_if_absent(conn, "products", "price_primary_aud", "REAL")
    add_column_if_absent(conn, "products", "price_secondary_aud", "REAL")
    legacy = {r[1] for r in conn.execute("PRAGMA table_info(products)")}
    if "price_aud" in legacy:
        conn.execute("UPDATE products SET price_primary_aud = price_aud "
                     "WHERE price_primary_aud IS NULL AND price_aud IS NOT NULL")


def _seed_sku_high_water(conn) -> None:
    """Start the high-water mark at whatever the file has already used.

    Without this, a database written before the table existed would begin at
    zero and reissue every code still sitting in it. Runs once: after the
    first pass the row exists and `INSERT OR IGNORE` does nothing.
    """
    rows = conn.execute("SELECT tenant_id, sku FROM products").fetchall()
    top: dict[str, int] = {}
    for tenant, sku in rows:
        tail = str(sku).rsplit("-", 1)[-1]
        if tail.isdigit():
            top[tenant] = max(top.get(tenant, 0), int(tail))
    for tenant, last in top.items():
        conn.execute(
            "INSERT INTO sku_high_water (tenant_id, last) VALUES (?, ?) "
            "ON CONFLICT(tenant_id) DO UPDATE SET last = MAX(last, excluded.last)",
            (tenant, last))


def piece_slug(sku: str) -> str:
    """A SKU as a path component.

    `ZM-0001` is what she reads on the phone; `zm-0001` is what may be a
    directory. The path validator refuses upper case on purpose — on a
    case-insensitive filesystem `ZM-0001` and `zm-0001` are one directory,
    so folding silently merges two pieces rather than rejecting one.

    Converted here, once, rather than at each call site. A call site that
    converts is a call site that can forget to, and this one would have
    failed on the first real photo.
    """
    return str(sku or "").strip().lower()


def _add_archive_column(conn) -> None:
    """Archiving, added after files existed. See `apply_schema`."""
    add_column_if_absent(conn, "products", "archived_at", "TEXT")


_CHANNEL_CHECK_BODY = (
    "channel IS NULL OR channel IN "
    "('instagram', 'market', 'etsy', 'direct')"
)


def _quote_identifier(name: str) -> str:
    """Quote a SQLite identifier read from SQLite's own catalog."""
    return '"' + name.replace('"', '""') + '"'


def _skip_sql_space_and_comments(sql: str, at: int) -> int:
    """Advance over SQLite whitespace and comments."""
    while at < len(sql):
        if sql[at].isspace():
            at += 1
        elif sql.startswith("--", at):
            newline = sql.find("\n", at + 2)
            at = len(sql) if newline < 0 else newline + 1
        elif sql.startswith("/*", at):
            end = sql.find("*/", at + 2)
            if end < 0:
                raise RuntimeError("unterminated comment in products CREATE TABLE")
            at = end + 2
        else:
            break
    return at


def _skip_sql_quoted(sql: str, at: int) -> int:
    """Return the first byte after a SQLite string or quoted identifier."""
    opener = sql[at]
    closer = "]" if opener == "[" else opener
    at += 1
    while at < len(sql):
        if sql[at] == closer:
            if closer != "]" and at + 1 < len(sql) and sql[at + 1] == closer:
                at += 2
                continue
            return at + 1
        at += 1
    raise RuntimeError("unterminated quote in products CREATE TABLE")


def _products_table_body_start(create_sql: str) -> int:
    """Find the top-level column-list opener without parsing its contents."""
    at = 0
    while at < len(create_sql):
        at = _skip_sql_space_and_comments(create_sql, at)
        if at >= len(create_sql):
            break
        if create_sql[at] in "'\"`[":
            at = _skip_sql_quoted(create_sql, at)
        elif create_sql[at] == "(":
            return at
        else:
            at += 1
    raise RuntimeError("products CREATE TABLE has no column list")


def _matching_sql_paren(sql: str, opener: int) -> int:
    """Find a balanced close parenthesis, ignoring quoted/commented text."""
    depth = 0
    at = opener
    while at < len(sql):
        at = _skip_sql_space_and_comments(sql, at)
        if at >= len(sql):
            break
        char = sql[at]
        if char in "'\"`[":
            at = _skip_sql_quoted(sql, at)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return at
        at += 1
    raise RuntimeError("unbalanced parentheses in products CREATE TABLE")


def _normalized_sql_tokens(sql: str) -> list[tuple[str, int, int]]:
    """Comparable SQL tokens with source spans; comments/spacing are ignored."""
    out: list[tuple[str, int, int]] = []
    at = 0
    while at < len(sql):
        at = _skip_sql_space_and_comments(sql, at)
        if at >= len(sql):
            break
        start = at
        char = sql[at]
        if char in "'\"`[":
            at = _skip_sql_quoted(sql, at)
            token = sql[start:at]
            if char == "'":
                normalized = token
            else:
                normalized = token[1:-1].replace(char * 2, char).lower()
            out.append((normalized, start, at))
        elif char.isalnum() or char in "_$":
            at += 1
            while at < len(sql) and (sql[at].isalnum() or sql[at] in "_$"):
                at += 1
            out.append((sql[start:at].lower(), start, at))
        else:
            at += 1
            two = sql[start:at + 1]
            if two in ("<=", ">=", "!=", "==", "<>", "||", "->"):
                at += 1
            out.append((sql[start:at].lower(), start, at))
    return out


_CHANNEL_CHECK_TOKENS = tuple(
    token for token, _start, _end in _normalized_sql_tokens(_CHANNEL_CHECK_BODY)
)


def _legacy_channel_check_span(create_sql: str) -> tuple[int, int] | None:
    """Return only the exact four-channel CHECK expression's source span."""
    tokens = _normalized_sql_tokens(create_sql)
    values = [token for token, _start, _end in tokens]
    width = len(_CHANNEL_CHECK_TOKENS)
    matches: list[tuple[int, int]] = []
    for at in range(len(values) - width + 1):
        if tuple(values[at:at + width]) == _CHANNEL_CHECK_TOKENS:
            matches.append((tokens[at][1], tokens[at + width - 1][2]))
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError("products channel CHECK is ambiguous")
    return matches[0]


def _products_rebuild_sql(create_sql: str, temporary_name: str) -> str:
    """Change only the legacy channel CHECK and the table being created.

    The source is the SQL SQLite retained in ``sqlite_master``, not ``SCHEMA``.
    That is what preserves columns added by an older build, manual recovery or a
    future build this one does not know about.
    """
    span = _legacy_channel_check_span(create_sql)
    if span is None:
        raise RuntimeError("products channel CHECK is not the expected legacy shape")
    insertion = span[1] - 1          # before the channel IN-list's closing ')'
    updated = create_sql[:insertion] + ", 'shopify'" + create_sql[insertion:]
    body_start = _products_table_body_start(updated)
    body_end = _matching_sql_paren(updated, body_start)
    return (f"CREATE TABLE {_quote_identifier(temporary_name)} "
            f"{updated[body_start:body_end + 1]}{updated[body_end + 1:]}")


def _migrate_products_channel_check(conn) -> None:
    """Permit Shopify in files whose products CHECK still names four channels.

    SQLite cannot alter a CHECK constraint. Rebuilding is therefore necessary,
    but it must happen before ``apply_schema`` and outside its transaction:
    ``PRAGMA foreign_keys`` is deliberately a no-op while a transaction is
    active. All schema objects are copied from SQLite's catalog so the rebuild
    does not discard legacy/unknown columns, indexes, triggers, or foreign keys.
    """
    if conn.in_transaction:
        raise RuntimeError("products channel migration requires autocommit")

    row = conn.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type = 'table' AND name = 'products'"
    ).fetchone()
    if row is None or row[0] is None:
        return                         # fresh file; apply_schema creates it
    create_sql = str(row[0])
    if _legacy_channel_check_span(create_sql) is None:
        return                         # current, unconstrained, or unrelated CHECK

    objects = [(str(r[0]), str(r[1]), str(r[2])) for r in conn.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE tbl_name = 'products' AND type IN ('index', 'trigger') "
        "AND sql IS NOT NULL ORDER BY CASE type WHEN 'index' THEN 0 ELSE 1 END, name"
    )]
    columns = [str(r[1]) for r in conn.execute("PRAGMA table_xinfo(products)")
               if int(r[6]) == 0]
    if not columns:
        raise RuntimeError("products table has no copyable columns")

    existing = {str(r[0]) for r in conn.execute(
        "SELECT name FROM sqlite_master UNION SELECT name FROM sqlite_temp_master"
    )}
    stem = "products_new"
    temporary_name = stem
    suffix = 0
    while temporary_name in existing:
        suffix += 1
        temporary_name = f"{stem}_{suffix}"
    rebuilt_sql = _products_rebuild_sql(create_sql, temporary_name)

    foreign_keys = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    temporary = _quote_identifier(temporary_name)
    product_table = _quote_identifier("products")
    column_list = ", ".join(_quote_identifier(name) for name in columns)
    succeeded = False
    try:
        if foreign_keys:
            conn.execute("PRAGMA foreign_keys = OFF")
            if int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) != 0:
                raise RuntimeError("could not disable foreign key enforcement")
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(rebuilt_sql)
            conn.execute(
                f"INSERT INTO {temporary} ({column_list}) "
                f"SELECT {column_list} FROM {product_table}")
            conn.execute(f"DROP TABLE {product_table}")
            conn.execute(f"ALTER TABLE {temporary} RENAME TO {product_table}")
            for _kind, _name, sql in objects:
                conn.execute(sql)
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(
                    f"foreign key check failed after products rebuild: {violations!r}")
            conn.execute("COMMIT")
            succeeded = True
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    finally:
        # CREATE/COPY/DROP/RENAME and object recreation are one transaction, so
        # rollback is the cleanup: it cannot delete a pre-existing collision or
        # leave this migration's uniquely-named table behind. A successful
        # rebuild leaves enforcement on; a failure restores the caller's mode.
        target_foreign_keys = 1 if succeeded else foreign_keys
        conn.execute(
            f"PRAGMA foreign_keys = {'ON' if target_foreign_keys else 'OFF'}")
        if int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) \
                != target_foreign_keys:
            raise RuntimeError("could not restore foreign key enforcement")
    if succeeded:
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(
                f"foreign key check failed with enforcement restored: {violations!r}")


MIGRATIONS = (_split_price_into_two, _seed_sku_high_water,
              _add_archive_column, _add_sale_events, _add_provenance)
PRE_SCHEMA_MIGRATIONS = (_migrate_products_channel_check,)

MAX_PHOTOS_PER_PRODUCT = 5
STATES = ("in_progress", "for_sale", "sold", "gifted")
CHANNELS = ("instagram", "market", "etsy", "direct", "shopify")
ENVIRONMENTS = ("production", "seed", "test", "demo", "legacy_unknown")
ORDER_STATUSES = ("reserved", "expired", "cancelled", "paid")
PAYMENT_STATUSES = ("pending", "confirmed", "settled", "failed",
                    "refunded", "reversed")
TRUSTED_CONFIRMATION_SOURCES = ("provider_webhook", "audited_receipt")

# Verdict names. Deliberately three, matching the three things worth saying.
LOSES_MONEY = "loses_money"    # priced under cost
STALE = "stale"                # listed a long time ago and still here
QUICK_SALE = "quick_sale"      # gone fast — make another like it

# `labour_hours` and `hourly_rate_aud` are no longer editable. The questions
# that produced them were removed, so admitting them here would mean the only
# way to set them is a hand-written request — a field nobody can reach through
# the app but everybody can reach through the API.
EDITABLE: tuple[str, ...] = (
    "name", "category", "description",
    "materials_cost_aud",
    "packaging_cost_aud", "price_primary_aud", "price_secondary_aud",
    "state", "channel", "listed_at", "sold_at",
    "marketing_status", "marketing_notes",
)

_NUMERIC = {"materials_cost_aud",
            "packaging_cost_aud", "price_primary_aud", "price_secondary_aud"}
_NULLABLE = {"price_primary_aud", "price_secondary_aud"}


class ProductError(Exception):
    """A product could not be written, with a reason a person can act on."""


@dataclass(frozen=True)
class Product:
    id: int
    tenant_id: str
    sku: str
    name: str
    category: str | None
    description: str | None
    materials_cost_aud: float
    labour_hours: float
    hourly_rate_aud: float
    packaging_cost_aud: float
    cogs_aud: float
    price_primary_aud: float | None
    price_secondary_aud: float | None
    state: str
    channel: str | None
    listed_at: str | None
    sold_at: str | None
    marketing_status: str
    marketing_notes: str | None
    created_at: str
    updated_at: str | None
    # Set when she puts it away. Orthogonal to `state`.
    archived_at: str | None = None
    # Provenance travels at the end with defaults so a caller (or fixture)
    # that predates it still constructs a Product; old rows read as legacy.
    environment: str = "legacy_unknown"
    source: str = "legacy_unknown"
    created_by: str = "legacy_unknown"

    @property
    def judged_price_aud(self) -> float | None:
        """The price every profit judgement is made against.

        The floor where she has set one, otherwise the listed price. Not the
        average and not the higher: the number that matters is the one she
        will actually accept, because that is the one the money arrives at.
        """
        if self.price_secondary_aud is not None:
            return self.price_secondary_aud
        return self.price_primary_aud

    @property
    def gross_margin_aud(self) -> float | None:
        """Judged price minus cost, before any platform takes its cut."""
        p = self.judged_price_aud
        return None if p is None else p - self.cogs_aud

    @property
    def gross_margin_pct(self) -> float | None:
        p = self.judged_price_aud
        if not p:
            return None
        return (p - self.cogs_aud) / p

    @property
    def loses_money(self) -> bool:
        """True only when a price exists and is below cost. An unpriced piece
        is not losing money — it is unpriced, which is a different thing and
        must not wear a red warning."""
        p = self.judged_price_aud
        return p is not None and p < self.cogs_aud

    def days_on_sale(self, today: str) -> int | None:
        """How long it has been available. For a sold piece this stops at the
        sale — otherwise nothing sold would ever count as having sold fast,
        because the number would keep growing after the event."""
        if not self.listed_at:
            return None
        end = self.sold_at or today
        return max(0, (_day(end) - _day(self.listed_at)).days)

    def as_dict(self, today: str = "") -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["judged_price_aud"] = self.judged_price_aud
        d["gross_margin_aud"] = self.gross_margin_aud
        d["gross_margin_pct"] = self.gross_margin_pct
        d["loses_money"] = self.loses_money
        if today:
            d["days_on_sale"] = self.days_on_sale(today)
        return d


def _day(iso: str) -> date:
    return date.fromisoformat(iso[:10])


# ── the pack's formula, applied ──────────────────────────────────────────
def cogs_for(fields: Mapping[str, Any], *, cost_fields: Sequence[str],
             labour_hours_field: str, labour_rate_field: str) -> float:
    """Cost of one piece: the declared cost components, plus paid time.

    The shape is fixed — a sum of costs and at most one hours×rate term — and
    the *names* come from the pack. That covers a business whose costs are
    materials and packaging and one whose costs are materials and travel,
    without this module knowing what either sells. It is not an expression
    evaluator, and it should not become one: a formula language in a config
    file is a way to run arbitrary arithmetic nobody reviewed.

    A pack that declares no labour block leaves both names empty, which means
    *no labour term* — checked explicitly rather than left to `get("")`
    returning nothing. Those are the same answer only for as long as no field
    is ever called `""`, and a rule that holds by coincidence is a rule that
    stops holding without anybody editing it.
    """
    total = 0.0
    for name in cost_fields:
        total += float(fields.get(name) or 0.0)
    if not labour_hours_field or not labour_rate_field:
        return total
    hours = float(fields.get(labour_hours_field) or 0.0)
    rate = float(fields.get(labour_rate_field) or 0.0)
    return total + hours * rate


def channel_fee(price: float | None, channel: str | None,
                fees: Mapping[str, Mapping[str, float]]) -> float:
    """What the place of sale takes. Zero when nothing has sold yet.

    Refuses rather than assuming for a channel with no configured fee: a
    silent zero would report a margin the business does not actually keep.
    """
    if channel is None or price is None:
        return 0.0
    row = fees.get(channel)
    if row is None:
        raise ProductError(
            f"کارمزد کانال «{channel}» در پک تعریف نشده — تا تعریف نشود "
            f"حاشیهٔ این فروش محاسبه نمی‌شود")
    return price * float(row.get("percent", 0.0)) + float(row.get("fixed", 0.0))


def net_margin_aud(p: Product,
                   fees: Mapping[str, Mapping[str, float]]) -> float | None:
    """Margin after the channel's cut, against the judged price."""
    price = p.judged_price_aud
    if price is None:
        return None
    return price - channel_fee(price, p.channel, fees) - p.cogs_aud


def money_view(p: Product, *, gst_rate: float, gst_known: bool,
               time_counted: bool = True) -> dict[str, Any]:
    """The money numbers as they may be shown, given what we know.

    Single source for anything a screen or an export prints, because the one
    way to get this wrong is to have two places compute it and disagree.

    A registered business never keeps the tax it collects. Counting it as
    income overstates every margin by the rate — roughly nine percent here,
    which is exactly the width of the band between "healthy" and "losing
    money". So when she is registered, profit is judged on the price net of
    tax.

    When nobody has said yet, no final figure is claimed: the numbers are
    returned with `gst_known` false so the screen can label them, rather
    than a number that looks settled and is not.

    `time_counted` is the same rule applied to a second gap. When the pack
    declares no labour term, `cogs_aud` is what was *bought* and none of the
    hours are in it. The subtraction below is still arithmetic — but calling
    its result "profit" would be the system stating, with the same confidence
    as every other number on the screen, something it has no basis for.

    So the figure travels with a flag rather than being suppressed. Hiding it
    would be its own lie: materials really are covered, and that is worth
    knowing. What must not happen is a green mark that means "you are fine"
    when nobody has counted the evenings.
    """
    price = p.judged_price_aud
    rate = gst_rate if gst_known else 0.0
    net = None if price is None else price / (1.0 + rate)
    over_cost = None if net is None else net - p.cogs_aud
    return {
        "judged_price_aud": price,
        "price_ex_tax_aud": net,
        # Named `margin` for every caller that already reads it. What it
        # *means* is now qualified by the two flags below, not by its name.
        "margin_aud": over_cost,
        "margin_pct": None if not net else (net - p.cogs_aud) / net,
        # Still exactly true when it fires: below this price the money spent
        # on materials does not come back. Its being false is what changes
        # meaning — that is now "costs covered", not "profitable".
        "loses_money": net is not None and net < p.cogs_aud,
        "gst_known": gst_known,
        "gst_rate": rate,
        "time_counted": time_counted,
    }


def verdicts(p: Product, today: str, *, stale_after_days: int | None,
             quick_sale_days: int,
             loses_money: bool | None = None) -> tuple[str, ...]:
    """The short list of things worth saying about one piece.

    `stale_after_days` of None means she has not said yet how long is too
    long — so nothing is called stale. Ninety days was somebody's guess, and
    a guess wearing a warning label is still a guess. Same rule as an absent
    fact: no answer, no number.
    """
    out: list[str] = []
    if loses_money if loses_money is not None else p.loses_money:
        out.append(LOSES_MONEY)
    age = p.days_on_sale(today)
    if age is not None:
        if p.state == "for_sale" and stale_after_days is not None \
                and age > stale_after_days:
            out.append(STALE)
        elif p.state == "sold" and age < quick_sale_days:
            out.append(QUICK_SALE)
    return tuple(out)


_COLUMNS = ("id, tenant_id, sku, name, category, description, "
            "materials_cost_aud, labour_hours, hourly_rate_aud, "
            "packaging_cost_aud, cogs_aud, price_primary_aud, "
            "price_secondary_aud, state, channel, "
            "listed_at, sold_at, marketing_status, marketing_notes, "
            "created_at, updated_at, archived_at, environment, source, created_by")


class ProductStore:
    def __init__(self, path: str, *, cost_fields: Sequence[str],
                 labour_hours_field: str, labour_rate_field: str) -> None:
        # The formula's field names arrive from the pack and are held here so
        # every write goes through the same one.
        self._cost_fields = tuple(cost_fields)
        self._hours_field = labour_hours_field
        self._rate_field = labour_rate_field
        self._pool = Pool(path)
        try:
            # Rebuilding a table with child FKs requires foreign_keys OFF, and
            # SQLite ignores that PRAGMA inside apply_schema's transaction.
            _migrate_products_channel_check(self._conn)
            apply_schema(self._conn, SCHEMA, MIGRATIONS)
        except Exception:
            self._pool.close()
            raise

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        """This thread's connection. See `Pool` for why it is per-thread."""
        return self._pool.conn

    # ── reads ────────────────────────────────────────────────────────────
    def get(self, tenant: str, sku: str) -> Product | None:
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM products "
            "WHERE tenant_id = ? AND sku = ?", (tenant, sku)).fetchone()
        return Product(*row) if row else None

    def list(self, tenant: str, *, include_archived: bool = False
             ) -> list[Product]:
        """Her shelf. Archived pieces are absent unless asked for.

        The default is the one she sees, because the common call is the one
        that must be right without anybody remembering a flag.
        """
        sql = (f"SELECT {_COLUMNS} FROM products WHERE tenant_id = ? ")
        if not include_archived:
            sql += "AND archived_at IS NULL "
        return [Product(*r) for r in self._conn.execute(
            sql + "ORDER BY id", (tenant,))]

    # ── sale events ───────────────────────────────────────────────────────
    def record_sale(self, tenant: str, sku: str, *, event_id: str,
                    sold_at: str, channel: str,
                    gross_cents: int | None = None,
                    amount_unknown: bool = False,
                    fee_cents: int | None = None,
                    fee_unknown: bool = False,
                    evidence_digest: str = "",
                    environment: str = "production",
                    source: str = "authenticated_panel",
                    created_by: str = "authenticated_panel",
                    now_iso: str = "") -> dict:
        """Record a real sale and its canonical product mutation atomically.

        A manual/operational receipt is a sale event, not a payment-provider
        event; this method deliberately never inserts into ``product_payments``.
        """
        now_iso = now_iso or _utc_now()
        error = _sale_input_error(
            event_id=event_id, sku=sku, sold_at=sold_at, channel=channel,
            gross_cents=gross_cents, amount_unknown=amount_unknown,
            fee_cents=fee_cents, fee_unknown=fee_unknown,
            environment=environment, source=source, created_by=created_by)
        if error:
            return {"ok": False, "error": error}
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            out = self._record_sale_tx(
                tenant, sku, event_id=event_id, sold_at=sold_at,
                channel=channel, gross_cents=gross_cents,
                amount_unknown=amount_unknown, fee_cents=fee_cents,
                fee_unknown=fee_unknown, evidence_digest=evidence_digest,
                environment=environment, source=source,
                created_by=created_by, now_iso=now_iso)
            self._conn.execute("COMMIT")
            return out
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def _record_sale_tx(self, tenant: str, sku: str, *, event_id: str,
                        sold_at: str, channel: str,
                        gross_cents: int | None, amount_unknown: bool,
                        fee_cents: int | None, fee_unknown: bool,
                        evidence_digest: str, environment: str, source: str,
                        created_by: str, now_iso: str) -> dict:
        """Sale write assuming the caller already owns a write transaction."""
        duplicate = self._conn.execute(
            "SELECT tenant_id, sku FROM product_sale_events WHERE event_id = ?",
            (event_id,)).fetchone()
        if duplicate is not None:
            return {"ok": False, "error": "duplicate sale event",
                    "event_id": event_id, "duplicate": True}

        product = self._conn.execute(
            "SELECT state, archived_at, listed_at FROM products "
            "WHERE tenant_id = ? AND sku = ?", (tenant, sku)).fetchone()
        if product is None:
            return {"ok": False, "error": "unknown tenant or sku"}
        if product["archived_at"] is not None:
            return {"ok": False, "error": "archived product cannot be sold"}
        if product["state"] not in ("in_progress", "for_sale"):
            return {"ok": False,
                    "error": f"product state {product['state']} cannot be sold"}

        self._conn.execute(
            "INSERT INTO product_sale_events "
            "(event_id, tenant_id, sku, gross_cents, amount_unknown, channel, "
            "fee_cents, fee_unknown, sold_at, evidence_digest, environment, "
            "source, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, tenant, sku, gross_cents, int(amount_unknown), channel,
             fee_cents, int(fee_unknown), sold_at, evidence_digest or "",
             environment, source, created_by, now_iso))
        cur = self._conn.execute(
            "UPDATE products SET state = 'sold', channel = ?, sold_at = ?, "
            "listed_at = COALESCE(listed_at, ?), updated_at = ? "
            "WHERE tenant_id = ? AND sku = ? AND archived_at IS NULL "
            "AND state IN ('in_progress', 'for_sale')",
            (channel, sold_at, sold_at, now_iso, tenant, sku))
        if cur.rowcount != 1:
            raise ProductError("sale product mutation affected an unexpected row count")
        return {"ok": True, "event_id": event_id, "tenant_id": tenant,
                "sku": sku, "state": "sold", "channel": channel,
                "sold_at": sold_at, "listed_at": product["listed_at"] or sold_at}

    def sales(self, tenant: str, sku: str,
              limit: int = 50) -> list[dict]:
        """Sale events for one piece, newest first, without customer data."""
        rows = self._conn.execute(
            "SELECT event_id, tenant_id, sku, gross_cents, amount_unknown, "
            "channel, fee_cents, fee_unknown, sold_at, evidence_digest, "
            "environment, source, created_by, created_at "
            "FROM product_sale_events WHERE tenant_id = ? AND sku = ? "
            "ORDER BY sold_at DESC LIMIT ?", (tenant, sku, limit)).fetchall()
        out = [dict(r) for r in rows]
        for row in out:
            row["amount_unknown"] = bool(row["amount_unknown"])
            row["fee_unknown"] = bool(row["fee_unknown"])
        return out

    # ── gated commerce records ────────────────────────────────────────────
    def record_listing(self, tenant: str, sku: str, *, listing_id: str,
                       channel: str, packet_sha256: str,
                       external_ref_digest: str = "", published_at: str,
                       environment: str = "production",
                       source: str = "authenticated_panel",
                       created_by: str = "authenticated_panel",
                       now_iso: str = "") -> dict:
        now_iso = now_iso or _utc_now()
        _require_id("listing_id", listing_id)
        _require_channel(channel)
        _require_timestamp("published_at", published_at)
        _require_digest("packet_sha256", packet_sha256)
        _require_provenance(environment, source, created_by)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            old = self._conn.execute(
                "SELECT * FROM product_listing_events WHERE listing_id = ?",
                (listing_id,)).fetchone()
            if old is not None:
                if old["tenant_id"] != tenant or old["sku"] != sku:
                    raise ProductError("listing_id already belongs to another product")
                self._conn.execute("COMMIT")
                return _idempotent(old, listing_id=listing_id)
            product = self._commerce_product(tenant, sku)
            if product["state"] in ("sold", "gifted"):
                raise ProductError("A sold or gifted product cannot be listed")
            self._conn.execute(
                "INSERT INTO product_listing_events (listing_id, tenant_id, sku, "
                "channel, packet_sha256, external_ref_digest, published_at, "
                "environment, source, created_by, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (listing_id, tenant, sku, channel, packet_sha256,
                 external_ref_digest or "", published_at, environment, source,
                 created_by, now_iso))
            self._conn.execute("COMMIT")
        except Exception as exc:
            self._conn.execute("ROLLBACK")
            if "unique" in str(exc).lower():
                return {"ok": False, "error": "duplicate listing reference",
                        "duplicate": True}
            raise
        return {"ok": True, "listing_id": listing_id, "tenant_id": tenant,
                "sku": sku, "environment": environment}

    def create_inquiry(self, tenant: str, sku: str, *, inquiry_id: str,
                       listing_id: str, channel: str,
                       source_ref_digest: str = "", received_at: str,
                       status: str = "received",
                       environment: str = "production",
                       source: str = "authenticated_panel",
                       created_by: str = "authenticated_panel",
                       now_iso: str = "") -> dict:
        now_iso = now_iso or _utc_now()
        _require_id("inquiry_id", inquiry_id)
        _require_channel(channel)
        _require_timestamp("received_at", received_at)
        _require_text("status", status)
        _require_provenance(environment, source, created_by)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            old = self._conn.execute(
                "SELECT * FROM product_inquiries WHERE inquiry_id = ?",
                (inquiry_id,)).fetchone()
            if old is not None:
                if old["tenant_id"] != tenant or old["sku"] != sku:
                    raise ProductError("inquiry_id already belongs to another product")
                self._conn.execute("COMMIT")
                return _idempotent(old, inquiry_id=inquiry_id)
            self._commerce_product(tenant, sku)
            listing = self._linked("product_listing_events", "listing_id",
                                   listing_id, tenant, sku)
            if listing["channel"] != channel:
                raise ProductError("Inquiry channel does not match its listing")
            if listing["environment"] != environment:
                raise ProductError("Inquiry environment does not match its listing")
            self._conn.execute(
                "INSERT INTO product_inquiries (inquiry_id, tenant_id, sku, "
                "listing_id, channel, source_ref_digest, received_at, status, "
                "environment, source, created_by, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (inquiry_id, tenant, sku, listing_id, channel,
                 source_ref_digest or "", received_at, status, environment,
                 source, created_by, now_iso))
            self._conn.execute("COMMIT")
        except Exception as exc:
            self._conn.execute("ROLLBACK")
            if "unique" in str(exc).lower():
                return {"ok": False, "error": "duplicate inquiry reference",
                        "duplicate": True}
            raise
        return {"ok": True, "inquiry_id": inquiry_id, "listing_id": listing_id,
                "tenant_id": tenant, "sku": sku, "environment": environment}

    def reserve(self, tenant: str, sku: str, *, order_id: str,
                reserved_at: str, expires_at: str,
                listing_id: str | None = None, inquiry_id: str | None = None,
                environment: str = "production",
                source: str = "authenticated_panel",
                created_by: str = "authenticated_panel",
                now_iso: str = "") -> dict:
        now_iso = now_iso or _utc_now()
        _require_id("order_id", order_id)
        _require_timestamp("reserved_at", reserved_at)
        _require_timestamp("expires_at", expires_at)
        if _parse_timestamp(expires_at) <= _parse_timestamp(reserved_at):
            raise ProductError("expires_at must be after reserved_at")
        _require_provenance(environment, source, created_by)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            old = self._conn.execute(
                "SELECT * FROM product_orders WHERE order_id = ?", (order_id,)
            ).fetchone()
            if old is not None:
                if old["tenant_id"] != tenant or old["sku"] != sku:
                    raise ProductError("order_id already belongs to another product")
                self._conn.execute("COMMIT")
                return _idempotent(old, order_id=order_id)
            product = self._commerce_product(tenant, sku)
            if product["state"] in ("sold", "gifted"):
                raise ProductError("A sold or gifted product cannot be reserved")
            listing = None
            if listing_id:
                listing = self._linked("product_listing_events", "listing_id",
                                       listing_id, tenant, sku)
            if inquiry_id:
                inquiry = self._linked("product_inquiries", "inquiry_id",
                                       inquiry_id, tenant, sku)
                if listing_id and inquiry["listing_id"] != listing_id:
                    raise ProductError("Inquiry and listing links do not match")
                listing_id = listing_id or inquiry["listing_id"]
                listing = listing or self._linked(
                    "product_listing_events", "listing_id", listing_id,
                    tenant, sku)
            if listing is not None and listing["environment"] != environment:
                raise ProductError("Order environment does not match its listing")
            self._conn.execute(
                "UPDATE product_orders SET status = 'expired', updated_at = ? "
                "WHERE tenant_id = ? AND sku = ? AND status = 'reserved' "
                "AND expires_at <= ?", (now_iso, tenant, sku, reserved_at))
            active = self._conn.execute(
                "SELECT order_id FROM product_orders WHERE tenant_id = ? "
                "AND sku = ? AND status = 'reserved'", (tenant, sku)).fetchone()
            if active is not None:
                raise ProductError("Product already has an active reservation")
            self._conn.execute(
                "INSERT INTO product_orders (order_id, tenant_id, sku, listing_id, "
                "inquiry_id, status, reserved_at, expires_at, environment, source, "
                "created_by, created_at) VALUES (?,?,?,?,?,'reserved',?,?,?,?,?,?)",
                (order_id, tenant, sku, listing_id, inquiry_id, reserved_at,
                 expires_at, environment, source, created_by, now_iso))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "order_id": order_id, "tenant_id": tenant,
                "sku": sku, "status": "reserved", "expires_at": expires_at,
                "environment": environment}

    def record_payment_confirmation(
            self, tenant: str, *, payment_id: str, order_id: str,
            amount_cents: int, currency: str, status: str,
            provider: str, provider_event_digest: str,
            confirmation_source: str, evidence_digest: str,
            confirmed_at: str | None = None, fee_cents: int | None = None,
            environment: str = "production", source: str = "payment_confirmation",
            created_by: str = "system", now_iso: str = "") -> dict:
        """Record a payment and, when confirmed, sell in one SQL transaction."""
        now_iso = now_iso or _utc_now()
        _require_id("payment_id", payment_id)
        _require_id("order_id", order_id)
        _require_nonnegative_int("amount_cents", amount_cents)
        if fee_cents is not None:
            _require_nonnegative_int("fee_cents", fee_cents)
        _require_text("currency", currency)
        _require_text("provider", provider)
        _require_digest("provider_event_digest", provider_event_digest)
        _require_text("confirmation_source", confirmation_source)
        if status not in PAYMENT_STATUSES:
            raise ProductError(f"Invalid payment status: {status}")
        _require_provenance(environment, source, created_by)
        if confirmed_at is not None:
            _require_timestamp("confirmed_at", confirmed_at)
        confirmed = status in ("confirmed", "settled")
        if confirmed and not confirmed_at:
            raise ProductError("confirmed_at is required for confirmed payments")
        if environment == "production" and confirmed:
            if amount_cents <= 0:
                raise ProductError("Production confirmed payment amount must be positive")
            if confirmation_source not in TRUSTED_CONFIRMATION_SOURCES:
                raise ProductError("Untrusted production confirmation_source")
            _require_digest("evidence_digest", evidence_digest)

        self._conn.execute("BEGIN IMMEDIATE")
        try:
            old = self._conn.execute(
                "SELECT * FROM product_payments WHERE payment_id = ? OR "
                "(provider = ? AND provider_event_digest = ?)",
                (payment_id, provider, provider_event_digest)).fetchone()
            if old is not None:
                if old["tenant_id"] != tenant or old["order_id"] != order_id:
                    raise ProductError("payment id/event already belongs to another order")
                self._conn.execute("COMMIT")
                return _idempotent(old, payment_id=old["payment_id"])
            order = self._conn.execute(
                "SELECT * FROM product_orders WHERE order_id = ?", (order_id,)
            ).fetchone()
            if order is None or order["tenant_id"] != tenant:
                raise ProductError("Order does not belong to tenant")
            if order["environment"] != environment:
                raise ProductError("Payment environment does not match its order")
            if environment == "production" and order["environment"] != "production":
                raise ProductError("Sandbox/test order cannot become production payment")
            if confirmed and order["status"] not in ("reserved", "paid"):
                raise ProductError(f"Order status {order['status']} cannot be paid")
            self._conn.execute(
                "INSERT INTO product_payments (payment_id, tenant_id, order_id, "
                "amount_cents, fee_cents, currency, status, provider, "
                "provider_event_digest, confirmation_source, evidence_digest, "
                "confirmed_at, environment, source, created_by, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (payment_id, tenant, order_id, amount_cents, fee_cents, currency,
                 status, provider, provider_event_digest, confirmation_source,
                 evidence_digest or "", confirmed_at, environment, source,
                 created_by, now_iso))
            sale = None
            if confirmed and order["status"] == "reserved":
                listing = None
                if order["listing_id"]:
                    listing = self._conn.execute(
                        "SELECT channel FROM product_listing_events "
                        "WHERE listing_id = ?", (order["listing_id"],)).fetchone()
                channel = listing["channel"] if listing else "direct"
                sale = self._record_sale_tx(
                    tenant, order["sku"], event_id=f"payment:{payment_id}",
                    sold_at=confirmed_at or now_iso, channel=channel,
                    gross_cents=amount_cents, amount_unknown=False,
                    fee_cents=fee_cents, fee_unknown=fee_cents is None,
                    evidence_digest=evidence_digest, environment=environment,
                    source=source, created_by=created_by, now_iso=now_iso)
                if not sale["ok"]:
                    raise ProductError(sale["error"])
                cur = self._conn.execute(
                    "UPDATE product_orders SET status = 'paid', updated_at = ? "
                    "WHERE order_id = ? AND tenant_id = ? AND status = 'reserved'",
                    (now_iso, order_id, tenant))
                if cur.rowcount != 1:
                    raise ProductError("payment order mutation affected unexpected rows")
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return {"ok": True, "payment_id": payment_id, "order_id": order_id,
                "status": status, "order_status": "paid" if confirmed else order["status"],
                "sale_event_id": sale["event_id"] if sale else None,
                "environment": environment}

    def listings(self, tenant: str, sku: str | None = None) -> list[dict]:
        return self._commerce_rows("product_listing_events", tenant, sku,
                                   "published_at")

    def inquiries(self, tenant: str, sku: str | None = None) -> list[dict]:
        return self._commerce_rows("product_inquiries", tenant, sku, "received_at")

    def orders(self, tenant: str, sku: str | None = None) -> list[dict]:
        return self._commerce_rows("product_orders", tenant, sku, "reserved_at")

    def payments(self, tenant: str, order_id: str | None = None) -> list[dict]:
        sql = "SELECT * FROM product_payments WHERE tenant_id = ?"
        args: list[Any] = [tenant]
        if order_id is not None:
            sql += " AND order_id = ?"
            args.append(order_id)
        return [dict(r) for r in self._conn.execute(
            sql + " ORDER BY created_at DESC", args)]

    def is_available(self, tenant: str, sku: str, *, at_iso: str) -> bool:
        product = self.get(tenant, sku)
        if product is None or product.archived_at or product.state not in (
                "in_progress", "for_sale"):
            return False
        row = self._conn.execute(
            "SELECT 1 FROM product_orders WHERE tenant_id = ? AND sku = ? "
            "AND status = 'reserved' AND expires_at > ? LIMIT 1",
            (tenant, sku, at_iso)).fetchone()
        return row is None

    def _commerce_rows(self, table: str, tenant: str, sku: str | None,
                       order_column: str) -> list[dict]:
        sql = f"SELECT * FROM {table} WHERE tenant_id = ?"
        args: list[Any] = [tenant]
        if sku is not None:
            sql += " AND sku = ?"
            args.append(sku)
        return [dict(r) for r in self._conn.execute(
            sql + f" ORDER BY {order_column} DESC", args)]

    def _commerce_product(self, tenant: str, sku: str):
        row = self._conn.execute(
            "SELECT state, archived_at FROM products WHERE tenant_id = ? AND sku = ?",
            (tenant, sku)).fetchone()
        if row is None:
            raise ProductError("Product does not belong to tenant")
        if row["archived_at"] is not None:
            raise ProductError("Archived product is unavailable for commerce")
        return row

    def _linked(self, table: str, id_column: str, value: str,
                tenant: str, sku: str):
        row = self._conn.execute(
            f"SELECT * FROM {table} WHERE {id_column} = ?", (value,)).fetchone()
        if row is None or row["tenant_id"] != tenant or row["sku"] != sku:
            raise ProductError(f"{id_column} does not belong to tenant/product")
        return row

    def listing_packet(self, tenant: str, sku: str) -> dict | None:
        """The exact manual listing packet for a piece (read-only).

        Built from the product's canonical fields; nothing is mutated. Used
        by the human before publishing to a channel.
        """
        product = self.get(tenant, sku)
        if product is None:
            return None
        packet = {
            "sku": sku,
            "name": product.name,
            "caption": product.description or "",
            "price_primary_aud": product.price_primary_aud,
            "price_secondary_aud": product.price_secondary_aud,
            "cogs_aud": product.cogs_aud,
            "state": product.state,
        }
        import hashlib, json as _json
        packet["sha256"] = hashlib.sha256(
            _json.dumps(packet, ensure_ascii=False, sort_keys=True,
                        default=str).encode()).hexdigest()
        return packet

    def archive(self, tenant: str, sku: str, *, now_iso: str) -> Product:
        """Put a piece away. It leaves her list and stays in the history.

        Not a delete, and the difference is the whole feature: a mistyped
        piece is going to happen, and the answer to it must not be an
        operation that also destroys a real one. The SKU is not freed —
        `sku_high_water` already holds it, and a code read out on a phone
        call is spent.
        """
        piece = self.get(tenant, sku)
        if piece is None:
            raise ProductError(f"قطعه‌ای با کد «{sku}» پیدا نشد")
        if piece.archived_at:
            raise ProductError(f"«{sku}» از قبل بایگانی شده")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE products SET archived_at = ? "
                "WHERE tenant_id = ? AND sku = ? AND archived_at IS NULL",
                (now_iso, tenant, sku))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        out = self.get(tenant, sku)
        assert out is not None
        return out

    def unarchive(self, tenant: str, sku: str) -> Product:
        """Bring it back. Archiving is reversible; that is why it exists."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE products SET archived_at = NULL "
                "WHERE tenant_id = ? AND sku = ?", (tenant, sku))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        out = self.get(tenant, sku)
        if out is None:
            raise ProductError(f"قطعه‌ای با کد «{sku}» پیدا نشد")
        return out

    def photo_count(self, product_id: int) -> int:
        return self._conn.execute(
            "SELECT count(*) FROM product_photos WHERE product_id = ?",
            (product_id,)).fetchone()[0]

    # ── photos ────────────────────────────────────────────────────────────
    def attach_media(self, tenant: str, sku: str, position: int, *,
                     mime: str, byte_size: int, now_iso: str) -> None:
        """Record that a piece has a photo in this slot.

        Refuses a piece that does not exist, because a media row pointing at
        nothing is a file nothing will ever clean up — and for a photo of
        somebody's work that is a file nobody knows they still have.
        """
        if isinstance(position, bool) or not isinstance(position, int):
            raise ProductError(f"موقعیت باید عدد باشد: {position!r}")
        if not 0 <= position < MAX_PHOTOS_PER_PRODUCT:
            raise ProductError(
                f"هر قطعه حداکثر {MAX_PHOTOS_PER_PRODUCT} عکس می‌گیرد")
        if self.get(tenant, sku) is None:
            raise ProductError(f"قطعه‌ای با کد «{sku}» پیدا نشد")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO product_media (sku, tenant_id, position, mime, "
                "byte_size, added_at) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(tenant_id, sku, position) DO UPDATE SET "
                "mime = excluded.mime, byte_size = excluded.byte_size, "
                "added_at = excluded.added_at",
                (sku, tenant, position, mime, int(byte_size), now_iso))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def media_of(self, tenant: str, sku: str) -> list[int]:
        """Which slots are filled, in order."""
        return [int(r[0]) for r in self._conn.execute(
            "SELECT position FROM product_media WHERE tenant_id = ? "
            "AND sku = ? ORDER BY position", (tenant, sku))]

    def media_counts(self, tenant: str) -> dict[str, int]:
        """How many photos each piece has, for the list screen."""
        return {str(r[0]): int(r[1]) for r in self._conn.execute(
            "SELECT sku, COUNT(*) FROM product_media WHERE tenant_id = ? "
            "GROUP BY sku", (tenant,))}

    def recompute_cogs(self, tenant: str, sku: str) -> float:
        """Cost as the formula says it should be, from the row's own inputs.

        Exists because `cogs_aud` is a stored column rather than a generated
        one: this is how a test, or a suspicious owner, checks that what is
        filed agrees with what is beside it.
        """
        p = self.get(tenant, sku)
        if p is None:
            raise ProductError(f"محصولی با کد {sku} پیدا نشد")
        return cogs_for(
            {f: getattr(p, f) for f in EDITABLE if hasattr(p, f)},
            cost_fields=self._cost_fields,
            labour_hours_field=self._hours_field,
            labour_rate_field=self._rate_field)

    # ── writes ───────────────────────────────────────────────────────────
    def next_sku(self, tenant: str, prefix: str) -> str:
        """Next free code for this business, as `ZM-0001`.

        Taken from the high-water mark, not from the rows present. This used
        to read `MAX(sku)` over the table and claimed in its own docstring
        that "retiring a row never hands its code to a different piece" — a
        promise the query could not keep, because a deleted row is exactly
        the one it can no longer see. The first deletion would have reissued
        ZM-0001 while the ledger still described a different ZM-0001 under
        that name.

        The rows are still consulted, as a floor: a file whose high-water
        table was somehow lost or reset must not start handing out codes
        that are visibly in use.
        """
        row = self._conn.execute(
            "SELECT last FROM sku_high_water WHERE tenant_id = ?",
            (tenant,)).fetchone()
        top = int(row[0]) if row else 0
        for (sku,) in self._conn.execute(
                "SELECT sku FROM products WHERE tenant_id = ? AND sku LIKE ?",
                (tenant, f"{prefix}-%")).fetchall():
            tail = str(sku).rsplit("-", 1)[-1]
            if tail.isdigit():
                top = max(top, int(tail))
        return f"{prefix}-{top + 1:04d}"

    def _claim_sku(self, tenant: str, number: int) -> None:
        """Spend a number, so nothing can ever issue it again."""
        self._conn.execute(
            "INSERT INTO sku_high_water (tenant_id, last) VALUES (?, ?) "
            "ON CONFLICT(tenant_id) DO UPDATE SET last = MAX(last, excluded.last)",
            (tenant, number))

    def delete(self, tenant: str, sku: str) -> Product:
        """Remove a piece, and return what was removed.

        Returns the row rather than a bare acknowledgement so the caller can
        write down what disappeared. A deletion that leaves no description of
        what it deleted is the one operation this node must not have.

        The code is not freed. `sku_high_water` already holds it, and the
        ledger still describes it.
        """
        piece = self.get(tenant, sku)
        if piece is None:
            raise ProductError(f"قطعه‌ای با کد «{sku}» پیدا نشد")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "DELETE FROM product_photos WHERE product_id = ?", (piece.id,))
            self._conn.execute(
                "DELETE FROM products WHERE tenant_id = ? AND sku = ?",
                (tenant, sku))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return piece

    def create(self, tenant: str, prefix: str, fields: Mapping[str, Any],
               *, now_iso: str, environment: str = "production",
               source: str = "authenticated_panel",
               created_by: str = "authenticated_panel") -> Product:
        clean = _validated(fields, required=("name",))
        _reject_generic_sold(clean)
        _require_provenance(environment, source, created_by)
        _check_state(clean, prior=None)
        _stamp_dates(clean, prior=None, now_iso=now_iso)
        clean["cogs_aud"] = self._cogs(clean, prior=None)

        sku = self.next_sku(tenant, prefix)
        number = int(sku.rsplit("-", 1)[-1])
        cols = ["tenant_id", "sku", "environment", "source", "created_by",
                "created_at"] + list(clean)
        vals = [tenant, sku, environment, source, created_by, now_iso] + [
            clean[c] for c in clean]
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO products ({', '.join(cols)}) "
                f"VALUES ({', '.join('?' for _ in cols)})", vals)
            # Spent in the same transaction as the row, so a crash between
            # the two cannot leave a code issued but not recorded.
            self._claim_sku(tenant, number)
            self._conn.execute("COMMIT")
        except Exception as exc:        # constraint text is not for partners
            self._conn.execute("ROLLBACK")
            raise ProductError(_friendly(exc)) from None
        out = self.get(tenant, sku)
        assert out is not None
        return out

    def update(self, tenant: str, sku: str, changes: Mapping[str, Any],
               *, now_iso: str) -> tuple[Product, Product]:
        """Apply an edit, returning (before, after) for the ledger."""
        before = self.get(tenant, sku)
        if before is None:
            raise ProductError(f"محصولی با کد {sku} پیدا نشد")
        clean = _validated(changes, required=())
        if not clean:
            raise ProductError("چیزی برای تغییر نیست")
        _reject_generic_sold(clean)
        _check_state(clean, prior=before)
        _stamp_dates(clean, prior=before, now_iso=now_iso)
        clean["cogs_aud"] = self._cogs(clean, prior=before)

        sets = ", ".join(f"{c} = ?" for c in clean) + ", updated_at = ?"
        vals = [clean[c] for c in clean] + [now_iso, tenant, sku]
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(f"UPDATE products SET {sets} "
                               "WHERE tenant_id = ? AND sku = ?", vals)
            self._conn.execute("COMMIT")
        except Exception as exc:
            self._conn.execute("ROLLBACK")
            raise ProductError(_friendly(exc)) from None
        after = self.get(tenant, sku)
        assert after is not None
        return before, after

    def _cogs(self, clean: Mapping[str, Any], prior: Product | None) -> float:
        merged: dict[str, Any] = {}
        if prior is not None:
            merged.update({f: getattr(prior, f) for f in EDITABLE
                           if hasattr(prior, f)})
        merged.update(clean)
        return cogs_for(merged, cost_fields=self._cost_fields,
                        labour_hours_field=self._hours_field,
                        labour_rate_field=self._rate_field)


def _validated(fields: Mapping[str, Any], required: Sequence[str]
               ) -> dict[str, Any]:
    unknown = set(fields) - set(EDITABLE)
    if unknown:
        raise ProductError(f"فیلد ناشناخته: {', '.join(sorted(unknown))}")
    for r in required:
        if not str(fields.get(r, "")).strip():
            raise ProductError("نام محصول لازم است")

    clean: dict[str, Any] = {}
    for key, value in fields.items():
        if key in _NUMERIC:
            if value is None and key in _NULLABLE:
                clean[key] = None       # unpriced is a legitimate state
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ProductError(f"«{key}» باید عدد باشد")
            if value < 0:
                raise ProductError(f"«{key}» نمی‌تواند منفی باشد")
            clean[key] = float(value)
        else:
            clean[key] = None if value is None else str(value).strip() or None
    return clean


def _reject_generic_sold(clean: Mapping[str, Any]) -> None:
    if clean.get("state") == "sold":
        raise ProductError(
            "فروش فقط با record_sale ثبت می‌شود / sold state requires record_sale")


def _check_state(clean: Mapping[str, Any], prior: Product | None) -> None:
    state = clean.get("state") or (prior.state if prior else "in_progress")
    if state not in STATES:
        raise ProductError(f"وضعیت نامعتبر: {state}")
    channel = clean.get("channel", prior.channel if prior else None)
    if channel is not None and channel not in CHANNELS:
        raise ProductError(f"کانال نامعتبر: {channel}")
    if state == "sold" and not channel:
        # Without this the fee is unknowable, so the margin on the one event
        # that actually earned money would be the one number nobody has.
        raise ProductError("برای «فروخته شد» باید کانال فروش را بگویید")


def _stamp_dates(clean: dict[str, Any], prior: Product | None,
                 *, now_iso: str) -> None:
    """Set the two dates from the state change, so nobody has to remember to."""
    state = clean.get("state")
    if state is None:
        return
    was = prior.state if prior else None
    if state == "for_sale" and not (prior and prior.listed_at):
        clean.setdefault("listed_at", now_iso)
    if state == "sold" and not (prior and prior.sold_at):
        clean.setdefault("sold_at", now_iso)
        # Sold without ever having been listed: treat the sale day as the
        # listing day so "how long was it available" is 0 rather than absent.
        if not (prior and prior.listed_at):
            clean.setdefault("listed_at", now_iso)
    if was == state:
        return


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ProductError("timestamp is required")
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(
            text[:-1] + "+00:00" if text.endswith("Z") else text)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        raise ProductError(f"Invalid timestamp: {value}") from None


def _require_timestamp(name: str, value: str) -> None:
    try:
        _parse_timestamp(value)
    except ProductError:
        raise ProductError(f"{name} must be a valid ISO timestamp") from None


def _require_id(name: str, value: str) -> None:
    _require_text(name, value)


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProductError(f"{name} is required")


def _require_digest(name: str, value: str) -> None:
    _require_text(name, value)


def _require_channel(channel: str) -> None:
    if not channel:
        raise ProductError("channel is required")
    if channel not in CHANNELS:
        raise ProductError(f"Invalid channel: {channel}")


def _require_nonnegative_int(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProductError(f"{name} must be a nonnegative integer")


def _require_provenance(environment: str, source: str, created_by: str) -> None:
    if environment not in ENVIRONMENTS:
        raise ProductError(f"Invalid environment: {environment}")
    _require_text("source", source)
    _require_text("created_by", created_by)


def _sale_input_error(*, event_id: str, sku: str, sold_at: str, channel: str,
                      gross_cents: int | None, amount_unknown: bool,
                      fee_cents: int | None, fee_unknown: bool,
                      environment: str, source: str, created_by: str) -> str | None:
    try:
        _require_id("event_id", event_id)
        _require_id("sku", sku)
        _require_timestamp("sold_at", sold_at)
        _require_channel(channel)
        _require_provenance(environment, source, created_by)
        if not isinstance(amount_unknown, bool):
            raise ProductError("amount_unknown must be boolean")
        if not isinstance(fee_unknown, bool):
            raise ProductError("fee_unknown must be boolean")
        if gross_cents is not None:
            _require_nonnegative_int("gross_cents", gross_cents)
        if fee_cents is not None:
            _require_nonnegative_int("fee_cents", fee_cents)
        if (gross_cents is not None) == amount_unknown:
            raise ProductError("exactly one of gross_cents or amount_unknown is required")
        if (fee_cents is not None) == fee_unknown:
            raise ProductError("exactly one of fee_cents or fee_unknown is required")
    except ProductError as exc:
        return str(exc)
    return None


def _idempotent(row: Any, **identity: Any) -> dict:
    out = {"ok": True, "idempotent": True}
    out.update(identity)
    if "status" in row.keys():
        out["status"] = row["status"]
    return out


def _friendly(exc: Exception) -> str:
    text = str(exc).lower()
    if "unique" in text and "sku" in text:
        return "این کد محصول قبلاً استفاده شده"
    if "state" in text:
        return "وضعیت نامعتبر است"
    if "channel" in text:
        return "کانال فروش نامعتبر است"
    return "ذخیره نشد — مقادیر را بررسی کنید"
