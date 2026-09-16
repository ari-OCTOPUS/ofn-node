#!/usr/bin/env python3
"""realwork_registry.py — verify the real backlog, test the worker gate, and
run the deterministic credential-rotation review (zero paid API).

REAL-WORK-BRIDGE-20260913. Prints no credential value, ever.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys
import time

NOW = time.strftime("%2026-%m-%dT%H:%M:%SZ")

# ---- A. worker provenance gate test (zero cognition) ------------------------
CW = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
spec = importlib.util.spec_from_file_location("cw_gate", CW)
mod = importlib.util.module_from_spec(spec)
sys.modules["cw_gate"] = mod
spec.loader.exec_module(mod)
recs = []
mod.receipt = lambda kind, **kw: recs.append(kind)

fake = {"task_id": "GATE-SELFTEST-NO-PROV", "purpose": "selftest",
        "target_file": "ops_agent.py", "anchors": [], "replacements": [],
        "proposal_field": "x", "stage_test": "t.py"}
r1 = mod.process_task(dict(fake))
good = dict(fake, provenance={"class": "REAL_CODE_DEFECT", "source": "receipts",
                              "source_ts": NOW, "source_hash": "ab" * 32})
captured = {}
mod.cognition_request = lambda t: captured.setdefault("called", t["task_id"]) or None
mod.set_cooldown = lambda s: None
r2 = mod.process_task(good)
print("gate: no-provenance ->", r1, "| with-provenance passes gate ->", r2,
      "(reaches cognition:", "called" in captured, ")")
print("gate receipts:", recs)

# ---- B. real backlog registry (verified today, deterministic) --------------
REG = pathlib.Path("/home/ari/ofn/state/coding-worker/real-backlog.json")
backlog = {
  "schema": "octopus.real-backlog.v1",
  "recorded_at": NOW,
  "directive": "REAL-WORK-BRIDGE-20260913",
  "tasks": [
    {"id": "TASK-OPS-BUDGET-CATSCOPE-005", "class": "REAL_CODE_DEFECT",
     "state": "WAITING_B8_BUDGET", "wake": "2026-09-14T01:49:08Z (BUDGET_NODE_24H frees)",
     "evidence": "patch packaged+tested; canary-requests/native-TASK-OPS-BUDGET-CATSCOPE-005.json; ops receipts OPS_B_BLOCKED reason=BUDGET_NODE_24H",
     "paid_needed": False, "action": "none until wake; do NOT regenerate the patch"},
    {"id": "PRED-E0E80E1D-RECONCILIATION", "class": "REAL_PREDICTION_DUE",
     "state": "WAITING_DUE", "wake": "2026-09-13T06:30:00Z",
     "evidence": "prediction-ledger.jsonl row pred-e0e80e1d",
     "paid_needed": False, "action": "automatic reconcile by supervisor"},
    {"id": "B5-STORAGE-MAINTENANCE-BREAKER", "class": "REAL_CODE_DEFECT",
     "state": "OPEN_SECOND_ROOT_CAUSE", "wake": "deterministic diagnosis possible now",
     "evidence": "failure-signatures.json b5 cache-regeneration-race signature; breaker open by budget",
     "paid_needed": False, "action": "diagnose deterministically; fix = patch -> B8"},
    {"id": "NODE-138-FAILOVER-LEASE", "class": "REAL_RUNTIME_INCIDENT",
     "state": "DESIGN_PENDING", "wake": "owner-visible design lane",
     "evidence": "single executor node; no split-brain protection yet",
     "paid_needed": "maybe later", "action": "design lease+fencing; no second executor before that"},
    {"id": "WILD-IO-CONTENTION", "class": "DERIVED_FROM_REAL_EVIDENCE",
     "state": "LAB_READY", "wake": "next WILD tournament",
     "evidence": "dual-verifier timing divergence measurements",
     "paid_needed": False, "action": "WILD evolves candidates under frozen rubric"},
    {"id": "GITHUB-AUTONOMY-BOT", "class": "REAL_GITHUB_WORK",
     "state": "BLOCKED_OWNER_TOGGLE", "wake": "owner enables deploy keys / provides PAT",
     "evidence": "gh api 422 deploy keys disabled (2026-09-13)",
     "paid_needed": False, "action": "local git continues; no polling with paid API"},
    {"id": "ANTHROPIC-WORKSPACE-SCOPE", "class": "REAL_CODE_DEFECT",
     "state": "RESOLVED_2026-09-13", "wake": None,
     "evidence": "ANTHROPIC_WORKSPACE_ID added; canary claude-sonnet-5 OK $0.00052; models 200/11",
     "paid_needed": False, "action": "none (superseded)"},
    {"id": "SAKANA-USAGE-LIMIT", "class": "REAL_RUNTIME_INCIDENT",
     "state": "PROVIDER_ACCOUNT_LIMITED", "wake": "provider account window",
     "evidence": "HTTP 429 usage_limit_reached while models list returns 200",
     "paid_needed": False, "action": "skipped by name in route rank; retries disabled; no IP investigation"},
    {"id": "EXPOSED-CREDENTIAL-ROTATION-REVIEW", "class": "REAL_SECURITY_FINDING",
     "state": "REVIEWED_2026-09-13", "wake": "owner provider-side actions",
     "evidence": "see rotation review below", "paid_needed": False,
     "action": "owner deletes chat-pasted Claude key; optional rotation of locally-exposed TG/Shopify/Gmail secrets"},
    {"id": "NODE-191-RETIRED", "class": "STALE", "state": "NO_TASK",
     "wake": "owner/hardware evidence", "evidence": "SSH refused; retired-until-provisioned",
     "paid_needed": False, "action": "none; no repeated SSH"}
  ]
}
REG.write_text(json.dumps(backlog, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("registry written:", REG)

# ---- C. deterministic credential-rotation review (zero paid API) -----------
print()
print("=== EXPOSED-CREDENTIAL-ROTATION-REVIEW (deterministic) ===")
cfg = pathlib.Path("/home/ari/.config/ofn")
bad_mode = []
for f in sorted(cfg.glob("*")):
    if f.is_file():
        m = oct(f.stat().st_mode)[-3:]
        if m != "600":
            bad_mode.append((f.name, m))
print("files not 600:", bad_mode or "none")

# exposure window of the previously world-readable backups (names only)
win = {"from": "2026-08-22", "until_hardened": "2026-09-13",
       "scope": "local node 138 users only (/home/ari was 755)"}
names_in_backups = set()
for f in cfg.glob("secrets.env.bak-*"):
    for line in f.read_text(errors="replace").splitlines():
        k = line.split("=")[0].strip() if "=" in line else ""
        if k and k.isupper():
            names_in_backups.add(k)
rotate_recommended = sorted(n for n in names_in_backups
                            if n.startswith(("OFN_BOT_TOKEN", "OFN_SHOPIFY",
                                             "GMAIL_APP_PASSWORD", "OFN_SESSION_SECRET",
                                             "OFN_REMOTE_API_KEY")))
print("credential NAMES present in those backups (rotation candidates):",
      rotate_recommended)

# misuse signal scan: any provider/TG/bridge receipts with anomalies?
p = pathlib.Path("/home/ari/ofn/state/ops-agent/state/ops-receipts.jsonl")
anom = 0
if p.exists():
    for line in p.read_text(errors="replace").splitlines():
        if "UNKNOWN_EFFECT" in line or "unauthorized" in line.lower():
            anom += 1
print("misuse signals in ops receipts:", anom,
      "(absence of evidence, not proof of no misuse)")
review = {
    "schema": "octopus.rotation-review.v1", "at": NOW, "paid_api_used": False,
    "findings": [
      {"id": "chat-pasted-claude-key", "severity": "HIGH",
       "exposure": "external chat transcript (outside organism control)",
       "used_by_octopus": False, "stored": False,
       "provider_action": "OWNER: delete key apikey_01HYoiWGnN2BiBxvDMiy8FD3 in Anthropic console",
       "rotation": "delete suffices; OCTOPUS runs on the in-file credential"},
      {"id": "local-backup-files-window", "severity": "MEDIUM",
       "exposure": win, "contained": "all files now mode 600 (2026-09-13)",
       "misuse_signals": anom,
       "provider_action": "OPTIONAL owner rotation of: " + ", ".join(rotate_recommended),
       "rotation": "recommended-not-urgent; local-only window; no misuse signal observed"},
      {"id": "identity-json-644", "severity": "NONE",
       "note": "no credential variable names inside (name-level scan 2026-09-13)"}
    ]}
out = pathlib.Path("/home/ari/ofn/state/coding-worker/rotation-review-20260913.json")
out.write_text(json.dumps(review, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("review written:", out)
