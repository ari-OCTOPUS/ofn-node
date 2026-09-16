import json

BASE = r"F:/backup/COUNCIL_REPORTS/2026-08-16-wave-01/A02_runtime_investigator"

# ---------- HEARTBEAT_TRANSCRIPT.jsonl ----------
raw = [json.loads(l) for l in open(BASE + "/raw/heartbeat_obs.jsonl", encoding="utf-8")]
prev_beat = None
with open(BASE + "/HEARTBEAT_TRANSCRIPT.jsonl", "w", encoding="utf-8") as f:
    for r in raw:
        o = r["samples"].get("ORGANISM-STATE.json", {})
        b = o.get("beat")
        rec = {
            "record_type": "sample",
            "observer_ts_local": r["ts"],
            "beat": b,
            "beat_advanced": (b != prev_beat),
            "organism_state_mtime": o.get("mtime"),
            "beat_state_mtime": r["samples"].get("beat-state.json", {}).get("mtime"),
            "arbiter_mtime": r["samples"].get("arbiter-latest.json", {}).get("mtime"),
            "events_jsonl_mtime": r["samples"].get("events.jsonl", {}).get("mtime"),
            "heartbeat_md_size": r["samples"].get("HEARTBEAT.md", {}).get("size"),
            "heartbeat_md_mtime": r["samples"].get("HEARTBEAT.md", {}).get("mtime"),
        }
        if prev_beat is not None and b != prev_beat:
            rec["interpretation"] = "beat advanced while observer made zero writes -> live writer active"
        prev_beat = b
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    f.write(json.dumps({
        "record_type": "summary",
        "observer_ts_local": "2026-08-16T23:59:30",
        "distinct_beats_observed": 3,
        "beat_values": [38511, 38513, 38516],
        "beat_advances": 3,
        "window": "23:54:27-23:59:27 +10:00",
        "observed_cadence_s": [128, 128],
        "expected_cadence_s": 125.02,
        "expected_source": "arbiter-latest.json effective_period_s (consensus of 3 hearts)",
        "zero_observer_writes": True,
    }, ensure_ascii=False) + "\n")
    f.write(json.dumps({
        "record_type": "hourly_heartbeat_line",
        "file": "F:/backup/_memory/HEARTBEAT.md",
        "last_line": "2026-08-16T23:06:44 - organism=ok - month AU$0.74 - suspect_zero_total=0 - healthy",
        "cadence": "hourly (3600s gate, organism.py:1335)",
        "note": "hourly line did not roll during the 5-min window (next due ~00:06:44); prior lines observed at ~60min spacing in file tail",
    }, ensure_ascii=False) + "\n")
print("transcript written")

# ---------- 03_EVIDENCE.jsonl ----------
EV = []

def ev(fid, claim, status, tier, source, lines, command, ts, conf, sev, contra, action):
    EV.append({"finding_id": fid, "claim": claim, "status": status, "evidence_tier": tier,
               "source_path": source, "line_range": lines, "command": command,
               "observed_timestamp": ts, "confidence": conf, "severity": sev,
               "contradiction_status": contra, "recommended_next_action": action})

TS = "2026-08-16T23:44:00..23:59:30+10:00"

ev("F-01", "Live OCTOPUS service stack: organism.py, cortex.py, live/server.py, telegram_center/center.py, miniapp_gateway.py, board_cp/server.py all running", "VERIFIED_LIVE", "T0",
   "raw/processes_snapshot1.json; raw/netstat_snapshot1.txt", "-", "powershell Get-CimInstance Win32_Process; netstat -ano", TS, 0.99, "INFO", "none", "none - baseline established")
ev("F-02", "12 scheduled tasks auto-sustain the stack (watchdogs every 5-10 min); 'OCTOPUS Observatory Hourly' executes from Desktop OUTSIDE the repo", "VERIFIED_LIVE", "T0",
   "raw/tasks.ps1 output", "-", "Get-ScheduledTask + Get-ScheduledTaskInfo", TS, 0.97, "MEDIUM", "none", "owner: move Desktop control-plane code into repo")
ev("F-03", "Named cloudflared tunnel exposes miniapp gateway publicly at https://app.master-painting.com -> 127.0.0.1:8774; tunnel PID file matches live PID 17332", "VERIFIED_LIVE", "T0",
   "_ops/state/telegram/miniapp-url.json; process 17332", "-", "netstat -ano; process snapshot", TS, 0.97, "MEDIUM", "none", "verify Telegram-side registration + initData HMAC gate (A03)")
