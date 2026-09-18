# OCTOPUS — NEXT-AGENT MEGAPROMPT: FULL HISTORY DISCOVERY

GOV_VERSION=V8 · LADDER=L2 · تاریخ: 2026-09-15

## تو چه خبری؟ — خلاصهٔ ۱۰ روز گذشته در ۵ دقیقه

اختصوس یک **ارگانیسم هفت‌بردی** است که روی ۷ برد در شبکهٔ خانگی تو زندگی میکند. مالک (تو، آری) ۱۰ روز vibe-coding کردی و الان اختاپوس:
- **خودش کار تولید میکند** (هر ۳۰ دقیقه بدون لپتاپ)
- **خودش از تجربه یاد میگیرد** (هر ۱۵ دقیقه رویداد → fact)
- **خودش شکستها را ارزیابی میکند** (هر ۶۰ دقیقه feedback loop)
- **خودش کد تولید میکند** (deepseek حالا JSON معتبر میدهد)
- **حافظهٔ ۳۶۷-fact** دارد که از ۱۸۰ بازیابی میشود

ولی هنوز **پول درنیاورده** (verified_cash = $0.00) و مسیر ورودی مالک هنوز تک-poller نشده.

---

## ۱. بدنهٔ اختاپوس — هفت برد

| نود | IP | نقش | وضعیت فعلی |
|---|---|---|---|
| **138** | 192.168.0.138 | coordinator + memory + scheduler | **فعال** — ۱۱ timer روشن |
| **180** | 192.168.0.180 | quality + restore + cognition broker | **فعال** — broker + restore copies |
| **182** | 192.168.0.182 | witness + sensorium | **فعال** — شاهد کلاس-B |
| **100** | 192.168.0.100 | knowledge_retrieve | **فعال** — worker + retrieve |
| **160** | 192.168.0.160 | knowledge_prep (ingestion) | **فعال** — ingestion روی پورت 8160 |
| **193** | 192.168.0.193 | model_infer | **فعال** — T3 extractive-v1 روی پورت 8193 |
| **114** | 192.168.0.114 | eval_batch | **فعال** — evaluator روی پورت 8114 |

SSH: `ssh -i ~/.ssh/octopus_mesh_ed25519 root@<IP>` (از 138 برای نودهای دیگر)

---

## ۲. حاکمیت — چه چیزهایی مجاز است

| سند | مسیر | معنی |
|---|---|---|
| **GOV-V8** | `06-EVIDENCE/.../GOV-V8-REVENUE-IGNITION-2026-09-05.md` | نردبان L0-L4؛ فعلاً L2 |
| **GOV-FREEDOM-V2** | `06-EVIDENCE/.../GOV-FREEDOM-V2-2026-09-13.md` | کار داخلی برگشت‌پذیر = PROCEED بدون پرسیدن |
| **GOV-AUTONOMY-V3** | `06-EVIDENCE/.../GOV-AUTONOMY-V3-2026-09-13.md` | DEFAULT=EXECUTE؛ سبز/زرد/نارنجی |
| **AGENTS.md** | `F:/backup/AGENTS.md` | قرارداد اصلی — هر ایجنت باید بخواند |

**سه ممنوعهٔ مطلق:** (1) هیچ secret چاپ/commit نشود (2) هیچ رسید حذف/بازنویسی نشود (3) هیچ PASS بدون رسید اعلام نشود

**وضعیت فعلی:** `customer_send=false` · `GO-B4=false` · `hold_external=true`

---

## ۳. چه چیزهایی ساخته شد — به ترتیب زمانی

### روز ۱-۳ (سپتامبر ۴-۶): زیمان و ساختار اولیه
- **زیمان** = محصولات هنری (ziman-gift.com.au روی Shopify) — **فروشگاه زنده ولی صفر سفارش**
- رشتههای کدگذاری، ساختار ADK، سیستم خرید
- **زیمان بعداً منسوخ شد** — به painting B2B تغییر جهت داد

### روز ۴-۵ (سپتامبر ۷-۸): اختاپوس بیدار شد
- **GOV-V7** سپس **V8** نوشته شد — حاکمیت اختیار
- **store Shopify** live شد (ziman-gift.com.au) — ولی مشتری نیامد
- **UNLOCK rounds 1-8** — باز کردن گیتها با رأی مالک
- **deep-scan**: 66% از vault unconnected
- **Airtasker monitoring** wire شد

