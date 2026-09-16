---
type: handoff
status: active
tags: [ops, integration, octopus]
created: 2026-07-18
updated: 2026-07-18
---

# Parallel Agents Consolidation — 2026-07-18

این سند، خروجی چند agent موازی روی یک پروژه واحد را به یک نقشهٔ عملیاتی تبدیل می‌کند. هدف: معلوم باشد **چه چیزی واقعاً روی دیسک فعلی است، چه چیزی فقط فلگ محلی است، چه چیزی روی branch جدا save شده، و اقدام بعدی چیست**.

## 1) وضعیت گیت / دیسک فعلی

| مورد | وضعیت تأییدشده |
|---|---|
| checkout فعلی | `integration-debug-2026-07-18` |
| HEAD فعلی | `acec0bc41acdab2e5a22e514e91771a658c53c16` |
| master ref | `f437a4642cf1c1c254cd2ffe0975533f7b5e90a0` |
| base جدایی integration از master | integration از `fc53252` ساخته شده، سپس کامیت‌های فاز ۱–۷، doctor-knob و accounting sweep روی آن آمده‌اند |
| Ziman/Fugu branding | روی branch جدا save شده: `claude/ziman-gif-deep-scan-19ef9a @ ef090f7`؛ روی دیسک فعلی merge نشده |

نتیجه: **همهٔ خروجی‌های مهم save شده‌اند، اما روی یک branch واحد نیستند.** برای runtime فعلی، ارگانیسم فایل‌های checkout فعلی (`integration-debug-2026-07-18`) را می‌خواند.

## 2) بسته‌های ادغام‌شده روی دیسک فعلی (`integration-debug-2026-07-18`)

### A. Integration/debug 7-phase package

Commits تأییدشده در reflog برنچ:

- `1189e8d` — budgets/debate/GLM/Painting-Accounting organ fixes
- `7b7734b` — `saba_brain.py` interactive LLM brain for Saba Studio
- `99cb9af` — `cortex-watchdog.ps1` + scheduled supervision for cortex 8772
- `eab10e2` — `_ops/BOTS-REGISTRY.md` + `saba-bridge.jsonl`
- `3b86e59` — PII guard test cherry-pick
- `da01c46` — `ARCHITECTURE-SOT.md`, DEPRECATED markers, health baseline
- `aea204f` — `INTEGRATION-REPORT-2026-07-18.md`

Canonical docs present:

- `ARCHITECTURE-SOT.md`
- `_ops/BOTS-REGISTRY.md`
- `_ops/HEALTH-BASELINE-2026-07-18.md`
- `INTEGRATION-REPORT-2026-07-18.md`

### B. Doctor self-change / real Telegram merge-tap package

Commits:

- `6b9dca8` — owner merge-tap applies a bounded real self-change (`tune` knob), not just lesson
- `67ef83b` — HANDOFF record for button-reality audit

Runtime flags confirmed in `_ops/OCTOPUS-flags.cmd`:

```cmd
set OCTOPUS_WIRE_PROPOSAL_BUTTONS=1
set OCTOPUS_WIRE_DOCTOR_KNOB_RFC=1
set OCTOPUS_WIRE_MERGE_APPLIES_KNOB=1
```

Safety boundary:

- Only whitelisted reversible knobs can be applied.
- Code/money/genome remain lesson-only/escalate.
- Owner explicit values are respected.
- Rejected knob RFCs are not re-minted.
- `apply_knob` float-string bug was fixed: integer env values now stay parseable by `int(...)` consumers.

Activation status: **needs organism restart** for the live process to import new code/flags.

### C. Accounting 8-phase sweep

Commit:

- `acec0bc` — accounting integration debug sweep, 8 phases / 11 real findings

Confirmed outcomes from agent reports and current flags:

- stale review session reset; next `/review` rebuilds from current store
- `/finance` UX and expert path `/finance!`
- duplicate flags cleaned, `TG_CENTER_BOT_TOKEN` moved to `.env`
- binary sidecars untracked/gitignored
- regression guards: COA/hash/no-jargon/dispatch
- source-code PII default empty
- organism was restarted by that agent and reported live
- PocketSmith/accounting flags are present in `OCTOPUS-flags.cmd`:

```cmd
set OCTOPUS_WIRE_POCKETSMITH=1
set OCTOPUS_WIRE_ACCT_BEAT=1
set ACCT_BEAT_SYNC=1
set OCTOPUS_WIRE_PS_WRITEBACK=1
set OCTOPUS_WIRE_ACCT_REVIEW_LLM=1
```

Owner actions still pending:

