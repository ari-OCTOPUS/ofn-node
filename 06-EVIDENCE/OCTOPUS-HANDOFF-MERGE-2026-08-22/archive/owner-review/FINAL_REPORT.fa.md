# وضعیت

Canonical: **KEEP_WAVE0_LOCKED**. `octopus-audit-ledger checkpoint anchored at seq=266`. Skill صفر = `model_is_the_baseline` نه شکست candidate. امضای seq 266 به‌تنهایی OA-T7 نمی‌سازد.


- Current wave: `WAVE0_OBSERVE_ONLY`
- Target wave: `WAVE0_OBSERVE_ONLY` (هیچ transition اجرا نشد)
- Verifier: `READY` / gates_failed=`[]` (معنی: READY observe-only)
- Doctor: read-only؛ انتظار FAIL/DEGRADED (پوشش، skill، GAP)
- Ledger: HASH_CHAIN_ACTIVE (WM `seq=111`)
- GAP-001: `OPEN` / `TESTED_FAIL` / `cryptographically_verified=false` — ادعای PASSED مگاپرامپت باطل است
- GAP-002: `DEFERRED_TO_WAVE1` — بسته نشده
- Skill: score=`0.0` = `model_is_the_baseline`؛ `is_evidence_of_model_quality=false`؛ T4 اجرا نشده؛ DENY
- Planner invocations: `0`
- Executed actions: `0`
- Authority: `NONE`
- T0: **DEGRADED** (would_decide=block)، mutations=0
- T1: PASS (usable_pairs=53 ≥ 50؛ eligible=false؛ calibration=UNKNOWN)
- 9101 bind: `127.0.0.1:9101`

# قفل‌ها

