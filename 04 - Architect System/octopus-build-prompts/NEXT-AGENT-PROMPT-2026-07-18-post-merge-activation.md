---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, activation, restart, telegram, validation, post-merge]
created: 2026-07-18
updated: 2026-07-18
replaces: "[[NEXT-AGENT-PROMPT-2026-07-18-integration-unification]]"
---

# NEXT AGENT PROMPT — Post-Merge Activation & Validation (2026-07-18)

## Mission

You are the next agent. The parallel-agent integration is **done and merged to master** (commit `7ad1ce4`). Your job is to **activate** the unified code on the live organism and validate that every Telegram-facing path works against the real, unified store.

**عدمِ توهّم:** وضعیتِ زیر را از دیسک/git باز verify کن، نه از رویِ این خلاصه. هر ادعا را با `git rev-parse` / `git log` / `ls` / `md5sum` چک کن قبل از اقدام.

## Verified ground truth (as of end of unification session)

### Git state — RE-VERIFY ALL

| Item | Expected state (verify before acting) |
|---|---|
| `master` | `7ad1ce4` — merge commit, **2 parents** (`f437a46` + `eacb13d`) |
| `unify/octopus-2026-07-18` | `eacb13d` (integration tip + Ziman branding, flag-off) |
| `integration-debug-2026-07-18` | `acec0bc` (untouched, kept as backup branch) |
| worktree branch | wherever the organism/owner left it — do NOT assume |
| merge tree | superset of master+integration+Ziman-branding |

Re-verify with:

```bash
git rev-parse master
git cat-file -p master | grep -c '^parent'   # must print 2
git rev-parse unify/octopus-2026-07-18
git log --oneline master -4
```

### What landed on master (the merge `7ad1ce4`)

- `c7ac2cd` — docs: consolidation manifest + this-prompt's predecessor + HANDOFF bullet + INDEX entry
- `acec0bc` — accounting integration debug sweep (8 phases, 11 findings)
- `6b9dca8` — doctor real merge-tap (bounded self-change via whitelisted tune-knob)
- `7b7734b` — Saba interactive LLM brain
- `99cb9af` — cortex-watchdog.ps1 (supervise brain on 8772)
- `ce6da6a` — **Ziman branding** (live leg → shared brain, `OCTOPUS_ZIMAN_BRANDING` flag-off by default)
- `eacb13d` — Ziman `$0` condition doc precision

### What was intentionally NOT merged

- mom-bot (full bot under `03 - Projects/Ziman Galerry/mom-bot/`)
- Ziman deep-scan report + V8/V9 verdict queue
- full branch merge of `claude/ziman-gif-deep-scan-19ef9a` (only 2 commits cherry-picked)
- **these remain available on `claude/ziman-gif-deep-scan-19ef9a @ ef090f7` if needed later**

### Local / gitignored files — MUST stay untouched

- `_ops/OCTOPUS-flags.cmd` — runtime truth, gitignored. md5 at handoff: `23248b213ffe062f8db7c58eb542cd19`. Contains the flags that need a restart to take effect.
- `.env` — secrets, **never print/write**
- `STOP-*` files — owner-gated kill switches

## Non-negotiable guardrails (carry forward)

1. **No secret exposure.** Never print `.env` values. Variable names/presence only.
2. **Do not blindly overwrite `_ops/OCTOPUS-flags.cmd`.** It is the runtime truth. Read-only unless owner explicitly directs a change.
3. **No `run_all` against a live organism** unless organism is safely stopped. Prefer targeted tests.
4. **Do not delete `STOP-*` files** without explicit owner command.
5. **`OCTOPUS_ZIMAN_BRANDING` stays OFF** unless owner explicitly votes to enable it.
6. **Self-modification stays bounded:** code/money/genome = lesson-only + escalate. Only whitelisted tune-knobs may apply. AST-enforced.
7. **Restart is owner-gated.** Do not restart the organism without owner confirmation.
8. **Windows Defender may lock `.git/objects/<subdir>` mid-operation** (signature: `Permission denied` on a *different* subdir each retry). Fix = retry-loop (3–5 attempts, sleep 1s). Do not "fix" permissions; it's real-time AV scanning.

## Desired end state of THIS session

A. Live organism restarted **once** (owner-gated) on the unified code.
B. Telegram paths validated against the real unified store:
   - `/sync` — accounting sync/writeback
   - `/review` — fresh session from current store
   - `/finance` — simple Persian UX
   - `/finance!` — expert UX
   - `/books` — first confirmation (only if owner ready)
C. Doctor knob-RFC card observed on first doctor cycle post-restart.
D. `OCTOPUS_ZIMAN_BRANDING` confirmed still OFF.
E. Owner gets a concise Persian report: what activated, what validated, what still pending.

## Recommended execution plan

### Phase A — Re-verify reality (read-only, do first)

```bash
git rev-parse master                              # expect 7ad1ce4
git cat-file -p master | grep -c '^parent'        # expect 2
git rev-parse --abbrev-ref HEAD                   # note current worktree branch
git status --short | grep -vE 'state/|pulse/|cortex/|budget/|neural/|genome/|_memory/|governor/' | head
md5sum _ops/OCTOPUS-flags.cmd                     # expect 23248b21... unless owner changed it
ls -la .env                                       # present, not opened
```

