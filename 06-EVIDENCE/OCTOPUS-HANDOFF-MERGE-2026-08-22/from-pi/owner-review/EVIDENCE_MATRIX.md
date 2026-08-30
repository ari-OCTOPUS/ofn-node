# EVIDENCE_MATRIX

منبع: فایل‌های زنده در `2026-08-17T03:49:18.866833+00:00`. اگر evidence نیست: UNKNOWN/BLOCKED.

| Claim | Evidence path / command | Live value | Verdict |
|---|---|---|---|
| verifier READY | `/var/lib/octopus/state/boot_report.json` | `READY` gates=`[]` | PASS as WAVE0_OBSERVE_ONLY |
| actuator_authority NONE | homeostasis latest | `NONE` | PASS |
| skill samples ≥ 50 | skill/latest.json | `53` | PASS (count); skill eligible=false (persistence vs persistence) |
| usable_pairs ≥ 50 | world_model/ledger.jsonl | `53` | PASS T1 accumulation |
| score 0.0 with ≥50 pairs | skill/latest.json + SKILL_INTERPRETATION.json | model==baseline → SS=0 analytically | NOT evidence of model quality; T4 not executed |
| planner_invocations=0 | WM ledger + latest | `0` | PASS |
| executable_actions=0 | WM ledger + metacontrol | `0` / executable=`False` | PASS |
| orphan_outcomes=0 | ledger walk | `0` | PASS |
| duplicate_predictions=0 | ledger walk | `0` | PASS |
| synthetic_live_leaks=0 | ledger walk | `0` | PASS |
| ledger_verify | ChainedLedger.verify | `True` `seq=111` | PASS |
| 9101 loopback | `ss -lntup` | 127.0.0.1:9101 | PASS |
| no :8080/:9464 | `ss -lntup` | absent | PASS |
| GAP-001 software-reboot PASS | gap001/boot_report.json | `TESTED_FAIL` pass=`False` status=`OPEN` | FAIL — live file is source of truth; megaprompt PASSED was wrong |
| GAP-002 closed | GAP-002 json + signed bundle | `DEFERRED_TO_WAVE1` signed bundle absent | FAIL/BLOCKED |
| registry v6 live | registry.yaml config_version | 5 | BLOCKED (v6 unsigned pack only) |
| seven-day telemetry | snapshots exist minutes-hours this boot | uptime `03:49:19 up  2:33,  0 users,  load average: 1.09, 1.00, 0.97` | UNKNOWN |
| candidate WM | octopus-world-model.service | persistence-v1 only | BLOCKED T4 |
| OA signature | none | empty | DENY |
| Doctor PASS | doctor-report.json | FAIL; blocking_checks=gap_001_open, checkpoint_unsigned, coverage_or_data_critical | FAIL |
| resolved_spontaneously rate | reflex ledger | live UNKNOWN; pre-chain not evidence | UNKNOWN |

T1 acceptance extras: persistence-v1 is baseline (`model_version=persistence-v1`). persistence vs persistence cannot become eligible (INV-02).
