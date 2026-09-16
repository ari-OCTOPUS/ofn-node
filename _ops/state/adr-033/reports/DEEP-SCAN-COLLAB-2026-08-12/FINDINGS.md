# FINDINGS — Deep Scan Collab/DeepSeek 2026-08-12

## Verdict: ALL CLOSED ✅

| Bug | Status | Evidence |
|-----|--------|----------|
| B1 — Auth 403 POST | **FIXED** | AUTH_MAX_AGE=3600; inject بدون fetch wrapper |
| B2 — Stub «موانع» | **FIXED** | سلام→intro · موانع→blockers · meta |
| B3 — Ask hang | **FIXED** | AbortController · timeout 60s |
| B4 — LOCAL_FIRST qwen | **FIXED** | `_skip_local` + no qwen fallback |
| B5 — timeout bad_json | **FIXED** | 200 + `kind=timeout` |
| B6 — adapter import | **FIXED** | flat `import model_router` |
| B7 — tool_request loop | **FIXED** | `_normalize_cost` |
| B8 — clarify heavy | **FIXED** | intent-first + cache |
| B9 — photo caption | **FIXED** | vision + blockers hint |
| Phase E — خودآگاهی | **FIXED** | خودت کی ای → intro |
| seed-journal-idempotent | **FIXED** | `append_entry(ts=pulse.ts)` · 2026-08-12 12:05 |
| blackbox SyntaxWarning | **FIXED** | raw docstring |
| UI «همکار فوری» | **FIXED** | متن صادق DeepSeek |

## Suites (12:05)

- `test_talk_discovery` — all green (incl. seed-journal-idempotent)
- `test_conversation` — OK 14
- `test_tool_request` — 20/20
- `test_miniapp_gateway` — 47/47

## Live

- gateway pid **26584** (restarted after closeout)
- collab path: DeepSeek secondary

## Owner action

مینی‌اپ را **ببند و باز کن** → همکار → سؤال تست.  
Footer: `secondary:deepseek-v4-flash`
