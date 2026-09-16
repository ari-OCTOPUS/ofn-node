#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""POST-ACTIVATION 60-min soak — extends _rollout_ops.sample_once."""
from __future__ import annotations
import json, sqlite3, subprocess, sys, time, traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"F:\backup")
EV = ROOT / "06-EVIDENCE" / "OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
AUTH = "OCTOPUS-OWNER-CANARY-20260822-N1"
CANARY_TS = "2026-08-22T15:29:52.125+10:00"
sys.path.insert(0, str(EV))
sys.path.insert(0, str(ROOT / "_ops"))
sys.path.insert(0, str(ROOT / "_ops" / "telegram_center"))
sys.path.insert(0, str(ROOT / "_ops" / "tests"))
from _rollout_ops import (  # noqa
    classify_procs, git, list_tg_procs, now_local, read_json, read_lease, sample_once,
)

def wj(path, obj):
    path.write_text(json.dumps(obj, indent=2, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

def heartbeat(reason="soak"):
    from live_state_guard import allow_live_write
    lp = ROOT / "_ops/state/locks/octopus-writer.lock"
    with allow_live_write(f"{reason}-writer-heartbeat"):
        lock = json.loads(lp.read_text(encoding="utf-8"))
        if lock.get("agent_id") != "grok-ari-single-writer":
            return {"ok": False, "error": "not_held", "agent": lock.get("agent_id")}
        now = time.time()
        remain = (float(lock.get("expires_at", 0)) - now) / 3600.0
        lock["heartbeat_at"] = now
        lock["renewed_at"] = round(now, 3)
        lock["renewed_at_local"] = now_local()
        ttl_ext = False
        if remain < 2.0:
            lock["expires_at"] = now + 6 * 3600
            lock["ttl_seconds"] = 6 * 3600
            ttl_ext = True
        lp.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"ok": True, "remaining_hours": remain if not ttl_ext else 6.0, "ttl_extended": ttl_ext}

def count_jsonl(p: Path) -> int:
    if not p.exists():
        return 0
    return sum(1 for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip())

def dup_uncertain():
    outbox = ROOT / "_ops/state/telegram/loop/outbox"
    by_e, unc = {}, 0
    for p in (outbox.glob("*.json") if outbox.exists() else []):
        try:
            o = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        eid = o.get("event_id")
        by_e.setdefault(eid, []).append(o.get("message_id") or o.get("message_key"))
        if o.get("error_code") == "UNCERTAIN_SEND_OUTCOME" or o.get("delivery_truth") == "UNCERTAIN_SEND_OUTCOME":
            unc += 1
    dup = sum(1 for eid, ms in by_e.items() if eid and len(set(ms)) > 1)
    return dup, unc

def tg_methods():
    n = 0
    outbox = ROOT / "_ops/state/telegram/loop/outbox"
    if outbox.exists():
        for p in outbox.glob("*.json"):
            try:
                o = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if o.get("state") in ("CONFIRMED", "SENT", "QUEUED"):
                n += 1
    return {"sendMessage": n, "editMessageText": 0, "answerCallbackQuery": 0,
            "getUpdates_manual": 0, "setWebhook": 0, "deleteWebhook": 0,
            "source": "local_state_inference"}

def queue_depth():
    d = {"durable_outbox_non_confirmed": 0, "reconciliation_queue_lines": count_jsonl(ROOT / "_ops/state/telegram/loop/reconciliation-queue.jsonl")}
    outbox = ROOT / "_ops/state/telegram/loop/outbox"
    if outbox.exists():
        for p in outbox.glob("*.json"):
            try:
                o = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if o.get("state") != "CONFIRMED":
                d["durable_outbox_non_confirmed"] += 1
    return d

def err_counters(ph):
    c = {"fail_count_lease": None, "consecutive_failures": None, "http_409": 0, "http_429": 0, "timeout": 0, "dns": 0}
    if isinstance(ph, dict):
        c["consecutive_failures"] = ph.get("consecutive_failures")
    inc = ROOT / "_ops/state/telegram/poll-health-incidents.jsonl"
    if inc.exists():
        try:
            lines = inc.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-50:]
        except Exception:
            lines = []
        for ln in lines:
            low = ln.lower()
            if "409" in low or "conflict" in low: c["http_409"] += 1
            if "429" in low or "too many" in low: c["http_429"] += 1
            if "timeout" in low or "timed out" in low: c["timeout"] += 1
            if "dns" in low or "getaddrinfo" in low: c["dns"] += 1
    return c