ev("F-04", "board_cp binds 0.0.0.0:8801 (LAN-exposed) - mitigated: TLS self-signed + Bearer + only /pull,/ack + fail-closed 503 when flag/Gate0 off", "VERIFIED_LIVE", "T0",
   "_ops/board_cp/server.py", "1-40", "netstat -ano (0.0.0.0:8801 PID 23464); file read", TS, 0.90, "MEDIUM", "none", "confirm board clients pin fingerprint; consider loopback+bridge")
ev("F-05", "beat is computed live: chrono Pacemaker resumes from chrono.db and increments per beat; observed 38511->38513->38516 with zero observer writes", "VERIFIED_LIVE", "T0+T2",
   "_ops/chrono.py", "1241,1273,1419-1422,1489", "heartbeat sampler (read-only, 11x30s)", TS, 0.97, "INFO", "none", "none")
ev("F-06", "arbiter state is computed live per beat (3-heart consensus, brake-dominates); advisory_only=true; effective period 125.02s vs base 60s", "VERIFIED_LIVE", "T0+T2",
   "_ops/state/pulse/arbiter-latest.json; _ops/heart/pulse_arbiter.py", "405-468", "file read + sampler", TS, 0.96, "INFO", "none", "document that arbiter is advisory, not enforcing")
ev("F-07", "identity_health computed live per math_control spine beat (0.542; learner .6 / earner 0 / guardian .675 / creator 1.0 / organism .435); may_authorize=false", "VERIFIED_LIVE", "T0+T2",
   "_ops/state/pulse/math-control-latest.json; _ops/math_control/spine.py", "157-181,717", "file read (fresh same-beat values)", TS, 0.93, "INFO", "none", "none")
ev("F-08", "coherence computed on demand behind OCTOPUS_WIRE_COHERENCE=1; feeds identity equations; no standalone fresh state file", "VERIFIED_CODE_ONLY", "T2",
   "_ops/identity_equations.py", "337-353,393-401", "flags-loaded-organism.json + code read", TS, 0.70, "LOW", "none", "surface coherence value in a state file for observability")
ev("F-09", "runtime_state, readiness_state, bus_state, acquisition_state, safety_state: no such fields exist in live code", "NOT_FOUND", "T2",
   "_ops (grep)", "-", "grep -r across _ops/4d_system/OCTOPUS", TS, 0.95, "INFO", "none", "map these terms to actual fields (wiring, halted, epoch_mode) or drop from claims")
ev("F-10", "Sensorium has no implementation anywhere in _ops or 4d_system", "NOT_FOUND", "T2",
   "_ops; 4d_system", "-", "grep -ri sensorium", TS, 0.95, "MEDIUM", "CONTRADICTS 'Sensorium is active'", "remove from claims or implement")
ev("F-11", "Physical legs: no hardware actuation path exists; 'legs' are software business legs; all leg beats propose-only (propose_only: true, empty HANDLERS registry)", "VERIFIED_CODE_ONLY", "T2",
   "_ops/wiring.py; _ops/cortex/approval_actuator.py", "637-677,1144-1159; 46-48", "code audit (read-only)", TS, 0.90, "INFO", "none", "none")
ev("F-12", "Propose-only nuance: IMPORTANT class always owner-gated, but live flags arm bounded automatic actions: OCTOPUS_AUTONOMY_FREE=1, OCTOPUS_AUTONOMY_GRANT=1, OCTOPUS_CODE_AUTOAPPLY_LOWRISK=1, OCTOPUS_LEAD_OUTBOUND=1 (cap 100/day); boot log shows code-apply armed but active()=False", "VERIFIED_LIVE", "T0",
   "_ops/state/flags-loaded-organism.json; _memory/HEARTBEAT.md", "-; 12:52:47 line", "file reads", TS, 0.95, "MEDIUM", "PARTIAL_CONTRADICTION of absolute propose-only claim", "owner: reconcile flags with narrative")
ev("F-13", "Money locked (live): money_gate fail-closed >AU$20 needs approval; default channel NotWiredStub=deny-all; month spend AU$0.74; cardiac budget 540/2000 units; OCTOPUS_ENFORCE_MONEY_FSM=1", "VERIFIED_LIVE", "T0+T2",
   "_ops/budget/money_gate.py; ORGANISM-STATE.json month/cardiac", "35-55", "code audit + live state read", TS, 0.90, "INFO", "none", "none")
