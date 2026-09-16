# DISCOVERY-PHASE1-02 — docs/NOW.md Specification (Sole-Truth Operational View)
Bundle: OCTOPUS World-Discovery Phase 1 · 2026-08-18 · Status: READY
Schemas: `_ops/world_discovery/schemas/discovery-evidence.v1.schema.json`, `now-input-manifest.v1.schema.json`

---

## 1. PURPOSE AND AUTHORITY

`docs/NOW.md` is the **generated, single, current-truth operational view** of the OCTOPUS ecosystem. It is a *view over evidence*, never an independent source of facts.

- `manual_editing_allowed: false` — permanent. Hand-edits are detected by digest mismatch against the recorded output hash and force regeneration.
- **Regenerated whole, never patched.** Each generation starts from zero and rebuilds every row from the input manifest.
- Its only inputs are artifacts listed in a manifest conforming to `now-input-manifest.v1.schema.json`. **Runbook prose and model chat output are never valid inputs.** This closes the leak where model-authored text quietly becomes system truth.
- In D0 it always ends `GO_FOR_INSTALLATION: false`. NOW.md computes GO from gate results in a table, never from narrative prose.

## 2. YAML FRONTMATTER (exact fields, every generation)

```yaml
---
doc: NOW
schema: octopus:world_discovery:now:v1
generated_at_utc: 2026-08-18T12:00:00Z        # UTC ISO-8601, always
generator:
  name: <generator script or agent id>          # e.g. agent://octopus/laptop-brain/main
  version: <semver or commit hash>
  sha256: <digest of the generator itself, or null + reason>
input_manifest:
  path: _ops/world_discovery/now/NOW-INPUT-MANIFEST-<ts>.json
  sha256: <digest of the manifest file>
output_sha256: null                             # filled post-write by the harness step
previous_now:
  path: docs/NOW.md | null
  sha256: <digest of previous output | null>
manual_editing_allowed: false
wave: WAVE0_OBSERVE_ONLY
autonomy: L2_ARMED_propose_only
actuator_authority: NONE
mqtt: DISABLED
board_180_activation: OWNER_APPROVAL_REQUIRED
go_for_installation: false                      # hard constant while wave = WAVE0_OBSERVE_ONLY
---
```

## 3. STATUS VOCABULARY, FRESHNESS, PRECISION

Status enum and freshness windows are the frozen ones from `discovery-evidence.v1.schema.json` (10 statuses; windows PT1H/PT24H/P7D/P30D/PINNED_TO_EVENT/UNKNOWN).

Freshness policy by field class (a VERIFIED row past its window auto-relabels `STALE` at generation time and its truth weight drops accordingly):

| Field class | Window |
|---|---|
| time.*, network.neighbor_cache, network.listening_* | PT1H |
| network.ip_addresses, ssh.*, svc.service_inventory, laptop.hourly_backup_status | PT24H |
| identity.*, git.*, config.*, checkpoint.*, reflex.*, w3.* | P7D |
| board180.power_target, execution.credential_handles, laptop.vault_root | PINNED_TO_EVENT (change only on new owner decision / event evidence) |
| everything else | UNKNOWN ⇒ treat as PT24H (conservative) |

Advisory precision weights (used only by the Active-Inference shadow in §9 — they never promote a status):

`VERIFIED_FRESH 1.00 · OWNER_DECISION 0.90 · TEST_VERIFIED 0.85 · GIT_CONFIG 0.70 · VERIFIED_STALE 0.35 · CLAIMED 0.20 · UNKNOWN/CONTRADICTED/BLOCKED/UNKNOWN_BY_POLICY/NOT_APPLICABLE 0.00`

## 4. FIELD ROW SCHEMA (every factual row in every table)

