# L9 PASS CRITERION (written before scanning outputs)
Lane: L9 Infrastructure hardening proposals
Written: 2026-09-01T23:50:00+10:00
Read-only: yes except 09-LANES/L9/
Forbidden: /etc/, src/, applying firewall changes
Depends on: none

This lane PASSES iff all of:
1. PASS-CRITERION.md hashed before drafting proposals from evidence.
2. Proposals written (not applied) for: (1) python3 Store alias vs python.exe hooks already patched — residual risk; (2) gitwrite 40-attempt timeout; (3) IMAP timeout errors.
3. Each proposal has status: open and requires: owner_decision.
4. NOTHING APPLIED to firewall. No /etc/ edits. No src/ edits.
5. Existing 09-LANES/L9/LANE-REPORT.md from install is replaced/extended, not silently discarded without rollback notes.
6. No flags, no network, no rm, no git push, no Telegram.

Baselines: persistence (install L9 report + L1 F1/F3), prior-only (do not claim patches applied this session), random (not used).
Every number needs a source path or the token unverified.
