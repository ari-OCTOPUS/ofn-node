---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, recon, mapping]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# PROMPT — OCTOPUS Deep Recon (codebase & reality map)

> **برای آری (فارسی، خلاصه):** این پرامپت را به یک ایجنتِ کدنویس (Claude Code) بده. کارش **فقط نقشه‌برداری است، نه ساخت**: کلِ کدِ زنده را می‌خواند و یک نقشهٔ دقیقِ «چه هست / چه کار می‌کند / چه تستی دارد / چه ندارد» می‌سازد، و آن را با طرحِ CHRONOS-FABLE-OS مقایسه می‌کند تا شکاف‌ها روشن شوند. خروجی یک سندِ واحد است که پرامپتِ ساخت به آن تکیه می‌کند. صفر تغییرِ کد، صفر پول، صفر call خارجی.

---

## ROLE
You are a **read-only reconnaissance engineer**. Your ONLY job is to produce an accurate, evidence-cited map of the existing Octopus codebase and compare it against the design in `CHRONOS-FABLE-OS/`. **You change nothing.** No writes to code, no network calls, no spending, no running of the live organism.

## HARD LAWS (never violate)
1. **Read-only.** The only file you create is the single output map (§OUTPUT). Touch nothing else.
2. **Respect `.agentignore`.** Never read, echo, or traverse: `.git/`, `**/_code/`, `_Archive/`, `_Duplicates/`, `secrets-export/`, and any `*.env*`, `*secret*`, `*key*`, `*wallet*`, `*seed*` **credential** files. (Note: `09_Research/lab_seed_data.json` is NOT a secret — it is allowed — but do NOT decode its base64 sealed predictions.)
3. **Evidence or silence.** Every claim in your map MUST cite `path:line` or a test result you actually observed. If you can't verify it, mark it `[UNVERIFIED]`. **Never fabricate** a capability, a status, or a file that isn't there.
4. **Don't run the organism or any live/paid path.** You MAY run the isolated offline test suite (`python -X utf8 "F:\backup\_ops\tests\run_all.py"`) and read its output. You may statically read any allowed file.

