#!/usr/bin/env python3
# Resume post-activation soak to complete original 60m window (append-only).
from __future__ import annotations
import json, sys, time, traceback
from pathlib import Path

ROOT = Path(r"F:\backup")
EV = ROOT / "06-EVIDENCE" / "OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
AUTH = "OCTOPUS-OWNER-CANARY-20260822-N1"
sys.path.insert(0, str(EV))
sys.path.insert(0, str(ROOT / "_ops"))
sys.path.insert(0, str(ROOT / "_ops" / "telegram_center"))
sys.path.insert(0, str(ROOT / "_ops" / "tests"))

# Reuse functions from the soak module by importing after path fix
import importlib.util
spec = importlib.util.spec_from_file_location("soak", EV / "_post_activation_soak.py")
soak = importlib.util.module_from_spec(spec)
spec.loader.exec_module(soak)

from _rollout_ops import now_local, sample_once

def wj(path, obj):
    path.write_text(json.dumps(obj, indent=2, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

def main():
    samples_path = EV / "POST-ACTIVATION-SAMPLES.jsonl"
    lines = [ln for ln in samples_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    first = json.loads(lines[0])
    last = json.loads(lines[-1])
    start = float(first["ts_unix"])
    start_local = first.get("ts_local") or now_local()
    duration, interval = 3600, 30
    # rebuild baseline err from first enriched failure_counters if present
    base_err = last.get("failure_counters")  # deltas vs last known; better use first
    base_err = first.get("failure_counters") or last.get("failure_counters")
    n = len(lines)
    samples_meta = [json.loads(ln) for ln in lines]
    failures = []
    rolled_back = False
    rollback_report = None
    last_hb = time.time()
    soak.heartbeat("soak-resume")
    print(f"RESUME n={n} start={start_local} elapsed={time.time()-start:.1f} remaining={duration-(time.time()-start):.1f}", flush=True)

    while True:
        now = time.time()
        if now - start >= duration:
            break
        # next sample index relative to start
        target = start + n * interval
        sleep_for = target - time.time()
        if sleep_for > 0:
            time.sleep(min(sleep_for, interval))
        if time.time() - start >= duration:
            break
        base = sample_once()
        s, _ = soak.enrich(base, base_err)
        with samples_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(s, default=str) + "\n")
        n += 1
        samples_meta.append(s)
        print(f"SOAK {n} ok={s.get('sample_ok')} counts={s.get('counts')} fail={s.get('lease',{}).get('fail_count')} age={s.get('poll_completed_age_s')} reasons={s.get('hard_fail_reasons')}", flush=True)
        if not s.get("sample_ok"):
            failures.append({"n": n, "ts": s.get("ts_local"), "reasons": s.get("hard_fail_reasons"), "criteria": s.get("criteria")})
            if not rolled_back:
                rolled_back = True
                rollback_report = soak.rollback("POST_ACTIVATION_HARD_FAIL:" + ",".join(s.get("hard_fail_reasons") or []), s)
                break
        if time.time() - last_hb >= 600:
            soak.heartbeat("soak-periodic")
            last_hb = time.time()

    end = time.time()
    soak.heartbeat("soak-end")
    last = samples_meta[-1] if samples_meta else {}
    counts = last.get("counts") or {}
    live_b = json.loads((EV / "LIVE-B-RESULT.json").read_text(encoding="utf-8"))
    live_status = live_b.get("status")

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
            "resumed_after_disconnect": True,
            "known_head_drift_policy": {"restart_for_drift_forbidden": True},
        }
    else:
        clean = len(failures) == 0 and n >= (duration // interval) - 1
        acceptance = clean and counts.get("center") == 1 and counts.get("launcher") == 1 and counts.get("poller_effective") == 1 and (end - start) >= (duration - 60)
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
            "resumed_after_disconnect": True,
            "known_head_drift_policy": {"restart_for_drift_forbidden": True},
            "acceptance": {
                "sixty_minutes": (end - start) >= (duration - 60),
                "one_center": counts.get("center") == 1,
                "one_launcher": counts.get("launcher") == 1,
                "one_poller": counts.get("poller_effective") == 1,
                "zero_hard_fails": len(failures) == 0,
            },
        }
    wj(EV / "POST-ACTIVATION-SUMMARY.json", summary)
    sea = soak.side_effects(start, end, samples_meta)
    wj(EV / "SIDE-EFFECT-ACCOUNTING.json", sea)
    # FINAL-REPORT
    if (EV / "FINAL-REPORT.md").exists():
        md = (EV / "FINAL-REPORT.md").read_text(encoding="utf-8")
        md = md.replace("**PENDING** (fill when window ends)", f"**{summary['result']}**")
        if "## Soak final" not in md:
            md += f"\n\n## Soak final\n- Result: **{summary['result']}**\n- Samples: {n}\n- Failures: {len(failures)}\n- Summary: `POST-ACTIVATION-SUMMARY.json`\n- Side effects: `SIDE-EFFECT-ACCOUNTING.json`\n- LIVE-B final status: {live_status}\n- Note: resumed after agent disconnect mid-window; continuous sample file preserved\n"
        else:
            md += f"\n\n### Resume note\nResumed after disconnect; final result **{summary['result']}**, samples={n}, LIVE-B={live_status}\n"
        (EV / "FINAL-REPORT.md").write_text(md, encoding="utf-8")
    wj(EV / "PROGRESS.json", {
        "schema": "octopus-post-activation-progress/1",
        "phase": "SOAK_COMPLETE",
        "LIVE_B_status": live_status,
        "soak_start_ts_local": start_local,
        "soak_result": summary["result"],
        "written_at_local": now_local(),
        "resumed_after_disconnect": True,
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
