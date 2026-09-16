# گزارش اجرای دستورالعمل — ۲۰۲۶-۰۸-۱۷ (جلسه دوم، ۰۹:۳۰–۰۹:۴۵ UTC)

- boot_id: `c8a0b325-7936-47bc-929d-7474ba9d008e` (از `/proc/sys/kernel/random/boot_id`، 2026-08-17T09:32:18+00:00)
- hostname فعلی: `DietPi` (تغییر نیافت — بخش مرحله ۳)
- سرویس: `octopus-sensorium.service`، PID 689، فعال از `Mon 2026-08-17 06:40:28 UTC`، NRestarts=0
- نکته نام‌گذاری: فایل `SESSION-REPORT-20260817.md` از جلسه قبلی (۰۶:۱۲ امروز) موجود بود؛ برای حفظ شواهد بازنویسی نشد و این گزارش با نام جدید نوشته شد.
- شواهد خام جلسه: `/tmp/evidence/` (کپی آرشیو: `/var/lib/octopus/evidence/session-20260817T0943Z/`) + زنجیره `{دستور، ts، boot_id}` در `/tmp/evidence/provenance.log`

## خلاصهٔ authority (باید بدون تغییر باشد)

- authority_state: **WAVE0_OBSERVE_ONLY — تغییر نکرد: بله**
  - شاهد: فیلدهای زنده در `state/snapshots/latest.json` در ابتدا (09:35:28Z) و انتهای جلسه (09:42:58Z) یکسان: `readiness_profile=WAVE0_OBSERVE_ONLY, operational_mode=OBSERVE_ONLY, actuator_authority=NONE, leg_authority=DENIED, mqtt_state=DISABLED`
  - شاهد هش: sha256 سه فایل authority در ابتدا و انتهای جلسه بیت‌به‌بیت یکسان:
    - `OWNER_REVIEW_DECISION.json` = `6fdf4f54…be271`
    - `wave_baseline_accepted.json` = `a313fd77…d728`
    - `gap001/verifier.json` = `56cf37a6…080c`
- executed_actions: **0 — باقی ماند: بله** (`OWNER_REVIEW_DECISION.executed_actions=0`, `authority_changed=false`؛ `metacontrol/latest.json`: `executable=false, executed=none, action=NONE`)
- سرویس ری‌استارت نشد: `MainPID=689`, `NRestarts=0`, `ActiveEnterTimestamp=06:40:28` در طول کل جلسه ثابت.
- ریبوت انجام نشد؛ boot_id در پایان جلسه همان ابتدای جلسه است.

## مرحله ۰ — قرنطینهٔ شواهد

- فایل خروجی: `/tmp/evidence/stage0-tainted-window.yaml` + کپی در چهار مسیر:
  - `/var/lib/octopus/state/skill/TAINTED_WINDOW.yaml` (مصرف‌کننده: Skill Tracker)
  - `/var/lib/octopus/state/metacontrol/TAINTED_WINDOW.yaml` (مصرف‌کننده: Metacontrol/World Model)
  - `/var/lib/octopus/state/quarantine/TAINTED_WINDOW_sensorium-cpu.yaml`
  - آرشیو: `/var/lib/octopus/evidence/stage0/stage0-tainted-window-c8a0b325.yaml`
- پنجرهٔ ثبت‌شده (boot فعلی):
  - start: `2026-08-17T06:40:28Z` — basis: `ActiveEnterTimestamp` + اینکه میانگین CPU از استارت (٪79.3 در ثانیهٔ ۱۰۲۷۵ام عمر پروسه) ≈ نرخ لحظه‌ای (٪99.9) است ⇒ پگ بودن از همان استارت شروع شده.
  - end: `2026-08-17T09:41:57Z` (پنجره در لحظهٔ ثبت هنوز باز بود؛ شرط ادامه‌دار است)
  - status: `TAINTED_COLLECTION`