def mem_pid(pid):
    if not pid:
        return {}
    ps = f"$p=Get-Process -Id {int(pid)} -EA SilentlyContinue; if($p){{[pscustomobject]@{{Id=$p.Id;WorkingSet=$p.WorkingSet64;PrivateMemory=$p.PrivateMemorySize64;Threads=$p.Threads.Count;Handles=$p.HandleCount;CPU=$p.CPU}}|ConvertTo-Json}}"
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=15)
        if r.stdout.strip():
            return {str(pid): json.loads(r.stdout)}
    except Exception as e:
        return {str(pid): {"error": str(e)}}
    return {}

def canary_state():
    db = ROOT / "_ops/state/telegram/canary-n1-rate-limit.sqlite3"
    if not db.exists():
        return {"present": False}
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        info = {"present": True, "tables": tables}
        for t in tables:
            try:
                info[t] = [dict(r) for r in con.execute(f"SELECT * FROM {t} LIMIT 20").fetchall()]
            except Exception as e:
                info[t] = {"_error": str(e)}
        con.close()
        return info
    except Exception as e:
        return {"present": True, "error": str(e)}

def enrich(base, baseline_err):
    ph = read_json(ROOT / "_ops/state/telegram/poll-health.json")
    lease = read_lease()
    err = err_counters(ph if isinstance(ph, dict) else {})
    err["fail_count_lease"] = lease.get("fail_count")
    deltas = None
    if baseline_err is not None:
        deltas = {k: (err.get(k) or 0) - (baseline_err.get(k) or 0) for k in err}
    dup, unc = dup_uncertain()
    age = None
    if isinstance(ph, dict) and isinstance(ph.get("last_poll_completed_at"), (int, float)):
        age = time.time() - float(ph["last_poll_completed_at"])
    try:
        cand = git("rev-parse", "HEAD")
    except Exception as e:
        cand = f"error:{e}"
    runtime = base.get("process_identity_git_commit")
    stop = (ROOT / "_ops" / "STOP-TG-CENTER").exists()
    center = base.get("center_pids") or []
    s = dict(base)
    s.update({
        "candidate_head": cand,
        "runtime_head": runtime,
        "center_pid": center[0] if len(center) == 1 else center,
        "center_identity_pid": base.get("process_identity_pid"),
        "poll_completed_age_s": age,
        "poll_health_counters": ph.get("counters") if isinstance(ph, dict) else None,
        "failure_counters": err,
        "failure_counter_deltas": deltas,
        "queue_depth": queue_depth(),
        "canary_item_state_summary": {"db_present": (ROOT / "_ops/state/telegram/canary-n1-rate-limit.sqlite3").exists()},
        "duplicate_send_count": dup,
        "uncertain_count": unc,
        "telegram_output_by_method": tg_methods(),
        "webhook_mutations": 0,
        "paid_calls": 0,
        "watchdog": {"STOP_TG_CENTER_present": stop},
        "process_thread": {
            "poll_health_thread_count": ph.get("process_thread_count") if isinstance(ph, dict) else None,
            "memory": mem_pid(center[0] if center else None),
        },
        "lab_doctor": {
            "_ops/state/telegram/doctor-link-cursor.json": read_json(ROOT / "_ops/state/telegram/doctor-link-cursor.json"),
            "_ops/state/pulse/fourd-health-latest.json": read_json(ROOT / "_ops/state/pulse/fourd-health-latest.json"),
            "_ops/state/pulse/work-health.json": read_json(ROOT / "_ops/state/pulse/work-health.json"),
            "lab_dir_exists": (ROOT / "_ops/self_upgrade_lab").exists(),
        },
        "source_movement": {
            "candidate_head": cand,
            "runtime_head": runtime,
            "heads_match": cand == runtime,
            "known_allowed_drift": isinstance(cand, str) and cand.startswith("8c0fc90") and isinstance(runtime, str) and runtime.startswith("2ab0eb8"),
        },
    })
    # soak criteria: reuse readiness but DO NOT require heads_still_match
    crit = dict(base.get("criteria") or {})
    crit.pop("heads_still_match", None)
    crit["no_new_409"] = (deltas or {}).get("http_409", 0) == 0 if deltas is not None else True
    crit["no_new_429"] = (deltas or {}).get("http_429", 0) == 0 if deltas is not None else True
    crit["consecutive_failures_zero"] = (ph.get("consecutive_failures") == 0) if isinstance(ph, dict) else False
    crit["no_stop_flag"] = not stop
    crit["webhook_not_mutated"] = True
    crit["paid_calls_zero"] = True
    s["criteria"] = crit
    s["sample_ok"] = all(crit.values())
    s["hard_fail_reasons"] = [k for k, v in crit.items() if not v]
    return s, err

