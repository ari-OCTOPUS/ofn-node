# EVIDENCE_MATRIX

| Claim | Path | Value | Verdict |
|---|---|---|---|
| control_safety | homeostasis latest | authority=NONE executed=none | PASS |
| Doctor PASS | DOCTOR_REPORT.json | FAIL | FAIL remaining ['sensor_coverage', 'gap001'] |
| GAP-001 | gap001/boot_report.json | TESTED_FAIL | OPEN; reboot not run |
| GAP-002 | GAP-002 json + signed bundle | CLOSED_BY_SIGNED_CHECKPOINT | VERIFIED |
| seq 266 full hash | AUDIT_CHECKPOINT_266.json | sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2 | match=False |
| T1 usable>=50 | CANDIDATE_VALIDATION.json | 127 | PASS |
| T4 PLAN_ALLOWED | CANDIDATE_VALIDATION.json | DENY | DENY |
| interaction guard | CANDIDATE_VALIDATION.json | True | required |
| live policy | policy.choose_action | NO_ACTION_OBSERVE_ONLY | PASS |
| pytest cognition | TEST_RESULTS/pytest_cognition.json | rc=0 | PASS |
| coverage not imputed | fusion latest | 0.6667 | reported |
| OA-T7 | (absent) | false | PASS (must stay absent) |