- نکته تکرار: پنجرهٔ آلودهٔ boot قبلی (`bcdab511`، بازهٔ 05:49:42–06:06:47، pid 698) از قبل علامت‌خورده بود و **حفظ شد** (آرشیو verbatim در `evidence/stage0/stage0-tainted-window.yaml`)؛ مشکل CPU بعد از ریبوتِ بین دو boot **عود کرد** ⇒ هر دو پنجره TAINTED هستند.
- ledgerهای hash-chained دست نخوردند: افزودن دستی ریسک شکستن زنجیرهٔ تأیید دارد؛ marking با همان سازوکار TAINTED_WINDOW (روال جلسه قبلی) انجام شد. حذفی صورت نگرفت.
- سیاست اعمال شد: هیچ عدد coverage/skill_score جدید از این پنجره «تازه» حساب نمی‌شود.

## مرحله ۱ — ریشهٔ CPU

**ROOT_CAUSE_IDENTIFIED (تکرار علت شناسایی‌شده در boot قبلی؛ عود پس از ریبوت تأیید شد).**

فایل کامل: `/tmp/evidence/stage1-root-cause.md`

ریشه: `persist_observation → _update_indexes` — بازنویسی کامل شش فایل ایندکس JSON چند‌مگابایتی به‌ازای **هر observation**.

سه证据 tuple کلیدی:

1. {claim: در ۱۰ ثانیه فقط ۶ رویداد جدید ولی ۱۳۵.۷MB نوشتن دیسک,
   command: `python3` نمونه‌برداری `/proc/689/io`,
   raw_output: `rchar Δ293,801,248 / wchar Δ135,570,562 / write_bytes Δ135,749,632 / syscw Δ61 / events Δ6`,
   timestamp: 2026-08-17T09:38–09:39Z, boot_id: c8a0b325-…}
   ⇒ تضخیم ≈ **۲۲.۶MB نوشتن به‌ازای هر observation**
2. {claim: شش ایندکس مجموعاً ≈۲۴.۵MB هستند و mtime آن‌ها هر تیک جلو می‌رود ولی حجم تقریباً ثابت است ⇒ بازنویسی کامل,
   command: `stat` در t0 و t0+10s,
   raw_output: `event_id.json 12,002,745→12,004,435 / timestamp.json 5,237,855→5,238,595 / observations.jsonl +22,463B`,
   timestamp: 09:35:57Z, boot_id: c8a0b325-…}
3. {claim: مسیر کد شش بار `_load_index`+`_save_index` به‌ازای هر observation صدا می‌زند,
   command: `grep -n "_update_indexes\|_save_index\|_load_index" /opt/octopus/current/src/octopus_sensorium/evidence/store.py`,
   raw_output: خطوط 51–87 (شش جفت load/save)، `app.py:720 interval = 5.0`,
   timestamp: 09:39:01Z, boot_id: c8a0b325-…}

پاسخ چهار سؤال دستورالعمل:
- busy-wait یا I/O wait؟ — **کار userspace در حالت R؛ نه iowait** (utime≫stime: 733444 در برابر 82067 تیک؛ %wa بین 0.0–0.2)
- حلقهٔ NATS reconnect بدون backoff؟ — **مدرکی ندارد** (bus=CONNECTED؛ reconnect_time_wait=1 در natsbus.py موجود؛ journal این boot فقط ۲ خط است)
- اسکن uncached رجیستری هر تیک؟ — **هزینهٔ اصلی نیست** (اثبات در جهش I/O ایندکس‌هاست)
- گرسنگی event loop؟ — **اشباع است نه گرسنگی** (تیک ۵ ثانیه‌ای زنده است؛ نخِ تنها مدام مشغول سریال‌سازی ایندکس است)

انباشته: از 06:40 تا 09:39 نوشتن ≈**۱۹۶GB** و خواندن ≈**۴۱۲GB** — برای مالک: بار فرسایشی روی eMMC.

ابزارها: `pidstat`, `py-spy`, `strace` غایب — **نصب نشدند** (طبق قانون). هیچ fix و هیچ restartی اعمال نشد؛ منتظر تأیید مالک.

## مرحله ۲ — verifier

فایل‌های verifier (از `find / -iname "*verifier*.json" -newer /etc/hostname`):
- `/var/lib/octopus/state/gap001/verifier.json` (timestamp `2026-08-17T06:42:01.427048+00:00`)
- `/var/lib/octopus/state/owner-review-final/GAP_001_CURRENT_VERIFIER.json` (`04:28:18`)
- `/var/lib/octopus/state/boot_report.json` (`03:40:58`)
- کپی laptop: `inbound/TO-LAPTOP/owner-review-final/GAP_001_CURRENT_VERIFIER.json`

