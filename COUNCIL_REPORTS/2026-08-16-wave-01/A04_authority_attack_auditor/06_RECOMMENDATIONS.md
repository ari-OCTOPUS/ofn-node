# A04 — RECOMMENDATIONS

Ordered by risk reduction per effort. None were implemented (READ_ONLY).

## Owner decisions (blocking posture questions)
- **OD-A · Choose one authority architecture.** Either wire `octopus_v3.P0ExecutionGate` (or containment/G8) as the single choke for shell/code-apply/outbound/OpsActionEngine, or formally declare the federated model as the design and delete/mark the dead gates. Today the strongest gate is the least used. [R-3]
- **OD-B · Raw shell posture.** Options: (1) disarm (`rm` the flag — deny by default, arm per session); (2) harden (deny `python`/`pip`/redirection to source trees; move cwd to a work dir away from `.env`; require `OCTOPUS_WIRE_CB_TOKEN`-style confirmation for `/sh`); (3) accept as-is and document that `/sh` = full owner trust. Recommend (1)+(2) combined. [R-1, R-4]
- **OD-C · Turn on `OCTOPUS_WIRE_CB_TOKEN=1`.** The HMAC binding code is already written, tested, and dormant. [R-7]
- **OD-D · Route `web_research` through `fetch_guard`** (or at minimum add the UNTRUSTED_EXTERNAL_CONTENT fence + private-IP rejection + size cap) before its flag is ever set to 1. [R-2, C-5]

## Engineering (no owner decision needed, small diffs)
1. **Label untrusted context.** Add a provenance/trust marker in `retrieval_router`/`vault_bridge` outputs and wrap vault+web snippets in the existing UNTRUSTED fence when injected into prompts. Cheap, directly reduces R-2.
2. **Bind approval_id to the store.** Give `PolicyGate` an injectable `approval_verifier(approval_id, action)` (default: deny) so future composes can't pass fabricated ids. [F-005]
3. **Remove `_ops/state` from `_ALLOW_ROOTS`**, or sub-scope it to a dedicated `state/proposals/` subtree already recognised by output_guard. [R-8, R-9]
4. **Delete `.env.bak-20260810`** (or move to an encrypted/external location). It's a full secret snapshot with no consumer. [R-6]
5. **Add allowlist tests for the shell deny-list** (see 07_TEST_PLAN T3) so bypasses like `python -c` become visible regressions rather than discoveries.
6. **Consolidate PolicyGate/owner-auth implementations** to one module each; keep the second as a shim. The repo's own INV-4 note already pleads this. [F-025, C-12]
7. **Guard the kill-switch directory**: make STOP-*/ACTIVATION-* file creation/deletion audited (append-only event) so a state-writer touching them is at least visible. [R-9]
8. **board_cp**: bind default to the LAN interface actually needed instead of `0.0.0.0`, or document the firewall assumption. [R-5]

## Explicitly NOT recommended
- Do not wire v3/G8 gates mid-wave without owner vote (their own docstrings require it).
- Do not "fix" the two-brain topology or memory direction based on this audit — out of A04 scope.
- Do not disable `httpauth` CSRF guard or loopback binds — they are correct as-is.
