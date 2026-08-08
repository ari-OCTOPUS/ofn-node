---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, mutations]
created: 2026-07-18
updated: 2026-08-08
---

# 🧬 نقاط کور و جهش‌های اختاپوس (۲۰۲۶-۰۸-۰۴)

> **به‌روزرسانیِ ۲۰۲۶-۰۸-۰۴.** جهش‌هایِ ۲۰۲۶-۰۷-۱۷ را با وضعیتِ تأییدشده‌ی امروز
> علامت‌گذاری کردیم + جهش‌هایِ جدید کشف‌شده در برش‌های ۰-۳ و جلسهٔ راستی‌آزمایی را
> افزودیم. نسخهٔ پیشین در git موجود است.

---

## ۱. تعریفِ جهش در این پروژه

[MUTATION] یعنی قابلیتی که:
- مستقیماً به هدف‌های درآمدی آشکار (lead/ziman/...) محدود نیست.
- به self-improvement، self-model، survival، novelty، epistemics، doctor، governance مربوط است.
- اگر فعال شود، رفتارِ کلِ ارگانیسم را تغییر می‌دهد.
- ممکن است scaffold باشد، ولی اگر به loop وصل شود، مهم می‌شود.

---

## ۲. جهش‌هایِ ثبت‌شده (با وضعیتِ امروز)

| جهش | مسیر | وضعیتِ ۲۰۲۶-۰۸ |
|---|---|---|
| **Box-of-Agents** | `_ops/doctor/box` | [UNKNOWN] هنوز probeِ هدفمند نشده — اولویتِ پایین (بی‌ربط به مسیرِ lead/اثر). |
| **Falsifiability harness** | `doctor/box/falsif_harness.py` | [OPPORTUNITY] مثبت؛ خود را با null baseline می‌سنجد. |
| **Fusion/novelty** | `doctor/box/b4_fusion.py` | [MUTATION] off-loop؛ اگر on-loop شود human-gate لازم دارد. |
| **Epistemics** | `_ops/epistemics` | [FACT] پشتِ `OCTOPUS_WIRE_EPISTEMICS`؛ در state ِ زنده روشن دیده شد (wiring.epistemics). |
| **Germline** | `_ops/germline.py` | [FACT] در state: `germline_lag_h` و `germline_alert:"ok"` — alert است، نه control signal. |
| **Nociceptor** | `_ops/neural/nociceptor.py` | [UNKNOWN] pain/protective وجود دارد؛ مسیرِ مصرف در cortex هنوز نگاشته نشده. |
| **Neural consolidation** | `_ops/neural` | [FACT] پشتِ `OCTOPUS_WIRE_NEURAL`؛ hebbian/bcm/circadian فعال. |
| **PMO** | `03 - Projects/_OCTOPUS-PMO` | [FACT] اندامِ مدیریتِ برنامه است، نه duplication. |
| **Autonomy free tier** | `cortex/autonomy_matrix` | [FACT] `OCTOPUS_AUTONOMY_FREE` از قبل روشن است (ردّ ادعای مگاپرامپت §۹). |

---

## ۳. نقاط کورِ **جديد** (کشفِ ۲۰۲۶-۰۸)

### ۳.۱ [RISK] governor/obsidian گم‌شده در miniapp_state
[FACT] تست‌های `test_miniapp_ops_readmodel.py` به `get_governor_state`,
`get_obsidian_state`، `_OBSIDIAN_DOCS`، `_governor_drift`، `cache_clear`، `_mono`
اشاره می‌کنند که در `miniapp_state` **وجود ندارند** → ۲۵ شکستِ `AttributeError`.
[UNKNOWN] این توابع حذف شده‌اند یا به ماژولِ دیگری منتقل؟ اگر حذف، تست stale است؛
اگر منتقل، import شکسته. **نیازمندِ تحقیق.**

