# 04_CONTRADICTIONS — A03 (2026-08-16)

## C-1 · "The ledger is live and bitemporal"
- **Documented:** project claims bitemporal ledger.
- **Observed:** genome ledger = hash-chained, append-only, fsync, **single `ts`** (record
  time only). Four SQLite stores have `occurred_at`+`recorded_at` columns but every producer
  sets both to "now" (spine publish default), so the duality is never exercised. MemoryStore
  has valid-time windows (different concept). The word "bitemporal" appears once, in a
  research note about a paper (TOKI), as aspiration.
- **Resolution:** claim is **half-true**: live + tamper-evident = yes; bitemporal = no.
- **Severity:** MEDIUM (epistemic hygiene — self-model may believe a capability it lacks).

## C-2 · "A2 actions are bounded automatic actions"
- **Documented:** A2 = bounded automatic.
- **Observed:** `DECISION_BY_CLASS["A2"] = "BLOCK"` — explicitly until governance vote
  VQ-SELFGOAL-002 lands (classifier.py:176-184); integration.py `still_closed` repeats it.
- **Resolution:** **contradicted in the safe direction** (stricter than documented). Docs stale.
- **Severity:** MEDIUM (docs misrepresent capability — in this case overclaiming autonomy that does not exist).

## C-3 · "Actions are propose-only"
- **Documented:** all actions propose-only.
- **Observed:** true inside action_bridge (only A0/A1 executable). But the lead email lane
  (`outbound_worker` → SMTP) performs real external sends after per-effect owner
  authorization (armed by recorded owner vote 2026-07-31); supervisor can restart processes;
  4d `self_code.approve` applies code after owner click.
- **Resolution:** **contradicted as a universal statement**; correct form: "autonomous
  proposals are propose-only; owner-armed lanes execute under their own gate stacks."
- **Severity:** MEDIUM.

## C-4 · "Sensorium is active; legs are unauthorized"
- **Observed:** no Sensorium (0 hits repo-wide); afferent path = rule-based stub ingesting
  *internal* aggregate labels; legs exist as code, and one leg lane (lead email) is
  owner-armed. "Unauthorized legs" is not accurate for the email lane (authorized by vote).
- **Resolution:** **contradicted/stale terminology**.
- **Severity:** MEDIUM.

## C-5 · "Governance is mutual veto (two brains)"
- **Observed:** dual_brain.py implements it, but the mission bridge passes the 4d brain as
  PENDING ("not yet connected W2+"), so when the veto flag is on, missions would hold on a
  non-vote rather than a genuine second brain's judgment.
- **Resolution:** **partially implemented** — one-brain + owner, not two-brain.
- **Severity:** LOW-MEDIUM.

## C-6 · "Policy Gate and Viability Loop are runtime-enforced"
- **Observed:** two policy systems. action_bridge ladder = enforced in the live mission
  path. 4d control_plane ladder = observe-only, evaluate() never called from execution
  paths, live flags default-off. Viability loop = live with honest FAIL verdicts.
- **Resolution:** **true for action_bridge + test_cycle; false for 4d control_plane**.
- **Severity:** LOW-MEDIUM (audit ambiguity risk).

## C-7 · "Money is locked and destructive actions disabled"
- **Observed:** A5 (money/contract) has **no executor function**; `paid_api_call`=A5;
  paid LLM paths are budget-capped elsewhere (llm router/budget modules exist, flagged);
  email lane forbids spend; FREEZE.flag present in budget dir; destructive 4d actions
  require approval + rollback per policy ladder.
- **Resolution:** **consistent at the action layer** (not fully audited at every paid-API
  client — llm router budget enforcement not line-audited by A03; see open questions).
- **Severity:** LOW (residual) — assign to A02/A04.

## C-8 · Naming collision: `knowledge/ledger.py` is not a ledger
- **Observed:** `4d_system/knowledge/ledger.py` is a read-only prompt-reference loader
  ("READS from 4D/ but NEVER writes").
- **Resolution:** benign, but any audit or doc saying "the ledger" must disambiguate among:
  genome ledger, action-ledger.jsonl, missions.jsonl, spine.db, knowledge/ledger.py.
- **Severity:** LOW.

## C-9 · "memory affects reasoning" — consistent, with an asymmetry wrinkle
- **Observed:** verified live (veto, prompts, dedup). No contradiction. But the *write*
  discipline differs by side (gated in _ops, ungated in 4d), which docs do not mention.
- **Severity:** LOW.
