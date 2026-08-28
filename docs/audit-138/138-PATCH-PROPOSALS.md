# PATCH PROPOSALS (none applied to runtime; audit branch only)
1. **fix/autoverify-embed-claims-138**: octopus_verify_dispatcher.py — embed frozen claims summary into AUTO-VERIFY payloads. Evidence: F-2 (two empty verdicts); regression: red = old payload lacks claims, green = claims present + witness populates claims_verified. Rollback: revert single commit. 
2. **fix/test-greeting-import-138**: convert relative import to absolute in tests/test_greeting_name.py (pre-existing error). Red→green trivial; no runtime impact.
3. **proposal/182-ntp-probe**: owner-approved method to measure 182 clock offset (install-free: python ntplib? no — propose `date` delta via ssh round-trip median, logged as UNKNOWN-grade) — needs owner GO per no-new-dependency rule.
All: small, additive, branch `audit/senior-auditor-20260828-138` → PR only; **no merge, no deploy**.