| Column | Rule |
|---|---|
| `field_id` | From the frozen schema. No local ids. |
| `value` | The fact, or `UNKNOWN`/`BLOCKED:<reason>`. |
| `status` | One of the 10 statuses. |
| `source_artifact` | Path from the input manifest. Mandatory for VERIFIED/TEST_VERIFIED/OWNER_DECISION. |
| `source_sha256` | Digest of that artifact. **A VERIFIED row without artifact+digest is automatically downgraded to CLAIMED at generation time.** |
| `observed_at_utc` / `verified_at_utc` | ISO-8601 UTC. Local time is never written. |
| `verification_command_id` | Step id from DISCOVERY-COMMAND-PLAN, or `NONE` (e.g. scheduler). |
| `freshness` | Window + computed age (`age: PT##H##M`); relabels STALE when expired. |

## 5. STATE VARIABLES

Two computed state variables live in frontmatter-adjacent block `state:` and are rebuilt every generation. Both are **advisory shadow quantities in Wave 0: they may inform, never gate actuators, never authorize, never issue commands.**

### 5.1 `identity_health`
- Domain: `HEALTHY | DEGRADED | UNVERIFIED | CONTRADICTED`
- Per node (`.191`, `.138`, `.182`, `.180`) — computed from: hostname/label consistency across sources, SSH host-key pin state, board_id match, checkpoint chain status, role_claim agreement with repo records.
- Rules: any contributing field `CONTRADICTED` ⇒ node = CONTRADICTED. Any required identity field `UNKNOWN` ⇒ UNVERIFIED. `STALE` contributors ⇒ DEGRADED. All contributors VERIFIED/TEST_VERIFIED fresh ⇒ HEALTHY.
- `.180` is `UNVERIFIED` by construction while `board180.power_state = UNKNOWN` (governance target OFF is not runtime identity).

### 5.2 `self_accuracy`
- Domain: float `[0.00, 1.00]` + `sample_size` + `window` (e.g. `0.86, n=14, P7D`); `null` until first calibrated window.
- Definition: 1 − (mean |prediction_error| / scale) over the §9 homeostatic metrics that have predictions recorded in the window, weighted by each metric's precision.
- Honesty rules: fewer than 5 scored predictions in the window ⇒ report `null` with `reason: INSUFFICIENT_SAMPLE`. A CONTRADICTED input field zeroes its contribution's weight, never inflates accuracy by being ignored. `self_accuracy` may never be computed from runbook prose or model claims — only recorded prediction-error pairs.

## 6. SECTION STRUCTURE (0–19, fixed order, fixed ids)

