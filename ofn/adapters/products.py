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
from datetime import date
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


MIGRATIONS = (_split_price_into_two, _seed_sku_high_water)

MAX_PHOTOS_PER_PRODUCT = 5
STATES = ("in_progress", "for_sale", "sold", "gifted")
CHANNELS = ("instagram", "market", "etsy", "direct")

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


def money_view(p: Product, *, gst_rate: float,
               gst_known: bool) -> dict[str, Any]:
    """The money numbers as they may be shown, given what we know about tax.

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
    """
    price = p.judged_price_aud
    rate = gst_rate if gst_known else 0.0
    net = None if price is None else price / (1.0 + rate)
    return {
        "judged_price_aud": price,
        "price_ex_tax_aud": net,
        "margin_aud": None if net is None else net - p.cogs_aud,
        "margin_pct": None if not net else (net - p.cogs_aud) / net,
        "loses_money": net is not None and net < p.cogs_aud,
        "gst_known": gst_known,
        "gst_rate": rate,
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
        apply_schema(self._conn, SCHEMA, MIGRATIONS)

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
               *, now_iso: str) -> Product:
        clean = _validated(fields, required=("name",))
        _check_state(clean, prior=None)
        _stamp_dates(clean, prior=None, now_iso=now_iso)
        clean["cogs_aud"] = self._cogs(clean, prior=None)

        sku = self.next_sku(tenant, prefix)
        number = int(sku.rsplit("-", 1)[-1])
        cols = ["tenant_id", "sku", "created_at"] + list(clean)
        vals = [tenant, sku, now_iso] + [clean[c] for c in clean]
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
