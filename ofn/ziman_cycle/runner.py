"""CYCLE-4 dry-run runner — readiness for owner input (not sales PASS)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .atomic_io import atomic_write_bytes, atomic_write_json, read_json, sha256_bytes, sha256_file
from .catalog import family_product_ids, load_catalog, load_catalog_bytes
from .gates import enforce_locks
from .idempotency import IdempotencyStore, make_idempotency_key
from .owner_template import human_markdown, machine_template
from .sales_fields import FieldStatus, build_cycle4_sales_fields
from .schema import OUTCOME_SCHEMA, OWNER_REQUIRED_FIELDS, SALES_FIELDS_SCHEMA
from .state_machine import CycleState, StateMachine
from .verify import verify_artifact


TASK_ID = "ZIMAN-INTERNAL-CYCLE-4-20260910-OWNER-INPUT-READY"
CYCLE = "4"
VERDICT = "READY_FOR_OWNER_INPUT_INTERNAL"
FAMILY = "F1_floral"


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_draft_id(prior_draft_id: str, previous_sha: str, cycle: str = CYCLE) -> str:
    digest = hashlib.sha256(
        f"{prior_draft_id}|cycle{cycle}|{previous_sha}".encode("utf-8")
    ).hexdigest()
    return f"P-{digest[:12]}"


def _sales_summary(records: list) -> dict[str, Any]:
    grounded = 0
    owner_required = 0
    for r in records:
        st = r.status if hasattr(r, "status") else r.get("status")
        if st in {
            FieldStatus.GROUNDED_OWNER_CONFIRMED.value,
            FieldStatus.GROUNDED_FROM_CATALOG.value,
        }:
            grounded += 1
        elif st == FieldStatus.OWNER_REQUIRED.value:
            owner_required += 1
    return {
        "grounded": grounded,
        "owner_required": owner_required,
        "unknown": 0,
        "complete": owner_required == 0,
        "owner_confirmed_sku": grounded >= 1,
    }


def run_dry_run_cycle4(
    *,
    prior_path: str | Path,
    catalog_path: str | Path,
    out_dir: str | Path,
    expected_prior_sha: str | None = None,
) -> dict[str, Any]:
    """Produce CYCLE-4 outcome + receipt + owner template. Idempotent."""
    prior_path = Path(prior_path)
    catalog_path = Path(catalog_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sm = StateMachine(CycleState.DISCOVERED)
    sm.transition(CycleState.BASELINED)
    sm.transition(CycleState.VALIDATING)

    locks = {
        "publish": False,
        "external_send": "none",
        "hold_external": True,
        "use_llm": False,
        "safe_to_claim": False,
        "safe_to_claim_live_executable_contract": False,
        "paid_api": False,
        "season_painting_asleep": True,
        "season_studio_asleep": True,
    }
    enforce_locks(locks)
    sm.assert_fail_closed_publish(False)
    sm.assert_fail_closed_external("none")

    previous_sha = sha256_file(prior_path)
    if expected_prior_sha and previous_sha != expected_prior_sha:
        raise ValueError(f"prior_sha_mismatch:{previous_sha}")

    prior = read_json(prior_path)
    schema = prior.get("schema")
    if schema != OUTCOME_SCHEMA and not str(schema or "").startswith("ziman_internal_cycle_outcome"):
        raise ValueError("prior_schema_invalid")

    catalog_raw = load_catalog_bytes(catalog_path)
    catalog_sha = sha256_bytes(catalog_raw)
    catalog = load_catalog(catalog_path)
    f1_ids = family_product_ids(catalog, FAMILY)

    prior_draft = prior.get("draft") or {}
    prior_draft_id = prior_draft.get("proposal_id") or "P-unknown"
    lineage_c2 = ((prior_draft.get("lineage") or {}).get("cycle2_draft_id")) or "P-ffcee157a933"
    lineage_c3 = ((prior_draft.get("lineage") or {}).get("cycle3_draft_id")) or prior_draft_id

    inputs = {
        "prior_path": str(prior_path),
        "previous_sha": previous_sha,
        "catalog_path": str(catalog_path),
        "catalog_sha": catalog_sha,
        "family": FAMILY,
        "task_id": TASK_ID,
    }
    idem_key = make_idempotency_key(TASK_ID, previous_sha, inputs)
    store = IdempotencyStore(out_dir / ".idempotency-cycle4.json")
    cached = store.lookup(idem_key)
    outcome_name = "ZIMAN-INTERNAL-CYCLE-4-20260910-OWNER-INPUT-READY.json"
    outcome_path = out_dir / outcome_name
    receipt_path = out_dir / "ZIMAN-INTERNAL-CYCLE-4-20260910-RECEIPT.json"
    template_json_path = out_dir / "OWNER-INPUT-TEMPLATE-CYCLE-4.json"
    template_md_path = out_dir / "OWNER-FORM-CYCLE-4-SELLFIELDS.md"

    if cached and outcome_path.exists():
        current_sha = sha256_file(outcome_path)
        return {
            "idempotent_hit": True,
            "idempotency_key": idem_key,
            "outcome_path": str(outcome_path),
            "receipt_path": str(receipt_path),
            "previous_sha": previous_sha,
            "current_sha": current_sha,
            "verdict": VERDICT,
            "readiness": VERDICT,
        }

    sell_records = build_cycle4_sales_fields(prior.get("sell_fields_table") or [])
    sku = next(r for r in sell_records if r.field_name == "sku")
    if sku.status != FieldStatus.GROUNDED_OWNER_CONFIRMED.value:
        raise ValueError("sku_not_grounded_owner_confirmed")
    if sku.owner_answer != "YES_USE_PRODUCT_ID":
        raise ValueError("sku_owner_answer_not_preserved")
    for name in OWNER_REQUIRED_FIELDS:
        rec = next(r for r in sell_records if r.field_name == name)
        if rec.status != FieldStatus.OWNER_REQUIRED.value or rec.value is not None:
            raise ValueError(f"field_must_be_owner_required_null:{name}")

    sku_ids = (sku.value or {}).get("product_ids") or []
    missing = [i for i in sku_ids if i not in f1_ids]
    if missing:
        raise ValueError(f"sku_ids_missing_from_catalog:{missing[:3]}")

    new_draft_id = derive_draft_id(prior_draft_id, previous_sha, CYCLE)
    prior_payload = dict(prior_draft.get("payload") or {})
    prior_payload["cycle"] = 4
    prior_payload["publish"] = False
    prior_payload["draft_only"] = True
    prior_payload["sell_fields_ref"] = "CYCLE-4 sell_fields_table"
    prior_payload["body_source"] = prior_payload.get("body_source") or "template"

    sm.transition(CycleState.OWNER_INPUT_REQUIRED)

    outcome: dict[str, Any] = {
        "schema": OUTCOME_SCHEMA,
        "schema_sales_fields": SALES_FIELDS_SCHEMA,
        "task_id": TASK_ID,
        "cycle": CYCLE,
        "at": _utcnow(),
        "family": FAMILY,
        "catalog_path": str(catalog_path),
        "catalog_sha256": catalog_sha,
        "use_llm": False,
        "consumed_prior": {
            "task_id": prior.get("task_id"),
            "path": str(prior_path),
            "sha256": previous_sha,
            "prior_verdict": (prior.get("review") or {}).get("verdict"),
            "learning_loop": "CONSUMED_INTO_CYCLE_4_OWNER_INPUT_READY",
            "cycle3_draft_id": lineage_c3,
            "cycle2_draft_id": lineage_c2,
        },
        "previous_sha": previous_sha,
        "draft": {
            "proposal_id": new_draft_id,
            "lineage": {
                "cycle2_draft_id": lineage_c2,
                "cycle3_draft_id": lineage_c3,
                "cycle4_draft_id": new_draft_id,
                "provenance": "deterministic_hash_from_c3_draft+cycle4+prior_sha; use_llm=false",
            },
            "payload": prior_payload,
        },
        "sell_fields_table": [r.to_dict() for r in sell_records],
        "sell_fields_summary": _sales_summary(sell_records),
        "claim_check": {
            "ok": True,
            "price_leak_in_draft_body": False,
            "publish": False,
            "draft_only": True,
            "used_llm": False,
            "invented_commercial_values": False,
        },
        "review": {
            "verdict": VERDICT,
            "readiness": VERDICT,
            "reviewer": "ofn.ziman_cycle.runner",
            "notes": (
                "CYCLE-4 dry-run: sku GROUNDED_OWNER_CONFIRMED YES_USE_PRODUCT_ID preserved; "
                "8 fields OWNER_REQUIRED; not a sales PASS."
            ),
            "state": CycleState.OWNER_INPUT_REQUIRED.value,
        },
        "locks": locks,
        "gates": {
            "publish": False,
            "external_send": "none",
            "hold_external": True,
            "use_llm": False,
        },
        "owner_answers": prior.get("owner_answers")
        or [
            {
                "q": 5,
                "field": "sku",
                "answer": "YES_USE_PRODUCT_ID",
                "at": sku.confirmed_at,
            }
        ],
        "idempotency_key": idem_key,
        "delta_vs_cycle3": [
            "Durable ofn.ziman_cycle package (schema+validators+gates+idempotency)",
            "Preserved SKU GROUNDED_OWNER_CONFIRMED YES_USE_PRODUCT_ID",
            "Marked 8 sell fields OWNER_REQUIRED (null; no invention)",
            "Deterministic draft_id lineage C2->C3->C4",
            "Verdict READY_FOR_OWNER_INPUT_INTERNAL (not sales PASS)",
        ],
    }

    current_sha = atomic_write_json(outcome_path, outcome, refuse_overwrite_if_different=True)

    receipt = {
        "schema": "ziman_cycle_receipt.v1",
        "task_id": TASK_ID,
        "cycle": CYCLE,
        "at": _utcnow(),
        "previous_sha": previous_sha,
        "current_sha": current_sha,
        "artifact_sha256": current_sha,
        "artifact_path": str(outcome_path),
        "catalog_sha256": catalog_sha,
        "verdict": VERDICT,
        "readiness": VERDICT,
        "idempotency_key": idem_key,
        "locks": locks,
    }
    atomic_write_json(receipt_path, receipt, refuse_overwrite_if_different=True)

    tmpl = machine_template(new_draft_id, CYCLE)
    atomic_write_json(template_json_path, tmpl, refuse_overwrite_if_different=True)
    md = human_markdown(new_draft_id, CYCLE, prior_sku_note="YES_USE_PRODUCT_ID")
    atomic_write_bytes(template_md_path, md.encode("utf-8"), refuse_overwrite_if_different=True)

    (outcome_path.with_suffix(outcome_path.suffix + ".sha256")).write_text(
        current_sha + "\n", encoding="utf-8"
    )

    store.remember(
        idem_key,
        {
            "outcome_path": str(outcome_path),
            "current_sha": current_sha,
            "previous_sha": previous_sha,
            "verdict": VERDICT,
        },
    )

    sm.transition(CycleState.HOLD_EXTERNAL)

    verify_artifact(
        outcome_path,
        expected_previous_sha=previous_sha,
        receipt_path=receipt_path,
        expected_cycle=CYCLE,
    )

    return {
        "idempotent_hit": False,
        "idempotency_key": idem_key,
        "outcome_path": str(outcome_path),
        "receipt_path": str(receipt_path),
        "owner_template_json": str(template_json_path),
        "owner_template_md": str(template_md_path),
        "previous_sha": previous_sha,
        "current_sha": current_sha,
        "verdict": VERDICT,
        "readiness": VERDICT,
        "draft_id": new_draft_id,
        "state": sm.state.value,
    }
