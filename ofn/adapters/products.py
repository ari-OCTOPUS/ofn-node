"""Product records — one row per thing Maliheh makes.

Separate database file from facts/ledger/outbox, same durability policy. A
product is not a fact: facts are what the business knows about itself and
carry validity over time, while a product is a row that gets edited. Mixing
them would put a shape with a lifecycle into a store built for statements.

Two rules here are worth stating because both are easy to get wrong and
expensive to discover later:

  * `hourly_rate_aud` is COPIED into the row at save time, never read live
    from the business's current rate. When she raises her rate from $25 to
    $35, last month's product must not silently become loss-making. It was
    profitable at the rate that applied, and the record has to keep saying so.

  * `cogs_aud` is computed by SQLite from the row's own columns, so there is
    no way to store a cost that disagrees with the inputs beside it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .sqlite_base import Pool, apply_schema

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS products (
        id                       INTEGER PRIMARY KEY,
        tenant_id                TEXT    NOT NULL DEFAULT 'ziman',
        sku                      TEXT    NOT NULL,
        name                     TEXT    NOT NULL,
        category                 TEXT,
        description              TEXT,

        batch_materials_cost_aud REAL    NOT NULL DEFAULT 0,
        batch_size               INTEGER NOT NULL DEFAULT 1
                                   CHECK (batch_size > 0),
        labour_hours             REAL    NOT NULL DEFAULT 0,
        -- Copied from the business's rate at save time. Deliberately not a
        -- lookup: see the module docstring.
        hourly_rate_aud          REAL    NOT NULL DEFAULT 0,
        packaging_cost_aud       REAL    NOT NULL DEFAULT 0,

        cogs_aud                 REAL GENERATED ALWAYS AS (
                                   batch_materials_cost_aud / batch_size
                                   + (labour_hours * hourly_rate_aud)
                                   + packaging_cost_aud
                                 ) STORED,

        -- Nullable on purpose. Nobody, including this system, invents a
        -- price for her.
        price_aud                REAL,
        stock_qty                INTEGER NOT NULL DEFAULT 0,

        status                   TEXT    NOT NULL DEFAULT 'draft'
                                   CHECK (status IN ('draft', 'ready',
                                          'listed', 'sold_out', 'archived')),
        marketing_status         TEXT    NOT NULL DEFAULT 'not_started'
                                   CHECK (marketing_status IN ('not_started',
                                          'photo_done', 'caption_done',
                                          'posted')),
        marketing_notes          TEXT,

        created_at               TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at               TEXT
    )
    """,
    # Photos land tomorrow, but the table is created tonight so that evening
    # is a feature and not a migration.
    """
    CREATE TABLE IF NOT EXISTS product_photos (
        id            INTEGER PRIMARY KEY,
        product_id    INTEGER NOT NULL
                        REFERENCES products (id) ON DELETE CASCADE,
        -- The bytes as her phone produced them. Never deleted, never
        -- re-encoded: a handmade item that has been sold cannot be
        -- photographed again.
        original_path TEXT    NOT NULL,
        -- A long-edge-1600 copy for display, made on the phone.
        display_path  TEXT    NOT NULL,
        mime          TEXT    NOT NULL DEFAULT 'image/jpeg',
        byte_size     INTEGER NOT NULL DEFAULT 0,
        position      INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS products_sku "
    "ON products (tenant_id, sku)",
    "CREATE INDEX IF NOT EXISTS products_tenant ON products (tenant_id)",
    "CREATE INDEX IF NOT EXISTS products_tenant_status "
    "ON products (tenant_id, status)",
    "CREATE UNIQUE INDEX IF NOT EXISTS product_photos_slot "
    "ON product_photos (product_id, position)",
    "CREATE INDEX IF NOT EXISTS product_photos_product "
    "ON product_photos (product_id)",
)

MAX_PHOTOS_PER_PRODUCT = 5

# Columns a partner may set. Everything outside this set is either computed
# (`cogs_aud`), assigned (`sku`, `id`), or timekeeping.
EDITABLE: tuple[str, ...] = (
    "name", "category", "description",
    "batch_materials_cost_aud", "batch_size", "labour_hours",
    "hourly_rate_aud", "packaging_cost_aud",
    "price_aud", "stock_qty",
    "status", "marketing_status", "marketing_notes",
)

_NUMERIC = {"batch_materials_cost_aud", "batch_size", "labour_hours",
            "hourly_rate_aud", "packaging_cost_aud", "price_aud", "stock_qty"}


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
    batch_materials_cost_aud: float
    batch_size: int
    labour_hours: float
    hourly_rate_aud: float
    packaging_cost_aud: float
    cogs_aud: float
    price_aud: float | None
    stock_qty: int
    status: str
    marketing_status: str
    marketing_notes: str | None
    created_at: str
    updated_at: str | None

    # ── the three numbers the shell shows under the price field ──────────
    @property
    def margin_aud(self) -> float | None:
        return None if self.price_aud is None else self.price_aud - self.cogs_aud

    @property
    def margin_pct(self) -> float | None:
        if not self.price_aud:
            return None
        return (self.price_aud - self.cogs_aud) / self.price_aud

    @property
    def loses_money(self) -> bool:
        """True only when a price exists and is below cost. An unpriced
        product is not losing money — it is unpriced, which is a different
        thing and must not wear a red warning."""
        return self.price_aud is not None and self.price_aud < self.cogs_aud

    def as_dict(self) -> dict[str, Any]:
        d = {f: getattr(self, f) for f in self.__dataclass_fields__}
        d["margin_aud"] = self.margin_aud
        d["margin_pct"] = self.margin_pct
        d["loses_money"] = self.loses_money
        return d


def _to_product(row) -> Product:
    return Product(*row)


_COLUMNS = ("id, tenant_id, sku, name, category, description, "
            "batch_materials_cost_aud, batch_size, labour_hours, "
            "hourly_rate_aud, packaging_cost_aud, cogs_aud, price_aud, "
            "stock_qty, status, marketing_status, marketing_notes, "
            "created_at, updated_at")


class ProductStore:
    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA)

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
        return _to_product(row) if row else None

    def list(self, tenant: str, *, include_archived: bool = False
             ) -> list[Product]:
        sql = f"SELECT {_COLUMNS} FROM products WHERE tenant_id = ?"
        if not include_archived:
            sql += " AND status != 'archived'"
        sql += " ORDER BY id"
        return [_to_product(r) for r in self._conn.execute(sql, (tenant,))]

    def photo_count(self, product_id: int) -> int:
        return self._conn.execute(
            "SELECT count(*) FROM product_photos WHERE product_id = ?",
            (product_id,)).fetchone()[0]

    # ── writes ───────────────────────────────────────────────────────────
    def next_sku(self, tenant: str, prefix: str) -> str:
        """Next free code for this business, as `ZM-0001`.

        Derived from the highest number already used rather than a count, so
        deleting a row never hands its code to a different product.
        """
        rows = self._conn.execute(
            "SELECT sku FROM products WHERE tenant_id = ? AND sku LIKE ?",
            (tenant, f"{prefix}-%")).fetchall()
        top = 0
        for (sku,) in rows:
            tail = sku.rsplit("-", 1)[-1]
            if tail.isdigit():
                top = max(top, int(tail))
        return f"{prefix}-{top + 1:04d}"

    def create(self, tenant: str, prefix: str, fields: Mapping[str, Any],
               *, now_iso: str) -> Product:
        clean = _validated(fields, required=("name",))
        sku = self.next_sku(tenant, prefix)
        cols = ["tenant_id", "sku", "created_at"] + list(clean)
        vals = [tenant, sku, now_iso] + [clean[c] for c in clean]
        placeholders = ", ".join("?" for _ in cols)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO products ({', '.join(cols)}) "
                f"VALUES ({placeholders})", vals)
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
            if value is None and key == "price_aud":
                clean[key] = None       # unpriced is a legitimate state
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ProductError(f"«{key}» باید عدد باشد")
            if value < 0:
                raise ProductError(f"«{key}» نمی‌تواند منفی باشد")
            clean[key] = int(value) if key in ("batch_size", "stock_qty") \
                else float(value)
        else:
            clean[key] = None if value is None else str(value).strip()
    if clean.get("batch_size") == 0:
        # SQLite returns NULL for x/0 rather than raising, so without this a
        # zero batch would store a product whose cost is simply missing.
        raise ProductError("اندازهٔ دسته باید حداقل ۱ باشد")
    return clean


def _friendly(exc: Exception) -> str:
    text = str(exc).lower()
    if "unique" in text and "sku" in text:
        return "این کد محصول قبلاً استفاده شده"
    if "batch_size" in text:
        return "اندازهٔ دسته باید حداقل ۱ باشد"
    if "status" in text:
        return "وضعیت نامعتبر است"
    return "ذخیره نشد — مقادیر را بررسی کنید"
