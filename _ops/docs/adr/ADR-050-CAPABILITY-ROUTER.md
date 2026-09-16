# ADR-050: Capability Router — Structural Tasks Never Reach the Model

## Status: ACCEPTED (2026-09-07, MP-FIX-01 F5)

## Context

ACD-01 and ACD-07 proved that qwen-0.6b on board 180:
- Simple extraction: 33% pass^5 (4/12 instances all-5-pass)
- Corrupt tool output: 54% fabrication rate
- Nested extraction: 0/6
- Never abstains on missing fields (0/15 in scaffold B)
- 100% fabrication on stale data and content injection

The code-guard pattern (deterministic validation in code) has two independent
witnesses (U1 sensors + ACD-01) plus a third from ACD-07 (54% vs 0% with guard).

## Decision

A `capability_router` module classifies tasks:
- **Structural tasks** (extraction, validation, presence, abstain, hash, freshness,
  units, contamination) → ALWAYS routed to deterministic code. NEVER to model.
- **Model tasks** (understanding, choice, synthesis, communication) → routed to brain.
- **Unknown tasks** → fail-closed to code.

## Consequences

1. The weak 0.6b brain is only used where it's actually needed (understanding/choice).
2. All data-touching paths have deterministic guards (INV-TOOL-GUARD).
3. Model upgrade becomes optional (better brain improves quality, not correctness).
4. This ADR is the architectural foundation for the three-role system (Cortex/Spine/Limbs).

## Evidence

- ACD-01: FAMILY-VERDICT + amendments (silent NOT_REFUTED, extraction 0.75 pass per-attempt)
- ACD-07: Arm-D validator 13/13 deterministic, Arm-M 54% fabrication
- U1: stress.v2 in production, data_quality visible
- SKILL-TOOL-GUARD-V1: transferred to U2 with 27/27 tests
