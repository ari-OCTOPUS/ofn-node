# گزارش اجرای دستورالعمل — 2026-08-17T06:12:22Z

## خلاصهٔ authority (باید بدون تغییر باشد)
- authority_state: WAVE0_OBSERVE_ONLY (تغییر نکرد: بله)
- executed_actions: 0 (باقی ماند: بله)
- executable: false (باقی ماند: بله)
- actuator_authority: NONE (باقی ماند: بله)
- evidence: `/tmp/evidence/authority-final-check.log` + OWNER_REVIEW_DECISION.json + metacontrol/latest.json
- boot_id این نشست: `bcdab511-3d46-4fdf-b113-f894cb8666f5`

## مرحله ۰ — قرنطینهٔ شواهد
- خروجی: `/tmp/evidence/stage0-tainted-window.yaml`
- پنجره:
  - start: `2026-08-17T05:49:42Z` (ActiveEnterTimestamp سرویس)
  - end: زمان علامت‌گذاری
  - status: `TAINTED_COLLECTION`
  - reason: octopus-sensorium CPU pegged؛ مشاهدات این پنجره unreliable
- علامت‌گذاری (حذف نشد):
  - `/var/lib/octopus/state/quarantine/TAINTED_WINDOW_sensorium-cpu.yaml`
  - sidecar در skill / world_model / metacontrol / fusion / homeostasis / stability: `TAINTED_WINDOW.yaml`
  - index: `/var/lib/octopus/state/evidence/indexes/tainted-windows.jsonl`
- سیاست: هیچ coverage / skill_score جدید از این پنجره «تازه» حساب نشود
- journal واحد فقط ۲ خط start دارد: `/tmp/evidence/sensorium-journal-boot0.log`

## مرحله ۱ — ریشهٔ CPU
- ابزار غایب (نصب نشد): pidstat/sysstat، py-spy، strace — گزارش در `stage1-tools.log`
- نمونهٔ ۱Hz/۶۰ثانیه: `/tmp/evidence/pidstat.log` — الگوی غالب ~۹۹٪ `state=R` برای ۱۰–۱۵ثانیه، سپس ~۵ثانیه `0%`/`S` (هم‌خوان با `interval=5.0` در `run_forever`)
- `vmstat`: `wa≈0` → نه I/O wait کلاسیک
- پنجره ۱۲ثانیه: rchar +633MB / write_bytes +297MB در حالی که `observations.jsonl` فقط +28KB — `stage1-io-growth-12s.log`
- **ROOT_CAUSE:** بازنویسی کامل ایندکس‌های JSON چندمگابایتی در `persist_observation` → `_update_indexes` (`evidence/store.py`) روی هر observation؛ جزئیات و نقل مستقیم: `/tmp/evidence/stage1-root-cause.md`
- فیکس اعمال نشد (نیاز تأیید مالک)

## مرحله ۲ — verifier
- مسیر verifier فعلی: `/var/lib/octopus/state/gap001/verifier.json`
- `systemctl cat octopus-gap001-boot-probe`: `gap001_probe.py --wait-ready-timeout 300` — آستانهٔ ۳۰۰ دستکاری نشد
- نقص: `has_boot_id=False` در verifier (`stage2-boot-id-check.log`) — probe نمی‌تواند تازگی فایل را به boot_id گره بزند
- schema پیشنهادی (اعمال نشد؛ نیاز تأیید مالک): verifier.v1 با boot_id / generated_at / agent_started_at / digests / gates_failed / authority_state
- سه فیلد جدا (هرگز ادغام نشوند):
  - process_state: **ACTIVE**
  - agent_readiness: **READY**
  - boot_acceptance: **PASSED** (probe این boot: `TESTED_PASS`, `gates_failed=[]`, waited ~36s؛ منبع `gap001/boot_report.json`)
- توجه: `open-gaps.json` هنوز `GAP-001.status=DEFERRED_BY_OPERATOR, pass=false` — این با `boot_acceptance` یکی نیست
- هشدار اجرا شد: آستانه ۳۰۰ لمس نشد

## مرحله ۳ — provenance
- listening ports: `/tmp/evidence/listening-ports.log`
  - `127.0.0.1:9101` python/stability
  - `127.0.0.1:8222` + `192.168.0.182:4222` nats-server
  - `0.0.0.0:22` dropbear
  - `127.0.0.1:36083` node (Cursor/VS Code)
- auditd: absent
- لاگ shell کانال چهارم: **اعمال نشد روی /etc** — فقط پیشنهاد در `manual-shell-audit.sh.proposed` و `inbound/TO-LAPTOP/pre-maintenance/` (نیاز تأیید مالک؛ تغییر /etc خارج از observe-only صرف)
- hostname فعلی: `DietPi` — `hostnamectl set-hostname sensorium-opi5pro-68e44cdf` **اجرا نشد** (نیاز تأیید مالک)

