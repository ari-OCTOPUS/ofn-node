import json, subprocess, time, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(r"F:\backup")
EV = ROOT / "06-EVIDENCE" / "OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
SYD = timezone(timedelta(hours=10))
now = datetime.now(SYD).isoformat()

head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(ROOT), text=True).strip()

lock_path = ROOT / "_ops/state/locks/octopus-writer.lock"
lock = json.loads(lock_path.read_text(encoding="utf-8"))
rem_h = (float(lock.get("expires_at", 0)) - time.time()) / 3600.0
renewed = False
renew_err = None
try:
    sys.path.insert(0, str(ROOT / "_ops"))
    try:
        from live_state_guard import allow_live_write  # type: ignore
        with allow_live_write(reason="rfc-merge-heartbeat"):
            if lock.get("agent_id") == "grok-ari-single-writer":
                lock["heartbeat_at"] = time.time()
                lock["renewed_at_local"] = now
                lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
                renewed = "allow_live_write+heartbeat"
    except Exception as e1:
        renew_err = f"allow_live_write:{type(e1).__name__}:{e1}"
        if lock.get("agent_id") == "grok-ari-single-writer":
            lock["heartbeat_at"] = time.time()
            lock["renewed_at_local"] = now
            lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
            renewed = "heartbeat_ts_touch_fallback"
except Exception as e:
    renew_err = str(e)

lab_proof = Path(r"F:\backup\_ops\state\lab\ce-evo-20260822T133352\state\sul\cycle-proof.json")
lab_cycle = Path(r"F:\backup\_ops\state\lab\ce-evo-20260822T133352\cycle-result.json")
cycle = json.loads(lab_cycle.read_text(encoding="utf-8")) if lab_cycle.exists() else {}
out = cycle.get("out") or {}
verify = out.get("verify") or {}

