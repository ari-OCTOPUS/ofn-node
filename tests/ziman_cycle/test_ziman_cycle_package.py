"""28 required cases for durable Ziman cycle repair package."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ofn.ziman_cycle.atomic_io import (
    SealedArtifactError,
    atomic_write_bytes,
    atomic_write_json,
    recover_interrupted_write,
    sha256_bytes,
    sha256_file,
)
from ofn.ziman_cycle.catalog import CatalogError, find_product, load_catalog, filter_family
from ofn.ziman_cycle.gates import GateError, GatePolicy, enforce_locks
from ofn.ziman_cycle.idempotency import make_idempotency_key
from ofn.ziman_cycle.runner import derive_draft_id, run_dry_run_cycle4
from ofn.ziman_cycle.sales_fields import (
    FieldRecord,
    FieldStatus,
    apply_validation,
    build_cycle4_sales_fields,
    validate_dimensions,
    validate_field,
    validate_license_clearance,
    validate_price_aud,
    validate_stock_qty,
)
from ofn.ziman_cycle.schema import OUTCOME_SCHEMA, SALES_FIELDS_SCHEMA, migrate_schema
from ofn.ziman_cycle.state_machine import CycleState, StateMachine, TransitionError
from ofn.ziman_cycle.verify import VerifyError, refuse_prior_cycle_as_new, verify_artifact


# --- catalog ---

def test_01_catalog_utf8(sample_catalog):
    cat = load_catalog(sample_catalog)
    assert len(filter_family(cat)) == 18


def test_02_catalog_utf8_sig(sample_catalog_bom):
    cat = load_catalog(sample_catalog_bom)
    assert find_product(cat, "ZIM-F1-01") is not None


def test_03_sku_found(sample_catalog):
    cat = load_catalog(sample_catalog)
    assert find_product(cat, "ZIM-F1-18")["family"] == "F1_floral"


def test_04_sku_missing(sample_catalog):
    cat = load_catalog(sample_catalog)
    assert find_product(cat, "ZIM-MISSING") is None


# --- sku confirm + owner required ---

def test_05_sku_confirm_preserved(prior_c3b, sample_catalog, tmp_out):
    result = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    doc = json.loads(Path(result["outcome_path"]).read_text(encoding="utf-8"))
    sku = next(r for r in doc["sell_fields_table"] if r["field"] == "sku")
    assert sku["status"] == "GROUNDED_OWNER_CONFIRMED"
    assert sku.get("owner_answer") == "YES_USE_PRODUCT_ID"


def test_06_eight_owner_required(prior_c3b, sample_catalog, tmp_out):
    result = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    doc = json.loads(Path(result["outcome_path"]).read_text(encoding="utf-8"))
    names = [
        "price_aud", "stock_qty", "delivery_options", "lead_time",
        "weight_g", "dimensions", "components_cost", "license_clearance",
    ]
    for n in names:
        row = next(r for r in doc["sell_fields_table"] if r["field"] == n)
        assert row["status"] == "OWNER_REQUIRED"
        assert row["value"] is None


def test_07_null_not_grounded():
    rec = apply_validation(FieldRecord(field_name="price_aud", value=None))
    assert rec.status == FieldStatus.OWNER_REQUIRED.value
    assert rec.status != FieldStatus.GROUNDED_FROM_CATALOG.value


def test_08_negative_price_rejected():
    errs = validate_price_aud(-1.0, currency="AUD")
    assert "price_aud_negative_rejected" in errs
    rec = apply_validation(FieldRecord(field_name="price_aud", value=-5, currency="AUD"))
    assert rec.status == FieldStatus.INVALID.value


def test_09_bad_stock_rejected():
    assert "stock_qty_negative_rejected" in validate_stock_qty(-1)
    assert "stock_qty_fractional_rejected" in validate_stock_qty(1.5)
    rec = apply_validation(FieldRecord(field_name="stock_qty", value=2.5))
    assert rec.status == FieldStatus.INVALID.value


def test_10_dimensions_no_unit():
    errs = validate_dimensions({"w": 10, "h": 20})
    assert "dimensions_unit_required" in errs


def test_11_license_no_evidence():
    errs = validate_license_clearance({"formal_clearance": None}, owner_confirmed=True, evidence=None)
    assert "license_clearance_evidence_required_for_final_confirm" in errs


def test_12_draft_id_persist(prior_c3b, sample_catalog, tmp_out):
    result = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    doc = json.loads(Path(result["outcome_path"]).read_text(encoding="utf-8"))
    lin = doc["draft"]["lineage"]
    assert lin["cycle2_draft_id"] == "P-ffcee157a933"
    assert lin["cycle3_draft_id"] == "P-0d4aa821990a"
    assert doc["draft"]["proposal_id"].startswith("P-")
    assert len(doc["draft"]["proposal_id"]) == 14  # P- + 12 hex
    # deterministic
    again = derive_draft_id("P-0d4aa821990a", result["previous_sha"], "4")
    assert again == doc["draft"]["proposal_id"]


def test_13_idempotent(prior_c3b, sample_catalog, tmp_out):
    r1 = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    r2 = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    assert r2["idempotent_hit"] is True
    assert r1["current_sha"] == r2["current_sha"]


def test_14_no_overwrite(tmp_path):
    p = tmp_path / "sealed.json"
    atomic_write_json(p, {"a": 1}, refuse_overwrite_if_different=True)
    with pytest.raises(SealedArtifactError):
        atomic_write_json(p, {"a": 2}, refuse_overwrite_if_different=True)
    # same content ok
    atomic_write_json(p, {"a": 1}, refuse_overwrite_if_different=True)


def test_15_sha_match(prior_c3b, sample_catalog, tmp_out):
    r = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    live = sha256_file(r["outcome_path"])
    assert live == r["current_sha"]
    v = verify_artifact(r["outcome_path"], expected_previous_sha=r["previous_sha"], receipt_path=r["receipt_path"])
    assert v["ok"] is True


def test_16_tamper_detect(prior_c3b, sample_catalog, tmp_out):
    r = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    path = Path(r["outcome_path"])
    # corrupt file but leave sidecar
    path.write_text(path.read_text(encoding="utf-8").replace("READY_FOR_OWNER_INPUT_INTERNAL", "TAMPERED"), encoding="utf-8")
    with pytest.raises(VerifyError):
        verify_artifact(path, receipt_path=r["receipt_path"], expected_cycle="4")


def test_17_interrupted_write_recovery(tmp_path):
    p = tmp_path / "recover.bin"
    data = b"complete-payload-v1"
    # simulate partial tmp left behind
    partial = p.parent / (p.name + ".partial.tmp")
    partial.write_bytes(b"partial")
    digest = recover_interrupted_write(p, data)
    assert p.read_bytes() == data
    assert digest == sha256_bytes(data)


def test_18_windows_paths(tmp_path):
    # Path objects with backslash-style names still work via pathlib
    nested = tmp_path / "backup" / "00-SEASON" / "ziman-internal-cycle-4"
    nested.mkdir(parents=True)
    target = nested / "artifact.json"
    atomic_write_json(target, {"ok": True})
    assert target.exists()
    assert sha256_file(target)


def test_19_no_pythonpath_hack():
    """Package imports from worktree root without setting PYTHONPATH."""
    # This test file already imported ofn.ziman_cycle.*; additionally spawn clean subprocess
    # with cwd=repo root (parent of ofn) — conftest lives under tests/, repo root is parents[2]
    repo_root = Path(__file__).resolve().parents[2]
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        [sys.executable, "-c", "import ofn.ziman_cycle; print(ofn.ziman_cycle.__version__)"],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "0.1.0" in proc.stdout


def test_20_external_hold():
    with pytest.raises(GateError):
        GatePolicy(hold_external=True, external_send="email").check()
    enforce_locks({"hold_external": True, "external_send": "none", "publish": False, "use_llm": False})


def test_21_publish_blocked():
    with pytest.raises(GateError):
        GatePolicy(publish=True).check()
    sm = StateMachine(CycleState.READY_INTERNAL)
    with pytest.raises(TransitionError):
        sm.assert_fail_closed_publish(True)


def test_22_use_llm_false():
    with pytest.raises(GateError):
        GatePolicy(use_llm=True).check()
    policy = GatePolicy(use_llm=False)
    policy.check()


def test_23_no_secrets_in_logs(prior_c3b, sample_catalog, tmp_out, capsys):
    r = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    dumped = json.dumps(r)
    for bad in ("BEGIN RSA", "api_key", "password=", "secret_token"):
        assert bad.lower() not in dumped.lower()


def test_24_malformed_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not-json", encoding="utf-8")
    with pytest.raises(Exception):
        load_catalog(p)
    with pytest.raises(VerifyError):
        verify_artifact(p)


def test_25_schema_migrate_load():
    doc = migrate_schema({"schema": "ziman_internal_cycle_outcome.v0", "cycle": "3"})
    assert doc["schema"] == OUTCOME_SCHEMA
    doc2 = migrate_schema({"schema": SALES_FIELDS_SCHEMA})
    assert doc2["schema"] == SALES_FIELDS_SCHEMA
    with pytest.raises(ValueError):
        migrate_schema({"schema": "totally.unknown"})


def test_26_retry_no_duplicate(prior_c3b, sample_catalog, tmp_out):
    r1 = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    # count files before retry
    before = sorted(p.name for p in tmp_out.glob("ZIMAN-INTERNAL-CYCLE-4*"))
    r2 = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    after = sorted(p.name for p in tmp_out.glob("ZIMAN-INTERNAL-CYCLE-4*"))
    assert before == after
    assert r2["idempotent_hit"] is True
    assert r1["current_sha"] == r2["current_sha"]


def test_27_cycle_number(prior_c3b, sample_catalog, tmp_out):
    r = run_dry_run_cycle4(prior_path=prior_c3b, catalog_path=sample_catalog, out_dir=tmp_out)
    doc = json.loads(Path(r["outcome_path"]).read_text(encoding="utf-8"))
    assert str(doc["cycle"]) == "4"
    assert doc["draft"]["payload"]["cycle"] == 4
    assert r["verdict"] == "READY_FOR_OWNER_INPUT_INTERNAL"


def test_28_verifier_wont_consume_prior_as_new(prior_c3b):
    with pytest.raises(VerifyError):
        refuse_prior_cycle_as_new(prior_c3b, claimed_cycle="4")
    with pytest.raises(VerifyError):
        verify_artifact(prior_c3b, expected_cycle="4", refuse_prior_as_new=True)
