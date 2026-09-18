"""Read-only check: EX1 criterion proposal facts versus existing receipts."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

SESSION = "09f879"
LOG = Path(r"F:\backup\debug-09f879.log")
LANE = Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907")
FACTS = LANE / "EX1-CRITERION-PROPOSAL.json"
EX1 = Path(r"F:\backup\09-LANES\MP-EXEC-EX1-EX2-20260907\EX1-VERIFICATION-RECEIPT.json")
LIVE = Path(r"F:\backup\09-LANES\MP-DEBUG-20260907\LIVE-READBACK.json")
MP = Path(r"C:\Users\Armin\Downloads\MEGAPROMPT-OCTOPUS-v3-EXECUTABLE-2026-09-07.md")
EXPECTED_MP_SHA = "ca736a4724ddac884fd39108dc6089e907fba6f1439ba61ff71cc7681cdaa4e3"


def _log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    rec = {
        "sessionId": SESSION,
        "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "runId": "ex1-criterion-facts",
        "hypothesisId": hypothesis_id,
    }
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    # #endregion


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    facts = _load(FACTS)
    ex1 = _load(EX1)
    live = _load(LIVE)
    failures: list[str] = []

    def fail(code: str) -> None:
        failures.append(code)

    # H-A: both records exist with agreed event/reason/seq
    live_targets = live["board_probe"]["snapshot"]["checks"]["target_records"]
    prefix_targets = live["board_probe"]["historical_prefix"]["checks"]["target_records"]
    agreed = {}
    for seq in ("194298", "194329"):
        live_fields = live_targets[seq]["safe_fields"]
        prefix_fields = prefix_targets[seq]["safe_fields"]
        ex1_row = ex1["target_records"][seq]["row"]
        proposed = facts["records"][seq]["safe_fields_agreed_by_both_receipts"]
        match = (
            live_fields.get("event") == prefix_fields.get("event") == ex1_row.get("event") == proposed.get("event")
            and live_fields.get("reason") == prefix_fields.get("reason") == ex1_row.get("reason") == proposed.get("reason")
            and live_fields.get("seq") == prefix_fields.get("seq") == ex1_row.get("seq") == proposed.get("seq")
        )
        if seq == "194298":
            match = match and live_fields.get("calib_tail") == prefix_fields.get("calib_tail") == ex1_row.get("calib_tail") == proposed.get("calib_tail")
        agreed[seq] = match
        if not match:
            fail(f"H-A-{seq}")
    _log(
        "H-A",
        "verify_ex1_facts.py:records",
        "both records exist with agreed event/reason/seq",
        {"agreed": agreed, "verdict": "CONFIRMED" if all(agreed.values()) else "REJECTED"},
    )

    # H-B: required per-record provenance absent on raw rows
    absent_ok = True
    absent_detail = {}
    for seq in ("194298", "194329"):
        present = live_targets[seq]["fields_present"]
        required = ["loaded_source_revision", "consumer_path", "read_receipt_id"]
        flags = {key: present.get(key) for key in required}
        absent_detail[seq] = flags
        if any(flags.values()):
            absent_ok = False
            fail(f"H-B-{seq}")
    _log(
        "H-B",
        "verify_ex1_facts.py:provenance",
        "required per-record provenance keys absent",
        {"fields_present": absent_detail, "verdict": "CONFIRMED" if absent_ok else "REJECTED"},
    )

    # H-C: receipt-level substitute exists on the later reader receipt, not on rows
    receipt_has = all(
        key in ex1 and ex1[key] not in (None, "")
        for key in ("read_receipt_id", "consumer_path", "loaded_source_revision")
    )
    contradiction_c2 = any(item.get("id") == "EX1-C2" for item in ex1.get("contradictions", []))
    proposal_says_substitute = facts["ledger_structure"].get("receipt_level_provenance_is_not_per_record") is True
    hc_ok = receipt_has and contradiction_c2 and proposal_says_substitute
    if not hc_ok:
        fail("H-C")
    _log(
        "H-C",
        "verify_ex1_facts.py:receipt-level",
        "reader receipt fields exist and are marked as not per-record",
        {
            "receipt_has_three_fields": receipt_has,
            "ex1_c2_recorded": contradiction_c2,
            "proposal_flag": proposal_says_substitute,
            "verdict": "CONFIRMED" if hc_ok else "REJECTED",
        },
    )

    # H-D: verify_chain E0 and writers are not a hash chain
    tool_e0 = "does NOT exist" in ex1.get("verify_method", "") or facts["ledger_structure"]["verify_chain_from_zero_tool"] == "E0_absent"
    writers = live["board_probe"]["writer_source"]
    no_hash = all(
        (not fn.get("contains_sha256")) and (not fn.get("contains_prev_hash"))
        for writer in writers
        for fn in writer.get("functions", [])
    )
    hd_ok = tool_e0 and no_hash and facts["ledger_structure"]["hash_chain_in_inspected_writers"] is False
    if not hd_ok:
        fail("H-D")
    _log(
        "H-D",
        "verify_ex1_facts.py:chain",
        "from-zero tool absent; inspected writers have no hash-chain",
        {"tool_e0": tool_e0, "writers_without_hash": no_hash, "verdict": "CONFIRMED" if hd_ok else "REJECTED"},
    )

    # H-E: 194329 mint_evidence/calib_tail absent; 194298 has calib_tail, not reason_code
    p298 = live_targets["194298"]["fields_present"]
    p329 = live_targets["194329"]["fields_present"]
    he_ok = (
        p298.get("calib_tail") is True
        and p298.get("reason_code") is False
        and p329.get("calib_tail") is False
        and p329.get("mint_evidence") is False
        and p329.get("reason_code") is False
        and live_targets["194329"]["mint_evidence_calib_tail_present"] is False
    )
    if not he_ok:
        fail("H-E")
    _log(
        "H-E",
        "verify_ex1_facts.py:mint-and-reason",
        "194298 has calib_tail not reason_code; 194329 lacks mint_evidence and calib_tail",
        {"p298": p298, "p329": p329, "verdict": "CONFIRMED" if he_ok else "REJECTED"},
    )

    # H-F: historical prefix fingerprint match and proposal does not claim PASS
    prefix = live["board_probe"]["historical_prefix"]
    prefix_ok = (
        prefix.get("matches_expected_sha256") is True
        and prefix.get("sha256") == facts["ledger_structure"]["historical_prefix_sha256"]
        and prefix.get("read_bytes") == facts["ledger_structure"]["historical_prefix_bytes"]
        and live["audit_verdict"]["ex1_original_acceptance"]
        == facts["original_verdict_this_proposal_does_not_change"]["ex1_original_acceptance"]
        and facts["status"] == "open"
        and facts["ex3"] == "not_started"
    )
    pass_guard = (
        facts["kind"] == "advisor_proposal"
        and facts["requires"] == "owner_decision"
        and "PASS" in facts["not"]
        and facts["recommended_option"] == "B_SPLIT_CRITERION"
    )
    mp_sha = hashlib.sha256(MP.read_bytes()).hexdigest() if MP.is_file() else None
    mp_ok = mp_sha == EXPECTED_MP_SHA
    text = MP.read_text(encoding="utf-8") if MP.is_file() else ""
    has_on_fail = "on_fail: کل lane متوقف" in text
    has_continue = "lane ادامه می‌دهد، متوقف نمی‌شود" in text
    hf_ok = prefix_ok and pass_guard and mp_ok and has_on_fail and has_continue
    if not hf_ok:
        fail("H-F")
    _log(
        "H-F",
        "verify_ex1_facts.py:prefix-and-proposal",
        "prefix fingerprint matches; proposal stays open and is not a PASS",
        {
            "prefix_match": prefix.get("matches_expected_sha256"),
            "mp_sha_match": mp_ok,
            "has_on_fail": has_on_fail,
            "has_section0_continue": has_continue,
            "proposal_kind": facts["kind"],
            "ex3": facts["ex3"],
            "verdict": "CONFIRMED" if hf_ok else "REJECTED",
        },
    )

    summary = {"failures": failures, "ok": not failures}
    _log("SUMMARY", "verify_ex1_facts.py:main", "proposal-vs-receipt check finished", summary)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
