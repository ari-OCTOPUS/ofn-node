# REPORT — Board2 Windows wire standup (reconciled)

**When (AEST):** 2026-08-22 ~17:19+10
**Context:** Owner priority step 3 after Orange Pi A+D+B PASS

## Created paths
- `F:\octopus-wire\` (ofn/wire working tree; origin → https://github.com/ari322/ofn-node.git)
- Evidence: `F:\backup\06-EVIDENCE\BOARD2-WIRE-WINDOWS-2026-08-22\`

## w001
- **Written:** yes — `## [20260822-1715] id:w001 from:windows`
- Commit: `ca038d4` (also on GitHub `origin/ofn/wire` and local `F:\ofn-node`)

## Push status
- Target: `ari322/ofn-node` branch `ofn/wire`
- First attempt: **FAIL** (no HTTPS username) → PUSH-ATTEMPT.json
- Retry: **SUCCESS** (GCM) bed6219..ca038d4 → PUSH-SUCCESS.json
- Board-side fetch of GitHub still blocked (no DietPi HTTPS creds)

## Germline interim
- `E:\germline\octopus.git` `ofn/wire` @ `175e9565` includes `MESSAGES-WINDOWS.md` with id:w001 for SMB `git fetch germline`

## Phase-3 next (still deferred)
- Do **not** arm OUTBOUND_ENABLED / CONTROL_URL / BOARD_CP_PULL until owner opens G7
- Pending: playbook step 4 (2h CronCreate), board GitHub read creds, then G7

## Onboarding
- Canonical: `WIRE-ONBOARDING-WINDOWS.md` (now in `F:\octopus-wire`; sourced from ofn/wire)
