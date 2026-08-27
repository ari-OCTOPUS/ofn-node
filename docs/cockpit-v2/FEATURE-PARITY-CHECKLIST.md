# FEATURE-PARITY-CHECKLIST

## M1 read-only scope

- [ ] Command Center reads runtime, freshness, queue/cycles, incidents, policy convergence, money truth labels, Telegram mode, and pause/hold state from `/api/v2/owner/status`
- [ ] Nodes view lists exactly 138/180/182 with role, semantic role, truthful heartbeat/queue/hash/resource metadata and no identity/network secrets
- [ ] Business Legs view lists exactly DEMAND, QUALIFICATION, OFFER, CONVERSION, DELIVERY, CASH, RETENTION, FINANCE
- [ ] Queue/Cycles view is metadata-only, bounded, paginated, and contains no payload/evidence/raw error
- [ ] Audit view is redacted, bounded, filterable, paginated, and distinguishes OFN hash-chain verification from mesh sequence continuity
- [ ] Version view exposes static build/schema/mesh versions without per-request Git or subprocess work
- [ ] Missing, stale, malformed, or contradictory sources render `UNKNOWN`, `STALE`, `DEGRADED`, or `CONTRADICTED`, never fabricated zero
- [ ] Quote, booking, sale, and invoice values are never labelled verified cash
- [ ] Legacy `/` and `/index.html` panel bytes remain unchanged
- [ ] `/cockpit-v2/` uses the same owner origin and current Telegram session authentication

## Legacy features that M1 must not regress

- [ ] observability/metrics/events
- [ ] painting leads/campaigns/channels/interactions dashboards
- [ ] businesses + consent views
- [ ] ledger + settlements (money)
- [ ] brain/probe/ask
- [ ] kill/kill-release stop controls (remain only in legacy panel; V2 M1 has no command)
- [ ] approved-manual (legacy only in M1)
- [ ] marketing/run + growth-workbench (legacy only in M1)
- [ ] mini-apps/mini-webs

## Deferred by design

- Owner Control API and command receipts: M2
- Web/Telegram command parity: M2+
- Approvals, pause/resume, emergency stop, and effect execution: M2/M3
- Production exceptions and business effects: M4 after fresh E2E GREEN + Telegram canary
- SSE: M1.1; M1 uses visibility-aware ETag polling
- Old panel retirement: M5 after feature parity, owner acceptance, rollback test, and seven days observation

V2 additions with no complete old-panel equivalent: mesh nodes/cycles/witness, approvals store, policies, incidents, claim-level calibration/learning, connectors, and event stream.
