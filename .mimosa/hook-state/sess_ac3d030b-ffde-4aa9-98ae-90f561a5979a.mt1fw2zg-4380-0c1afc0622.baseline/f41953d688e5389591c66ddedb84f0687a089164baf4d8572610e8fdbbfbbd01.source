"""test_product.py — تست‌های خالص product.py (stdlib-only، صفر شبکه)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "ziman"))

from product import (
    CommercialBlock,
    InventoryBlock,
    InventorySnapshot,
    PhotoProductMap,
    ProductCard,
    anti_misread_guard,
    capacity_fail_closed,
    next_product_id,
    valid_product_id,
)


def test_valid_ids():
    assert valid_product_id("ZM-C1-0001")
    assert valid_product_id("ZM-C4-9999")
    assert not valid_product_id("ZM-C5-0001")
    assert not valid_product_id("ZM-C3-1")
    assert not valid_product_id("")


def test_next_product_id():
    assert next_product_id("C1", ["ZM-C1-0001"]) == "ZM-C1-0002"
    assert next_product_id("C3", []) == "ZM-C3-0001"
    assert next_product_id("C3", ["ZM-C3-0001", "ZM-C3-0005"]) == "ZM-C3-0006"


def test_inventory_block_atp():
    # unmeasured → None
    inv = InventoryBlock(quantity_on_hand=None, quantity_reserved=0)
    assert inv.compute_atp() is None
    # measured → computed
    inv2 = InventoryBlock(quantity_on_hand=10, quantity_reserved=2, measured_at="2026-07-12T10:00:00+00:00")
    assert inv2.compute_atp() == 8
    # negative → None
    inv3 = InventoryBlock(quantity_on_hand=-1, measured_at="2026-07-12")
    assert inv3.compute_atp() is None
    # reserved > on_hand → 0
    inv4 = InventoryBlock(quantity_on_hand=2, quantity_reserved=10, measured_at="2026-07-12")
    assert inv4.compute_atp() == 0


def test_inventory_freshness():
    from datetime import datetime, timezone
    fresh = InventoryBlock(measured_at=datetime.now(timezone.utc).isoformat())
    assert fresh.is_fresh(max_hours=168)
    stale = InventoryBlock(measured_at="2026-01-01T00:00:00+00:00")
    assert not stale.is_fresh(max_hours=168)


def test_product_card_passes():
    card = ProductCard(
        product_id="ZM-C3-0001",
        family_id="C3",
        title="Shadow Box Birthday",
        classification={"perishable": False, "personalisable": True},
        inventory=InventoryBlock(quantity_on_hand=5, quantity_reserved=0, measured_at="2026-07-12T10:00:00+00:00"),
        commercial=CommercialBlock(price_status="unknown"),
        fulfilment={"policy": "shippable", "delivery_promise_authority": False},
    )
    assert card.validate() == []
    # ATP should be auto-computable
    assert card.inventory.compute_atp() == 5


def test_c4_invariants():
    # C4 without perishable=true
    c = ProductCard(
        product_id="ZM-C4-0001",
        family_id="C4",
        classification={"perishable": False},
        fulfilment={"policy": "shippable"},
    )
    errs = c.validate()
    assert any("perishable" in e for e in errs)
    assert any("C4 policy" in e for e in errs)
    # C4 with correct policy
    c2 = ProductCard(
        product_id="ZM-C4-0002",
        family_id="C4",
        classification={"perishable": True},
        fulfilment={"policy": "pickup"},
    )
    assert c2.validate() == []


def test_price_gate():
    c = ProductCard(
        product_id="ZM-C1-0001",
        family_id="C1",
        commercial=CommercialBlock(public_price_aud=120, price_status="draft"),
    )
    assert any("owner_approved" in e for e in c.validate())
    c2 = ProductCard(
        product_id="ZM-C1-0002",
        family_id="C1",
        commercial=CommercialBlock(public_price_aud=120, price_status="owner_approved"),
    )
    assert c2.validate() == []


def test_delivery_promise_blocked():
    c = ProductCard(
        product_id="ZM-C1-0003",
        family_id="C1",
        fulfilment={"delivery_promise_authority": True},
    )
    assert any("delivery_promise" in e for e in c.validate())


def test_atp_mismatch():
    c = ProductCard(
        product_id="ZM-C2-0001",
        family_id="C2",
        inventory=InventoryBlock(
            quantity_on_hand=10, quantity_reserved=0,
            available_to_promise=99, measured_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    assert any("ATP mismatch" in e for e in c.validate())


def test_atp_stale_no_measured():
    c = ProductCard(
        product_id="ZM-C2-0002",
        family_id="C2",
        inventory=InventoryBlock(quantity_on_hand=10, available_to_promise=10, measured_at=None),
    )
    assert any("fail-closed" in e for e in c.validate())


def test_family_id_mismatch():
    c = ProductCard(product_id="ZM-C1-0001", family_id="C3")
    assert any("mismatch" in e for e in c.validate())


def test_anti_misread_guard():
    assert anti_misread_guard("we have 50 unique SKUs")["allowed"] is False
    assert anti_misread_guard("capacity is 50 per week")["allowed"] is False
    assert anti_misread_guard("30/week measured capacity")["allowed"] is False
    assert anti_misread_guard("50 physical products, families C1-C4")["allowed"] is True


def test_capacity_fail_closed():
    assert capacity_fail_closed(None) == 0
    assert capacity_fail_closed(0) == 0
    assert capacity_fail_closed(30, owner_revalidated=False) == 6   # CF-01 open
    assert capacity_fail_closed(30, owner_revalidated=True) == 30
    assert capacity_fail_closed(4, owner_revalidated=False) == 4


def test_to_from_dict():
    c = ProductCard(product_id="ZM-C3-0001", family_id="C3", title="Test")
    d = c.to_dict()
    assert d["schema_version"] == "product_card.v1"
    c2 = ProductCard.from_dict(d)
    assert c2.product_id == c.product_id
    assert c2.title == c.title


def test_atp_requires_fresh_timezone_aware_measurement():
    naive = ProductCard(
        product_id="ZM-C1-0007", family_id="C1",
        inventory=InventoryBlock(quantity_on_hand=2, available_to_promise=2,
                                 measured_at="2026-07-12T10:00:00"),
    )
    assert any("fail-closed" in e for e in naive.validate())
    future = ProductCard(
        product_id="ZM-C1-0008", family_id="C1",
        inventory=InventoryBlock(quantity_on_hand=2, available_to_promise=2,
                                 measured_at="2099-01-01T00:00:00+00:00"),
    )
    assert any("fail-closed" in e for e in future.validate())


def test_load_product_cards_reads_cli_json_and_skips_invalid(tmp_path):
    from product import load_product_cards
    valid = ProductCard(product_id="ZM-C3-0001", family_id="C3", title="Valid")
    (tmp_path / "ZM-C3-0001.json").write_text(json.dumps(valid.to_dict()), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    assert [card.product_id for card in load_product_cards(tmp_path)] == ["ZM-C3-0001"]


def test_inventory_snapshot_dict():
    snap = InventorySnapshot(snapshot_id="INV-001", measured_at="2026-07-12")
    d = snap.to_dict()
    assert d["schema_version"] == "inventory_snapshot.v1"


def test_photo_map_dict():
    mp = PhotoProductMap(map_id="MAP-001", created_at="2026-07-12")
    d = mp.to_dict()
    assert d["schema_version"] == "photo_product_map.v1"


if __name__ == "__main__":
    for name, fn in globals().items():
        if name.startswith("test_"):
            try:
                fn()
                print(f"✅ {name}")
            except AssertionError as e:
                print(f"❌ {name}: {e}")
