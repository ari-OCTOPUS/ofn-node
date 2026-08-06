---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, audit, purposefulness, cleanup]
created: 2026-08-06
updated: 2026-08-06
created_by: agent
sources:
  - "9-finder purposefulness audit workflow (w3r6q78oe), 2026-08-06"
---

# کاتالوگِ ممیزیِ هدفمندی — ۱۱ ایجنت، ۲۰۲۶-۰۸-۰۶

> مالک پرسید: «چه جاهاییش الکی و بی‌هدف؟ به تک‌تک بخشاش هدف بدیم.» این
> کاتالوگ خروجیِ ۹ finder ِ موازی + سنتز است — هر بخشِ بی‌هدف با severity و
> **هدفِ پیشنهادی**. لایهٔ تصمیمِ معمار (چه GLM بسازد، چه رأیِ مالک می‌خواهد)
> در `_ops/MEGAPROMPT-GLM-WORKER-2026-08-06.md` فاز ۲ و در
> [[22-SELF-AWARENESS-ROADMAP-2026-08-06]].
> ⚠️ نقشهٔ راه (سندِ ۲۲) چند یافتهٔ همین کاتالوگ را با خواندنِ کدِ زنده
> **تصحیح** کرد (سیلوها ۲ تا نه ۵؛ reducerِ جزئیِ `self-claims.jsonl` از قبل
> کار می‌کند) — آن تصحیح‌ها معتبرترند.

*Synthesis of 9 parallel investigator passes (vault-foldermap, ops-wiring, projects-legs, self-awareness-layer, docs-architecture, telegram-ui-surface, flags-overall-purpose, genome-learning-decision, root-clutter). Findings merged into clusters where multiple dimensions independently hit the same underlying issue; proposed_purpose revised where cross-dimension context sharpened it.*

---

## Bucket 1 — Actively Misleading (fix first: looks purposeful, isn't)

### 1.1 Flags armed in `OCTOPUS-flags.cmd` whose own adjacent comment says the opposite, or whose armed state produces zero live effect
**Dimensions: flags-overall-purpose + ops-wiring (exact overlap on BUDGET_JUDGE).**
- `OCTOPUS_WIRE_BUDGET_JUDGE` — `_ops/OCTOPUS-flags.cmd:711-715`: comment literally says "2026-07-28 DISARMED... wiring is owner decision, not agent" directly above a `set ...=1`. Also zero importers of `heart/budget_judge.py` anywhere (ops-wiring, independently confirmed via orphan_scan.py) — armed flag writes an unread plan file.
- `OCTOPUS_WIRE_ROMAJAN_PROBES` — `:433-434`: comment says "OFF until owner confirms F:\romajan readable," next line sets `=1`.
- `OCTOPUS_WIRE_GOVERNOR` / `OCTOPUS_TG_OPS_BUTTONS` — `:684-700`: header says these are commented-out illustrative defaults ("uncommenting is a change"); both are live `set ...=1`.
- `OCTOPUS_WIRE_LEAD_OUTBOUND` — `:872-875` stale "stays 0, no SMTP creds" comment never removed after `:913-924` armed it 2026-08-01.
- `now_moves/unified_bus_guard.py` (`OCTOPUS_WIRE_BUS_GUARD=1`, armed): docstring says arming should make `wiring.py`'s `make_unified_bus` return `wrap(bus)`; `wiring.py` never reads this flag at all — `is_human=True` forgery protection is exactly as absent as before arming. Security-relevant.
- `legs/agent_gateway_http.py` (`OCTOPUS_WIRE_AGENT_GATEWAY=1`, armed): `serve()` — the function that opens the listening socket — has zero callers anywhere; the AGI-peer gateway has never once started despite being "on."
- `now_moves/staleness_stamp.py` (`OCTOPUS_WIRE_STALENESS_STAMP=1`, armed): docstring names the exact two call-sites to add (`live/server.py`, `telegram_center/render.py`); neither exists. The specific bug it claims to fix (36h-frozen cell rendering green) is still live today.
- Meta-finding: the 49-flag block header (`:1052-1059`) claims "each of these has its own citation" — false; 48 of 49 have zero individual comment.

