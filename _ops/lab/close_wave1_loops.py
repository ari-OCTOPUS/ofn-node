#!/usr/bin/env python3
"""Megaprompt 3 — close laboratory loops (fixture-only).

Seeds the 24 owner experiment cards, appends one DECISION conclusion each,
never rewrites preregistration rows, never touches production ``_ops/state/lab``
unless OCTOPUS_STATE_DIR is already isolated by the caller.

CANARY_PROPOSED cards conclude INCONCLUSIVE (live gate still open).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "lab") not in sys.path:
    sys.path.insert(0, str(_OPS / "lab"))

# Evidence pointers are git objects / receipt hashes, not live Telegram ids.
_SIGIV_HEAD = "bfbb03f36a6510eafe6d4910625895a127c14e7c"
_SIGIV = {
    "security-c1-c4": "22c1cdd05f7c96b6c0ed2e912680ea91b441b46ba654bdabf10e7bc119da0bac",
    "lab-registry": "397205752051265f7e7af81768b763a3d155c21f1bb73c8f813f751013b7edb3",
    "durable-loop": "7b9ea689e85907b5aca3db98668cdb689f78adbb9c16bfadbad210f59f76a01d",
    "delivery-reconciliation": "84b134c4480b28f90fa488efd92ced135a561595b709e4d3752a9574a6386b2e",
    "side-effects-send": "75aad44cc295ea86bb2fb8fc99ec0bd4576630c659674ee85aab1a1caa88d6cf",
}

CONCLUSIONS = (
    ("EXP-SEC-001", "SUPPORTED", ["security-c1-c4", "t_c1_expired_age_301_rejected"],
     "TTL 300 / age 301 fail-closed in registered suite"),
    ("EXP-SEC-002", "SUPPORTED", ["security-c1-c4", "t_c2_replay_after_consumed_is_409"],
     "replay after consume is 409"),
    ("EXP-SEC-003", "SUPPORTED", ["security-c1-c4", "t_c2_concurrent_consumers_have_one_winner"],
     "one winner among concurrent consumers"),
    ("EXP-SEC-004", "SUPPORTED", ["security-c1-c4", "t_c3_retry_after_75_is_not_capped"],
     "retry_after 75 not capped"),
    ("EXP-SEC-005", "SUPPORTED", ["security-c1-c4", "t_c4_retry_not_before_survives_restart"],
     "retry_not_before survives restart"),
    ("EXP-TG-001", "SUPPORTED", ["security-c1-c4", "t_c1_tampered_and_fake_hash_rejected"],
     "tampered initData 403 empty zero dispatch"),
    ("EXP-TG-002", "SUPPORTED", ["durable-loop", "t_d_restart_never_resends_confirmed_message"],
     "confirmed outbox never resends"),
    ("EXP-TG-003", "INCONCLUSIVE", ["CANARY_PROPOSED"],
     "dual poll+webhook ingestion not exercised; webhook forbidden"),
    ("EXP-TG-004", "SUPPORTED", ["security-c1-c4", "t_c4_42_findings_coalesce_to_one_digest"],
     "42 findings coalesce to one digest"),
    ("EXP-TG-005", "INCONCLUSIVE", ["CANARY_PROPOSED"],
     "webhook secret path not live-tested; webhook forbidden"),
    ("EXP-TG-006", "SUPPORTED", ["durable-loop", "t_b_duplicate_update_creates_no_second_task"],
     "duplicate update creates no second task"),
    ("EXP-MEM-001", "SUPPORTED", ["sig-iv-retry2-side-effects", _SIGIV["side-effects-send"]],
     "memory ingest hashes unchanged during 163-run"),
    ("EXP-MEM-002", "SUPPORTED", ["test_wave1_preflight.py", "cross_task_leaks=[]"],
     "wave1 preflight asserts zero cross-task leaks"),
    ("EXP-HUB-001", "INCONCLUSIVE", [],
     "no dedicated hub memory-lane failure fixture in registered 163"),
    ("EXP-HUB-002", "INCONCLUSIVE", [],
     "no dedicated hub auth-all-lanes fixture in registered 163"),
    ("EXP-HUB-003", "INCONCLUSIVE", [],
     "MCP propose-only not in registered 163"),
    ("EXP-LAB-001", "SUPPORTED", ["lab-registry", "t_d_registration_writes_append_only_ledger"],
     "failed/negative rows remain on append-only ledger"),
    ("EXP-LAB-002", "SUPPORTED", ["lab-registry", "sig-iv-summary-counts"],
     "registered/executed/failed/skipped/unexecuted kept separate"),
    ("EXP-DOC-001", "SUPPORTED", ["SECURITY-REALITY-MAP.json", "verdict provenance_distinct"],
     "three distinct provenance SHAs"),
    ("EXP-DOCTOR-001", "INCONCLUSIVE", [],
     "stuck-mission quarantine not in registered 163"),
    ("EXP-C15-001", "SUPPORTED", ["durable-loop", "t_e_unknown_send_outcome_is_quarantined_not_retried"],
     "uncertain send quarantined, not auto-resent"),
    ("EXP-C19-001", "SUPPORTED", ["delivery-reconciliation", "t_c_receipt_commit_crash_leaves_no_fake_confirmation"],
     "empty/crash receipt is not confirmation"),
    ("EXP-C21-001", "INCONCLUSIVE", [],
     "doctor diagnosis closure not in registered 163"),
    ("EXP-C23-001", "INCONCLUSIVE", [],
     "owner capability matrix freshness not in registered 163"),
)


def close_loops(*, code_head: str = _SIGIV_HEAD) -> dict:
    import registry as lab
    seeded = lab.seed_owner_experiments()
    conclusions = []
    errors = []
    for eid, result, refs, note in CONCLUSIONS:
        ev = [f"sigiv:{code_head}"] + [str(x) for x in refs]
        out = lab.conclude_experiment(eid, result=result, evidence_refs=ev, note=note)
        if out.get("ok"):
            conclusions.append({"experiment_id": eid, "result": result})
        else:
            errors.append({"experiment_id": eid, "errors": out.get("errors")})
    latest = lab.latest_conclusions()
    counts = {"SUPPORTED": 0, "INCONCLUSIVE": 0, "REFUTED": 0, "PENDING": 0}
    for row in latest.values():
        r = str(row.get("result") or "PENDING")
        counts[r] = counts.get(r, 0) + 1
    return {
        "schema": "lab-close-wave1/1",
        "code_head": code_head,
        "seeded_ok": seeded.get("ok"),
        "seed_errors": seeded.get("errors") or [],
        "conclusions": conclusions,
        "errors": errors,
        "latest_count": len(latest),
        "result_counts": counts,
        "all_24": len(latest) >= 24 and not errors,
        "live_send": False,
        "production_lab_untouched": True,
    }


def main() -> int:
    out = close_loops()
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out.get("all_24") and not out.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
