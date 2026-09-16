# TDR: MCP 2026-07-28 stateless revision — `Mcp-Method` / `Mcp-Name` adapter headers

> **Anchoring note.** This record cites **symbol names first**, line numbers second, per
> `_ops/octopus_mcp/CONSTITUTION.md` §4 (*"این سند نامِ نماد می‌برد … نه شماره‌خط"*) and the
> recorded lesson that the live tree can switch under a session mid-run. Line numbers are
> as-of 2026-08-23; if they have drifted, trust the symbol.

## 1. Verification status — **VERIFIED 2026-08-23** (was REPORTED_NOT_VERIFIED)

> **Update, same day.** This record was first written with the driving claim marked
> `REPORTED_NOT_VERIFIED`, because the audit had filesystem access only. The official
> changelog has since been fetched. The claim is **confirmed**, and the spec contains two
> provisions the owner report did not mention that **change this record's verdict**. §1, §6
> and §11 are rewritten accordingly; the original reasoning is preserved where it still holds.

Source: [MCP specification 2026-07-28 — Key Changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
(official), corroborated by [the 2026-07-28 announcement](https://blog.modelcontextprotocol.io/posts/2026-07-28/).

Confirmed as reported:

| Claim | Verdict | Spec wording |
|---|---|---|
| Revision 2026-07-28 exists | ✅ | Largest revision since launch |
| `initialize`/`notifications/initialized` removed | ✅ | *"Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake"* (major #2, SEP-2575) |
| `Mcp-Session-Id` removed | ✅ | *"Remove protocol-level sessions and the `Mcp-Session-Id` header from the Streamable HTTP transport"* (major #1, SEP-2567) |
| `Mcp-Method` / `Mcp-Name` mandatory | ✅ **but narrower than implied** | *"Require standard MCP request headers (`Mcp-Method`, `Mcp-Name`) **on Streamable HTTP POST requests**"* (**minor** #4, SEP-2243) |
| Roots / Sampling / Logging deprecated | ✅ | SEP-2577 |
| ≥12-month transition | ✅ | *"a minimum twelve-month deprecation window"* (SEP-2596) |

Version/capability negotiation moves into `_meta`
(`io.modelcontextprotocol/protocolVersion`, `io.modelcontextprotocol/clientCapabilities`);
mismatch returns `UnsupportedProtocolVersionError`.

**Note the headers are a *minor* change scoped explicitly to Streamable HTTP POST.** That is
the official confirmation of §4 below: they do not exist on stdio, and the report's framing
of them as the headline item inverts the spec's own emphasis.

### Two provisions the owner report omitted — both decisive

**(a) `server/discover` is a MUST, and it is the stdio backward-compat answer.**

> *"Add `server/discover`: servers **MUST** implement this RPC to advertise their supported
> protocol versions, capabilities, and identity. Clients MAY call it before any other
> request for up-front version selection, **or use it as a backward-compatibility probe on
> STDIO**."* (major #3, SEP-2575)

This is a larger obligation than the headers, and it **closes the `[UNKNOWN]` that
`MIGRATION-INVENTORY.md` §6 left open** ("what should a stateless server return to an old
client that still sends `initialize`?"). The answer: the migration is **additive** — add
`server/discover`, keep `initialize` for old clients through the 12-month window. Nothing
needs to be removed to conform.

**(b) `Last-Event-ID` and SSE event IDs were removed from MCP's transport.**

> *"Remove SSE stream resumability and message redelivery (the `Last-Event-ID` header and
> SSE event IDs) from the Streamable HTTP transport. A broken response stream loses the
> in-flight request; clients **MUST** re-issue it as a new request with a new request ID."*
> (major #9)

Scoped carefully: this governs **MCP's** transport, **not** the mini-app's private
`/api/runs/{run_id}/events` endpoint, which is not MCP. It does not bind that endpoint.
It is, however, a strong directional signal for `TDR-SSE-O-E4.md` — the ecosystem is moving
*away* from resumable SSE toward re-issue-the-request, which favors that record's option A
(treat it as a poll) over option B (build `Last-Event-ID` resumability). See the addendum there.

Also newly relevant: MCP now documents **OpenTelemetry** trace-context propagation in `_meta`
(`traceparent`, `tracestate`, `baggage`; minor #2, SEP-414), and the Logging deprecation
explicitly suggests *"log to `stderr` (stdio) or use OpenTelemetry instead"*. This does not
change `TDR-OTEL-MAPPING.md`'s verdict — that record rejects the mapping because 19 of 25
local event types have no emitter, which no external spec fixes — but it does mean an
eventual OTel decision would have MCP-side precedent.

## 2. Two different "stateless" — do not conflate them

This is the trap. `server.py` already contains something that looks like the target and is not.

| | Already implemented (`_StatelessHTTPHandler`) | Claimed 2026-07-28 revision |
|---|---|---|
| Basis | Streamable HTTP **stateless mode** of spec **2025-06-18** | A **later, distinct** protocol revision |
| Sessions | No `Mcp-Session-Id`; sending one gets `400 stateless-server-no-sessions` | Concept removed protocol-wide |
| Handshake | **`initialize` still required and answered** | **`initialize` removed entirely** |
| Routing headers | none | `Mcp-Method` + `Mcp-Name` mandatory |
| Present here? | **Yes** | **No** |

`AUDIT.json` flagged this and it bears repeating: the existing statelessness is
*session-less transport under the old handshake*. The claimed revision is
*handshake-less protocol*. Reading "we already went stateless" and closing the ticket would
be wrong.

## 3. Current state — verified in code

Server: `_ops/octopus_mcp/server.py`. There is no separate "Tool Registry" component; the
registry is the `TOOLS` dict + `_tool_defs()` + the `_handle()` dispatcher, all in this one file.

- `PROTOCOL_VERSION = "2025-06-18"` (~:43).
- `SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")` (~:45) —
  three-version negotiation, live.
- `_handle()` answers `method == "initialize"` (~:561-569), echoing the client's requested
  version when recognized, else its own. **The handshake is alive.**
- `notifications/initialized` and `notifications/cancelled` return `None` (~:570).
- No occurrence of `Mcp-Method` or `Mcp-Name` anywhere in the tree.
- Tool surface unchanged and orthogonal to all of this: `list_tree`, `read_file_slice`,
  `hash_file`, `search_hybrid`, `propose_action`.

## 4. The decisive finding — the headers have no consumer here

`Mcp-Method` / `Mcp-Name` are **HTTP headers**. Their stated benefit, per the report, is
that *a gateway can route and authorize on the header without parsing the body*.

The registered transport is **stdio**. `.mcp.json`:

```json
{"mcpServers": {"octopus-vault": {"command": "python",
  "args": ["-X","utf8","F:\\backup\\_ops\\octopus_mcp\\server.py"]}}}
```

No `--http`. Over stdio the messages are newline-delimited JSON on a pipe — **there are no
headers at all**. The benefit therefore requires all three of:

1. running the server in `--http` mode (optional, not registered),
2. an HTTP **gateway in front of it** — none exists,
3. that gateway making routing/authz decisions on the headers.

None of the three holds. Adopting the headers today is a **no-op for the real deployment**
and would add an untested code path serving zero clients — the
`feedback-tested-module-zero-callers` pattern, pre-emptively.

*(Caveat: I could not exhaustively confirm no unregistered `--http` launcher exists — a
repo-wide grep timed out on this mechanical disk. `.mcp.json` is the authoritative
registration and is stdio; treat "zero HTTP consumers" as high-confidence, not proven.)*

## 5. Authority — the constitutional constraint

`CONSTITUTION.md` §2 fixes the tool surface as read-only with `propose_action` the sole
writer, guarded by `_resolve` (resolve-then-judge) and `_denied` (`.agentignore` +
`_HARD_DENY`), fail-closed when `.agentignore` is missing. `OWNER-REPORT.md` and
`EXEC-GUIDE-CONSERVATIVE.md` both restate: **MCP is an interface adapter and never creates
new authority.**

Header-based authorization deserves an explicit warning. Moving authz decisions to a
gateway reading `Mcp-Name` would place a trust decision **outside** `_resolve`/`_denied` —
in front of the guards rather than behind them. That is precisely the shape the
constitution forbids, and the recorded lesson
`feedback-a-rejection-does-not-prove-the-rule-ran` applies: a gateway that *appears* to
enforce is not the gate. If headers are ever adopted, they must be **routing metadata only**,
with `_resolve`/`_denied` remaining the sole authority — and that must be tested from both
directions.

## 6. Cost of the change the report implies

Removing `initialize` is not additive. The registered client (Claude Code, via `.mcp.json`)
speaks 2025-06-18 and **opens every session with `initialize`**. Deleting that branch breaks
the only live consumer, immediately, in exchange for conformance to an unverified revision
whose headers nothing here can use.

`MIGRATION-INVENTORY.md` sized the edit at ~10-20 lines and recommended "Path A — minimal,
zero-dependency." That sizing is right for the *mechanics* and understates the *risk*: the
open `[UNKNOWN]` in its own §6 is exactly "what should a stateless server return to an old
client that still sends `initialize`?" Until that is answered from the spec, the edit is not
safe at any size.

## 7. Stale baseline — do not inherit the number

`MIGRATION-INVENTORY.md` records the STEP 1 baseline as
`test_octopus_mcp_search.py → FAIL 1` on `t_empty_query_is_handled`, and hypothesizes the
cause as a whitespace-only query reaching `rg` as a literal pattern.

Reading `_rg_search` today, that guard is present:

```python
terms = [t for t in query.split() if t]
if not terms:
    return [], "empty-query"
```

`_py_search` has the matching guard. **The 08-16 failure appears already fixed.** I did not
execute the suite — running it against the live tree during an audit is the
`feedback-probe-halted-the-live-organism` risk, and the exec-guide's step 1 is read-only.

Whoever does STEP 1 must **re-baseline**, not copy the 08-16 number.

## 8. Options

| # | Option | Verdict |
|---|---|---|
| A | Verify the spec claim first (fetch migration guide + changelog), change nothing | **Recommended.** The one action whose value does not depend on the unverified claim |
| B | Add `Mcp-Method`/`Mcp-Name` to the HTTP handler now | **DEFER.** Zero consumers; untested path; benefit needs a gateway that does not exist |
| C | Remove `initialize` to conform to the claimed revision | **REJECT.** Breaks the only live client, on unverified evidence, for no reachable benefit |
| D | Bump `PROTOCOL_VERSION` without removing the handshake | **DEFER.** Cosmetic; may cause a real client to negotiate a version this server does not actually implement — strictly worse than doing nothing |

## 9. Trial threshold

No admission, so no trial. The gate for *reopening* this record:

1. Spec claim verified from the official migration guide — revision date, header
   mandatoriness, transition window; **and**
2. A concrete consumer exists — the server is actually run under `--http` behind a real
   gateway with a reason to route on headers.

Both, not either. (1) without (2) is conformance for its own sake.

If reopened, acceptance must test the gate **from both directions**
(`feedback-a-rejection-does-not-prove-the-rule-ran`): a request with valid headers reaching a
denied path is still denied by `_denied`, *and* a request with absent/forged headers cannot
reach anything `_resolve` would refuse.

## 10. Rollback

Nothing to roll back — recommendation is no code change. Were option B taken, it is additive
to `_StatelessHTTPHandler` and revertible in one commit with no state migration (the server
holds no persistent state; `propose_action` writes go to the owner queue and are unaffected).
Option C's rollback is the reason to refuse it: between breaking change and revert, the
owner's MCP tooling is simply down.

## 11. Recommendation — revised after verification

Option A is **done** (§1). The claim is verified, and verification changed the answer.

**The headers stay DEFER.** Confirmed HTTP-POST-only and classified *minor* by the spec
itself. Registered transport is stdio. No gateway exists. Nothing to gain.

**Removing `initialize` stays REJECT — and is now revealed as unnecessary.** The migration
the spec actually prescribes is **additive**: implement `server/discover` (a MUST) while
keeping `initialize` for existing clients through the ≥12-month window. `server/discover`
is explicitly designed as *"a backward-compatibility probe on STDIO"*, so conformance costs
nothing in compatibility. My original reasoning — that dropping `initialize` breaks the only
live client — holds, but it was answering a question the spec does not ask.

**New, higher-priority item than anything in the owner report: `server/discover` is a MUST
we do not implement.** It is additive, ~15-25 lines in `_handle()` alongside the existing
`initialize` branch, breaks no client, needs no dependency, and is the only genuinely
required conformance gap found. It was invisible until the spec was actually read — the
owner report never mentions it.

Revised ordering:

1. **`server/discover`** — additive conformance, low risk, real obligation. Do this first.
2. `_meta` protocol-version reading — accept `io.modelcontextprotocol/protocolVersion` on
   requests while `initialize` still works. Additive.
3. Headers — DEFER indefinitely, revisit only if the server is ever run under `--http`
   behind a real gateway.
4. Removing `initialize` — not before the 12-month window closes **and** the registered
   client has migrated. No action now.

Steps 1-2 are within normal L0-L2 change scope (additive, reversible, no new authority,
no dependency). Deferred here rather than executed because this record's batch was closed at
the `run_store` fix; flagged for the next batch.

---

```yaml
candidate: MCP 2026-07-28 stateless revision -- Mcp-Method / Mcp-Name adapter headers
claim_status: VERIFIED
claim_verified_on: 2026-08-23
claim_verified_against:
  - "https://modelcontextprotocol.io/specification/2026-07-28/changelog (official Key Changes)"
  - "https://blog.modelcontextprotocol.io/posts/2026-07-28/ (announcement)"
claim_provenance_original: "owner-pasted external research; OWNER-REPORT.md self-declared citations not re-verified. Superseded by direct fetch above."
verification_outcome: "Claim CONFIRMED on all points. Headers are real but MINOR-classified and scoped to Streamable HTTP POST only. TWO omissions found in the owner report that change this record's verdict -- see below."
report_omission_1_server_discover: "server/discover is a MUST for servers in this revision (major #3, SEP-2575) and is explicitly the backward-compatibility probe on STDIO. Not implemented here. This is a LARGER and more real obligation than the headers, and it CLOSES the open [UNKNOWN] in MIGRATION-INVENTORY.md §6 -- the prescribed migration is ADDITIVE, nothing must be removed."
report_omission_2_last_event_id: "Last-Event-ID and SSE event IDs REMOVED from MCP's Streamable HTTP transport (major #9); broken stream -> client MUST re-issue as a new request. Governs MCP transport ONLY, NOT the mini-app's private /api/runs/{id}/events endpoint. Directional signal favoring TDR-SSE-O-E4 option A (poll) over option B (build Last-Event-ID resumability)."
observed_problem: "one, newly found by reading the spec: server/discover is a MUST and is unimplemented. The headers themselves remain a non-problem."
baseline_evidence:
  - "_ops/octopus_mcp/server.py :: PROTOCOL_VERSION = '2025-06-18' (~:43)"
  - "_ops/octopus_mcp/server.py :: SUPPORTED_PROTOCOL_VERSIONS = 3-version negotiation (~:45)"
  - "_ops/octopus_mcp/server.py :: _handle() answers method=='initialize' -- handshake ALIVE (~:561-569)"
  - "_ops/octopus_mcp/server.py :: _StatelessHTTPHandler rejects Mcp-Session-Id with 400 -- this is 2025-06-18 stateless HTTP MODE, NOT the claimed 2026-07-28 revision"
  - "zero occurrences of Mcp-Method / Mcp-Name in the tree"
  - ".mcp.json :: registered transport is STDIO (python -X utf8 server.py), no --http"
decisive_finding: "Mcp-Method/Mcp-Name are HTTP headers. Registered transport is stdio, which has no headers at all. The stated benefit (gateway routes/authorizes on header without parsing body) requires --http mode + an HTTP gateway in front + that gateway making authz decisions. None of the three exists. Adopting the headers is a no-op for the real deployment."
do_not_conflate:
  already_present: "session-less HTTP transport under the 2025-06-18 handshake (initialize still required)"
  claimed_revision: "handshake-less protocol (initialize removed) + mandatory routing headers"
authority_constraint: "CONSTITUTION.md §2 -- tool surface read-only, propose_action sole writer, _resolve/_denied are the authority, fail-closed without .agentignore. Header-based authz at a gateway would sit IN FRONT of those guards, creating authority outside them -- forbidden by 'MCP never creates new authority'. If ever adopted: routing metadata ONLY."
stale_baseline_warning: "MIGRATION-INVENTORY.md records test_octopus_mcp_search.py FAIL 1 (t_empty_query_is_handled) as of 2026-08-16. The guard `if not terms: return [], 'empty-query'` is present in _rg_search and _py_search today -- the failure appears already fixed. Suite NOT executed here (read-only step; probe-halted-the-live-organism risk). RE-BASELINE, do not inherit the number."
new_dependency: none for any option considered
technology_admission_gate: not_triggered
trial_threshold: "Reopen only when BOTH hold: (1) claim verified from the official migration guide/changelog -- revision date, header mandatoriness, transition window; AND (2) a real consumer exists -- server actually running under --http behind a gateway with a reason to route on headers. (1) without (2) is conformance for its own sake. If reopened, test the gate from BOTH directions: valid headers still denied by _denied on a forbidden path, and absent/forged headers cannot reach anything _resolve would refuse."
rollback: "n/a -- recommendation is no code change. Option B would be additive to _StatelessHTTPHandler, revertible in 1 commit, no state migration. Option C's rollback cost (owner MCP tooling down between break and revert) is itself the reason to refuse it."
decision: DEFER_ON_HEADERS / ACT_ON_SERVER_DISCOVER
sub_decisions:
  verify_spec_claim: DONE_2026-08-23 (claim CONFIRMED)
  implement_server_discover: RECOMMENDED_NEXT_BATCH (spec MUST; additive; ~15-25 lines in _handle(); breaks no client; no dependency)
  read_protocolVersion_from_meta: RECOMMENDED_NEXT_BATCH (additive, alongside surviving initialize)
  add_headers: DEFER (HTTP-POST-only per spec; registered transport is stdio; no gateway exists)
  remove_initialize: REJECT_NOW (unnecessary -- prescribed migration is additive; revisit only after the >=12-month window closes AND the registered client migrates)
  bump_protocol_version_alone: DEFER (cosmetic; would advertise a revision this server does not implement)
evidence_refs:
  - "_ops/octopus_mcp/server.py :: _handle, _StatelessHTTPHandler, _resolve, _denied, TOOLS, _tool_defs, _rg_search, _py_search"
  - "_ops/octopus_mcp/CONSTITUTION.md §2 (tool surface + guards), §4 (cite symbols not line numbers)"
  - ".mcp.json (stdio registration)"
  - "_ops/state/migration/MIGRATION-INVENTORY.md §3, §6 (prior inventory; open [UNKNOWN] on old-client backward-compat)"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/AUDIT.json"
  - "06-EVIDENCE/OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23/OWNER-REPORT.md"
status: DRAFT — awaiting owner/ari review. Not committed, not pushed.
date: 2026-08-23
```
