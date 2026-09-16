---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
tags: [painting, lead, trust-engine, runbook, owner]
created: 2026-07-21
updated: 2026-07-21
---

# OWNER RUNBOOK — لِینِ لیدِ نقاشی (COMPLETE-UNARMED)

> یک صفحه برای مالک. لِینِ لید **کامل و متصل** است ولی **مسلح نیست** (هیچ ارسالِ واقعی ممکن نیست).
> این‌جا: چه فلگ‌هایی هست، چطور دمو را ببینی، چطور یک لیدِ synthetic تزریق کنی، چه باید ببینی،
> و چه هنوز ممنوع است. **بدونِ من می‌توانی click-through کنی.**

## ۱. فلگ‌ها (همه پیش‌فرض خاموش — هیچ‌کدام در PAPER_FULL نیست)
| فلگ | چه می‌کند | پیش‌فرض |
|---|---|---|
| `OCTOPUS_WIRE_LEAD_CANDIDATES` | ورودیِ canonical (`submit_candidate` از تلگرام/منو) | **خاموش** |
| `OCTOPUS_WIRE_LEAD_BOUNDARY` | مرزِ HTTPِ امضاشده روی 127.0.0.1:8774 (n8n) | **خاموش** |
| `OCTOPUS_WIRE_LEAD_DISCOVERY` + `_LEAD_DRAFT` | scorer→quote→کارت | **خاموش** |
| `OCTOPUS_WIRE_LEAD_OUTBOUND` | authorizeِ effect + workerِ خروجی (**همچنان NOT_ARMED**) | **خاموش** |
| secretهای `OCTOPUS_INGEST_SECRET_<SRC>` | امضای HMACِ producerهای بیرونی | فقط `.env`؛ الان **PLACEHOLDER**، مالک بعداً ست می‌کند |

هیچ‌کدام روی master روشن نیست. حتی روشن‌شدنِ `OCTOPUS_WIRE_LEAD_OUTBOUND` هم چیزی نمی‌فرستد (transport = stubِ `NOT_ARMED`).

## ۲. دمو را ببین (۵ فرمانِ PowerShell)
```powershell
cd F:\backup\_ops\discovery\2026-07-21_LEAD-SAFETY-C1-DEMO
powershell -ExecutionPolicy Bypass -File replay.ps1
```
انتظار: **۹/۹ PASS** · receiptهای خواندنی · گیت‌ها همه سبز · صفر فلگِ ACTIVATIONِ مسلح.

## ۳. یک لیدِ synthetic تزریق کن (worktree، sandbox — درختِ زنده لمس نمی‌شود)
```powershell
cd F:\backup\_ops\discovery\2026-07-21_LEAD-SAFETY-C1-DEMO
python -X utf8 demo_run.py
```
این خودش یک لیدِ synthetic + یک fixtureِ consented + یک market_signal را از کلِ قوس می‌گذراند.
(تزریقِ زندهٔ منو/API نیازِ روشن‌کردنِ فلگ + راه‌اندازیِ ارگانیسم دارد — که owner-gated است؛ برای
دیدنِ رفتار، همین دمو کافی است و امن‌تر.)

## ۴. چه باید ببینی
1. لیدِ synthetic از `submit_candidate → firewall → فایلِ `uuid.json` → scorer → receipt` عبور می‌کند.
2. رأیِ approve → `on_lead_verdict`: **synthetic هیچ effectِ authorize‌شده نمی‌گیرد** (دفاع در عمق).
3. fixtureِ consented → approve → effect authorize می‌شود → `outbound_worker` = **NOT_ARMED** (صفر ارسال).
4. market_signal → **رد برای outreach**، هیچ فایلِ draftِ top-level.
5. chrono: یک رأیِ انسانی `PAY` را batch می‌کند ولی `lead_outbound` (هر هجی) pending می‌ماند.
6. STOP present → همه release/authorize **deny**.
7. receiptها فقط رویدادهای صادق: `lead.candidate.received / proposal.owner_approved / effect.settled / effect.refused` — **هیچ `communication.sent`** (چون چیزی نرفته).

## ۵. مسیرِ کامل (COMPLETE، اما نقطهٔ آخر = arm که با توست)
```
تلگرام /lead  یا  n8n POST /api/v1/lead-candidates
        → submit_candidate → consent_firewall → dedup → فایل/receipt
        → lead_discovery (lead_sense→scorer→quote) → کارتِ اپراتور
        → رأیِ owner (approve)
            ├─ measurement:  verdict_recorder → OutcomeStore   (سنجش، جدا)
            └─ effect:       on_lead_verdict → lead_effect_gate.authorize (per-effect)
        → outbound_worker → lead_effect_gate.release_and_settle → transport = NOT_ARMED  ← اینجا می‌ایستد
```
**تنها نقطهٔ arm:** وصل‌کردنِ دکمهٔ رأیِ کارتِ زندهٔ تلگرام به `on_lead_verdict` **و** مسلح‌کردنِ یک
transportِ واقعی. هر دو عمداً باز مانده‌اند (این همان «UNARMED» است). `on_lead_verdict` ساخته، تست‌شده
(۱۸/۱۸) و adversarial-verify شده؛ فقط منتظرِ رأیِ صریحِ توست.

## ۶. هنوز ممنوع (حتی با click-through)
- ارسالِ واقعی به انسان/کسب‌وکارِ واقعی (transport مسلح نیست).
- برداشتنِ STOP · روشن‌کردنِ دائمیِ فلگ روی master · هرگونه پول/LIVE · secretِ واقعی در repo.
- تضعیفِ consent firewall (market_signal هرگز outreach).

## ۷. اگر خواستی مسلح کنی
یک رأیِ صریحِ جدا لازم است (فاز آینده): (الف) transport adapterِ واقعی (SMS/email) با کلیدها در `.env`،
(ب) وصلِ دکمهٔ کارت → `on_lead_verdict`، (ج) `set OCTOPUS_WIRE_LEAD_OUTBOUND=1`. تا آن رأی، لِین **کامل ولی خاموش** می‌ماند.
