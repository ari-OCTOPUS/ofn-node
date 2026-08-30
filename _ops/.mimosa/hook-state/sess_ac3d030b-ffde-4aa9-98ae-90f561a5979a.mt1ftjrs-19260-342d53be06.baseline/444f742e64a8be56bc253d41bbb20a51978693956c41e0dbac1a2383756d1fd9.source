#!/usr/bin/env python3
"""test_ziman_phase2.py — تست‌های خالص/آفلاین اعتبارسنج‌های فاز ۲ زیمان."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

from datetime import datetime, timezone  # noqa: E402

from ziman_phase2 import (  # noqa: E402
    anti_misread_guard, capacity_fail_closed, compute_atp,
    valid_product_id, validate_product_card)

_NOW = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)  # CF-07: ساعتِ تزریقیِ قطعی


def _card(**over):
    base = {
        "product_id": "ZM-C3-0001", "family_id": "C3",
        "classification": {"perishable": False},
        "fulfilment": {"policy": "local_only",
                       "delivery_promise_authority": False},
        "commercial": {"public_price_aud": None, "price_status": "unknown"},
        "inventory": {"quantity_on_hand": None, "quantity_reserved": 0,
                      "available_to_promise": None, "measured_at": None},
    }
    base.update(over)
    return base


def test_valid_ids():
    assert valid_product_id("ZM-C1-0001")
    assert not valid_product_id("ZM-C5-0001")
    assert not valid_product_id("ZM-C3-1")
    assert not valid_product_id("")


def test_atp_fail_closed_unmeasured():
    assert compute_atp(None, 0, None) is None
    assert compute_atp(10, 2, None) is None          # no measured_at → None
    assert compute_atp(10, 2, "2026-07-12", _now=_NOW) == 8
    assert compute_atp(2, 10, "2026-07-12", _now=_NOW) == 0     # never negative
    assert compute_atp(-1, 0, "2026-07-12", _now=_NOW) is None  # negative rejected


def test_atp_future_rejected():
    # CF-07: اندازه‌گیریِ آینده = نامعتبر
    assert compute_atp(10, 0, "2099-01-01", _now=_NOW) is None


def test_atp_stale_by_age_rejected():
    # CF-07: کهنه‌تر از ۳۰ روز = نامعتبر؛ ~۱۱ روز = تازه
    assert compute_atp(10, 0, "2026-05-01", _now=_NOW) is None
    assert compute_atp(10, 0, "2026-07-01", _now=_NOW) == 10


def test_atp_garbage_and_nonstring_rejected():
    # CF-07: غیرقابل‌parse یا غیر-رشته = None (قبلاً ATP واقعی می‌داد)
    assert compute_atp(10, 0, "banana", _now=_NOW) is None
    assert compute_atp(10, 0, 20260712, _now=_NOW) is None
    # naive ISO پذیرفته و UTC فرض می‌شود (نه رد):
    assert compute_atp(10, 0, "2026-07-12T00:00:00", _now=_NOW) == 10


def test_validate_rejects_stale_atp_card():
    # CF-07: کارت با ATP ولی measured_at کهنه → fail-closed (۲۰۲۰ همیشه کهنه است)
    c = _card(inventory={"quantity_on_hand": 10, "quantity_reserved": 0,
                         "available_to_promise": 10, "measured_at": "2020-01-01"})
    assert any("fail-closed" in e for e in validate_product_card(c))


def test_valid_card_passes():
    assert validate_product_card(_card()) == []


def test_c4_shipping_violation():
    c = _card(product_id="ZM-C4-0001", family_id="C4",
              classification={"perishable": True},
              fulfilment={"policy": "shippable",
                          "delivery_promise_authority": False})
    errs = validate_product_card(c)
    assert any("C4 policy" in e for e in errs)


def test_c4_must_be_perishable():
    c = _card(product_id="ZM-C4-0002", family_id="C4",
              classification={"perishable": False},
              fulfilment={"policy": "pickup",
                          "delivery_promise_authority": False})
    assert any("perishable" in e for e in validate_product_card(c))


def test_price_gate():
    c = _card(commercial={"public_price_aud": 120, "price_status": "draft"})
    assert any("owner_approved" in e for e in validate_product_card(c))
    c2 = _card(commercial={"public_price_aud": 120,
                           "price_status": "owner_approved"})
    assert validate_product_card(c2) == []


def test_delivery_promise_blocked():
    c = _card(fulfilment={"policy": "local_only",
                          "delivery_promise_authority": True})
    assert any("delivery_promise" in e for e in validate_product_card(c))


def test_atp_stale_rejected():
    c = _card(inventory={"quantity_on_hand": 10, "quantity_reserved": 0,
                         "available_to_promise": 10, "measured_at": None})
    assert any("fail-closed" in e for e in validate_product_card(c))


def test_family_id_mismatch():
    c = _card(product_id="ZM-C1-0001", family_id="C3")
    assert any("mismatch" in e for e in validate_product_card(c))


def test_anti_misread_guard():
    assert anti_misread_guard("we have 50 unique SKUs")["allowed"] is False
    assert anti_misread_guard("capacity = 50 per week")["allowed"] is False
    assert anti_misread_guard("30/week verified capacity")["allowed"] is False
    assert anti_misread_guard("50 physical products, families C1-C4")["allowed"] is True


def test_capacity_fail_closed():
    assert capacity_fail_closed(None) == 0
    assert capacity_fail_closed(0) == 0
    assert capacity_fail_closed(30, owner_revalidated=False) == 6   # CF-01 open
    assert capacity_fail_closed(30, owner_revalidated=True) == 30
    assert capacity_fail_closed(4, owner_revalidated=False) == 4


def test_not_a_dict():
    assert validate_product_card(None) == ["card is not a dict"]
