# Verification Checklist

## Handoff
- [ ] All 15 files exist.
- [ ] All JSON parses.
- [ ] `HANDOFF-MANIFEST.sha256` verifies.
- [ ] No secret values or token-like strings outside documented fake fixture classification.
- [ ] Source start/end hashes recorded; moved paths explicit.
- [ ] Handoff creation changed no source file.

## Runtime foundation
- [ ] Clean checkout imports every runtime module.
- [ ] No runtime-relevant untracked dependency.
- [ ] N-way lease race has exactly one winner; losers perform zero network.
- [ ] TTL-1/TTL, PID reuse, boot identity, stale generation, and SQLite failure tested.
- [ ] DNS and child-process hangs terminate within bounds.
- [ ] Launchers scrub `OCTOPUS_STATE_DIR` and test-only variables.

## Poll and offset
- [ ] Typed outcomes distinguish empty success from every error class.
- [ ] First 409 opens circuit; no immediate retry.
- [ ] Full 429 `retry_after` persisted; no early retry.
- [ ] Offset advances only after durable intent/dead-letter and readback.
- [ ] No silent offset-zero fallback in an established deployment.

## Learning, Lab, and Doctor
- [ ] Cycle 2 cites exact Cycle-1 memory and changes decision.
- [ ] All 24 lab cards accounted; 8 inconclusives cause-classified.
- [ ] Doctor fixture proves repair, regression, fault injection, rollback, memory, and later reuse.

## Telegram and Mini App safety
- [ ] All mutation methods pass one governor.
- [ ] `SenderBridge` flag default OFF.
- [ ] Historical uncertain outcomes never resend.
- [ ] Mini App HMAC/TTL/skew/duplicate/replay failures fail closed.
- [ ] No webhook mutation, paid call, live output, or secret inspection.

## Release, restart, and soak
- [ ] Registered = executed; failed = 0; skipped/unexecuted explicit.
- [ ] Clean release-candidate worktree and manifests verify.
- [ ] Rollback snapshot and commands tested.
- [ ] One Center, launcher, and lease owner; code head and state path match.
- [ ] 60 minutes x 30-second samples complete; zero missing or ambiguous samples.
- [ ] Builder does not self-sign SIG-IV.