1. Abbas `chat_id` for `TELEGRAM_ALLOWED_CHAT_IDS`
2. `legal_name` and `abn` in accounting policy profile
3. First manual Telegram `/sync` to trigger initial writeback/backfill
4. First `/books` confirmation to post first journal to `ledger_core`

### D. Cortex/brain/cortisol flags

Current flags confirmed in `_ops/OCTOPUS-flags.cmd`:

```cmd
set CORTEX_LOCAL_FIRST=1
set CORTEX_THINK_EVERY_N=1
set OCTOPUS_CORTISOL_EVENTS=1
set OCTOPUS_SYNTH_EVENT_DRIVEN=1
```

Meaning:

- local-first model routing is on
- cortex thinks from boot / every cycle
- cortisol event edge can trigger immediate synthesis, with cooldown and paid-gate constraints
- timer synthesis skips paid call when inputs unchanged

Activation caveat: code/flags only affect the running process after restart.

## 3) Saved but NOT on current disk: Ziman branding/Fugu branch

Branch:

- `claude/ziman-gif-deep-scan-19ef9a @ ef090f7`

Commits from reflog:

- `86c1345` — Ziman Gift deep scan report / PROJECT-HANDOFF refresh
- `9344799` — Ziman operator L1 decision package
- `27544e0` — mom-bot built/hardened, 23 tests green
- `2974f68` — mom-bot handoff activation path
- `6166b39` — `feat(ziman):` live leg wired to shared brain/Fugu, flag-off
- `ef090f7` — docs: `$0` condition depends on `CORTEX_LOCAL_FIRST=1`

Ground truth check on current disk:

- Current `_ops/legs/ziman_leg.py` does **not** contain `draft_content(use_llm=...)`.
- Current checkout does **not** contain `BRANDING-AUTOMATION-2026-07-18.md` under the expected path.

Therefore: Ziman branding is **saved in git**, but **not merged into current live checkout**.

Recommended integration path:

1. Review diff of `claude/ziman-gif-deep-scan-19ef9a` against current integration branch.
2. Cherry-pick or merge only after resolving conflicts with the newer integration/accounting/doctor changes.
3. Keep `OCTOPUS_ZIMAN_BRANDING` default-off until owner explicitly flips.
4. After merge, run targeted Ziman + wiring tests before restart.

## 4) What is local-only / gitignored

These are intentionally not committed and must be treated as live-local configuration:

- `.env` — secrets and API keys
- `_ops/OCTOPUS-flags.cmd` — appears gitignored / local toggle file; current runtime flags are present on disk
- accounting private stores/reports and PocketSmith state

Do not paste secrets into chat or docs. This manifest records only flag names and branch/commit identifiers.

## 5) Unified next-action checklist

### Prepared next-agent runbook

Prompt آمادهٔ اجرا برای agent بعدی:

```text
04 - Architect System/octopus-build-prompts/NEXT-AGENT-PROMPT-2026-07-18-integration-unification.md
```

این prompt دقیقاً ترتیب امن را می‌دهد: commit docs → ساخت branch یکپارچه → مقایسه master/integration → ادغام محتاطانه → review/cherry-pick احتمالی Ziman/Fugu → تست هدفمند → گزارش نهایی.

### Immediate safe verification

- [ ] Restart organism once, so current integration branch code and local flags are imported.
- [ ] In Telegram, run `/sync` and confirm accounting sync/writeback behavior.
- [ ] In Telegram, run `/review`; verify fresh session builds from current store.
- [ ] In Telegram, wait for / trigger doctor cycle; verify knob-RFC card appears and `merge ✅` applies only whitelisted knob.

### Owner data required

- [ ] Abbas chat_id for `TELEGRAM_ALLOWED_CHAT_IDS`
- [ ] accounting policy profile: legal name + ABN
- [ ] BotFather token for Saba bot if Saba Studio should go live

### Branch consolidation

- [ ] Decide whether `integration-debug-2026-07-18 @ acec0bc` should be merged into master.
- [ ] Decide whether `claude/ziman-gif-deep-scan-19ef9a @ ef090f7` should be merged/cherry-picked into integration or master.
- [ ] After merge, re-run targeted suites and update this manifest/HANDOFF.

## 6) Current verdict

**Saved:** yes — the major agent outputs are committed either on `integration-debug-2026-07-18` or `claude/ziman-gif-deep-scan-19ef9a`, and local runtime flags are present on disk.

**Unified into one branch:** not yet — integration/accounting/doctor are on current branch; Ziman branding remains branch-only; master is a separate ref.

**Live runtime consistency:** current running organism may still need a restart to load the latest current-branch code and flags.