ev("F-14", "OCTOPUS_SPEND_CAP_USD=200 window EXPIRED (UNTIL=2026-08-13) - temporary cap lapsed; permanent gates remain", "VERIFIED_LIVE", "T0",
   "_ops/state/flags-loaded-organism.json", "-", "file read", TS, 0.85, "LOW", "none", "owner: confirm intended post-window state")
ev("F-15", "octopus-v3 HARD_NO_GO/INTENT/budget overlay exists but WIRED=False and never imported by organism/wiring - inert in live runtime", "DOCUMENTED_NOT_IMPLEMENTED", "T2+T3",
   "_ops/octopus_v3/__init__.py; gate.py; budget.py; profile.py", "__init__:7-12", "grep import octopus_v3 (no hits) + code read", TS, 0.97, "HIGH", "CONTRADICTS 'HARD_NO_GO enforced' if so claimed", "owner vote to wire, or mark docs as future-work")
ev("F-16", "Mutual-veto dual-brain governance: full logic exists but OCTOPUS_WIRE_DUAL_VETO absent from live flags -> disabled in live runtime", "PRESENT_NOT_WIRED", "T0+T2",
   "_ops/control_plane/dual_brain.py; flags-loaded-organism.json", "110-117", "flags snapshot grep (DUAL_VETO -> False)", TS, 0.95, "HIGH", "CONTRADICTS 'governance is mutual veto'", "owner decision required")
ev("F-17", "Policy Gate is fail-closed in code (deny-on-exception/kill/unknown) and wired; but adr-033 event stream silent since 2026-08-13 - no recent live exercise observed", "VERIFIED_CODE_ONLY", "T2+T3",
   "_ops/policy/policy_gate.py; _ops/state/adr-033/events/", "102-140", "code audit + state dir mtimes", TS, 0.85, "MEDIUM", "none", "add canary probe through policy gate on a schedule")
ev("F-18", "Viability Loop: no code anywhere", "NOT_FOUND", "T2",
   "_ops;4d_system;OCTOPUS;03-GATES;04-SYSTEMS", "-", "grep -r viability", TS, 0.95, "MEDIUM", "CONTRADICTS 'runtime-enforced'", "implement or remove claim")
ev("F-19", "Kill switches checked per-loop in all four processes (organism.py:532, cortex.py:842, center.py:592-606) and at launcher boot; OCTOPUS_WIRE_KILL_SEAM=1 live", "VERIFIED_CODE_ONLY", "T0+T2",
   "_ops/organism.py; _ops/cortex/cortex.py; _ops/telegram_center/center.py; _ops/budget/opslib.py", "532;842;592-606;355-407", "code audit + flags snapshot", TS, 0.90, "INFO", "none", "enforcement provable only by exercised rejection (tests)")
ev("F-20", "OFF-heartbeat mechanism wired into main loop (every 10 beats) BUT zero dormant modules exist now (all module flags on) -> no OFF events emitted; events.jsonl last write 23:11", "VERIFIED_CODE_ONLY", "T2+T0",
   "_ops/off_heartbeat.py; _ops/organism.py; events.jsonl tail", "23-56;549-557", "code audit + events tail scan (0 module.heartbeat lines)", TS, 0.90, "LOW", "none", "test in sandbox with one flag off")
ev("F-21", "Event bus is file/in-process (events.jsonl + unified_bus); no broker process; stream sparse (45+ min silent while organism healthy)", "VERIFIED_LIVE", "T0",
   "_ops/state/events.jsonl; _ops/unified_bus.py", "-", "mtime + tail + process map (no broker)", TS, 0.90, "LOW", "none", "add bus-last-event-age readiness signal")
ev("F-22", "Config precedence (live-proven): OCTOPUS-flags.cmd env > pre-set env > .env (fills only empty, env_loader.py:33-56) > auto-knobs.json (fills only empty, bounded, auto_approve.py:395-408) > hardcoded defaults; 335 flags loaded, shortfall 0, secrets auto-redacted", "VERIFIED_LIVE", "T0+T2",
   "_ops/state/flags-loaded-organism.json; _ops/budget/env_loader.py; RUN-ORGANISM.bat", "-;33-56;26", "flags snapshot + code read", TS, 0.95, "INFO", "none", "none")
