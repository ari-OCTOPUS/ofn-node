# RUNBOOK-POINTERS — Board2 bridge key rotate (2026-08-22)

Search scope: `F:\backup` (brief; BRIDGE*KEY*ROTATE*, ofn/wire bridge key docs).
Do **not** invent rotate steps. Marketing owns DietPi Board2 mutate.

## Verdict

**NEED_MARKETING_DOCUMENTED_PATH** — no standalone marketing-owned rotate runbook (step-by-step procedure) found under F:\backup.

Prior rotate evidence exists (PASS today) but is evidence of an already-executed rotate, not a reusable documented marketing path.

## Paths found (related; not a full rotate runbook)

### Prior rotate evidence / auth reuse
- `F:\backup\06-EVIDENCE\BOARD2-PHASE3-2026-08-22\BRIDGE-KEY-ROTATE-20260822T092315Z.json`
  - auth token: `OCTOPUS-BOARD2-BRIDGE-KEY-ROTATE-20260822` (reuse → SUPERSEDE_RESUME=true)
  - result: PASS; notes laptop `OCTOPUS_BOARD_CP_BEARER` + DietPi `OCTOPUS_BRIDGE_API_KEY` rotated in place; secrets not printed
- `F:\backup\06-EVIDENCE\BOARD2-PHASE3-2026-08-22\BOARD2-PHASE3-PASS-20260822T091329Z.json`
- `F:\backup\06-EVIDENCE\BOARD2-PHASE3-2026-08-22\BOARD2-PHASE3-REPROBE-PASS-20260822T091428Z.json`

### Env bak artifacts (ops; not runbook)
- `F:\backup\_ops\OCTOPUS.env.bak-keyrotate-20260822T092315Z`
- `F:\backup\_ops\OCTOPUS.env.bak-keyrotate-20260822T094830Z`

### OFN / wire bridge related docs (context; not key-rotate steps)
- `F:\backup\06-EVIDENCE\OFN-SYNC-CONTRACT-2026-08-16.md`
- `F:\backup\06-EVIDENCE\BOARD2-WIRE-SEND-IDB-FIX-2026-08-22\PATCH-FOR-MARKETING.txt`
- `F:\backup\06-EVIDENCE\BOARD2-WIRE-SEND-IDB-FIX-2026-08-22\ofn-wire-send.sh.BEFORE`
- `F:\backup\06-EVIDENCE\BOARD2-WIRE-SEND-IDB-FIX-2026-08-22\ofn-wire-send.sh.AFTER`
- `F:\backup\06-EVIDENCE\BOARD2-WIRE-SEND-IDB-FIX-2026-08-22\README.md`
- `F:\backup\04-SYSTEMS\OFN-NODE.md`
- `F:\backup\02-DECISIONS\OWNER-AUTH-BOARD2-OFN-GATES-2026-08-22.md`
- `F:\backup\agent-prompts\MEGAPROMPT-OFN-BOOT-2026-08-16.md`
- `F:\backup\_ops\BRIDGE-CONTRACT.md` (generic bridge contract / capability model — not DietPi API key rotate)

## Not found
- No `*BRIDGE*KEY*ROTATE*` runbook `.md` with marketing-owned step sequence
- No documented path titled for Board2 bridge API key rotation procedure for marketing handoff

## Agent constraints (this package)
- Do NOT perform rotate on DietPi from this agent (marketing owns Board2)
- Do NOT paste full key in chat
- Do NOT setWebhook
- Do NOT github_pat_install
- Do NOT commit secrets; no `git add -A`
