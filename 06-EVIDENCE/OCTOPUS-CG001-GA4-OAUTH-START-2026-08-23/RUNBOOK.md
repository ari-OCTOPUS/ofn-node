# CG-001 GA4 owner OAuth — START

stamp: 2026-08-23T16:30:50+10:00
status: IN_PROGRESS
gap_id: CG-001
connector: GA4
scope: master-painting, ziman, studio

## Rules
- Owner OAuth only (no agent-automated consent)
- No invent metrics; metrics_allowed stays false until READY_FOR_RETEST
- Vault secrets only under _ops/secrets/ (never chat)
- After OAuth: property-mapping signoff (D1/D7)

## Owner steps
1. Sign into the Google account that owns the GA4 properties for Painting / Ziman / Studio.
2. Confirm Analytics Admin access to each property (or create missing properties later — do not invent IDs).
3. Enable Google Analytics Data API on a GCP project you control (if not already).
4. Create OAuth client (Desktop or Web) OR service-account with property access — owner chooses; store client JSON under _ops/secrets/google-ga4/ only.
5. Complete consent once; save refresh token vault-only.
6. Fill PROPERTY-MAP.json with real property IDs (G-XXXXXXXX / numeric) mapped to the three businesses; sign off.
7. Tell ari → registry CG-001 moves WAITING_OWNER_OAUTH → READY_FOR_RETEST → read-only probe.

## Agent steps this session
- Open analytics.google.com for owner login handoff
- Inventory visible properties (names/IDs only) after login
- Do not claim LIVE metrics