ev("F-23", "Version drift: live processes booted 12:53-16:43; organism.py/wiring.py edited 23:01; HEAD 028fe81 committed 23:27 -> running code predates current tree; lazy imports could mix versions", "VERIFIED_LIVE", "T0",
   "process CreationDates; file mtimes; git show", "-", "process snapshot + stat + git", TS, 0.95, "MEDIUM", "none", "record boot commit-hash in ORGANISM-STATE; schedule restart windows")
ev("F-24", "Clock: TZ AUS Eastern +10; NO time.monotonic anywhere; beat loop on time.time() wall clock; human logs naive local; math-control-latest.json writes LOCAL time with 'Z' suffix (10h mislabel); board-status uses explicit +10:00; miniapp-url/state_guard use correct UTC", "VERIFIED_LIVE", "T0+T2",
   "_ops/state/pulse/math-control-latest.json; _ops/organism.py; _ops/budget/opslib.py; _ops/chrono.py", "540;175;93-114", "grep monotonic (0 hits); file ts comparisons", TS, 0.95, "MEDIUM", "none", "fix Z mislabel; adopt monotonic for scheduling")
ev("F-25", "No zombies, no duplicate listeners, no stale PID files: launcher chains have dead ancestors (normal); launchers self-guard against double-start; miniapp/tg-center pid fields match live PIDs; no *.pid files found", "VERIFIED_LIVE", "T0",
   "raw/processes_snapshot1.json; _ops/state", "-", "python genealogy analysis + find *.pid", TS, 0.95, "INFO", "none", "none")
ev("F-26", "Python env: system-wide Python 3.13.7 (C:/Program Files/Python313); no venv for any service; stdlib http.server based", "VERIFIED_LIVE", "T0",
   "process ExecutablePaths; python --version", "-", "process snapshot; python -c", TS, 0.97, "LOW", "none", "consider per-service venv for dependency isolation")
ev("F-27", "Local brain backend live: ollama serve (11434) + llama-server (1495, --offline, ctx 4096) started 23:41; external provider keys present but unused by this audit", "VERIFIED_LIVE", "T0",
   "processes 20192/9796", "-", "process snapshot", TS, 0.95, "INFO", "none", "none")
ev("F-28", "_octopus legacy control-plane mostly stale (status since 2026-07-18) but approvals.json/audit.log STILL active (latest approval.add_pending 12:35:57 today, risk=medium)", "VERIFIED_LIVE", "T0",
   "_octopus/state/approvals.json; _octopus/logs/audit.log", "tail", "tail audit.log", TS, 0.90, "MEDIUM", "none", "A03: determine authoritative approval ledger")
ev("F-29", "Three independent beat counters coexist: chrono beat 38511 (organism), beat-state 4163 (heart-card organs=4), board-status beat 601 (ofn bridge, last 22:57)", "VERIFIED_LIVE", "T0",
   "ORGANISM-STATE.json; pulse/beat-state.json; board-status.txt", "-", "file reads", TS, 0.95, "LOW", "naming collision risk", "namespace counters in dashboards")
ev("F-30", "Telegram channel live (long-poll T-8, channel-status 23:51, tg-center pulse 23:54:49); autonomous notification sends are NOT per-message approval-gated (audit-logged, STOP-gated)", "VERIFIED_LIVE", "T0+T2",
   "_ops/state/channel-status.json; pulse/tg-center.json; _ops/telegram_center/tg_api.py", "489-534", "file reads + code audit", TS, 0.88, "LOW", "none", "none")

with open(BASE + "/03_EVIDENCE.jsonl", "w", encoding="utf-8") as f:
    for e in EV:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print("evidence written:", len(EV))

