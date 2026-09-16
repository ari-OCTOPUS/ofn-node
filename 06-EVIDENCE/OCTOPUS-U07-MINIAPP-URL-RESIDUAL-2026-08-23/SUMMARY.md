# OCTOPUS-U07 MiniApp URL residual — 2026-08-23

**Status: PASS_WITH_HOLDS**

## Problem
Triple residual after U05: state already named-tunnel; User/`OCTOPUS.env` already named URL; **Process env still trycloudflare**; docs still mixed (localhost primary / CONFIG_NEEDED unset) via G10/DOC-RECONCILE truth card.

## Measure (before)
- `miniapp-url.json`: `https://app.master-painting.com` kind=named pid=8512 (cloudflared LIVE)
- `OCTOPUS.env` + User env: named URL + `OCTOPUS_TG_MINIAPP=1`
- Process env: `https://qualification-payday-functionality-choice.trycloudflare.com/miniapp` (stale)
- `MINIAPP-URL-TRUTH.md`: still contained unset/CONFIG_NEEDED language
- Public HTTPS `/` and `/miniapp`: 200 MiniApp shell
- Gateway: `127.0.0.1:8774` PID 12220

## Repair
1. Audit backup `OCTOPUS.env.bak-u07-20260823` (no content change needed)
2. Cleared Process residual → named URL + TG=1
3. Durable: `OCTOPUS-flags.cmd` now sets `OCTOPUS_MINIAPP_URL=https://app.master-painting.com`
4. Rewrote `docs/MINIAPP-URL-TRUTH.md` — single public primary; localhost=bind only; trycloudflare=SUPERSEDED
5. Supersede notes on historical G10/DOC-RECONCILE packs (not deleted)
6. PLAN-T4 banner: named URL primary

## Prove
- Process/User/`OCTOPUS.env`/state/truth/flags: one public URL `https://app.master-painting.com`
- No trycloudflare as active primary in operational surfaces
- Docs do not claim CONFIG_NEEDED for missing public URL
- Public HTTPS still 200
- No Telegram mutate; no money/PWM/secrets in pack

## Holds
- Historical pack bodies remain (SUPERSEDED notes added)
- Optional recycle of long-lived processes for Process-env inheritance

## Evidence
`F:\backup\06-EVIDENCE\OCTOPUS-U07-MINIAPP-URL-RESIDUAL-2026-08-23\`