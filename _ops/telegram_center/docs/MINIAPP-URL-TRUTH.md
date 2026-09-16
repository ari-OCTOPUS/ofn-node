# MiniApp URL truth (single source)

stamp: 2026-08-23T16:15:00+10:00 (U07 residual close)

## Authoritative public URL (LIVE)
- **Public LIVE:** `https://app.master-painting.com`
- Source of truth for agents/docs/env/state operational reads: this named URL only.
- Verified: HTTPS 200 MiniApp shell on `/` and `/miniapp` (U05 + U07 re-measure).
- Do **not** invent alternate domains.

## Surfaces (roles — not triple primary)
| Surface | Role | Status |
|---|---|---|
| `https://app.master-painting.com` | **Public LIVE** MiniApp URL (named tunnel `octopus-miniapp`) | ACTIVE primary |
| `127.0.0.1:8774` | Gateway **bind only** (local loopback) | ACTIVE bind; not a public URL |
| `*.trycloudflare.com` (incl. qualification-payday-…) | Quick-tunnel leftover | **SUPERSEDED / stale** — never primary |

## Config / state (measured)
- `OCTOPUS.env`: `OCTOPUS_TG_MINIAPP=1` + `OCTOPUS_MINIAPP_URL=https://app.master-painting.com`
- User env (HKCU): same as above
- `OCTOPUS-flags.cmd`: `OCTOPUS_TG_MINIAPP=1` + `OCTOPUS_MINIAPP_URL=https://app.master-painting.com` (U07)
- `_ops/state/telegram/miniapp-url.json`: `url=https://app.master-painting.com` `kind=named` (PID is tunnel metadata; re-check liveness, do not invent)
- Telegram menu: already matching live URL (U05: SKIP_ALREADY_MATCHING; no mutate)

## Speaking rule
| Claim | Allowed when |
|---|---|
| Public MiniApp LIVE | Named URL HTTPS 200 + env/state/truth align on `app.master-painting.com` |
| Gateway bind LIVE | PID listening `127.0.0.1:8774` |
| trycloudflare active primary | **Never** after U07 — treat as SUPERSEDED |
| CONFIG_NEEDED (missing public URL) | **False** for operational path after U05/U07 — durable URL is set |

Do not equate localhost bind with public URL. Do not present trycloudflare or localhost as public primary.

## History
- U05 PASS: durable env + User env set; menu already matching.
- U07: closed Process/env residual + doc triple-primary; trycloudflare not primary anywhere operational.
- Evidence: `06-EVIDENCE/OCTOPUS-U05-MINIAPP-PUBLIC-MENU-2026-08-23/`, `06-EVIDENCE/OCTOPUS-U07-MINIAPP-URL-RESIDUAL-2026-08-23/`
- Older G10 / DOC-RECONCILE packs that said localhost primary or trycloudflare env: **SUPERSEDED** by this card (packs kept, not deleted).