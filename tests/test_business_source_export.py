"""The business-source export: read-only, PII-free, deterministic.

These tests exist to keep three promises the export makes. That no byte of
a person's name, phone, email, message or source reference can appear in a
snapshot. That the source databases are opened read-only and left exactly
as found — same size, same mtime, same hash. And that the same inputs
produce the same file, which is what makes one snapshot comparable to the
next.

The source files are built with plain `sqlite3` and the stores' own SCHEMA
constants, not through the store classes: the export must work against the
file as it lies on disk, including files written by older versions of the
stores (the legacy-drift test) and files with junk in them (the malformed
row).
"""

import hashlib
import json
import os
import sqlite3
import unittest
from pathlib import Path

from ofn.adapters.business_source_export import (
    SCHEMA_NAME,
    SOURCE_NODE,
    UNKNOWN_MARKER,
    WARNING_SCHEMA_NAME,
    export_business_sources,
    load_export,
)
from ofn.adapters.lead_store import SCHEMA as PAINTING_SCHEMA
from ofn.adapters.products import SCHEMA as PRODUCTS_SCHEMA
from tests.tmpdir import temp_dir

NOW = "2026-08-28T00:00:00Z"
SNAP = "snap-0001"

LINE_KEYS = {
    "schema", "source_node", "lane", "internal_id_hash", "fields",
    "observed_at_utc", "source_row_hash", "may_contact", "pii_redacted",
}
HEX64 = "0123456789abcdef"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical(row: dict) -> str:
    """The export's own canonical form, mirrored here so the tests pin it:
    sorted keys, no spaces, no NaN, real UTF-8 characters."""
    return json.dumps(row, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def source_row(path: str, table: str, where: str, value) -> dict:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {table} WHERE {where} = ?", (value,)).fetchone()
        return dict(row)
    finally:
        conn.close()


class Base(unittest.TestCase):
    def setUp(self):
        d = temp_dir(self)
        self.painting = os.path.join(d, "painting.sqlite")
        self.ziman = os.path.join(d, "products.sqlite")
        self.out = Path(d) / "out"
        self.paths = {"painting": self.painting, "ziman": self.ziman}

    def make_db(self, path: str, schema, insert_sql: str, rows) -> None:
        conn = sqlite3.connect(path)
        try:
            for stmt in schema:
                conn.execute(stmt)
            if rows:
                conn.executemany(insert_sql, rows)
            conn.commit()
        finally:
            conn.close()

    def export(self, lane="painting", *, now=NOW, snap=SNAP) -> Path:
        return export_business_sources(self.paths, lane, self.out,
                                       now_utc=now, snapshot_id=snap)


def painting_insert(lead_id, *, name="Sarah Cameron", phone="0412 345 678",
                    email="sarah@example.com", suburb="Newtown",
                    job_type="exterior repaint", rooms="4",
                    budget="about 4000", message="please call me urgently",
                    source_ref="https://ref.example/lead/99", score=80,
                    follow_ups=1):
    return (lead_id, "lead", "website", source_ref, name, phone, email,
            suburb, job_type, rooms, budget, message, score, "hot", "new",
            "call today", follow_ups, NOW, NOW)


PAINTING_SQL = (
    "INSERT INTO painting_leads (lead_id, tenant_id, source, source_ref, "
    "customer_name, phone, email, suburb, job_type, rooms, budget_text, "
    "message, score, temperature, status, next_action, follow_up_count, "
    "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


class PaintingExportTests(Base):
    def test_redacts_pii_and_hashes_identity(self):
        self.make_db(self.painting, PAINTING_SCHEMA, PAINTING_SQL, [
            painting_insert("lead:web-1"),
            painting_insert("lead:web-2", name="Ari Tahririan",
                            phone="02 9876 5432",
                            email="ari@example.com",
                            message="my name and number are inside"),
        ])
        path = self.export()
        self.assertEqual(path, self.out / "exports" / f"{SNAP}-painting.jsonl")
        data = path.read_bytes()
        for forbidden in (b"Sarah", b"Cameron", b"Ari", b"Tahririan",
                          b"0412", b"9876", b"sarah@example.com",
                          b"ari@example.com", b"please call", b"my name",
                          b"ref.example", b"lead:web-1", b"lead:web-2"):
            self.assertNotIn(forbidden, data, forbidden)

        records = load_export(path)
        self.assertEqual(len(records), 2)
        for rec, lead_id in zip(records, ("lead:web-1", "lead:web-2")):
            self.assertEqual(rec["schema"], SCHEMA_NAME)
            self.assertEqual(rec["source_node"], SOURCE_NODE)
            self.assertEqual(rec["lane"], "painting")
            self.assertIs(rec["may_contact"], False)
            self.assertIs(rec["pii_redacted"], True)
            self.assertEqual(rec["observed_at_utc"], NOW)
            self.assertEqual(rec["internal_id_hash"], sha(lead_id))
            row = source_row(self.painting, "painting_leads", "lead_id",
                             lead_id)
            self.assertEqual(rec["source_row_hash"],
                             hashlib.sha256(canonical(row).encode("utf-8"))
                             .hexdigest())
            self.assertEqual(set(rec["fields"]),
                             {"suburb", "job_type", "rooms", "budget_text",
                              "score", "temperature", "status", "next_action",
                              "follow_up_count", UNKNOWN_MARKER})
            self.assertEqual(rec["fields"]["suburb"], "Newtown")
            self.assertEqual(rec["fields"]["follow_up_count"], 1)
        # The atomic write left no temporary behind.
        self.assertEqual(os.listdir(self.out / "exports"),
                         [f"{SNAP}-painting.jsonl"])

    def test_deterministic_and_stably_ordered(self):
        self.make_db(self.painting, PAINTING_SCHEMA, PAINTING_SQL, [
            painting_insert("lead:web-2"),
            painting_insert("lead:web-1"),
        ])
        first = self.export(snap="snap-a")
        second = self.export(snap="snap-b")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        records = load_export(first)
        # Ordered by the primary key, not by insertion: web-1 before web-2
        # even though web-2 was inserted first.
        self.assertEqual([r["internal_id_hash"] for r in records],
                         [sha("lead:web-1"), sha("lead:web-2")])
        # A re-export of the same snapshot is the same file, not a third one.
        again = self.export(snap="snap-a")
        self.assertEqual(again.read_bytes(), first.read_bytes())

    def test_none_vs_unknown_preserved(self):
        # A file written before follow_up_count existed. The column is
        # simply absent; suburb exists and was answered with "none".
        legacy = (
            """
            CREATE TABLE painting_leads (
                lead_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT 'lead',
                source TEXT NOT NULL,
                suburb TEXT NOT NULL DEFAULT '',
                job_type TEXT NOT NULL DEFAULT '',
                rooms TEXT NOT NULL DEFAULT '',
                budget_text TEXT NOT NULL DEFAULT '',
                score INTEGER NOT NULL DEFAULT 0,
                temperature TEXT NOT NULL DEFAULT 'new',
                status TEXT NOT NULL DEFAULT 'new',
                next_action TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
        )
        conn = sqlite3.connect(self.painting)
        try:
            for stmt in legacy:
                conn.execute(stmt)
            conn.execute(
                "INSERT INTO painting_leads (lead_id, source, suburb, "
                "created_at, updated_at) VALUES (?,?,?,?,?)",
                ("lead:old-1", "manual", "", NOW, NOW))
            conn.commit()
        finally:
            conn.close()

        (rec,) = load_export(self.export())
        fields = rec["fields"]
        # Empty string is *none*: kept, and not marked unknown.
        self.assertEqual(fields["suburb"], "")
        self.assertNotIn("suburb", fields[UNKNOWN_MARKER])
        # A missing column is *unknown*: null, and named in the marker.
        self.assertIsNone(fields["follow_up_count"])
        self.assertIn("follow_up_count", fields[UNKNOWN_MARKER])


ZIMAN_SQL = (
    "INSERT INTO products (tenant_id, sku, name, category, "
    "materials_cost_aud, labour_hours, hourly_rate_aud, packaging_cost_aud, "
    "cogs_aud, price_primary_aud, price_secondary_aud, state, channel, "
    "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


def ziman_insert(sku, tenant="ziman", *, name="earring", category="",
                 primary=120.0, secondary=None, state="for_sale",
                 channel=None):
    return (tenant, sku, name, category, 70.0, 0.0, 25.0, 2.5, 72.5,
            primary, secondary, state, channel, NOW)


class ZimanExportTests(Base):
    def test_fields_costs_price_and_id_ordering(self):
        self.make_db(self.ziman, PRODUCTS_SCHEMA, ZIMAN_SQL, [
            ziman_insert("ZM-0002"),           # id 1
            ziman_insert("ZM-0001", category="jewellery",
                        secondary=90.0, channel="instagram"),   # id 2
        ])
        records = load_export(self.export("ziman"))
        self.assertEqual([r["internal_id_hash"] for r in records],
                         [sha("ZM-0002"), sha("ZM-0001")])
        second = records[1]["fields"]
        self.assertEqual(second["name"], "earring")
        self.assertEqual(second["category"], "jewellery")
        self.assertEqual(second["state"], "for_sale")
        self.assertEqual(second["channel"], "instagram")
        self.assertEqual(second["costs"], {
            "materials_cost_aud": 70.0, "labour_hours": 0.0,
            "hourly_rate_aud": 25.0, "packaging_cost_aud": 2.5,
            "cogs_aud": 72.5,
        })
        self.assertEqual(second["price"], {"price_primary_aud": 120.0,
                                           "price_secondary_aud": 90.0})
        self.assertEqual(second[UNKNOWN_MARKER], [])

        first = records[0]["fields"]
        # An empty category is *none*: kept as "", not marked unknown.
        self.assertEqual(first["category"], "")
        self.assertNotIn("category", first[UNKNOWN_MARKER])
        # NULL columns are unknown and named.
        self.assertIsNone(first["price"]["price_secondary_aud"])
        self.assertIn("price.price_secondary_aud", first[UNKNOWN_MARKER])
        self.assertIsNone(first["channel"])
        self.assertIn("channel", first[UNKNOWN_MARKER])

    def test_duplicate_internal_id_exports_once(self):
        # The same sku under two tenants: one identity, one exported line —
        # the first row in id order, not a merge and not a second line.
        self.make_db(self.ziman, PRODUCTS_SCHEMA, ZIMAN_SQL, [
            ziman_insert("ZM-0001", tenant="ziman", name="kept"),
            ziman_insert("ZM-0001", tenant="demo", name="dropped"),
            ziman_insert("ZM-0002"),
        ])
        records = load_export(self.export("ziman"))
        self.assertEqual(len(records), 2)
        kept = [r for r in records
                if r["internal_id_hash"] == sha("ZM-0001")]
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["fields"]["name"], "kept")
        row = source_row(self.ziman, "products", "sku", "ZM-0001")
        # The kept line is the first source row for that id.
        self.assertEqual(kept[0]["source_row_hash"],
                         hashlib.sha256(canonical(row).encode("utf-8"))
                         .hexdigest())


class RobustnessTests(Base):
    def test_empty_and_missing_sources_export_empty(self):
        self.make_db(self.painting, PAINTING_SCHEMA, PAINTING_SQL, [])
        path = self.export()
        self.assertTrue(path.exists())
        self.assertEqual(path.stat().st_size, 0)
        self.assertEqual(load_export(path), [])
        # A lane whose database has never been created is an empty
        # observation, not an error.
        self.paths["ziman"] = os.path.join(os.path.dirname(self.ziman),
                                           "never-created.sqlite")
        empty = self.export("ziman")
        self.assertEqual(empty.stat().st_size, 0)

    def test_unknown_lane_rejected(self):
        with self.assertRaises(ValueError):
            self.export("mining")

    def test_malformed_row_tolerated_with_warning_line(self):
        conn = sqlite3.connect(self.painting)
        try:
            for stmt in PAINTING_SCHEMA:
                conn.execute(stmt)
            conn.execute(PAINTING_SQL, painting_insert("lead:a-good"))
            conn.execute(PAINTING_SQL, painting_insert("lead:b-blob"))
            # SQLite is dynamically typed: a BLOB fits an INTEGER column,
            # and it is exactly the kind of junk an old importer leaves.
            conn.execute("UPDATE painting_leads SET score = ? "
                         "WHERE lead_id = 'lead:b-blob'",
                         (sqlite3.Binary(b"\x00\x01\x02"),))
            conn.commit()
        finally:
            conn.close()

        records = load_export(self.export())
        self.assertEqual(len(records), 2)
        good = [r for r in records if r["schema"] == SCHEMA_NAME]
        warned = [r for r in records
                  if r["schema"] == WARNING_SCHEMA_NAME]
        self.assertEqual(len(good), 1)
        self.assertEqual(good[0]["internal_id_hash"], sha("lead:a-good"))
        self.assertEqual(len(warned), 1)
        self.assertEqual(warned[0]["lane"], "painting")
        self.assertEqual(warned[0]["row_number"], 2)
        self.assertEqual(warned[0]["reason"], "malformed-row")
        self.assertEqual(warned[0]["observed_at_utc"], NOW)
        # The warning carries what happened, never what was in the row.
        raw = (self.out / "exports" / f"{SNAP}-painting.jsonl").read_bytes()
        self.assertNotIn(b"Sarah", raw)
        self.assertNotIn(b"\x00\x01\x02", raw)

    def test_every_line_schema_valid(self):
        self.make_db(self.painting, PAINTING_SCHEMA, PAINTING_SQL, [
            painting_insert("lead:web-1"),
        ])
        self.make_db(self.ziman, PRODUCTS_SCHEMA, ZIMAN_SQL, [
            ziman_insert("ZM-0001"),
        ])
        for lane in ("painting", "ziman"):
            for rec in load_export(self.export(lane)):
                self.assertEqual(set(rec), LINE_KEYS, lane)
                self.assertEqual(rec["schema"], SCHEMA_NAME)
                self.assertEqual(rec["lane"], lane)
                self.assertEqual(rec["source_node"], SOURCE_NODE)
                for digest in (rec["internal_id_hash"],
                               rec["source_row_hash"]):
                    self.assertEqual(len(digest), 64)
                    self.assertTrue(all(c in HEX64 for c in digest))
                self.assertIs(rec["may_contact"], False)
                self.assertIs(rec["pii_redacted"], True)
                self.assertIsInstance(rec["fields"], dict)
                self.assertIn(UNKNOWN_MARKER, rec["fields"])

    def test_sources_are_not_mutated(self):
        self.make_db(self.painting, PAINTING_SCHEMA, PAINTING_SQL, [
            painting_insert("lead:web-1")])
        self.make_db(self.ziman, PRODUCTS_SCHEMA, ZIMAN_SQL, [
            ziman_insert("ZM-0001")])
        before = {}
        for path in (self.painting, self.ziman):
            stat = os.stat(path)
            with open(path, "rb") as fh:
                before[path] = (stat.st_mtime_ns, stat.st_size,
                                hashlib.sha256(fh.read()).hexdigest())
        self.export("painting")
        self.export("ziman")
        for path in (self.painting, self.ziman):
            stat = os.stat(path)
            with open(path, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            self.assertEqual(before[path],
                             (stat.st_mtime_ns, stat.st_size, digest))
            # No journal the read side never asked for.
            for sidecar in ("-wal", "-shm", "-journal"):
                self.assertFalse(
                    os.path.exists(path + sidecar), path + sidecar)


if __name__ == "__main__":
    unittest.main()
