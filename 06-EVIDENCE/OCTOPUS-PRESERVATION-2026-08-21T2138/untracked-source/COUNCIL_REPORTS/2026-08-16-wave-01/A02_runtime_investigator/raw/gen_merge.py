import json

BASE = r"F:/backup/COUNCIL_REPORTS/2026-08-16-wave-01/A02_runtime_investigator"

# ---- Rebuild merged 03_EVIDENCE.jsonl: parallel-observer findings (R-*) + primary findings (F-*) ----
R = []
def r(rid, claim, status, tier, conf, sev, evidence, contra, nxt):
    R.append({"finding_id": rid, "observer": "A02-parallel (window 23:48-23:54+10:00)", "claim": claim,
              "status": status, "evidence_tier": tier, "source_path": "see 02_FINDINGS.md " + rid,
              "line_range": "-", "command": "read-only per 01_SCOPE_AND_METHOD.md",
              "observed_timestamp": "2026-08-16T23:48:00..23:54:00+10:00", "confidence": conf,
              "severity": sev, "contradiction_status": contra, "recommended_next_action": nxt,
              "evidence": evidence})

r("R-001", "OCTOPUS runs locally as a live python organism (6 services + ollama + cloudflared)", "VERIFIED_LIVE", "T0", 1.0, "INFO",
  "PID 29028 organism.py since 12:53:10 matches ORGANISM-STATE.started; 5 more python services", "none", "none")
r("R-002", "Beat loop alive, non-regressing, >=3 cycles (38507->38509->38511 at ~65s)", "VERIFIED_LIVE", "T0", 0.95, "INFO",
  "chrono.db heartbeat 38509 rows, checkpoint 38508 with per-beat ledger_hash; WAL mtime advanced", "none", "longer soak for A15")
r("R-003", "Brains are 4d_system and NBB-CP", "CONTRADICTED (runtime)", "T0+T2", 0.85, "MEDIUM",
  "No 4d_system process; live brains = organism loop + cortex; brain_core SHADOW matched=0 missing_old=4167; CURRENT-TRUTH itself says 4d not connected", "contradicts project claim (C-1)", "A09 canonical brain inventory")
r("R-004", "Telegram cockpit surface live", "VERIFIED_LIVE", "T0", 0.95, "INFO",
  "center.py PID 11724; channel-status telegram live=true long-poll(T-8) 23:51:09; 3 bot token key names in .env (values unread); tunnel to 8774", "none", "A04 audits gateway auth wall")
r("R-005", "identity_health reported 0.572 in docs", "STALE", "T0+T2", 0.95, "LOW",
  "Live value 0.542 recomputed each math-control tick (spine.py:157-181 via identity_equations.evaluate); 0.572 is outdated lore", "contradicts claim", "regenerate docs from state")
r("R-006", "Ledger live and bitemporal", "VERIFIED_LIVE (liveness) / NOT_FOUND (bitemporality)", "T0", 0.9, "LOW",
  "chrono.db tables heartbeat/checkpoint/leg_clock/experience_meter/duration_marker/metabolic_age/gated_effect; no valid-from/to/supersedes columns; gated_effect has 0 rows ever", "bitemporal documented vs schema absent", "A03/A12 implement or verify contract")
r("R-007", "External actions are propose-only", "VERIFIED_CODE_ONLY (structural) with caveat", "T2", 0.85, "MEDIUM",
  "propose_only:True is a hardcoded reporting label per leg (wiring.py:454,594,677,1105,3386,3742,4040); real blocking structural: executor.py:35 EXECUTABLE={A0,A1}; tg_api wired() guard; outbound_https NOT_WIRED", "label-vs-mechanism (C-3)", "A05 convert to enforced gate")
r("R-008", "Money locked", "VERIFIED_CODE_ONLY", "T2", 0.9, "INFO",
  "money_gate.py:48 NotWiredStub deny >AU$20; outbound_https.py:176 NOT_WIRED; no payment API call sites; baseline.py:159-175 fails on money-code fingerprint change", "none", "none")