If any of these disagree with the table above, **STOP and report the discrepancy**. Do not paper over it.

### Phase B — Pre-restart health check (read-only)

Before restart, confirm the unified code is coherent on disk:

```bash
# Ziman branding flag-off check
grep -c "ZIMAN_BRANDING" _ops/OCTOPUS-flags.cmd    # expect 0 (absent = off)
grep -n "OCTOPUS_ZIMAN_BRANDING" _ops/wiring.py | head -3   # confirm default-off in code

# Quick targeted test on the unified tree (do NOT run run_all on live organism)
python -X utf8 "F:\backup\_ops\tests\test_merge_applies_knob.py"
python -X utf8 "F:\backup\_ops\tests\test_ziman_branding.py"
```

If these aren't green, stop and report — do not restart onto broken code.

### Phase C — Restart (OWNER-GATED — confirm first)

This is the single irreversible-ish step. Get explicit owner confirmation, then:

1. Stop the organism cleanly (use the existing stop path, do not kill -9).
2. Restart on the unified code.
3. Confirm organism boots and probes succeed (8771 organism, 8772 cortex).

> If owner says "not yet" → skip to Phase E (report + pending list). Do not pressure.

### Phase D — Telegram validation (after restart)

In order, observe each path against the **real unified store** (not fixtures):

1. `/sync` — does accounting sync/writeback run cleanly? Note any error.
2. `/review` — does a fresh review session start from the current store?
3. `/finance` — simple Persian UX renders, zero jargon for owner view.
4. `/finance!` — expert view still has the detail fields.
5. `/books` — only if owner is ready for first confirmation.
6. Wait for / trigger the **doctor cycle** — verify the knob-RFC card appears (epoch-gate fires on first tick because `_beat_epoch_fired=0`).
7. Confirm `OCTOPUS_ZIMAN_BRANDING` is still OFF (no branding card should fire).

If any path errors, **do not auto-fix**. Report the exact error + `path:line` and ask owner.

### Phase E — Report + pending decisions

Give the owner a concise Persian report:

```text
✅ / ⚠️ وضعیتِ فعال‌سازی
- restart انجام شد / نشد (چرا)
- مسیرهای تلگرامی: /sync /review /finance /finance! /books — نتیجهٔ هر کدام
- کارتِ knob-RFC دکتر: آمد / نیامد
- Ziman branding: خاموش ماند (تأیید)
- خطاها (اگر هر): path:line
```

## Pending owner decisions (from prior sessions, still open)

Carry these forward — do NOT resolve unilaterally:

- **Abbas `chat_id`** for `TELEGRAM_ALLOWED_CHAT_IDS` (env).
- **Accounting policy profile:** legal name + ABN.
- **BotFather token for Saba** if Saba Studio goes live.
- **Enable `OCTOPUS_ZIMAN_BRANDING`?** (currently OFF; owner-gated)
- **Cleanup:** delete `unify/octopus-2026-07-18` and `integration-debug-2026-07-18` branches after owner confirms master is good? (keep at least one as backup)
- **mom-bot / Ziman deep-scan:** merge from `claude/ziman-gif-deep-scan-19ef9a @ ef090f7` now or postpone?

## Known issues to flag (do not auto-fix)

1. **Stray nested dir:** `03 - Projects/Accounting/03 - Projects/Accounting/personal/ledger/journal-proposals.json` — a path-mirroring bug in the live organism created a duplicate tree. Left untouched. Flag for owner.
2. **9 legacy test files** still inject `REAL_VAULT` into `sys.path` directly (open chip from prior session). Not a blocker for activation but tracked.
3. **`test_durable_journal.py`** may exit during pytest collection — known script-test behavior, not a regression unless touched.

## Reversibility (if something breaks)

The merge is fully reversible via reflog:

```bash
# see pre-merge master
git reflog master | head -3        # master@{1} = f437a464 (pre-merge)
# rollback (owner-gated, only if something is genuinely broken)
git update-ref refs/heads/master f437a4642cf1c1c254cd2ffe0975533f7b5e90a0
```

Do NOT rollback without owner confirmation + a clear diagnosis of what broke.

## Final report format (Persian, concise, factual)

```text
✅ وضعیت نهایی فعال‌سازی
- وضعیتِ git (master/worktree) بعد از verify
- restart: انجام شد/نشده + دلیل
- مسیرهای تلگرامی و نتیجهٔ هر یک
- کارتِ knob-RFC دکتر: وضعیت
- Ziman branding: خاموش (تأیید) / روشن (خطا)
- فایل‌های local/gitignored دست‌نخورده (flags.cmd md5, .env)
- تصمیم‌های owner باقی‌مانده
- خطاها با path:line (اگر هر)
```

## What NOT to do

- Do not run `run_all` on the live organism.
- Do not enable `OCTOPUS_ZIMAN_BRANDING` without owner vote.
- Do not restart without owner confirmation.
- Do not auto-fix Telegram errors — report with `path:line`.
- Do not blindly overwrite `_ops/OCTOPUS-flags.cmd` or `.env`.
- Do not delete `STOP-*` files.
- Do not trust summaries — verify from disk/git first.
