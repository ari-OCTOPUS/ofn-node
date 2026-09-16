#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import hashlib
import json
from datetime import datetime

root = Path(r"F:\backup")
run_id = "20260818T030354p10"
started_at = "2026-08-18T03:03:54+10:00"
finished_at = datetime.now().astimezone().isoformat(timespec="seconds")

hashed = []
files = [
    r"06-EVIDENCE/envelopes/cycle-01-feet.json",
    r"06-EVIDENCE/envelopes/cycle-01-sensorium.json",
    r"06-EVIDENCE/envelopes/cycle-02-feet.json",
    r"06-EVIDENCE/envelopes/cycle-02-sensorium.json",
    r"06-EVIDENCE/envelopes/cycle-02-continuity.json",
    r"_ops/backup/GITWRITE-FAILED.flag",
    r"octopus-bridge/octopus_bridge/__init__.py",
    r"octopus-bridge/octopus_bridge/models.py",
    r"04-SYSTEMS/OFN-NODE.md",
]
for rel in files:
    p = root / rel
    hashed.append(
        {
            "path": rel.replace("\\", "/"),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
        }
    )
hashed.sort(key=lambda x: x["path"])
manifest_hash = hashlib.sha256(
    json.dumps(hashed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
).hexdigest()

changed = [
    "06-EVIDENCE/canonical/receipts/custodian-191-20260818T030354p10.json",
    "06-EVIDENCE/canonical/receipts/_build_custodian_191_receipt.py",
    "06-EVIDENCE/canonical/decisions/owner-constitution-role-2026-08-18.md",
    "06-EVIDENCE/canonical/contradictions/custodian-191-health-ledger-2026-08-18.md",
    "06-EVIDENCE/canonical/inbox/custodian-191-health-ledger-2026-08-18.md",
    "00 - Inbox/2026-08-18 NOTE — Custodian-191 health ledger.md",
    "01 - Dashboard/HANDOFF.md",
]

receipt = {
    "run_id": run_id,
    "node_id": ".191",
    "hostname": "DESKTOP-KA9RFN5",
    "task_id": "custodian-gate-pass",
    "authority": "CANONICAL_EVIDENCE_AND_OWNER_GATE",
    "mode": "READ_ONLY_BY_DEFAULT",
    "wave": "WAVE0_OBSERVE_ONLY",
    "effect": "NONE",
    "production": False,
    "observed_tz": "UTC+10",
    "tzutil": "AUS Eastern Standard Time",
    "base_commit": "d10887cbb5c80ec2c3e347f070556ba8276d8a79",
    "base_branch": "equip/g10-cognition-20260816",
    "a2_worktree": None,
    "input_manifest_hash": manifest_hash,
    "hashed_files": hashed,
    "started_at": started_at,
    "finished_at": finished_at,
    "commands_run": [
        "hostname; Get-Date; tzutil /g",
        "Get-ChildItem USERPROFILE/.ssh (Name,Length,LastWriteTime only)",
        "Test-Path octopus_key / octopus_key.pub",
        "ssh-keygen -l -f USERPROFILE/.ssh/id_ed25519.pub",
        "Get-Item F:/backup/_ops/backup/GITWRITE-FAILED.flag; Get-Content -TotalCount 1; sha256 raw bytes",
        "git -C F:/backup rev-parse HEAD; rev-parse --abbrev-ref HEAD; worktree list",
        "git -C F:/backup rev-parse pre-deploy-2026-07-25",
        "git --git-dir=E:/germline/vault.git rev-parse pre-deploy-2026-07-25",
        "git --git-dir=E:/germline/octopus.git rev-parse pre-deploy-2026-07-25 (ABSENT)",
        "git --git-dir=E:/germline/octopus.git rev-parse refs/heads/ofn/bridge; ls-tree -r --name-only",
        "git -C F:/backup push --dry-run --porcelain E:/germline/vault.git refs/tags/pre-deploy-2026-07-25",
        "git -C F:/backup ls-files octopus-bridge; Get-ChildItem octopus-bridge -Recurse",
        "python hashlib envelopes + sidecar compare + _ops.handshake.envelope.validate_envelope",
        "sqlite3 file:F:/backup/_ops/state/board_cp/commands.sqlite?mode=ro (ids/state only, LIKE 01a00d3d)",
        "git -C F:/backup remote -v; Test-Path E:/germline/vault.git",
        "Get-NetAdapter (Name,Status,LinkSpeed,MediaType,InterfaceDescription)",
        "netsh wlan show interfaces (band/channel/radio; identifiers omitted from notes)",
        "Select-String 4d_system/brain/automation.py daemon.py for EQUIP-G2 / JOB-RESEARCH markers",
        "Get-Item PATCH-EQUIP-G2* PATCH-JOB-RESEARCH*",
        "git -C organism-alive-69a5db rev-parse HEAD; ls-files octopus-bridge",
        "cmd dir _ops/world_discovery/schemas",
    ],
    "changed_files": changed,
    "test_results": {
        "envelope_module": "F:/backup/_ops/handshake/envelope.py",
        "schema": "octopus-handshake-envelope/1",
        "cycle-01-continuity.json": "ABSENT",
        "files": {
            "cycle-01-feet.json": {
                "bytes": 6672,
                "sha256": "0cab6661c3723518384d877a2cf7b7482aa4589a4cba37a3d2d50d5d951bb24a",
                "sidecar_match": True,
                "validate_envelope": [],
            },
            "cycle-01-sensorium.json": {
                "bytes": 6677,
                "sha256": "83d47f47b618efd231eb6c0bbe96818b41e42ea24e63e8da5a7fd26462ca2fa6",
                "sidecar_match": True,
                "validate_envelope": [],
            },
            "cycle-02-feet.json": {
                "bytes": 9613,
                "sha256": "ce0e588b567a650ad275fd72e6aaec4dc20dbd6eefebd8c1bc312c0e90b34819",
                "sidecar_match": True,
                "validate_envelope": [],
            },
            "cycle-02-sensorium.json": {
                "bytes": 9618,
                "sha256": "2cc65012332051c47472cac63140fdddebc5b22f9219aea24c50b5326927f8fd",
                "sidecar_match": True,
                "validate_envelope": [],
            },
            "cycle-02-continuity.json": {
                "bytes": 9619,
                "sha256": "e9fad1de21bf2ca72a689adfb59aee0feaa60c2e0c4898276f99a5622db27d3f",
                "sidecar_match": True,
                "validate_envelope": [],
            },
        },
    },
    "statuses": {
        "SSH_OFFICIAL_KEY_MISSING": {
            "status": "MISSING",
            "path": "USERPROFILE/.ssh/octopus_key",
            "octopus_key_exists": False,
            "octopus_key_pub_exists": False,
            "fallback_pub": "USERPROFILE/.ssh/id_ed25519.pub",
            "fallback_pub_fingerprint": "SHA256:IrKVkKK9SwcdlmrtAiLiUakNQFX8Fb88zuNUBmJIUwg",
            "ssh_hop_this_pass": "NOT_RUN",
            "confidence": "HIGH",
        },
        "GITWRITE-FAILED": {
            "status": "PRESENT_NOT_CLEARED",
            "path": "_ops/backup/GITWRITE-FAILED.flag",
            "bytes": 120,
            "mtime": "2026-08-16T03:50:24+10:00",
            "sha256": "e0774eec840e10b2808171fb999b5b5e7a8360b9fc2867e7280a1f22de2ed05e",
            "first_line": "GITWRITE-FAILED 2026-08-16_035024 : git-write lock TIMEOUT after 40 attempts on F:/backup/_ops/backup/gitwrite.lock",
            "note": "raw bytes include UTF-8 BOM; green manual push is not the scheduled path",
            "confidence": "HIGH",
        },
        "TAG_pre-deploy-2026-07-25": {
            "status": "REJECTED_DRY_RUN",
            "local": "dab81a828c9546ad7e36141b6f3a23858e6ce0a8",
            "vault_git": "9c49f17490ab466d9fe7a88458b0283e7b75cf39",
            "octopus_git": "ABSENT",
            "dry_run": "git push --dry-run --porcelain E:/germline/vault.git refs/tags/pre-deploy-2026-07-25",
            "dry_run_exit": 1,
            "dry_run_result": "rejected (already exists)",
            "confidence": "HIGH",
        },
        "UNKNOWN_CANONICAL": {
            "status": "UNKNOWN_CANONICAL",
            "task": "A2-001",
            "live_stub": "F:/backup/octopus-bridge (2 tracked files, schemas ABSENT, mirror_verify.py ABSENT)",
            "worktree_copy": "F:/backup/.claude/worktrees/organism-alive-69a5db/octopus-bridge HEAD bfc673fe0e184fdb8e79613d092c2bd224592945",
            "ofn_bridge": "E:/germline/octopus.git refs/heads/ofn/bridge e21f20d7c690e4660894226b1cef1bd47b219b5a; no schemas/; no mirror_verify.py",
            "empty_schemas_unrelated": "F:/backup/_ops/world_discovery/schemas 0 files",
            "sot_file_line": "04-SYSTEMS/OFN-NODE.md line 27: octopus-bridge is OFN/board package, not A2-001 home",
            "a2_worktree": "F:/backup-wt-a2-001 ABSENT",
            "mirror_verifier_dir": "_ops/mirror_verifier ABSENT",
            "confidence": "HIGH",
        },
        "cmd_01a00d3d": {
            "status": "dispatched",
            "message_id": "01a00d3d-2b7f-7362-b283-275723a85b24",
            "sqlite": "_ops/state/board_cp/commands.sqlite",
            "sqlite_bytes": 16384,
            "sqlite_mtime": "2026-08-17T23:57:31+10:00",
            "acked": False,
            "confidence": "HIGH",
        },
        "EQUIP-G2_JOB-RESEARCH": {
            "status": "UNAPPLIED",
            "patches_present": True,
            "strings_in_automation_py": False,
            "strings_in_daemon_py": False,
            "confidence": "HIGH",
        },
        "ETHERNET": {
            "status": "Disconnected",
            "linkspeed": "0 bps",
            "confidence": "HIGH",
        },
        "WIFI_5GHZ": {
            "status": "connected",
            "band": "5 GHz",
            "channel": 36,
            "radio": "802.11ac",
            "confidence": "HIGH",
        },
        "A2_180_LAB": {
            "status": "NOT_STARTED_AS_PRODUCTION",
            "local_artifacts": "no a2 worktree; no _ops/mirror_verifier",
            "remote_process": "INSUFFICIENT_EVIDENCE (no SSH)",
            "confidence": "MEDIUM",
        },
    },
    "pending_owner_approvals_not_closed": [
        "01a00d3d dispatched",
        "TCB ceremony EQUIP-G2 + JOB-RESEARCH unapplied",
        "tag pre-deploy-2026-07-25",
        "GITWRITE-FAILED hold",
        "A2-001 promotion never automatic",
        "Ethernet still disconnected",
        "octopus_key official SSH",
        ".180 lab not started as production",
    ],
    "warnings": [
        "Did not SSH to .138 or .180 this pass.",
        "Did not re-run write-bench; 40-73s vs 1080ms remains prior evidence + owner statement.",
        "Hardware identifiers from netsh (GUID/MAC/BSSID) observed live and omitted from notes.",
        "sqlite LIKE matched the same 01a00d3d row twice (two columns); unique message_id count is 1.",
        "Live git remote of F:/backup is E:/germline/octopus.git; scheduled tag path is E:/germline/vault.git.",
        "cycle-01-continuity.json does not exist; cycle-01 only feet+sensorium.",
        "msg-evidence-latest.json vs msg-evidence-162739.json disagree on CHARTER_ACTIVATED seq 26.",
    ],
    "uncertainty": [
        "SSH hop success to .138 this pass: INSUFFICIENT_EVIDENCE (not probed).",
        "Live .182 charter ACTIVE vs STAGED: vault copies disagree; board not queried.",
        "GAP-001 is a homonym across board checkpoint ledger and laptop verifier/telegram notes.",
        ".180 production process state unknown without SSH.",
        "Owner-stated 1080ms write-bench not re-measured.",
    ],
    "outcome": "BASELINE_RED",
}

canon = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()
receipt["report_hash"] = digest
out = root / "06-EVIDENCE" / "canonical" / "receipts" / f"custodian-191-{run_id}.json"
out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("wrote", out)
print("report_hash", digest)
print("finished_at", finished_at)
print("bytes", out.stat().st_size)
print("input_manifest_hash", manifest_hash)