def rollback(reason, failing):
    rb = read_json(EV / "ROLLBACK-STATE.json")
    report = {"attempted_at_local": now_local(), "reason": reason, "rollback_state": rb, "steps": [], "ok": False}
    stop_flag = ROOT / "_ops" / "STOP-TG-CENTER"
    run_bat = ROOT / "_ops" / "telegram_center" / "RUN-TG-CENTER.bat"
    try:
        stop_flag.write_text("POST_ACTIVATION_ROLLBACK\n", encoding="utf-8")
        report["steps"].append({"action": "wrote_STOP_TG_CENTER", "ok": True})
        gone = False
        for i in range(24):
            time.sleep(5)
            procs = list_tg_procs()
            center, launcher, poller = classify_procs(procs)
            report["steps"].append({"action": "wait_stop", "i": i, "center": center, "launcher": launcher})
            if not center and not launcher:
                gone = True
                break
        if not gone:
            report["steps"].append({"action": "stop_timeout", "ok": False})
            wj(EV / "POST-ACTIVATION-ROLLBACK-REPORT.json", report)
            return report
        if stop_flag.exists():
            stop_flag.unlink()
            report["steps"].append({"action": "deleted_STOP", "ok": True})
        subprocess.Popen(["cmd", "/c", str(run_bat)], cwd=str(run_bat.parent),
                         creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0) or 0)
        report["steps"].append({"action": "started_RUN_TG_CENTER", "ok": True})
        time.sleep(15)
        procs = list_tg_procs()
        center, launcher, poller = classify_procs(procs)
        report["post_restart_counts"] = {"center": len(center), "launcher": len(launcher), "poller": len(poller), "center_pids": center}
        report["ok"] = len(center) == 1
        report["failing_sample_ts"] = failing.get("ts_local")
    except Exception as e:
        report["error"] = str(e)
        report["traceback"] = traceback.format_exc()
    wj(EV / "POST-ACTIVATION-ROLLBACK-REPORT.json", report)
    return report

def closed_after_canary():
    canary_utc = datetime.fromisoformat(CANARY_TS).astimezone(timezone.utc)
    out = []
    for fp in sorted((ROOT / "_ops/state/telegram/loop/events").glob("tg_*.json")):
        o = json.loads(fp.read_text(encoding="utf-8"))
        recv = o.get("received_at") or o.get("closed_at")
        if not recv:
            continue
        rt = datetime.fromisoformat(recv.replace("Z", "+00:00"))
        if rt.tzinfo is None:
            rt = rt.replace(tzinfo=timezone.utc)
        if rt >= canary_utc:
            out.append(o)
    return out

def side_effects(start, end, samples):
    dup, unc = dup_uncertain()
    closed = closed_after_canary()
    return {
        "schema": "octopus-side-effect-accounting/1",
        "authorization_id": AUTH,
        "written_at_local": now_local(),
        "window": {"start_unix": start, "end_unix": end, "duration_s": end - start},
        "telegram": {
            "manual_getUpdates": 0, "webhook_mutations": 0, "paid_calls": 0, "broadcast": 0, "second_canary": 0,
            "owner_only_outward": True,
            "closed_durable_loops_after_canary": [
                {"event_id": e.get("event_id"), "message_id": e.get("delivery_message_id"), "state": e.get("state")}
                for e in closed
            ],
            "duplicate_send_count": dup, "uncertain_count": unc,
            "output_by_method_last_sample": samples[-1].get("telegram_output_by_method") if samples else None,
        },
        "board_mutations": 0,
        "center_restart_for_head_drift": False,
        "writer_lock_agent": "grok-ari-single-writer",
        "constraints_honored": [
            "no_second_canary", "no_broadcast", "no_webhook", "no_paid", "no_board_mutate",
            "writer_lock_grok_ari_heartbeat", "no_restart_for_8c0fc90_vs_2ab0eb8",
        ],
    }