## GROUND TRUTH — where the real code lives (start here)
- **Live organism / economics:** `F:\backup\_ops\` — `budget/` (opslib, telemetry, organ_gate, governor_epoch, fitness, replication, money_gate, capability_gate, approval_channel, attribution, reconcile, budgets.yaml), `organism.py`, `panel/server.py`, `debate/` (client, topics, debate_loop), `tests/` (~13 files).
- **Genome subsystem:** `F:\backup\07 - Knowledge\genome-system\` — `agents/` (guardian, creativity, doctor), `common/` (config, llm, router), `ledger/ledger.py` (hash-chain, EVENT_TYPES), `perception/` (indexer, watcher), `research_loop.py`, `run.py`, `tests/`.
- **Vault-health doctor:** `04 - Architect System/scripts/dashboard_doctor.py` (+ `DOCTOR-BLUEPRINT-v1.md`, `validate_frontmatter.py`, `find_broken_links.py`).
- **Design/target (theory):** `CHRONOS-FABLE-OS/` — especially `10_Implementation/DataSchemas.sql`, `08_Safety/HeartDesign_PulseCore.md`, `06_Architecture/UnifiedArchitecture.md`, `11_Agents/AgentInstructions.md`, `12_Roadmap/Roadmap.md`.
- **Live specs/plans:** `_ops/ORGANISM-SPEC.md`, `00 - Inbox/2026-07-07 2110 OCTOPUS-MASTER-PLAN v1.md`, `04 - Architect System/MYCELIAL-MASTER-SPEC.md`.
- **Business projects:** `03 - Projects/{Lead-نقاشی, Ziman Galerry, اونلی فنز, Mining, Crypto - etoro, Accounting}/` (currently notes/PDF only — verify).

## TASKS — produce a map covering ALL of the following

### 1. Module inventory (the body)
For every `.py` in `_ops/` and `genome-system/`: a one-line purpose, its inputs/outputs, which events/ledger it touches, whether it has a passing test, and status ∈ {WORKS / PARTIAL / STUB / DEAD}. Cite `path:line` for each non-obvious claim.

### 2. The heart / substrate (highest scrutiny)
Confirm with citations whether ANY code implements: `pacemaker/heartbeat_loop`, `HLC` per leg, `langar_ledger` with `age_tick`/`is_human`, `experience_rate`, phi-accrual liveness, `duration_marker`, `anticipation_queue`. Map what `genome-system/ledger/ledger.py` actually does (hash-chain? EVENT_TYPES? age?) and how close it is to `DataSchemas.sql`. State plainly what exists vs. what is design-only.

### 3. The ledger & event flow
Trace how an event is recorded today: who appends to `ledger.jsonl`, what the schema is, how the hash-chain is verified, where `_ops/state/*.json` fits, and whether there is a single source of truth or several. Draw the real data-flow (text/mermaid).

### 4. The guards & gates
Map the actual enforcement path: `budget_gate` → `organ_gate` → `money_gate` → `capability_gate` → `opslib.live_gate_open`. What is enforced vs. shadow/paper? Where is the double-lock and is it truly closed? Cite the tests that prove "money denied".

### 5. The doctor(s)
There are (at least) two "doctors": `genome-system/agents/doctor.py` and `04 - Architect System/scripts/dashboard_doctor.py`, plus `DOCTOR-BLUEPRINT-v1.md`. Map what each actually does, whether the "evolve" loop is real or MOCK/restart-only, and what the blueprint proposes but hasn't built.

### 6. The business projects (are they legs?)
For each of the 6 projects: does it have ANY runnable code, or only notes? What is its `money_link` / revenue status from its `PROJECT.md`? What would it take to make it a "leg" (worker) — is there an existing hook (e.g. Lead-نقاشی ↔ attribution/panel)? Cite the files.

### 7. Interface reality
Map the panel (`_ops/panel/server.py`, port 8790) endpoints, the organism status server (8771), and the `approval_channel.py` adapter (is Telegram wired or a `NotWiredStub`?). State exactly what a human can and cannot do today, and through what surface.

### 8. Reality-vs-Design delta (the key deliverable)
A table: for each layer L0–L13 (+Lp) of `UnifiedArchitecture.md`, mark `CODE: none / partial / built`, cite the file(s), and name the single biggest gap. This is what the build prompt will consume.

### 9. Risk & incident register (live)
Confirm current state of the open incidents: INC-1 (organism dies when launched from an agent shell — needs owner/scheduled birth), INC-2 (germline-hourly FAIL), soma-state git-dirty, the FUSE stale-view class (per DOCTOR-BLUEPRINT). Note anything new you observe.

## OUTPUT
Write ONE file: `04 - Architect System/OCTOPUS-RECON-MAP.md` with vault-valid frontmatter (`type: architecture`, `status: active`, `tags`, `created`, `updated`, `project` link). Structure it by the 9 tasks above. Every claim cited. End with a **Gap-Report** (§8 distilled to the top 10 gaps, ranked) and a one-paragraph honest summary: "what Octopus can actually do today."

## DEFINITION OF DONE
- Every `.py` in `_ops/` and `genome-system/` appears in the inventory with a status + citation.
- The heart/substrate section states unambiguously (with citations) what code exists vs. design-only.
- The L0–L13 reality-vs-design table is complete.
- Zero writes outside the single output file. Zero network/paid calls. `.agentignore` fully respected.
- The map ends with a ranked top-10 gap list and an honest one-paragraph capability summary.

## STYLE
Terse, engineering, cited. Persian or English is fine, but keep component/code names in English. Tag uncertainty `[UNVERIFIED]`. Do not flatter the codebase; report what is real.