**Revised proposed purpose:** treat as one systemic pattern, not five isolated bugs — this codebase's convention of gating everything behind flags has drifted into flags being armed without anyone updating the adjacent prose or wiring the consumer. Recommend a single pass: for every flag where comment and `set` value disagree, either fix the code to match the comment's stated intent or fix the comment/value to match reality, dated and attributed. Do this before trusting any OCTOPUS_WIRE_* flag as ground truth elsewhere in the audit.

### 1.2 Four uncoordinated "octopus architecture status" silos, none reachable from the vault's own MOC, two of them both claiming `status: active`
**Dimensions: vault-foldermap + docs-architecture.**
- `06 - Architecture Maps/_Index - Architecture Maps.md` links only 9 of ~60 files in its own folder — misses both MASTER-ARCHITECTURE docs, the whole 10-file OCTOPUS-* registry family, ADR-001, AUTONOMY-MATRIX, etc.
- `MASTER-ARCHITECTURE-2026-07-09.md` and `MASTER-ARCHITECTURE-2026-07-29.md` are both `status: active`, 20 days apart, describing materially different topologies ("second-brain" vs. legs/heart/cortex/doctor/cockpit organism), with no `supersedes`/`archived` field linking them.
- `03 - Projects/_OCTOPUS-PMO/` (20+ audit/forensic docs, own `SOURCE-OF-TRUTH-MATRIX.md`) competes directly with 06's `SYSTEM_MAP.md` for "the" architecture source of truth — no PROJECT.md, absent from every index.
- `06 - Architecture Maps/نقشه-اختاپوس/` duplicates the vault's own governance filenames (`REGISTRY.md`, `VERDICT_QUEUE.md`) inside a folder whose stated purpose is diagrams only.
- `07 - Knowledge/شناخت-اختاپوس/` is a fourth, still-growing (as of today, 2026-08-06) chronological octopus-status stream, absent from the Knowledge index.

**Revised proposed purpose:** pick exactly one canonical location (06 - Architecture Maps fits its declared charter best), regenerate its index from a directory scan rather than a hand-maintained list, mark the older MASTER-ARCHITECTURE `archived`/`superseded-by`, and drop a one-line pointer note in `_OCTOPUS-PMO`, `نقشه-اختاپوس`, and `شناخت-اختاپوس` saying which location is authoritative. This is the single highest-leverage documentation fix in the vault — four other findings below (genome docs, `_memory-blueprints`, `_doctor-research`) are symptoms of the same "no canonical SoT" root cause.

### 1.3 Self-awareness layer reports confidence/freshness it hasn't earned
**Dimension: self-awareness-layer (single dimension, but internally a tight cluster of 5 sub-findings around one root cause).**
- `doctor/self_knowledge.py` emits a **hardcoded 0.85 confidence** even in the same cycle its own `self_accuracy.py` measured **0.667 accuracy** — nothing lowers the stated confidence when the measured accuracy is bad.
- `cortex/calibration_probe.py` — live re-run 2026-08-06: Brier=0.290 vs. baseline (constant-guess) 0.232 — the organism's stated confidences are **measurably worse than a coin flip today**, and nothing pushes this verdict anywhere; it only surfaces if the owner manually types `/insight`.
- `cortex/self_model.py:99-155` — `self_awareness_pct` (97.7%) is literally "percent of modules with a non-empty docstring first line," fed into a claim key labeled `self_model.coherence`, and the code's own comment admits the key is **permanently ungraded, structurally unfalsifiable**.
- `telegram_center/mirror_room.py` — owner-corrections channel silent for 10 days; `self_knowledge.py` still re-quotes the 2026-07-27 sentence verbatim as "current focus" with no staleness flag.
- `cortex/self_audit.py:392-431` — `static_by_construction: True`, several probes (`_probe_named_owner`, `_probe_trace_independent`) are hardcoded `return _item(..., True)` — always-pass, can never register a regression — the exact "unfalsifiable claim" pattern the codebase's own `coherence.py` was built to hunt.
- Root cause (also self-awareness-layer): `cockpit_brain.py:180-199` — the one channel that proactively pushes to the owner wires only 3 of ~10 discovered self-observation modules (code-archaeology tools), never `self_model.json`, `calibration-latest.json`, or `doctor/self-knowledge-latest.json` — so it can only ever say "code changed," never "what I believe about myself changed."

