# LANE-REPORT — AIRTASKER-WATCH-20260908

GOV_VERSION=V8 · LADDER=L2 · lane: AIRTASKER-WATCH-20260908 · closed: 2026-09-08
Session scope: discovery lane, read-only on external world + lane-folder writes
only. No ofn-node file touched. No wire flag touched. No telegram/email send.
No login. No anti-bot interaction (see PROBE-20260908.md).

## What was done

1. **Channel map** (Phase 0.1) — `CHANNEL-MAP.md`. Four official alert
   channels documented from Airtasker Support Centre: task alerts
   (location/keywords), notification preferences, SMS (after phone verify),
   app push. **All latency + payload values: status unverified** (no real
   sample yet). No guessing.
2. **imap_listener analysis** (Phase 0.2) — read
   `F:\ofn-node\ofn\agents\imap_listener.py`. Key fact: unknown senders fall
   into `classify()`'s `noise` branch untouched (no \Seen, no delete) — that
   fall-through is the exact integration point for the airtasker branch.
   Listener contract absorbed: idempotent, receipts in events.jsonl, dry-run
   first, never raise.
3. **Probes** (Phase 0.3) — `PROBE-20260908.md`. Registry search URL → **404
   (stale, schema_drift)**; site root → **302 normal, no challenge**. Honest
   UA, HEAD, one shot each, no retry. Verdict: not BLOCKED — the registry
   URL is dead. Matches the pre-registered ACD-07F-dev-10 fault class.
4. **Parser written + tested** (Phase 1) — `airtasker_alert_parser.py`,
   `test_airtasker_alert_parser.py`. Real run: **pytest 8/8 passed**
   (2026-09-08). One real bug caught and fixed by tests (budget text bled
   across list items; now block-scoped). Parser: zero network, never raises,
   never fabricates (missing → None/—), sender-gated, supply_risk direction
   flag, dedupe by URL.
5. **Pipeline design** (Phases 1–3) — `PIPELINE-DESIGN.md`. Wiring plan into
   imap_listener → painting.sqlite → direction gate → TG card with receipt;
   draft-pen sketch (owner-commanded, local model, manual send only);
   rhythm histogram spec.

## Capability grades (honest)

| Capability | Grade | Basis |
|---|---|---|
| Channel existence (4 official channels) | E2 | Official support articles read 2026-09-08 (existence), no runtime test |
| Alert latency / payload shape | E0 unverified | No real sample; measurement plan in CHANNEL-MAP.md |
| airtasker_alert_parser on designed input | **E2** | 8/8 pytest on designed fixtures |
| Parser on REAL alert email | **E0 pending** | Blocked on owner saving one real .eml (see below) |
| Registry URL liveness | E2 (measured) | 404 stale; root 302; headers recorded 2026-09-08T03:02–03:04Z |
| Digest pipeline end-to-end | E0 | Design only — wiring needs owner GO lane |
| Draft pen | E0 | Sketch only |
| Latency posted→seen | no data | UNDERPOWERED regime until n≥30 |

## What failed / friction

- WebFetch to support.airtasker.com returned 403 (Cloudflare); web_reader
  fallback worked — noted for future research lanes.
- First pytest run failed 1/8 (budget cross-contamination) — fixed by
  block-scoped context window; this failure is itself evidence the
  fail-closed contract is being enforced by tests, not by hope.

## Rollback

All lane artefacts live in this folder only; deleting the folder fully
reverts the session. No external effect exists to roll back (2 HEAD probes
with honest UA are the only outbound touch).

## Remains open (requires owner decision — AGENTS.md §6)

1. **Enable alert channels on your Airtasker account** (task alerts: Painting
   + Sydney keywords; email + push on; optional SMS) — only you can do this;
   it is the sanctioned pipeline's intake.
2. **Provide one real alert email**: forward it to the watched Gmail, or save
   as `.eml` into this lane folder → unlocks parser E2-real + payload map.
3. **GO for wiring lane**: a follow-up lane (own worktree, pre-image
   receipts) adds the airtasker branch to imap_listener + painting.sqlite
   insert + TG card via outbox. Nothing sent until you approve the first
   dry-run output.
4. **Registry fix (ofn-node, other lane's property)**: mark
   `airtasker_painting.probe_url` DEAD (404 stale) or point it at a
   supervised-browser-determined URL. Staged as a suggestion only.
5. Optional: **SMS channel** — your verified number can receive task SMS;
   that path bypasses email entirely (parser for SMS would be a separate,
   later decision).

## Evidence paths

- 09-LANES/AIRTASKER-WATCH-20260908/CHANNEL-MAP.md
- 09-LANES/AIRTASKER-WATCH-20260908/PROBE-20260908.md
- 09-LANES/AIRTASKER-WATCH-20260908/airtasker_alert_parser.py
- 09-LANES/AIRTASKER-WATCH-20260908/test_airtasker_alert_parser.py (8/8 green)
- 09-LANES/AIRTASKER-WATCH-20260908/PIPELINE-DESIGN.md
