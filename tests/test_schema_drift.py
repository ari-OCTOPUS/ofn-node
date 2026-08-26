"""Schema drift: a file that is older than the code that opens it.

Written after the failure it describes. `CREATE TABLE IF NOT EXISTS` is
idempotent about a table's existence and silent about its shape, so when the
two-price model was added to `products.SCHEMA` the file already on the board
kept its single `price_aud` column for ever. Nothing said so: the node booted
clean, and every test passed because every test builds its database from the
current schema in a fresh temporary directory — the one arrangement in which
drift cannot exist.

It surfaced as `sqlite3.OperationalError: no such column: price_primary_aud`,
raised inside a request, seconds after the partner's first successful login.

So these tests do the one thing the suite never did: create a database with
an *older* schema and then open it with today's code.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from ofn.adapters import products as P
from ofn.adapters.boot import SCHEMAS, BootSupervisor, Mode, Severity
from ofn.adapters.sqlite_base import (
    add_column_if_absent, apply_schema, connect, declared_columns,
    missing_columns,
)

# The products table exactly as it stood before the two-price change: one
# nullable `price_aud`, everything else identical. Kept verbatim rather than
# generated, because a fixture derived from the current schema could not have
# caught this.
OLD_PRODUCTS = """
CREATE TABLE products (
    id                  INTEGER PRIMARY KEY,
    tenant_id           TEXT    NOT NULL DEFAULT 'ziman',
    sku                 TEXT    NOT NULL,
    name                TEXT    NOT NULL,
    category            TEXT,
    description         TEXT,
    materials_cost_aud  REAL    NOT NULL DEFAULT 0,
    labour_hours        REAL    NOT NULL DEFAULT 0,
    hourly_rate_aud     REAL    NOT NULL DEFAULT 0,
    packaging_cost_aud  REAL    NOT NULL DEFAULT 0,
    cogs_aud            REAL    NOT NULL DEFAULT 0,
    price_aud           REAL,
    state               TEXT    NOT NULL DEFAULT 'in_progress',
    channel             TEXT,
    listed_at           TEXT,
    sold_at             TEXT,
    marketing_status    TEXT    NOT NULL DEFAULT 'not_started',
    marketing_notes     TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT
)
"""

# A once-current products table immediately before Shopify became a channel.
# It deliberately carries an unknown legacy column, non-schema index and
# trigger. The migration must alter only the channel CHECK and retain all of
# those, plus the child FK below.
FOUR_CHANNEL_PRODUCTS = """
CREATE TABLE products (
    id                  INTEGER PRIMARY KEY,
    tenant_id           TEXT    NOT NULL DEFAULT 'ziman',
    sku                 TEXT    NOT NULL,
    name                TEXT    NOT NULL,
    category            TEXT,
    description         TEXT,
    materials_cost_aud  REAL    NOT NULL DEFAULT 0,
    labour_hours        REAL    NOT NULL DEFAULT 0,
    hourly_rate_aud     REAL    NOT NULL DEFAULT 0,
    packaging_cost_aud  REAL    NOT NULL DEFAULT 0,
    cogs_aud            REAL    NOT NULL DEFAULT 0,
    price_primary_aud   REAL,
    price_secondary_aud REAL,
    state               TEXT    NOT NULL DEFAULT 'in_progress'
                              CHECK (state IN ('in_progress', 'for_sale',
                                     'sold', 'gifted')),
    channel             TEXT
                              CHECK (channel IS NULL OR channel IN
                                     ('instagram', 'market', 'etsy', 'direct')),
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
    archived_at         TEXT,
    legacy_note         TEXT    NOT NULL DEFAULT 'kept'
)
"""


class Tmp(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._dir.name, "products.sqlite")

    def tearDown(self):
        self._dir.cleanup()

    def write_old_file(self, *rows):
        """A products database as it existed before the schema changed."""
        conn = sqlite3.connect(self.path)
        conn.execute(OLD_PRODUCTS)
        for sku, price in rows:
            conn.execute("INSERT INTO products (tenant_id, sku, name, price_aud) "
                         "VALUES ('ziman', ?, ?, ?)", (sku, sku, price))
        conn.commit()
        conn.close()

    def write_four_channel_file(self):
        """A real pre-Shopify row with objects and a child FK to preserve."""
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(FOUR_CHANNEL_PRODUCTS)
        conn.execute(
            "CREATE UNIQUE INDEX products_sku ON products (tenant_id, sku)")
        conn.execute(
            "CREATE INDEX legacy_products_note ON products (legacy_note)")
        conn.execute(
            "CREATE TABLE legacy_listing ("
            " listing_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL,"
            " sku TEXT NOT NULL, note TEXT NOT NULL,"
            " FOREIGN KEY (tenant_id, sku)"
            " REFERENCES products (tenant_id, sku))")
        conn.execute(
            "CREATE TABLE legacy_product_audit (sku TEXT NOT NULL, name TEXT NOT NULL)")
        conn.execute(
            "CREATE TRIGGER legacy_products_name AFTER UPDATE OF name ON products "
            "BEGIN INSERT INTO legacy_product_audit (sku, name) "
            "VALUES (NEW.sku, NEW.name); END")
        conn.execute(
            "INSERT INTO products (tenant_id, sku, name, state, legacy_note) "
            "VALUES ('ziman', 'ZM-0042', 'legacy piece', 'for_sale', 'do not drop')")
        conn.execute(
            "INSERT INTO legacy_listing (listing_id, tenant_id, sku, note) "
            "VALUES ('listing-1', 'ziman', 'ZM-0042', 'child stays')")
        conn.commit()
        conn.close()


class TestDriftIsDetected(Tmp):
    def test_an_old_file_reports_the_columns_it_lacks(self):
        self.write_old_file()
        conn = connect(self.path)
        try:
            gap = missing_columns(conn, P.SCHEMA)
        finally:
            conn.close()
        # Grows as columns are added. That is the point: the fixture is the
        # schema as it stood before, frozen, and every later addition shows
        # up here — which is exactly what a drift detector is for. The last
        # three entries are the provenance columns that now disqualify a row
        # from being counted as a real sale.
        self.assertEqual(sorted(gap["products"]),
                         ["archived_at", "created_by", "environment",
                          "price_primary_aud", "price_secondary_aud",
                          "source"])

    def test_a_current_file_reports_nothing(self):
        store = P.ProductStore(self.path, cost_fields=("materials_cost_aud",),
                               labour_hours_field="labour_hours",
                               labour_rate_field="hourly_rate_aud")
        store.close()
        conn = connect(self.path)
        try:
            self.assertEqual(missing_columns(conn, P.SCHEMA), {})
        finally:
            conn.close()

    def test_declared_columns_reads_the_schema_sqlite_would_build(self):
        """Not a regex over the CREATE TABLE text — the real thing.

        The schema carries comments, CHECK constraints and defaults that call
        functions. Anything less than SQLite parsing it is a second parser
        that will disagree eventually.
        """
        declared = declared_columns(P.SCHEMA)
        self.assertIn("products", declared)
        self.assertIn("price_secondary_aud", declared["products"])
        self.assertIn("product_photos", declared)

    def test_a_table_absent_from_the_file_is_not_reported_as_drift(self):
        """A store that has never been opened is not behind — it is empty."""
        conn = connect(self.path)
        try:
            self.assertEqual(missing_columns(conn, P.SCHEMA), {})
        finally:
            conn.close()


class TestMigrationCarriesTheFileForward(Tmp):
    def test_opening_an_old_file_adds_the_missing_columns(self):
        self.write_old_file()
        store = P.ProductStore(self.path, cost_fields=("materials_cost_aud",),
                               labour_hours_field="labour_hours",
                               labour_rate_field="hourly_rate_aud")
        try:
            # The query that raised in production. It is the assertion.
            store.list("ziman")
        finally:
            store.close()

    def test_the_old_price_becomes_the_primary_one(self):
        """It was the listed price, which is what `primary` means."""
        self.write_old_file(("A-1", 120.0), ("A-2", None))
        store = P.ProductStore(self.path, cost_fields=("materials_cost_aud",),
                               labour_hours_field="labour_hours",
                               labour_rate_field="hourly_rate_aud")
        try:
            by_sku = {p.sku: p for p in store.list("ziman")}
        finally:
            store.close()
        self.assertEqual(by_sku["A-1"].price_primary_aud, 120.0)
        self.assertIsNone(by_sku["A-2"].price_primary_aud)

    def test_the_floor_price_is_not_invented(self):
        """Nobody knows what she will actually take. Guessing it would put a
        number she never said underneath every margin judgement."""
        self.write_old_file(("A-1", 120.0))
        store = P.ProductStore(self.path, cost_fields=("materials_cost_aud",),
                               labour_hours_field="labour_hours",
                               labour_rate_field="hourly_rate_aud")
        try:
            self.assertIsNone(store.list("ziman")[0].price_secondary_aud)
        finally:
            store.close()

    def test_running_it_twice_changes_nothing(self):
        """Migrations run on every boot, so the second run must be a no-op."""
        self.write_old_file(("A-1", 120.0))
        for _ in range(3):
            store = P.ProductStore(self.path, cost_fields=("materials_cost_aud",),
                                   labour_hours_field="labour_hours",
                                   labour_rate_field="hourly_rate_aud")
            rows = store.list("ziman")
            store.close()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].price_primary_aud, 120.0)

    def test_a_value_already_migrated_is_not_overwritten(self):
        """The backfill fires once. If a later edit set a primary price, a
        second boot must not push the legacy value back over it."""
        self.write_old_file(("A-1", 120.0))
        conn = sqlite3.connect(self.path)
        add_column_if_absent(conn, "products", "price_primary_aud", "REAL")
        conn.execute("UPDATE products SET price_primary_aud = 99.0")
        conn.commit()
        conn.close()

        store = P.ProductStore(self.path, cost_fields=("materials_cost_aud",),
                               labour_hours_field="labour_hours",
                               labour_rate_field="hourly_rate_aud")
        try:
            self.assertEqual(store.list("ziman")[0].price_primary_aud, 99.0)
        finally:
            store.close()

    def test_add_column_if_absent_is_idempotent(self):
        self.write_old_file()
        conn = sqlite3.connect(self.path)
        try:
            add_column_if_absent(conn, "products", "extra_col", "REAL")
            add_column_if_absent(conn, "products", "extra_col", "REAL")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(products)")}
        finally:
            conn.close()
        self.assertIn("extra_col", cols)

    def test_a_failing_migration_leaves_the_file_untouched(self):
        """Creates and migrations share one transaction, so a half-applied
        schema is not a state this node can be found in."""
        self.write_old_file()
        conn = connect(self.path)

        def explode(_):
            raise RuntimeError("no")

        try:
            with self.assertRaises(RuntimeError):
                apply_schema(conn, P.SCHEMA, (explode,))
            cols = {r[1] for r in conn.execute("PRAGMA table_info(products)")}
        finally:
            conn.close()
        self.assertNotIn("price_primary_aud", cols)


class TestShopifyChannelCheckMigration(Tmp):
    def open_store(self):
        return P.ProductStore(
            self.path, cost_fields=("materials_cost_aud",),
            labour_hours_field="labour_hours",
            labour_rate_field="hourly_rate_aud")

    def catalog_snapshot(self):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            ).fetchall()
        finally:
            conn.close()

    def test_open_rebuilds_old_check_and_preserves_everything(self):
        self.write_four_channel_file()
        store = self.open_store()
        try:
            self.assertEqual(store._conn.execute(
                "PRAGMA foreign_keys").fetchone()[0], 1)
            sale = store.record_sale(
                "ziman", "ZM-0042", event_id="sale-shopify",
                sold_at="2026-08-26T10:00:00Z", channel="shopify",
                amount_unknown=True, fee_unknown=True,
                now_iso="2026-08-26T10:00:00Z")
            self.assertTrue(sale["ok"])
            self.assertEqual(store.get("ziman", "ZM-0042").channel, "shopify")
            self.assertEqual(store._conn.execute(
                "SELECT note FROM legacy_listing WHERE listing_id = 'listing-1'"
            ).fetchone()[0], "child stays")
            self.assertEqual(store._conn.execute(
                "SELECT legacy_note FROM products WHERE sku = 'ZM-0042'"
            ).fetchone()[0], "do not drop")
            self.assertEqual(store._conn.execute(
                "PRAGMA foreign_key_check").fetchall(), [])
            names = {r[0] for r in store._conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('index','trigger')")}
            self.assertIn("legacy_products_note", names)
            self.assertIn("legacy_products_name", names)
            store._conn.execute(
                "UPDATE products SET name = 'renamed' WHERE sku = 'ZM-0042'")
            self.assertEqual(store._conn.execute(
                "SELECT name FROM legacy_product_audit").fetchone()[0], "renamed")
            product_sql = store._conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' "
                "AND name = 'products'").fetchone()[0]
            self.assertIn("'direct', 'shopify'", product_sql)
            self.assertNotIn("products_new", product_sql)
        finally:
            store.close()

    def test_second_run_is_a_catalog_noop(self):
        self.write_four_channel_file()
        first = self.open_store()
        first.close()
        before = self.catalog_snapshot()
        second = self.open_store()
        second.close()
        self.assertEqual(self.catalog_snapshot(), before)

    def test_fresh_current_and_no_check_files_are_noops(self):
        conn = connect(self.path)
        try:
            P._migrate_products_channel_check(conn)
            self.assertEqual(conn.execute(
                "SELECT count(*) FROM sqlite_master").fetchone()[0], 0)
        finally:
            conn.close()

        store = self.open_store()
        store.close()
        before = self.catalog_snapshot()
        conn = connect(self.path)
        try:
            P._migrate_products_channel_check(conn)
        finally:
            conn.close()
        self.assertEqual(self.catalog_snapshot(), before)

        os.unlink(self.path)
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, channel TEXT)")
        conn.execute("INSERT INTO products (channel) VALUES ('legacy-channel')")
        conn.commit()
        conn.close()
        before = self.catalog_snapshot()
        conn = connect(self.path)
        try:
            P._migrate_products_channel_check(conn)
        finally:
            conn.close()
        self.assertEqual(self.catalog_snapshot(), before)

    def test_products_new_collision_is_not_touched(self):
        self.write_four_channel_file()
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE products_new (sentinel TEXT)")
        conn.execute("INSERT INTO products_new VALUES ('keep me')")
        conn.commit()
        conn.close()

        store = self.open_store()
        try:
            self.assertEqual(store._conn.execute(
                "SELECT sentinel FROM products_new").fetchone()[0], "keep me")
            self.assertIsNone(store._conn.execute(
                "SELECT 1 FROM sqlite_master WHERE name = 'products_new_1'"
            ).fetchone())
        finally:
            store.close()

    def test_success_enables_foreign_keys_even_if_caller_had_them_off(self):
        self.write_four_channel_file()
        conn = connect(self.path)
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            P._migrate_products_channel_check(conn)
            self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            conn.close()

    def test_failure_rolls_back_and_restores_foreign_keys(self):
        self.write_four_channel_file()
        conn = connect(self.path)
        original_execute = conn.execute

        class FailingConnection:
            @property
            def in_transaction(self):
                return conn.in_transaction

            def execute(self, sql, parameters=()):
                if sql.startswith("ALTER TABLE"):
                    raise RuntimeError("injected rebuild failure")
                return original_execute(sql, parameters)

        try:
            with self.assertRaisesRegex(RuntimeError, "injected rebuild failure"):
                P._migrate_products_channel_check(FailingConnection())
            self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(tuple(conn.execute(
                "SELECT name, legacy_note FROM products WHERE sku = 'ZM-0042'"
            ).fetchone()), ("legacy piece", "do not drop"))
            self.assertEqual(conn.execute(
                "SELECT note FROM legacy_listing").fetchone()[0], "child stays")
            self.assertIsNone(conn.execute(
                "SELECT 1 FROM sqlite_master WHERE name LIKE 'products_new%'"
            ).fetchone())
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            conn.close()


class TestBootRefusesToRunOnADriftedFile(Tmp):
    def supervise(self):
        sup = BootSupervisor(db_paths={"products": self.path}, tenants=[],
                             now_epoch_s=lambda: 1_800_000_000,
                             state_dir=os.path.dirname(self.path))
        return sup.run()

    def test_a_file_a_migration_can_fix_is_fixed_and_boots_normally(self):
        """Pre-flight runs before the node opens its stores, so a pending
        migration is not a fault — it is work not yet done. Reporting it as
        CRITICAL would put a healthy node into SAFE MODE for a condition it
        was about to resolve on its own."""
        self.write_old_file(("A-1", 120.0))
        rep = self.supervise()
        check = next(c for c in rep.checks if c.name == "schema:products")
        self.assertIs(check.severity, Severity.OK)
        self.assertIs(rep.mode, Mode.NORMAL)

        conn = connect(self.path)
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(products)")}
        finally:
            conn.close()
        self.assertIn("price_primary_aud", cols)

    def test_drift_with_no_migration_is_critical_and_forces_safe_mode(self):
        """Failing here is failing in front of the operator. The alternative
        is failing in front of a partner, mid-request, which is how this got
        written."""
        self.write_old_file()
        conn = sqlite3.connect(self.path)
        conn.execute("ALTER TABLE products DROP COLUMN marketing_notes")
        conn.commit()
        conn.close()

        rep = self.supervise()
        check = next(c for c in rep.checks if c.name == "schema:products")
        self.assertIs(check.severity, Severity.CRITICAL)
        self.assertIn("marketing_notes", check.detail)
        self.assertIs(rep.mode, Mode.SAFE)

    def test_a_migrated_file_boots_normally(self):
        self.write_old_file()
        store = P.ProductStore(self.path, cost_fields=("materials_cost_aud",),
                               labour_hours_field="labour_hours",
                               labour_rate_field="hourly_rate_aud")
        store.close()
        rep = self.supervise()
        check = next(c for c in rep.checks if c.name == "schema:products")
        self.assertIs(check.severity, Severity.OK)
        self.assertIs(rep.mode, Mode.NORMAL)

    def test_every_checked_store_has_a_schema_registered(self):
        """A store missing from `SCHEMAS` is silently unchecked — exactly the
        kind of gap this whole file exists because of."""
        from ofn import config
        cfg = config.load()
        self.assertEqual(set(cfg.db_paths), set(SCHEMAS))


if __name__ == "__main__":
    unittest.main()
