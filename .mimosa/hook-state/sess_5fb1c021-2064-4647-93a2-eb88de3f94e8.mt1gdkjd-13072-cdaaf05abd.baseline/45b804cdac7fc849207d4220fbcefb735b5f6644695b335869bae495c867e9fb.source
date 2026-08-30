"""Approved pilot metric: only a linked production commerce chain passes."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest

from tools.pilot_report import evaluate_pilot

START = datetime(2026, 8, 1, tzinfo=timezone.utc)
END = datetime(2026, 8, 15, tzinfo=timezone.utc)


def database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE product_listing_events (
            listing_id TEXT PRIMARY KEY, published_at TEXT NOT NULL,
            environment TEXT NOT NULL, source TEXT NOT NULL);
        CREATE TABLE product_inquiries (
            inquiry_id TEXT PRIMARY KEY, listing_id TEXT NOT NULL,
            received_at TEXT NOT NULL, environment TEXT NOT NULL,
            source TEXT NOT NULL);
        CREATE TABLE product_orders (
            order_id TEXT PRIMARY KEY, inquiry_id TEXT NOT NULL,
            reserved_at TEXT NOT NULL, environment TEXT NOT NULL,
            source TEXT NOT NULL);
        CREATE TABLE product_payments (
            payment_id TEXT PRIMARY KEY, order_id TEXT NOT NULL,
            amount_cents INTEGER NOT NULL, status TEXT NOT NULL,
            evidence_digest TEXT NOT NULL, confirmed_at TEXT,
            refunded_at TEXT, reversed_at TEXT,
            confirmation_source TEXT NOT NULL,
            environment TEXT NOT NULL, source TEXT NOT NULL);
        """)
    return conn


def listing(conn: sqlite3.Connection, number: int, *,
            at: str = "2026-08-02T00:00:00Z",
            environment: str = "production", source: str = "manual") -> None:
    conn.execute("INSERT INTO product_listing_events VALUES (?,?,?,?)",
                 (f"l{number}", at, environment, source))


def three_listings(conn: sqlite3.Connection) -> None:
    for number in range(1, 4):
        listing(conn, number)


def inquiry(conn: sqlite3.Connection, *, inquiry_id: str = "i1",
            listing_id: str = "l1", at: str = "2026-08-03T00:00:00Z",
            environment: str = "production", source: str = "manual") -> None:
    conn.execute("INSERT INTO product_inquiries VALUES (?,?,?,?,?)",
                 (inquiry_id, listing_id, at, environment, source))


def order(conn: sqlite3.Connection, *, order_id: str = "o1",
          inquiry_id: str = "i1", at: str = "2026-08-04T00:00:00Z",
          environment: str = "production", source: str = "manual") -> None:
    conn.execute("INSERT INTO product_orders VALUES (?,?,?,?,?)",
                 (order_id, inquiry_id, at, environment, source))


def payment(conn: sqlite3.Connection, *, order_id: str = "o1",
            status: str = "confirmed", at: str = "2026-08-05T00:00:00Z",
            evidence: str = "sha256:receipt", amount: int = 5000,
            refunded_at: str | None = None, reversed_at: str | None = None,
            confirmation_source: str = "audited_receipt",
            environment: str = "production", source: str = "manual") -> None:
    conn.execute("INSERT INTO product_payments VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 ("p1", order_id, amount, status, evidence, at, refunded_at,
                  reversed_at, confirmation_source, environment, source))


def result(conn: sqlite3.Connection):
    return evaluate_pilot(conn, window_start=START, window_end=END)


def test_seed_and_legacy_rows_are_excluded() -> None:
    conn = database()
    listing(conn, 1, environment="seed", source="seed_pilot")
    listing(conn, 2, environment="test", source="test")
    listing(conn, 3, environment="demo", source="demo")
    listing(conn, 4, environment="legacy_unknown", source="legacy_unknown")
    inquiry(conn, environment="seed", source="seed_pilot")
    order(conn, environment="seed", source="seed_pilot")
    payment(conn, environment="seed", source="seed_pilot")

    out = result(conn)

    assert not out.passed
    assert out.production_listings == 0
    assert out.linked_production_inquiries == 0
    assert out.qualifying_production_payments == 0


def test_three_production_listings_without_inquiry_fail() -> None:
    conn = database()
    three_listings(conn)

    out = result(conn)

    assert not out.passed
    assert out.production_listings == 3
    assert out.linked_production_inquiries == 0


def test_linked_inquiry_without_payment_fails() -> None:
    conn = database()
    three_listings(conn)
    inquiry(conn)
    order(conn)

    out = result(conn)

    assert not out.passed
    assert out.linked_production_inquiries == 1
    assert out.qualifying_production_payments == 0


def test_linked_real_chronological_chain_passes() -> None:
    conn = database()
    three_listings(conn)
    inquiry(conn)
    order(conn)
    payment(conn, status="settled")

    out = result(conn)

    assert out.passed
    assert out.production_listings == 3
    assert out.linked_production_inquiries == 1
    assert out.qualifying_production_payments == 1


def test_nonchronological_chain_fails() -> None:
    conn = database()
    three_listings(conn)
    inquiry(conn, at="2026-08-06T00:00:00Z")
    order(conn, at="2026-08-04T00:00:00Z")
    payment(conn)

    out = result(conn)

    assert not out.passed
    assert out.qualifying_production_payments == 0


@pytest.mark.parametrize("break_chain", ["outside", "wrong_order"])
def test_outside_window_or_wrong_order_fails(break_chain: str) -> None:
    conn = database()
    three_listings(conn)
    inquiry(conn)
    order(conn)
    if break_chain == "outside":
        payment(conn, at="2026-08-16T00:00:00Z")
    else:
        payment(conn, order_id="unlinked-order")

    out = result(conn)

    assert not out.passed
    assert out.qualifying_production_payments == 0


@pytest.mark.parametrize("status,refunded_at,reversed_at", [
    ("refunded", None, None),
    ("reversed", None, None),
    ("confirmed", "2026-08-06T00:00:00Z", None),
    ("settled", None, "2026-08-06T00:00:00Z"),
])
def test_refunded_or_reversed_payment_fails(
        status: str, refunded_at: str | None, reversed_at: str | None) -> None:
    conn = database()
    three_listings(conn)
    inquiry(conn)
    order(conn)
    payment(conn, status=status, refunded_at=refunded_at, reversed_at=reversed_at)

    out = result(conn)

    assert not out.passed
    assert out.qualifying_production_payments == 0


def test_untrusted_confirmation_source_fails() -> None:
    """A payment confirmed by an untrusted source (e.g. 'manual') must not
    satisfy the pilot, even if the amount and evidence are valid.  The report
    must prove trusted confirmation from persisted data, not trust the writer.
    """
    conn = database()
    three_listings(conn)
    inquiry(conn)
    order(conn)
    payment(conn, confirmation_source="manual")

    out = result(conn)

    assert not out.passed
    assert out.qualifying_production_payments == 0


@pytest.mark.parametrize("confirmation_source", ["provider_webhook",
                                                 "audited_receipt"])
def test_trusted_confirmation_sources_pass(
        confirmation_source: str) -> None:
    conn = database()
    three_listings(conn)
    inquiry(conn)
    order(conn)
    payment(conn, confirmation_source=confirmation_source)

    out = result(conn)

    assert out.passed
    assert out.qualifying_production_payments == 1
