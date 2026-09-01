# OCTOPUS — Discovery Guide for External Agents

**Audience:** an external agent (human or AI) encountering this system for the first
time and trying to figure out what is real, what is paper, and who has authority.
Written 2026-09-01, end of the 2026-08/09 season. Everything below is verifiable;
verification paths are given instead of trust claims.

---

## 1. What OCTOPUS is

OCTOPUS is an autonomous revenue system for a Sydney painting business
("Master Painting"). Its mandate, given directly by the owner (Armin, GitHub
`@ari322`, org `ari-OCTOPUS`):

> The system finds painting customers, writes quotes, sends them, and earns
> revenue **without a human in the loop**. The human is the owner, not the operator.

It is NOT a demo. The first five real outbound emails to real NSW government
painting buyers were sent by the system on **2026-09-01 13:17 UTC** (campaign
`PAINT-L5-001`, issue #48). That is the current frontier.

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
- `~/ofn/data/state/legs/lead-inbox/events.jsonl` — append-only receipts
- `~/ofn/data/state/legs/lead-send-counter.json` — daily cap counter (cap 10/day,
  owner vote 2026-07-31)

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
- NSW OCP buyer harvester (`nsw_ocp_harvest.py`) → 5 buyers, $3.4M verified painting
  spend, from the official bulk registry download
- Demand-direction gate (`demand_harvest.py`): supply-side (job ads) harvesting is
  permanently rejected; 80 stale seek leads were cancelled, never sent to
- The email writing skill (`lead_email_writer.py`): deterministic per lead, requires a
  real OCP dollar figure (R1), blacklists bot clichés (R2), enforces ≤130 words and a
  single ask (R3/R4) — see `check()` style gate
- Branch protection: ruleset `protect-main` active, `required_approving_review_count=1`
  (readback 2026-09-01, evidence in #51)

**Stub / not yet real (do not trust claims to the contrary):**
- All non-email channels (SMS, DM, portal submit) — deliberately stubbed
- Quote generation → actual money (quote/deposit path not E2E yet)
- Learning loop: Brier score UNDECIDED at n=35 (issue #49), Phase-8 observatory
  compressed to 24h (owner vote #62)
- NSW eTendering API — awaiting owner registration on buy.nsw.gov.au; OCP bulk is the
  supplementary source until then

## 5. How to verify the 5/5 send yourself (no trust required)

```bash
ssh ari@192.168.0.138
sqlite3 ~/.local/share/ofn/agi2027_runtime/outbound-effects.sqlite3 \
  "SELECT lead_id, state, attempt_count FROM outbound_effects"
# expect 5 rows, state='sent', attempts=1
sqlite3 ~/.local/share/ofn/painting.sqlite \
  "SELECT customer_name, status, last_contacted_at FROM painting_leads WHERE lead_id LIKE '%nsw_ocp%'"
grep communication.sent ~/ofn/data/state/legs/lead-inbox/events.jsonl
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

## 7. Open items (as of this writing)

- #47 governance: independent review pending (Elahe-z, PR #53 — owner chose to wait
  for genuine review; no self-approval)
- #48 campaign in flight: awaiting replies; follow-up timer +7d per lead
- #49 learning loop; #61 recording-mechanism fix; #57 backlog (159 triaged items)
- Owner-side: NSW eTendering API registration

## 8. Rules for agents touching this system

1. Read `CURRENT-TRUTH.md` in the Obsidian vault before doing anything.
2. Never fake green. A test that didn't run is a failure, not a pass.
3. Never send on any path that skips the §3 ladder. No exceptions, including "just a test".
4. Record every owner decision as a GitHub issue; never decide authority yourself.
5. When the vault and your memory disagree, the vault wins (NBB-CP).
