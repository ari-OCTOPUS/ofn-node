# WF2 (approval callback) — REMOVED in v1.1. Do not recreate it in n8n.

**What v1.0 did (wrong):** an n8n workflow received the Telegram approval callback and relayed
the owner's verdict to Octopus `/gate/approve|reject|defer`. n8n therefore held a standing
credential capable of triggering gate actions.

**Why that is unacceptable (reviewer correction, 2026-07-21, accepted):** any component holding
a gate-capable credential is inside the trusted computing base for external effects. A bug,
compromise, or mis-wired workflow in n8n could approve/release effects without a human. That
violates the Octopus invariants (human acceptance mandatory; LANGAR → EffectorGate as the only
release path) in spirit even when a human pressed the button, because the *capability* exists
without the human.

**The v1.1 rule (binding):**

```
n8n → POST /api/v1/lead-candidates          ALLOWED  (signed, propose-only)
n8n → /gate/*                               FORBIDDEN
n8n → Telegram approval surface             FORBIDDEN (Octopus-owned bot)
n8n → Twilio / SendGrid / any outbound      FORBIDDEN in P0
n8n → LANGAR / effect release / settlement  FORBIDDEN, ever
```

**Where the approval flow lives now:** Octopus itself.
1. WF1 submits a signed candidate to the ingestion boundary.
2. Octopus normalises → dedupes → classifies → qualifies → renders the Telegram card
   **from its own bot**.
3. The owner's Approve/Edit/Reject callback arrives at Octopus's own webhook.
4. Verdict → LANGAR append → EffectorGate → Octopus-owned outbound worker.

**Required negative test (must exist in the P0 test suite):** "n8n has no gate credentials and
no reachable gate endpoint" — verify no n8n credential store entry, env var, or allowlisted
route can reach `/gate/*`, and that the inbox HMAC secret is scoped to candidate submission
only.

**Fallback when the Octopus HTTP surface is not yet deployed:** WF1 may create a **Gmail
draft** (never send) in the owner's own mailbox as the propose-only artifact; the owner reviews
and sends manually from Gmail. No gate semantics are simulated in n8n even in fallback mode.
