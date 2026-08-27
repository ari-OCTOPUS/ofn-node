# Cockpit V2 M1 Acceptance Matrix

This document maps the owner mission's M1-01…M1-35 requirements to executable evidence. A row is not marked PASS until the named automated test or final system comparison succeeds.

| ID | Requirement | Evidence |
|---|---|---|
| M1-01 | Old panel unchanged hash | `tests.test_cockpit_v2_purity.TestLegacyPanelPreserved` |
| M1-02 | `/cockpit-v2/` loads | real `serve(app, 0)` HTTP test |
| M1-03 | Same origin/port | static-map HTTP test; no separate server configuration |
| M1-04 | No new listener | pre/post sorted `ss -tln` snapshot |
| M1-05 | Unauthenticated API rejected | V2 HTTP auth matrix |
| M1-06 | Valid owner accepted | signed Telegram owner-session fixture |
| M1-07 | Non-owner rejected | valid signed non-owner fixture |
| M1-08 | Status schema | read-model and HTTP envelope tests |
| M1-09 | Nodes schema | read-model and HTTP envelope tests |
| M1-10 | Legs schema | fixed eight-leg and HTTP tests |
| M1-11 | Queue schema | metadata-only pagination tests |
| M1-12 | Audit schema | bounded redacted audit tests |
| M1-13 | No effect verbs from frontend | frontend + purity source contracts |
| M1-14 | No direct DB/file write | AST purity + before/after fixture snapshots |
| M1-15 | No secret in HTML/JS/API/log | source and hostile-fixture scans |
| M1-16 | XSS escaping | inert DOM rendering fixtures |
| M1-17 | Prompt-injection text inert | hostile metadata frontend/read-model fixtures |
| M1-18 | Stale data marked | injected clock/freshness tests |
| M1-19 | API failure honestly degraded | missing/corrupt/unreadable source tests |
| M1-20 | No overlapping poll | pure polling-controller test |
| M1-21 | Hidden-tab interval 60s | pure polling-controller test |
| M1-22 | ETag/304 | authenticated real HTTP conditional request test |
| M1-23 | Mobile viewport | frontend contract test |
| M1-24 | RTL | frontend contract test |
| M1-25 | Keyboard/accessibility smoke | semantic/ARIA/focus/keyboard source tests |
| M1-26 | Quote is not cash | business-truth test |
| M1-27 | Booking is not cash | business-truth test |
| M1-28 | Invoice is not cash | business-truth test |
| M1-29 | Trusted receipt may become verified cash | provenance fixture test; otherwise UNKNOWN |
| M1-30 | Legacy panel checklist unchanged | hash plus existing `test_panel_coverage` |
| M1-31 | No systemd mutation | service state + source + journal/listener comparison |
| M1-32 | No external action | no command route/effect callback and audit comparison |
| M1-33 | No model call from polling | import/callback purity tests |
| M1-34 | Rollback to old panel | exact `/` and `/index.html` bytes through HTTP handler |
| M1-35 | Clean Git diff | `git diff --check`, cache cleanup, final review |

## Additional hidden-boundary evidence

- Duplicate, unknown, overlong, malformed, negative, zero, boolean, and over-cap query values.
- Cursor/filter binding, stable ordering, and past-end pages.
- Missing, empty, malformed, truncated, oversized, stale, future-dated, and symlink-escaped mesh sources.
- One corrupt JSONL line among valid rows.
- Payload, evidence, raw errors, identities, network paths, and PII omitted by field allowlist.
- Auth failure cannot be converted to 304; 304 is bodyless and retains security/cache headers.
- Telegram launch replay, stale launch, current owner allowlist, and partner/owner host-role isolation.
- Late poll response cannot overwrite newer state; teardown aborts all requests; 401 stops polling.
- No token in URL, source, localStorage, sessionStorage, cookies, or API response.
