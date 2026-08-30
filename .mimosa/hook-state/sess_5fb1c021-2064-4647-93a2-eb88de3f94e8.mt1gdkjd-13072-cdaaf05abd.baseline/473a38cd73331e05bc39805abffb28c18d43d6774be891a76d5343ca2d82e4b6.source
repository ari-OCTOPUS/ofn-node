from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=10))
now = datetime.now(TZ).replace(microsecond=0).isoformat()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def write_json(path: Path, obj: dict) -> dict:
    body = {k: v for k, v in obj.items() if k != "receipt_hash"}
    canonical = json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    obj = dict(obj)
    obj["receipt_hash"] = sha256_bytes(canonical.encode("utf-8"))
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(sha256_file(path) + "\n", encoding="ascii")
    print(path.name, "file_sha256", sidecar.read_text().strip(), "receipt_hash", obj["receipt_hash"])
    return obj


root = Path(r"F:\backup")
ev = root / "06-EVIDENCE"
rec = ev / "canonical" / "receipts"
p3 = ev / "p3-tcb-2026-08-18"

scripts = {
    "hourly-push-error-capture.ps1": root / "04 - Architect System" / "scripts" / "hourly-push-error-capture.ps1",
    "germline-hourly.ps1": root / "04 - Architect System" / "scripts" / "germline-hourly.ps1",
    "test-hourly-push-error-capture.ps1": root / "04 - Architect System" / "scripts" / "test-hourly-push-error-capture.ps1",
}
script_hashes = {k: sha256_file(v) for k, v in scripts.items()}

binding = root / "06-EVIDENCE" / "canonical" / "inbox" / "TO-180-A2-001-binding.json"
auth = root / "06-EVIDENCE" / "canonical" / "inbox" / "TO-180-A2-001-execution-authorization.json"
ack = root / "06-EVIDENCE" / "canonical" / "inbox" / "from-180" / "run-20260817T175442Z-a2-001-binding-ack.json"
execute = root / "06-EVIDENCE" / "canonical" / "inbox" / "from-180" / "run-20260817T180808Z-a2-001-execute.json"
diffp = p3 / "germline-hourly.diff"

write_json(rec / "TO-180-A2-001-binding-ack-verified-2026-08-18.json", {
    "schema": "octopus.a2.binding-ack-verified.v1",
    "task_id": "A2-001",
    "from_node": ".191",
    "to_node": ".180",
    "observed_at": now,
    "observed_tz": "UTC+10",
    "delivery_claim": "DELIVERED",
    "source_path": r"F:\backup\06-EVIDENCE\canonical\inbox\TO-180-A2-001-binding.json",
    "source_sha256": sha256_file(binding),
    "expected_sha256": "95527b069a15af1cd45d35894d7e42861fc9b30fffa8b2c269a43392216f7d68",
    "ack_copy_path": str(ack),
    "ack_sha256": sha256_file(ack),
    "ack_outcome": "BINDING_ACKED",
    "ack_hash_match": True,
    "ack_field_verify": "ALL_OK",
    "ack_event_time_utc": "2026-08-17T17:54:58Z",
    "independent_180_report": True,
    "uncertainty": [
        "ACK timestamp_utc_plus_11 uses +11; August Sydney is UTC+10. UTC event_time accepted.",
        "Older transfer receipt remains historically NOT_DELIVERED; this receipt upgrades the live claim after independent ACK.",
    ],
})

write_json(rec / "TO-180-A2-001-execution-authorization-transfer-2026-08-18.json", {
    "schema": "octopus.a2.execution-authorization-transfer.v1",
    "task_id": "A2-001",
    "authorization": "EXECUTION_AUTHORIZATION_A2-001",
    "from_node": ".191",
    "to_node": ".180",
    "observed_at": now,
    "observed_tz": "UTC+10",
    "delivery_claim": "AUTHORIZATION_DELIVERED_AND_CONSUMED",
    "source_path": str(auth),
    "source_file_sha256": sha256_file(auth),
    "packet_hash": "a7dc5dfde2c96f655a91a50deb8c581160980784edd8a3d548eb926bea101b11",
    "destination_path": "/opt/octopus/a2-lab/inbox/TO-180-A2-001-execution-authorization.json",
    "transfer_method": "scp -p via existing OpenSSH config Host root. BatchMode=yes. No IdentityFile added. No authorized_keys/sshd_config/key files edited. Bytes not regenerated.",
    "destination_stat_observed_from_191": {
        "bytes": 1549,
        "mode": "0o100666",
        "sha256": "9fb65045556362c02482035aed9ed957c318669d064a955b36d42bf1230fb771",
        "sha256_match_source": True,
        "observer": ".191-via-ssh",
    },
    "independent_180_consume": {
        "envelope": "/opt/octopus/a2-lab/envelopes/run-20260817T180808Z-a2-001-execute.json",
        "copy": str(execute),
        "copy_sha256": sha256_file(execute),
        "execution_authorization_sha256_match": True,
        "packet_hash_match": True,
    },
    "bytes_altered": False,
    "runner_started_from_191": False,
})

