---
type: prompt
status: ready
tags: [4d, prompts, phases, implementation]
created: 2026-07-16
updated: 2026-07-16
depends-on: "[[04 - Architect System/4D-Obsidian-Foundation/01-FOUNDATION-AND-BOUNDARIES]]"
target: "next implementation agents"
---

# Prompt Pack — فازهای تکمیل 4D × Obsidian

> هر Prompt یک ایجنت محدود و مستقل است. هر ایجنت فقط همان فاز را انجام می‌دهد، گزارش می‌دهد و می‌ایستد. اجرای چند فاز در یک موج ممنوع است مگر با رأی مالک.

## قرارداد مشترک همه Promptها

این متن ابتدای هر Prompt فرض می‌شود:

```text
Binding law: IMPROVE, DON'T REWRITE. Read 00-START-HERE and all earlier phase reports. Before mutation show Current / Delta / Preserved / Rollback. Do not read or expose secrets. Do not touch .env, _ops runtime/state, TCB, core anchors, live daemon, Telegram, cloud APIs, or self-code apply. Historical documents are claims; verify against current code/filesystem. Unknown stays UNKNOWN. Keep previous versions. Stop at the phase gate and await explicit human verdict.
```

---

## P0 — Canonical Reality & Baseline Agent

```text
Mission: establish the evidence-based baseline only.

Tasks:
1. Determine the canonical 4D working tree, git status, Python environment, and whether F:\backup\4d_system is live, mirror, or both. Do not move files.
2. Inventory top-level packages while excluding .env contents, venvs, caches, outputs payloads, binaries, and archives.
3. Reconcile README/PROJECT_STATE/MANIFEST/REGISTRY claims with code and command evidence.
4. Identify the exact safe test command. If running tests could conflict with a live process, stop and ask. Never start runtime.
5. Produce BASELINE-REPORT with facts, reported claims, discrepancies, unknowns, and G0 verdict recommendation.

Deliverables: one new report only; no code edits.
Gate: canonical path and safe verification procedure are unambiguous.
Stop: AWAITING HUMAN VERDICT.
```

## P1 — Boundary, TCB & Threat Model Agent

```text
Mission: prove what may and may not be connected.

Tasks:
1. Read guardrails and derive the current TCB from code, not old prose.
2. Map trust zones: runtime, output stores, internal control_plane, Vault, Architect/_ops, human.
3. Build data classification and forbidden-flow matrix.
4. Threat-model prompt injection, secret leakage, PII replication, stale evidence, duplicate notes, path traversal, symlink/reparse points, race/partial write, and agent overreach.
5. Compare findings to OI-1..OI-10 and propose corrections without changing law.

Deliverables: TCB-MAP and THREAT-MODEL as new docs.
Gate: G1 safety boundaries have cited evidence and owner sign-off request.
No implementation.
```

## P2 — Obsidian IA & Contract Agent

```text
Mission: turn the approved blueprint into a minimal Obsidian file plan.

Tasks:
1. Search for existing 4D MOCs/projects/notes to avoid duplication.
2. Map every proposed note to existing Property Schema and templates.
3. Design exact paths, names, links, MOC, review queue, status lifecycle, and dedup key.
4. Keep this additive; propose the smallest tree, not the largest.
5. Generate a dry-run change manifest listing files that would be created. Do not create the full tree yet.

Deliverables: IA-CHANGE-MANIFEST and link graph.
Gate: owner approves paths/schema and confirms no duplicate structure.
```

## P3 — Export Schema & Fixture Agent

```text
Mission: define the provider-neutral export contract with synthetic fixtures.

Tasks:
1. Inspect current 4D producers and vault_sync interface read-only.
2. Specify versioned export envelope and compatibility rules.
3. Create only non-sensitive synthetic fixtures outside TCB/runtime outputs.
4. Define observed/derived/interpreted/unknown mapping and provenance requirements.
5. Write contract tests first if owner approved implementation.

Gate: fixtures validate; no Vault write; no secret/PII patterns; schema versioned.
Stop after report.
```

