---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, build, money, live, gates]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# PROMPT — Octopus Build · Phase 6: MONEY / LIVE (last, fully human-gated)

> **برای آری:** آخرین مرحله و پرریسک‌ترین. تا اینجا همه‌چیز paper بوده. اینجا گیت‌های پول را کامل و enforce می‌کنیم و اولین دلارِ واقعی را — فقط با تاییدِ صریحِ تو و فقط بعد از سبزشدنِ همهٔ گیت‌ها — باز می‌کنیم. هیچ‌چیز قبل از این مرحله زنده نمی‌شود.

## 0. ROLE
Turn on real money **safely and last**. Nothing here fires without the full gate stack + an owner flag + a Telegram human-append.

## 1. PREREQUISITE (hard)
Phases 1–5 green. `OCTOPUS-RECON-MAP.md` §4 (gates) reviewed. Date ≥ **2026-07-21** (calendar floor, not a key). Owner present.

## 2. SOURCES
- `00 - Inbox/2026-07-07 2110 OCTOPUS-MASTER-PLAN v1.md` Track A (A1–A5), `_ops/ORGANISM-SPEC.md` §3–§4 (invariants + activation ladder).
- Existing: `scripts/budget_gate.py`, `_ops/budget/{budgets.yaml, organ_gate, money_gate, capability_gate, approval_channel, attribution, reconcile}.py`, `opslib.live_gate_open`.
- `CHRONOS-FABLE-OS/08_Safety/SafetyModel.md` (human-approval gates) + `MasterSystemPrompt.v2.md`.

## 3. LAWS (critical — non-negotiable)
- **No live path before ALL of:** `budget_gate v2` green + `money_gate` enforcing + `capability-gate` marker written by a green suite + date ≥ 07-21 + owner `ACTIVATION-*.flag`. Any one missing ⇒ closed.
- **Every real-money effect ≥ threshold needs a matched human-append token from Telegram.** Self-reported approval is never valid.
- **Financial-action ban stays:** the system prepares; the human executes trades/transfers. No autonomous money movement, ever.
- **Kill-switch + cost-cap always live;** a budget breach or safety warning freezes the relevant automation and logs it.

## 4. STEPS

**M-1 · budget_gate v2 (SoT-read).** Read caps from `_ops/budget/budgets.yaml`; fail-closed = strictest of (yaml, hardcoded floor) if yaml unreadable; real per-organ buckets (the agent param must actually bind). Files: `scripts/budget_gate.py` + `_ops/tests/test_budget_gate_v2.py` + update the `organ_gate` chain. Test: caps come from SoT; unreadable yaml ⇒ strictest; per-organ enforced.

**M-2 · money_gate enforcement.** `check(amount_aud, approval_token)`: `> human_gate_aud (AU$20)` without a valid token (from the Telegram control-brain queue only) = deny + log. Test: forged token denied; > threshold without approval denied; ≤ threshold within budget allowed (paper still).

**M-3 · capability-gate marker.** `opslib.live_gate_open` becomes three-condition: date ≥ 07-21 (floor) **AND** owner flag **AND** a `CAPABILITY-OK` marker written **only** by a fully green suite (incl. M-1/M-2 tests), bound to the money-code fingerprint. Reaching the date alone opens nothing. Test: prove that after 07-21, without capability+owner+human, no gate opens.

**M-4 · V2 ledger event type.** Add the `MONEY_ATTRIBUTION` type to `genome-system/ledger/ledger.py` `EVENT_TYPES` + chain-compat test + CHANGELOG bump. (Core-ledger edit ⇒ owner verdict.)

**M-5 · First live dollar (owner-gated).** With all gates green + owner flag + a Telegram approval, settle exactly one real, small, reversible-as-possible money effect end-to-end, fully logged and attributed. Then re-freeze and review. Test: the full path is auditable; a single missing gate blocks it.

## 5. DEFINITION OF DONE
- Gate stack green and proven: no live money path opens without budget_gate v2 + money_gate + capability marker + date + owner flag + human-append.
- One live dollar settled under full audit, then re-frozen for review.
- Zero invariant violations; test-backed report.

## 6. OPEN-DECISIONS (operator verdicts required before M-3/M-4/M-5)
- Convert `live_gate` to capability+human (changes the lock definition). Edit `EVENT_TYPES` (core ledger governance). `ACTIVATION-*` flag timing. First-dollar target + amount. Reconcile feed cadence.

## 7. HAND-BACK
Update `ORGANISM-SPEC.md` §4 (activation ladder progressed), `HANDOFF.md`, STAGE3-REPORT; suite + preflight green; owner-gated commit. Octopus is now a complete, human-anchored organism: it lives on its heartbeat, ages only by your hand, does its work through Telegram, and never moves money or itself without you.
