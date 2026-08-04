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
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence

from .sqlite_base import Pool, apply_schema

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

        -- Nullable on purpose. Nobody, including this system, invents a
        -- price for her.
        price_aud           REAL,

        state               TEXT    NOT NULL DEFAULT 'in_progress'
                              CHECK (state IN ('in_progress', 'for_sale',
                                     'sold', 'gifted')),
        -- Where it sold. Null until it does.
        channel             TEXT
                              CHECK (channel IS NULL OR channel IN
                                     ('instagram', 'market', 'etsy', 'direct')),
        listed_at           TEXT,
        sold_at             TEXT,

        marketing_status    TEXT    NOT NULL DEFAULT 'not_started'
                              CHECK (marketing_status IN ('not_started',
                                     'photo_done', 'caption_done', 'posted')),
        marketing_notes     TEXT,

        created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at          TEXT
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
    "CREATE UNIQUE INDEX IF NOT EXISTS products_sku "
    "ON products (tenant_id, sku)",
    "CREATE INDEX IF NOT EXISTS products_tenant ON products (tenant_id)",
    "CREATE INDEX IF NOT EXISTS products_tenant_state "
    "ON products (tenant_id, state)",
    "CREATE UNIQUE INDEX IF NOT EXISTS product_photos_slot "
    "ON product_photos (product_id, position)",
    "CREATE INDEX IF NOT EXISTS product_photos_product "
    "ON product_photos (product_id)",
)

MAX_PHOTOS_PER_PRODUCT = 5
STATES = ("in_progress", "for_sale", "sold", "gifted")
CHANNELS = ("instagram", "market", "etsy", "direct")

# Verdict names. Deliberately three, matching the three things worth saying.
LOSES_MONEY = "loses_money"    # priced under cost
STALE = "stale"                # listed a long time ago and still here
QUICK_SALE = "quick_sale"      # gone fast — make another like it

EDITABLE: tuple[str, ...] = (
    "name", "category", "description",
    "materials_cost_aud", "labour_hours", "hourly_rate_aud",
    "packaging_cost_aud", "price_aud",
    "state", "channel", "listed_at", "sold_at",
    "marketing_status", "marketing_notes",
)

_NUMERIC = {"materials_cost_aud", "labour_hours", "hourly_rate_aud",
            "packaging_cost_aud", "price_aud"}


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
    price_aud: float | None
    state: str
    channel: str | None
    listed_at: str | None
    sold_at: str | None
    marketing_status: str
    marketing_notes: str | None
    created_at: str
    updated_at: str | None

    @property
    def gross_margin_aud(self) -> float | None:
        """Price minus cost, before any platform takes its cut."""
        return None if self.price_aud is None else self.price_aud - self.cogs_aud

    @property
    def gross_margin_pct(self) -> float | None:
        if not self.price_aud:
            return None
        return (self.price_aud - self.cogs_aud) / self.price_aud

    @property
    def loses_money(self) -> bool:
        """True only when a price exists and is below cost. An unpriced piece
        is not losing money — it is unpriced, which is a different thing and
        must not wear a red warning."""
        return self.price_aud is not None and self.price_aud < self.cogs_aud

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

    The shape is fixed — a sum of costs and one hours×rate term — and the
    *names* come from the pack. That covers a business whose costs are
    materials and packaging and one whose costs are materials and travel,
    without this module knowing what either sells. It is not an expression
    evaluator, and it should not become one: a formula language in a config
    file is a way to run arbitrary arithmetic nobody reviewed.
    """
    total = 0.0
    for name in cost_fields:
        total += float(fields.get(name) or 0.0)
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
    """Margin after the channel's cut. None while unpriced."""
    if p.price_aud is None:
        return None
    return p.price_aud - channel_fee(p.price_aud, p.channel, fees) - p.cogs_aud


def verdicts(p: Product, today: str, *, stale_after_days: int,
             quick_sale_days: int) -> tuple[str, ...]:
    """The short list of things worth saying about one piece."""
    out: list[str] = []
    if p.loses_money:
        out.append(LOSES_MONEY)
    age = p.days_on_sale(today)
    if age is not None:
        if p.state == "for_sale" and age > stale_after_days:
            out.append(STALE)
        elif p.state == "sold" and age < quick_sale_days:
            out.append(QUICK_SALE)
    return tuple(out)


_COLUMNS = ("id, tenant_id, sku, name, category, description, "
            "materials_cost_aud, labour_hours, hourly_rate_aud, "
            "packaging_cost_aud, cogs_aud, price_aud, state, channel, "
            "listed_at, sold_at, marketing_status, marketing_notes, "
            "created_at, updated_at")


class ProductStore:
    def __init__(self, path: str, *, cost_fields: Sequence[str],
                 labour_hours_field: str, labour_rate_field: str) -> None:
        # The formula's field names arrive from the pack and are held here so
        # every write goes through the same one.
        self._cost_fields = tuple(cost_fields)
        self._hours_field = labour_hours_field
        self._rate_field = labour_rate_field
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
        return Product(*row) if row else None

    def list(self, tenant: str) -> list[Product]:
        return [Product(*r) for r in self._conn.execute(
            f"SELECT {_COLUMNS} FROM products WHERE tenant_id = ? "
            "ORDER BY id", (tenant,))]

    def photo_count(self, product_id: int) -> int:
        return self._conn.execute(
            "SELECT count(*) FROM product_photos WHERE product_id = ?",
            (product_id,)).fetchone()[0]

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

        Derived from the highest number already used rather than a count, so
        retiring a row never hands its code to a different piece.
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
        _check_state(clean, prior=None)
        _stamp_dates(clean, prior=None, now_iso=now_iso)
        clean["cogs_aud"] = self._cogs(clean, prior=None)

        sku = self.next_sku(tenant, prefix)
        cols = ["tenant_id", "sku", "created_at"] + list(clean)
        vals = [tenant, sku, now_iso] + [clean[c] for c in clean]
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                f"INSERT INTO products ({', '.join(cols)}) "
                f"VALUES ({', '.join('?' for _ in cols)})", vals)
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
            if value is None and key == "price_aud":
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


def _friendly(exc: Exception) -> str:
    text = str(exc).lower()
    if "unique" in text and "sku" in text:
        return "این کد محصول قبلاً استفاده شده"
    if "state" in text:
        return "وضعیت نامعتبر است"
    if "channel" in text:
        return "کانال فروش نامعتبر است"
    return "ذخیره نشد — مقادیر را بررسی کنید"