**نقص تأیید شد: هیچ‌کدام فیلد `boot_id` ندارند** (`grep -c boot_id` = 0 در هر سه فایل) ⇒ probe نمی‌تواند تازگی فایل را نسبت به boot قبلی اثبات کند؛ تازگی فقط از راه همبستگی timestamp است. schema پیشنهادی دستورالعمل (verifier.v1 با boot_id) **اعمال نشد** — نیاز به تأیید مالک.

واحد systemd probe: `octopus-gap001-boot-probe.service` با `--wait-ready-timeout 300` و `TimeoutStartSec=360`.

سه فیلد جدا (طبق قانون):
```
process_state:    ACTIVE      (systemd active, PID 689, از 06:40:28)
agent_readiness:  READY       (readiness_state=READY، profile=WAVE0_OBSERVE_ONLY، gates_failed=[] در verifier 06:42 و snapshot زنده)
boot_acceptance:  PASSED      (برای این boot: rکورد controlled_reboot_retry — probe_started=06:40:28.496، probe_waited_s=93.0 < 300، gates_failed=[]، readiness READY، SYNCED_NTP، pre_boot_id=55ba3334 → post_boot_id=c8a0b325)
```
تبیین ابهام «هم READY هم verifier_missing»: readiness مربوط به پروسه/عامل است و PASSED است؛ «missing» به نبود boot_id در خود فایل verifier برمی‌گردد (نقص schema)، نه به آماده نبودن عامل.

- **آستانهٔ ۳۰۰ ثانیه دست نخورد.** در رکوردهای این boot سناریوی «۳۱۶ در برابر ۳۰۰» دیده نشد (probe فعلی ۹۳ ثانیه منتظر ماند و PASS شد). boot اول (۱۶ Aug) به دلیل G6 (MONOTONIC_ONLY، ~۱۷ ثانیه بعد از boot) FAIL شده بود — دلیلی متفاوت از آستانه.
- وضعیت GAP-001: رکورد رسمی `SOFTWARE_REBOOT_PASS_POWER_LOSS_UNTESTED` — فقط **یک PASS متوالی** (boot فعلی) در کار است؛ شرط بستن (حداقل ۲ PASS متوالی با boot_id جدید و gates_failed=[]) برآورده نشده ⇒ **GAP-001 باز می‌ماند**. power-loss همچنان untested.

## مرحله ۳ — provenance

- پورت‌ها (`ss -tlnp` → `/tmp/evidence/listening-ports.log`):
  - `0.0.0.0:22 / [::]:22` — dropbear (SSH)
  - `192.168.0.182:4222` — nats-server (روی LAN گوش می‌دهد؛ گیت PORTS همین را انتظار دارد؛ ufw فعال است)
  - `127.0.0.1:8222` — nats monitoring (loopback)
  - `127.0.0.1:9101` — stability metrics (loopback-only — تأیید مستقیم مدعای مرحله ۷)
- auditd: `inactive` و باینری MISSING ⇒ کانال چهارم با خط دقیق دستورالعمل فعال شد:
  - فایل: `/etc/profile.d/manual-shell-audit.sh` — `export PROMPT_COMMAND="history -a; logger -t manual-shell \"$(history 1)\""`
  - فقط ثبت است، مسدودسازی ندارد. یادداشت برای مالک: این خط هر PROMPT_COMMAND قبلی را override می‌کند؛ اگر hook دیگری لازم است باید merge شود.
- hostname: `DietPi` باقی ماند. اجرای `hostnamectl set-hostname sensorium-opi5pro-68e44cdf` **انجام نشد** — طبق دستورالعمل مشروط به تأیید مالک است (و در این جلسه `hostnamectl` به system bus هم وصل نشد). شناسهٔ واقعی سیستم در همهٔ recordها `board_id=sensorium-opi5pro-68e44cdf` ثبت شده است.

## مرحله ۴ — checkpoint pre-maintenance

