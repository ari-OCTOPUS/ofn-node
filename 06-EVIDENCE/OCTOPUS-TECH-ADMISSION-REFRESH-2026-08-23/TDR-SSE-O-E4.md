# TDR: SSE run-event streaming (phase O-E4)

**Expected outcome going in:** a clean retraction — "already live, no code action needed."
**Actual outcome:** the capability exists, but it is **not a stream**, and my own `AUDIT.json`
overstated its readiness. This TDR corrects that. See §Correction below.

## 1. Measured problem

The original O-E4 goal: let the owner watch a chat run progress (retrieval → model →
tool → response) instead of staring at a blank box until the whole answer lands.

That goal **is** served today. `GET /api/runs/{run_id}/events` exists, is owner-authed,
returns sequence-numbered frames, and the mini-app renders a timeline from it.

## 2. What is actually implemented

`_ops/telegram_center/miniapp_gateway.py:1090-1144`

```
GET /api/runs/{run_id}          → JSON summary  (event_stream.run_summary)
GET /api/runs/{run_id}/events?after=N → Content-Type: text/event-stream
```

- Owner auth enforced first (`_owner_initdata_ok`, line 1094); 403 otherwise.
- `run_id` sanitized to `[alnum-_]{,64}` (line 1101) before touching the filesystem.
- Frames are well-formed SSE: `id: {seq}\nevent: {et}\ndata: {json}\n` (line 1135).
- Empty case emits `: no events\n\n` — a valid SSE comment frame (line 1136).
- Payload is digest/metadata only (`sequence`, `event_type`, `producer`, `status`,
  `occurred_at`, `intent`, `may_authorize:false`) — no raw text. Consistent with the
  redaction invariant enforced in `run_store.append_event` and asserted by
  `test_cognitive_events.py::t_no_raw_text_persisted`.

## 3. Correction to my own AUDIT.json

`AUDIT.json` said: *"Already implemented and live, not just planned… Remaining work per
the report (heartbeat behavior, resume-after-sequence correctness) is a test-writing task,
not a build task."*

**That was wrong on two counts**, found by reading the handler body rather than a grep window:

**(a) It does not stream.** The handler builds the complete list, joins it into one
`sse_body`, returns it, and the connection closes. There is no generator, no incremental
flush, no keep-alive loop, and **no heartbeat mechanism at all** — not a missing test, a
missing feature. It is a one-shot HTTP response wearing an `text/event-stream`
Content-Type.

**(b) `Last-Event-ID` is never read.** Resume works *only* via the `after=` query
parameter (lines 1112-1120). The SSE spec says a reconnecting client re-sends the last
`id:` it saw in a `Last-Event-ID` **header**. This server ignores that header entirely.

### Consequent latent defect

A spec-compliant `EventSource` client against this endpoint will:
1. receive all frames, 2. see the connection close, 3. auto-reconnect per spec,
4. send `Last-Event-ID`, which is ignored, so `after` defaults to `0`,
5. → `list_events(after_sequence=-1)` → **every event re-delivered**, 6. → repeat forever.

Duplicate redelivery on every reconnect, indefinitely, even for a terminated run.

**Why this has not bitten yet:** the current client does not use `EventSource`. Per
`01 - Dashboard/HANDOFF.md` (2026-08-12, entry "Cognitive Runtime v1"), `app.js` uses
*"XHR sync fetch برای event timeline"* — i.e. it polls. Polling is exactly what the server
actually implements, so client and server agree today. The defect is **latent**: it fires
the moment anyone swaps in a real `EventSource`, which is the obvious "let's do this
properly" refactor and would look like a safe change.

### Secondary: `after=` semantics are ambiguous

`after_sequence=after - 1` (line 1121) with `list_events` filtering `sequence > after_sequence`
means `after=N` returns events with `sequence >= N` — i.e. it **re-sends event N**, which the
client named as already-seen. Harmless under "give me from N onward"; an off-by-one under
"give me everything after N". The parameter name says the latter. No test pins either reading.

## 4. Why current is insufficient (scoped)

For the **owner-watching-a-run** use case: it is sufficient. Not a fiction — it works.

It is insufficient for two narrower things:
- Honest naming. A `text/event-stream` Content-Type is a promise to clients. This one
  cannot keep it.
- Long runs. Without incremental flush, the owner sees nothing until the poll interval,
  which is the exact latency problem O-E4 set out to remove — merely reduced, not solved.

## 5. Test coverage gap

`_ops/tests/test_cognitive_events.py` (10 checks) covers the **store**, not the endpoint.
It never issues an HTTP request. There is **zero** test coverage of
`/api/runs/{run_id}/events` — not of auth, not of frame format, not of `after=`, not of
reconnect. `t_list_events_after_sequence` tests `run_store.list_events` directly and
sidesteps the `after - 1` translation that the handler performs, so the ambiguity in §3 is
invisible to the suite.

Per the vault's own recorded lesson (`feedback-tested-module-zero-callers`): the store
being green says nothing about the endpoint above it.

