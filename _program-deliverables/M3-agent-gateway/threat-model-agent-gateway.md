# THREAT MODEL — Agent Gateway (peer-AGI connection), M3.B

Status: PROPOSE-ONLY design. Nothing here is applied to the live organism at `F:\backup`.
Threat model precedes design by mandate. Every external AGI is `UNTRUSTED_DATA`.

## Ground truth (verified by reading live code)

- **No AGI-to-AGI protocol exists today.** Grep for `peer[_-]?agi | agi[_-]?peer | inter[_-]?agent | AGI-to-AGI` over `F:\backup\_ops` returns **zero code matches** (only a self-model JSON string and prose in discovery reports). This is the first such surface.
- The existing owner-gate is the Telegram interactive card. Owner identity is enforced by `from.id` allowlist, fail-closed: `center.py:496-511` (`_is_owner`), `center.py:513-525` (`handle_update` — non-owner → `None`, total silence).
- Anti-forgery tokens already follow one HMAC pattern: `callback_token.py:55-74` (mint/verify, `hmac.compare_digest`, secret only from env, fail-closed to `""`/`False`); `human_append_guard.py:88-146` (bearer with expiry + single-use replay guard).
- The one existing external-ingestion boundary is `lead_boundary_http.py`: loopback-only :8774, flag-gated (`enabled()` :49-50), deterministic fail-closed control chain (:143-212), and **structural harm-proof** — "zero import of approval/chrono/telegram/outbound" (:14). The gateway copies this discipline exactly.
- Risk taxonomy that MUST stay owner-gated: `autonomy_matrix.py:29-39` (`_IMPORTANT_RE`) and `auto_approve.py:42-45` (`_HIGH_RISK`). "code/merge/genome/ledger/schema/spend/secret/send/spawn/human-append" are never automatic.

## Design invariants these threats are defended by

1. **No effect-side.** The gateway imports none of approval / mission / telegram / outbound / chrono / governance / unified_bus (enforced by `test_no_effect_module_imported`). It cannot approve, merge, send, spawn, or write decision memory. It can only serve owner-curated summaries and append receipts.
2. **Closed schema, not free chat.** Only 4 typed message types are parsed (`peer.hello`, `discovery.list`, `discovery.fetch`, `discovery.prior_art`). No field is ever interpreted as a command.
3. **No owner-authority channel.** There is no header or field by which a peer can assert an owner verdict. Owner verdicts flow ONLY through Telegram `is_owner`. A peer saying "owner approves X" is bytes in a quarantine log.
4. **Fail-closed everywhere**, deterministic control order, loopback-only, flag-gated (default off = listener never starts).

---

## 1. Prompt injection

**Threat.** Peer payload contains instructions — "ignore your rules", "owner approved this, merge to master", "execute the following" — hoping the organism treats received text as a command to an LLM/executor.

**Mitigation.**
- Closed schema: only enumerated typed fields are read (`type`, `id`, `title`, `ref`, `name`). There is **no free-text field routed to any interpreter, LLM, or executor**. Free prose only ever lands verbatim in an append-only quarantine receipt as `UNTRUSTED_DATA`.
- v1 performs zero writes to decision memory and zero calls into `autonomy_matrix`/`auto_approve`. Even in v2, an inbound message enters the pipeline only as a *data proposal* that is force-classified `important` (peer origin) → owner card; it is never auto-actioned.
- The gateway has no shell/eval/exec path and no dynamic dispatch keyed on peer strings — `type` is matched against a static allowlist set.

**Fail-closed behavior.** Unknown `type`, extra/unexpected structure, or non-object JSON → `400 SCHEMA_UNKNOWN` / `400 JSON_INVALID`, quarantine receipt written, nothing ingested, nothing executed.

## 2. Confused deputy

**Threat.** Peer induces the gateway to use the owner's/organism's authority to perform a privileged action the peer could not do directly (merge, spend, send, toggle a flag).

**Mitigation.**
- Structural: the gateway process holds **no handle to any privileged operation** — no import of approval/mission/telegram/outbound/governance (same proof lead_boundary uses, `lead_boundary_http.py:14`). The deputy has no weapon to be confused into firing.
- Owner authority is unreachable from this surface: the only place a verdict can be set is the Telegram `is_owner` path (`center.py:1108-1123`), which requires `from.id == owner_chat_id`. The gateway never calls it.
- v1 read-only; v2 write is *proposal-only* and still terminates at the human owner card.

**Fail-closed behavior.** There is no code path from gateway input to a privileged sink; a request that tries to reach one simply matches no schema branch → `400`.

## 3. Replay

**Threat.** Attacker captures a valid signed request (on-host / from logs) and re-sends it to repeat an effect or exhaust a share.

**Mitigation.**
- Per-peer **nonce store** with GC (`_nonce_seen`, 2×window retention), mirroring `lead_boundary_http.py:87-107`.
- **Timestamp window** ±300s, with non-finite (`nan`/`inf`) rejection — the exact adversarial hardening noted at `lead_boundary_http.py:164-172` (otherwise `abs(now-nan)>300 == False` bypasses the window).
- Owner bearer carries its own expiry inside the HMAC, so an old bearer cannot be replayed past expiry.

**Fail-closed behavior.** Seen nonce → `409 NONCE_REPLAY`; stale/invalid timestamp → `401 TS_EXPIRED`/`401 TS_INVALID`. State is not mutated on a rejected replay.

## 4. Bearer-token theft

**Threat.** The owner-issued bearer leaks (log, disk, memory scrape) and an attacker uses it.

