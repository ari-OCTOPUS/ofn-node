# Safety Model — defense-in-depth (L8 control plane)

_Consolidates the 7 Guards, the effect/cognition split, and the 5 independent safety layers. Evidence: A (DOC-02 guards) + B/C (TINV gates) + Master Handoff §5. See also `IsolationModel.md` for the CFL-03 deep-drill._

## Posture

Assume every component and every LLM call can be wrong, confused, or adversarially manipulated. Make that **safe by construction, not by trusting judgment** `[SOLID]`. Default-deny: an action is denied unless a guard explicitly allows it.

## The 7 Guards (default-deny middleware)

Each guard intercepts an event and returns `allow` / `deny` / `queue-for-cooldown`, as a function of **(action class × operating Mode × autonomy level)**. Strictness tightens automatically in low-energy / offline / impulsive modes (INV-15).

| Guard | Rule | Atom | Safety-rel |
|---|---|---|---|
| **Truth** | No write to canonical without snapshot + event; LLM/Telegram output is never truth | AKO-003 | 95 |
| **Money** | money/crypto/credential/external-msg/delete = irreversible class → approval + cooldown; Offline → freeze | AKO-004 | 100 |
| **State** | impulsive/high-energy → irreversible decisions enter cooldown; low-energy → minimums only | AKO-005 | 90 |
| **Autonomy** | every event carries `autonomy_level`; level > domain ceiling → halt, await approval | AKO-006 | 90 |
| **Evolution** | Evolution Doctor is sandbox-only; no merge to prod without diff + test + human approval | AKO-007 | 95 |
| **Worker** | worker sees only an isolated `task_packet`; no canonical/credential/PII | AKO-008 | 90 |
| **Non-Destruct** | nothing deleted; deprecate + version to `/_legacy` | AKO-009 | 85 |

## Effect / Cognition split (PAT-09 / AKO-026)

On operator absence: **irreversible EFFECTS freeze; internal COGNITION/aging MAY continue (bounded)**. This resolves the stasis-vs-24/7 conflict (CFL-01). Canon verdict still owed (**OQ-1**) — treat as the default and flag if the operator overrides.

## The 5 independent safety layers

1. **Kill-switch** — always live; any safety warning halts the relevant automation and logs it.
2. **Cost-cap** — economic brake above everything; budget breach freezes effects (INV-07); `cgroups v2` enforces it structurally.
3. **TINV-7 effect-gate** — no `send/publish/sync` settles without a LANGAR append (INV-01).
4. **Human anchor** — root-of-trust; irreversible/sensitive effects require a human append (§ human-approval gates below).
5. **Epistemic gap-report** — every synthesis names what is missing/uncertain (INV-16); breaks agreement-spiral.

## Human-approval gates (always human, never auto)

money movement · deletion/irreversible migration · public publishing · credential change · production deploy/merge · long-running autonomous workflows · any system self-modification. The system may PREPARE a proposal; the human makes the call `[SOLID]`.

## Residual risks (accepted, not eliminated)

- **R1 model-layer injection** — a worker can still emit a *convincingly wrong* proposal; caught by human review + Critic, not eliminated.
- **R2 shared-silicon side-channels** — process isolation does not remove timing/cache channels on shared hardware.
- **CFL-03 isolation** — reduced to `[EST]` process-level design (see `IsolationModel.md`); never claim "solved."
