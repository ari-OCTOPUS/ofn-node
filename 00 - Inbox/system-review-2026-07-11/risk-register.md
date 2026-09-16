---
type: report
status: draft
tags: [risk, register, security, governance, ops, handoff]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[00 - Inbox/system-review-2026-07-11/architecture-review]]"
  - "[[06 - Architecture Maps/2027 Standards Base & Backlog]]"
  - "[[01 - Dashboard/HANDOFF]]"
---

# Risk Register — READ-ONLY (2026-07-11)

> Proposal artifact. No fix applied. Severity = impact × likelihood for a single-operator local-first system. Each risk maps to a backlog item (`implementation-backlog.md`) and, where owner-only, to a decision (`user-decision-packet.md`).

| ID | Risk | Sev | Evidence | Reversible? | Mitigation (proposed, NOT applied) | Owner-only? |
|---|---|---|---|---|---|---|
| **R1** | `is_human=1` forgeable → fake "human" verdict advances genome mortal age-tick | **HIGH** | `FACT` `human_append_guard.py:78-80` fail-open when no secret; default guard = `HumanAppendGuard(None)` | yes | Owner#1: additive `strict=False` param + `HH_HUMAN_GUARD_STRICT` env → unconfigured = DENY. HMAC path untouched. Shadow-alert variant available first. | approve (touches `_ops/budget/`) |
| **R2** | No live money kill-switch; drawdown breaker is test-only | **HIGH** | `INFER` `spike_pct=25` only test-asserted (Owner#4) | yes | Owner#4: enforcer reads same drawdown, behind `HH_DRAWDOWN_ENFORCE`, **shadow-count first** (log would-halt) | approve (near money) |
| **R3** | Git backups/pushes silently broken by stale AV `.git` locks; 113 dirty live entries | **HIGH** | `INFER`(memory/HANDOFF) chronic `HEAD.lock` false-locks; RUN-CLEANUP never run on live | yes (owner) | Owner clears `F:\backup\.git\*.lock`; run `_ops/maintenance/RUN-CLEANUP-2026-07-11.bat`; gitignore runtime projections | **owner-only** (agent denied `.git`/live-business writes — correct) |
| **R4** | Append-only logs (events.jsonl, …) grow unbounded → retrieval/perf decay | MED | `INFER` no consolidation (Owner#7) | yes | Owner#7: `cortex/consolidate.py` (recency×importance×relevance → bounded semantic note; archive-not-delete), flag `CORTEX_CONSOLIDATE` | notify (additive/$0) |
| **R5** | Self-model claims not externally graded → overconfidence | MED | `INFER` self_model offline/AST only (Owner#5) | yes | Owner#5: `online_calibration_probe()` graded vs external ledgers (Brier/AURC), flag `CORTEX_SELF_MONITOR` | notify |
| **R6** | Cost attribution unreliable — 47 governor errors from unlocked `price_in/price_out` | MED | `INFER`(HANDOFF ~13:00) budgets.yaml missing locked prices | yes | Lock `price_in/price_out` per role in budgets.yaml (your data/rates) | approve (money config, your numbers) |
| **R7** | HANDOFF.md = 1015 lines → violates own 200-line index cap; onboarding/observability debt | MED | `FACT` read 1015 lines / 123k tokens | yes | Additive: split into `HANDOFF.md` (last ~5 sessions, wikilinks) + `_Archive/Logs/HANDOFF-archive-2026.md` (older). Move, never delete. | notify |
| **R8** | ~20 tests use Windows raw paths → fail on Linux/sandbox CI | LOW | `INFER`(Owner#9) e.g. `test_leg.py:25` `r"_ops\legs"` | yes | Owner#9: `REAL_VAULT / "a" / "b"` (portable joins) + py3.12 f-string fix in test_dashboard | notify |
| **R9** | `debate` `KeyError:'text'` runtime bug | LOW | `INFER`(HANDOFF ~13:00, registered) | yes | Scoped fix + regression test (needs repro) | notify |
| **R10** | Anti-black-box invariants (delegation depth ≤2, "no write without event/state") are conventions, not enforced | MED | `INFER` not verified in code this session | n/a | Add a lightweight assert/lint (depth counter in workflow harness; event-emit guard) — shadow first | notify |
| **R11** | Many capabilities built but shadow/flag-gated, never promoted → capability debt / drift between "built" and "live" | LOW-MED | `FACT`(docs) precision-weight, soft-WTA, HeartState telemetry, incident-wiring all shadow | yes | Decision D4: choose which to promote; each promotion is its own shadow→canary→live gate | approve per-item |

## Cross-cutting observations

- **Your safety design is why every red is *reversible*.** Nothing here is a smoking crater; the gaps are "not-yet-closed," not "broken." That is a direct dividend of the additive/shadow/flag discipline.
- **R1 + R2 + R3 are the only HIGHs**, and all three are already known to you (R1/R2 in the 2027 doc, R3 in memory/HANDOFF). The value I add is *ranking + staged closure*, not discovery.
- **R3 is the one you should not defer**: a control plane whose own git backup is silently wedged is one disk event away from real loss, and by design I cannot fix it (I'm correctly denied `.git` writes).
