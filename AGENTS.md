# OCTOPUS — Agent Operating Contract

Every agent working in this repository (Cursor Agent, Cursor CLI, cloud agent, Tab) is bound by this file.
Nested `AGENTS.md` files in subdirectories add constraints; they never remove them.

## GOV-V8 — OWNER OVERRIDE (REVENUE-IGNITION) (2026-09-05)

`GOV-V8 (REVENUE-IGNITION)` بالادست بندهای wire، outgoing_message و budget است.
اختیار ایجنت با نردبان L0..L4 در سند
`06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/GOV-V8-REVENUE-IGNITION-2026-09-05.md`
تعیین می‌شود، نه با رأی موردی مالک.
بالا رفتن پله فقط با شرط خودبازشوی همان پله مجاز است.
پایین آمدن پله خودکار، فوری و بدون رأی است.
سه قفل دائمی (secret، زنجیرهٔ رسید، PASS بدون رسید) با این حکم باز نمی‌شوند.
هیچ ایجنتی مجاز به تغییر دامنهٔ اختیار خودش نیست، از جمله تغییر همین بند.

شروع امضاشده: GOV-V8-ACK.json · سطح فعلی **L2** (OWNER-CANCEL cash-gate 2026-09-05) · VERIFIED_CASH=0 (لجر صادق؛ گیت L2 لغو شد).
تعارض میان این فایل و GOV-V8 دربارهٔ نردبان اختیار ⇒ GOV-V8 برنده است.
GOV-V7 سه ممنوعه و چهار حفاظ را نگه می‌دارد؛ برای نردبان درآمد V8 مقدم است.

هر ایجنت باید `GOV_VERSION=V8` و `LADDER=L2` (تا ارتقای شاهد) را در ابتدای گزارش lane بنویسد.

## GOV-V7 — OWNER OVERRIDE (2026-09-05)

سند `OWNER-RULING-GOV-V7-AGGRESSIVE-IGNITION-2026-09-05.md` بالادست همهٔ بندهای
`wire`، `auto_email`، `outgoing_message`، `live_node_contact`، `commit/push/PR`،
`may_authorize` و `paid_call` این فایل است.

پیش‌فرض حاکمیت: ALLOW_WITH_RECEIPT.
بار اثبات بر عهدهٔ توقف است، نه بر عهدهٔ اقدام.

سه ممنوعهٔ باقی‌مانده، مطلق و غیرقابل‌مذاکره:
1. هیچ secret / token / .env / seed / wallet چاپ، ارسال، کپی یا commit نمی‌شود.
2. هیچ entry از زنجیرهٔ رسید حذف یا بازنویسی نمی‌شود.
3. هیچ PASS یا LIVE بدون رسید هم‌دامنه اعلام نمی‌شود.

چهار حفاظ اجباری: kill switch `F:\ofn-node\HALT` · سقف `BUDGET.json` ·
pre-image پیش از هر نوشتن روی نود · «رسید یا rollback» برای هر اثر خارجی.

هر ایجنت باید `GOV_VERSION=V8` (و در صورت نیاز یادداشت V7-locks) را در ابتدای گزارش lane بنویسد. نردبان: V8.
تعارض میان این فایل و GOV-V7 ⇒ GOV-V7 برنده است، بدون پرسش تازه.

## 0. Current engineering entry point

Before orienting in this large vault, read `07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md`; it routes agents to fresh evidence without replacing the truth hierarchy below.

## 1. Truth hierarchy (strongest to weakest)
1. Runtime output: real `pytest` run, execution receipt, `git log`
2. Repository file: ledger, MANIFEST, registry
3. Fresh CHECKPOINT / HANDOFF / DECISIONS
4. Older notes, megaplans
5. FORBIDDEN as evidence: chat summaries, agent memory, guesses

If a claim cannot be confirmed from level 1 or 2, write `status: unverified`. Never write it as fact.

## 2. Evidence grades (attach to every capability claim)
- E0 claimed, no code found
- E1 code exists, no test
- E2 unit test green on designed input
- E3 negative and boundary cases green
- E4 works on held-out (unseen) input
- E5 works under fault injection and scaffold variation

Hard rule: no capability rises above E3 without a scaffold-variation measurement.
Lowering a grade is a successful outcome, not a failure.

## 3. Number discipline
- Number without a source = `unverified`
- Small n = `UNDERPOWERED`, never "improved"
- Contradiction: record both values with `resolution: null, status: open`. Never silently pick one.
- Never generate synthetic or "illustrative" data.

## 4. Output boundaries (non-negotiable)
- Do not enable or flip any flag matching `OCTOPUS_WIRE_*`, `OFN_WIRE_*`.
  Scope (owner vote R2-4, 2026-09-08, "yes to all"): this binds editor-agents touching
  code/config. The wire flags already ON in the organism's own runtime environment are its
  production config, not agent-enabled; agents may not change them in either direction
  without an explicit owner vote.
- `OBSERVATORY`, `CORTEX_HYPOTHESIS`: retired — no definition or consumer found
  (owner vote R2-3, 2026-09-08). Still do-not-enable.
- The email channel is retired; no email is sent. Outbound messages leave only through the
  GOV-V7/V8-governed Telegram path, with receipts (owner vote R2-3 superseded the old
  `auto_email` line).
- Do not open blocked gates: `secret_rotation`, `OWNER_KEY`.
  Removed from this list as moot/undefined by owner vote R2-3, 2026-09-08:
  `partner_precondition`, `wire_publish`, `miner_isolation`, `D1`, `D7`
  (board gates.json rows partner_precondition + wire_publish deleted with pre-image
  receipt; D1/D7 had no recoverable definition — see UNLOCK-REGISTRY history).
- Blocked is a decision, not a defect.

## 5. Self-elevation ban
Never raise your own authority. Do not edit your own gate, quota, or approval threshold.
Do not change a scoring formula mid-cycle. An attempt to self-elevate is an incident and gets logged.

## 6. Owner decisions
Do not decide on the owner's behalf, even when the answer looks obvious.
List it in `07-HANDOFF/` as `status: open, requires: owner_decision` and continue.

## 7. Deletion and naming
- `rm -rf` is forbidden. Stale files move to `99-ARCHIVE/` with an `archive_` prefix.
- No file named "brain v2" or "replacement orchestrator".
- Secrets: key names only, never values. Redact emails and names in logs and fixtures.

## 8. Lane discipline
Each agent works in exactly one lane, declared at session start, in its own git worktree.
Touching a file owned by another lane is a stop condition: log it and halt.

## 9. Exit requirement
Every session ends with `09-LANES/<LANE>/LANE-REPORT.md` containing: what was done, what
remains, what failed, evidence paths, rollback steps. No report, no completion.