| Lock | Purpose | Evidence | Missing | Owner signature | Decision |
|---|---|---|---|---|---|
| `LOCK-ACTUATOR-AUTHORITY` | Keep actuator_authority=NONE | homeostasis.actuator_authority=NONE; reflex.armed=false | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-EXECUTABLE` | Keep executable=false on every Wave 0 decision | metacontrol.executable=false; policy NO_ACTION_OBSERVE_ONLY | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-REFLEX-ARMING` | Reflex A0 must not arm | ARMED.json armed=false; execute_enabled=false; criteria owner_approval=required | 14 observation days; GAP-001 PASS; GAP-002 CLOSED; registry v6 live; rollback drill; OA for A0 | empty / required | `KEEP_LOCKED` |
| `LOCK-PLANNER-LIVE` | No live planner import or invocation | AST: live scripts do not import planner; planner_invocations=0 | candidate WM; OA for planning | empty / required | `KEEP_LOCKED` |
| `LOCK-POLICY-NO-ACTION` | Policy must return only NO_ACTION_OBSERVE_ONLY | world_model/policy.py choose_action hard-coded | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-GPIO-PWM` | No GPIO/PWM actuation | boot G9 octopus pwm export not writable; leg_authority=DENIED | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match; hardware actuator contract | empty / required | `KEEP_LOCKED` |
| `LOCK-MQTT` | MQTT stays DISABLED | boot mqtt_state=DISABLED; mqtt_1883_open=false | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-LEG` | No leg commands / NATS user leg01 | leg_authority=DENIED | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-REBOOT` | No experimental reboot | this session mutations=0; no shutdown issued | GAP-001 cryptographic PASS still missing; reboot not authorized here | empty / required | `KEEP_LOCKED` |
| `LOCK-SERVICE-RESTART` | No service restart this session | executed_actions=0 | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-REGISTRY-WRITE` | No unsigned registry write | apply_signed_inbound requires Ed25519; live registry v5 signed | Windows-signed Registry v6 bundle | empty / required | `KEEP_LOCKED` |
| `LOCK-HOST-MUTATION` | No drop_caches/cpufreq/kill/network manipulation | reflex execute_enabled=false | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-LAN-NEW-ENDPOINTS` | No new LAN listeners | ss: no :8080/:9464; 9101 loopback-only | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-METRICS-LOOPBACK` | Metrics remain 127.0.0.1:9101 | ss tcp 127.0.0.1:9101; bind.conf | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-FASTAPI-DOCKER-LAB` | Do not deploy FastAPI/docker lab on board | docker not running; shadow-validation disabled | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |
| `LOCK-SYNTHETIC-LIVE-INJECTION` | No synthetic samples in live skill | synthetic_live_leaks=0 | — | empty / required | `KEEP_LOCKED` |
| `LOCK-MISSING-DATA-IMPUTATION` | Missing skill/calibration stay UNKNOWN | homeostasis unknown=[model_skill,prediction_calibration] | — | empty / required | `KEEP_LOCKED` |
| `LOCK-GAP-002-CLOSE-ON-BOARD` | Do not close GAP-002 on board | status=DEFERRED_TO_WAVE1; unsigned export only | laptop root-v2 signature matching live head | empty / required | `KEEP_LOCKED` |
| `LOCK-ROOT-V2-ON-BOARD` | Board never signs; never invents signatures | sign_checkpoint.py is Windows-only; no private key on board | — | empty / required | `KEEP_LOCKED` |
| `LOCK-AUTHORITY-TRANSITION` | Two-key transition T7+ forbidden this session | no OA; Doctor FAIL; GAP-001 OPEN; T4 not executed | Doctor PASS; GAP-001 PASS_WITH_EVIDENCE; GAP-002 CLOSED; candidate skill_lower_bound>0; signed OA | empty / required | `KEEP_LOCKED` |
| `LOCK-DOCTOR-AUTO-REPAIR` | Doctor must not repair | octopus_doctor_readonly.py repairs_attempted=0 | — | empty / required | `KEEP_LOCKED` |
| `LOCK-CANDIDATE-WM-LIVE` | No live candidate world model | live model persistence-v1 predictor_shadow; octopus-shadow-validation disabled | T4 candidate eval off-path; 50 pairs vs persistence | empty / required | `KEEP_LOCKED` |
| `LOCK-A0-ADVISORY-ARMING` | T7 A0 advisory arming not executed | T7 not in scope; reflex armed=false | signed OA-T7; T1 PASS; Doctor PASS | empty / required | `KEEP_LOCKED` |
| `LOCK-SHADOW-VALIDATION-ENABLE` | Do not enable torch/:9464/shadow unit | unit enabled=false active=inactive; torch_enabled=false | octopus.owner-authorization.v1 signed by existing root-v2; scope/expiry/digest match | empty / required | `KEEP_LOCKED` |

قفل‌ها: **24** — هیچ‌کدام `safe_to_unlock=true` نیست.

# تغییرات پیشنهادی

| File/service | Exact change | Risk | Validation | Rollback |
|---|---|---|---|---|
| skill_tracker_loop.py | رد outcome با timestamp قدیمی | کم | INV-05 | restore script |
| gate.py | PLAN_ALLOWED_ADVISORY فقط executable=false | متوسط | INV-12/13 | restore |
| shadow ledger.py | LedgerError برای stale timestamp | کم / staging | INV-05 | restore |
| live WM / Reflex / FastAPI / GAP-002 | **اعمال نشود** | بالا | — | — |

جزئیات: `PROPOSED_DIFFS.md`. اعمال‌شده در live: خیر (به‌جز artifact/test/doctor/export مجاز).

# مجوز موردنیاز

```json
{
  "schema": "octopus.owner-authorization.v1",
  "authorization_id": "OA-T7-A0-ADVISORY-ARMING-NOT-ISSUED",
  "issued_at": "",
  "expires_at": "",
  "current_wave": "WAVE0_OBSERVE_ONLY",
  "target_wave": "WAVE0_A0_ADVISORY_ARMED",
  "scope": [
    "A0-advisory-only",
    "unit:octopus-sensorium.service",
    "unit:octopus-stability.service"
  ],
  "allowed_actions": [
    "WRITE_ADVISORY",
    "CLOSE_ADVISORY",
    "APPEND_LEDGER",
    "OWNER_ALERT",
    "PROPOSE_RUNBOOK"
  ],
  "forbidden_actions": [
    "GPIO",
    "PWM",
    "MQTT_ACTUATION",
    "LEG",
    "REBOOT",
    "SERVICE_RESTART",
    "REGISTRY_WRITE",
    "DROP_CACHES",
    "CPUFREQ",
    "HOST_BLOCK",
    "PROCESS_KILL",
    "NETWORK_MANIPULATION",
    "PLANNER_INVOKE",
    "EXECUTABLE_TRUE",
    "ACTUATOR_AUTHORITY_CHANGE"
  ],
  "target_hosts": [
    "sensorium-opi5pro-68e44cdf"
  ],
  "config_digest": "sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5",
  "checkpoint_digest": "sha256:3b60751b3759698b4982ccda035a008539cc0014cb086d96f516fc274142c150",
  "rollback_digest": "",
  "max_duration_s": 0,
  "max_actions": 0,
  "owner_identity": "",
  "owner_signature": "",
  "root_key_id": "root-v2",
  "_verify_note": "Empty signature, empty identity, max_actions=0 => DENY. This instance is a request template, not a grant."
}
```

نبود `owner_signature` یعنی DENY.

# تصمیم

**KEEP_WAVE0_LOCKED**
