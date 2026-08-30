# FILESYSTEM TREE — F:/backup (filtered)

Excluded: .git internals, __pycache__, node_modules, .pytest_cache, egg-info, secrets,
build artifacts, zips, model weights, media. Depth-limited to significant levels.
Generated 2026-08-16 by A01 (read-only).

```
F:/backup/  [git: equip/g10-cognition-20260816 @ 028fe81, dirty 219]
├── .claude/worktrees/            5 active agent worktrees (see REPOSITORY_STATE.json)
├── 00 - Inbox/                   daily notes, MOCs, megaprompts, discovery reports
├── 00-INDEX.md                   vault master index
├── 01 - Dashboard/               HANDOFF.md, Home.md
├── 01-TRUTH/                     STATE snapshots (nightly truth files)
├── 02 - Life OS/                 personal OS docs
├── 02-DECISIONS/                 decision records
├── 03 - Projects/                Accounting, Chord, Crypto-etoro, Lead-نقاشی, Mining,
│   │                             NBB-Control-Plane (src/nbb_cp + history bundle),
│   │                             OFN-Board, WLOS, Ziman Gallery, research-spec-compiler
├── 03-GATES/                     gate records
├── 04 - Architect System/        architect agent system (PROJECT.md, exports)
├── 04-SYSTEMS/                   systems docs
├── 05 - Agents/                  agent definitions
├── 05-BUSINESSES/                business docs
├── 06 - Architecture Maps/       maps
├── 06-EVIDENCE/                  evidence packs (POISONING-WATCH-4d.md etc.)
├── 07 - Knowledge/               _doctor-research, genome-system/ [NESTED GIT REPO,
│   │                             ledger/ledger.jsonl 11444 records LIVE], شناسایی-اختاپوس/
├── 07-HANDOFF/                   handoff docs
├── 08 - Assets/  08-PLANS/  09 - People/  09-DESIGN/
├── 10 - Telegram processing/     telegram artifacts
├── 4D-Vault/                     reference markdown for 4d_system RAG
├── 4d_system/                    [STANDALONE RESEARCH BRAIN — 709 py]
│   ├── run.py                    self-test + streamlit entry
│   ├── brain/ (38py: automation, autoloop, self_code, self_evolve, telegram_bot, guardrails…)
│   ├── src/nbb_cp/               [DIVERGENT COPY #2 of NBB-CP kernel+adapters]
│   ├── nbb-cp-kre/               read-only vault link-prediction module (write-guarded)
│   ├── control_plane/ (approvals, killswitch, policy ladder [pure], registry, supervisor)
│   ├── councils/ + councils_real.py, agents/, core/, data/, llm/, memory/, ui/, tests/ (70py)
│   ├── start.bat                 [STALE → Desktop path that does not exist]
│   └── MANIFEST.yaml             self-declares: NOT wired to Octopus projects
├── 99-ARCHIVE/  _Archive/ (orphaned worktrees)  _Duplicates/  _archive-binaries/
├── COUNCIL_REPORTS/2026-08-16-wave-01/  council output (this report; only legal write target)
├── OCTOPUS/                      [STATIC VIZ: 3D HTML dashboards, 10 worlds, admin-telegram]
├── OCTOPUS-DOCTOR/               doctor knowledge base (FA indices/scans/findings) + doctor/
├── OCTOPUS-PRIME/phase-0/        early phase docs
├── PRE-0/                        governance: CONSTITUTION.md, governance.py, risk ladder
├── _memory/                      EXPERIENCE-LEDGER.md, HEARTBEAT.md
├── _octopus/                     [STATE STORE: config/logs/manifests/quarantine/queue/reports/state]
├── _ops/                         [LIVE ORGANISM RUNTIME — 1542 py, ~60 subsystem dirs]
│   ├── organism.py               ★ main loop (live PID 29028, port 8771)
│   ├── wiring.py (4347 ln)       ★ composition root
│   ├── budget/                   opslib, money_gate, organ_gate, governor(_epoch), approvals,
│   │                             FREEZE.flag [LIVE INCIDENT], budgets.yaml, telemetry
│   ├── cortex/                   cortex.py (live), registry.py, improve.py, model_router
│   ├── live/                     server.py (live 8773)
│   ├── telegram_center/          center.py (live) + 60 files: actions, approvals, miniapp/
│   ├── board_cp/                 server.py (live), service/queue/schema/config
│   ├── control_plane/            dual_brain.py (mutual veto), supervisor, collector
│   ├── policy/                   policy_gate.py (ADR-033), talk_gate.py
│   ├── octopus_v3/               P0 overlay: gate/kill/ledger/lease/taint/budget [WIRED=False]
│   ├── heart/                    control_law, pulse_arbiter, work_pump, sim_heart, fuel_meter
│   ├── neural/                   hebbian, bcm, consolidation, latent_space, nociceptor, pain
│   ├── legs/                     80+ business-leg modules (lead, ziman, mining, crypto,
│   │                             cartographer, pocketsmith, xero, austender…)
│   ├── spine/ outcomes/ epistemics/ spectral/ chord/ chrono_rhythm/ identity/ memory/
│   ├── governance-ish: owner_console/, owner_cockpit/, observatory/, runtime/, registry/
│   ├── tests/ (large) + harness; state/ (LIVE state files); deploy/, infra/, scripts/
│   ├── RUN-*.bat, RESTART-*.ps1, *-watchdog.ps1, OCTOPUS-flags.cmd
│   └── ACTIVATION-*.flag (~14), STOP-* (none active except cleared markers)
├── architecture/                 registries: capabilities, hypotheses, signals (+json schema), observatory allowlist
├── continuity/ docs/             docs
├── nervous-system/               dashboard data extractors (extract_*.py) + specs
├── octopus-bridge/octopus_bridge/ bridge package
├── agent-prompts/                prompt library
├── _ops-state-adjacent: _build/, _portable-build/, _zip-verify/
├── .env [NOT READ — secrets], .env.bak, .mcp.json, CLAUDE.md, README.md
└── root one-offs: generate_report.py, generate_cover.py, merge_and_qa.py,
    agi_body.pdf, AGI_Investment_Landscape_August_2026.pdf, lead-naghshi-portable.zip

OUTSIDE THE REPOSITORY (same machine):
C:/Users/Armin/Desktop/
├── OCTOPUS-NBB-CP-WORKING/       [SEPARATE GIT REPO — active today 16:02; 81 py;
│   └── nbb-control-plane/          branch claude/second-brain-governor-v02-2a6e36;
│                                   remote = git bundle inside F:/backup vault]
├── OCTOPUS-REDESIGN-SCAN-2026-08-07, octopus-ambiguity-remediation-v1/v2,
│   octopus-completion-r0-r4-v1, octopus-discovery-d1-d8-full-v1/v2, octopus-s8r-run,
│   octopus-stage9-12, octopus-through-simulation, octopus-human-handoff,
│   octopus-owner-to-end-* (x2), octopus-owner-waived-audit, octopus-overnight-completion
│   → all pinned at legacy commit a3000f0 (2026-07-14)
├── NBB-CP-BASELINE-20260815-145952.txt, NBB-CP-READONLY-REPORT.txt, NBB-CP-TEST-INVENTORY.txt
├── OCTOPUS-R1-EXTERNAL-AUDIT-RESULT.zip, OCTOPUS-SAFE-SNAPSHOT.zip,
│   OCTOPUS-THROUGH-SIMULATION-FINAL-EVIDENCE-PACK.zip
├── 4D-Vault/ (second copy), اختاپوس بک لپ/ (backup-laptop copies incl. another organism.py)
└── fix-redteam.py, fix2.py, lab.py, make-nbb-readonly-report.ps1
E:/germline/octopus.git            [remote bare repo "germline"]
```