**Proposed purpose (as originally stated, sound):** one shared append-only self-state reducer that all five producers write into, with `cockpit_brain.diff()` running over the merged stream; wire `self_accuracy`'s measured value back into `self_knowledge`'s emitted confidence instead of a constant; treat a calibration "worse" verdict as an always-notable event like `halted`/`germline_alert`.

### 1.4 Accounting leg reports itself dead while a real accounting engine runs beside it
**Dimension: projects-legs.**
`accounting_status()` reads only the mtime of `.xlsx` files (`age_days=612.8`, `live=False`) while, in the same package, PocketSmith sync is armed (`OCTOPUS_WIRE_ACCT_BEAT=1`), 576+ transactions are synced/reconciled, `ledger_core.py` is live, and write-back is armed (`OCTOPUS_WIRE_PS_WRITEBACK=1`). The PROJECT.md itself calls this "a measurement gap, not a dead business," unfixed since 2026-08-01. Accounting is the architect's own declared #1-priority tenant — the organism's self-awareness is wrong about its most important leg. **Fix:** repoint `accounting_status()` at the live PocketSmith/`ledger_core` pipeline.

### 1.5 Lead-نقاشی: the one "real" leg has never received a real external lead
**Dimension: projects-legs.**
Live=true, money_link=active, invoices/quotes real (ABN/GST/bank details filled), but the log states "zero delivered proposals in the system's entire lifetime" and the website's SSL certificate has been expired **294 days** with zero contact-form submissions — the one real external intake channel has been silently broken for ~10 months while everything downstream of it looks fully operational. **Fix:** reconcile Mission/KPIs to say "pipeline proven on synthetic data, awaiting live intake" until the cert is renewed.

### 1.6 Lead-card outbound buttons: marked fixed (VQ-DEAD-LEAD-BUTTONS-001), still cannot fire end-to-end
**Dimension: telegram-ui-surface. Cross-references 1.5 (same lead pipeline).**
The *receiving* side (`center.py:4710-4764`, verbs `lcall`/`ldraft`) was explicitly fixed and has a passing regression test (`test_lead_card_buttons_live.py`) — but nothing in production calls `lead_card.render()`/`keyboard()`/`deliver()`; `lead_scorer.py` only calls the text-only `card_text()`. Even if wired, `GROUP_CALLBACK_VERBS` (`input_surface_policy.py:78-80`) doesn't include `lcall`/`ldraft`, so a tap from the group's lead topic would be denied anyway. A green regression test is giving false confidence that this ships. **Fix:** wire `_contact_card()` to `render()`+`deliver()` and add the two verbs to `GROUP_CALLBACK_VERBS`, or delete the whole send/receive split honestly.

### 1.7 `approval_queue_unified.py` docstring makes a checkably false claim about what the Telegram bot reads
**Dimension: ops-wiring.**
Docstring claims it unifies two approval queues into one JSON that "Telegram bot از همین JSON می‌خواند." `refresh()`/`main()` have zero callers anywhere (confirmed by orphan_scan.py) — the JSON is never produced, so the bot still reads the old non-unified queue. The claim is false today, embedded in living code. **Fix:** wire `refresh()` into the bot's actual queue source, or delete the module and correct the docstring.

### 1.8 genome-system's own canonical docs present a retired system as current
**Dimension: docs-architecture.**
`HANDOFF.md`/`README.md`/`INDEX.md`/`CHANGELOG.md` all `status: active`, but `STATUS.json` in the same folder says `"status": "retired"` (2026-07-17, tri-scan: "zero `_ops` importers, no scheduled task"). HANDOFF.md still tells other agents *how to propose to* Guardian/Creativity/Doctor and describes a "3x/day" schedule with no mention it was retired three weeks before today. **Fix:** archive-flag the four docs scoped precisely to the loop app (ledger/opslib consumer stays documented as live).

### 1.9 `_memory-blueprints` — 6 active PROJECT.md files still cite a stale design via a dead path
**Dimension: docs-architecture.**
`LIVING-BRAIN-BLUEPRINT.md`, `TWO-BRAIN-CONTROL-BLUEPRINT.md`, `FRANKENSTEIN-BUILD-PLAN.md` are `status: active` but one month stale, describe a "pyramid/two-brain" vocabulary absent from every current architecture map (organism/legs/heart/cortex/doctor/cockpit instead). Accounting, Crypto, اونلی فنز, Ziman, Mining, and Lead-نقاشی PROJECT.md files all still link to these via `[[_memory/TWO-BRAIN-CONTROL-BLUEPRINT]]` — the **old, renamed** path (folder is now `_memory-blueprints`), so the links are stale in both content and path simultaneously.

