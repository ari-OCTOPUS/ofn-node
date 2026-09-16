---
type: reference
status: idea
tags: [prompt, integration, phase-4, architect]
created: 2026-07-03
updated: 2026-07-06
---

# Prompt — Phase 4: Real Integration (اتصال واقعی همه دامنه‌ها)

> **کی اجرا شود:** فقط بعد از این زنجیره — (۱) ☐ verdict روی Phase 0 → (۲) ☐ فاز ۱–۳ پرامپت vault-phase3 (manifestها + ARCHITECT_CHARTER + SYSTEM_MAP + AGENT_REGISTRY) → (۳) ☐ آدیت ۸-پاسه fusion-mvp → (۴) ☐ اجرای TOP-5 از REFACTOR_PLAN. زودتر اجرا شود = روی شن ساختن.
> وضعیت 2026-07-03: هر ۴ مرحله باز است — گیت‌چک همین تاریخ: P1 تا P4 همگی false [Verified].
> متن زیر را همان‌طور که هست به جلسه بده.

---

```
ultrathink

You are continuing work on this vault + the architect runtime (fusion-mvp).
Phases 1-3 gave us a PAPER spine: manifests, charter, registry, map.
This run makes it REAL: the runtime must read the vault as its contract,
act only through the charter's gates, and report through one Telegram
command plane. Paper -> daemon.

PREREQUISITES (verify first; if ANY is false, STOP and report which):
- P1. ARCHITECT_CHARTER.md + all domain PROJECT.md manifests exist
      (frontmatter: status, risk_level, autonomy_level + Agent interface).
- P2. fusion-mvp AUDIT.md + REFACTOR_PLAN.md exist and the TOP-5 items
      are implemented with their verification steps passed.
- P3. ROTATION_CHECKLIST.md has ZERO open CRITICAL rows and I have given
      an explicit verdict lifting the Security Gate.
- P4. secrets-export/ no longer exists inside the vault.

OPERATING RULES (unchanged, non-negotiable):
- Human-only verdicts; global kill-switch honored everywhere; append-only
  Anchor Ledger; agents may never modify the charter, their own
  permissions, or the safety layer.
- Plan -> propose -> my approval for anything destructive or >5 files.
- No secret values in vault, code, logs, or chat. Config via env outside
  the vault only.
- Tag claims: [Verified] / [Unverified] / [Assumption] / [To measure].

PHASE A — CONTRACT LOADER (vault <-> runtime):
Build a manifest loader in the architect runtime: parse every domain
PROJECT.md (frontmatter + Agent interface section) into runtime config
at boot. The vault is the single source of truth — no domain rule may be
hardcoded in agent code. Fail-closed: unparseable or schema-invalid
manifest => that domain runs read-only. Wire validate_frontmatter.py as
a pre-boot gate. Deliverable: loader + tests + a BOOT_REPORT note.

PHASE B — TELEGRAM COMMAND PLANE (one bot, one interface):
Commands: /status (per-domain digest built from Active Context),
/verdict <proposal-id> approve|reject, /kill (global kill-switch),
/gate (Security Gate state parsed live from ROTATION_CHECKLIST.md).
Every inbound verdict and outbound notification = one Anchor Ledger row.
PRIVACY RULE (hard): the اونلی فنز domain appears in Telegram, dashboards
and cross-domain reports ONLY as "Project-F" — never platform name,
partner identity, or content details.

PHASE C — ANCHOR LEDGER, FOR REAL:
Hash-chained append-only log (JSONL): verdicts, auto-actions, gate
changes, adapter failures. Chain verified on every boot; verification
failure => system-wide read-only + Telegram alert. No agent write path
except the ledger API.

PHASE D — DOMAIN ADAPTERS (smallest viable, one per AGENT_REGISTRY row):
- Lead-نقاشی: lead-log ingest -> weekly experiment report (draft only).
- Crypto-etoro: exit_rules watcher -> SELL/TRIM proposals per §Trading
  Autonomy (D1). Starts in dry-run; no live execution until my verdict.
- Mining: death-watch checklist evaluator per D2 -> report only.
- Accounting: receipt/invoice inbox -> categorized DRAFT entries, every
  tax rule tagged [Unverified — accountant to confirm].
- Ziman: capacity guard per D4 — refuse campaign drafts above ceiling.
- Project-F: checklist/task reporter only; never touches content/media.
- هیپنوتیزم: read-only indexer; fiction-canon notes never cited as
  evidence (epistemic_status enforced).
Each adapter reads/writes EXACTLY what its registry row allows. A silent
adapter failure is the highest-severity bug: every failure must surface
to the HITL step.

PHASE E — SHADOW WEEK + GO-LIVE GATES:
7 days shadow mode: all adapters read-only, one daily digest to
Telegram, zero external actions. Exit criteria per domain: zero silent
failures, ledger chain verified daily, false-alarm rate reported, and my
explicit per-domain go-live verdict. Autonomy after go-live = whatever
that domain's manifest allows, still capped by the charter and the
kill-switch. Metrics to log: proposals made vs accepted, time-to-verdict,
alerts per domain.

REPORT: INTEGRATION-REPORT.md at vault root — what runs, what is still
paper, every [Unverified] left, top 5 next actions by risk-reduction per
hour. If context fills: finish current phase, update HANDOFF.md, stop.
```