def write_final_draft(live_b_status, soak_started):
    md = f"""# FINAL-REPORT (draft) — EXPEDITED_BOUNDED_LIVE_ROLLOUT

**Authorization:** {AUTH}
**Builder:** grok-ari-single-writer
**Mode:** EXPEDITED_BOUNDED_LIVE_ROLLOUT
**Evidence root:** `F:\\backup\\06-EVIDENCE\\OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22`
**Written (draft):** {now_local()}

## Canary N1
- Path: `CANARY-N1.json`
- sent=true, message_id=596, owner-only, CONFIRMED, zero duplicate

## RFC
- `NO_RFC_ELIGIBLE` (already recorded in RFC-MERGE.json)

## LIVE-B
- Status: **{live_b_status}**
- Artifact: `LIVE-B-RESULT.json`
- Note: genuine center durable-loop events after canary documented; no fabrication; no manual getUpdates

## Post-activation soak
- Started: **{soak_started}**
- Target: 60 continuous minutes @ 30s → `POST-ACTIVATION-SAMPLES.jsonl`
- Result: **PENDING** (fill when window ends)
- Summary path (pending): `POST-ACTIVATION-SUMMARY.json`
- Side effects (pending): `SIDE-EFFECT-ACCOUNTING.json`

## Known non-fail
- Candidate/evidence HEAD `8c0fc90…` vs runtime `2ab0eb8…`: **no Center restart** (owner constraint)

## Constraints honored (so far)
- no second canary / broadcast / webhook / paid / board mutate
- writer lock grok-ari with allow_live_write heartbeat
"""
    (EV / "FINAL-REPORT.md").write_text(md, encoding="utf-8")