### روز ۶ (سپتامبر ۹-۱۰): ساختار کار
- **W24 owner-reply chain** — دریافت پیام مالک از تلگرام
- **coding worker v1.4** — ساخت patch با مدل
- **witness 182** — شاهد کلاس-B فعال شد
- **ETI simulation** — v1.1 failed, v1.2 repaired

### روز ۷ (سپتامبر ۱۱-۱۲): بدنهٔ سختافزاری
- **OPi5 boards** — ۶ Pro + ۱ Plus هدف
- 182 از OOM درست شد با 2G swapfile
- .100/.160 (nodes قدیمی Hacash mining پاک شد)
- Plus روی eMMC alive شد (`.193`)
- دیسک بحران: F: 0.05→61GB آزاد شد

### روز ۸ (سپتامبر ۱۳): **بزرگترین روز** — اختاپوس شروع به خودتعمیری کرد
- **G13**: نوشتن spool مالک هرگز اجرا نشده بود (pathlib bug در except:pass)
- **G8**: روتینگ لین — پیام B3 به مسیر پول نرود
- **G24**: broker شامل envelope تشخیصی روی همهٔ مسیرهای خروج
- **G16**: broker حالت free-form دارد (mode: patch)
- **G22**: executor وابستگیها را چک میکند
- **اولین patch موفق توسط خود ارگانیسم**: 009-A تولید، تست، canary شد
- **اولین bind موفق مالک→ارگانیسم**: STRATA-CHOICE consumed
- **money gate**: bare «بفرست» = صفر اثر پولی
- **producer recovery**: ENOSPC تزریق، رفع، همان update یکبار ذخیره
- **self-feed**: اختاپوس خودش از شکستها task میسازد

### روز ۹ (سپتامبر ۱۴): deploy و اصلاح
- **B8 deploy شد** — executor با ۴ حفاظ (prefer-patched + base-verify + dep-gate + retire)
- **G28**: باگ dedupe ساختاری (scan-all-executed)
- **watchdog**: ۶ disposition (rc=0 skip، rc=4 auth، rc=5 config، rc=6 unclassified، rc=7 heartbeat)

### روز ۱۰ (سپتامبر ۱۵): **مغز ماندگار** — امروز
- **fleet-scheduler**: timer هر ۳۰ دقیقه، بدون لپتاپ
- **T3 مدل**: extractive-v1 روی 193
- **corpus**: از 1 → 23 → 367 fact
- **PB-4**: حافظه روشن 0.75 در برابر خاموش 0.0 — **IMPROVED**
- **PB-3**: restore از 180، hash match، semantic query کار میکند
- **evaluator 114**: ۱۳ کلاس خطا، score + next_action
- **ingestion 160**: event → candidate → dedup → fact/hypothesis
- **feedback loop 138**: هر ۶۰ دقیقه شکستها → ارزیابی → improvement
- **chain fix**: patch tasks از local رد میشوند به deepseek — **JSON معتبر برمیگردد**

---

## ۴. چه چیزهایی باز است — دقیق و با owner

| مورد | مانع | owner |
|---|---|---|
| **G8 producer deploy** | ops-agent در تیک بعدی؛ درخواست در صف | خودکار |
| **W24 binder deploy** | بعد از G8 (dependency) | خودکار |
| **PB-1 24h soak** | از 04:31Z شروع؛ PASS بعد از فردا | خودکار (صبر) |
| **verified_cash = $0** | هیچ مشتری واقعی هنوز پول نداده | مالک — پیام تازه لازم |
| **160/114 systemd** | سرویسها با nohup کار میکنند؛ unit نصب نشده | خودکار |
| **semantic retrieval** | keyword-based فعلی؛ embedding بعد از corpus و evaluator | خودکار |
| **ziman-gift.com.au** | فروشگاه live ولی صفر سفارش 251+ چک | مالک — تصمیم بازاریابی |

---

## ۵. مسیرهای حیاتی — producer/consumer واقعی

