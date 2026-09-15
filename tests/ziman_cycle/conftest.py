from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_out(tmp_path: Path) -> Path:
    d = tmp_path / "out"
    d.mkdir()
    return d


@pytest.fixture
def sample_catalog(tmp_path: Path) -> Path:
    products = []
    for i in range(1, 19):
        products.append(
            {
                "product_id": f"ZIM-F1-{i:02d}",
                "family": "F1_floral",
                "form": "bouquet",
                "one_line": f"Floral item {i}",
            }
        )
    products.append({"product_id": "ZIM-X-01", "family": "other", "one_line": "x"})
    data = {
        "products": products,
        "stats": {"n": len(products)},
        "data_gaps": {"missing_sell_fields_entirely_absent_from_catalog_schema": [
            "price_aud", "stock_qty", "delivery_options", "lead_time",
            "weight_g", "dimensions", "components_cost", "license_clearance",
        ]},
    }
    path = tmp_path / "ziman-catalog.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def sample_catalog_bom(tmp_path: Path, sample_catalog: Path) -> Path:
    raw = sample_catalog.read_bytes()
    path = tmp_path / "ziman-catalog-bom.json"
    path.write_bytes(b"\xef\xbb\xbf" + raw)
    return path


def _sku_row():
    return {
        "field": "sku",
        "value": {
            "family": "F1_floral",
            "product_ids": [f"ZIM-F1-{i:02d}" for i in range(1, 19)],
            "count": 18,
        },
        "source": "ziman-catalog.json",
        "status": "GROUNDED_OWNER_CONFIRMED",
        "owner_answer": "YES_USE_PRODUCT_ID",
        "owner_answered_at": "2026-09-10T03:33:48Z",
        "note": "owner confirmed product_id == sell SKU",
    }


@pytest.fixture
def prior_c3b(tmp_path: Path) -> Path:
    sell = []
    for name in [
        "price_aud", "stock_qty", "delivery_options", "lead_time",
        "weight_g", "dimensions", "components_cost", "license_clearance",
    ]:
        sell.append({"field": name, "value": None, "status": "OWNER_REQUIRED", "source": "ABSENT"})
    sell.insert(4, _sku_row())
    doc = {
        "schema": "ziman_internal_cycle_outcome.v1",
        "task_id": "ZIMAN-INTERNAL-CYCLE-3b-20260910-SKU-CONFIRM",
        "cycle": "3b",
        "family": "F1_floral",
        "use_llm": False,
        "draft": {
            "proposal_id": "P-0d4aa821990a",
            "lineage": {
                "cycle2_draft_id": "P-ffcee157a933",
                "cycle3_draft_id": "P-0d4aa821990a",
            },
            "payload": {
                "draft_only": True,
                "publish": False,
                "cycle": 3,
                "product_family": "F1_floral",
                "body_source": "template",
                "sku_product_ids": [f"ZIM-F1-{i:02d}" for i in range(1, 19)],
            },
        },
        "sell_fields_table": sell,
        "review": {"verdict": "PASS_INTERNAL_PARTIAL_SELLFIELDS"},
        "owner_answers": [
            {"q": 5, "field": "sku", "answer": "YES_USE_PRODUCT_ID", "at": "2026-09-10T03:33:48Z"}
        ],
        "locks": {"publish": False, "hold_external": True, "external_send": False},
    }
    path = tmp_path / "prior-c3b.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
