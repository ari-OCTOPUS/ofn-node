# DISCOVERY PACK — for external agents meeting OCTOPUS (updated 2026-09-01 night)

**You are probably an agent who was pointed at this vault/repo and told "discover
OCTOPUS". Start here, then go to the code-level guide.**

## The one-paragraph truth

OCTOPUS is an autonomous revenue system for a Sydney painting business, owned by
Armin (`@ari322`, org `ari-OCTOPUS`). On **2026-09-01 13:17 UTC it sent its first
five real business emails to real NSW government painting buyers** ($3.4M verified
painting spend, campaign `PAINT-L5-001`) through a multi-gate safety ladder with no
human touching the sends. **The same day** it gained ears (IMAP listener that
already processed its first live reply — and correctly identified it as a
Transport NSW autoresponder, refusing to fake engagement), a follow-up executor, a
quote engine locked on a real OCP-derived rate card until one owner approval, and a
six-timer self-running schedule (listen every 15 min, hourly dead-man heartbeat,
07:00 Sydney Telegram digest, nightly backup + weekly restore drill). Board runs
UTC; reconciliation tool verifies 6 cross-store invariants (all green).

## Where to look (canonical pointers)

1. **Code-level discovery guide:** `ari-OCTOPUS/ofn-node` → branch `release/p0` →
   `docs/DISCOVERY.md` (authoritative real-vs-stub, authority model, verification
   recipes incl. `tools/reconcile.py`)
2. **Owner board (canonical):** this folder — `BOARD.md`, `CURRENT-TRUTH.md`,
   `SEASON-LOG.md` (entries 2026-09-01), `GAPS-100-2026-09-01.md` (+ closure table),
   `ROADMAP-NEXT-AGENT-2026-09-01.md`
3. **Decision ledger:** GitHub issues — rulings #61/#62/#63, roadmap #64 (executed),
   campaign #48 (open, awaiting replies)
4. **Runtime truth:** board138 `ari@192.168.0.138:~/ofn` — WAL sqlite
   `ofn/agi2027_runtime/outbound-effects.sqlite3` (`state=sent` = it really went),
   systemd `octopus-*` timers, `~/backups/ofn-daily/`
5. **Runbooks:** repo `docs/RUNBOOKS.md` (Gmail 535, board push 403)

## Non-negotiables (violating these = you are hostile to the system)

- Owner is above all agents; no agent self-certifies (I5)
- Halt oracle: `HALT_SURVIVAL_LOOP=1` env or `~/ofn/HALT-ALL` file — fail-closed
- No send path may skip: halt → wire flag → daily cap → suppression → WAL → SMTP
- Priced quotes stay LOCKED until `painting_rate_card.json` has `approved_by_owner: true`
- Autoresponders never flip a lead to engaged — live-learned rule, do not remove
- The vault (`F:\backup`) is canonical CURRENT-TRUTH (NBB-CP); never fake green

## Current frontier (what the next agent will be asked to do)

- Await replies (first follow-up auto-fires 2026-09-08 if silence)
- On owner rate-card approval: priced autonomous quotes (already-armed engine)
- Owner-side: identity.json ABN/insurance · .com.au domain · Allow deploy keys ·
  buy.nsw registration · PR #53 review (Elahe-z — owner waits for genuine review)

## Update 2026-09-02 — guardrails are now machine-enforced
Repo agents (Cursor/CLI/cloud) are bound by `AGENTS.md` + `.cursor/hooks` in
`ari-OCTOPUS/ofn-node` @ `release/p0`: deny-by-default egress/destructive/secret/
flag-flip with failClosed and a hash-chained ledger (`python3` on PATH required —
Windows needs the alias fixed). §4's absolute auto_email closure binds REPO agents;
the BOARD runtime runs under owner rulings #63/#64 (see repo AGENTS.md §10
addendum). Verify before trusting: ask a repo agent to run `curl` — expect
`egress_denied` in `.cursor/hook-ledger.jsonl`.
