#!/usr/bin/env python3
"""Build OWNER_SIGNATURE_BUNDLE_V1 — complete owner signature ceremony (2026-08-21).

Deterministic builder: reads the source payload records, computes their exact
SHA-256, and writes canonical payloads (UTF-8 no BOM, LF, sorted keys, indent=2,
trailing newline), the root manifest, the bundle-root payload bytes, SIG-IV, and
the discovery register. No timestamps inside hashed content (fixed date only).

Owner-only steps happen OUTSIDE this script (SIGN-BUNDLE-V1-2026-08-21.ps1);
agent-only post-sign steps happen in fanout_receipts.py after the owner returns
the detached signature.

Usage:  python build_bundle.py [--root F:\\backup]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT_DEFAULT = Path(r"F:\backup")
OUT = "bundle-v1"
BUNDLE_TAG = "OCTOPUS_OWNER_SIGNATURE_BUNDLE_V1"
IMPLEMENTATION_HEAD = "fa38d16cca944a80396ae1e1a16c547ab3122f78"
EVIDENCE_HEAD = "d3013390d52aab2e61bd2578613aff7077f68742"
DECLARED_VERIFY_HEAD = "cc267048075b0f64bd56c8ac59074d8a43233ae2"
KEY_FINGERPRINT = "2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2"
KEY_ALGORITHM = "Ed25519 (pure, openssl pkeyutl -rawin)"
PUBKEY_LOCATION = "_ops/owner-signing/octopus-owner-ed25519-public.pem"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT_DEFAULT))
    args = ap.parse_args()
    root = Path(args.root)
    out = root / "_ops" / "owner-signing" / OUT
    payloads_dir = out / "payloads"
    payloads_dir.mkdir(parents=True, exist_ok=True)

    def rel(p: Path) -> str:
        return str(p.relative_to(root)).replace("\\", "/")

    # ---- source records (immutable; only hashed, never rewritten) ----
    src = {
        "b1_old_payload": root / "02-DECISIONS/B1-SIGNING-PAYLOAD-2026-08-20.json",
        "ablation_prereg": root / "02-DECISIONS/PRE-REG-ABLATION-FOUR-ARM-2026-08-20.md",
        "k9_prereg": root / "02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20.json",
        "shadow_slice": root / "02-DECISIONS/OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json",
        "gate0": root / "06-EVIDENCE/GATE-0-DISCOVERY-2026-08-20.md",
        "d6_evidence": root / "06-EVIDENCE/D6-BETWEEN-RUN-VARIANCE-2026-08-20.md",
        "d8_evidence": root / "06-EVIDENCE/D8-PAIN-TRIAGE-CANARY-2026-08-20.md",
    }
    missing = [k for k, p in src.items() if not p.is_file()]
    if missing:
        print("FATAL missing source records:", missing, file=__import__("sys").stderr)
        return 2
    hashes = {k: sha256_file(p) for k, p in src.items()}

    owner_identity = {
        "display_name": "OWNER (ari-vault)",  # confirm or correct at decision time
        "owner_id": "OWNER",
    }

    # ---- canonical payloads ----
    payloads: dict[str, dict] = {}

    payloads["SIG-B1"] = {
        "sig_id": "SIG-B1",
        "purpose": "Bind the declared owner identity to the supplied public-key fingerprint",
        "project": "OCTOPUS",
        "owner_identity": owner_identity,
        "owner_key": {
            "algorithm": KEY_ALGORITHM,
            "public_key_fingerprint": KEY_FINGERPRINT,
            "public_key_location": PUBKEY_LOCATION,
            "private_key_never_in_repo": True,
        },
        "effective_date": "2026-08-20",
        "revocation_procedure": "TRUST-ANCHOR.md + _ops/owner-runbook/BACKUP-KEY-VERIFY-RUNBOOK.md (fail-closed on any fingerprint mismatch)",
        "superseded": [{
            "record": "02-DECISIONS/B1-SIGNING-PAYLOAD-2026-08-20.json",
            "sha256": hashes["b1_old_payload"],
            "status": "ALREADY_SIGNED_AND_VERIFIED (openssl, 2026-08-20)",
        }],
    }

    payloads["SIG-D1"] = {
        "sig_id": "SIG-D1",
        "purpose": "Owner approval of the exact D1 (ablation four-arm) payload and scope",
        "phase": "MEGA-DISCOVERY-GATE-0 D1",
        "payload_file": "02-DECISIONS/PRE-REG-ABLATION-FOUR-ARM-2026-08-20.md",
        "payload_sha256": hashes["ablation_prereg"],
        "scope": {
            "arms": ["M+", "M-", "P", "B"],
            "valid_pairs_target_per_arm": 30,
            "learning_gate": "20/30 overall (not per-arm)",
            "metrics_frozen": [
                "Brier delta on frozen Live-4 class: delta = Brier(arm) - Brier(baseline); T1 target delta < 0 for M+ vs B",
                "per-arm hit/miss/void rates (void never silently dropped from valid denominator)",
                "T6 causality: M- memory removal must change selection vs M+ repeatably",
            ],
            "thresholds_frozen": ["30 valid pairs", "20 wins", "Brier delta < 0", "provenance >= 0.9"],
        },
        "execution_blocked_until": [
            "D6 closed (BETWEEN_RUN_VARIANCE / cross-instrument VOID)",
            "K=9 three-seed run on the canonical instrument",
            "owner approval of this bundle",
        ],
        "exclusions": {"paid_calls": "0 until valid FX pin (R12)", "live_telegram": "0"},
        "supersedes": "none - new experiment; results from pre-canonical-instrument runs are VOID",
    }

    payloads["SIG-D7"] = {
        "sig_id": "SIG-D7",
        "purpose": "Owner acceptance of the exact D7 evidence, verdict, limitations and checkpoint",
        "phase": "MEGA-DISCOVERY-GATE-0 D7",
        "verdict": {
            "os_level_sandbox": False,
            "isolation_verdict": "policy_workspace_env_timeout",
            "model_mutation_in_sandbox": "FORBIDDEN",
            "allowed": "reviewed code only",
        },
        "evidence": {
            "GATE-0-DISCOVERY-2026-08-20.md": hashes["gate0"],
            "D6-BETWEEN-RUN-VARIANCE-2026-08-20.md": hashes["d6_evidence"],
            "D8-PAIN-TRIAGE-CANARY-2026-08-20.md": hashes["d8_evidence"],
        },
        "limitations": [
            "D6: BETWEEN_RUN_VARIANCE - cross-instrument comparisons are VOID",
            "D8: pain-triage promotion is CANARY, not VERIFIED",
        ],
        "checkpoint": "06-EVIDENCE/GATE-0-DISCOVERY-2026-08-20.md",
    }

    payloads["SIG-K9"] = {
        "sig_id": "SIG-K9",
        "purpose": "Freeze the K=9 three-seed preregistration",
        "payload_file": "02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20.json",
        "payload_sha256": hashes["k9_prereg"],
        "freeze": True,
        "seeds": {"A": "k9-triple-2026-08-20/A", "B": "k9-triple-2026-08-20/B",
                  "C": "k9-triple-2026-08-20/C", "master": "k9-triple-2026-08-20"},
        "temperature": 0,
        "max_calls": 80,
        "max_cost_aud": 2.0,
        "fisher": "two_sided",
        "execution_condition": "ONLY_AFTER_4H_SOAK_PASS",
        "budget_semantics": "fresh_reservation_not_cap_increase",
        "negative_outcome_policy": "VOID retained; historical 5-of-9 vs 9-of-9 comparison VOID",
        "canonicalization": "utf-8-no-bom; lf; sorted keys; indent=2; trailing newline",
    }

    payloads["SIG-GOV"] = {
        "sig_id": "SIG-GOV",
        "purpose": "Governance policy: A2 automatic, A4 owner-centric, TCB protection",
        "a2_reversible_engineering": "AUTOMATIC_WITH_RECEIPT",
        "a4_owner_confirmed": [
            "TCB changes", "owner identity", "cryptographic roots", "destructive actions",
            "paid calls", "externally visible operations",
        ],
        "tcb_protection": True,
        "append_only_governance": True,
    }

    payloads["SIG-W1"] = {
        "sig_id": "SIG-W1",
        "purpose": "Conditional Wave 1 authorization and single-owner Telegram canary",
        "authorization": "PREPARE Wave 1 and execute a single-owner Telegram canary ONLY after independent verification passes",
        "gates_required": [
            "independent verification PASS (SIG-IV) at declared head cc267048... or a later declared descendant",
            "owner Telegram chat target resolved",
            "kill switch tested",
            "rollback tested",
            "fake transport rehearsal passes",
            "queue empty or fully reconciled",
        ],
        "limits": {
            "max_recipients": 1,
            "max_confirmed_real_messages": 1,
            "target": "OWNER_CHAT_ONLY",
            "webhook": "OFF",
            "paid_calls": 0,
            "sender_default": "OFF",
        },
        "expansion": "forbidden without new owner authorization",
        "verification_head_note": "declared descendant cc267048 (preflight findings 2026-08-21: d301339 alone does not reproduce 163/163)",
    }

    payloads["SIG-LAB"] = {
        "sig_id": "SIG-LAB",
        "purpose": "Laboratory execution authorization",
        "fixture_only": "AUTOMATIC execution authorized",
        "canary_proposed": "PREPARATION only; no live execution",
        "requirements": ["preregistration", "append-only evidence", "rollback", "budgets", "kill switches"],
    }

    payloads["SIG-REPAIR"] = {
        "sig_id": "SIG-REPAIR",
        "purpose": "Automatic repair, test, commit and checkpoint authorization",
        "authorized": [
            "repository inspection", "code repair", "testing", "branch creation",
            "commits", "evidence generation", "manifests", "rollback packages",
        ],
        "excluded": [
            "secret disclosure", "history rewriting", "destructive production changes",
            "fabricated verification",
        ],
    }

    payloads["SIG-RESTART"] = {
        "sig_id": "SIG-RESTART",
        "purpose": "Restart authorization for dev/fixture/canary environments",
        "authorized": ["development processes", "fixture processes", "isolated canary processes"],
        "excluded": ["production-wide restart without separate owner approval"],
    }

    payloads["SIG-CLOSEOUT"] = {
        "sig_id": "SIG-CLOSEOUT",
        "purpose": "Accept implementation completion within the tested scope",
        "acceptance_scope": "tested scope only (registered suite 163/163 reproduced at declared head cc267048, preflight 2026-08-21)",
        "preserve_state": "IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING until an independent verifier signs SIG-IV",
    }

    payloads["SIG-VS"] = {
        "sig_id": "SIG-VS",
        "purpose": "Owner acceptance of the shadow vertical-slice verdict card (discovered AWAITING_OWNER_SIGNATURE)",
        "decision_id": "OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20",
        "payload_file": "02-DECISIONS/OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json",
        "payload_sha256": hashes["shadow_slice"],
        "owner_verdict": "ACCEPTED_FOR_SHADOW_WITH_CONDITIONS",
        "authority": "owner order #5",
    }

    for sig_id in sorted(payloads):
        (payloads_dir / f"{sig_id}.json").write_bytes(canonical_json(payloads[sig_id]))

    # ---- root manifest (sorted by signature ID) ----
    sig_records = []
    for sig_id in sorted(payloads):
        p = payloads[sig_id]
        sig_records.append({
            "sig_id": sig_id,
            "purpose": p["purpose"],
            "payload_path": f"payloads/{sig_id}.json",
            "payload_sha256": sha256_file(payloads_dir / f"{sig_id}.json"),
            "scope": p.get("scope") or p.get("authorized") or p.get("limits") or p.get("verdict") or p.get("gates_required") or p.get("exclusions"),
            "superseded": p.get("superseded") or p.get("supersedes") or None,
        })

    manifest = {
        "bundle_version": "OWNER_SIGNATURE_BUNDLE_V1",
        "project": "OCTOPUS",
        "owner_identity": owner_identity,
        "owner_key_fingerprint": KEY_FINGERPRINT,
        "owner_key_algorithm": KEY_ALGORITHM,
        "implementation_head": IMPLEMENTATION_HEAD,
        "evidence_head": EVIDENCE_HEAD,
        "declared_verification_head": DECLARED_VERIFY_HEAD,
        "created": "2026-08-21",
        "tool": "octopus-bundle-builder",
        "tool_version": "1.0",
        "signature_records": sig_records,
        "excluded_signatures": [
            {"sig_id": "SIG-IV", "reason": "INDEPENDENT_VERIFIER_ONLY - the owner must not sign; AWAITING_INDEPENDENT_VERIFIER"},
            {"sig_id": "SIG-MANIFEST", "reason": "the single root signature over this manifest (owner) - not a separate payload"},
        ],
    }
    manifest_bytes = canonical_json(manifest)
    manifest_path = out / "OWNER_SIGNATURE_MANIFEST_V1.json"
    manifest_path.write_bytes(manifest_bytes)

    root_payload = (BUNDLE_TAG + "\n").encode("utf-8") + manifest_bytes
    root_path = out / "OWNER_SIGNATURE_BUNDLE_V1.root-payload.txt"
    root_path.write_bytes(root_payload)
    bundle_root = hashlib.sha256(root_payload).hexdigest()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    # ---- SIG-IV (independence boundary) ----
    sig_iv = {
        "sig_id": "SIG-IV",
        "status": "AWAITING_INDEPENDENT_VERIFIER",
        "verifier_identity": None,
        "independence_declaration": None,
        "exact_verified_head": DECLARED_VERIFY_HEAD,
        "suite_results": None,
        "run_local_side_effect_hashes": None,
        "manifest_verification": None,
        "failed_checks": None,
        "verifier_signature": None,
        "note": "Owner bundle must not satisfy SIG-IV. Implementation agent must not satisfy SIG-IV. "
                "Do not promote SECURITY_SHADOW_PASS until SIG-IV is valid.",
    }
    (out / "SIG-IV.json").write_bytes(canonical_json(sig_iv))

    # ---- discovery register ----
    register = {
        "schema": "owner-signature-register/1",
        "generated": "2026-08-21",
        "discovered_and_classified": [
            {"record": "02-DECISIONS/B1-SIGNING-PAYLOAD-2026-08-20.json (+ .sig)",
             "found_via": "B1", "class": "DUPLICATE - already signed and verified; linked into SIG-B1 superseded"},
            {"record": "02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20.json",
             "found_via": "AWAITING_OWNER_SIGNATURE / K=9 prereg", "class": "OWNER_SIGNABLE (SIG-K9)"},
            {"record": "02-DECISIONS/PRE-REG-ABLATION-FOUR-ARM-2026-08-20.md",
             "found_via": "AWAITING_OWNER_SIGNATURE / D1", "class": "OWNER_SIGNABLE (SIG-D1)"},
            {"record": "02-DECISIONS/OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json",
             "found_via": "AWAITING_OWNER_SIGNATURE", "class": "OWNER_SIGNABLE (SIG-VS)"},
            {"record": "06-EVIDENCE/GATE-0-DISCOVERY-2026-08-20.md (D1..D10 table)",
             "found_via": "D1 / D7", "class": "OWNER_SIGNABLE as evidence scope of SIG-D1/SIG-D7"},
            {"record": "06-EVIDENCE/D6-BETWEEN-RUN-VARIANCE-2026-08-20.md", "found_via": "D6",
             "class": "OWNER_SIGNABLE as evidence of SIG-D7"},
            {"record": "06-EVIDENCE/D8-PAIN-TRIAGE-CANARY-2026-08-20.md", "found_via": "D8",
             "class": "OWNER_SIGNABLE as evidence of SIG-D7"},
        ],
        "observed_not_signature_items": [
            {"item": "OWNER-DECISION-QUEUE Q1-Q8", "reason": "owner decisions (TCB/vote), not signature records; remain open"},
            {"item": "_octopus/queue/pending (20 files)", "reason": "approval-queue decisions, not owner signatures; remain open"},
            {"item": "00 - Inbox/AGENT_QUESTIONS.md", "reason": "owner inbox questions; signature-relevant ones (OD-002, ablation unsigned) mapped into SIG-B1/SIG-D1"},
        ],
        "never_owner_signed": ["SIG-IV (independent verifier only)"],
    }
    (out / "OWNER_SIGNATURE_REGISTER.json").write_bytes(canonical_json(register))

    # ---- expected-hash table for the owner runbook ----
    expected = {
        "bundle_tag": BUNDLE_TAG,
        "manifest_sha256": manifest_sha256,
        "bundle_root": bundle_root,
        "root_payload_file": "OWNER_SIGNATURE_BUNDLE_V1.root-payload.txt",
        "payloads": {sig_id: sig["payload_sha256"] for sig_id, sig in zip(sorted(payloads), sig_records)},
    }
    (out / "bundle-hashes-expected.json").write_bytes(canonical_json(expected))

    print("=" * 62)
    print("OWNER SIGNATURE BUNDLE V1 - DIGEST TABLE (ordered by signature ID)")
    print("=" * 62)
    print(f"implementation_head : {IMPLEMENTATION_HEAD}")
    print(f"evidence_head       : {EVIDENCE_HEAD}")
    print(f"declared verify head: {DECLARED_VERIFY_HEAD}")
    print(f"owner key fingerprint: {KEY_FINGERPRINT}")
    for sig in sig_records:
        print(f"{sig['sig_id']:>12}  {sig['payload_sha256']}  {sig['payload_path']}")
    print("-" * 62)
    print(f"manifest_sha256     : {manifest_sha256}")
    print(f"bundle_root         : {bundle_root}")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
