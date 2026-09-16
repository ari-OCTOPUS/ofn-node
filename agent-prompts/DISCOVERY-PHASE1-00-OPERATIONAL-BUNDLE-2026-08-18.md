# DISCOVERY-PHASE1-00 — OCTOPUS World-Discovery Operational Bundle (index)
Created: 2026-08-18 · Status: READY · Supersedes: nothing (new capability)
Inputs consumed: council rounds 2026-08-17/18 ("Where Models Agree / Disagree / Unique Discoveries" — Kimi K3, GPT-5.6, Claude Opus 5), repo evidence through 2026-08-18, owner decisions D1–D15 (`06-EVIDENCE/sensorium-d14-verify-2026-08-18/OWNER-DECISIONS.md`).

---

## 1. WHAT THIS BUNDLE IS

The complete operational kit for **OCTOPUS multi-model discovery**: two competing models (Kimi, GLM) independently author read-only discovery runbooks for the four nodes; the owner captures passive evidence locally; a third merge-and-validation pass arbitrates the two model outputs into consensus runbooks without ever promoting model agreement into evidence; the results feed the generated sole-truth document `docs/NOW.md`; and GAP-001's executable closure is verified by script, not by prose.

## 2. FILE MAP

| File | Role |
|---|---|
| `agent-prompts/DISCOVERY-PHASE1-01-MEGAPROMPT-DISCOVERY-2026-08-18.md` | **Phase 1** mega-prompt (Kimi + GLM, one device per call) |
| `agent-prompts/DISCOVERY-PHASE1-02-NOW-SPEC-2026-08-18.md` | `docs/NOW.md` exact schema: sections 0–19, `identity_health`, `self_accuracy`, 10 generation rules |
| `agent-prompts/DISCOVERY-PHASE1-03-MERGE-VALIDATION-PROMPT-2026-08-18.md` | **Phase 3** merge-and-validation prompt (field_id join, V1–V10, anti-promotion) |
| `agent-prompts/DISCOVERY-PHASE1-04-ARBITRATION-CONFLICT-MATRIX-2026-08-18.md` | Conflict-resolution matrix A1–A15 for Agree/Disagree/Unique council output |
| `agent-prompts/DISCOVERY-PHASE1-05-COMMAND-POLICY-2026-08-18.md` | Binding whitelist/blacklist for LAPTOP-191, BOARD-138, BOARD-182, BOARD-180 |
| `agent-prompts/DISCOVERY-PHASE1-06-GAP001-CLOSURE-VERIFY-2026-08-18.md` | GAP-001 executable-closure doctrine + workflow |
| `_ops/world_discovery/gap001_closure_verify.ps1` | GAP-001 verifier script (read-only, manifest-driven) |
| `_ops/world_discovery/gap001-criteria.manifest.json` | GAP-001 closure criteria manifest |
| `_ops/world_discovery/schemas/discovery-evidence.v1.schema.json` | **Frozen** field_id taxonomy (46 ids) + evidence envelope schema — the join key for everything |
| `_ops/world_discovery/schemas/now-input-manifest.v1.schema.json` | NOW.md input manifest schema (runbook prose forbidden as NOW input) |

## 3. EXECUTION ORDER

```
Phase 0  (done)  freeze schemas + field_ids BEFORE any prompting          [§ this bundle]
Phase 1  prompts  01 per device × {Kimi, GLM}  → 06-EVIDENCE/world-discovery/phase1/{KIMI,GLM}-RUNBOOK-<device>.md
Phase 2  owner    run P0 evidence capture yourself (policy file 05), starting with the laptop block;
                 real evidence pasted into later prompts kills the hallucination surface
Phase 3  prompt   03 per device-pair → merged runbooks + CONTRADICTIONS/UNKNOWN/REJECTED/EVIDENCE-MAP
                 + NOW-INPUT-MANIFEST + FACT-PACKs (save under 06-EVIDENCE/world-discovery/phase3/)
Phase 4  generate docs/NOW.md per spec 02 (manifest inputs only, ten generation rules)
Phase 5  verify   GAP-001 closure script (file 06) whenever the signed checkpoint lands;
                 expected verdict until then: PENDING_OWNER_SIGNATURE
```

## 4. BINDING GOVERNANCE (restated everywhere, owner-decidable nowhere in this bundle)

`WAVE0_OBSERVE_ONLY · L2_ARMED propose-only (may_authorize=false, autonomy_delta=0) · actuator NONE · legs DENIED · MQTT DISABLED · BOARD-180 activation OWNER_APPROVAL_REQUIRED · scheduler zero-interaction (reads included) · GO_FOR_INSTALLATION=false while wave = WAVE0`

Node map (roles CLAIMED from repo evidence until Phase-2 evidence confirms): LAPTOP-191 `DESKTOP-KA9RFN5` brain/vault · BOARD-138 Feet (silent since 2026-08-16, wire b003 down) · BOARD-182 Sensorium (Orange Pi 5 Pro, Armbian, NATS) · BOARD-180 A2 lab, continuity candidate, **zero proven edges, zero commands**.

## 5. OPEN OWNER QUESTIONS (block stage-2; recorded, not decided, by this bundle)

1. **YELLOW semantics** for the W3/GREEN-counter: does YELLOW zero the consecutive-day counter or only invalidate that day? (`OWNER_DECISION_REQUIRED` — enforced in files 01/03/04.)
2. **BOARD-138 reflex latency budget**: numeric max response time with no laptop and no internet.
3. **Canonical repository**: which repo is canonical, and do boards clone it or only receive artifacts.
4. **GAP-001 formalization** (defined, pending signature): produce the signed checkpoint per DISCOVERY-PHASE1-06 §4; current script verdict `PENDING_OWNER_SIGNATURE`.

## 6. RELATIONSHIP TO EXISTING SYSTEMS

- Evidence envelopes extend the VERIFIER-series envelope contract (`agent-prompts/MEGAPROMPT-VERIFIER-00-SHARED-CONTRACT-2026-08-18.md`): same no-claim-without-witness discipline, now with frozen field_ids so merge = join.
- Contradictions surfaced by Phase 3 register in `01-TRUTH/CONTRADICTIONS.md` (next free id: C-035 — C-034 allocated).
- NOW.md supersedes no truth file; it is the generated view layer over `01-TRUTH/` + `06-EVIDENCE/`.
- The GAP-001 verifier is laptop-side only and cannot touch board ledgers — board-side agents never hand-edit gap ledgers (D5).
