# OWNER-GO-LOCKS - Ziman / Fugu Strong Agent 48h

## 2026-08-24 AEST
- **G2 LOCK+DEPLOY:** Sydney metro same-day 8am-10pm; AU elsewhere 2-5 business days; no overnight 10pm-8am
- **G3 LOCKED:** wine in 0007 photos is FAKE/PLASTIC - ban wine/alcohol/Jacob's Creek in all copy/ads
- **Owner FULL GO:** G1 CDN delete, G2 deploy, medium SKUs, Cycle C+D, 0007 paid path
- **0014** unpublished (draft) - CDN purge covered by owner **G1** FULL GO
- Continue Fugu cycles under FULL GO (medium SKUs + Cycle C+D)

## 2026-09-02 night — قفل‌های زندهٔ R0 season (وضعیت فعلی)
- **WAL** = `"0"` خلع‌سلاح (set_by owner-disarm-armin-2026-09-02) — re-arm فقط با رسید صریح مالک؛ بند «re-arm tonight» سابق منسوخ.
- **fast-lane** = قفل تا merge شدن **#102** (گیت استقلال) — پیش‌فرض در سکوت: قفل بماند.
- **فریز اندام‌ها** (Cockpit زنده / Telegram Glass / هر اندام تازه) = پابرجا تا رأی مادهٔ ۱۰ مالک، و فقط بعد از #102.
- **merge discipline** = هیچ self-merge؛ مسیر CODEOWNERS فقط Elahe-z؛ مرج فقط روی mergeable_state=CLEAN.
- **restart/kill/bind پروسه‌ها** = ممنوع (سه یونیت failed با تایمر خودشان دوباره راه می‌افتند؛ درمان پورت‌ها = رأی V2 باز).
- **ارسال بیرونی** (DET/email) = فقط دست مالک (R3)؛ برچسب Gmail دست‌نخورده.
- **حریم خصوصی** = صورت‌حساب/بیمه/قرارداد/شماره‌حساب هرگز در مخزن عمومی GitHub؛ فقط والت + بورد 138.
- **verified payments**: شرط عددی فریز برآورده (۵ پرداخت بانکی) — بازشدن با رأی، نه خودکار.
## 2026-09-03 صبح — قفل‌ها پس از رأی ۴ گیت (وضعیت جایگزین بند قبلی)
- **WAL = REARM AUTHORIZED · EXECUTION REPORTED/UNVERIFIED-until-independent-read** (agent-executed 15:10Z; live re-read 15:35:47Z value=1 sha 234f81f8…; verify one-liner in FOUR-GATES receipt; rollback documented; caps 25/50/0 + two-step confirm intact). OFN_WIRE_OUTBOUND همچنان 0.
- **مسیر ارسال quote = بسته**: 110A فقط تولید؛ 110B (#113) پارک تا GOV-V6 روی main + رأی سازگاری D-26/D-27 + تست‌های منفی.
- **مادهٔ ۱۰ = باز** (Cockpit هفت‌کارته + تلگرام فقط‌خواندنی؛ دو PR در ساخت).
- **fast-lane = روشن** از merge شدن #107 (یعنی یک رأی معتبر GOV-V6 برای docs/tests سبز).
- ممنوعیت‌های پابرجا: no self-merge · رأی ربات هرگز · restart/kill ممنوع تا پیام تایمر · مدارک مالی هرگز مخزن عمومی.
## 2026-09-03 ~09:30 AEST — بند تفکیک کانال‌های ارسال (حل تنش R3 ↔ رأی۱۷/گیت۲)
**قاعده: رأیِ یک دامنه، مجوزِ دامنهٔ دیگر نیست. هر ارسال باید نام دامنه و شمارهٔ رأی خودش را دارد.**

| دامنه | وضعیت | مجوز/سقف |
|---|---|---|
| **لید — ایمیل آژانس‌ها** | **خودکار مجاز** | رأی ۱۷ (2026-07-31) + ARM مالک (2026-08-31) + گیت۲ (2026-09-02T15:10Z). سقف ۱۰/روز دو-لایه (override با `OCTOPUS_LEAD_DAILY_SEND_CAP`، رأی 2026-08-12) + چارچوب D-27 (۲۵/روز، AUD۵۰/روز) + kill-switch `OFN_EXTRA_CLOSED_GATES`. شمارنده: `data/state/legs/lead-send-counter.json` فقط با sent=True واقعی |
| **تلگرام → مالک** (pulse/گلاس) | **خودکار مجاز** فقط به چت‌های مالک/کانال شیشه `-1004440663399` | Lane I رأی Q7 + ماده-۱۰ لین ۴ (#114)؛ fail-soft با رسید در events.jsonl |
| **DET / ایمیل مشتری / quote_sent** | **فقط دست مالک** (R3) — خودکار ممنوع | زنجیرهٔ درآمد در `campaign_envelope_ready` ختم می‌شود؛ 110A فقط تولید، 110B (#113) پارک |
| **live_sms · live_dm · tender_submit · vendor_submit · portal_submit · terms_acceptance · auto_scrape · auto_post · auto_dm** | **کلاً بسته** — حتی دستی هم نه، تا رأی جداگانه | مقدار زندهٔ `OFN_EXTRA_CLOSED_GATES` در node.env بورد |

**تصحیح اندازه‌گیری**: بند صبح «OFN_WIRE_OUTBOUND همچنان 0» اندازه‌گیری‌نشده بود — مقدار زندهٔ node.env بورد از ≤2026-08-22 (جلسهٔ shopify-domain) `=1` است، اما طبق config.py:78–81 **intent-only** است و هیچ گیت‌ای را نمی‌بندد؛ آن را ایمنی مترقب نباشید (حذف/تبدیل به startup-assert = debt ثبت‌شده).

### کانال چهارم — کشف 2026-09-03؛ رأی در معماری پیدا شد ✓
| دامنه | وضعیت اندازه‌گیری‌شده | رأی |
|---|---|---|
| **octopus-bridge → cp.master-painting.com** | `OCTOPUS_BRIDGE_OUTBOUND_ENABLED=1` · `OCTOPUS_BOARD_CP_PULL=1` · سرویس active (127.0.0.1:8796) · env مهر 2026-08-22 09:48 | **AUTHORIZED — جلسهٔ unlock مالک 2026-08-22**: پکیج BOARD2-OWNER-PACKAGE-2026-08-22 («Bridge پس از key-rotate PASS — OUTBOUND=1 · PULL=1 · Phase-3 CONTROL pull PASS») + OWNER-UNLOCK-2026-08-22.json (grant: 02-DECISIONS/OWNER-GRANT-UNLOCK-LOCKS-2026-08-22.md) + OCTOPUS-BOARD2-BRIDGE-KEY-ROTATE-2026-08-22/OWNER-AUTHORIZATION |

```
measured_at=2026-09-03T01:05Z  cmd= ssh ari@192.168.0.138 systemctl cat octopus-bridge --no-pager && cat ~/.config/ofn/octopus-bridge.env
rollback = OCTOPUS_BRIDGE_OUTBOUND_ENABLED=0 + CONTROL_URL= (با رأی + restart مجازشده)
```

### ارتقای شاهد WAL — WITNESS_A (2026-09-03T01:22:06Z)
```
reader = board-182 «sensorium-opi5pro» (خودِ شاهدِ معماری؛ خواندن readonly به ari@138 دارد)
read   = ssh root@182 → ssh ari@138 sha256sum managed_flags.json
result = 234f81f81817b1256654cdaa9ba1a681df2d2260482e561ac813ba3e39b2e2d0 ← مطابق، محاسبه روی ماشین دوم
WAL_REARM_EXECUTION = VERIFIED (WITNESS_A — ماشین دوم؛ خوانش انسانی جداگانه همچنان ممکن ولی دیگر شرط نیست)
```

### قاعدهٔ اندازه‌گیری (اضافهٔ ~09:50 AEST، پس از کشف drift سندی)
**هر عدد در این سند که وضعیت یک پرچم/سرویس را ادعا می‌کند، باید کنارش `measured_at` و فرمان اندازه‌گیری داشته باشد. ادعای بدون اندازه‌گیری = ننوشتن.** سند قفل‌ها خودش نباید منبع drift شود (نمونه: «OFN_WIRE_OUTBOUND همچنان 0» از صبح تا ظهر تصادفی درست مانده بود).

اندازه‌گیری‌های پشتیبان بند بالا (همه از F:\ با ssh به ari@192.168.0.138):
```
managed_flags.json (WAL=1, sha 234f81f8…)     measured_at=2026-09-02T22:56Z  cmd= sha256sum + cat ~/ofn/ofn/agi2027_runtime/managed_flags.json
node.env: OFN_WIRE_OUTBOUND=1 · OFN_WIRE_EMAIL=1 · OFN_WIRE_PUBLISH=1 ·
          OFN_EXTRA_CLOSED_GATES=(۹ کلاس) · OFN_TELEGRAM_CHANNEL_ID=-1004440663399
                                               measured_at=2026-09-02T22:56Z  cmd= grep -nE '^OFN_WIRE|^OFN_EXTRA|^OFN_TELEGRAM' ~/.config/ofn/node.env
lead-send-counter {"date":"2026-09-02","sent":1} measured_at=2026-09-02T23:05Z cmd= cat ~/ofn/data/state/legs/lead-send-counter.json
digest timer disabled                          measured_at=2026-09-02T23:27:56Z cmd= systemctl is-enabled/is-active octopus-digest.timer (rollback: enable --now)
```