### 1.10 `_doctor-research` MOC presents itself as a running hourly pipeline; it ran for one day
**Dimension: docs-architecture.**
`type: moc, status: active`, describes an "hourly scheduled task" deepening 8 research columns. Its own execution log stops at 2026-07-06 10:22 (5 entries, one day), every verdict row still `⬜ pending` a month later, with no indication in the note itself that it stalled.

### 1.11 Dashboard drift — the vault's own session-start navigation hub is stale and self-contradicting
**Dimension: vault-foldermap.** CLAUDE.md names `Home.md` as the mandatory first stop every session; unmodified 22 days despite 6+ new projects and a whole `_OCTOPUS-PMO` tree appearing since. `Brain.md` claims to be "live," rewritten every 3h by a `brain-pulse` cron per AGENT_REGISTRY — actually 31 days stale. `Domains Status.md` states "Bases plugin still not active" while three `.base` files sit in the same folder proving otherwise.

### 1.12 Inbox silently violates its own stated 7-day SLA and exit criterion
**Dimension: vault-foldermap.** 89 of 92 top-level notes are 8-34 days stale against a rule that says nothing sits past 7 days; exit criterion ("only AGENT_QUESTIONS.md remains") is nowhere close. Compounding: `octopus-new-modules-2026-07-24/` has live Python code sitting in Inbox for 2+ weeks (code must never live outside `_code` per rule §1.2) with a WIRING-GUIDE implying integration that never happened; `replication-kit/`, `system-review-2026-07-11/`, `build-proposals/` are whole deliverable folders parked 26-34 days, never triaged.

### 1.13 NBB-Control-Plane: unresolved governance question the repo structurally treats as answered
**Dimension: vault-foldermap.** A full nested software repo (own `.github/`, git bundle, `pyproject.toml`) sits inside the Obsidian-managed tree while `VQ-ROOT-001` ("relationship of app/NBB-CP to Architect/_ops") has been open ~26 days — every day it sits there un-registered (no PROJECT.md, no _Index entry) is a day the vault silently answers "portable sibling" by default without anyone deciding that.

---

## Bucket 2 — Genuinely Dead Clutter (safe to archive/remove)

