---
type: reference
status: active
project: "[[04 - Architect System/architect/PROJECT]]"
tags: [design, brain, self-improvement, model-swap]
created: 2026-07-03
updated: 2026-07-03
---

# BRAIN-UPGRADE-LOOP — تعویض مغز با تأیید انسانی

> طراحی درخواست اپراتور (2026-07-03): «مغز خودش را هم عوض کند — با تأیید گرفتن، براساس تحقیق جدید وب.» ثبت تصمیم: [[DECISIONS]] D-28. اقدام‌ها: [[BACKLOG]] #21–#22. این سند مکمل §۴ [[SYSTEM-BLUEPRINT-v2]] است، جایگزینش نیست.

## تعریف «مغز» — دو لایهٔ قابل‌ارتقا

| لایه | چیست | مکانیزم ارتقا | سطح autonomy |
|---|---|---|---|
| **M — مدل LLM** | model ID در config (`providers.py` → آینده: `model_registry`) | Lane M این سند | پیشنهاد=AUTONOMOUS · اعمال=**APPROVE_FIRST + passphrase** |
| **P — پرامپت/Skill** | پرامپت‌ها، skillها، دستورالعمل‌ها | حلقهٔ §۴ blueprint + ورودی جدید «تحقیق وب» (Lane P) | مثل قبل: گیت سه‌شرطی + verdict |

**مرز مطلق دست‌نخورده:** weight update / fine-tune همچنان Non-goal است (سطح C ممنوع). تعویض model ID یک **تغییر config** است، نه تغییر وزن — با Non-goals تعارض ندارد. «رئیس کل» انسان می‌ماند (D-01): سیستم فقط پیشنهاد می‌دهد؛ timeout = DENY (D-13).

## Lane M — تعویض مدل (کشف → ارزیابی → پیشنهاد → verdict → canary)

### ۱. کشف (Discovery)

- **منبع اولیه — rule-based، نه متن آزاد:** `GET /v1/models` از API انتروپیک — فهرست رسمی مدل‌ها، جدیدترین اول، با pagination. پارس ساختاری JSON؛ هیچ LLM در این مرحله (سازگار با P11).
- **منبع ثانویه — تحقیق وب (langar-pro):** قیمت (در endpoint مدل‌ها نیست)، بنچمارک، تاریخ deprecation — همه با برچسب `<external_data>` و امتیاز source_quality طبق pipeline موجود.
- زمان‌بندی: job هفتگی + فرمان دستی `/brain check` در تلگرام.
- فیلتر کاندید: خانوادهٔ Anthropic اول (fallback chain حفظ می‌شود)؛ providerهای دیگر فقط برای batch غیرحساس طبق [[11-research-cost-infra-routing]].

### ۲. ارزیابی (Eval gate — همان گیت سه‌شرطی §۴)

- اجرای anchor set (۵۰–۱۰۰ case) روی مدل کاندید از طریق **Batch API (۵۰٪ ارزان‌تر)**.
- شرط عبور: regression روی anchor ≤۵٪ **و** بهبود روی held-out unseen **و** صفر failure category جدید ([[09-research-evaluation-observability]]).
- «cheaper per token ≠ cheaper per task» — مقایسهٔ هزینه روی **task واقعی** انجام می‌شود نه قیمت اسمی ([[11-research-cost-infra-routing]]).
- سقف هزینهٔ هر دور eval: $0.50 (Normal mode)؛ کل Lane M زیر زیرسقف تحقیق.
- پیش‌نیاز سخت: `held_out.json` واقعی (BACKLOG-11) — بدون آن Lane M فقط گزارش می‌دهد، پیشنهاد swap صادر نمی‌کند.

### ۳. پیشنهاد (Proposal card در تلگرام)

```
🧠 پیشنهاد تعویض مغز
فعلی:   claude-haiku-4-5 (tier: ساده)
کاندید: <model-id>
Anchor: -1.2% (≤5% ✓) · Held-out: +6.4% ✓ · Failure جدید: 0 ✓
Δ هزینه/ماه (مصرف واقعی ۳۰ روز از trace): -$4.10
منابع: /v1/models + ۲ لینک (source_quality 12/15، 11/15)
تأیید؟ /approve BRN-042 <passphrase> — timeout 24h = DENY
```