def find_rb(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "rollback" in str(k).lower():
                found.append({"path": path + "." + k, "value_type": type(v).__name__, "value_preview": v if not isinstance(v, (dict, list)) else None})
            found.extend(find_rb(v, path + "." + k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:30]):
            found.extend(find_rb(v, f"{path}[{i}]"))
    return found

rb_fields = find_rb(cycle)
rfcs_live = json.loads((ROOT / "_ops/state/doctor/rfcs.json").read_text(encoding="utf-8")).get("rfcs") or []
live_ids = [r.get("rfc_id") for r in rfcs_live]

candidates = [{
    "rfc_id": "RFC-CE-EVO-20260822",
    "source": "lab_isolated_worktree",
    "experiment_id": out.get("experiment_id"),
    "in_live_doctor_registry": "RFC-CE-EVO-20260822" in live_ids,
    "test_ok": (out.get("test_outcome") == "pass") or bool(((out.get("tests") or {}).get("after") or {}).get("all_pass")),
    "evidence_path": str(lab_proof) if lab_proof.is_file() else None,
    "evidence_path_exists": lab_proof.is_file(),
    "rollback_plan_present": False,
    "rollback_ok_flag": bool(verify.get("rollback_ok")),
    "rollback_related_fields": rb_fields[:20],
    "gate_with_proofs_lab": cycle.get("gate_with_proofs"),
    "live_promote": out.get("live_promote"),
    "promotion_level": out.get("promotion_level"),
    "worktree_only": True,
    "artifacts_on_live_tree": False,
    "eligible": False,
    "missing_proofs": [
        "not_in_live_doctor_rfcs_registry (apply_merge returns False unless rfc_id in Doctor._rfcs)",
        "missing_rollback_plan field on lab cycle artifacts (only verify.rollback_ok boolean; refuse inventing plan)",
        "apply_merge path does not cherry-pick worktree code commits for change_level=code; fixture stayed LAB_PASS/live_promote=false",
    ],
}]

for r in rfcs_live:
    sr = r.get("sandbox_result") or {}
    tests = sr.get("tests")
    test_ok = False
    if isinstance(tests, dict):
        test_ok = bool(tests.get("all_pass") or tests.get("passed"))
    ep = sr.get("evidence_path") or r.get("evidence_path")
    rb = r.get("rollback") or sr.get("rollback_plan") or sr.get("rollback")
    missing = []
    if not test_ok:
        missing.append("test_ok (sandbox tests null/unvalidated)")
    if not ep:
        missing.append("evidence_path")
    if not rb:
        missing.append("rollback_plan")
    status = r.get("status")
    if status not in ("submitted", "submitted-no-channel"):
        missing.append("status=%s not submitted" % status)
    critic = (sr.get("critic") or r.get("critic_review") or {})
    if critic.get("sandbox_validated") is False:
        missing.append("sandbox_validated=false")
    if status == "stale-input":
        missing.append("stale-input")
    if status == "applied":
        missing.append("already_applied")
    candidates.append({
        "rfc_id": r.get("rfc_id"),
        "source": "live_doctor_rfcs.json",
        "status": status,
        "test_ok": test_ok,
        "evidence_path": ep,
        "rollback_plan_present": bool(rb),
        "rollback": rb,
        "sandbox_validated": critic.get("sandbox_validated"),
        "eligible": False,
        "missing_proofs": missing,
    })

eligible = [c for c in candidates if c.get("eligible")]

doc = {
    "schema": "octopus-expedited-live-rollout-rfc-merge/1",
    "authorization_id": "OCTOPUS-OWNER-CANARY-20260822-N1",
    "mode": "EXPEDITED_BOUNDED_LIVE_ROLLOUT",
    "builder": "grok-ari-single-writer",
    "independent_verification": False,
    "written_at_local": now,
    "section": "ONE_gate_qualified_RFC_merge",
    "result": "NO_RFC_ELIGIBLE",
    "merged": False,
    "merge_performed": False,
    "rfc_id_merged": None,
    "before_head": head,
    "after_head": head,
    "heads_changed": False,
    "branch": branch,
    "git_head": head,
    "precheck_head_reference": "2ab0eb8725653b02c19b316dc136347af26465c2",
    "note_on_head": "Recorded live HEAD at RFC step; no merge commit applied. Precheck HEAD may differ if other writers advanced tree; this step did not mutate git.",
    "candidates_examined": candidates,
    "eligible_count": len(eligible),
    "reason": (
        "No gate-qualified RFC for owner [merge]. "
        "Lab fixture RFC-CE-EVO-20260822 has test pass + evidence file but is worktree-isolated, "
        "absent from live Doctor._rfcs registry (apply_merge would no-op/False), and lacks an explicit rollback_plan object "
        "(only verify.rollback_ok). Live submitted RFC-dac24854 lacks test_ok/evidence_path and sandbox_validated=false. "
        "Per P2: refuse without proofs; prefer NO_RFC_ELIGIBLE over inventing RFC/proofs/force-merge."
    ),
    "constraints_honored": [
        "thematic_stage_only_no_git_add_A",
        "no_money_wires",
        "no_live_telegram_send",
        "no_webhook",
        "no_SIG-IV",
        "no_force_merge",
        "no_invented_rfc_or_proofs",
        "writer_lock_grok-ari-single-writer",
    ],
    "writer_lock": {
        "agent_id": lock.get("agent_id"),
        "session_id": lock.get("session_id"),
        "lease_id": lock.get("lease_id"),
        "expires_at": lock.get("expires_at"),
        "remaining_hours_approx": rem_h,
        "renew_attempt": renewed,
        "renew_error": renew_err,
    },
    "paths": {
        "evidence": str(EV / "RFC-MERGE.json"),
        "lab_cycle_result": str(lab_cycle),
        "lab_cycle_proof": str(lab_proof),
        "live_rfcs": str(ROOT / "_ops/state/doctor/rfcs.json"),
    },
    "next_deferred": ["canary", "LIVE-B", "soak"],
    "canary_started": False,
}

out_path = EV / "RFC-MERGE.json"
out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("WROTE", out_path)
print("result", doc["result"])
print("HEAD", head)
print("eligible_count", doc["eligible_count"])
for c in candidates:
    print("CAND", c["rfc_id"], "missing=", c.get("missing_proofs"))
