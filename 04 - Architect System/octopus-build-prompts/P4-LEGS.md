---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, build, legs, workers, projects]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# PROMPT — Octopus Build · Phase 4: PROJECTS → LEGS (tentacles/workers)

> **برای آری:** هر پروژهٔ کاری‌ات (که الان فقط نوت و PDF است) یک «پا» می‌شود: یک Workerِ ایزوله که مأموریتش را از PROJECT.md می‌خواند، فقط **پیشنهاد** می‌دهد (کوت/draft/گزارش)، و هیچ‌وقت خودش پول/پیام/ترید اجرا نمی‌کند — آن‌ها با یک تاییدِ تلگرامیِ تو. اول Lead-نقاشی (درآمدِ اصلی).

## 0. ROLE
Turn each business project into an **isolated Worker (leg)**. Propose-only. Additive.

## 1. PREREQUISITE
Phases 1–3 green (heart + doctor + Telegram approval channel). Read `OCTOPUS-RECON-MAP.md` §6 (projects). Each leg's proposals are approved via Phase 3.

## 2. SOURCES
- `CHRONOS-FABLE-OS/11_Agents/AgentInstructions.md` (Worker Guard, universal contract), `08_Safety/IsolationModel.md` (worker sandboxing: task_packet, `secrets:[]`, seccomp/cgroups), `04 - Architect System/MYCELIAL-MASTER-SPEC.md` (the shared spec all projects connect to).
- Each project's brief: `03 - Projects/<name>/PROJECT.md` (+ that folder's notes, read-allowlisted).
- Existing revenue hooks: `_ops/budget/attribution.py` + `reconcile.py` + panel `/lead` (Lead-نقاشی).

## 3. LAWS (critical for this phase)
- **Worker isolation (INV-17):** each leg gets a minimal `task_packet` — read-allowlist to ONLY its own project notes, scoped tools, hard budgets, `spawn=0`, **`secrets:[]`**. Output = a single structured proposal to the parent. No ledger write path. At least process-level isolation (non-root; seccomp/cgroups where the OS allows).
- **Propose-only:** a leg may draft a quote, estimate, report, scouting note. It may **never** send, publish, pay, or trade. Those route to Telegram human-append.
- **money_link required:** a leg without a resolved `money_link` stays `incubating` (INV-14). Each leg sits under an organ budget (`organ_gate`).
- **Financial-action ban:** the Crypto/eToro leg is **read-only analysis, never trades**.
- **Privacy:** customer/PII data stays local, never sent to any external LLM (existing rule).

## 4. STEPS — build one leg at a time (revenue-first, risk-aware)

**L-0 · Leg framework.** Create a `Leg` base (isolated worker): loads `task_packet`, reads its allowlisted brief, produces proposal-events, runs under `organ_gate`, emits HLC-stamped events (Phase 1). One shared, tested harness. Test: a leg cannot read outside its allowlist; `secrets` is empty; output is proposal-only.

**L-1 · Lead-نقاشی (Rule Zero, revenue #1).** Complete the paper loop: intake (Telegram `/lead`) → draft quote + `attribution_id` printed on it → `reconcile.py` matches an operator-dropped CSV in a 7-day window → `fitness` counts only CONFIRMED. Grounded in `MASTER-PLAN Track B`. Test: a paper dollar goes PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED with correct attribution; every customer contact is human-gated.

**L-2 · Accounting (read-only reporting).** A leg that produces tax/report drafts from its notes (tax map already drafted). No money movement. Test: reports as proposals; zero writes to source-of-truth.

**L-3 · Ziman Gallery.** Leg from `ARCHITECTURE-multiuser-admin`/`Business-Zeiman`; propose drafts/plans only. Test: proposal-only.

**L-4 · OnlyFans (content — extra care).** Content-draft leg **strictly inside ToS/KYC red-lines** (DOC-07). Nothing published without human-append; the leg drafts only. Test: no publish path exists in the leg; drafts flagged for human review.

**L-5 · Mining.** Hardware-registry/coin-scouting leg; propose-only briefings. Test: proposal-only.

**L-6 · Crypto - eToro (READ-ONLY).** Market-analysis leg that produces briefings ONLY. **No order/trade path may exist in code.** The human places any order. Test: assert the leg has no trade/execute capability; output is analysis proposals.

## 5. DEFINITION OF DONE
- Each built leg is an isolated worker emitting proposal-events under budget+guards, reading only its own allowlisted notes, `secrets:[]`.
- Lead-نقاشی produces a paper-CONFIRMED dollar with correct attribution.
- Zero irreversible effect fires without a Telegram human-append. The Crypto leg provably cannot trade.
- Suite green; isolation verified per `IsolationModel.md`.

## 6. OPEN-DECISIONS
- Which legs beyond Lead-نقاشی to build first (operator priority). The OnlyFans ToS boundary. Reconcile CSV format/cadence (MASTER-PLAN #5). Carrier-id print location (#9).

## 7. HAND-BACK
Update each `03 - Projects/<name>/PROJECT.md` (Active Context: now a leg), `ORGANISM-SPEC.md`, `HANDOFF.md`; suite green; owner-gated commit.
