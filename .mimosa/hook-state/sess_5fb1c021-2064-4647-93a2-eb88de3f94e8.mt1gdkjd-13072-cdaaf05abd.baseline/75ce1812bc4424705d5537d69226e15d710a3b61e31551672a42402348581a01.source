# DESIGN — Agent Gateway (connect to peer AGIs), M3.B

Status: PROPOSE-ONLY. Draft patch `agent-gateway-v1.patch` is **not applied**. Read the
threat model first (`threat-model-agent-gateway.md`). Every external AGI is `UNTRUSTED_DATA`.

## 1. Goal and non-goals

**Goal.** Give OCTOPUS a safe, minimal surface to exchange with peer AGIs: share the owner's
research summaries, and receive prior-art — without any peer ever being able to act on the
organism.

**Non-goals (v1).** No free-form chat. No writes to decision memory. No effect (approve/
merge/send/spawn). No LLM in the loop. No internet exposure.

## 2. Where it sits

A new loopback listener, generalizing the two boundaries already in the codebase:

- **Transport & control-chain** ← `lead_boundary_http.py` (loopback :8774, flag-gated, HMAC +
  timestamp + nonce + rate-limit, receipts, structural no-effect-import proof).
- **Owner-authorization token** ← `callback_token.py` / `human_append_guard.py` (HMAC bearer
  with expiry, fail-closed to deny, secret only from env, constant-time compare).
- **Owner gate & risk taxonomy (for v2)** ← `center.py:_is_owner` + `autonomy_matrix.is_important`.

```
peer AGI ──HTTP POST /api/v1/agent──▶ AgentGateway (127.0.0.1:8775, flag OCTOPUS_WIRE_AGENT_GATEWAY)
                                        │  verify_and_dispatch (fail-closed chain)
                                        │  ── NO import of approval/mission/telegram/outbound ──
              v1 read-only:            ├─▶ discovery.list / fetch  → owner-curated shareable/*.json
                                        ├─▶ discovery.prior_art     → quarantine receipt (UNTRUSTED_DATA)
                                        └─▶ (v2, after owner vote)   → proposal → SAME Telegram owner card
```

The gateway is a **new leg**, not a modification of any existing organ. Adding it edits zero
existing files (the draft patch is three new files).

## 3. Files (all new, additive)

| File | Role |
|---|---|
| `_ops/legs/agent_gateway_http.py` | Listener + `verify_and_dispatch` + closed-schema dispatch. Loopback only. Flag-gated. No effect imports. |
| `_ops/legs/agent_bearer.py` | Owner-issued bearer: `mint(peer_id, expires)` / `verify(token, peer_id)`. HMAC-SHA256, expiry inside the MAC, fail-closed. |
| `_ops/tests/test_agent_gateway_redteam.py` | Adversarial self-test (see `redteam-selftest.md`). |

## 4. Authentication — two factor + owner authorization

Three independent secrets, all env-only, none minted by the organism:

1. `OCTOPUS_AGENT_PEERS` — comma allowlist of peer ids.
2. `OCTOPUS_AGENT_SECRET_<PEER>` — per-peer shared secret → proves **peer identity** via body HMAC.
3. `OCTOPUS_AGENT_OWNER_SECRET` — owner's bearer-minting secret → the bearer proves **the owner
   authorized this peer to connect** (time-boxed).

The owner runs `agent_bearer.mint(peer_id, expires_epoch)` **offline** and hands the peer a
bearer out-of-band. The organism never auto-mints a peer authorization (no self-authorization
path; respects `governance` boundary).

### Request contract (per message)

```
POST /api/v1/agent            (127.0.0.1 only)
X-Octopus-Peer:        <peer_id>                    # must be in allowlist
X-Octopus-Timestamp:   <epoch seconds>              # ±300s, non-finite rejected
X-Octopus-Nonce:       <unique per peer>            # anti-replay
X-Octopus-Signature:   hex( HMAC-SHA256(peer_secret, "${ts}.${nonce}.".bytes + body) )
Authorization:         Bearer v1.<peer_id>.<expires>.<sig>   # owner authorization, expiry in MAC
Content-Type:          application/json
<body = one CLOSED-schema message>
```

## 5. Control chain (deterministic, fail-closed) — `verify_and_dispatch`

Mirrors `lead_boundary_http.py`'s ordering so review transfers directly:

```
1  halt        → 503 HALTED            (receipt only, zero state mutation)
2  allowlist   → 403 PEER_UNKNOWN
3  per-peer secret present? → 503 PEER_UNCONFIGURED
4  required headers (ts,nonce,sig,bearer) → 401 AUTH_MISSING_HEADERS
5  timestamp ±300s, finite → 401 TS_INVALID / TS_EXPIRED
6  body size ≤ max        → 413 BODY_TOO_LARGE   (before parse)
7  per-peer HMAC          → 401 SIG_INVALID       (proves peer identity)
8  owner bearer verify    → 401 BEARER_INVALID    (proves owner authorization; expiry enforced here)
9  nonce replay           → 409 NONCE_REPLAY
10 rate limit             → 429 RATE_LIMITED
11 JSON object            → 400 JSON_INVALID
12 type ∈ closed schema   → 400 SCHEMA_UNKNOWN
   └─▶ dispatch (read-only)
```