### ۳.۲ [RISK] scorer فارسی = لیدِ قانونی را دور می‌ریزد
[FACT] `lead_scorer.py` ۱۰۰٪ انگلیسی است؛ vocab فارسی (`fa_required_any`: رنگ/نقاشی/...)
پشتِ `OCTOPUS_LEAD_FA_VOCAB` است که **خاموش** است. کامنتِ `lead_scorer.py:42` خود
این را تأیید می‌کند. یه لیدِ فارسیِ قانونی از مشتری وارد می‌شود ولی `score=0, skip`
می‌گیرد. **گپِ واقعی در مسیرِ lead.** (lead 001 در جلسهٔ ۲۰۲۶-۰۸-۰۳ این دام را خورد.)

### ۳.۳ [RISK] drive_outbound در تولید ولی فقط هر ۳۰ beat
[FACT] `wiring.py:2934` در `lead_pipeline_beat`، `outbound_worker.drive_outbound` را
صدا می‌زند (پشتِ `OCTOPUS_WIRE_LEAD_OUTBOUND`). یعنی ایمیلِ واقعی **می‌تواند** خودبخود
ارسال شود، فقط هر ۳۰ beat و با gated_effect ِ authorized. برایِ اولین ارسال، گیرندهٔ
انسانِ واقعی (برگشت‌ناپذیر) لازم است.

### ۳.۴ [RISK] drive_outbound از دو secret ِ جدا تغذیه می‌شود
[FACT] gateway از `OCTOPUS.env` می‌خواند (RESTART-PROCESS.ps1:161)، organism از
`OCTOPUS-flags.cmd` (RUN-ORGANISM.bat:26). یه فلگ در یکی و نه دیگری = رفتارِ ناهماهنگ.
جلسهٔ ۲۰۲۶-۰۸-۰۳ PF_MINIAPP را اول در flags.cmd گذاشت (gateway ندید)، بعد در OCTOPUS.env.

### ۳.۵ [RISK] RESTART-ALL false-negative (رفع شد)
[FACT] acceptance gate فقط `ts` را چک می‌کرد → snapshotِ گذرایِ shutdown با
`stop_organism=true` یه ری‌استارتِ سالم را FAIL کرد. **رفع شد** (`97b3caf`): حالا
هم `ts` و هم `started` ِ پروسهٔ نو چک می‌شود.

---

## ۴. نقاط کورِ **بسته‌شده** (پاسخ‌داده‌شده از ۲۰۲۶-۰۷-۱۷)

| نقطه‌کورِ قدیم | پاسخِ ۲۰۲۶-۰۸ |
|---|---|
| چند Source of Truth؟ | **`_ops` بدنِ زنده است؛ بقیه افزونه.** (Snapshot §۱) |
| Box-of-Agents active یا scaffold؟ | [UNKNOWN] ولی اولویتِ پایین — بی‌ربط به اثر. |
| Epistemics off-loop؟ | روشن در wiring ولی authoritative نیست. |
| Germline control یا alert؟ | **alert** (`germline_alert:"ok"`، نه freeze/redirect). |

---

## ۵. ریسک‌هایِ جهش (بدون تغییر — هنوز معتبر)

| ریسک | توضیح |
|---|---|
| objective creep | self-improvement از هدفِ درآمدی جلو بزند |
| self-preservation drift | germline از backup به هدفِ رفتاری تبدیل شود |
| off-loop activation | scaffoldهای خاموش بدون readiness وارد loop شوند |
| split-brain | چند بدن/مغز هم‌زمان خود را SoT بدانند |
| novelty without gate | خلاقیت بدون human gate به production برسد |
| **stale documentation** | نقشه‌ها/اسناد از فایل‌های واقعی عقب باشند — **این خودِ این vault قربانیِ آن بود** |

---

## ۶. اولویتِ probe بعدی (به ترتیبِ ارزش برای «اثر»)

1. **governor/obsidian گم‌شده** — کجا رفتند؟ stale یا منتقل؟ (۳.۱)
2. **scorer فارسی** — `OCTOPUS_LEAD_FA_VOCAB` روشن کنیم؟ (۳.۲) — رأیِ مالک لازم.
3. Nociceptor به کجا وصل است؟ (مصداقِ کاملِ ۳.۴ قدیم).
4. Box-of-Agents — فقط اگر اولویتِ اثر اجازه داد.