write_json(rec / "TO-180-A2-001-lab-execute-observed-2026-08-18.json", {
    "schema": "octopus.a2.lab-execute-observed.v1",
    "task_id": "A2-001",
    "observer": ".191",
    "observed_at": now,
    "observed_tz": "UTC+10",
    "envelope_copy": str(execute),
    "envelope_sha256": sha256_file(execute),
    "outcome": "BASE_COMMIT_UNAVAILABLE",
    "implemented": False,
    "merged": False,
    "pushed": False,
    "deployed": False,
    "canonical": False,
    "fresh_worktree_created": False,
    "fetched": False,
    "ssh_from_180": False,
    "a2_002_started": False,
    "a2_003_started": False,
    "halt_reason": "git object d10887cbb5c80ec2c3e347f070556ba8276d8a79 is absent on .180; fetch and SSH are denied",
    "preexisting_sandbox_reused": False,
    "promotion": False,
    "lab_verdict": "NOT_QUARANTINED_PASS",
    "uncertainty": [
        r"repo_locator F:\backup\octopus-bridge is not mounted on .180",
        "pre-existing sandbox commit b5fb9676 was not reused",
        ".191 did not copy git objects or start runner.py",
    ],
})

write_json(rec / "DEV-182-0001-review-refresh-2026-08-18.json", {
    "schema": "octopus.dev-182-0001.review.v1",
    "deviation_id": "DEV-182-0001",
    "automation_id": "automation-25cfa808-6251-4bb2-be54-98a8264c45a1",
    "reviewer": ".191",
    "observed_at": now,
    "observed_tz": "UTC+10",
    "verdict": "INSUFFICIENT_EVIDENCE",
    "record": "EVIDENCE_INSUFFICIENT",
    "session_label": "NOT_PASS_READONLY",
    "store": {
        "name": "Cursor Automations / cloud harness",
        "reachable_from_this_session": False,
        "reason": "MCP catalog is Phantom plugins only. cursor-app-control not attached. No CURSOR_API_KEY. No Automations Management API in this session.",
        "enabled": None,
        "lifecycle_state": None,
        "run_count": None,
        "created_at": None,
        "updated_at": None,
        "effective_prompt_or_task_scope": None,
    },
    "negative_checks": {
        "windows_scheduled_task_matching_id": False,
        "ssh_config_hosts_other_than_root": False,
        "cursor_api_key_present": False,
    },
    "os_scheduler_systemd_cron_fs_net_external_altered_for_this_id": "NOT_OBSERVED",
    "cancel": False,
    "cancel_reason": "Owner permits cancel only if live harness confirms existence and in-scope read-only health batch. Store unread; cancel DENIED.",
    "dot182_after": "manual-read-only (unchanged by this review)",
})

write_json(p3 / "P3-CEREMONY-2026-08-18.json", {
    "schema": "octopus.p3.tcb-ceremony.v1",
    "observed_at": now,
    "observed_tz": "UTC+10",
    "p3_status": "ACTIVATED",
    "p3_status_note": r"Capture is wired into the already-scheduled germline-hourly.ps1. Timer/remotes/credentials/fallback unchanged. Not SCHEDULED_CYCLE_OBSERVED because E:\germline\hourly-push-errors.jsonl is absent and the last hourly cycle failed at gitwrite.lock TIMEOUT before push capture.",
    "vocabulary": {
        "PATCH_TESTED": True,
        "TCB_APPROVED": True,
        "ACTIVATED": True,
        "SCHEDULED_CYCLE_OBSERVED": False,
        "DIAGNOSTICS_VERIFIED": False,
        "ROLLED_BACK": False,
        "HALTED": False,
    },
    "tcb_kind": "limited P3 script ceremony; NOT 4d daemon.py/automation.py TCB sign",
    "allowlist": [
        "04 - Architect System/scripts/hourly-push-error-capture.ps1",
        "04 - Architect System/scripts/germline-hourly.ps1",
        "04 - Architect System/scripts/test-hourly-push-error-capture.ps1",
    ],
    "allowlist_review": "PASS: only the three P3 scripts. Push argv remains push --quiet $BARE --all then --tags. No remote edit, credential, timer, fallback, fetch/retry, force push, or GITWRITE flag clearance.",
    "file_sha256": script_hashes,
    "tracked_diff": {
        "path": str(diffp),
        "sha256": sha256_file(diffp),
        "bytes": diffp.stat().st_size,
    },
    "tests": {
        "test-hourly-push-error-capture.ps1": {
            "result": "PASS",
            "nonzero_class": "REMOTE_NOT_FOUND",
            "success_class": "NONE",
            "lock_class": "LOCK_FAILURE",
            "tags_class": "REF_REJECTED",
            "records": 8,
        },
        "test-git-serialize.ps1": {
            "result": "PASS",
            "note": r"offline temp repo only; real F:\backup\.git not touched",
        },
        "run_all.py": "NOT_REGISTERED_WORKLOCK",
    },
    "secret_scan": {
        "production_scripts": "PASS no live token/URL-userinfo",
        "test_fixtures": "synthetic ghp_TESTTOKEN / s3cretValue / example URL only; absent from persisted jsonl",
        "output_samples": "offline test jsonl had no https://, ghp_, or username=alice",
    },
    "owner_authorization": "this session owner mandate work item C; not inferred from green tests",
    "activation": {
        "scheduled_task": r"\germline-hourly",
        "task_state_observed": "Ready",
        "timer_changed": False,
        "jsonl_path": r"E:\germline\hourly-push-errors.jsonl",
        "jsonl_exists": False,
    },
    "lock_observation": {
        "gitwrite_lock_present": True,
        "gitwrite_lock_lastwrite": "2026-08-18T03:30:04+10:00",
        "gitwrite_lock_in_use": True,
        "GITWRITE_FAILED_flag_present": True,
        "flag_cleared": False,
        "last_hourly_log": "2026-08-18 03:50:30 FAIL git-write lock TIMEOUT after 40 attempts",
        "did_not_steal_lock": True,
    },
    "github_wire_channel": r"separate jsonl row push_phase=github_wire remote_class=absent; probe skipped because F:\backup has no github remote. This is not a GitHub heartbeat.",
    "rollback_not_run": True,
})

