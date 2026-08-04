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
        # up here — which is exactly what a drift detector is for.
        self.assertEqual(sorted(gap["products"]),
                         ["archived_at", "price_primary_aud",
                          "price_secondary_aud"])

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
