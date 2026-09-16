# Board2 Studio/Saba UNLOCK PACKAGE — READY for ACK (2026-08-22)

**Status:** DRAFT / READY FOR OWNER+ari ACK — **DO NOT EXECUTE** until ACK.  
**Scope:** scheduled posts from **existing library only** (`studio/shot-*`, 66 media). No invent content. No paid spend. No mining.  
**Lane:** Studio/OnlyFans with Saba (`studio` `:8793`). Canonical map applies.

---

## Why blocked now (exact)

| # | Gate / control | Current | Where |
|---|---|---|---|
| A | `OFN_WIRE_OUTBOUND` | `0` | `/home/ari/.config/ofn/node.env` |
| B | `wire_outbound` token | listed in `OFN_EXTRA_CLOSED_GATES` | same `node.env` |
| C | `OFN_WIRE_PUBLISH` | `1` (alone insufficient) | `node.env` |
| D | `live_publish` EXTRA token | already **absent** from closed list | EXTRA list |
| E | `secret_rotation` | **closed** (auto after `GATE_OPEN_UNTIL_UTC=2026-08-17`) | `ofn/config.py` |
| F | `partner_precondition` | **closed** (same expiry) | `ofn/config.py` |
| G | Owner two-step | required for real publish | `ofn/kernel/release_switch.py` (`RULE_OWNER_TWO_STEP`) |
| H | Transport | `sender_dryrun` exposes **only** `dry_run_diff()` — no `send()` until release green | `ofn/adapters/sender_dryrun.py` |

Also leave **closed** on purpose (blast guards): `auto_post`, `auto_dm`, `auto_email`, `auto_scrape`, `live_sms`, `live_dm`, tender/vendor/portal/terms.

---

## Unlock package (propose — execute only after ACK)

### Step 0 — Preconditions (human)
1. Confirm CRITICAL secrets rotation status (or accept risk explicitly). Documented path: `OFN_KEEP_GATES_OPEN=1` only after owner accepts post-`2026-08-17` reopen of `secret_rotation` + `partner_precondition` (`ofn/config.py` comments / INDEX).
2. Record/confirm **partner_precondition** for Saba/studio (INDEX: ثبت پیش‌شرط انتشار استودیو).
3. ACK this package in chat (ari relays owner).

### Step 1 — Config (Board2 DietPi, reversible)
File: `/home/ari/.config/ofn/node.env` (backup first to `node.env.bak-studio-unlock-YYYYMMDDHHMMSS`).

1. Set `OFN_WIRE_OUTBOUND=1`
2. Remove **only** `wire_outbound` from `OFN_EXTRA_CLOSED_GATES` (keep all other EXTRA tokens)
3. Set `OFN_KEEP_GATES_OPEN=1` **only if** Step 0 accepted (reopens E+F)
4. Do **not** clear `auto_post` / `auto_email` / `auto_dm` from EXTRA

### Step 2 — Reload
- `sudo systemctl restart ofn.service` (expect SIGTERM hang risk → SIGKILL if needed, as known Board2 behavior)
- Prove: legs healthz 200; `closed_gates` no longer contains `wire_outbound`; `cfg.wire_outbound is True`; if KEEP_GATES_OPEN: `secret_rotation` + `partner_precondition` open

### Step 3 — Two-step publish path (per item, existing library only)
1. Pick media from existing library only, e.g. `studio/shot-0016`, `shot-0017`, … (no new assets, no invented captions — use empty/owner-provided caption already on board if any)
2. Build **dry_run_diff** first (`sender_dryrun.dry_run_diff`) — human reviews exact payload
3. Owner **step1** + **step2** confirmations (`release_switch.OwnerRelease.may_publish`)
4. Enqueue/outbox drain **one item** / one platform / one tenant=`studio` cap
5. Stop; report external id / ledger; no fan-out

### Step 4 — Schedule (if scheduler exists)
- Queue next N library shots with schedule metadata only after dry-run+two-step per item or per batch policy owner chooses
- If no scheduler endpoint yet: document BLOCKED_SCHEDULER and keep manual one-shot queue

---

## Rollback (exact)

1. Restore `node.env` from `.bak-studio-unlock-*` **or** manually:
   - `OFN_WIRE_OUTBOUND=0`
   - add `wire_outbound` back to `OFN_EXTRA_CLOSED_GATES`
   - remove `OFN_KEEP_GATES_OPEN` (or set `0`)
2. `sudo systemctl restart ofn.service`
3. Prove: `wire_outbound` closed again; publish dry-run-only; legs still 200

---

## Ready checklist for ACK widget

- [ ] Owner accepts CRITICAL secret / KEEP_GATES_OPEN risk
- [ ] Partner precondition recorded for Saba
- [ ] ACK execute Step 1–2 only (config+restart) vs full Step 1–3 (include first dry-run item)
- [ ] Confirm: no paid, no invent, no auto_* blast gates

**Board2 will not flip `wire_outbound` until ari sends execute ACK.**