## 6. Options

| # | Option | Cost | Note |
|---|---|---|---|
| A | Document as a poll endpoint; change Content-Type to `application/json`; rename to `/poll` | ~10 lines | Honest, kills the latent defect at the root. Breaks any client keying on the current type. |
| B | Keep the type; honor `Last-Event-ID`; add heartbeat + incremental flush | ~40-60 lines + threading | Makes the promise true. Real work; `ThreadingHTTPServer` holds a worker per open stream. |
| C | Leave as-is, add tests pinning current behavior | ~30 lines test-only | Cheapest. Pins the defect rather than fixing it — the `feedback-suite-can-pin-the-very-bug` failure mode. Not recommended alone. |

## 7. Trial threshold

None required — nothing new is being admitted. No dependency, no service, no new authority.
This is existing first-party code. The Technology Admission Gate does not apply; this
record exists to correct the status claim, not to license an install.

If option B is chosen, its acceptance bar: a real `EventSource` client reconnecting
mid-run receives **zero** duplicate sequences, and a run idle >30s emits at least one
heartbeat frame.

## 8. Rollback

- Option A: revert one commit; the XHR client is unaffected (it ignores Content-Type).
- Option B: revert to the current one-shot handler. Because the current client polls, a
  rollback from B to today's behavior is invisible to it — the client would keep working.
- Option C: n/a.

## 9. Recommendation

**Do not "adopt" anything — the ADOPT was already true.** Take **option A**, and treat it
as a naming/honesty fix rather than a feature. It is the smallest change that removes a
trap laid for the next agent, and it costs about ten lines.

Do **not** take option B unless the owner actually wants live token-level streaming into the
mini-app; it buys correctness for a client that does not exist yet, at the price of holding a
server thread per viewer.

Whichever is chosen, add the endpoint tests from option C alongside it — but write them
against the *intended* behavior, not the current behavior.

## 10. Addendum 2026-08-23 — external signal, scoped carefully

While verifying an unrelated claim for `TDR-MCP-ADAPTER-HEADERS.md`, the official
[MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
turned out to have removed exactly the mechanism option B would build:

> *"Remove SSE stream resumability and message redelivery (the `Last-Event-ID` header and
> SSE event IDs) from the Streamable HTTP transport. A broken response stream loses the
> in-flight request; clients **MUST** re-issue it as a new request with a new request ID."*

**This does not govern our endpoint.** `/api/runs/{run_id}/events` is the mini-app's private
API, not MCP. No obligation follows, and it would be an overreach to claim otherwise.

It is a **directional signal** worth one line of weight: a major protocol that had
`Last-Event-ID` resumability looked at the complexity and deleted it in favor of
re-issue-the-request. That is the same trade-off §6 poses here, resolved the same way option A
resolves it. It strengthens option A (name it a poll) and weakens option B (build
resumability), without changing the decision on its own.

---

```yaml
candidate: SSE run-event streaming (phase O-E4)
observed_problem: "none for the stated use case — capability already serves it"
baseline_evidence:
  - "_ops/telegram_center/miniapp_gateway.py:1090-1144 — endpoint live, owner-authed, sequence-numbered"
  - "_ops/tests/test_cognitive_events.py — 10 checks, store-only, ZERO endpoint coverage"
  - "01 - Dashboard/HANDOFF.md 2026-08-12 — app.js uses XHR sync fetch, not EventSource"
new_dependency: none
technology_admission_gate: not_applicable
open_defects:
  - "latent: Last-Event-ID ignored (line 1112-1120) -> spec-compliant EventSource client gets infinite duplicate redelivery"
  - "ambiguous: after=N returns sequence>=N (line 1121), re-sending event N; no test pins either reading"
  - "absent: no heartbeat, no incremental flush -- text/event-stream Content-Type is not honored"
trial_threshold: "n/a for ADOPT (no admission). If option B taken: reconnecting EventSource sees zero duplicate sequences; run idle >30s emits >=1 heartbeat frame"
rollback: "option A = revert 1 commit, XHR client unaffected; option B = revert to one-shot handler, invisible to current polling client"
decision: ADOPT
decision_qualifier: "ADOPT is retroactive/already-true, NOT a new admission. Ships with an open latent defect; recommend option A (rename to poll + correct Content-Type) as a separate honesty fix."
supersedes_claim_in: "AUDIT.json -> components_located.sse_run_events_endpoint_O_E4 (overstated readiness; corrected in section 3 of this record)"
evidence_refs:
  - "_ops/telegram_center/miniapp_gateway.py:1090-1144"
  - "_ops/cognitive/run_store.py:151-154 (list_events filter semantics)"
  - "_ops/cognitive/event_stream.py:112-131 (run_summary)"
  - "_ops/tests/test_cognitive_events.py"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/AUDIT.json"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/OWNER-REPORT.md"
status: DRAFT — awaiting owner/ari review. Not committed, not pushed.
date: 2026-08-23
```