### ورودی مالک (هنوز رقابتی)
```
Telegram → glass_runner (هر ۵ دقیقه poll)
                 ↓ spool
         tg-inbox.jsonl (money lane)
         go_b3_inbox.jsonl (B3 lane — بعد از G8 deploy)
                 ↓
         owner_reply.py (money)
         go_b3_owner_bind.py (B3)
```
**مشکل:** هنوز دو poller فعالند (glass + binder قدیمی). G8 deploy این را حل میکند.

### درآمد (کار میکند ولی پول ندارد)
```
revenue_drive (هر ۶ ساعت)
  → rate_hunt → lead_enrich → money_executor
  → owner_ask → send_queue (۳ email فرستاده شد)
  → owner_reply (از spool میخواند)
```
**وضعیت:** SENT=3 · verified_cash=$0.00 · مشتری هنوز جواب نداده

### خودتعمیری (تازه کار میکند)
```
learning ledger → self-feed → task queue
  → coding_worker → api_budget → deepseek (JSON معتبر)
  → patch → stage test → canary → witness 182 → deploy
  → verify_canary_outcomes → feedback_loop
  → evaluator 114 → improvement → 160 ingestion → corpus
```

### حافظه (رشد میکند)
```
state files → experience_ingest (هر ۱۵ دقیقه) → fleet_facts.jsonl (367)
160 ingestion → dedup/provenance → fact/hypothesis
180 restore → snapshot → readback
```

---

## ۶. شمارههای مهم — از دیسک، نه از حافظه

| سنجه | مقدار | منبع |
|---|---|---|
| fleet_facts | 367 | fleet-memory/fleet_facts.jsonl |
| fleet_jobs | 61+ ردیف | fleet-jobs/fleet_jobs.jsonl |
| coding receipts | 200+ | coding-worker/state/coding-receipts.jsonl |
| corpus قبل از امروز | 1 fact | (فقط P1 bootstrap) |
| PB-4 A_avg | 0.75 | PB4-FINAL.json |
| PB-4 B_avg | 0.0 | PB4-FINAL.json |
| verified_cash | $0.00 | revenue-state.json |
| rate card | $15-60/m² | rate-card.json |
| class-B quota | 1/2 used | ops-receipts.jsonl |
| next class-B slot | 2026-09-15T22:21Z | از ledger |

---

## ۷. چه چیزهایی فراموش نشود

1. **ziman هنوز live است** — فروشگاه Shopify با 35 محصول. صفر سفارش. تبلیغات نخریده.
2. **3 email واقعی فرستاده شد** — به painting leads. جواب نیامد.
3. **token OWNER bot**: @Robo2725_bot (نام «pi 4+1») — مالک از chat id 6150431610
4. **هیچ secret چاپ نشود** — کلیدها فقط نامشان ذکر شود
5. **رسیدها append-only** — هیچ رسید حذف یا بازنویسی نمیشود
6. **138 خاموش نشود** — это commander
7. **180 auto-promote ممنوع** — همیشه RO
8. **اختصاص با توقف نگه نمیدارد** — kill switch = `F:\ofn-node\HALT`
9. **زمان checkpoint دستی ننویس** — همیشه `date -u` اجرا کن
10. **resp_len=0 به معنی مدل صفر تولید کرده نیست** — شاید caller فیلدها را دور ریخته

---

## ۸. فرمان شروع

از این نقطه ادامه بده:

1. `09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/FULL-CYCLE-20260915.json` بخوان — آخرین وضعیت
2. `AGENTS.md` + `GOV-FREEDOM-V2` + `GOV-AUTONOMY-V3` را رعایت کن
3. سهمیهٔ کلاس-B را از ledger بخوان — اگر آزاد است، G8 deploy کن
4. PB-1 را بعد از 24 ساعت چک کن
5. اگر مالک پیام تازه فرستاد، آن را از tg-inbox یا B3 lane بخوان

**هدف نهایی مالک:** اختاپوس خودش پول دربیاورد برای بقای خودش.

---

*این سند توسط OCTOPUS_COMMANDER در 2026-09-15T05:15Z نوشته شد.*
*همهٔ عددها از فایلهای روی دیسک خوانده شدهاند، نه از حافظه.*
