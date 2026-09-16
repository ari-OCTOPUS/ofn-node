# ARCH-LOOP-INPUTS — safe feeds for a 24h improve-architecture loop
**Stamp (AEST):** 2026-08-23T08:55:00+10:00  
**Purpose:** List math/files that already exist and are safe to read into an architecture-evolution loop.  
**Hard excludes for the loop:** money unlock · paid calls · git auto-push · force-push · live Telegram sendMessage · self-awareness / consciousness / phenomenal claims · WAVE0 physical mutate · inventing GPIO/PWM.

## Loop contract (safe mode)
- Mode: **propose-only** (RFC / outbox cards / evidence packs).
- Profile: treat as **paper-full** unless owner GO.
- Epistemics: **advisory-only** (`advisory_only=true`); never enforce.
- Doctor: bottlenecks → RFC; merge still human `[merge]` / `[reject]`.
- Output: evidence under `06-EVIDENCE/` + optional durable outbox `live_send=false`.
- Do **not** claim the organism is self-aware; `self_reference` is FUNCTIONAL relative self-modeling only.

## A) Math & metrics already on disk

| Input | Path | Why safe / how to use |
|---|---|---|
| Epistemics metrics math | `_ops\epistemics\metrics.py` | Real estimators; feed numbers, not narratives |
| Epistemics readers (topology live) | `_ops\epistemics\readers.py` | Levels/ident/channel/self_vs_twin samples |
| Epistemics contracts / MIN_SAMPLES | `_ops\epistemics\contracts.py` | Gate authoritative vs advisory |
| Off-loop runner | `_ops\epistemics\run_offloop.py` | Dry metric pack |
| Topology RESULT (27-node Laplacian) | `06-EVIDENCE\OCTOPUS-EPISTEMICS-TOPOLOGY-2026-08-23\RESULT.json` | algebraic_connectivity / spectral_gap / eigenvalues |
| Wire-on samples | `06-EVIDENCE\OCTOPUS-EPISTEMICS-WIRE-ON-2026-08-23\SAMPLES.json` | Advisory beat samples |
| Doctor spectral metrics | `_ops\doctor\spectral_metrics.py` | Spectral defs for doctor |
| Doctor criticality | `_ops\doctor\criticality_v2.py` | Criticality signals |
| MATH-ATLAS | `06-EVIDENCE\MATH-ATLAS.md` | Atlas pointer |
| Metaphor↔math dictionary | `06 - Architecture Maps\METAPHOR-MATH-DICTIONARY-v1.md` | Naming discipline |
| Budget YAML / state | `_ops\budget\budgets.yaml`, `_ops\budget\budget-state.json` | Caps / drawdown — **read-only**; do not arm money |
| Fisher / fitness | `_ops\budget\fisher.py`, `_ops\budget\fitness.py` | Optimization math without spend |
| Signals registry | `architecture\signals-registry.yaml` (+ schema) | Allowed signal vocabulary |
| Capabilities registry | `architecture\capabilities-registry.yaml` | Capability map |
| Hypothesis registry | `architecture\hypothesis-registry.yaml` | Propose experiments only |

## B) Topology / wiring / truth (structure inputs)

| Input | Path | Notes |
|---|---|---|
| Organ WIRING | `_ops\organs\WIRING.json` | Flags + OOB studio/money policy notes |
| wiring.py beats | `_ops\wiring.py` | `doctor_beat`, `doctor_uniqueness_beat`, `epistemics_beat` (advisory) |
| CURRENT-TRUTH | `OCTOPUS\CURRENT-TRUTH.md` | Human status; prefer over stale BLOCKER alone |
| Architecture SoT | `06 - Architecture Maps\ARCHITECTURE-SOT.md` | Large SoT map |
| Master architecture | `06 - Architecture Maps\MASTER-ARCHITECTURE-2026-07-29.md` | Historical master |
| Integration status | `06 - Architecture Maps\OCTOPUS-INTEGRATION-STATUS.md` | May lag; cross-check continuous mission |
| Continuous mission STATUS | `06-EVIDENCE\OCTOPUS-CONTINUOUS-MISSION-2026-08-23\STATUS.json` | PARTIAL truth of what already PASS |
| iOS TG contradiction scan | `06-EVIDENCE\OCTOPUS-IOS-CONTRADICTION-SCAN-2026-08-23\CONTRADICTIONS.json` | Label splits to fix in docs |
| Board2 contradiction scan | `06-EVIDENCE\BOARD2-CONTRADICTION-SCAN-2026-08-23\CONTRADICTIONS.json` | Money/photos — loop may only propose holds/drafts, not settle bank |
| This gap inventory | `06-EVIDENCE\OCTOPUS-GAP-INVENTORY-2026-08-23\GAPS.json` | Ranked backlog |

