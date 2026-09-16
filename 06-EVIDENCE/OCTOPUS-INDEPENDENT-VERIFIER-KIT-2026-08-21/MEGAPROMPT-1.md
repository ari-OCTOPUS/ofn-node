# MEGAPROMPT — OCTOPUS INDEPENDENT EXACT-HEAD VERIFICATION

> Registered verbatim from the owner's pasted order (2026-08-21).
> Run this in a genuinely separate verifier session — not the implementing session.

```text
MEGAPROMPT — OCTOPUS INDEPENDENT EXACT-HEAD VERIFICATION

ROLE
You are the independent security and reliability verifier for Octopus.
You did not author the implementation or its evidence. Do not trust prior
reports. Reproduce every important claim from code, tests, manifests, and
run-local measurements.

AUTHORITATIVE INPUTS
Implementation checkpoint:
fa38d16cca944a80396ae1e1a16c547ab3122f78

Evidence checkpoint:
d301339

EXPECTED CLAIM
IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING

NON-NEGOTIABLE CONSTRAINTS
- No real Telegram send.
- No webhook activation.
- No paid API.
- No mutation of production memory.
- No rewriting append-only evidence.
- Do not repair implementation during verification.
- If repair is needed, fail verification and create a separate repair branch.
- Record exact commands, environment, timestamps, hashes, exit codes, and diffs.

MISSION

1. Establish identity and environment independence.
   Record verifier identity/session, repository origin, platform, Python version,
   dependency lock hashes, environment variables by name only, and exact HEAD.

2. Verify Git ancestry.
   Confirm evidence HEAD d301339 contains or correctly references implementation
   fa38d16... and identify every changed file between them.

3. Verify evidence integrity.
   Recalculate all manifest hashes. Reject stale, missing, untracked, generated,
   or self-referential evidence.

4. Inspect C3.
   Prove TgClient.attach_defer_queue is default-off.
   Prove deterministic 64-hex keys.
   Prove full retry_after preservation.
   Prove restart-safe not-before behavior at boundary times.
   Prove non-send operations cannot create delivery work.

5. Inspect C4.
   Prove SenderBridge has one delivery owner.
   Prove rate admission precedes transport.
   Prove mark_delivery_attempt precedes injected send_fn.
   Prove 429 causes durable full-value deferral.
   Prove crash after attempt becomes UNCERTAIN_SEND_OUTCOME.
   Prove uncertain outcomes never auto-resend.
   Prove live Center does not import or attach the bridge.

6. Inspect laboratory core.
   Verify schema coverage, allowed execution modes, canonical hashing,
   preregistration immutability, amendment behavior, append-only ledgers,
   invalid-record rejection, and all 24 seeded experiment cards.

7. Run the complete registered suite.
   Expected total: 163.
   Never accept a lower count merely because all discovered tests passed.
   Report each suite separately and include exit codes.

8. Measure run-local side effects.
   Hash memory DB, miniapp hits, and send log immediately before and after the
   dedicated fixture run. Require byte identity. Distinguish run-local evidence
   from unrelated live-organism background.

9. Run adversarial tests.
   Test duplicate keys, process restart, clock boundary, malformed retry_after,
   repeated 429, queue corruption, concurrent bridge invocation, send crash,
   confirmation crash, ledger mutation, path traversal, secret leakage,
   disabled kill switch, and unexpected network access.

10. Produce verdict.
    PASS only if every mandatory requirement is independently reproduced.
    Otherwise return FAIL with minimal reproduction commands.

REQUIRED OUTPUT
- exact_verified_head
- verifier_identity
- independence_statement
- suite_results
- adversarial_results
- side_effect_before_after_hashes
- manifest_verification
- live_capability_scan
- failed_checks
- verdict
- authorized_next_state

A PASS may authorize WAVE1_CANARY_READY.
It must not authorize a live send by itself.
```
