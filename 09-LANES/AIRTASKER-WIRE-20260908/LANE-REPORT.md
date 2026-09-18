# LANE-REPORT — AIRTASKER-WIRE-20260908

GOV_VERSION=V8 · LADDER=L2 · closed: 2026-09-08
Owner order (verbatim intent): build the connection with real executable output,
test it, DELETE NOTHING from the rest of the octopus, connect the website
(Airtasker) to the organism. This lane EXECUTED connection C1 from
OCTOPUS-138-WIRING matrix.

## What was done

1. **Base truth established**: runtime file on 138
   (`/home/ari/ofn/ofn/agents/imap_listener.py`, sha 76f5ec63…) fetched;
   laptop clone differs ONLY by CRLF — patch based on 138 runtime, so
   nothing of 138's evolution could be overwritten. File is git-clean on 138
   (HEAD 63938eb0).
2. **Additive-only wiring** (deploy/ folder = source of truth copy):
   - `airtasker_alert_parser.py` (from AIRTASKER-WATCH lane, 8/8-tested,
     pure stdlib, never fabricates)
   - `airtasker_intake.py` (NEW): alert email → parse → dedupe by task URL →
     INSERT painting_leads (source='airtasker', temperature/status='new',
     empty fields stay empty) → receipt events → TG card via owner_notify
     (max 3/email). supply_risk tasks NEVER become leads. dry=True writes
     nothing. Never raises.
   - `imap_listener.py` patch: ONE branch in `classify()` (airtasker sender →
     ("alert","airtasker",…)) before the noise fall-through; ONE branch in
     `_act()` handling kind="alert" (dry respected). Every other sender's
     path byte-identical.
3. **Tests — real, two hosts**:
   - Laptop pytest: **15/15** (8 regression locking old behaviour incl.
     bounce/reply/optout/autoreply/noise-untouched + 7 new-branch incl.
     dedupe idempotency, supply-risk skip, dry-zero-writes, receipt chain).
     (One iteration: initial 8 fails were a sys.path-order bug in my own test
     harness + 2 fixture nits — fixed, documented.)
   - On-host dry selftest (138, synthetic TEST email): classify + parse +
     would_insert correct, **zero writes**.
   - On-host real `--dry` cycle: ran to the credentials gate (ssh shell has
     no unit env — expected; service is armed via
     `/home/ari/.config/ofn/secrets.env`).
   - **First production cycle with new code: 03:45:12Z→03:45:51Z, exit 0,
     Result=success.** No restart performed or needed (timer-driven one-shot).
4. **Deploy receipt**: DEPLOY-RECEIPT-20260908.json — pre/post sha256 for
   all three files, backup `imap_listener.py.bak-airtasker-20260908` kept on
   138 (no rm anywhere), py_compile OK on 138 python3.

## Capability grades

| Capability | Grade |
|---|---|
| Parser (designed input) | E2 (8/8) — real-format gate still needs owner's first real alert email |
| classify regression (nothing deleted) | E2 (8/8 tests lock prior behaviour) |
| intake insert/dedupe/supply-skip (tmp DB) | E2 |
| New code survives production service cycle on 138 | E2 (exit 0, 03:45Z run) |
| Full E2E alert→lead→TG card | **E0 pending owner action** (enable Airtasker alerts on own account) |

## Rollback (no rm)

`cp imap_listener.py.bak-airtasker-20260908 imap_listener.py` on 138 — next
timer fire (≤15 min) reverts behaviour. Parser/intake files are inert without
the listener branch and can stay.

## What was NOT done (honest)

- No git commit: 138 repo tree is dirty with parallel agents' work (gates.json,
  self_model_producer.py, mesh) — committing there would mix lanes; laptop
  clone left untouched by design. Source of truth: this lane's deploy/ folder
  + backup on 138. Follow-up decision listed below.
- No restart of any service (none needed; none allowed by red lines).
- No DB row written on 138 by tests (dry only — no synthetic data in
  production DB, per number discipline).
- Full E2E blocked ONLY on owner enabling Airtasker account alerts.

## Open decisions for owner (AGENTS.md §6)

1. **Enable Airtasker task alerts** (Painting + Sydney; email on) — the
   pipeline's intake. Everything else is live and waiting.
2. Git durability: commit the 3 files via a clean worktree + bundle→gh PR
   path (needs a small follow-up lane; 138 tree currently dirty from other
   agents).
3. (Carried) first real alert email → forward/save to validate parser
   real-format E2.

## Evidence paths

- 09-LANES/AIRTASKER-WIRE-20260908/DEPLOY-RECEIPT-20260908.json
- 09-LANES/AIRTASKER-WIRE-20260908/test_airtasker_wire.py (15/15)
- 09-LANES/AIRTASKER-WIRE-20260908/deploy/ (imap_listener.138-base.py,
  imap_listener.py, airtasker_alert_parser.py, airtasker_intake.py)
- On-138: backup file + running listener (sha c6c9dad0…) +
  /home/ari/ofn/data/state/legs/airtasker-watch/ (future receipts)
