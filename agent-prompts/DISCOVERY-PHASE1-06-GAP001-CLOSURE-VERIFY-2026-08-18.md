# DISCOVERY-PHASE1-06 — GAP-001 Executable Closure Verification
Bundle: OCTOPUS World-Discovery Phase 1 · 2026-08-18 · Status: READY (expected verdict today: `PENDING_OWNER_SIGNATURE`)
Artifacts: `_ops/world_discovery/gap001_closure_verify.ps1` + `_ops/world_discovery/gap001-criteria.manifest.json`

---

## 1. WHAT GAP-001 IS (canonical, disambiguated)

**GAP-001 (board checkpoint ledger)** = the readiness gap on the board's checkpoint ledger: reboot-recovery evidence incomplete. Canonical record — `06-EVIDENCE/sensorium-d14-verify-2026-08-18/OWNER-DECISIONS.md` **D5**:

> "Closure criteria met (2 consecutive software-reboot PASS, new boot_ids, gates_failed=[]). Record as CLOSED with the standing rider POWER_LOSS_UNTESTED. To be formalized by the owner in the next signed checkpoint (board-side agent does not hand-edit gap ledgers)."

Live payload (`msg-evidence-latest.json`): `gaps.GAP-001 = { boot_id: 4dbf4819-…, readiness: READY }`, `readiness.gates_failed: []`, `readiness_state: READY`.

**Homonym warning (registered contradiction, custodian-191):** in the Telegram-redesign backlog, the string `GAP-001` means `conversation_metadata_store_missing` — a different ledger entirely. The verifier hard-fails if fed Telegram-context evidence (manifest `ledger_id` guard). Never conflate the two.

**Structural gate coupling (D14):** `WAVE0_OBSERVE_ONLY` + `GITWRITE-FAILED` retention *stays until GAP-001 is formally closed. No agent lifts it alone.* The verifier reports gate state; it structurally cannot lift anything (read-only file inspection, zero network, `flags_lifted: false` in every report).

## 2. WHAT "EXECUTABLE CLOSURE" MEANS

GAP-001 is closed **when a machine-checkable predicate over evidence artifacts holds**, not when a document says so:

| # | Criterion | Check id | Evidence class today |
|---|---|---|---|
| 1 | Evidence concerns the board checkpoint ledger (not the Telegram homonym) | `HOMONYM-SCOPE` | runtime (JSON payload with boot_id) |
| 2 | Gap payload present, `readiness: READY` | `GAP-PAYLOAD-READY` | runtime |
| 3 | `gates_failed = []` | `GATES-FAILED-EMPTY` | runtime |
| 4 | 2 consecutive software-reboot PASS | `REBOOT-PASS-STREAK` | documentary (D5) — upgrade when boot-report artifact is exported |
| 5 | PASS boots on distinct new boot_ids | `BOOT-IDS-DISTINCT` | documentary (D5) |
| 6 | **Owner-signed checkpoint records GAP-001 CLOSED** | `OWNER-SIGNED-CHECKPOINT` | **absent ⇒ UNKNOWN_PENDING (the open item)** |
| 7 | Standing rider `POWER_LOSS_UNTESTED` recorded | `RIDER-POWER-LOSS-UNTESTED` | documentary (D5) |
| 8 | Doctrine text intact (gate stays until closure) | `STRUCTURAL-GATE-RETAINED` | informational |

**Verdicts:** `CLOSED` (all criteria + runtime signed artifact) · `PENDING_OWNER_SIGNATURE` (criteria hold, signature not yet captured — the honest state as of 2026-08-18) · `NOT_CLOSED` (criteria incomplete) · `INTEGRITY_INCIDENT` (any FAIL, e.g. CLOSED claimed while `gates_failed` non-empty → stop, report, await owner per D14).

Note the honesty boundary: checks 4, 5, 7 passing on the D5 owner-decision record is `PASS_DOCUMENTED`, not runtime proof. The signed checkpoint (check 6) is the only step that converts documentary closure into formal closure — and only the owner can produce it.

## 3. HOW TO RUN

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\world_discovery\gap001_closure_verify.ps1 `
  -EvidenceDir "F:\backup\06-EVIDENCE\sensorium-d14-verify-2026-08-18" `
  -RepoRoot    "F:\backup"
```

- Output: `GAP001-CLOSURE-REPORT-<runid>.json` + `.md` in `<EvidenceDir>\gap001-verify\`, every report carrying sha256 of every consumed input (tamper-evident chain of custody).
- Exit codes: `0` CLOSED · `1` not closed / pending (report still written) · `2` error (incl. homonym-guard trip).
- Costs nothing to re-run: read-only, zero network (enforced by the built-in command allowlist/blacklist — the same policy family as DISCOVERY-PHASE1-05), idempotent.

## 4. CLOSURE WORKFLOW (who does what)

1. Owner produces the signed checkpoint bundle formalizing GAP-001 CLOSED + rider (per D5/D6 signing flow on Windows) and drops it under `06-EVIDENCE/`.
2. Re-run the verifier. `OWNER-SIGNED-CHECKPOINT` flips to runtime `PASS`; verdict becomes `CLOSED`.
3. Extend the manifest: set check 7's content regex to also require `POWER_LOSS_UNTESTED` inside the signed bundle (one-line manifest edit — the *script* never needs changing; criteria live in the manifest, exactly so governance changes are manifest changes).
4. Only then does the owner (never an agent) consider lifting `WAVE0_OBSERVE_ONLY` + `GITWRITE-FAILED` — as a separate, signed decision. A `CLOSED` verdict from this script is *input* to that decision, not permission.

## 5. UPGRADE PATH (runtime-izing the documentary checks)

When the board exports its boot-report history: add to the manifest a `JSON_PATH` check over the export (`reboot_pass_count >= 2`, `boot_ids` distinct) and demote the D5 documentary checks to corroboration. The manifest already sketches this in `upgrade_to_runtime`. Documentary → runtime is a one-way ratchet: never the reverse.