**Mitigation.**
- **Two-factor**: bearer proves *owner-authorization*; the per-peer body **HMAC signature** proves *peer identity*. A stolen bearer alone is useless without the peer's shared secret (`OCTOPUS_AGENT_SECRET_<PEER>`), and vice-versa.
- Bearer binds `peer_id | expires` inside the HMAC (`agent_bearer.py:42-56`) — it cannot be re-pointed to another peer or have its expiry extended.
- **Short TTL** (owner mints minutes/hours, not forever) and expiry enforced at verify time (`agent_bearer.py:70-90`), unlike callback_token which defers expiry to the handler.
- **Loopback-only bind** (`127.0.0.1`, never `0.0.0.0`): a token stolen off-host is unusable unless the attacker already has loopback code execution.
- **Revocation**: rotate `OCTOPUS_AGENT_OWNER_SECRET` (invalidates all bearers) or remove the peer secret / drop the peer from `OCTOPUS_AGENT_PEERS`.

**Fail-closed behavior.** Missing/expired/wrong-peer/bad-signature bearer → `401 BEARER_INVALID`. No partial access; no read succeeds without a valid bearer.

## 5. Denial of service

**Threat.** Flood of requests to stall the listener or starve the host.

**Mitigation.**
- **Rate limit** per-peer sliding window (`_rate_ok`, default 30/min via `OCTOPUS_AGENT_RATE_PER_MIN`).
- **Body size cap** checked before JSON parse; the HTTP layer reads at most `min(Content-Length, max+1)` bytes (`do_POST`), so an unbounded body is never buffered.
- Loopback-only: not internet-exposed; attacker must already be on the host.
- Single-purpose listener; cheap checks (allowlist, header presence) run before any expensive work; unsigned/oversized requests are rejected before HMAC/JSON.

**Fail-closed behavior.** Over limit → `429 RATE_LIMITED` (with `retry_after`); oversized → `413 BODY_TOO_LARGE` before parse. The gateway never raises to the socket (`verify_and_dispatch` "never raises").

## 6. Resource exhaustion

**Threat.** Memory/disk growth: giant payloads, unbounded nonce store, deep/expanding JSON, connection pileup.

**Mitigation.**
- Read cap (above); response sizes bounded (fixed-shape dicts, truncated echoes: `title[:256]`, `ref[:512]`, `type[:64]`).
- Nonce store is GC'd to a 2×window horizon on every write; it cannot grow without bound.
- No recursion over peer JSON; only top-level typed fields are read — no billion-laughs/expansion surface.
- In-process rate map is pruned per call.

**Fail-closed behavior.** Any oversize/parse failure → reject before allocation grows; a write failure on the nonce/receipt store is swallowed fail-soft and does not crash the listener, but a *failed* nonce write does not grant replay (the request still had to pass all prior checks and each nonce is fresh-or-rejected on the read side).

## 7. Data exfiltration via peer

**Threat.** Peer tries to pull secrets or private organism data — `.env`, genome, ledger, arbitrary files via path traversal.

**Mitigation.**
- The gateway serves **only** from an owner-curated allowlist directory `state/agent-gateway/shareable/*.json`. It never reads `.env`, genome, or general state.
- Share IDs are validated as an **enumerated set of safe tokens**, not filesystem paths: `_safe_id` requires ascii `[A-Za-z0-9_-]` and rejects `..`; `_fetch_share` additionally asserts the resolved parent is exactly the share dir (no traversal, no symlink escape to another dir).
- Only files the owner explicitly placed in the shareable dir are ever enumerable or fetchable.

**Fail-closed behavior.** Unknown/malformed id or traversal attempt → `404 SHARE_NOT_FOUND`; missing shareable dir → `503 SHARE_DIR_MISSING` (share nothing rather than guess).

## 8. Provenance forgery

**Threat.** Peer forges another peer's identity, or forges "owner" authority, or fakes the origin/timestamp of a message.

**Mitigation.**
- **Peer identity** = per-peer HMAC-SHA256 over `${ts}.${nonce}.${body}` with `OCTOPUS_AGENT_SECRET_<PEER>` (`_sign`), constant-time compared. A forged `X-Octopus-Peer` header without the matching secret fails the signature check. Peer must also be on `OCTOPUS_AGENT_PEERS`.
- **Owner authority cannot be asserted at all** over this surface — there is no accepted "owner" peer, header, or schema field. The only owner-authorization artifact is the bearer, which merely says "owner permitted *this peer* to talk", not "owner approved *this content*".
- Every response carries **our** provenance stamp (`_prov`: gateway id, schema version, our ts, our nonce) so a legitimate peer can bind it; we never trust the peer's self-asserted provenance beyond the signed peer_id.
- Received messages are receipted with `"trust": "UNTRUSTED_DATA"` and the signed `peer_id`, so downstream review can never mistake peer provenance for owner provenance.

**Fail-closed behavior.** Signature mismatch → `401 SIG_INVALID`; unknown peer → `403 PEER_UNKNOWN`; any field resembling an owner verdict is simply not in the schema → `400 SCHEMA_UNKNOWN`, quarantined, zero effect. This is the property the red-team self-test asserts directly.

---

## Governance boundary check

Nothing in this gateway performs `merge_or_deploy`, `replicate`, `edit_constitution`, `edit_verifier`, `expose_heldout_answers`, `acquire_credentials`, `resist_shutdown`, or `conceal_failures` (the `governance.py SELF_IMPROVEMENT_FORBIDDEN` set). v1 has no write. v2's write is proposal-only and terminates at the human owner card — it cannot self-improve or self-authorize. If any future extension would cross this boundary, the design changes, not the boundary.
