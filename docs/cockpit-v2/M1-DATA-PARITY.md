# M1 Data Parity — Cockpit V2

Status: implementation-time contract. Values are compared, never averaged or silently reconciled.

| Widget / domain | V1 source | V2 source | Equality rule | Expected difference / honest fallback |
|---|---|---|---|---|
| Runtime / node 138 | `/api/v1/owner/status`, `owner/observability` | `/api/v2/owner/status`, `/nodes` | Same observed health where timestamps overlap | V2 adds freshness and truth status; stale or missing evidence is `UNKNOWN`, not healthy |
| Nodes 180/182 | no complete V1 owner projection | bounded mesh metadata adapter | no false parity claim | Live remote CPU/RAM/temp/listeners are `UNKNOWN` unless a fresh local artifact proves them |
| Businesses | `/api/v1/owner/businesses` | lifecycle-leg read model using safe business aggregates | Source counts must match when comparable | V2 exposes eight lifecycle legs, not tenant pack names |
| Consent | `/api/v1/owner/consent/*` | aggregated Demand/Qualification/Retention fields | Aggregate counts only | No subject labels, names, contact data, or raw consent records |
| Ledger summary | `/api/v1/owner/ledger/summary` | status/audit source metadata | Chain status and counts must match | Mesh audit sequence continuity is not labelled a cryptographic hash chain |
| Metrics | `/api/v1/owner/metrics` | status/nodes read model | Same local 138 metrics where fresh | Missing remote metrics remain `UNKNOWN` |
| Events | `/api/v1/owner/events` (may include payloads) | audit metadata projection | Category/time/source only | V2 never emits event payloads or evidence |
| Queue / outbox | `/api/v1/owner/risks` plus mesh queue metadata | `/api/v2/owner/queue` | Counts and IDs match safe sources | V2 strips payload, evidence, raw errors, identities, and `.state.json` pseudo-messages |
| Observability | `/api/v1/owner/observability` | status/node/leg projections | Comparable counts match | Adapter failure is `DEGRADED`/`UNKNOWN`, never fabricated zero |
| Quotes | existing offer/quote events | OFFER estimated-value fields | Never counted as cash | Explicit estimate label |
| Bookings | painting booking aggregates | CONVERSION booking fields | Never counted as cash | Explicit booking label |
| Invoices | no authoritative model found in M0 | CASH/FINANCE | no fabricated value | `UNKNOWN`, not zero |
| Verified cash | provenance-valid production receipts only | CASH/FINANCE verified-cash fields | Must have trusted receipt provenance | Sale/booking/quote/invoice is insufficient |
| Contribution margin | no complete unambiguous source | FINANCE | only if every required component is proven | Otherwise `UNKNOWN` |

## Comparison procedure

1. Capture V1 and V2 responses under the same owner session and a bounded time window.
2. Compare values only when both sources are fresh and semantically equivalent.
3. If timestamps differ, retain both observations and label freshness; do not average.
4. If evidence conflicts, V2 reports `CONTRADICTED` and hides the disputed aggregate.
5. If a source is absent, unreadable, malformed, stale beyond its threshold, or semantically weaker than the widget claim, V2 reports `UNKNOWN` or `DEGRADED`.
6. Any V2 value that looks more certain than its source is a bug and blocks promotion.

## M1 parity scope

M1 proves read-side parity and truth semantics only. Command parity, Web/Telegram receipt parity, approvals, pause/resume, and effect execution remain gated to M2+.
