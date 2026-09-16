# DEEPSEEK-CREDENTIAL-HYGIENE-TEST — DEEPSEEK-AUTOMATIC-ROUTING-01

Executed: 2026-08-19T02:23Z–02:28Z · Executor: ZCode agent (read-only scan; key value never read into any output)

## Verdict: PASS (all checks)

| # | Required check | Result | Evidence |
|---|---|---|---|
| 1 | Key present (confirm only true/false) | `DEEPSEEK_KEY_PRESENT = true` — `DEEPSEEK_API_KEY` in `F:\backup\.env` (name-only check; value length>10) | scan trace below |
| 2 | No key material in logs/receipts/evidence | **0 exact-key hits across 1,352 files** in `_ops/state`, `06-EVIDENCE`, `docs`, `02-DECISIONS`, `01 - Dashboard`, `06-RISKS`, `03-GATES`, `01-TRUTH`, `07-HANDOFF`, `_ops/scripts`, `_ops/cortex`, `_ops/memory` | tree scan |
| 3 | No `sk-…`-pattern secrets in `_ops/state` | 0 hits (known fake fixture `sk-1234567890abcdef` in a test file excluded by design) | pattern scan |
| 4 | No key material in git-tracked tree | `git grep -F` (pattern via stdin; key never on disk/command line) → **0 hits** | git scan |
| 5 | `.env` untracked | `git ls-files -- .env .env.bak-20260810` → empty; history: `git log --all -- .env` → 0 commits (verified in AUDIT-191 §I10) | git |
| 6 | No key in docs/NOW.md / Obsidian / this report | Included in surface scan (#2) — 0 hits | tree scan |
| 7 | Key fingerprint (non-material, sha256[:12]) | `ada979483727` — for future tamper comparison only | — |

## Method (reproducible)

```
1. presence: parse .env for DEEPSEEK_API_KEY name; assert value length>10; report true/false only
2. tree scan: walk leak-surface dirs; read each file; test `key in text`; report path counts (never content)
3. pattern scan: regex sk-[A-Za-z0-9_\-]{24,} over _ops/state; compare against key; exclude documented fake fixture
4. git scan: `git grep -F -f - -- .` with the key piped via stdin (never argv, never a temp file)
5. tracking: `git ls-files -- .env .env.bak-20260810` → empty
```

## Key-absent behavior (static verification, REQUIRED TEST #1)

`_ops/cortex/model_router.py` gates paid tiers on key presence (`_has = {"primary": bool(kp.get("deepseek")), …}` at model_router.py:515-518). With key absent, primary/secondary are reported unavailable and the router does not dispatch a paid network attempt; the failure surfaces in the paid-calls log with `ok=false` (no silent success path — freeze/fallback annotation layer, model_router.py:637-655). A live key-absent drill (removing the key) was NOT executed — would require mutating the live `.env`; recorded as the one static-verified item in this report.

## Limitations

- Binary/large files >30 MB skipped in tree walk (no known credential files that size).
- `git grep` covers the tracked working tree, not unreachable objects; full-history secret scanning remains part of D3 (owner-gated).
- The scan is a point-in-time snapshot; the standing protections (.gitignore, `<redacted>` flag snapshots) remain the durable defense.