## C) Doctor bottlenecks (propose-only)

| Input | Path | Notes |
|---|---|---|
| Doctor core | `_ops\doctor\doctor.py` | `propose_rfc` / bottleneck objects |
| lab_bridge | `_ops\doctor\lab_bridge.py` | RFC→SUL→outbox propose-only |
| Uniqueness heartbeat | `_ops\doctor\uniqueness_heartbeat.py` | RO poller uniqueness |
| Uniqueness latest receipt | `_ops\state\doctor\poller-uniqueness-latest.json` | Soak health |
| Evelab wire RESULT | `06-EVIDENCE\OCTOPUS-EVELAB-DOCTOR-WIRE-2026-08-23\RESULT.json` | Contract for propose-only |
| Self-upgrade lab | `_ops\self_upgrade_lab\` | Verifier/promoter exist; **do not auto-promote** |
| Self-upgrade cycle pack | `06-EVIDENCE\SELF-UPGRADE-LAB-CYCLE-2026-08-21\` | Prior cycle evidence |

## D) Explicitly OUT of scope for this 24h loop
- Shopify payouts / bank / PayPal / ABN entry (owner noon / Maliheh).
- Paid LLM activation despite ACTIVATION-*.flag sprawl.
- git commit -a / push / auto-push; dirty tree is a **hygiene gap**, not a loop write target unless owner sparse-commit GO.
- live sendMessage / webhook mutation / WAVE0 MQTT open / physical estop purchase-as-PASS.
- Lowering epistemics MIN_SAMPLES to force “authoritative”.
- Any text claiming consciousness / transcendence / “self-aware OCTOPUS”.

## E) Suggested 24h loop agenda (propose-only)
1. **Doc/label reconcile:** supersede stale A18-BLOCKED-canary wording; keep inbound Full Loop separate (G04/G05).
2. **Architecture connectivity:** use Laplacian disconnect (G25) to propose organ-bridge RFCs (no live wire).
3. **Outbox topology:** propose single-SoT dashboard over loop/outbox vs event-bridge vs urgent (G08).
4. **Flag sprawl RFC:** map ACTIVATION-* vs writer-lock forbidden_actions vs paper-full (G17) — propose cleanup checklist only.
5. **MiniApp truth card:** reconcile `miniapp-url.json` vs env vs docs (G10) — no Telegram menu mutate without owner.
6. **Epistemics sample accrual plan:** natural cadence to raise channel/identifiability toward MIN_SAMPLES (G16) — no threshold cheat.
7. **Board2 hold proposals only:** draft/hold photo-incomplete SKUs language (G02) — no money unlock.
8. Emit evidence pack; leave merge to human.

## F) Success criteria (loop)
- ≥1 evidence pack with propose-only RFCs citing paths above.
- Zero paid calls; zero live sendMessage; zero git push.
- No self-awareness claims in outputs.
- Epistemics advisories (if any) stamped `advisory_only=true`.
- Dirty-tree size not increased by mass formatting (prefer sparse path writes).



<!-- G25-GAP-CLOSE-NOTE -->
## G25 note (gap-close 2026-08-23T09:14:00+10:00)
Laplacian algebraic_connectivity=0 / spectral_gap=0 is a topology fact. Propose organ-bridge RFCs only; do not claim self-aware OCTOPUS. Evidence: 06-EVIDENCE/OCTOPUS-GAP-CLOSE-2026-08-23/LAPTOP/G25/.