- **Root-level AGI-report toolchain** (`generate_report.py`, `generate_cover.py`, `generate_agi_report.js`, `merge_and_qa.py`, plus outputs `AGI_Infrastructure_Investment_Report_Aug2026.docx`, `AGI_Investment_Landscape_August_2026.pdf`, `agi_body.pdf`, `cover.pdf`, `cover.html`, plus `package.json`/`package-lock.json`/`node_modules`) — *root-clutter*. One 4-minute session (2026-08-04), topic matches none of the 8 declared vault areas, hardcodes throwaway absolute paths, `/Producer: Z.ai Report System` metadata confirms external one-off tool. All untracked/gitignored. **Action:** keep final deliverable only (move to `_Archive`), delete the rest.
- **`leaks.txt` / `mixed_examples.txt`** — *root-clutter*. Grep-dump of 64 `_ops/*.py` files; confirmed **no actual secrets** (targeted checks for tokens/keys/IBAN/wallet patterns all negative — the captured lines are the codebase's own redaction regexes, not secret values). Still currently sitting untracked in this exact worktree (`?? leaks.txt`, `?? mixed_examples.txt` in git status) — misleading filename, zero callers. **Action:** delete or move to a scratch dir; do not leave "leaks" in a filename at vault root even when contents are clean.
- **`lead-naghshi-portable.zip`** (23.8MB, root) — *root-clutter*. Created 1.5 min after its source `_build/lead-naghshi-portable/` finished writing — a packaged build left loose instead of delivered or archived.
- **`now_moves/kill_seam_closer.py`** — *ops-wiring*. Correctly self-documented as superseded: its intended callers (`organ_gate.py`, `debate_loop.py`) broke on import and were reimplemented as `opslib.kill_seam_denies()` (confirmed live at both call-sites). The flag is genuinely live — just via the reimplementation. This file itself is pure dead weight; its own docstring says "ROLLBACK: delete this module" is a valid path.
- **Dead miniapp functions `renderStudio()` / `renderNext()`** — *telegram-ui-surface*. `renderStudio` (112 lines) has zero call sites; two comments in the same file document it was replaced by `renderLeadOps`/`renderTasks` on 2026-08-04/05 yet the body was never deleted, so it still ships in every bundle with its own documented bugs intact. `renderNext` duplicates `renderTasks`'s data source, not in the dispatch map, no tab references it, removal not even commented.
- **`octopus-prime-labs/`, `octopus-ramanujan/`** (`03 - Projects/`) — *vault-foldermap*. Completely empty directory trees, no PROJECT.md, absent from every index; only mentioned in two old handoff docs.
- **`07 - Knowledge/_backups/.staging-20260706-172057/`** and **`_backups/*.tar.gz`** — *docs-architecture + vault-foldermap*. Pre-build genome-system snapshot, zero frontmatter, duplicates content that now lives properly in `07 - Knowledge/genome-system/`; the `.tar.gz` binaries also directly violate §2's "no binaries in Knowledge" rule.
- **`07 - Knowledge/_audit/`** — *docs-architecture*. One-off 2026-07-05 audit, predates `genome-system`/`_memory-blueprints`/`_doctor-research`, non-canonical free-text `status:` field, own completion banner says done but was never moved to `_Archive`.
- **`07 - Knowledge/school-memory/`** (`curriculum.py`, `test_curriculum.py`, `__pycache__`) — *vault-foldermap*. Executable code sitting directly in the Knowledge folder, violating §1.2 and §2 simultaneously.
- **`01 - Dashboard/PARALLEL-AGENTS-CONSOLIDATION-2026-07-18.md`** — *vault-foldermap*. One-off dated snapshot in a folder that should only hold Home/HANDOFF/`.base` files; unlinked, untouched 19 days.
- **`brain/cockpit.py` (`BrainCockpit` class)** — *self-awareness-layer*. Fully tested (3 test files) but zero production callers anywhere in the live Telegram stack — the live 6-option owner panel uses `owner_views.py`/`owner_menu.py`/`owner_debug.py` instead. Only production reference is one constant import. A fully-tested parallel implementation nothing renders — the tests actively launder false confidence that it's live.
- **Crypto - etoro leg** — *projects-legs*. 47 days of zero forward motion (age_days grew only by calendar time, no new data ingested since creation), empty Portfolio Registry, no automated execution path even in principle (eToro retail API doesn't support it), all 3 next-actions unchecked. The PROJECT.md itself already asks for an active-vs-paused verdict.
- **`05 - Agents/Vault Operator SYSTEM-PROMPT v2.md`** — *vault-foldermap*. `status: active` but 26 days stale, absent from `_Index - Agents.md`, only inbound references are two old Inbox scan docs — likely superseded by Vault Cartographer.
- **`04 - Architect System/_intake-photos/`** — *vault-foldermap*. Contains exactly one placeholder file ("put things here"); never used.

---

## Bucket 3 — Aspirational-Never-Built (build it or archive it honestly)

### 3.1 The entire genome self-improvement pipeline reports itself as more functional than it is
**Dimension: genome-learning-decision (5 tightly linked sub-findings, one root pattern: "decision machinery that decides nothing").**
- `DOCTOR_MERGE`/`apply_merge` — 47 ledger entries, **all** `knob_applied: null`. The one structurally eligible flag (`OCTOPUS_WIRE_MERGE_APPLIES_KNOB=1`, whitelisted knob `CHRONO_NUDGE_EVERY_N_BEATS`) still nulls out; the same bottleneck was re-drafted as a fresh RFC three separate times without ever actually landing. `_ops/state/cortex/auto-knobs.json` (the file it's supposed to write) doesn't exist. **This is the single closest-to-real lane — worth prioritizing over the rest** (likely the flag is armed in a config snapshot never loaded into the running process's `os.environ`).
- RFC corpus: 276/293 (~94%) status `drafted`, only 17 `merged`; `change_level=='code'` RFCs are hard-coded to only ever write a lesson note, never apply code.
- `code-autonomy-applied.jsonl`: exactly one row, ever — `applied:false, rolled_back:true`. Four full 2026-07-26 self-improvement cycles all stopped at "card to owner."
- Debate survivors queue: 147 entries since 2026-07-17, **100%** still `pending-human`/`undecided-after-3-rounds`, content frequently degenerate (mixed-language garbage), same ~15 topics recycling verbatim weekly.
- Metabolic governor: 673 hourly epoch snapshots, every allocation tagged `SPEC(shadow — zero enforce)` by its own output, zero graduation toward enforcement in a month.
- Genome ledger: 89.6% of 14,924 entries are advisory-only `SCHEDULER_DISPATCH` noise; only 0.08% are real `PROPOSAL` entries.

**Proposed purpose:** either complete the one nearly-working lane (DOCTOR_MERGE knob-apply) as proof the mechanism can work at all, or relabel the whole apparatus honestly as "lesson generator," not "self-improvement/RFC system" — it currently reads as decision machinery producing 14,000+ log lines of decisions it never makes.

### 3.2 `world_discovery/` + `integrations/world_discovery_action/` — matched orphan pair
**Dimension: ops-wiring.** Two fully-built subsystems (world_discovery's 5-function public contract `observe/triangulate/discover/design_experiment/export_bundle`, plus its dedicated action-bridge translator) stacked on each other, zero importers outside their own test suites in either. `action_bridge/integration.py:9` states outright it does not import world_discovery "not today." **Decide as one unit** — wire both behind a shared flag, or archive both together (they were clearly designed as a pair).

### 3.3 `legs/consent_gate.py` — the lead-outbound compliance firewall was never wired in
**Dimension: ops-wiring.** `may_draft()`/`may_release()` — documented as "every consumer calls, no Leg reads the table directly" — are called by nothing in the live lead pipeline. Master flag `OCTOPUS_WIRE_CONSENT_FW` is absent from `OCTOPUS-flags.cmd` entirely (fail-closed by omission is currently the only thing protecting this). **Priority:** wire before `OCTOPUS_WIRE_LEAD_OUTBOUND` sends real email (cross-ref 1.1's LEAD_OUTBOUND finding — it's already armed).

### 3.4 `budget/drawdown_guard.py` — circuit breaker never fires even in shadow mode
**Dimension: ops-wiring.** Own docstring is candid it never live-HALTs anything by design, but even its stated minimum (shadow-log a would-halt verdict when `spike_pct=25` is breached) never happens — `verdict()`/`shadow_count()` have zero callers, flag on or off.

### 3.5 `budget/governor.py` — unclear relationship to `governor_epoch.py`
**Dimension: ops-wiring.** Only importer is its own test file; `organism.py` never imports it, only mentions "governor" in Persian prose comments about the different `governor_epoch.py`. Needs an owner call on whether `decide()`/`route()` supersedes or feeds the epoch router.

### 3.6 `self_insight.py` — the most sophisticated self-correction mechanism has never completed a cycle
**Dimension: self-awareness-layer.** Its docstring's stated differentiator from `self_scan` is exactly a falsifiable-prediction grading loop (`predicted_observations` → `score_previous()`), but its own journal file `state/self-insight.jsonl` doesn't exist on disk — its only caller in the whole repo is the owner-typed `/insight` Telegram command, never invoked. Cross-references 1.3 (cockpit_brain wiring gap) as the likely fix: add it as a periodic tier.

### 3.7 Ziman Galerry — built feature sitting unused, hard gate unmet a month
**Dimension: projects-legs.** `OCTOPUS_ZIMAN_BRANDING` fully built and tested 2026-07-18, project's own log says "three weeks built and left dark" as of 08-01. D4 hard gate (capacity ceiling) unmet since creation because owner never supplied a units/week number — both capacity=30 and inventory=20 still `[تأییدنشده]`. A full silent week (07-29 to 08-01) with zero project-specific commits.

### 3.8 Mining leg — honest permanent skeleton, but UI investment outpaces the physical blocker
**Dimension: projects-legs.** `mining_status()` correctly always returns `live=False` by design (no live scorer will be faked); root blocker is 162 nodes off since before project creation, still off a month later, Next-action #1 "(owner) turn on OPI-01" still unchecked. Yet six Telegram UI features (numeric cards, stop-intent, swap/switch receipts) were built 2026-08-01 on top of this dead leg, all acknowledged in the log as unproven.

### 3.9 اونلی فنز (Project-F) — engineering complete, blocked purely on 3 signatures
**Dimension: projects-legs.** 209/209 tests passing, two cockpits, DecisionLog governance, a mini-app — zero external action since creation because GATE 0 has blocked everything since 2026-07-20 pending three owner signatures still outstanding two weeks later. Also invisible to the organism's own self-awareness (`ORGANISM-STATE.business_legs`) for its first month. Correctly gated, no code needed — the single next action is surfacing the outstanding ballot, not more features.

### 3.10 `02 - Life OS` — self-described empty scaffold
**Dimension: vault-foldermap.** `_Index - Life OS.md` literally says "currently empty; just a starting point," `status: paused`. `Weekly Review.md` describes a weekly cadence never once exercised in 34 days.

### 3.11 `4D-Obsidian-Foundation/` — 8-doc doctrine set, never linked, unclear if superseded
**Dimension: vault-foldermap.** All 8 docs created in one 2026-07-16 session, zero links from Home/_Index/MOC/AGENT_REGISTRY anywhere. Needs a decision: still governs vault IA (link it) or superseded by later ADRs (archive it explicitly).

---

## Bucket 4 — Missing Only a Purpose-Explaining Comment (cheap fix)

**Dimension: flags-overall-purpose** (all in `_ops/OCTOPUS-flags.cmd`, all currently `set ...=1` with zero rationale nearby):
- `OCTOPUS_HTTP_AUTH` / `EVOLVE_REQUIRE_APPROVAL` (`:255,257`) — sit inside a heartbeat-tuning comment block that never mentions either; both are security/governance-relevant with zero explanation.
- `OCTOPUS_OBS_ALERT` (`:27`) — sandwiched between unrelated comment blocks, undocumented.
- `OCTOPUS_WIRE_MENU_V2` / `OCTOPUS_TG_LLM_ASK` (`:336,338`) — isolated between two unrelated documented blocks.
- `OCTOPUS_WIRE_LEAD_OUTCOME` (`:380`) — undocumented despite being part of the learning loop discussed extensively elsewhere in the same file.
- `OCTOPUS_GOVERNOR_USE_ROUTER` / `OCTOPUS_HEART_DOCTOR_USE_ROUTER` / `OCTOPUS_DOCTOR_SELFKNOW_PAID` / `OCTOPUS_HEART_HONEST_PULSE` (`:436-442`) — four consecutive undocumented `set` lines; `SELFKNOW_PAID` is money-relevant (routes to paid brain) per an *earlier* comment at `:317` that never explains why it was actually thrown.
- `OCTOPUS_WIRE_THESIS_QUEUE` / `OCTOPUS_WIRE_COHERENCE` (`:431-432`) — ride along in a block whose comment enumerates 5 other flags but never these two.
- `OCTOPUS_WIRE_LEAD_CANDIDATES` — the good rationale (`:535-546`) is 335 lines away from the actual `set` line (`:870`), which carries only a generic comment.
- `OCTOPUS_WIRE_HARVEST` (`:19-25`) — comment exists but is mojibake-corrupted (violates the file's own ASCII-only rule), effectively zero usable information survives.

**Dimension: ops-wiring:**
- `legs/agent_gateway_http.py:49,68,75` — three numeric env knobs (`PORT`, `MAX_BYTES`, `RATE_PER_MIN`) with bare defaults and no rationale, against a codebase norm of 1-3 line explanations for every other tunable. (Currently moot since the parent module is unwired per 1.1, but cheap to fix alongside it.)

**Dimension: vault-foldermap:**
- `AGENT_REGISTRY.md` — already honestly self-documents that 12 agent identities + 19 scouts + 6 selfimprove lines are undeployed/intentionally dark. Cheap fix: split into "live" vs. "backlog" tables so readers/validators don't have to re-derive which is which.
- `Chord/PROJECT.md` — well-formed, `status: active`, just absent from `_Index - Projects.md` and CLAUDE.md's ecosystem table. Add it (or confirm superseded and archive).

**Dimension: docs-architecture:**
- `MYCOLEDGER-REBUILD-CHARTER-proposal.md` (v1) — sibling v2 already declares `supersedes:` pointing at it; v1 itself just needs a one-line `superseded_by:` added to match the vault's own existing convention (e.g. SYSTEM-BLUEPRINT-v2).
- `CLEANUP.md` — no frontmatter at all, body-only date predates its own folder's other files; needs `status:` (done/idea) and folding of any surviving items into `BACKLOG.md`.
