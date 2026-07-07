---
type: spec
subject: "Phase 0a — corrected ingest-eligibility logic (drop-in replacement)"
date: 2026-07-04
supersedes: "BUILD-PROMPT.md § Phase 0a exclusion rules (denylist-by-glob)"
rationale: "[[REVIEW]] — findings #2 (checklist-named .md), #3 (RTL glob fragility)"
status: proposed
---

# Phase 0a (corrected): Ingest Eligibility — Allowlist by Scan + Checklist Quarantine

## Design principle

**Never rely on filename globs to keep secrets out.** Globs demonstrably fail on RTL/Persian word-order variants (see hardening log: `راهنمای_05_…` vs. `05_راهنمای_…` never matched). Failure modes are asymmetric:

- Missed **denylist** glob → secret leaks into the memory DB. Unrecoverable without rebuild.
- Missed **allowlist** entry → one note temporarily under-included. Trivially fixable.

Therefore: files enter the ingest set only by **passing checks on content**, never by "not matching an exclusion pattern."

## Eligibility pipeline (all gates must pass, in order)

```
candidate .md
  │
  ├─ Gate 1: PATH SCOPE (cheap, structural)
  │    inside vault root, not under: _Duplicates/, secrets-export/,
  │    .git/, .obsidian/, any path listed in .agentignore
  │    → matching is done on RESOLVED ABSOLUTE PATHS, never raw glob
  │      against the filename component
  │
  ├─ Gate 2: CHECKLIST QUARANTINE (hard, unconditional)
  │    file basename OR relative path appears anywhere in
  │    ROTATION_CHECKLIST.md → QUARANTINED until that row's
  │    status == ROTATED. No scan result can override this gate.
  │    Matching: normalize NFC + casefold; compare both basename
  │    and full relative path; substring match is acceptable
  │    (over-quarantine is safe, under-quarantine is not).
  │
  ├─ Gate 3: SECRET SCAN (content, two-engine)
  │    3a. gitleaks detect --no-git -c "04 - Architect System/scripts/gitleaks.toml"
  │        — MUST run on host (Windows), not sandbox. If gitleaks
  │        binary unavailable → the ENTIRE pipeline halts with
  │        status SCAN-UNAVAILABLE. Regex-only results are NEVER
  │        accepted as a substitute for this gate.
  │    3b. Python regex pass (existing scanner) as a second net.
  │    Any hit from either engine → QUARANTINED (file listed in
  │    quarantine manifest with rule id + line no, content never
  │    echoed).
  │
  ├─ Gate 4: ENCODING SANITY
  │    file must decode as UTF-8 (or UTF-8 after BOM strip).
  │    Non-decodable bytes → SKIPPED-ENCODING (listed, not ingested,
  │    never "repaired" in place).
  │
  └─ PASS → written to ingest manifest
```

## Outputs (all committed to `_memory/`)

| File | Content |
|---|---|
| `ingest-manifest.json` | Every file that passed all 4 gates: relpath, sha256, size, mtime, gate-pass timestamp |
| `quarantine-manifest.json` | Every quarantined file: relpath, gate that caught it (2 or 3), rule id / checklist row ref. **Never file content, never the matched string.** |
| `skipped-encoding.json` | Gate-4 failures |

Ingestion (Phase 1+) reads **only** `ingest-manifest.json`. It never re-derives eligibility, never walks the filesystem itself. A file not in the manifest does not exist as far as downstream phases are concerned.

## Invariants

1. **No glob ever grants or denies eligibility on its own.** Path-scope gate uses resolved paths against a fixed directory list; everything else is content-based.
2. **Quarantine is monotonic within a run.** A file cannot move quarantine → eligible mid-run; re-eligibility requires a fresh full Phase-0a pass after the human updates ROTATION_CHECKLIST.
3. **Gate 2 dominates Gate 3.** A checklist-named file that scans clean stays quarantined — "regex found nothing" is exactly the failure mode this gate exists to cover.
4. **SCAN-UNAVAILABLE is a full stop**, not a downgrade. The Phase-0b sandbox precedent (gitleaks missing → silent fallback to regex) must not recur.
5. **Manifests are append-only evidence.** Each run writes a new timestamped set; prior manifests are never edited.

## Filename normalization rules (RTL hardening)

- Normalize all paths to **Unicode NFC** before any comparison.
- Strip/ignore directional control chars (U+200E, U+200F, U+202A–U+202E, U+2066–U+2069) in comparison keys — they are invisible and defeat equality checks.
- Never construct match patterns by concatenating Persian tokens in "expected" order; compare whole normalized strings only.

## Acceptance tests (must pass before Phase 1)

1. `TELEGRAM_SETUP.md`, `TODO.md`, `PROJECT_EXPORT_COMPLETE.md` → quarantined by Gate 2 even with clean scan output.
2. A copy of a checklist-named file under an RTL-reordered filename → still quarantined (normalization test).
3. Planted canary token (fake `sk-ant-…`) in a scratch note → caught by Gate 3, listed in quarantine manifest, string not echoed anywhere.
4. gitleaks binary renamed away → run halts SCAN-UNAVAILABLE; ingest manifest not written.
5. File with a raw 0x9D byte → lands in `skipped-encoding.json`, untouched on disk.

## Diff vs. BUILD-PROMPT as written

| BUILD-PROMPT (current) | This spec |
|---|---|
| Denylist globs exclude secret-bearing files | Content-scan allowlist; globs only for structural dirs |
| "READMEs may be ingested if they pass the secret scan" | Checklist-named files quarantined regardless of scan |
| Regex fallback when gitleaks unavailable | Hard stop; regex is a second net, never a substitute |
| Eligibility implicit at ingest time | Frozen manifest; downstream reads manifest only |