## مرحله ۴ — checkpoint
- `octopus_sync` روی برد: ABSENT
- export یک‌طرفه اجرا نشد
- بستهٔ درخواست برای مالک: `inbound/TO-LAPTOP/pre-maintenance/CHECKPOINT-EXPORT-REQUEST.md`
- وضعیت: **در انتظار امضای مالک** (sign-checkpoint.bat روی ویندوز)
- checkpoint.unsigned زنده: sequence=284 در `OCTOPUS-AUDIT-CHECKPOINT/checkpoint.unsigned.json`

## مرحله ۵ — ریبوت
- **اجرا نشد** — `OWNER_MAINTENANCE_WINDOW_REQUIRED` تأیید صریح مالک در این نشست دریافت نشد
- پیش‌شرط‌ها جمع‌آوری/اجرا نشدند

## مرحله ۶ — GAP-002
```
finding: GAP-002 status conflict
  - runtime observed: live unsigned checkpoint sequence=284; gap file earlier recorded live seq=275 vs signed checkpoint seq=266 (open)
    raw GAP-002 state file: {'gap_id': 'GAP-002', 'title': 'audit_head_unsigned', 'status': 'OPEN', 'pass': False, 'signed': True, 'head_match': False, 'chain': 'seq=275 head=sha256:630458945545514cfb9217cb291927e2251b37d9adc5f0eb1be2c7e19acfb1fd', 'checkpoint_sequence': 266, 'live_sequence': 275, 'leaked_private_removed': []}
  - registry official (/opt/octopus/current/manifests/open-gaps.json): {"GAP-001": {"status": "DEFERRED_BY_OPERATOR", "pass": false}, "GAP-002": {"status": "DEFERRED_TO_WAVE1", "audit_integrity": "HASH_CHAIN_ONLY", "pass": false}}
  - prior advisory: "close GAP-002 next" (architect/season docs before Doctor build)
  - owner official record: DEFERRED_TO_WAVE1
  - CHECKPOINT_266_VERIFY.gap_002: CLOSED_BY_SIGNED_CHECKPOINT (امضا ≠ بستن registry)
  action: NO ACTION TAKEN. Escalate to owner for explicit re-confirmation.
```

## مرحله ۷ — Prometheus
- برچسب STALE به بالای بخش ۴ اضافه شد در:
  - `/root/LAPTOP-AGENT-INSTRUCTIONS.md`
  - `/var/lib/octopus/inbound/TO-LAPTOP/LAPTOP-AGENT-INSTRUCTIONS.md`
- تأیید runtime: `ss` نشان می‌دهد `127.0.0.1:9101` loopback-only
- پیشنهاد (اجرا نشد): سرویس دائمی SSH tunnel روی لپ‌تاپ با `ExitOnForwardFailure=yes` و keepalive به‌جای `ssh -N -L` دستی

## مرحله ۸ — سنسورها
```yaml
sensors_active: 4
sensors_discovered_unbound: 2
sensors_manifest_only: 66
sensors_disabled: 29
external_physical_sensors: 0
power_observability: NOT_INSTRUMENTED
homeostatic_claim_ceiling: PARTIAL
```
- منبع خام: `/var/lib/octopus/state/sensors/health.json` (timestamp در `stage8-sensors.yaml`)؛ نکتهٔ اضافی STALE=2 در همان counts
- پیشنهاد (نصب نشد): ماژول INA219/INA226 برای رفع سقف PARTIAL توان

## کارهایی که اجرا نشد و چرا
| مورد | چرا |
|---|---|
| فیکس CPU / تغییر store.py | نیاز تأیید مالک پس از root-cause |
| restart هر سرویس | ممنوع در دستورالعمل |
| schema verifier + boot_id | نیاز تأیید مالک |
| فعال‌سازی `/etc/profile.d/manual-shell-audit.sh` | نیاز تأیید مالک (تغییر /etc) |
| `hostnamectl set-hostname` | نیاز تأیید مالک صریح |
| `octopus_sync export-checkpoint` | مرحله ۴: اجرا نکن؛ فقط درخواست آماده شد؛ باینری غایب |
| reboot مرحله ۵ | بدون `OWNER_MAINTENANCE_WINDOW_REQUIRED` |
| بستن GAP-002 | DEFERRED_TO_WAVE1 — اقدام ممنوع |
| نصب INA219/INA226 | فقط پیشنهاد |
| سرویس tunnel لپ‌تاپ | فقط پیشنهاد |
| تغییر آستانه probe 300→600 | صریحاً ممنوع |

## آرشیو شواهد
- `/tmp/evidence/`
- `/var/lib/octopus/evidence/session-20260817T0610Z/`
- `/var/lib/octopus/inbound/TO-LAPTOP/evidence-session-20260817/`
