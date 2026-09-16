# `_ops/chord` — Chord Filter v0 (SHADOW ONLY)

**What this is.** A small, deterministic, evidence-first decision-geometry module for the
Evolutionary Doctor and every self-healing subsystem. It turns observations (logs, tests,
LLM-extracted summaries) into a normalized state vector, measures the weighted Euclidean
gap between actual and target state, models uncertainty, and emits an **advisory** verdict:

`HEALTHY · OBSERVE_MORE · PROPOSE_PATCH · REQUEST_APPROVAL · BLOCK · UNKNOWN`

**What this is NOT.** Not a proof of consciousness/intelligence, not a psychology tool,
not an execution engine, not a bypass of approval gates. The human-language /
self-understanding research lives separately in `03 - Projects/Chord/` behind mandatory
evidence labels (`established/supported/hypothesis/speculative`).

## Math

```
d(x, x*) = sqrt( Σ_i w_i (x_i − x*_i)² / Σ_i w_i )   ∈ [0,1]
```

8 dimensions, all normalized to [0,1] (`schemas.DIMENSIONS`): evidence_quality,
test_health, goal_alignment, operational_risk, reversibility, cost_budget, uncertainty,
dependency_health. Direction of "good" is encoded in targets (risk→0, evidence→1 …).
Default weights favor risk and evidence over everything an LLM merely *says*.

## Safety by construction (mirrors `_ops/epistemics`)

- **Off-loop.** Imports nothing from `organism.py` / `center.py`. Nothing imports it yet.
- **Own ledger only.** Appends to `_ops/chord/state/chord-ledger.jsonl`
  (hash-chained `prev_sha256`, dedup_key idempotency; `CHORD_STATE_DIR` overrides in tests).
  Never touches financial ledger or organism state.
- **Models are advisors.** `adapters/llm_adapter.py` goes through the organism's single
  door `cortex.model_router.ask` (local-first Qwen/Ollama → Fugu), demands strict JSON,
  validates deterministically, caps LLM evidence_strength at **0.5**, and returns an
  honest `(None, reason)` on malformed output or offline — which upstream becomes
  `UNKNOWN`, never "healthy".
- **Missing evidence = UNKNOWN** (`uncertainty_gate`): coverage < 0.35 → UNKNOWN;
  < 0.60 or any contradiction or uncertainty > 0.6 → OBSERVE_MORE, auto-repair closed.
- **Important class is structural** (`repair_policy`): money/secrets/destructive/external
  side effects/genome/credentials/irreversible → always REQUEST_APPROVAL, regardless of
  distance. `allowed_actions` can never contain `code.apply`/`code.patch`/`money.move`…
  (filtered against `SAFE_ACTIONS`, aligned with mission_runner's allowlist).
- **Fail-closed blocks:** kill-switch context or secret-tainted observation → BLOCK.
- **Telegram is a thin surface.** `adapters/telegram_cards.py` only renders strings;
  wiring into `center.py` is a separate serial-lane worktree change behind the (unset)
  flag `OCTOPUS_WIRE_CHORD`, owner-gated.

## Integration contract (when the owner votes to wire)

```python
from chord.adapters.doctor_adapter import shadow_assess
rec = shadow_assess(mission_id, observations, dim_claims, context)
# rec["verdict"] is advice. Doctor keeps its own gates. Nothing here executes.
```

## Tests

`python -X utf8 _ops/tests/test_chord.py` — 30/30 green (sandbox py3.10; portable paths,
no REAL_VAULT). Covers: known-value math, clamps, negative weights, no-evidence→UNKNOWN,
contradictions, high risk/low reversibility→approval, money context→approval,
kill-switch/secret→BLOCK, malformed LLM JSON, offline honesty, strength cap, hash-chain +
dedup, shadow_assess side-effect boundary, card rendering.

## Activation ladder (owner votes at every step)

1. **Now:** shadow only — callers may compute+log, nothing reads verdicts.
2. **Phase C (next agent, worktree):** doctor calls `shadow_assess` per RFC/mission and
   *records* chord verdicts next to its own decisions (no behavior change).
3. **Evaluate:** after ≥2 weeks of paired records, check whether chord verdicts predicted
   real outcomes (test failures, rollbacks, wasted spend) better than baseline.
4. **Only then:** owner may flip `OCTOPUS_WIRE_CHORD=1` to let verdicts gate low-risk
   auto-repairs. Money/LIVE stays P7, owner-only, forever out of chord's authority.

Spec (FA): `04 - Architect System/CHORD — معماری فیلترِ وتر (v0).md`
Discovery: `04 - Architect System/ANALYSES/2026-07-18_CHORD-DISCOVERY.md`
Next-agent prompt: `04 - Architect System/octopus-build-prompts/CHORD-AGENT-PROMPT-2026-07-18.md`
