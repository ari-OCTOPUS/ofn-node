# HANDOFF — start here (for the next agent)

You are continuing **CHRONOS-FABLE OS**. This tree has everything needed to continue safely with **zero prior context**. Read in this order.

## 1. Read the operating rules first
`13_MasterPrompts/MasterSystemPrompt.v2.md` — the self-contained contract (DNA, invariants, 15-layer architecture, execution loop, extension law, safety posture). This is how **you** must behave: propose, don't execute; tag every claim; end with a gap-report; never delete; never fabricate a blocked value; never settle an irreversible effect yourself.

## 2. Understand the state
- `00_Executive/ProjectState.md` — continuity anchor, phase status, locked decisions, open questions.
- `00_Executive/Audit_2026-07-08.md` — the consistency/gap audit; every finding (F-1..F-8) and its fix.
- `CHANGELOG.md` — what changed this session (additive).

## 3. Know what's solid vs blocked
- `01_SourceMap/MissingEvidenceRegister.md` — MER-1 **closed** (DOC-B in repo); MER-2/3/6 still open with exact upgrade triggers.
- `MANIFEST.md` §Blocked — the hard evidence walls and which upload clears each.

## 4. If you're given a task
Work only with evidence-supported material. If asked for a `[BLOCKED]`/`[UNVERIFIED]` value, cite the specific blocked item and stop — do not invent schemas, parameters, or results.

## 5. If you're given a missing primary
Ingest it, then upgrade the linked items to their new confidence and log the change additively in `CHANGELOG.md`. Priority order of value: **SRC-1** (unblocks the most) → **Survival-Stack** (DOC-A) → **lab-seed JSON**.

## Operator decisions currently owed (no file needed)
OQ-1 stasis canon · OQ-2 ratify `age_tick=is_human` (evidence already resolved) · OQ-4 system name · ratify INV-17*/AP-14*.

## First implementation step when building starts
`12_Roadmap/Roadmap.md` Phase 0: ship the L0 substrate (Event-Bus/LANGAR + HLC + pacemaker + TINV-7 gate) using `10_Implementation/DataSchemas.sql`. No hybrid work before that (anti-meta-escalation).