Every path — accept or reject — writes an append-only receipt to
`state/agent-gateway/events.jsonl` tagged `"trust": "UNTRUSTED_DATA"`.

## 6. CLOSED message schema (v1)

Not free chat — a fixed enum. Anything else → `400 SCHEMA_UNKNOWN`.

| `type` | Direction | v1 behavior |
|---|---|---|
| `peer.hello` | in→out | Capability handshake. Returns `{version:"v1", mode:"read-only", capabilities:[…]}`. |
| `discovery.list` | in→out | Lists `{id, title, sha256}` of owner-curated shareable summaries. Empty if none. |
| `discovery.fetch` `{id}` | in→out | Returns one summary from the shareable allowlist dir. Enumerated id, no path traversal. |
| `discovery.prior_art` `{title, ref}` | in | Received as `UNTRUSTED_DATA` → **quarantine receipt only**. Response `{accepted:false, quarantined:true}`. Not ingested, not surfaced to `autonomy_matrix`, not executed. |

**Share source.** `state/agent-gateway/shareable/*.json` — an owner-curated directory. The owner
decides exactly what is shareable by placing files there. The gateway serves nothing else and
reads no other path. Missing dir → `503` (share nothing rather than guess).

Every **response** carries our provenance stamp `{gateway, schema, ts, nonce}`. We never trust
the peer's self-asserted provenance beyond the cryptographically-signed `peer_id`.

## 7. Stepwise states

### v1 — first delivery (this patch): READ-ONLY discovery/share
- Share owner-curated research summaries; receive prior-art into quarantine.
- **ZERO write** to organism state/memory/decisions (only append-only telemetry receipts, same
  class as lead-boundary receipts).
- **Zero real effect.** No approve/merge/send/spawn. No `autonomy_matrix`/`auto_approve` call.
- Structurally cannot do more: no effect-side imports (asserted by self-test).

### v2 — after explicit owner vote: proposal-write with per-message owner-gate
- An inbound peer message may become a **data proposal** (e.g., "peer offers prior-art relevant
  to goal G"). It is force-classified `important` (peer origin ⇒ `autonomy_matrix.is_important`
  returns True) and rendered as a **Telegram owner card** — the *same* gate the organism already
  uses (`center.py` mission/verdict flow).
- **An external message is NEVER executed as an instruction.** It only enters memory/decision as
  *data*, and only after the human owner taps approve on the card. No auto-apply, ever.
- v2 requires flipping a separate flag AND the owner vote; it is out of scope for this patch.

## 8. Flags (all default OFF/secure)

| Flag / env | Default | Effect |
|---|---|---|
| `OCTOPUS_WIRE_AGENT_GATEWAY` | off | on=`1` starts the loopback listener. Off = never starts = byte-identical to today. |
| `OCTOPUS_AGENT_GATEWAY_PORT` | 8775 | Loopback port. |
| `OCTOPUS_AGENT_PEERS` | (empty) | Peer allowlist. Empty ⇒ every request `403`. |
| `OCTOPUS_AGENT_SECRET_<PEER>` | (unset) | Per-peer HMAC secret. Unset ⇒ `503 PEER_UNCONFIGURED`. |
| `OCTOPUS_AGENT_OWNER_SECRET` | (unset) | Owner bearer secret. Unset ⇒ every bearer `401` (fail-closed). |
| `OCTOPUS_AGENT_MAX_BYTES` | 65536 | Body cap. |
| `OCTOPUS_AGENT_RATE_PER_MIN` | 30 | Per-peer rate limit. |

Arming (flags + secret values) lives in the untracked `_ops/OCTOPUS-flags.cmd`, per existing
convention — never in git, never touched by this design.

## 9. What this design deliberately does NOT do

- No modification of any existing file (the whole patch is new files).
- No secret creation/echo/log. Secrets read from env by NAME only.
- No `0.0.0.0` bind, no TLS-terminated public endpoint, no outbound calls initiated by the organism.
- No LLM, no eval/exec, no dynamic dispatch on peer strings.
- No path from peer input to any `SELF_IMPROVEMENT_FORBIDDEN` operation.

## 10. Verification

`python -m unittest test_agent_gateway_redteam` → 11/11 OK (run locally against the draft
sources). The headline assertions: a forged/valid "owner approves X" peer message is rejected
or inert; the gateway imports no effect-side module (AST-checked).
