---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, integration, git, handoff]
created: 2026-07-18
updated: 2026-07-18
---

# NEXT AGENT PROMPT — Octopus Parallel-Agents Integration Unification

## Mission

You are the next agent. Your job is to turn the current multi-agent outputs into a single coherent, safe, tested integration path.

Do **not** assume the previous summaries are fully live. Verify from disk and git refs first.

The owner wants: **همهٔ خروجی agentهای موازی روی یک پروژه واحد منسجم شوند و مطمئن شویم همه‌چیز save است.**

## Current verified ground truth

Read this first:

- `01 - Dashboard/PARALLEL-AGENTS-CONSOLIDATION-2026-07-18.md`
- `01 - Dashboard/HANDOFF.md`
- `INTEGRATION-REPORT-2026-07-18.md`
- `ARCHITECTURE-SOT.md`
- `_ops/BOTS-REGISTRY.md`

Verified state as of the handoff:

| Item | Verified state |
|---|---|
| current checkout | `integration-debug-2026-07-18` |
| current HEAD | `acec0bc41acdab2e5a22e514e91771a658c53c16` |
| master ref | `f437a4642cf1c1c254cd2ffe0975533f7b5e90a0` |
| integration branch contents | integration/debug phases + Saba brain + cortex watchdog + doctor real merge-tap + accounting sweep |
| Ziman/Fugu branding | saved on `claude/ziman-gif-deep-scan-19ef9a @ ef090f7`, **not merged into current disk** |
| local runtime flags | `_ops/OCTOPUS-flags.cmd`, gitignored/local, currently contains accounting/cortex/doctor flags |

Important: current live checkout is **not** master. Do not report “merged to master” unless you actually verify/perform it.

## Non-negotiable guardrails

1. **Never paste or expose secrets.** Do not print `.env` values. You may check for variable names/presence only if needed.
2. **Do not overwrite `_ops/OCTOPUS-flags.cmd` blindly.** It is local/gitignored and contains the runtime truth. If any checkout/merge would touch it, stop and handle manually with a copy/restore plan.
3. **Do not run `run_all` against a live organism.** If testing broadly, first ensure organism is stopped or use isolated targeted tests. Prefer targeted tests.
4. **Do not delete `STOP-*` files unless owner explicitly asks.** They are owner-gated kill switches.
5. **Do not merge Ziman branch blindly.** It started from an older master (`76ab9e8`) and may conflict with newer integration/accounting/doctor changes. Review diff first.
6. **Keep high-risk self-modification bounded.** Code/money/genome changes remain human-gated. Doctor merge-tap may apply only whitelisted reversible tune knobs.
7. **Commit docs/checkpoints before risky integration.** Make merge reversible.

## Desired end state

A. All current docs/handoff changes are committed.

B. There is a clear branch strategy:

- either merge `integration-debug-2026-07-18 @ acec0bc` into `master`, or create a new unification branch from the correct base and merge there first;
- then integrate `claude/ziman-gif-deep-scan-19ef9a @ ef090f7` by cherry-pick/merge after diff review;
- preserve local flags and secrets.

C. Targeted tests pass for touched domains.

D. The owner gets a final concise report with:

- exact branch/HEADs before and after;
- what was merged;
- what was intentionally left unmerged;
- tests run and results;
- restart/Telegram validation steps.

## Recommended execution plan

### Phase 0 — Freeze facts and protect docs

1. Confirm current branch/HEAD using git.
2. Confirm refs:
   - `master`
   - `integration-debug-2026-07-18`
   - `claude/ziman-gif-deep-scan-19ef9a`
3. Commit the already-written consolidation docs if uncommitted:
   - `01 - Dashboard/HANDOFF.md`
   - `01 - Dashboard/PARALLEL-AGENTS-CONSOLIDATION-2026-07-18.md`
   - this prompt file, if present

Suggested commit message:

```bash
git add "01 - Dashboard/HANDOFF.md" \
        "01 - Dashboard/PARALLEL-AGENTS-CONSOLIDATION-2026-07-18.md" \
        "04 - Architect System/octopus-build-prompts/NEXT-AGENT-PROMPT-2026-07-18-integration-unification.md"
git commit -m "docs(handoff): consolidate parallel agent integration state"
```

If there are unrelated dirty files, do **not** stage them. Report them separately.

### Phase 1 — Decide merge topology safely

Preferred safe topology:

```bash
git checkout -b unify/octopus-2026-07-18 integration-debug-2026-07-18
```

Why: current integration branch already contains the latest accounting/doctor/Saba work. A unification branch lets you review/merge without mutating master immediately.

Then compare with master:

```bash
git log --oneline --decorate --graph --all --max-count=80
git diff --stat master..integration-debug-2026-07-18
git diff --stat integration-debug-2026-07-18..master
```

Do not assume master is behind or ahead; verify.

### Phase 2 — Integrate master delta if needed

If `master @ f437a464` contains commits not in integration, inspect them before merging:

```bash
git log --oneline integration-debug-2026-07-18..master
git diff --stat integration-debug-2026-07-18..master
```

If safe, merge master into the unification branch:

```bash
git merge --no-ff master
```

Resolve conflicts carefully. Special caution:

- `_ops/wiring.py`
- `_ops/organism.py`
- `_ops/budget/approval_channel.py`
- `_ops/legs/accountant.py` / accounting files
- `_ops/doctor/doctor.py`
- `01 - Dashboard/HANDOFF.md`
- `ARCHITECTURE-SOT.md`
- `_ops/OCTOPUS-flags.cmd` — should not be overwritten blindly

After merge, run targeted tests for affected modules.

### Phase 3 — Review and integrate Ziman/Fugu branch

Branch:

```text
claude/ziman-gif-deep-scan-19ef9a @ ef090f7
```

First inspect:

```bash
git diff --stat HEAD..claude/ziman-gif-deep-scan-19ef9a
git diff HEAD..claude/ziman-gif-deep-scan-19ef9a -- "_ops/legs/ziman_leg.py" "_ops/wiring.py" "03 - Projects/Ziman Galerry" "01 - Dashboard/HANDOFF.md"
```

Expected feature from that branch:

- `_ops/legs/ziman_leg.py`: `draft_content(use_llm=...)` / `_llm_brand_body`
- `_ops/wiring.py`: `OCTOPUS_ZIMAN_BRANDING` daily beat wiring
- docs under Ziman project for branding activation
- mom-bot docs/build from earlier commits

Recommended integration style:

- Cherry-pick the feature commits if clean:
  - `6166b39` — Ziman branding live leg to shared brain, flag-off
  - `ef090f7` — docs precision for `$0` condition
- Consider whether earlier mom-bot commits should also merge now. They are not required for Ziman branding runtime.

Suggested cautious sequence:

```bash
git cherry-pick 6166b39
git cherry-pick ef090f7
```

If conflicts occur, stop and resolve manually. Preserve current integration/accounting/doctor changes.

Do **not** enable `OCTOPUS_ZIMAN_BRANDING` unless owner explicitly asks. Feature should remain flag-off by default.

### Phase 4 — Targeted tests

Run only targeted suites unless organism is safely stopped.

Minimum targeted tests after integration:

```bash
python -X utf8 "F:\backup\_ops\tests\test_merge_applies_knob.py"
python -X utf8 "F:\backup\_ops\tests\test_auto_approve.py"
python -X utf8 "F:\backup\_ops\tests\test_self_improve.py"
```

Accounting targeted tests, choose based on filenames present:

```bash
python -X utf8 "F:\backup\_ops\tests\test_accountant.py"
python -X utf8 "F:\backup\_ops\tests\test_acct_review.py"
python -X utf8 "F:\backup\_ops\tests\test_books_telegram.py"
python -X utf8 "F:\backup\_ops\tests\test_review_telegram.py"
python -X utf8 "F:\backup\_ops\tests\test_finance_card.py"
```

Ziman targeted tests, inspect filenames first:

```bash
dir "F:\backup\_ops\tests\*ziman*"
python -X utf8 <ziman test files>
```

Saba targeted tests:

```bash
python -X utf8 "F:\backup\03 - Projects\اونلی فنز\studio\test_saba_brain.py"
python -X utf8 "F:\backup\03 - Projects\اونلی فنز\studio\test_saba_studio.py"
```

If `test_durable_journal.py` exits during pytest collection, do not treat it as a regression unless touched. It is known script-test behavior.

### Phase 5 — Commit unification branch

After tests pass:

```bash
git status --short
git add <only intended files>
git commit -m "merge: unify 2026-07-18 integration outputs"
```

Then either:

- report branch ready for owner merge to master, or
- if owner explicitly approved master merge, merge `unify/octopus-2026-07-18` into master.

### Phase 6 — Runtime activation / validation

Only after code is unified and tests pass:

1. Restart organism once.
2. Validate Telegram:
   - `/sync` — accounting sync/writeback path
   - `/review` — fresh session from current store
   - `/finance` and `/finance!` — simple/expert UX
   - `/books` — first confirmation if owner is ready
3. Wait for doctor cycle or trigger appropriately; verify knob-RFC card and merge-tap behavior.
4. Do not flip `OCTOPUS_ZIMAN_BRANDING` unless owner explicitly approves.

## Owner actions still pending

- Abbas `chat_id` for `TELEGRAM_ALLOWED_CHAT_IDS`
- accounting policy profile: legal name + ABN
- BotFather token for Saba if Saba Studio goes live
- decision: merge integration to master now or keep as integration branch
- decision: include Ziman branding branch now or postpone

## Final report format

Report in Persian, concise but factual:

```text
✅ وضعیت نهایی
- branch/HEAD قبل و بعد
- چه چیزهایی merge/cherry-pick شد
- چه چیزهایی عمداً merge نشد
- تست‌های اجراشده و نتیجه
- فایل‌های local/gitignored که دست نخورده ماندند
- اقدام‌های owner: restart، /sync، /review، /books، Ziman flag
```

## Known pitfalls

- Search tools may fail on Persian path/globs. Direct path listing confirmed Saba files exist under:
  `03 - Projects/اونلی فنز/studio/`
- Ziman branch is real and saved, but not on current disk.
- `OCTOPUS-flags.cmd` is runtime truth and should remain local-safe.
- Master and integration are diverged; do not flatten without checking logs/diffs.
- HANDOFF is already long; prefer linking to the consolidation manifest rather than pasting huge content.
