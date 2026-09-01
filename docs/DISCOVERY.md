# OCTOPUS — Discovery Guide for External Agents

**Audience:** an external agent (human or AI) encountering this system for the first
time and trying to figure out what is real, what is paper, and who has authority.
Written 2026-09-01, updated same night after the autonomy roadmap (#64) was
executed. Everything below is verifiable; verification paths are given instead of
trust claims.

---

## 1. What OCTOPUS is

OCTOPUS is an autonomous revenue system for a Sydney painting business
("Master Painting"). Its mandate, given directly by the owner (Armin, GitHub
`@ari322`, org `ari-OCTOPUS`):

> The system finds painting customers, writes quotes, sends them, and earns
> revenue **without a human in the loop**. The human is the owner, not the operator.

It is NOT a demo. The first five real outbound emails to real NSW government
painting buyers were sent by the system on **2026-09-01 13:17 UTC** (campaign
`PAINT-L5-001`, issue #48). That same day the system gained **ears** (IMAP
listener, first live reply processed), a **follow-up executor**, a **locked
quote engine** (real OCP-derived rate card awaiting one owner approval), and a
**self-running schedule** (six systemd timers: listen/heartbeat/digest/follow-up/
backup/restore-drill). The frontier is now: first human reply → first autonomous
quote → first booked revenue.

## 2. Where the bodies are buried (system map)

| Location | What lives there |
|---|---|
| `ari@192.168.0.138:~/ofn` ("the board") | Runtime. Branch `release/p0`. SQLite stores under `~/.local/share/ofn/` |
| `F:\ofn-node` (Windows workstation) | Dev clone + push relay (board's GitHub token lacks push rights) |
| `F:\backup` ("the vault") | Canonical CURRENT-TRUTH (owner vote NBB-CP), legacy legs, decision records |
| Obsidian vault `F:\backup` | Season logs, owner board: `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/` |
| GitHub `ari-OCTOPUS/ofn-node` | Code + governance (issues = decision ledger) |

Key runtime stores on the board:
- `~/.local/share/ofn/painting.sqlite` — leads CRM (5 NSW buyers: `contacted`)
- `~/.local/share/ofn/outbox.sqlite` — outbound queue (composite PK `tenant,idem_key`)
- `~/ofn/ofn/agi2027_runtime/outbound-effects.sqlite3` — **WAL / G-03 dedup**: every
  send is an effect row; `state=sent` is the single source of truth that an email left
- `~/.local/share/ofn/painting_rate_card.json` — OCP-derived rate card,
  `approved_by_owner: false` (pricing LOCKED until owner approves — ruling Q6)
- `~/.config/ofn/identity.json` — ABN/insurance fields, awaiting owner values;
  signatures read from here, nothing hard-coded
- `~/ofn/data/state/legs/lead-inbox/events.jsonl` — append-only receipts
- `~/ofn/data/state/legs/lead-send-counter.json` — daily cap counter (cap 10/day,
  owner vote 2026-07-31)
- `~/ofn/data/state/imap/last_uid.json` — IMAP cursor (uidvalidity-aware)

Autonomous schedule (systemd timers, board clock = UTC since ADR-A):
`octopus-imap` every 15 min · `octopus-heartbeat` hourly (dead-man pulse to owner
Telegram) · `octopus-digest` 21:00 UTC (=07:00 Sydney) · `octopus-followup`
01:00 UTC · `octopus-backup` 03:00 UTC (sqlite .backup + sha256 manifest, 14-day
retention) · `octopus-drill` Sundays 04:00 UTC (restore drill — first one passed
2026-09-01). Nightly backups land in `~/backups/ofn-daily/`.

## 3. Authority model (do not skip this)

1. **Owner is supreme.** Armin's explicit written votes outrank everything. Votes are
   recorded as GitHub issues (#61, #62, #63). No agent may self-certify (invariant I5).
2. **NBB-CP governs** above the six legs (owner ruling #61): persistence separate from
   prediction; vault is canonical CURRENT-TRUTH.
3. **Halt oracle is single and board-native:** env `HALT_SURVIVAL_LOOP=1` or the flag
   file `~/ofn/HALT-ALL`. `opslib.master_halted()` is fail-closed; every send checks it
   first. If you find a second kill switch, treat it as a bug.
4. **Nothing sends without passing, in order:** halt → wire flag → daily cap →
   consent/suppression → WAL dedup → SMTP. The implementation is
   `ofn/agents/outbound_worker.py:send_one` wrapping `lead_outbound_transport.py:send`.
   Any path that bypasses these is unauthorized, period.

## 4. What is REAL vs STUB (honesty section — the system's core value)

**Real and verified:**
- Email transport via Gmail app-password SMTP (`mail_credentials.py`; password value
  never logged — only the env var name is recorded)
- **IMAP listener** (`imap_listener.py`): 15-min systemd poll; classifies
  reply/bounce/optout/**autoreply** — autoresponders are logged but never flip a
  lead to engaged (learned live from a Transport NSW auto-reply on day one);
  hard-bounce `wrong_recipient` kills the campaign envelope; STOP writes a
  suppression the transport already respects (`consent_store.py` deployed)
- **Follow-up executor** (`followup_worker.py`): the +7d reminders finally have a
  runner (ruling Q4: max 2, 7 days apart, then archived — never deleted)
- **Quote engine** (`quote_engine.py`): `QT-YYYYMMDD-NNN` quotes; priced ONLY from
  the rate-card bands; 30-day validity clause; honest signature from
  `identity.json`; `book_wins()` is the first writer of `booked_amount_cents`.
  PRICED QUOTES ARE LOCKED until the owner approves the rate card (ruling Q6) —
  until then quotes go out as unpriced meeting requests
- **Rate card** (`rate_card_builder.py`): derived from 9 real OCP painting
  contracts (median $218K); `ocp_derived` vs `market_assumption` are separate keys
  — assumptions are labelled, never passed off as OCP data
- NSW OCP buyer harvester (`nsw_ocp_harvest.py`) → 5 buyers, $3.4M verified painting
  spend; source formally allowlisted in the registry (G-51 closed, basis #63)
- Demand-direction gate (`demand_harvest.py`): supply-side (job ads) harvesting is
  permanently rejected; 80 stale seek leads were cancelled, never sent to
- The email writing skill (`lead_email_writer.py`): deterministic per lead, requires a
  real OCP dollar figure (R1), blacklists bot clichés (R2), enforces ≤130 words and a
  single ask (R3/R4) — see `check()` style gate; follow-up variant has its own pool
- **Infrastructure**: six systemd timers; UTC unification (ADR-A); nightly backup
  with sha256 manifest; restore drill PASSED (first in system history); hourly
  dead-man heartbeat + 07:00 Sydney Telegram digest (both live-verified to owner)
- **Reconciliation** (`tools/reconcile.py`): 6 invariants across
  outbox↔WAL↔leads↔counter/events — all green 2026-09-01; run it before trusting
  any health claim
- Branch protection: ruleset `protect-main` active, `required_approving_review_count=1`
  (readback 2026-09-01, evidence in #51)

**Stub / not yet real (do not trust claims to the contrary):**
- All non-email channels (SMS, DM, portal submit) — deliberately stubbed
- Priced autonomous quotes — engine is live but LOCKED on owner rate-card approval
- Actual revenue — `booked_amount_cents` writer exists, no booking has occurred yet
- Learning loop: Brier score UNDECIDED at n=35 (issue #49), Phase-8 observatory
  compressed to 24h (owner vote #62)
- NSW eTendering API — awaiting owner registration on buy.nsw.gov.au; OCP bulk is the
  supplementary source until then
- Business domain / SPF-DKIM-DMARC / second transport — owner bought-in (ruling Q2),
  not yet purchased; mail still goes from the personal Gmail
- Board→GitHub push — deploy key generated (`~/.ssh/ofn_deploy.pub`) but the org
  blocks deploy keys until owner enables them; pushes relay via the Windows clone

## 5. How to verify the 5/5 send (and the live machinery) yourself

```bash
ssh ari@192.168.0.138
sqlite3 ~/ofn/ofn/agi2027_runtime/outbound-effects.sqlite3 \
  "SELECT lead_id, state, attempt_count FROM outbound_effects"
# expect 5 rows, state='sent', attempts=1
sqlite3 ~/.local/share/ofn/painting.sqlite \
  "SELECT customer_name, status, last_contacted_at FROM painting_leads WHERE lead_id LIKE '%nsw_ocp%'"
grep communication.sent ~/ofn/data/state/legs/lead-inbox/events.jsonl
systemctl list-timers --no-pager | grep octopus   # six timers, board clock UTC
python3 ~/ofn/tools/reconcile.py                  # 6 invariants, expect rc=0
sudo journalctl -u octopus-imap.service -n 20     # last listen cycle
```

The five recipients (domains): det.nsw.edu.au, transport.nsw.gov.au ×2,
dpie.nsw.gov.au, health.nsw.gov.au — all four domains were explicitly allow-listed by
owner decision (#63) before the send.

## 6. Season log 2026-08/09 (what happened, terse)

- Black-box testing → P0 Owner→Brain round-trip fix → parallel test campaigns
- Outbox rewritten to raw-key composite PK with lossless migration + fingerprint
  verification (integrity incidents #51 era; ruleset restored)
- Supply-side harvest mistake found and reversed: leads deleted, direction gate built
- Email legs recovered from vault, dependencies rebuilt (opslib shim, agi2027_control)
- Gmail app password expired → owner renewed → **5/5 real sends SENT**
- Writing skill shipped per owner mandate "it must not sound like AI"
- Governance: owner rulings #61/#62/#63 recorded; CODEOWNERS added; protection verified
- **2026-09-01 (night) — roadmap #64 executed same day:** 10 owner rulings collected
  via structured questionnaire (issue #64); IMAP listener live (first live reply was
  a Transport NSW autoresponder — autoreply class added so it can never fake
  engagement); follow-up executor; OCP rate card (9 contracts) LOCKED on owner
  approval; quote engine + first `booked_amount_cents` writer; six systemd timers;
  UTC unification; first successful restore drill; hourly heartbeat + 07:00 digest;
  G-51 closed; 80 stale supply-side outbox items cancelled; reconcile.py 6/6 green

## 7. Open items (as of this writing)

- Awaiting first human reply; first follow-up fires 2026-09-08 (7d) if silence
- Owner-side (docs/OWNER-CHECKLIST.md): ABN/insurance into identity.json · buy the
  .com.au domain · Org Settings → Allow deploy keys · buy.nsw registration ·
  one-time rate-card approval (unlocks priced autonomous quotes per ruling Q5/Q6)
- #47 governance: independent review pending (Elahe-z, PR #53 — owner chose to wait
  for genuine review; no self-approval)
- #48 campaign in flight; #49 learning loop; #61 recording-mechanism fix;
  #57 backlog (159 triaged items)

## 8. Rules for agents touching this system

1. Read `CURRENT-TRUTH.md` in the Obsidian vault before doing anything.
2. Never fake green. A test that didn't run is a failure, not a pass.
3. Never send on any path that skips the §3 ladder. No exceptions, including "just a test".
4. Priced quotes stay locked until the rate card carries `approved_by_owner: true`.
5. Autoresponders never flip a lead to engaged — the classifier class exists for a
   live-learned reason; don't "simplify" it away.
6. Record every owner decision as a GitHub issue; never decide authority yourself.
7. When the vault and your memory disagree, the vault wins (NBB-CP).
8. Run `tools/reconcile.py` before claiming the system is healthy.
9. Operative runbooks: docs/RUNBOOKS.md (Gmail app-password expiry, board push 403).