| § | Section | Required content |
|---|---|---|
| 0 | Governance Snapshot | The binding header values (wave/autonomy/actuator/mqtt/.180) + `state:` block (`identity_health` per node, `self_accuracy` with n/window) |
| 1 | Node Identity Matrix | `identity.*` rows, all four nodes |
| 2 | Time & Clock State | `time.*` incl. drift vs laptop-191; notes AEST operator ↔ UTC storage rule |
| 3 | Network State | `network.*` rows (cache ages explicit) |
| 4 | SSH Surface | `ssh.*` rows; host-key pin state; dropbear/openssh status |
| 5 | Git / Canonical Repository | `git.*` rows (remote URL redacted form only) |
| 6 | Config Inventory | `config.*` metadata + hashes; key names, never values |
| 7 | Services (non-scheduler) | `svc.service_inventory`; **`svc.scheduler` shown as UNKNOWN_BY_POLICY, verification_command NONE** |
| 8 | Checkpoints & Gaps | `checkpoint.*`; `checkpoint.gap_001_state` with the ledger disambiguation note (board checkpoint ledger ≠ Telegram-redesign GAP-001 homonym) |
| 9 | Homeostatic Snapshot (Active-Inference shadow) | Per metric: value, setpoint, `prediction_error`, `precision`. Header rule: *this section may compute; it must never issue actuator/MQTT/BOARD-180 commands; executable=false always in Wave 0* |
| 10 | Capability Matrix | Device × capability; explicit `FORBIDDEN` rows: Active Inference on BOARD-138 reflex and on BOARD-180; reflex = deterministic FSM/threshold only |
| 11 | Contradiction Register (summary) | Count + open ids, linked to `01-TRUTH/CONTRADICTIONS.md` (next free id rule C-0xx) |
| 12 | Unknown Register (summary) | Field, why, resolving evidence, obtainable-in-D0? |
| 13 | Evidence Freshness Table | Per input artifact: digest, collected_at, age vs window |
| 14 | Owner Decisions In Force | Only valid binding records (e.g. OWNER-DECISIONS.md D1–D15 with digest) |
| 15 | Safety State | `.180` power_target/power_state/proven_edges; scheduler status; secrets-in-outputs = CLEAN |
| 16 | Changes Since Previous NOW | `NEW / CHANGED / RESOLVED / REGRESSION / STALE` per field + `safety_impact` column (yes/no). Regressions may not be silently overwritten — they persist until explicitly RESOLVED |
| 17 | Session Closure | agent-checkpoint status, test suite status (counts), exactly one `NEGATIVE_MEMORY:` line (the session's worst gotcha) |
| 18 | Open Gates / Owner Questions | The blocking questions (see DISCOVERY-PHASE1-00 §4) with status |
| 19 | Generation Validation | The self-audit below, filled with actual yes/no + exceptions |

## 7. THE TEN GENERATION RULES (sole-truth validation — the generator must pass all ten)

1. **Canonical inputs only** — every row traces to an entry in NOW-INPUT-MANIFEST; no runbook prose, no model chat, no memory.
2. **No runtime probes during generation** — generating NOW.md launches zero commands at any node; it reads captured artifacts only.
3. **Full regeneration** — no section is carried over by copy-paste from a previous NOW.
4. **VERIFIED requires digest** — artifact + sha256 or automatic downgrade to CLAIMED.
5. **Auto-STALE** — expired freshness windows relabel STALE at generation time; stale fields keep their history visible in §16.
6. **Secret scan pre-write** — a scanner pass over the rendered document; any hit aborts the write (document is quarantined, not published).
7. **Contradictions preserved** — CONTRADICTED rows render with both values and both sources; generation never resolves a contradiction by choosing a side.
8. **GO computed from gates** — any GO/NO-GO verdict comes from a gate table with per-gate pass/fail, never from narrative.
9. **`GO_FOR_INSTALLATION: false` always in D0** — the generator cannot set it true while `wave: WAVE0_OBSERVE_ONLY`; a change requires a new owner-signed wave record as a manifest input.
10. **Hashes recorded** — the generator's own digest (or documented null+reason) and the output digest are written into frontmatter immediately after the write; a subsequent hand-edit makes the file fail verification against `output_sha256`.

## 8. §19 GENERATION-VALIDATION SELF-AUDIT (template, filled per run)

```
[a] no hand-edit of previous NOW:            yes/no
[b] every field sourced from manifest:        yes/no (+ exceptions list)
[c] zero secrets in rendered output:          yes/no
[d] no guessed UNKNOWN->value promotions:     yes/no
[e] all VERIFIED rows carry artifact+digest:  yes/no (count downgraded: N)
[f] all timestamps UTC ISO-8601:              yes/no
[g] contradictions preserved (not resolved):  yes/no (ids: ...)
[h] no authority escalation in any section:   yes/no
[i] scheduler fields UNKNOWN_BY_POLICY:       yes/no
[j] GO computed from gate table only:         yes/no
[k] freshness applied / STALE relabel count:  N
[l] generator+output hashes recorded:         yes/no
```

Any `no` ⇒ the generation is invalid: do not publish; quarantine the rendered file; the failure reason becomes a §18 open-gate entry.

## 9. RENDERING CONTRACT (machine-readability)

- Header comment `<!-- now:v1 digest-check:output_sha256 -->` on line 1 for tamper detection tooling.
- Every factual table renders as a Markdown table whose first column is `field_id` — parseable with a fixed column set (§4).
- Mermaid allowed only in §10 (capability graph) and §15 (emergency flow with explicit negative edges: `no laptop dependency`, `no internet dependency`, `no LLM` on the BOARD-138 reflex path).
- File path: `docs/NOW.md` (single current file). Prior generations move to `docs/now-archive/NOW-<UTC-ts>.md` with their manifests; nothing is deleted.
