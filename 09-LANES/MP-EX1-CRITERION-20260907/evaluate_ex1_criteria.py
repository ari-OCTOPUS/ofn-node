"""Local EX1 criterion evaluator. Reads prior receipts only. No SSH, no ledger write."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

LANE = Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907")
LIVE = Path(r"F:\backup\09-LANES\MP-DEBUG-20260907\LIVE-READBACK.json")
EX1 = Path(r"F:\backup\09-LANES\MP-EXEC-EX1-EX2-20260907\EX1-VERIFICATION-RECEIPT.json")
ORDER = Path(r"C:\Users\Armin\Downloads\MEGAPROMPT-OCTOPUS-v3-EXECUTABLE-2026-09-07.md")
EXPECTED_ORDER_SHA = "ca736a4724ddac884fd39108dc6089e907fba6f1439ba61ff71cc7681cdaa4e3"
REQUIRED_PROVENANCE = ("loaded_source_revision", "consumer_path", "read_receipt_id")
EXPECTED_TAIL = ["unresolved", "confirmed", "unresolved"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _present(snapshot: dict, seq: str, key: str) -> bool:
    return bool(snapshot["checks"]["target_records"][seq]["fields_present"].get(key))


def main() -> int:
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    ex1 = json.loads(EX1.read_text(encoding="utf-8"))
    board = live["board_probe"]
    snap = board["snapshot"]
    prefix = board["historical_prefix"]
    rec_live = snap["checks"]["target_records"]
    rec_prefix = prefix["checks"]["target_records"]
    rec_ex1 = ex1["target_records"]
    order_sha = _sha256(ORDER) if ORDER.is_file() else "MISSING"
    a298 = rec_live["194298"]["safe_fields"]
    a329 = rec_live["194329"]["safe_fields"]
    existence = {
        "seq_194298_in_live": "194298" in rec_live,
        "seq_194329_in_live": "194329" in rec_live,
        "event_194298": a298.get("event"),
        "event_329": a329.get("event"),
        "event_194298_matches": a298.get("event") == "standing_go_halted",
        "event_194329_matches": a329.get("event") == "standing_go_minted",
        "line_equals_seq_298": rec_live["194298"]["line"] == 194298,
        "line_equals_seq_329": rec_live["194329"]["line"] == 194329,
        "prefix_same_events": rec_prefix["194298"]["safe_fields"].get("event") == a298.get("event")
        and rec_prefix["194329"]["safe_fields"].get("event") == a329.get("event"),
        "raw_line_sha256_194298": rec_live["194298"]["raw_line_sha256"],
        "raw_line_sha256_194329": rec_live["194329"]["raw_line_sha256"],
    }
    tail = a298.get("calib_tail")
    b298 = {
        "reason": a298.get("reason"),
        "reason_matches_report": a298.get("reason") == "calibration_error_ge_0.5",
        "calib_tail": tail,
        "calib_tail_matches_report": tail == EXPECTED_TAIL,
        "reason_code_present_live": _present(snap, "194298", "reason_code"),
        "reason_code_present_prefix": _present(prefix, "194298", "reason_code"),
        "reason_is_not_reason_code": True,
    }
    ex1_329_row = rec_ex1["194329"]["row"]
    c329 = {
        "reason": a329.get("reason"),
        "reason_matches": a329.get("reason") == "internal_pulse",
        "calib_tail_present_live": _present(snap, "194329", "calib_tail"),
        "mint_evidence_present_live": _present(snap, "194329", "mint_evidence"),
        "mint_evidence_calib_tail_present": rec_live["194329"]["mint_evidence_calib_tail_present"],
        "owner_go_id_in_ex1_receipt_row": ex1_329_row.get("owner_go_id"),
        "owner_go_id_in_debug_safe_fields": "owner_go_id" in a329,
        "debug_safe_field_filter": ["event", "reason", "reason_code", "seq", "calib_tail"],
        "owner_go_id_status": "measured_in_ex1_receipt_only_debug_probe_filtered_it",
    }
    trio = {}
    for seq in ("194298", "194329"):
        trio[seq] = {
            key: {"live": _present(snap, seq, key), "prefix": _present(prefix, seq, key)}
            for key in REQUIRED_PROVENANCE
        }
    expects = {
        "both_records_exist": existence["event_194298_matches"] and existence["event_194329_matches"],
        "calib_tail_194298_matches_report": b298["calib_tail_matches_report"],
        "reason_code_in_both_records": _present(snap, "194298", "reason_code")
        and _present(snap, "194329", "reason_code"),
        "provenance_trio_in_194298": all(trio["194298"][k]["live"] for k in REQUIRED_PROVENANCE),
        "provenance_trio_in_194329": all(trio["194329"][k]["live"] for k in REQUIRED_PROVENANCE),
        "mint_evidence_calib_tail_on_194329": rec_live["194329"]["mint_evidence_calib_tail_present"],
        "specified_verify_chain_ok": False,
        "seq_monotonic_on_observed_bytes": snap["checks"]["seq_non_increment_breaks"] == 0
        and snap["checks"]["parse_errors"] == 0,
    }
    literal_pass = all(
        [
            expects["both_records_exist"],
            expects["calib_tail_194298_matches_report"],
            expects["reason_code_in_both_records"],
            expects["provenance_trio_in_194298"],
            expects["provenance_trio_in_194329"],
            expects["mint_evidence_calib_tail_on_194329"],
            expects["specified_verify_chain_ok"],
        ]
    )
    summary = {
        "schema": "octopus.ex1.criterion_eval.v1",
        "lane": "MP-EX1-CRITERION-20260907",
        "gov_version": "V8",
        "ladder": "L2",
        "kind": "advisor_proposal_input",
        "order_sha256": order_sha,
        "literal_ex1_pass": literal_pass,
        "expects": expects,
        "existence": existence,
        "record_194298": b298,
        "record_194329": c329,
        "provenance": trio,
        "sources": {
            "live_readback": str(LIVE),
            "ex1_receipt": str(EX1),
            "live_sha256": _sha256(LIVE),
            "ex1_sha256": _sha256(EX1),
        },
    }
    layers = {
        "schema": "octopus.ex1.three_results.v1",
        "lane": "MP-EX1-CRITERION-20260907",
        "kind": "advisor_proposal_input",
        "owner_instruction": "keep_both_records_and_receipts; do_not_drop_from_baseline; do_not_rerun_same_test_unchanged; split_three_results; no_pass_if_any_clause_unmet",
        "layer_1_existence_and_content": {
            "verdict": "MEASURED_WITHIN_RECEIPT_KEYS_ONLY",
            "pass_name_forbidden": "EX1_PASS",
            "194298": {
                "keys_measured": ["event", "reason", "seq", "calib_tail"],
                "event": existence["event_194298"],
                "reason": b298["reason"],
                "calib_tail": b298["calib_tail"],
                "raw_line_sha256": existence["raw_line_sha256_194298"],
            },
            "194329": {
                "keys_measured_in_debug_safe_fields": ["event", "reason", "seq"],
                "event": existence["event_329"],
                "reason": c329["reason"],
                "owner_go_id": {
                    "ex1_receipt": c329["owner_go_id_in_ex1_receipt_row"],
                    "debug_safe_fields": None,
                    "status": "open",
                },
                "raw_line_sha256": existence["raw_line_sha256_194329"],
            },
        },
        "layer_2_halt_and_mint_modes": {
            "verdict": "TWO_MODES_OBSERVED_NOT_A_RATE_OR_QUALITY_CLAIM",
            "halt_seq": 194298,
            "mint_seq": 194329,
            "not_claimed": ["rate", "stability", "decision_quality", "scientific_calibration"],
        },
        "layer_3_ex1_original_contract": {
            "verdict": "NOT_PASSED",
            "literal_ex1_pass": literal_pass,
            "unmet_or_contradicted": [
                "reason_code key absent on both records",
                "loaded_source_revision/consumer_path/read_receipt_id absent on both records",
                "mint_evidence.calib_tail absent on 194329",
                "tools.verify_chain --from-zero is E0; specified status=OK not obtained",
            ],
            "met": [
                "both records exist",
                "194298 calib_tail matches prior report list",
                "seq-monotonic on observed snapshot bytes (not the specified verifier)",
            ],
        },
        "ex3_started": False,
        "baseline_records_retained": True,
    }
    (LANE / "CRITERION-EVAL.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    (LANE / "THREE-RESULTS.json").write_text(
        json.dumps(layers, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