هر پیشنهاد یک ID دارد و در ledger ثبت می‌شود (write-once، مثل verdictهای موجود).

### ۴. اعمال + Canary + Rollback

1. verdict ✓ → تغییر ردیف در `model_registry` (config/DB — **نه prompt**، P3) + git commit (هرگز main).
2. **Canary 48h:** مدل قبلی در fallback chain می‌ماند؛ judge سبک روی نمونهٔ خروجی‌ها (FM-4).
3. drift ≥۵٪ یا جهش failure → **rollback خودکار** به مدل قبلی (AUTONOMOUS — جهت امن) + گزارش تلگرام.
4. چک kill-switch: ابتدای هر مرحله + قبل از commit (مثل §۴.۸ blueprint). هیچ swap وسط task در جریان.

### ردیف‌های جدید action_policy

| action | autonomy |
|---|---|
| `brain.discover` / `brain.eval` | AUTONOMOUS (read-only + زیر بودجه) |
| `brain.propose` | AUTONOMOUS (فقط پیام تلگرام) |
| `brain.swap` | **APPROVE_FIRST + step-up passphrase** |
| `brain.rollback` | AUTONOMOUS (بازگشت به وضعیت تأییدشدهٔ قبلی) |

## Lane P — بهبود پرامپت/Skill براساس تحقیق وب

حلقهٔ موجود §۴ blueprint دست نمی‌خورد؛ فقط یک **منبع ورودی جدید** اضافه می‌شود:

1. Researcher (langar-pro) تکنیک/الگوی جدید را از وب پیدا می‌کند → خروجی = **candidate diff** روی پرامپت/skill + شواهد و لینک.
2. یافتهٔ وب **هرگز مستقیم اعمال نمی‌شود** — فقط به‌عنوان diff پیشنهادی وارد همان گیت سه‌شرطی + judge بین‌خانواده می‌شود (دفاع prompt-injection: `<external_data>` در نوشتن و بازیابی، FM-3).
3. بقیهٔ قواعد بدون تغییر: ≥۵۰ trajectory (D-17)، `MAX_UPDATE_ROUNDS=4`، `FORBIDDEN_IN_PROMPT` (گیت/kill-switch/secrets/مسیر مالی دست‌نخوردنی)، git + rollback <۵ دقیقه (P4).
4. تفاوت با Lane M: اینجا verdict برای **هر diff** لازم است (سطح B فقط با ≥۲۰۰ trajectory و باز هم gated).

## حالت‌های شکست و دفاع‌ها

| ریسک | دفاع |
|---|---|
| صفحهٔ اعلان جعلی/آلوده (injection) | منبع حقیقت = `/v1/models` (پارس rule-based)؛ وب فقط مکمل با `<external_data>` |
| Goodhart روی anchor کهنه | refresh فصلی ~۲۵٪ anchor (FM-10، §۴.۹ blueprint) |
| مدل ارزان‌تر ولی بدتر در عمل | گیت سه‌شرطی + مقایسهٔ per-task، نه per-token |
| حلقهٔ فراری / خرج بی‌سقف | زیرسقف بودجه + kill-switch هر round + hard-stop ماهانه (§۵ v2) |
| swap در غیاب اپراتور | timeout=DENY؛ بدون passphrase هیچ اعمالی |

## نگاشت به فازها

- **MVP:** هیچ — اولویت با BACKLOG-01 (امنیت).
- **v1-فاز:** `model_registry` + `/brain check` دستی + proposal card (BACKLOG-21) و pipeline eval کاندید با Batch API (BACKLOG-22). Discovery فقط دستی.
- **v2-فاز:** job هفتگی خودکار Lane M + فعال‌سازی Lane P (بعد از LIVE شدن حلقهٔ §۴ با held-out واقعی).

## منابع خارجی (2026-07-03)

- [List Models — Claude API Reference](https://docs.anthropic.com/en/api/models-list) — endpoint رسمی `/v1/models`
- [Models overview — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/models/overview)
