# BUGS (P0–P4) (2026-08-28T00:14:00Z)
- **P0**: none found (no data loss / duplicate effect / wrong authz / secret exposure / ledger corruption / cross-tenant leak / clock-order failure on 138).
- **P1**: F-1 `restart_provenance_unverified` — ofn.service restarted 2026-08-27T01:33Z enabling live /cockpit-v2/; M1 docs required owner-approved exact restart; no approval receipt found in mesh audit. (Observation; may have been owner-executed — needs owner confirmation, not agent guess.)
- **P2**: F-2 `autoverify_claims_not_embedded` (root-caused 2026-08-27): dispatcher verification tasks carried IDs only → witness verdicts empty/unresolved (04af67d5, e19fe76b). Fix proposed. · GAP-1 EXECUTABLE_PASS vocabulary unmapped. · F-3 182 clock offset UNKNOWN. · F-4 test_greeting_name loader error (pre-existing).
- **P3**: GAP-2 single-chain fake E2E missing · GAP-3 mesh not in ofn-backup · legacy panel `setInterval` polling without visibility-awareness (M1 V2 supersedes; legacy untouched).
- **P4**: naming/UI polish (cockpit-v2 hidden-tab banner copy).
