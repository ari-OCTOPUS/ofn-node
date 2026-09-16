#!/usr/bin/env python3
"""14-day pilot report from the canonical stores.

The success metric is deliberately evaluated from linked commerce rows, not
from counters. Run: ``python3 tools/pilot_report.py [--days 3]``.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn import config  # noqa: E402
from ofn.adapters.lead_store import LeadStore  # noqa: E402
from ofn.adapters.products import ProductStore  # noqa: E402
from ofn.adapters.studio_store import StudioStore  # noqa: E402


_EXCLUDED_ENVIRONMENTS = {"seed", "test", "demo", "legacy_unknown"}
_EXCLUDED_SOURCES = {"seed", "seed_pilot", "test", "demo", "legacy_unknown"}
# A qualifying payment must be confirmed by one of these, independently of
# whether the store enforced it at insertion time — the report must prove it
# from persisted data, not trust the writer.
_TRUSTED_CONFIRMATION_SOURCES = frozenset({"provider_webhook", "audited_receipt"})
_TABLE_CANDIDATES = {
    "listings": ("commerce_listing_events", "product_listing_events",
                 "listing_events"),
    "inquiries": ("commerce_inquiry_events", "product_inquiry_events",
                  "commerce_inquiries", "product_inquiries", "inquiry_events"),
    "orders": ("commerce_orders", "product_orders", "orders"),
    "payments": ("commerce_payment_events", "product_payment_events",
                 "commerce_payments", "product_payments", "payment_events",
                 "payments"),
}


@dataclass(frozen=True)
class PilotResult:
    """Deterministic result of evaluating one requested UTC window."""

    passed: bool
    production_listings: int
    linked_production_inquiries: int
    qualifying_production_payments: int
    window_start: datetime
    window_end: datetime
    missing_tables: tuple[str, ...] = ()


def _utc(value: datetime) -> datetime:
    """Require an aware timestamp and normalize it to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("pilot window timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _event_time(value: Any) -> datetime | None:
    """Parse a stored timestamp, accepting only timestamps with UTC context."""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            return None
        return value.astimezone(timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _first(row: Mapping[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name not in row:
            continue
        value = row[name]
        if value is not None and (not isinstance(value, str) or value.strip()):
            return value
    return None


def _row_id(row: Mapping[str, Any], *specific: str) -> str:
    return str(_first(row, (*specific, "event_id", "id")) or "").strip()


def _is_production(row: Mapping[str, Any]) -> bool:
    environment = str(row.get("environment") or "legacy_unknown").strip().lower()
    source = str(row.get("source") or "").strip().lower()
    return (environment == "production"
            and environment not in _EXCLUDED_ENVIRONMENTS
            and source not in _EXCLUDED_SOURCES)


def _inside(row: Mapping[str, Any], names: Iterable[str],
            start: datetime, end: datetime) -> datetime | None:
    at = _event_time(_first(row, names))
    return at if at is not None and start <= at <= end else None


def _table_rows(conn: sqlite3.Connection, candidates: Iterable[str]
                ) -> tuple[str | None, list[dict[str, Any]]]:
    existing = {str(row[0]) for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    table = next((name for name in candidates if name in existing), None)
    if table is None:
        return None, []
    # The table name comes exclusively from the static allow-list above.
    cursor = conn.execute(f'SELECT * FROM "{table}"')
    columns = [str(item[0]) for item in cursor.description or ()]
    return table, [dict(zip(columns, row)) for row in cursor.fetchall()]


def _is_reversed_or_refunded(payment: Mapping[str, Any]) -> bool:
    status = str(payment.get("status") or "").strip().lower()
    if status in {"refunded", "reversed"}:
        return True
    for field in ("refunded_at", "reversed_at", "refund_id", "reversal_id"):
        if str(payment.get(field) or "").strip():
            return True
    for field in ("is_refunded", "is_reversed"):
        value = payment.get(field)
        if value is True or value == 1 or str(value or "").lower() == "true":
            return True
    return False


def evaluate_pilot(conn: sqlite3.Connection, *, window_start: datetime,
                   window_end: datetime,
                   thresholds: Mapping[str, int] | None = None) -> PilotResult:
    """Evaluate the approved pilot criterion from linked commerce tables.

    A passing window contains at least three production listing events and a
    chronological listing -> inquiry -> order -> confirmed/settled payment
    chain. Every row in that chain must be inside the inclusive UTC window.
    The payment must have a positive amount and non-empty evidence digest.
    Seed, test, demo and legacy-unknown rows never participate.

    The function has no clock, filesystem, store, or printing dependency; the
    caller supplies an open products.sqlite connection and explicit bounds.
    """
    start, end = _utc(window_start), _utc(window_end)
    if start > end:
        raise ValueError("pilot window start must not be after its end")

    loaded: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    for kind, candidates in _TABLE_CANDIDATES.items():
        table, rows = _table_rows(conn, candidates)
        loaded[kind] = rows
        if table is None:
            missing.append(kind)
    if missing:
        return PilotResult(False, 0, 0, 0, start, end, tuple(missing))

    listings: dict[str, tuple[dict[str, Any], datetime]] = {}
    for row in loaded["listings"]:
        at = _inside(row, ("published_at", "listed_at", "occurred_at",
                           "event_at"), start, end)
        event_id = _row_id(row, "listing_event_id", "listing_id")
        if event_id and at is not None and _is_production(row):
            listings[event_id] = (row, at)

    inquiries: dict[str, tuple[dict[str, Any], datetime, str]] = {}
    for row in loaded["inquiries"]:
        at = _inside(row, ("received_at", "inquired_at", "occurred_at",
                           "event_at"), start, end)
        inquiry_id = _row_id(row, "inquiry_id")
        listing_id = str(_first(row, ("listing_event_id", "listing_id")) or "").strip()
        listing = listings.get(listing_id)
        if (inquiry_id and listing is not None and at is not None
                and _is_production(row) and listing[1] <= at):
            inquiries[inquiry_id] = (row, at, listing_id)

    orders: dict[str, tuple[dict[str, Any], datetime, str]] = {}
    for row in loaded["orders"]:
        at = _inside(row, ("reserved_at", "ordered_at", "occurred_at",
                           "event_at"), start, end)
        order_id = _row_id(row, "order_id")
        inquiry_id = str(row.get("inquiry_id") or "").strip()
        inquiry = inquiries.get(inquiry_id)
        if (order_id and inquiry is not None and at is not None
                and _is_production(row) and inquiry[1] <= at):
            orders[order_id] = (row, at, inquiry_id)

    qualifying_payments = 0
    for row in loaded["payments"]:
        at = _inside(row, ("confirmed_at", "settled_at", "paid_at",
                           "occurred_at", "event_at"), start, end)
        order_id = str(row.get("order_id") or "").strip()
        order = orders.get(order_id)
        status = str(row.get("status") or "").strip().lower()
        evidence = str(_first(row, ("evidence_digest", "receipt_digest")) or "").strip()
        confirmation_source = str(
            _first(row, ("confirmation_source",)) or "").strip().lower()
        try:
            amount = int(row.get("amount_cents"))
        except (TypeError, ValueError):
            amount = 0
        if (order is not None and at is not None and order[1] <= at
                and _is_production(row) and status in {"confirmed", "settled"}
                and not _is_reversed_or_refunded(row)
                and amount > 0 and evidence
                and confirmation_source in _TRUSTED_CONFIRMATION_SOURCES):
            qualifying_payments += 1

    listing_count = len(listings)
    inquiry_count = len(inquiries)
    # Thresholds: caller may pass owner-set values; default matches
    # docs/operations/PILOT-14DAY.md (never invent a softer bar).
    from ofn.adapters.pilot_thresholds import DEFAULT_THRESHOLDS
    th = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        for key in DEFAULT_THRESHOLDS:
            try:
                val = int(thresholds.get(key, th[key]))
                if val > 0:
                    th[key] = val
            except (TypeError, ValueError):
                pass
    passed = (listing_count >= int(th["min_production_listings"])
              and inquiry_count >= int(th["min_linked_production_inquiries"])
              and qualifying_payments >= int(
                  th["min_qualifying_production_payments"]))
    return PilotResult(passed, listing_count, inquiry_count, qualifying_payments,
                       start, end)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report the approved pilot metric")
    parser.add_argument("--days", type=int, default=3,
                        help="inclusive lookback window in UTC days (default: 3)")
    return parser


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    if args.days <= 0:
        _parser().error("--days must be greater than zero")

    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=args.days)
    cfg = config.load()
    painting = LeadStore(cfg.painting_path)
    products = ProductStore(
        cfg.products_path,
        cost_fields=["materials_cost_aud"],
        labour_hours_field="labour_hours",
        labour_rate_field="hourly_rate_aud")
    studio = StudioStore(cfg.studio_path)
    try:
        leads = painting.list_leads("lead", limit=100)
        open_leads = [lead for lead in leads
                      if lead.get("status") in ("new", "review", "contacted", "quoted")]
        due = painting.follow_ups_due("lead", before_iso=config.now_iso())
        pieces = products.list("ziman")
        ready = [piece for piece in pieces if piece.state == "for_sale"]
        sold = [piece for piece in pieces if piece.state == "sold"]
        drafts = studio.drafts("studio") or []
        from ofn.adapters.pilot_thresholds import load as load_pilot_cfg
        pilot_cfg = load_pilot_cfg(cfg.state_dir)
        th = pilot_cfg.thresholds
        with sqlite3.connect(cfg.products_path) as conn:
            pilot = evaluate_pilot(conn, window_start=window_start,
                                   window_end=window_end, thresholds=th)

        print(f"pilot report ({window_start.isoformat()} to {window_end.isoformat()})")
        print(f"  lead: {len(open_leads)} open · {len(due)} follow-up due")
        print(f"  ziman: {len(ready)} ready-to-list · {len(sold)} sold")
        print(f"  studio: {len(drafts)} drafts")
        print("  payment rails: "
              + ", ".join(f"{k}={v}" for k, v in pilot_cfg.payment_methods.items()))
        print("  approved metric: "
              f"{pilot.production_listings}/{th['min_production_listings']} "
              "production listings · "
              f"{pilot.linked_production_inquiries}/"
              f"{th['min_linked_production_inquiries']} linked inquiries · "
              f"{pilot.qualifying_production_payments}/"
              f"{th['min_qualifying_production_payments']} qualifying payments")
        print(f"  pilot criterion: {'PASS' if pilot.passed else 'FAIL'}")
        if pilot.missing_tables:
            print("  commerce tables missing: " + ", ".join(pilot.missing_tables))
    finally:
        painting.close()
        products.close()
        studio.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
