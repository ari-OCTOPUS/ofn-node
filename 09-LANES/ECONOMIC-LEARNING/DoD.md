# LANE ECONOMIC-LEARNING — Definition of Done

Lane: **Economic learning loop, shadow-only** (owner order 2026-09-02)
Base: origin/main @ 389d39958e34568ce225d4cb45522d64921aed47 (includes merged LB #86)
Worktree: F:\wt-economic-learning · Branch: lane/economic-learning-loop
First commit = this file only, per owner order (B6.1).

## Mission

Give OCTOPUS a taste of economic outcome: from REAL events, learn which actions
led to response, quote and payment. Shadow-only: observe → verify receipt →
link action chain → score outcome → extract lesson → propose experiment →
human-gated PR → Obsidian receipt. Nothing here sends, authorizes, merges, or
touches production models.

## Measurable exit criteria

1. **B1 truth measured from receipts only**: campaign PAINT-L5-001 —
   contacts/responses/quotes/payments counted from board138 sqlite (mode=ro),
   not from prose. No real payment receipt exists ⇒
   `payment_received_verified=false` exactly.
2. **Typed-events vocabulary untouched**: `ofn/kernel/events.py` NOT modified
   on this branch (verified by diff); finding + separate contract proposal
   produced instead (payment_received is absent AND quote_sent-class names are
   deliberately sealed FORBIDDEN_EFFECT_KINDS — vocabulary change = owner).
3. **Six modules** under `ofn/learning/`: ReceiptVerifier (independent-receipt
   verification: payment_id/amount/currency/received_at/external hash/source/
   status), ActionChainLinker (lead→contact→response→quote→payment; missing
   links stay UNKNOWN), OutcomeScorer (verified payment = top evidence;
   response/quote = intermediate; no-response = informational failure, never a
   market verdict; NEVER emits send_authorized or substitutes consent),
   LessonExtractor (lesson + supporting + contradicting evidence + confidence
   + sample size + expiry; n=1 ⇒ confidence ≤ low, no general conclusion),
   ExperimentProposer (hypothesis/treatment/control/metric/stop/rollback,
   owner approval always required), EconomicLearningLedger (append-only,
   idempotent, tamper-evident per-line sha256, zero records without destiny,
   crash recovery fail-closed).
4. **15 mandated test scenarios** green, numbered in test names.
5. **Shadow run on PAINT-L5-001** with the honest result recorded even if
   verified_payments=0 (expected: 0).
6. **Three Obsidian outputs** in the owner-board folder generated FROM the
   run receipts (not agent prose): ECONOMIC-LEARNING-CURRENT.md (with
   generated_at, code SHA, board/runtime SHA, counts, STALE/UNKNOWN markers),
   ECONOMIC-LEARNING-LEDGER.jsonl, ECONOMIC-LEARNING-QUEUE.md (every proposal
   in exactly one of PR_CREATED / QUEUED_WITH_REASON / REJECTED_WITH_REASON /
   ESCALATED_TO_OWNER). Only these paths staged in the vault.
7. Full suite green; independent PR; no self-merge; no WAL re-arm; no
   web/cockpit/self_model/kernel changes; no fake payments; no causation
   claims from single samples.

Valid end states: DONE | BLOCKED_BY_OWNER | BLOCKED_BY_CONFLICT | FAILED_WITH_EVIDENCE
