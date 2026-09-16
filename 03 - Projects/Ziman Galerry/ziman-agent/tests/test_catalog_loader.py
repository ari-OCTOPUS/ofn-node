"""تست‌های catalog_loader — اتصالِ کاتالوگِ ۳۵‌محصولی به product_card.v1.

نکتهٔ کلیدی: هر رکوردِ واقعیِ کاتالوگ باید به یک ProductCard معتبر نگاشت شود،
بدونِ هیچ قیمت/موجودیِ جعلی، و F4/perishable باید محلی (local_only) باشد.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "ziman"))

from catalog_loader import (  # noqa: E402
    card_from_record,
    catalog_summary,
    find_catalog_json,
    load_catalog,
)
from product import _ID_RE_ZIM  # noqa: E402

_CATALOG = find_catalog_json()
_needs_catalog = pytest.mark.skipif(_CATALOG is None, reason="ziman-catalog.json not found")


# ── unit tests (no file needed) ─────────────────────────────────────────────

def test_f4_forced_local_even_if_not_flagged_perishable():
    rec = {"product_id": "ZIM-F4-99", "family": "F4_mixed_hamper",
           "one_line": "hamper", "perishable": False, "photo_files": ["x.jpg"]}
    card = card_from_record(rec)
    assert card.family_id == "F4"
    assert card.fulfilment["policy"] == "local_only"      # R0-F1 fail-closed
    assert card.validate() == []


def test_floral_non_perishable_is_shippable():
    rec = {"product_id": "ZIM-F1-99", "family": "F1_floral",
           "one_line": "silk bouquet", "perishable": False, "photo_files": ["x.jpg"]}
    card = card_from_record(rec)
    assert card.fulfilment["policy"] == "shippable"
    assert card.validate() == []


def test_never_fabricates_price_or_stock():
    rec = {"product_id": "ZIM-F1-98", "family": "F1_floral",
           "one_line": "bouquet", "perishable": False, "photo_files": []}
    card = card_from_record(rec)
    assert card.commercial.public_price_aud is None
    assert card.commercial.price_status == "unknown"
    assert card.inventory.quantity_on_hand is None
    assert card.inventory.available_to_promise is None
    assert card.governance["propose_only"] is True


def test_alcohol_facet_detected():
    rec = {"product_id": "ZIM-F4-97", "family": "F4_mixed_hamper",
           "one_line": "luxury hamper with a bottle of sparkling wine",
           "perishable": True, "photo_files": []}
    assert card_from_record(rec).classification["alcohol"] is True


# ── integration against the real catalog ────────────────────────────────────

@_needs_catalog
def test_every_real_record_maps_to_valid_card():
    cards = load_catalog(_CATALOG)
    assert len(cards) >= 35
    # مهم‌ترین ادعا: صفر خطای اعتبارسنجی در کلِ کاتالوگ
    bad = [(c.product_id, c.validate()) for c in cards if c.validate()]
    assert bad == [], f"invalid cards: {bad}"


@_needs_catalog
def test_all_ids_follow_zim_scheme():
    for c in load_catalog(_CATALOG):
        assert _ID_RE_ZIM.match(c.product_id), c.product_id


@_needs_catalog
def test_all_f4_are_local_only():
    for c in load_catalog(_CATALOG):
        if c.family_id == "F4":
            assert c.fulfilment["policy"] in ("local_only", "pickup"), c.product_id


@_needs_catalog
def test_no_card_is_priced_yet():
    summary = catalog_summary(load_catalog(_CATALOG))
    assert summary["priced"] == 0            # قیمت‌گذاری تا ZIM-V5 قفل است
    assert summary["total"] >= 35


@_needs_catalog
def test_family_distribution_matches_evidence():
    summary = catalog_summary(load_catalog(_CATALOG))
    fam = summary["by_family"]
    # از شمارشِ گراندشدهٔ کاتالوگ: 18 F1 · 2 F2 · 4 F3 · 11 F4
    assert fam.get("F1") == 18
    assert fam.get("F2") == 2
    assert fam.get("F3") == 4
    assert fam.get("F4") == 11
