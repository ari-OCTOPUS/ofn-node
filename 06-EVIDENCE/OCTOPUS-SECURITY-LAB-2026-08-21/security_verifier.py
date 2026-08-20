#!/usr/bin/env python3
"""Independent security verifier — reads exported artifacts only.

This script imports no patch-internal test helpers and executes no fixtures. It
re-derives the verdict from the receipts/summary/side-effect artifacts and the
preregistry, so it is a different reader than the patch author's own suite.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHECKS: list[tuple[str, bool]] = []


def _read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _read_lines(name):
    return [json.loads(x) for x in (ROOT / name).read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    summary = _read("SECURITY-TEST-SUMMARY.json")
    receipts = _read_lines("SECURITY-TEST-RECEIPTS.jsonl")
    side = _read("SECURITY-ZERO-SIDE-EFFECTS.json")
    reality = _read("SECURITY-REALITY-MAP.json")
    baseline = _read("SECURITY-FAILING-TEST-BASELINE.json")
    prereg = _read_lines("SECURITY-EXPERIMENT-PREREGISTRY.jsonl")

    head = summary.get("code_head")
    CHECKS.append(("all_receipts_pass", bool(receipts) and all(r.get("verdict") == "PASS" for r in receipts)))
    CHECKS.append(("receipts_nonempty", all(r.get("output_sha256") for r in receipts)))
    CHECKS.append(("receipts_match_head", all(r.get("code_head") == head for r in receipts)))
    CHECKS.append(("registered_equals_executed", summary.get("registered") == summary.get("executed")))
    CHECKS.append(("failed_zero", summary.get("failed") == 0))
    CHECKS.append(("baseline_was_red", baseline.get("expected_red_before_patch") is True and baseline.get("failed", 0) > 0))
    CHECKS.append(("preregistered_experiments", len(prereg) >= 6))
    CHECKS.append(("memory_unchanged", side.get("memory_unchanged") is True))
    CHECKS.append(("miniapp_hits_unchanged", side.get("miniapp_hits_unchanged") is True))
    CHECKS.append(("test_live_sends_zero", side.get("test_live_telegram_sends") == 0))
    CHECKS.append(("send_log_appends_are_edits", side.get("send_log_append_classification", {}).get("all_periodic_edits") is True))
    CHECKS.append(("wave1_locked", side.get("wave1_unlocked") is False))
    CHECKS.append(("paid_calls_zero", side.get("paid_calls") == 0))
    CHECKS.append(("webhook_not_activated", side.get("webhook_activated") is False))
    CHECKS.append(("provenance_distinct", len({reality.get("initial_document_commit"),
                                               reality.get("security_correction_commit"),
                                               reality.get("provenance_commit")}) == 3))

    failed = [name for name, ok in CHECKS if not ok]
    # The verifier is a different reader, but not a different identity/agent.
    verifier_independent = False
    confirmed = not failed
    result = {
        "schema": "security-independent-verifier/1",
        "generated_at": "2026-08-21T09:20:00Z",
        "code_head": head,
        "confirmed": confirmed,
        "failed_checks": failed,
        "checks": dict(CHECKS),
        "verifier_independent": verifier_independent,
        "terminal_state": ("SECURITY_SHADOW_PASS" if confirmed and verifier_independent
                           else ("IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING" if confirmed
                                 else "FAILED_SAFE")),
        "note": ("All artifact checks pass. verifier_independent=false because the "
                 "same agent authored the patch and this reader; a separate identity "
                 "must sign for SECURITY_SHADOW_PASS."),
    }
    (ROOT / "SECURITY-INDEPENDENT-VERIFIER.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"confirmed": confirmed, "failed_checks": failed,
                      "terminal_state": result["terminal_state"]}, ensure_ascii=False))
    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
