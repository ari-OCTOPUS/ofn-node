# CURRENT_STATE

تاریخ انجماد (T0): `2026-08-17T03:49:18.866833+00:00`  
board_id: `sensorium-opi5pro-68e44cdf`  
hostname: `DietPi` (`192.168.0.182`)  
boot_id: `063fef44-cd54-4a68-81b5-7ac5fd2c39f0`  
mutations: **0**  
executed_actions: **0**  
READY یعنی `WAVE0_OBSERVE_ONLY` — نه ARMED.

## وضعیت مبنا (live، نه فرض)

| Field | Live value |
|---|---|
| readiness_profile | `WAVE0_OBSERVE_ONLY` |
| verifier readiness_state | `READY` |
| gates_failed | `[]` |
| clock_trust | `SYNCED_NTP` |
| actuator_authority | `NONE` |
| world_model | `persistence-v1` / `predictor_shadow` |
| skill.samples | `53` |
| skill.score | `0.0` |
| skill.reason | `not_better_than_baseline` |
| metacontrol.recommendation | `DENY` |
| metacontrol.executable | `False` |
| planner_invocations (ledger) | `0` |
| executable_actions (ledger) | `0` |
| reflex.armed | `False` |
| GAP-001 live file | `OPEN` / probe `TESTED_FAIL` pass=`False` |
| GAP-002 | `DEFERRED_TO_WAVE1` |
| metrics bind | `127.0.0.1:9101` |
| :8080 / :9464 | absent / absent |
| Doctor | NOT a live service; read-only script added this session |
| coverage | `0.5` (3/6) |

## T0 — inventory

### units / timers

- `nats-server.service` = `active`
- `octopus-sensorium.service` = `active`
- `octopus-stability.service` = `active`
- `octopus-fusiond.service` = `active`
- `octopus-reflex.service` = `active`
- `octopus-world-model.service` = `active`
- `octopus-skill-tracker.service` = `active`
- `octopus-metacontrol.service` = `active`
- `octopus-shadow-validation.service` = `inactive`
- `octopus-gap001-boot-probe.service` = `failed`
- `octopus-ledger-verify.timer` = `active`
- `octopus-apply-checkpoint.path` = `active`
- `octopus-apply-registry.path` = `active`
- `dropbear.service` = `active`
- `ufw.service` = `active`
- `systemd-timesyncd.service` = `active`

`octopus-gap001-boot-probe.service` در این boot در وضعیت `failed` است (هم‌خوان با TESTED_FAIL).  
`octopus-shadow-validation.service` = `inactive` (باید disabled/inactive بماند).

### پورت‌ها (ss)

```
tcp   LISTEN 0      1000         0.0.0.0:22         0.0.0.0:*    users:(("dropbear",pid=691,fd=3))   
tcp   LISTEN 0      5          127.0.0.1:9101       0.0.0.0:*    users:(("python",pid=7190,fd=3))    
tcp   LISTEN 0      4096       127.0.0.1:8222       0.0.0.0:*    users:(("nats-server",pid=692,fd=3))
tcp   LISTEN 0      4096   192.168.0.182:4222       0.0.0.0:*    users:(("nats-server",pid=692,fd=6))
tcp   LISTEN 0      1000            [::]:22            [::]:*    users:(("dropbear",pid=691,fd=4))   
```

NATS روی LAN (`192.168.0.182:4222`) از قبل در gate `PORTS` مستند است. listener جدید Wave0 نیست.  
متریک فقط loopback است. `:8080` و `:9464` نیستند.