r("R-009", "A2 bounded automatic; A4 owner approval", "CONTRADICTED (safer than claimed)", "T2+T0", 0.9, "LOW",
  "action_bridge/classifier.py:176-184: A0/A1 ALLOW, A2 BLOCK (VQ-SELFGOAL-002), A3 OWNER_GATE, A4/A5 BLOCK, A6 REJECT; executor has no A2+ paths; A1 defaults dry_run; bridge flag ON", "contradicts claim (C-6)", "governance decision whether A2 stays blocked")
r("R-010", "Policy Gate runtime-enforced", "DOCUMENTED_NOT_IMPLEMENTED (as universal chokepoint) / VERIFIED_CODE_ONLY (narrow)", "T2", 0.9, "MEDIUM",
  "policy_gate.py fail-closed but only ONE live call site (wiring.py:2057-2094 request_protective_halt); octopus_v3 overlay WIRED=False not imported", "overstated (C-2)", "A05 design; wave-2 prototype")
r("R-011", "Clock basis", "VERIFIED_LIVE", "T0+T2", 0.9, "INFO",
  "state ts local wall clock; hlc epoch ms; epoch_mode allostatic (pressure-driven); host date consistent within seconds", "none", "none")
r("R-012", "coherence 0.859 / arbiter GREEN are live-generated", "VERIFIED_LIVE", "T0", 0.85, "INFO",
  "CURRENT-TRUTH auto-block regenerated 13:41:27Z by truth_sync_tick (cortex.py:559-623, 30-min cooldown, OCTOPUS_WIRE_TRUTH_SYNC=1); arbiter GREEN consensus in live state", "none", "note 30-min lag")
r("R-013", "channel-status panel_8790 live", "STALE", "T0", 0.9, "LOW",
  "No 8790 listener (nor 8770); live/server.py:34 references dashboard=8770; file's writer_note admits only telegram entry is refreshed", "contradicts state file (C-4)", "refresh or tombstone dashboard entries")
r("R-014", "Public exposure surfaces active (tunnel + 0.0.0.0:8801)", "VERIFIED_LIVE", "T0", 0.95, "MEDIUM",
  "cloudflared octopus-miniapp -> 8774 since 06:58 (initData HMAC wall code-verified); board_cp TLS 0.0.0.0:8801 Bearer + self-signed pinning", "none", "carried to A04")
r("R-015", "frozen:true while beats continue", "VERIFIED_LIVE", "T0+T2", 0.8, "LOW",
  "state frozen=true halted=null stop_organism=false beat advancing; opslib.frozen() checks FREEZE_FLAG; beat_scheduler blocks ACT/LEARN only under HALT", "none (naming hazard)", "document semantics")
r("R-016", "Config provenance incl. secrets hygiene", "VERIFIED_LIVE", "T0+T2", 0.9, "LOW",
  "process env > F:/backup/.env (17 key names; values unread) > _ops/OCTOPUS.env + OCTOPUS-flags.cmd setdefault (board_cp/server.py:36-56); OCTOPUS_WIRE_ACTUATOR=1 flags.cmd:1114; .env.bak-20260810 stale credential copy at root", "none", "purge .env.bak; confirm gitignore")
r("R-017", "brain_core SHADOW comparator never matched", "VERIFIED_LIVE", "T0", 0.9, "LOW",
  "compared=4167 matched=0 missing_old=4167 over 348826s soak; CURRENT-TRUTH: do not promote", "none", "fix old-side producer")
r("R-018", "Life-currency budgets live", "VERIFIED_LIVE", "T0", 0.9, "INFO",
  "cardiac budget spent 538/2000 remaining 1462 depleted=false (2026-08-16); cardiac-budget.json mtime advanced during session", "none", "none")
r("R-019", "proposals_effected=42 vs gated_effect 0 rows", "CONTRADICTED (internal bookkeeping)", "T0", 0.8, "LOW",
  "proposal_metrics delivered=105 effected=42, proposals_fake_delivered=10 self-labeled; chrono.db gated_effect 0 rows; effects are internal state writes", "contradicts metric implication (C-5)", "separate internal vs gated-external counters")
r("R-020", "Git/runtime consistency (HEAD fields)", "VERIFIED_LIVE", "T0", 0.9, "INFO",
  "CURRENT-TRUTH auto-block HEAD 028fe81 == git rev-parse HEAD; 220 dirty files mostly runtime state", "none", "pair with boot-hash recommendation (F-23)")