## P4 — Read-only Extractor Agent

```text
Mission: implement a thin read-only extractor behind an adapter/port.

Constraints:
- Reuse existing vault_sync where possible; do not replace it.
- Source allowlist only; outputs are in-memory or dry-run files in a safe temp/test location.
- No real Vault mutation.

Tasks:
1. Extract aggregate metadata from approved artifact classes.
2. Sanitise, hash, validate, and emit deterministic dry-run manifests.
3. Add idempotency and bounded batch behavior.
4. Add L0/L1 tests and negative-path tests.

Gate G3: repeated fixture run is byte-stable; secret fixture is blocked; source missing fails closed; previous tests remain green.
```

## P5 — Staging Writer Agent

```text
Mission: write generated Markdown only to a temporary Vault first.

Tasks:
1. Implement atomic temp-write + replace, path containment, collision handling, and versioned templates.
2. Write only Pending/Staging notes; never Knowledge canonical or existing human notes.
3. Validate frontmatter and links.
4. Prove rollback by deleting the temporary generated tree only.
5. Present exact real-Vault path proposal and wait for owner approval before enabling it.

Gate G4: temp-vault tests green, no out-of-root write, no overwrite, no leak. Real write default-off.
```

## P6 — Review & Promotion Agent

```text
Mission: design and implement human review without automatic truth promotion.

Tasks:
1. Represent pending, accepted, rejected, blocked, stale, and conflict states using approved schema/body conventions.
2. Require evidence pointer and reviewer verdict for promotion.
3. Preserve rejected versions and conflict/tension.
4. No automatic canonical write from 4D.
5. Create reviewer checklist and audit trail.

Gate G5: promotion without verdict is impossible in tests; rejection preserves history; stale evidence is visible.
```

## P7 — MOC & Dashboard Read-model Agent

```text
Mission: produce human-readable Obsidian views from accepted evidence.

Tasks:
1. Create/update only approved new 4D MOC/dashboard files.
2. Show SOG evidence, Brain-OS hypotheses, approvals, risks, unknowns, and freshness separately.
3. Never present interpreted/unverified content as verified.
4. Keep index pages under 200 lines and link rather than copy.
5. Dashboard must be rebuildable from notes.

Gate G6: seeded test data renders correct truth labels; removing/rebuilding view loses no source knowledge.
```

## P8 — Architect Registry Coupling Agent

```text
Mission: couple 4D evidence upward without merge.

Tasks:
1. Read the tri-plane reconciliation and current _ops registry contract.
2. Propose a sanitised, read-only status/manifest adapter; do not wire it live.
3. Ensure HEAD receives health/evidence only and returns policy envelopes, not direct internal commands.
4. Reuse registry; do not create another ledger/control plane.
5. Submit an exact owner-gated wiring plan with rollback and kill behavior.

Gate G7: contract approved. No _ops code/state/flag mutation in this phase.
```

## P9 — Hardening & Operations Agent

```text
Mission: prepare safe operation after all earlier gates are approved.

Tasks:
1. Add replay tests, mutation tests for redaction/idempotency, backup/restore drill, bounded queue, observability, and incident runbook.
2. Verify default-off/shadow-first behavior.
3. Produce an activation checklist for one artifact class only.
4. Never activate daemon, Telegram, cloud, self-code, or external action.
5. Run the approved complete test suite and attach actual outputs.

Gate: clean test evidence, incident drill, owner sign-off checklist, one-command rollback.
```

## گزارش اجباری هر فاز

```markdown
## Phase P# Report — title
- Gate: GREEN | RED | BLOCKED
- Current:
- Delta:
- Preserved:
- Files created/changed:
- Commands and actual evidence:
- Safety checks:
- Unknowns/discrepancies:
- Rollback:
- Next-phase prerequisites:
AWAITING HUMAN VERDICT — do not continue.
```
