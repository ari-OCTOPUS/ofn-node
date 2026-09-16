# 06 Recommendations — A02 Runtime Investigator (CONSOLIDATED)

Evidence-based only; no rewrite proposals. Owner/governance decisions marked **[owner]**.

1. **Adopt the runtime brain inventory as canonical.** Wave-1 architects (esp. A09) should design dual-brain governance around organism-loop + cortex (the live processes), treating 4d_system as an unwired external module until separately armed. *(R-003)*
2. **[owner] Wire the octopus_v3 P0 overlay behind a shadow flag first** (per its own WIRED=False contract), so INTENT-ledger receipts start accumulating before any A2+ capability is ever allowed. Do not enable A2 enforcement and new effectors in the same change. *(R-010, RK-3)*
3. **Convert propose_only from label to check**: a single assertion point that fails the beat if a leg reporting propose_only=True invokes any effector registry entry with propose_only falsy. Small, local, no rewrite. *(R-007)*
4. **Bind board_cp to a specific LAN IP or localhost + explicit owner opt-in**; keep 0.0.0.0 out of defaults. *(RK-2)*
5. **Add tunnel/bind state to runtime truth**: channel-status should report cloudflared up/down and the 8801 bind, and stop asserting dead ports (8790/8770). Include a bus "last event age" readiness signal (events.jsonl was silent 45+ min while healthy). *(RK-5, F-21)*
6. **[owner] Purge `.env.bak-*` from repo root** (stale credentials) and confirm `.env` is git-ignored. *(RK-4)*
7. **Rename or document runtime semantics** for `frozen`, `money_link`, `epoch_mode` in a single glossary next to the ORGANISM-STATE writer code. *(RK-6)*
8. **Fix the brain_core shadow comparator** so old-side samples are produced; otherwise drop the matched=0 soak claim. *(RK-7)*
9. **Freeze the lore numbers**: identity_health is 0.542 live; all docs citing 0.572 should be regenerated from state, not hand-edited. *(R-005)*
10. **Record the boot commit-hash in ORGANISM-STATE.json** (and ideally a module-manifest digest) so running-code drift becomes detectable without archaeology; schedule owner-approved restart windows after code commits. *(F-23, RK-9)*
11. **Move the Desktop control-plane into the repo** (or a managed deploy dir) so every scheduled execution has git provenance. *(F-02, RK-10)*
12. **[owner] Reconcile autonomy flags with the propose-only narrative**: either document the bounded-automation regime (AUTONOMY_FREE/CODE_AUTOAPPLY_LOWRISK/LEAD_OUTBOUND on) or turn the flags off; keep the A2 BLOCK vote explicit and reviewed. *(F-12, R-009, RK-11)*
13. **Adopt `time.monotonic()` for beat scheduling and freshness checks** (keep wall clock only for human-readable stamps); fix the math-control `Z` mislabel; standardize one timestamp convention per artifact family (naive-local banned; explicit offset or UTC). *(F-24, RK-12)*
14. **Namespace the three beat counters** (chrono / heart-card / board) in dashboards to prevent cross-counter confusion, and refresh or tombstone board-status when the bridge is idle. *(F-29, RK-5)*
15. **[owner] Decide the authoritative approval ledger** (`_octopus` approvals vs adr-033 vs cortex cards) before any of them gains write-back power. *(F-28, RK-14)*
16. **Isolate service environments** (per-service venv) and document the co-located third-party listeners (fingagent 0.0.0.0:3653) in the threat model. *(F-26, RK-13)*

Sequencing note for A15: none of these require new autonomy; all are observability/consistency fixes except #2 and #12, which are owner decisions, and #2's execution is wave-2 scope.