- دستور `octopus_sync export-checkpoint …` **قابل اجرا نبود**: `octopus_sync` نه در PATH است، نه در `/opt/octopus/scripts/` (جستجو شد؛ ابزار مشابه export وجود ندارد). چیزی جعل نشد.
- وضعیت موجود: `inbound/TO-LAPTOP/OCTOPUS-AUDIT-CHECKPOINT/checkpoint.unsigned.json` — `sequence=292`, `head_hash=sha256:62ba9a8a…`, نوشته‌شده `2026-08-17T06:42` (مطابق G15 همان لحظه؛ خروجی زندهٔ خود بورد).
- **وضعیت: در انتظار امضای مالک** روی ویندوز با `sign-checkpoint.bat` (طبق handoff: اگر seq با head زنده mismatch باشد بورد دوباره export می‌کند — فایل تازه را امضا کنید). تا امضا نشده، ریبوت مرحلهٔ ۵ شروع نمی‌شود.

## مرحله ۵ — ریبوت

**اجرا نشد.** پیش‌شرط `OWNER_MAINTENANCE_WINDOW_REQUIRED` در این جلسه به‌صورت صریح تأیید نشده بود. `systemd-analyze verify/critical-chain` هم اجرا نشد (فقط پیش‌ریبوت معنا دارد).
زمینه برای مالک: boot فعلی (c8a0b325) خود نتیجهٔ ریبوت مجاز مالک در ۰۶:۴۰ بوده است (`pre_reboot.json`: `authorized_by_owner=true`، هدف: نقطهٔ PASS دوم GAP-001 — که PASS شد، اما برای بستن GAP-001 طبق معیار دستورالعمل به PASS متوالی بعدی نیاز است).

## مرحله ۶ — GAP-002 (فقط گزارش، بدون اقدام)

```
finding: GAP-002 status conflict
  - runtime observed (fresh, this session):
      gaps/GAP-002-audit_head_unsigned.json (05:17Z): live_sequence=275, checkpoint_sequence=266, status=OPEN, head_match=false
      live export 06:42Z: sequence=292 (seq زنده از 275 به 292 جلو رفته — فاصله از checkpoint امضاشده بیشتر شده)
  - prior advisory: "close GAP-002 next" (before Doctor build)
  - owner official record: DEFERRED_TO_WAVE1
      (منابع: doctor ledger seq=8 و seq=27 «observed.status=DEFERRED_TO_WAVE1, pass=false»؛
       signed_checkpoint.json: "GAP-002 remains DEFERRED_TO_WAVE1. Do not treat this file as CLOSED."؛
       TICKET-DOC-002.json: status=DEFERRED_TO_WAVE1)
  action: NO ACTION TAKEN. Escalate to owner for explicit re-confirmation.
```
همچنین مطابق رکورد CHECKPOINT_266_VERIFY: `closes_gap_001=false, creates_authority=false, decision=KEEP_WAVE0_LOCKED`. منتظر رأی صریح مالک.

## مرحله ۷ — Prometheus / سند قدیمی

- برچسب از قبل (جلسهٔ ۰۶:۱۰ امروز) در **هر دو نسخه** موجود است و محتوای دستورالعمل تغییر نکرده:
  - `/root/LAPTOP-AGENT-INSTRUCTIONS.md` خط ۵۰ (بخش ۴)
  - `/var/lib/octopus/inbound/TO-LAPTOP/LAPTOP-AGENT-INSTRUCTIONS.md` خط ۴۶ (بخش «۴. Metrics»)
  - متن برچسب: `> STATUS: STALE/SUPERSEDED as of 2026-08-17. Runtime confirms 127.0.0.1:9101 loopback-only. Use SSH tunnel per handoff.`
  - شاهد خام: `grep -n "STALE/SUPERSEDED"` → هر دو فایل؛ تأیید runtime: `ss -tlnp` → `127.0.0.1:9101`
  - هیچ خط جدیدی اضافه نشد چون دقیقاً همان خط لازم از قبل موجود بود (اضافهٔ دوباره = ایجاد تکرار).
- پیشنهاد (فقط پیشنهاد، اجرا نشد): سرویس دائمی tunnel روی لپ‌تاپ به‌جای `ssh -N -L` دستی، با `ExitOnForwardFailure=yes` و keepalive (`ServerAliveInterval`).

