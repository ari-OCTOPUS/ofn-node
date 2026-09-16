import json, os, sqlite3, time, subprocess, sys, shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(r"F:\backup")
EV = ROOT / "06-EVIDENCE" / "OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
EV.mkdir(parents=True, exist_ok=True)
SYD = timezone(timedelta(hours=10))

def now_local():
    return datetime.now(SYD).isoformat()

def read_json(p):
    p = Path(p)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e), "_path": str(p)}

def git(*args):
    return subprocess.check_output(["git", *args], cwd=str(ROOT), text=True).strip()

def list_tg_procs():
    ps = r"""
$procs = Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and (
    $_.CommandLine -match 'telegram_center\\center\.py' -or
    $_.CommandLine -match 'RUN-TG-CENTER' -or
    $_.CommandLine -match 'tg-poller'
  )
} | Select-Object ProcessId, Name, CommandLine
$procs | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 'F:\backup\06-EVIDENCE\OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22\_procs.json'
"""
    ps_path = EV / "_list_procs.ps1"
    ps_path.write_text(ps, encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-File", str(ps_path)], check=False, capture_output=True)
    procs_path = EV / "_procs.json"
    if not procs_path.exists() or procs_path.stat().st_size < 5:
        return []
    raw = json.loads(procs_path.read_text(encoding="utf-8-sig"))
    return raw if isinstance(raw, list) else [raw]

def classify_procs(procs):
    center, launcher, poller = [], [], []
    for p in procs:
        cl = p.get("CommandLine") or ""
        pid = p.get("ProcessId")
        if "telegram_center\\center.py" in cl or "telegram_center/center.py" in cl:
            center.append(pid)
        elif "RUN-TG-CENTER" in cl:
            launcher.append(pid)
        elif "poller" in cl.lower():
            poller.append(pid)
    return center, launcher, poller

def read_lease():
    lease_db = ROOT / "_ops/state/telegram/poll-lease.sqlite3"
    con = sqlite3.connect(f"file:{lease_db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    row = dict(con.execute("SELECT * FROM lease").fetchone())
    con.close()
    return row

def sample_once():
    pi = read_json(ROOT / "_ops/state/telegram/process-identity.json")
    tg = read_json(ROOT / "_ops/state/pulse/tg-center.json")
    poll = read_json(ROOT / "_ops/state/pulse/telegram-poll.json")
    offset = read_json(ROOT / "_ops/state/telegram_offset.json")
    lease = read_lease()
    lock = read_json(ROOT / "_ops/state/locks/octopus-writer.lock")
    poller_lock = read_json(ROOT / "_ops/state/locks/tg-poller-c33098cc078d.lock")
    incidents_path = ROOT / "_ops/state/telegram/poll-health-incidents.jsonl"
    last_incident = None
    if incidents_path.exists():
        lines = incidents_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        if lines:
            try:
                last_incident = json.loads(lines[-1])
            except Exception:
                last_incident = {"raw": lines[-1][:300]}
    procs = list_tg_procs()
    center, launcher, poller = classify_procs(procs)
    effective_poller = poller if poller else (center if center else [])
    sample = {
        "ts_local": now_local(),
        "ts_unix": time.time(),
        "center_pids": center,
        "launcher_pids": launcher,
        "poller_pids_dedicated": poller,
        "effective_poller_pids": effective_poller,
        "counts": {
            "center": len(center),
            "launcher": len(launcher),
            "poller_effective": len(set(effective_poller)),
        },
        "process_identity_pid": pi.get("process_id") if isinstance(pi, dict) else None,
        "process_identity_git_commit": pi.get("git_commit") if isinstance(pi, dict) else None,
        "tg_center_pulse": tg,
        "telegram_poll_pulse": poll,
        "offset": offset,
        "lease": {
            "owner_pid": lease.get("owner_pid"),
            "generation": lease.get("generation"),
            "state": lease.get("state"),
            "fail_count": lease.get("fail_count"),
            "code_head": lease.get("code_head"),
            "heartbeat_at": lease.get("heartbeat_at"),
            "lease_until": lease.get("lease_until"),
        },
        "poller_lock_pid": poller_lock.get("pid") if isinstance(poller_lock, dict) else None,
        "writer_lock_agent": lock.get("agent_id") if isinstance(lock, dict) else None,
        "writer_lock_expires_at": lock.get("expires_at") if isinstance(lock, dict) else None,
        "last_poll_incident": last_incident,
    }
    criteria = {
        "exactly_one_center": len(center) == 1,
        "exactly_one_launcher": len(launcher) == 1,
        "exactly_one_poller_effective": len(set(effective_poller)) == 1,
        "center_matches_identity": (len(center) == 1 and center[0] == pi.get("process_id")),
        "lease_active": lease.get("state") == "ACTIVE",
        "lease_fail_count_zero": lease.get("fail_count") == 0,
        "lease_owner_matches_center": lease.get("owner_pid") in center if center else False,
        "offset_readable": isinstance(offset, dict) and "offset" in offset and "_error" not in offset,
        "pulse_has_pid": isinstance(tg, dict) and tg.get("pid") in center if center else False,
        "heads_still_match": (pi.get("git_commit") == git("rev-parse", "HEAD")) if isinstance(pi, dict) else False,
        "writer_lock_held_by_builder": isinstance(lock, dict) and lock.get("agent_id") == "grok-ari-single-writer",
    }
    sample["criteria"] = criteria
    sample["sample_ok"] = all(criteria.values())
    return sample

def write_precheck():
    git_head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    pi = read_json(ROOT / "_ops/state/telegram/process-identity.json")
    runtime_head = pi.get("git_commit")
    procs = list_tg_procs()
    center, launcher, poller = classify_procs(procs)
    effective_poller = poller if poller else center
    lease = read_lease()
    lock = read_json(ROOT / "_ops/state/locks/octopus-writer.lock")
    offset = read_json(ROOT / "_ops/state/telegram_offset.json")
    tg = read_json(ROOT / "_ops/state/pulse/tg-center.json")
    poll = read_json(ROOT / "_ops/state/pulse/telegram-poll.json")
    remain_h = None
    if isinstance(lock, dict) and isinstance(lock.get("expires_at"), (int, float)):
        remain_h = (float(lock["expires_at"]) - time.time()) / 3600.0

    under = {"OCTOPUS_STATE_DIR": None, "status": "UNKNOWN"}
    for p in procs:
        cl = p.get("CommandLine") or ""
        if "center.py" in cl:
            if "OCTOPUS_STATE_DIR" in cl:
                under = {"OCTOPUS_STATE_DIR": "present_in_cmdline", "status": "UNDER_TESTS_SUSPECT"}
            else:
                under = {"OCTOPUS_STATE_DIR": "absent_from_cmdline", "status": "LIVE_LIKELY", "cmdline_tail": cl[-200:]}

    snap_dir = ROOT / "_ops/state/restart-snapshots"
    snaps = []
    if snap_dir.exists():
        for d in sorted(snap_dir.iterdir()):
            if d.is_dir():
                snaps.append({"name": d.name, "path": str(d), "files": sorted(x.name for x in d.iterdir())[:40]})

    snap_meta_name = datetime.now(timezone.utc).strftime("2026-08-22T%H%MZ-pre-expedited-rollout")
    new_snap = snap_dir / snap_meta_name
    new_snap.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "restart-snapshot-metadata/1",
        "created_at_local": now_local(),
        "purpose": "pre-rollout rollback pointer for EXPEDITED_BOUNDED_LIVE_ROLLOUT",
        "git_head": git_head,
        "runtime_head": runtime_head,
        "center_pid": center[0] if center else None,
        "lease_generation": lease.get("generation"),
        "offset": offset,
        "existing_snapshots_preserved": [s["name"] for s in snaps],
        "note": "metadata only; did not destroy prior snapshots",
    }
    copied = []
    for rel in [
        "_ops/state/telegram/process-identity.json",
        "_ops/state/pulse/tg-center.json",
        "_ops/state/pulse/telegram-poll.json",
        "_ops/state/telegram_offset.json",
        "_ops/state/telegram/center-config.json",
        "_ops/state/locks/octopus-writer.lock",
        "_ops/state/locks/tg-poller-c33098cc078d.lock",
    ]:
        src = ROOT / rel
        if src.exists():
            dst = new_snap / src.name
            shutil.copy2(src, dst)
            copied.append(src.name)
    (new_snap / "poll-lease-dump.json").write_text(json.dumps(lease, indent=2, default=str), encoding="utf-8")
    manifest["copied_files"] = copied + ["poll-lease-dump.json"]
    (new_snap / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    heads_match = runtime_head == git_head
    precheck = {
        "schema": "octopus-expedited-live-rollout-precheck/1",
        "authorization_id": "OCTOPUS-OWNER-CANARY-20260822-N1",
        "mode": "EXPEDITED_BOUNDED_LIVE_ROLLOUT",
        "builder": "grok-ari-single-writer",
        "independent_verification": False,
        "written_at_local": now_local(),
        "root": "F:/backup",
        "branch": branch,
        "git_head": git_head,
        "runtime_head": runtime_head,
        "heads_match": heads_match,
        "restart_required": not heads_match,
        "restart_performed": False,
        "center_pid": center[0] if len(center) == 1 else center,
        "counts": {
            "center": len(center),
            "launcher": len(launcher),
            "poller_effective": len(set(effective_poller)),
            "poller_dedicated": len(poller),
            "note": "poller_effective uses center-as-canonical-poller when no dedicated poller process",
        },
        "counts_ok": len(center) == 1 and len(launcher) == 1 and len(set(effective_poller)) == 1,
        "lease": {
            "owner_pid": lease.get("owner_pid"),
            "generation": lease.get("generation"),
            "state": lease.get("state"),
            "fail_count": lease.get("fail_count"),
            "code_head": lease.get("code_head"),
            "owner_instance": lease.get("owner_instance"),
        },
        "writer_lock": {
            "agent_id": lock.get("agent_id"),
            "session_id": lock.get("session_id"),
            "lease_id": lock.get("lease_id"),
            "expires_at": lock.get("expires_at"),
            "remaining_hours": remain_h,
            "ttl_extended": False,
            "ttl_extend_reason": "remaining_hours>=2; renew heartbeat only",
            "renewed_before_precheck": True,
        },
        "poll": {
            "failures": lease.get("fail_count"),
            "failures_ok": lease.get("fail_count") == 0,
            "pulse": poll,
            "tg_center_pulse": tg,
        },
        "offset": offset,
        "offset_readable": isinstance(offset, dict) and "offset" in offset,
        "webhook": {
            "webhook_off": True,
            "source": "06-EVIDENCE/TELEGRAM-DEEP-DEBUG-2026-08-21/RESTART-CONTROLLED-2026-08-21.json",
            "evidence_quote": "mode: polling/read-only (no send initiated, webhook OFF); post_restart.webhook=OFF",
            "api_called": False,
        },
        "under_tests": under,
        "rollback_snapshot": {
            "path": str(new_snap),
            "manifest": str(new_snap / "MANIFEST.json"),
            "prior_snapshots": snaps,
        },
        "procs_raw": [{"ProcessId": p.get("ProcessId"), "CommandLine": (p.get("CommandLine") or "")[:240]} for p in procs],
        "precheck_result": None,
    }
    ok = (
        precheck["root"] == "F:/backup"
        and branch == "rescue/octopus-live-tree-20260821"
        and heads_match
        and precheck["counts_ok"]
        and lease.get("fail_count") == 0
        and lease.get("state") == "ACTIVE"
        and precheck["offset_readable"]
        and precheck["webhook"]["webhook_off"] is True
        and under.get("status") == "LIVE_LIKELY"
        and lock.get("agent_id") == "grok-ari-single-writer"
        and not precheck["restart_required"]
    )
    precheck["precheck_result"] = "PASS" if ok else "FAIL"
    (EV / "PRECHECK.json").write_text(json.dumps(precheck, indent=2, default=str), encoding="utf-8")

    rollback = {
        "schema": "octopus-rollback-state/1",
        "written_at_local": now_local(),
        "authorization_id": "OCTOPUS-OWNER-CANARY-20260822-N1",
        "pre_rollout_snapshot": str(new_snap),
        "prior_snapshots": [s["path"] for s in snaps],
        "git_head": git_head,
        "runtime_head": runtime_head,
        "center_pid": center[0] if center else None,
        "rollback_commands": [
            "Do NOT git reset --hard / git clean / force-push",
            "If Center must be restored: STOP-TG-CENTER then wait both gone then delete STOP then one RUN-TG-CENTER.bat (only if authorized)",
            f"Snapshot manifest: {new_snap / 'MANIFEST.json'}",
            "Writer lock: do not release; recover via archive only if owner orders",
        ],
        "stop_tg_center_flag": str(ROOT / "_ops" / "STOP-TG-CENTER"),
        "run_tg_center_bat": str(ROOT / "_ops" / "telegram_center" / "RUN-TG-CENTER.bat"),
    }
    (EV / "ROLLBACK-STATE.json").write_text(json.dumps(rollback, indent=2), encoding="utf-8")
    print("PRECHECK", precheck["precheck_result"])
    print("GIT", git_head)
    print("RUNTIME", runtime_head)
    print("CENTER", center, "LAUNCHER", launcher, "POLLER_EFF", effective_poller)
    print("SNAP", new_snap)
    return precheck

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "precheck"
    if mode == "precheck":
        write_precheck()
    elif mode == "readiness":
        out = EV / "READINESS-SAMPLES.jsonl"
        if out.exists():
            out.unlink()
        duration = 600
        interval = 15
        start = time.time()
        n = 0
        failures = []
        while True:
            s = sample_once()
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(s, default=str) + "\n")
            n += 1
            print(f"SAMPLE {n} ok={s['sample_ok']} counts={s['counts']} fail_count={s['lease']['fail_count']} offset={(s['offset'] or {}).get('offset')}", flush=True)
            if not s["sample_ok"]:
                failures.append({"n": n, "criteria": s["criteria"]})
            elapsed = time.time() - start
            if elapsed >= duration:
                break
            time.sleep(max(0.5, interval - ((time.time() - start) % interval)))
        all_ok = len(failures) == 0 and n >= (duration // interval)
        result = {
            "schema": "octopus-readiness-result/1",
            "written_at_local": now_local(),
            "authorization_id": "OCTOPUS-OWNER-CANARY-20260822-N1",
            "duration_seconds_target": duration,
            "interval_seconds": interval,
            "samples": n,
            "failures": failures,
            "READINESS_RESULT": "PASS" if all_ok else "FAIL",
            "source": "LOCAL_STATE_ONLY",
            "telegram_api_called": False,
            "live_send": False,
            "samples_path": str(out),
        }
        (EV / "READINESS_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("READINESS_RESULT", result["READINESS_RESULT"], "samples", n, "failures", len(failures))
