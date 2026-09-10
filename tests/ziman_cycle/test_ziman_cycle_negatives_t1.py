"""P2-T1 invent/empty NEGATIVE inventory — fail-closed paths.

Closes QA caveat T1: explicit invent + empty coverage with those markers in names.
Fixtures never invent commercial sell VALUES — only null / invalid / refuse paths.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ofn.ziman_cycle.atomic_io import SealedArtifactError, atomic_write_json
from ofn.ziman_cycle.catalog import CatalogError, load_catalog
from ofn.ziman_cycle.gates import GateError, GatePolicy, enforce_locks
from ofn.ziman_cycle.runner import run_dry_run_cycle4
from ofn.ziman_cycle.sales_fields import (
    FieldRecord,
    FieldStatus,
    apply_validation,
    build_cycle4_sales_fields,
    owner_required_null,
)
from ofn.ziman_cycle.schema import OWNER_REQUIRED_FIELDS
from ofn.ziman_cycle.verify import VerifyError, refuse_prior_cycle_as_new, verify_artifact


def _sku_row():
    return {
        "field": "sku",
        "value": {
            "family": "F1_floral",
            "product_ids": [f"ZIM-F1-{i:02d}" for i in range(1, 19)],
            "count": 18,
        },
        "status": "GROUNDED_OWNER_CONFIRMED",
        "owner_answer": "YES_USE_PRODUCT_ID",
    }


def test_t1_invent_non_null_owner_required_stripped_by_build():
    """Invented non-null OWNER_REQUIRED prior values must not survive cycle-4 build."""
    prior = [_sku_row()]
    for name in OWNER_REQUIRED_FIELDS:
        prior.append(
            {
                "field": name,
                "value": 99.0 if name == "price_aud" else "INVENTED_PLACEHOLDER",
                "status": "GROUNDED_FROM_CATALOG",
                "source": "invent_attempt",
            }
        )
    records = build_cycle4_sales_fields(prior)
    by = {r.field_name: r for r in records}
    assert by["sku"].status == FieldStatus.GROUNDED_OWNER_CONFIRMED.value
    for name in OWNER_REQUIRED_FIELDS:
        assert by[name].value is None, name
        assert by[name].status == FieldStatus.OWNER_REQUIRED.value, name


def test_t1_invent_price_aud_without_owner_stays_ungrounded():
    """Non-null price without owner confirm must not become grounded invent."""
    rec = apply_validation(FieldRecord(field_name="price_aud", value=42.0, currency="AUD"))
    assert rec.status not in {
        FieldStatus.GROUNDED_FROM_CATALOG.value,
        FieldStatus.GROUNDED_OWNER_CONFIRMED.value,
    }
    null_rec = owner_required_null("price_aud")
    assert null_rec.value is None
    assert null_rec.status == FieldStatus.OWNER_REQUIRED.value


def test_t1_empty_catalog_products_list_refuses_dry_run(prior_c3b, tmp_out, tmp_path):
    """Empty catalog products list → refuse (sku ids missing), no invent fill."""
    empty_cat = tmp_path / "empty-catalog.json"
    empty_cat.write_text(json.dumps({"products": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="sku_ids_missing_from_catalog"):
        run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=empty_cat, out_dir=tmp_out)


def test_t1_empty_catalog_missing_products_key(tmp_path):
    """Invalid/empty catalog shape without products key → CatalogError."""
    p = tmp_path / "bad-empty.json"
    p.write_text(json.dumps({"stats": {}}), encoding="utf-8")
    with pytest.raises(CatalogError, match="catalog_products_missing"):
        load_catalog(p)


def test_t1_empty_catalog_root_not_object(tmp_path):
    p = tmp_path / "list-catalog.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(CatalogError, match="catalog_root_not_object"):
        load_catalog(p)


def test_t1_gate_elevation_safe_to_claim_fail_closed():
    with pytest.raises(GateError, match="safe_to_claim"):
        GatePolicy(safe_to_claim=True).check()
    with pytest.raises(GateError):
        enforce_locks(
            {
                "safe_to_claim": True,
                "publish": False,
                "external_send": "none",
                "hold_external": True,
            }
        )


def test_t1_gate_elevation_publish_external_fail_closed():
    with pytest.raises(GateError, match="publish_blocked"):
        GatePolicy(publish=True).check()
    with pytest.raises(GateError, match="external_send"):
        GatePolicy(hold_external=True, external_send="telegram").check()


def test_t1_sealed_overwrite_refuse(tmp_path):
    """Sealed artifact overwrite with different bytes must refuse."""
    p = tmp_path / "sealed-outcome.json"
    atomic_write_json(p, {"cycle": "4", "value": None}, refuse_overwrite_if_different=True)
    with pytest.raises(SealedArtifactError):
        atomic_write_json(
            p,
            {"cycle": "4", "value": "INVENTED"},
            refuse_overwrite_if_different=True,
        )


def test_t1_prior_as_new_refuse(prior_c3b):
    """Prior cycle artifact must not be consumed as cycle-4 new."""
    with pytest.raises(VerifyError, match="refuse_consuming_prior_cycle_as_new"):
        refuse_prior_cycle_as_new(prior_c3b, claimed_cycle="4")
    with pytest.raises(VerifyError, match="refuse_consuming_prior_cycle_as_new"):
        verify_artifact(prior_c3b, expected_cycle="4", refuse_prior_as_new=True)


def test_t1_dry_run_refuses_to_emit_invented_owner_required(prior_c3b, sample_catalog, tmp_out):
    """Dry-run strips invent poison from prior; invented_commercial_values stays false."""
    prior = json.loads(Path(prior_c3b).read_text(encoding="utf-8"))
    for row in prior["sell_fields_table"]:
        if row.get("field") in OWNER_REQUIRED_FIELDS:
            row["value"] = 123
            row["status"] = "GROUNDED_FROM_CATALOG"
    poisoned = Path(prior_c3b).with_name("prior-c3b-invent-poison.json")
    poisoned.write_text(json.dumps(prior), encoding="utf-8")
    result = run_dry_run_cycle4(prior_path=poisoned, catalog_path=sample_catalog, out_dir=tmp_out)
    doc = json.loads(Path(result["outcome_path"]).read_text(encoding="utf-8"))
    assert doc["claim_check"]["invented_commercial_values"] is False
    for row in doc["sell_fields_table"]:
        if row["field"] in OWNER_REQUIRED_FIELDS:
            assert row["value"] is None
            assert row["status"] == "OWNER_REQUIRED"