## مرحله ۸ — سنسورها (بدون آرایش عدد)

منبع: `state/registry/active.json` (09:35:08Z) و تأیید متقابل `state/sensors/health.json` (09:38:59Z) — هر دو:

```
sensors_active:                 4
sensors_discovered_unbound:     2
sensors_manifest_only:         66
sensors_disabled:              29
sensors_stale (ردهٔ اضافی):     2
total sensor_count:           103   (enabled_count: 6)
external_physical_sensors:      0
power_observability:            NOT_INSTRUMENTED
homeostatic_claim_ceiling:      PARTIAL
```

- external_physical_sensors=0: تنها iio موجود `iio:device0 = fec10000.saradc` (ADC روی برد) است؛ hwmonها همه thermal داخلی + pwmfan هستند؛ سنسور خارجی متصل نیست.
- power_observability=NOT_INSTRUMENTED: از snapshot زنده (`power.power_state=NOT_INSTRUMENTED`, note: «add INA219/INA226 before claiming NORMAL»).
- homeostatic_claim_ceiling=PARTIAL: `model_skill=0.0 (critical, not_better_than_baseline)`، `prediction_calibration=unknown/stale`، `skill.eligible=false` (samples=200) ⇒ سقف ادعا PARTIAL است، نه بیشتر.
- جملهٔ «Sensorium با ۱۰۰ سنسور» از این پس باید این‌گونه خوانده شود: ۱۰۳ سنسور تعریف‌شده در رجیستری؛ فقط ۴ تا ACTIVE واقعی؛ ۶۶ تا فقط MANIFEST_ONLY (فقط heartbeat).
- پیشنهاد (فقط پیشنهاد، نصب نشد): ماژول INA219/INA226 برای سنجش توان ورودی — ارزان‌ترین راه رفع محدودیت NOT_INSTRUMENTED.

## کارهایی که اجرا نشد و چرا

| مورد | دلیل |
|---|---|
| ریبوت (مرحله ۵) | بدون تأیید صریح مالک (OWNER_MAINTENANCE_WINDOW_REQUIRED) |
| تغییر hostname به sensorium-opi5pro-68e44cdf | صریحاً مشروط به تأیید مالک |
| اعمال schema جدید verifier (boot_id و…) | نیاز به تأیید مالک |
| تغییر آستانهٔ ۳۰۰s probe (مثلاً به ۶۰۰) | ممنوع طبق دستورالعمل — انجام نشد و انجام نخواهد شد |
| fix ریشهٔ CPU / restart سرویس | «فقط بعد از تأیید مالک فیکس واقعی اعمال شود» |
| `octopus_sync export-checkpoint` | ابزار روی بورد وجود ندارد |
| append به ledgerهای hash-chained | ریسک شکستن زنجیرهٔ تأیید؛ marking با TAINTED_WINDOW انجام شد |
| نصب pidstat / py-spy / strace | نصب ممنوع بود؛ فقط غیبت گزارش شد |
| نصب INA219/INA226 | فقط پیشنهاد؛ نیاز به تأیید مالک |
| هر اقدام روی GAP-002 | رسماً DEFERRED_TO_WAVE1 — فقط گزارش تناقض |

## اقدامات نوشتاریِ انجام‌شده در این جلسه (شفافیت کامل)

1. علامت‌گذاری پنجرهٔ آلودهٔ boot فعلی در ۴ مسیر (skill/, metacontrol/, quarantine/, evidence/stage0/) + فایل /tmp/evidence/stage0-tainted-window.yaml — بدون حذف هیچ دادهٔ قبلی.
2. `/etc/profile.d/manual-shell-audit.sh` (خط دقیق دستورالعمل مرحله ۳ — فقط لاگ، auditd غایب بود).
3. فایل‌های شواهد و گزارش در `/tmp/evidence/` و همین گزارش.

هیچ‌کدام authority را تغییر ندادند (اثبات با هش‌های ابتدا/انتها در بالا).

— پایان گزارش؛ قانون آخر رعایت شد: هر جا عدم قطعیت بود، اجرا نشد و «نیاز به تأیید مالک» ثبت شد.