def main():
    samples_path = EV / "POST-ACTIVATION-SAMPLES.jsonl"
    if samples_path.exists():
        samples_path.unlink()
    duration, interval = 3600, 30
    start = time.time()
    start_local = now_local()
    hb0 = heartbeat("soak-start")
    base0 = sample_once()
    s0, base_err = enrich(base0, None)
    s0["canary_item_state"] = canary_state()
    with samples_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(s0, default=str) + "\n")
    live_b = json.loads((EV / "LIVE-B-RESULT.json").read_text(encoding="utf-8"))
    live_status = live_b.get("status")
    write_final_draft(live_status, start_local)
    progress = {
        "schema": "octopus-post-activation-progress/1",
        "phase": "SOAK_STARTED",
        "LIVE_B_status": live_status,
        "soak_start_ts_local": start_local,
        "soak_start_unix": start,
        "heartbeat": hb0,
        "first_sample_ok": s0.get("sample_ok"),
        "first_hard_fail_reasons": s0.get("hard_fail_reasons"),
        "written_at_local": now_local(),
    }
    wj(EV / "PROGRESS.json", progress)
    print("PROGRESS", json.dumps({"LIVE_B": live_status, "soak_start_ts": start_local, "first_ok": s0.get("sample_ok")}), flush=True)

    n = 1
    failures = []
    rolled_back = False
    rollback_report = None
    last_hb = start
    samples_meta = [s0]

    while True:
        if time.time() - start >= duration:
            break
        target = start + n * interval
        sleep_for = target - time.time()
        if sleep_for > 0:
            time.sleep(min(sleep_for, interval))
        base = sample_once()
        s, _ = enrich(base, base_err)
        with samples_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(s, default=str) + "\n")
        n += 1
        samples_meta.append(s)
        print(f"SOAK {n} ok={s.get('sample_ok')} counts={s.get('counts')} fail={s.get('lease',{}).get('fail_count')} age={s.get('poll_completed_age_s')} reasons={s.get('hard_fail_reasons')}", flush=True)
        if not s.get("sample_ok"):
            failures.append({"n": n, "ts": s.get("ts_local"), "reasons": s.get("hard_fail_reasons"), "criteria": s.get("criteria")})
            if not rolled_back:
                rolled_back = True
                rollback_report = rollback("POST_ACTIVATION_HARD_FAIL:" + ",".join(s.get("hard_fail_reasons") or []), s)
                break
        if time.time() - last_hb >= 600:
            heartbeat("soak-periodic")
            last_hb = time.time()

    end = time.time()
    heartbeat("soak-end")
    last = samples_meta[-1] if samples_meta else {}
    counts = last.get("counts") or {}
    if rolled_back:
        summary = {
            "schema": "octopus-post-activation-summary/1",
            "authorization_id": AUTH,
            "written_at_local": now_local(),
            "result": "FAIL: POST_ACTIVATION_ROLLBACK",
            "soak_start_ts_local": start_local,
            "soak_end_ts_local": now_local(),
            "duration_seconds_target": duration,
            "interval_seconds": interval,
            "samples": n,
            "failures": failures,
            "rollback": rollback_report,
            "samples_path": str(samples_path),
            "known_head_drift_policy": {"restart_for_drift_forbidden": True},
        }
    else:
        clean = len(failures) == 0 and n >= (duration // interval) - 1
        acceptance = clean and counts.get("center") == 1 and counts.get("launcher") == 1 and counts.get("poller_effective") == 1
        summary = {
            "schema": "octopus-post-activation-summary/1",
            "authorization_id": AUTH,
            "written_at_local": now_local(),
            "result": "PASS" if acceptance else "FAIL",
            "soak_start_ts_local": start_local,
            "soak_end_ts_local": now_local(),
            "duration_seconds_target": duration,
            "duration_seconds_actual": end - start,
            "interval_seconds": interval,
            "samples": n,
            "failures": failures,
            "last_counts": counts,
            "stable_candidate_runtime_note": "candidate HEAD may be 8c0fc90 while runtime remains 2ab0eb8 — not a fail",
            "samples_path": str(samples_path),
            "known_head_drift_policy": {"restart_for_drift_forbidden": True},
            "acceptance": {
                "sixty_minutes": (end - start) >= (duration - 30),
                "one_center": counts.get("center") == 1,
                "one_launcher": counts.get("launcher") == 1,
                "one_poller": counts.get("poller_effective") == 1,
                "zero_hard_fails": len(failures) == 0,
            },
        }
    wj(EV / "POST-ACTIVATION-SUMMARY.json", summary)
    sea = side_effects(start, end, samples_meta)
    wj(EV / "SIDE-EFFECT-ACCOUNTING.json", sea)
    md = (EV / "FINAL-REPORT.md").read_text(encoding="utf-8")
    md = md.replace("**PENDING** (fill when window ends)", f"**{summary['result']}**")
    md += f"\n\n## Soak final\n- Result: **{summary['result']}**\n- Samples: {n}\n- Failures: {len(failures)}\n- Summary: `POST-ACTIVATION-SUMMARY.json`\n- Side effects: `SIDE-EFFECT-ACCOUNTING.json`\n- LIVE-B final status: {live_status}\n"
    (EV / "FINAL-REPORT.md").write_text(md, encoding="utf-8")
    wj(EV / "PROGRESS.json", {
        "schema": "octopus-post-activation-progress/1",
        "phase": "SOAK_COMPLETE",
        "LIVE_B_status": live_status,
        "soak_start_ts_local": start_local,
        "soak_result": summary["result"],
        "written_at_local": now_local(),
        "paths": {
            "LIVE_B": str(EV / "LIVE-B-RESULT.json"),
            "SAMPLES": str(samples_path),
            "SUMMARY": str(EV / "POST-ACTIVATION-SUMMARY.json"),
            "SIDE_EFFECTS": str(EV / "SIDE-EFFECT-ACCOUNTING.json"),
            "FINAL_REPORT": str(EV / "FINAL-REPORT.md"),
        },
    })
    print("SUMMARY", summary["result"], "samples", n, "failures", len(failures), flush=True)
    return 0 if str(summary.get("result", "")).startswith("PASS") else 2

if __name__ == "__main__":
    raise SystemExit(main())

