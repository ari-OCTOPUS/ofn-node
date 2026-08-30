from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=10))
now = datetime.now(TZ).replace(microsecond=0).isoformat()
root = Path(r"F:\backup")
rec = root / "06-EVIDENCE" / "canonical" / "receipts"
jsonl = Path(r"E:\germline\hourly-push-errors.jsonl")
raw = jsonl.read_bytes()
jsonl_sha = hashlib.sha256(raw).hexdigest()
rows = [json.loads(l) for l in raw.decode("utf-8-sig").splitlines() if l.strip()]
c0949 = [r for r in rows if str(r.get("cycle_id", "")).startswith("20260818T0949")]


def write_json(path: Path, obj: dict) -> None:
    body = {k: v for k, v in obj.items() if k != "receipt_hash"}
    canonical = json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    obj = dict(obj)
    obj["receipt_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(hashlib.sha256(path.read_bytes()).hexdigest() + "\n", encoding="ascii")
    print(path.name, sidecar.read_text().strip(), obj["receipt_hash"])


write_json(rec / "P3-scheduled-cycle-observed-2026-08-18.json", {
    "schema": "octopus.p3.scheduled-cycle.v1",
    "observed_at": now,
    "observed_tz": "UTC+10",
    "wave": "WAVE0_OBSERVE_ONLY",
    "production": False,
    "promotion": "NONE",
    "p3_status": "DIAGNOSTICS_VERIFIED",
    "writer_health_claimed": False,
    "GLOBAL_GITWRITE_FAILED": "OPEN",
    "gitwrite_flag": {
        "path": r"F:\backup\_ops\backup\GITWRITE-FAILED.flag",
        "present": True,
        "mtime": "2026-08-18T03:50:30.6184975+10:00",
        "cleared": False,
    },
    "natural_cycle": {
        "task": r"\germline-hourly",
        "last_run": "2026-08-18T09:49:05+10:00",
        "last_task_result": 0,
        "last_task_result_meaning": "script exit 0 on throttled PUSH-FAIL; not writer-healthy",
        "next_run": "2026-08-18T10:49:04+10:00",
        "log_line": "2026-08-18 09:56:49  OK PUSH-FAIL (fallback throttled, 1.4h of 6h; push err: To E:\\germline\\vault.git) +state",
        "manually_invoked": False,
        "lock_stolen_by_observer": False,
    },
    "lock": {
        "acquisition": "SUCCESS",
        "age_at_acquisition": "new CreateNew; observed mtime 2026-08-18T09:49:11+10:00 (~0s)",
        "held_during_push": True,
        "release": "SUCCESS",
        "absent_by": "2026-08-18T09:51:03+10:00",
        "absent_after_task_ready": True,
        "timeout_this_cycle": False,
        "did_not_steal_delete_rename_overwrite": True,
    },
    "phases": {
        "all": {"exit_code": 0, "error_class": "NONE", "dest_heads_local_count": 30, "dest_heads_mismatch": 0, "dest_heads_only_local": 0},
        "tags": {"exit_code": 1, "error_class": "REF_REJECTED", "tag": "pre-deploy-2026-07-25", "local": "dab81a828c9546ad7e36141b6f3a23858e6ce0a8", "vault": "9c49f17490ab466d9fe7a88458b0283e7b75cf39"},
        "github_wire": {"exit_code": 0, "error_class": "NONE", "remote_class": "absent", "note": "skip; not a GitHub heartbeat"},
    },
    "jsonl": {
        "path": r"E:\germline\hourly-push-errors.jsonl",
        "present": True,
        "rows": len(rows),
        "sha256": jsonl_sha,
        "schema_fail": False,
        "secret_or_url_hits": False,
        "cycle_0949": c0949,
        "prior_natural_cycles_same_class": ["20260818T044907", "20260818T054907", "20260818T064926", "20260818T074909", "20260818T084907"],
    },
    "separate_fields": {
        "germline_local_path": r"E:\germline\vault.git",
        "github_wire": "absent_on_F_backup",
        "hourly_diagnostics": "DIAGNOSTICS_VERIFIED",
        "GLOBAL_GITWRITE_FAILED": "OPEN",
    },
    "a2_001": {
        "binding_and_authorization": "valid",
        "lab_halt": "BASE_COMMIT_UNAVAILABLE",
        "next_permitted_remedy": "owner-authorized hash-verified offline Git bundle",
        "fetch_ssh_network_to_lab": False,
        "bundle_created_this_observation": False,
    },
    "dev_182_0001": "EVIDENCE_INSUFFICIENT pending live-harness verification; no scheduler inspect/cancel this turn",
})
print("NOW", now)
print("JSONL_SHA", jsonl_sha)
print("ROWS", len(rows))