F = [json.loads(l) for l in open(BASE + "/03_EVIDENCE.jsonl", encoding="utf-8")]
for e in F:
    e["observer"] = "A02-primary (window 23:44-23:59+10:00)"

# reconcile F-12 with R-007/R-009 in the evidence record itself
for e in F:
    if e["finding_id"] == "F-12":
        e["contradiction_status"] = "PARTIAL - flags arm internal free-tier automation; structural executor limits actions to A0/A1 (see R-009); absolute propose-only claim remains misleading"
        e["recommended_next_action"] = "owner: reconcile flags with narrative; keep A2 BLOCK or document intent"

with open(BASE + "/03_EVIDENCE.jsonl", "w", encoding="utf-8") as f:
    for e in R + F:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print("merged evidence lines:", len(R) + len(F))

# ---- Append reconciliation records to HEARTBEAT_TRANSCRIPT.jsonl ----
with open(BASE + "/HEARTBEAT_TRANSCRIPT.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({
        "record_type": "cross-observer-reconciliation", "observer_ts_local": "2026-08-17T00:10:00",
        "note": "parallel observer measured ~65s beat cadence 23:49-23:53 (38507->38509->38511); this observer measured ~128s 23:53-23:57 (38511->38513->38516). Both windows are real: organism tick cadence is variable. arbiter.effective_period_s (~125s) describes the heart-consensus period, NOT the organism beat loop - naming trap (C-7)."
    }, ensure_ascii=False) + "\n")
print("transcript reconciliation appended")

# ---- Rebuild merged 09_MACHINE_SUMMARY.json ----
summary = json.load(open(BASE + "/09_MACHINE_SUMMARY.json", encoding="utf-8"))
summary["dual_observer_note"] = "Two independent read-only A02 instances observed the same host (windows 23:48-23:54 and 23:44-23:59 +10:00). Findings merged: R-001..R-020 (parallel) + F-01..F-30 (primary). Evidence JSONL carries observer tags."
summary["key_statuses"].update({
    "brains_4d_nbb": "CONTRADICTED at runtime (R-003): live brains are organism-loop + cortex; brain_core SHADOW matched=0",
    "action_classes": "SAFER THAN CLAIMED (R-009): A2/A4/A5 BLOCK, A6 REJECT; only A0/A1 executable; A1 defaults dry_run",
    "propose_only": "STRUCTURAL, not gated (R-007): executor has no A2+ paths; propose_only label is reporting-only; PLUS autonomy flags armed (F-12)",
    "policy_gate_scope": "ONE live call site - protective halt only (R-010); not a universal chokepoint",
    "ledger": "live per beat with per-beat ledger_hash (R-002/R-006); bitemporality NOT FOUND in schema; gated_effect 0 rows (A03 scope)",
    "identity_health_docs": "docs value 0.572 STALE; live 0.542 (R-005, F-07)",
    "dashboard_claims": "panel_8790 STALE - no listener (R-013)",
    "truth_sync": "VERIFIED_LIVE - CURRENT-TRUTH auto-block regenerates every 30 min, HEAD matches git (R-012/R-020)",
    "secrets_hygiene": ".env.bak-20260810 stale credential copy at repo root (R-016)"
})
summary["top_risks"] = [
    "safety is structural (absence of executor paths), not gate-enforced - new effector code silently inherits allowed (R-007/R-010)",
    "governance overlay unwired while narrative claims enforcement (F-15, F-16, F-18)",
    "public tunnel + 0.0.0.0:8801 exposure (F-03, F-04, R-014)",
    "runtime runs pre-edit code vs HEAD; no boot-hash recorded (F-23)",
    "scheduled task executes from Desktop outside repo (F-02)",
    "autonomy flags armed beyond propose-only narrative (F-12); A2 stays BLOCK only by classifier vote (R-009)",
    "stale-secret hygiene: .env.bak at root (R-016)",
    "no time.monotonic + local-time-with-Z bug in math-control (F-24)"
]
summary["verdict"] = "READY_FOR_NEXT_WAVE"
with open(BASE + "/09_MACHINE_SUMMARY.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("machine summary merged")
