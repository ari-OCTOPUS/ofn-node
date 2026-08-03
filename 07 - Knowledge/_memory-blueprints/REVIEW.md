---
type: review
subject: BUILD-PROMPT.md + 00_recon_report.md + EXCLUDED.md
date: 2026-07-04
reviewer: claude (cowork session)
verification: grounded — key claims spot-checked against live vault, read-only
status: final
---

# Grounded Review — Memory-Layer BUILD-PROMPT & Phase-0 Recon

## Verdict

The BUILD-PROMPT is a disciplined agent-orchestration spec; the security architecture is sound, not theater. The recon report's headline findings hold up under live spot-check. Residual risk is concentrated in three places: the secret scan is provisional but presented as near-authoritative, the exclusion mechanism is fragile against RTL filenames, and the orphan metric overstates isolation.

**Plan complexity as written: 7/10.** Achievable, but secret-handling edge cases carry more residual risk than the document's confident tone implies.

## Verification against the live vault

| Claim (recon / prompt) | Result |
|---|---|
| Vault root, root meta-files, `ROTATION_CHECKLIST.md` exist | ✅ Confirmed |
| Validators + `gitleaks.toml` in `04 - Architect System/scripts/` | ✅ All 4 present |
| Rotation gate: 23 rows, 4 CRITICAL+OPEN (Monero · Bybit · OKX · Anthropic) | ✅ Exact match, read row by row |
| `_Archive/` missing vs. 3.2 GB cleanup snapshot | ✅ Genuinely absent — real discrepancy, not scan artifact |
| Non-UTF-8 / encoding fragility | ✅ Corroborated (checklist itself ends with stripped broken-byte note) |
| ~385 accessible `.md` | ≈ Counted 389 excl. excluded trees — within noise |

The gate status the whole plan hinges on is accurate.

## What the prompt gets right

- **Correct threat posture:** "moved ≠ rotated; any plaintext secret is compromised," enforced as a hard read-only gate pending human rotation — not agent "cleanup." Right call on an untracked, no-safety-net vault.
- **Epistemic hygiene:** VAULT FACTS marked as to-verify with forced Phase-0 re-derivation prevents acting on stale/hallucinated context.
- **Process-log layer separation:** with ~24% of notes being agent-reports/handoffs/scout-digests, keeping them out of recall is the single highest-leverage design choice in the doc.
- **Connectivity delta** (orphans + avg degree, before/after) as success metric instead of recall@k vanity numbers.
- **Local `bge-m3`** is the correct privacy call given wallets/keys on disk.

## Gaps and risks

### 🔴 CRITICAL

1. **Secret scan is provisional but treated as near-authoritative.** Phase 0b's own note: gitleaks unavailable in sandbox → Python-regex only. Regex-clean ≠ gitleaks-clean. The gate cannot be trusted until `gitleaks detect --no-git -c scripts/gitleaks.toml` runs from Windows. This must be in the verdict, not a footnote.
2. **Ingestable Markdown containing secrets is under-handled.** ROTATION_CHECKLIST itself names `TELEGRAM_SETUP.md`, `TODO.md`, `PROJECT_EXPORT_COMPLETE.md` as containing hardcoded tokens — and `PROJECT_EXPORT_COMPLETE.md` is on the orphan/ingest list. The `Lead-نقاشی.md` hit confirms the class is live. "Scan and hope" is too weak: **any `.md` referenced in ROTATION_CHECKLIST must be hard-quarantined until its row is ROTATED**, independent of regex results.

### 🟠 HIGH

3. **Denylist-by-glob fragile against RTL/non-ASCII filenames.** The hardening log documents a Persian word-order glob bug (`راهنمای_05_…` vs. real `05_راهنمای_…`) that never matched — a one-character-from-leak near-miss. For secret-bearing classes: invert to **scan-then-include (allowlist)**. A missed denylist glob leaks; a missed allowlist glob only under-includes. → See `[[PHASE-0A-EXCLUSION-SPEC]]`.
4. **The gate protects the DB, not the vault.** Rotation rows 20–23 point outside the vault root (`Desktop/ENV.rar`, `Desktop/Mining/…`, `Desktop/AI-sume/…`). Phase-7 "zero secret-leak eval" proves only the memory DB is clean — never the vault or Desktop siblings. Make the boundary explicit so a green eval isn't misread as "secrets handled."

### 🟡 MEDIUM

5. **Orphan metric overstates isolation.** Of 138 "orphans," ~45+ are internally-coherent island clusters (`brushline/` subtrees, `فیوژن هیپنوتیزم/00_Knowledge_Base`) isolated by design. Flat orphan-rescue will generate false link suggestions across intentional boundaries. Compute orphan-ness **per subtree**; separate "true orphan" from "island cluster" before Phase 4/5.
6. **No hallucination check on extracted relations.** Phases 3/4 LLM-infer entities/edges with no precision audit. A hallucinated edge is worse than a missing one. Add a sampled precision audit before edges are committed.
7. **Infra weight vs. "dependency-light" for ~372 notes.** `bge-m3` + `sqlite-vec` + local Qwen/Llama is heavy for the corpus size. Ship **FTS5-first**; add the vector layer only if the measured connectivity/recall delta justifies it.

### ⚪ LOW

8. **`_Archive` absence deserves escalation.** On a no-safety-net vault, a 3.2 GB archive that the cleanup snapshot says exists but doesn't is a data-integrity signal (intentional delete vs. failed sync). Confirm before any Phase ≥1 mutation — Prime Directive 0's backup gate is already unverified.

## Priority order

1. Rotate the 4 CRITICAL rows (human action).
2. Run gitleaks from Windows; re-baseline Phase 0b.
3. Triage the `Lead-نقاشی.md` hit (`generic-assignment` is a common false-positive shape).
4. Confirm `_Archive` + encrypted backup.
5. Before ingest: allowlist-by-scan for secret classes, hard-quarantine checklist-named `.md`, per-subtree orphan scoping. → `[[PHASE-0A-EXCLUSION-SPEC]]`