write_json(ev / "canonical" / "decisions" / "github-wire-recovery-design-2026-08-18.json", {
    "schema": "octopus.github-wire.recovery-design.v1",
    "observed_at": now,
    "observed_tz": "UTC+10",
    "precondition_p3": "NOT_DIAGNOSTICS_VERIFIED",
    "option_chosen": None,
    "credentials_changed": False,
    "GLOBAL_GITWRITE_FAILED": "OPEN",
    "observed_writer_target": r"E:\germline\vault.git",
    "observed_vault_remotes": ["germline -> E:/germline/octopus.git (local-path only)"],
    "github_remote_on_F_backup": False,
    "option_r": {
        "name": "OPTION_R",
        "intent": "restore/rotate GitHub credential using an approved secure secret-management path",
        "blast_radius": "Feet GitHub heartbeat and any git remote still using that credential. Does not by itself fix local vault.git --tags reject.",
        "rollback": "revert to previous secret version in the same secret manager; do not rewrite git history; do not force-push.",
        "test_method": "non-interactive redacted probe of GitHub heartbeat after owner confirmation; no token in logs",
        "expected_refs": "unchanged GitHub refs; heartbeat becomes reachable if failure class was AUTH_*",
        "stale_message_behavior": "not applicable unless Feet was blocked only on auth; queued commands remain unconsumed until heartbeat resumes",
        "audit_trail": "P3 github_wire phase plus owner confirmation note; redacted receipts only",
        "owner_confirmation_point": "after P3 classifies github_wire as AUTH_REQUIRED or AUTH_DENIED on a real scheduled cycle, owner records which secret path to use",
    },
    "option_m": {
        "name": "OPTION_M",
        "intent": "migrate Feet wire-read from GitHub to the already-observed germline source",
        "blast_radius": "Feet command ingestion source identity; WIRE_LAST progression; risk of duplicate consumption if both GitHub and germline are read",
        "rollback": "restore previous wire-read source pointer; keep GLOBAL_GITWRITE_FAILED OPEN",
        "test_method": "verify WIRE_LAST advances and source identity is germline; verify no duplicate command consumption; no unexpected external action",
        "expected_refs": "germline/octopus.git already observed at d10887cbb5c80ec2c3e347f070556ba8276d8a79 for equip branch; not a GitHub dest",
        "stale_message_behavior": "GitHub-queued commands may remain unread; must not replay already-consumed germline messages",
        "audit_trail": "source-identity receipt + WIRE_LAST before/after; owner confirmation",
        "owner_confirmation_point": "fresh owner record after P3 DIAGNOSTICS_VERIFIED; choose M only if github_wire remains absent/unneeded",
    },
    "do_not": [
        "choose R or M in this receipt",
        "put secrets in logs",
        "clear GITWRITE-FAILED.flag",
        "force tag pre-deploy-2026-07-25",
    ],
    "known_local_writer_failure_not_github": "hourly --tags reject of pre-deploy-2026-07-25 (local dab81a82 vs vault 9c49f174) is REF_REJECTED on local-path vault.git; Option R would not close that.",
})

write_json(rec / "WAVE0-OWNER-EXEC-A-D-2026-08-18.json", {
    "schema": "octopus.wave0.owner-exec.v1",
    "wave": "WAVE0_OBSERVE_ONLY",
    "production": False,
    "promotion_authority": "NONE",
    "autonomy_raised": False,
    "observed_at": now,
    "observed_tz": "UTC+10",
    "work_items": {
        "A": "PARTIAL",
        "B": "PARTIAL",
        "C": "PARTIAL",
        "D": "NOT_STARTED",
    },
})

print("NOW", now)
print("SCRIPTS", json.dumps(script_hashes, indent=2))
print("execute_sha256", sha256_file(execute))
print("ack_sha256", sha256_file(ack))
print("auth_sha256", sha256_file(auth))
print("binding_sha256", sha256_file(binding))
print("diff_sha256", sha256_file(diffp))