### firewall (ufw)

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere                  
22/tcp (v6)                ALLOW IN    Anywhere (v6)
```

### digest کانفیگ مؤثر

- `/etc/octopus/world-model.yaml` = `sha256:ea4b482fdc8e936e87fef1c0aa3f3104a0754c4b0541fd1daa705fa1c590fb8b`
- `/etc/octopus/homeostasis.yaml` = `sha256:2396535d517c2eea5fe5ac2f958a17390ce778777b44db0b408ea2982f9f7c1c`
- `/etc/octopus/reflex_arming_criteria.yaml` = `sha256:f2f98b3e3369d38d3a2af53b06b21aadf67a12586a11ea0996fe0c8f9ad6e5b4`
- `/etc/octopus/config/registry.yaml` = `sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5`
- `/etc/octopus/config/registry.yaml.sig` = `sha256:29b0477ad56519b12c95d7a4d415d8bd779af816aacddd87a0dc63c2746a3ad2`
- `/etc/octopus/config/board.yaml` = `sha256:b53ec5ba3764f035513535577df5e72f25767e54dda2cedfd5d9b1ca73cd0d5d`
- `/etc/octopus/config/board.yaml.sig` = `sha256:083901105698edc8cc5cb41fd7c519d75d38878a2cd67446849bf7d82cf18756`
- `/etc/octopus/trust/root.pub` = `sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40`
- `/etc/systemd/system/octopus-stability.service.d/bind.conf` = `sha256:65fa8b55fcb356369ec1d07d19544f8dceff483e2ae4ba942efa40ff4b976786`
- `/etc/systemd/system/octopus-world-model.service` = `sha256:8c0830e6bd77fde9050b7f3187dd9d781463f420016021fcf5234fc5b63c0761`
- `/etc/systemd/system/octopus-shadow-validation.service` = `sha256:79a0bf5e94a2a7359fe578fecc4305d9a31ff326bbf7586e119b3a8ce231d8f0`
- `/opt/octopus/scripts/world_model_shadow.py` = `sha256:7a52d208172273e89b9ee0f1cbeecc67a401f510e3627b3f1dc86c3470826158`
- `/opt/octopus/scripts/metacontrol_shadow.py` = `sha256:e4d7de8f9240ce6f4d2a9d03b20bc5d9eb7f8165b15c40f37ef880314cabd58a`
- `/opt/octopus/scripts/skill_tracker_loop.py` = `sha256:006807ccfd26d9b13e1515e5b44ec820a52e0571a5de6bdd6de16e16a02e5706`
- `/opt/octopus/scripts/apply_signed_inbound.py` = `sha256:a70430c4ebe55240aba99dec03164227365100e94d07fab5594d36574f58faa1`
- `/opt/octopus/scripts/write_laptop_handoff.py` = `sha256:5dcb2d89b25fda2b3a71927f20b6ccefbb47cc689bbac0a62081ee5382d91c39`
- `/opt/octopus/scripts/octopus_doctor_readonly.py` = `sha256:b61817038d0c834e301d58c8173921a2d280c2a727b0e4849aa65fe9ea93fa53`

root.pub fingerprint = `sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40` (EXPECTED_V2).

### ledgers (دو زنجیرهٔ مستقل)

عبارت ممنوع: `ledger head = 266`. عبارت دقیق: `octopus-audit-ledger checkpoint anchored at seq=266`.

| Ledger | Chain ID | Head/anchor | کاربرد |
|---|---|---|---|
| Audit | `octopus-audit-ledger` | checkpoint anchored at seq=266 | شواهد T0–T6 و audit |
| Reflex | `octopus-reflex-ledger` | seq=1 | advisoryهای Reflex |
| ارتباط | فعلاً مستقل | نباید یکی فرض شوند | اتصال آینده فقط با checkpoint صریح |

- audit record hash **کامل** (نه خلاصه): `sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2`
- `represents_latest_state`: false — لنگر تاریخی تا seq 266 است
- world_model HEAD at T0 freeze: seq=111 hash `91d72bc852b01553139dbe42990cb3ac48c06224e88739e81a744e2f05959661`
- metacontrol HEAD: seq=2 hash `5dca54c213af65a543896bb80c26f28dd1b72db31b6893cd0d6fc64a7313c050`
- reflex HEAD: seq=1 hash `018d8bc5bb6e12290e01979aaade8f701deeba306dcce90aa847b0b357f49260`

### prediction / outcome

- predictions: `56`
- outcomes: `55`
- usable_pairs: **53** (حد نصاب T1 = 50)
- pending: `1`
- orphan_outcomes: `0`
- duplicate_predictions: `0`
- outcome_before_prediction: `0`
- synthetic_live_leaks: `0`

### host envelope

- envelope_profile: `WAVE0_IDLE`
- host_in_range: `True`
- in_envelope: `True`
- data_ok: `False` (پوشش حسگر critical است)
- homeostasis_ok: `False`
- unknown: `['prediction_calibration']`

### resolved_spontaneously

زنجیرهٔ زندهٔ Reflex فقط genesis (seq=1) دارد؛ نرخ resolved_spontaneously روی زنجیرهٔ زنده قابل‌محاسبه نیست (UNKNOWN). بایگانی pre-chain شامل 198 رکورد است که 198 مورد status=advisory_clear دارند. genesis صریحاً می‌گوید این بایگانی evidence آرمینگ نیست.

نرخ زنده: **UNKNOWN**

### GAP-001 — حقیقت فایل زنده

مگاپرامپت کاربر مقدار `PASSED` را به‌عنوان وضعیت مبنا نوشته است. فایل‌های زنده این را تأیید نمی‌کنند:

- `/var/lib/octopus/state/gaps/GAP-001-cold_boot_unverified.json` status=`OPEN`
- controlled_reboot.result=`TESTED_FAIL`
- controlled_reboot_retry / probe status=`TESTED_FAIL` pass=`False`
- gates در retry: `['G8']`
- power_loss_recovery: untested
- cryptographic software-reboot PASS: **false** — `gap_001=OPEN`, `gap_001_last_result=TESTED_FAIL`, `gap_001_cryptographically_verified=false` (اصلاح ادعای مگاپرامپت PASSED)

### GAP-002

status=`DEFERRED_TO_WAVE1`، wave0_signature=`None`.  
export بدون امضا انجام شد (seq=`266`). **بسته نشده.**

## نتایج transition (این جلسه)

| ID | Result | Note |
|---|---|---|
| T0 | DEGRADED | freeze mutations=0؛ would_decide=block → DEGRADED نه PASS |
| T1 | ACCUMULATION_PASS_SKILL_NOT_EVIDENCE | ≥۵۰ جفت؛ score=0.0 یعنی مدل همان persistence است؛ T4 اجرا نشده |
| T2 | UNSIGNED_EXPORT_ONLY | GAP-002 بسته نشد |
| T3 | SPEC+READONLY_RUN | Doctor تعمیر نمی‌کند |
| T4 | NOT_EXECUTED_NO_CANDIDATE | candidate_loss=null؛ Skill Score شاهد کیفیت مدل نیست |
| T5 | QUALIFIED_SHADOW | PLAN_ALLOWED_ADVISORY در live emit نمی‌شود؛ planner صدا زده نمی‌شود |
| T6 | NOT ready_for_owner_decision | KEEP_WAVE0_LOCKED |
| T7 | NOT EXECUTED | — |
| T8 | stub only | در OWNER_REVIEW_PACKAGE |

تصمیم: **KEEP_WAVE0_LOCKED**