# ---------- 09_MACHINE_SUMMARY.json ----------
summary = {
    "agent_id": "A02_runtime_investigator",
    "wave": "2026-08-16-wave-01",
    "mode": "READ_ONLY",
    "observation_window_local": "2026-08-16T23:44:00 -> 23:59:30 +10:00 (AUS Eastern)",
    "head_commit": "028fe8149515415852b2a3b1feaaff44681e5bf8 (2026-08-16T23:27:30+10:00)",
    "live_processes": [
        {"pid": 29028, "name": "organism.py", "ports": ["127.0.0.1:8771", "127.0.0.1:8777"], "started": "2026-08-16T12:53:10", "boot_config": "_ops/OCTOPUS-flags.cmd + .env via env_loader"},
        {"pid": 11144, "name": "cortex/cortex.py", "ports": ["127.0.0.1:8772"], "started": "2026-08-16T13:01:53"},
        {"pid": 7852, "name": "live/server.py", "ports": ["127.0.0.1:8773"], "started": "2026-08-16T16:36:56"},
        {"pid": 11724, "name": "telegram_center/center.py", "ports": ["127.0.0.1:8776"], "started": "2026-08-16T16:37:33"},
        {"pid": 19076, "name": "telegram_center/miniapp_gateway.py", "ports": ["127.0.0.1:8774"], "started": "2026-08-16T16:43:38", "exposed_via": "cloudflared named tunnel https://app.master-painting.com"},
        {"pid": 23464, "name": "board_cp/server.py", "ports": ["0.0.0.0:8801 TLS"], "started": "2026-08-16T16:42:50"},
        {"pid": 17332, "name": "cloudflared (named tunnel)", "ports": ["127.0.0.1:20241 metrics"], "started": "2026-08-16T06:58:06"},
        {"pid": 20192, "name": "ollama serve", "ports": ["127.0.0.1:11434"]},
        {"pid": 9796, "name": "llama-server --offline", "ports": ["127.0.0.1:1495"], "started": "2026-08-16T23:41:29"}
    ],
    "scheduled_tasks_octopus_related": 12,
    "heartbeat_observation": {"distinct_beats": [38511, 38513, 38516], "advances": 3, "cadence_s_observed": 128, "cadence_s_expected": 125.02, "observer_writes": 0},
    "value_classification": {
        "beat": "live (chrono Pacemaker, resumed from chrono.db)",
        "coherence": "computed-on-demand behind OCTOPUS_WIRE_COHERENCE=1 (no standalone state file)",
        "identity_health": "live per math_control spine beat (0.542)",
        "arbiter_state": "live per beat, advisory_only=true, 3-heart consensus 125.02s",
        "runtime_state": "NOT_FOUND", "readiness_state": "NOT_FOUND", "bus_state": "NOT_FOUND",
        "acquisition_state": "NOT_FOUND", "safety_state": "NOT_FOUND"
    },
    "key_statuses": {
        "live_stack": "VERIFIED_LIVE",
        "sensorium_active": "NOT_FOUND (no code)",
        "legs_unauthorized": "VERIFIED_CODE_ONLY (no hardware path; propose-only)",
        "propose_only_absolute": "PARTIALLY CONTRADICTED (AUTONOMY_FREE/GRANT/CODE_AUTOAPPLY_LOWRISK/LEAD_OUTBOUND armed)",
        "money_locked": "VERIFIED_LIVE (money_gate fail-closed; spend AU$0.74/mo)",
        "destructive_disabled_HARD_NO_GO": "PRESENT_NOT_WIRED (octopus_v3 WIRED=False)",
        "mutual_veto": "PRESENT_NOT_WIRED (OCTOPUS_WIRE_DUAL_VETO off)",
        "policy_gate": "VERIFIED_CODE_ONLY (events stale since 08-13)",
        "viability_loop": "NOT_FOUND",
        "off_heartbeats": "VERIFIED_CODE_ONLY (mechanism on; zero dormant modules today)",
        "event_bus": "VERIFIED_LIVE file-based (sparse; 45min silent)",
        "kill_switches": "VERIFIED_CODE_ONLY per-loop checks; flag OCTOPUS_WIRE_KILL_SEAM=1"
    },
    "top_risks": [
        "governance overlay unwired while narrative claims enforcement (F-15, F-16, F-18)",
        "public tunnel + 0.0.0.0:8801 exposure (F-03, F-04)",
        "runtime runs pre-edit code vs HEAD (F-23)",
        "scheduled task executes from Desktop outside repo (F-02)",
        "autonomy flags armed beyond propose-only narrative (F-12)"
    ],
    "special_question_answer": "Runtime evidence can establish PRESENCE (process, listener, fresh state writes) and ACTIVITY (values changing per beat); it CANNOT by itself establish ENFORCEMENT. Enforcement is only provable by observing a violating action being rejected (requires exercising the gate - out of scope for read-only) or by tests (T1). In this wave, runtime evidence affirmatively shows ABSENCE of wiring for two claimed enforcers (dual-brain veto, octopus_v3 HARD_NO_GO).",
    "verdict": "READY_FOR_NEXT_WAVE"
}
with open(BASE + "/09_MACHINE_SUMMARY.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("machine summary written")
