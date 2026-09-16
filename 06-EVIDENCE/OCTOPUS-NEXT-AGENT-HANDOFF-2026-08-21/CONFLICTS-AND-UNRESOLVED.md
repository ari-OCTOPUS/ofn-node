# Conflicts and Unresolved Items

Generated: 2026-08-21T22:19:58.680900+10:00

1. **Clean-checkout reproducibility:** tracked `tg_api.py` imports untracked `poll_lease.py`; the optional transport path depends on untracked `transport_subprocess.py`.
2. **Dirty source ownership:** valid work is mixed with live runtime churn. Preservation commit `360d436` captures source/test content without staging originals.
3. **Archived plan vs current tree:** `d301339` findings are valid for that commit, but much W1-W7 functionality landed later; never implement blindly.
4. **Poll truth:** canonical Center must expose typed outcomes; empty success must differ from 409/429/DNS/timeout/malformed.
5. **Offset:** crash-consistent, separate high-water ownership remains open.
6. **T5 supervision:** `watchdog_truth()` exists, but the PowerShell watchdog still acts from pulse age.
7. **Outbound governor:** edits and other mutations are not all routed through C4; SenderBridge remains owner-gated and unattached.
8. **Memory learning:** two-cycle fixture is green; live decision reuse and credit assignment are not operationally proven.
9. **Lab:** 8/24 cards remain INCONCLUSIVE and require cause classification, not promotion.
10. **Doctor/Survival:** measurable contracts are partial; no production self-repair claim.
11. **Mini App:** auth/nonce suites are fixture/shadow proven; live C1/C2 path needs remeasurement.
12. **Verification:** builder cannot self-sign SIG-IV.
13. **Soak:** 60-minute polling-only BLOCK_ALL soak has not been run.
