# E3 propose + next safe enrich

## E3 feeds quality soak (readonly)
- duration: 15m every 60s
- recommendation: **WAIT_GO** (prior hold was separate GO for E3; plan is ready readonly)
- live now: ok=7/7 fail=[]

## After E1/E2 other safe
- E4: wave01-range.json readonly triage (KEEP until GO) (readonly)
- E5: Refresh/rewrite live boot_report from current snapshot (or stop doctor reading ancient boot_report) (reversible_observe)
- E6: Document NATS octopus-core E2E creds rotation checklist (no rotate without GO) (docs_only)