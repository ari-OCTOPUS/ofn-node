# 🚦 Risk Ladder — رنگ‌بندی اجرای پازل هشت‌پا

> هم‌راستا با لایهٔ رئیس اختاپوس (`Architect/_ops`) و فایل `ARCHITECT-ORGANISM-CONTEXT.md`.  
> این فایل policy اجرایی برای workspace فعلی است؛ secret/PII ندارد.

---

## اصل مادر

هر اکشن اول از این سؤال رد می‌شود:

```text
آیا این کار فقط خواندن/گزارش است، یا به دنیای بیرون اثر می‌گذارد؟
```

- خواندن، گزارش، ساخت فایل پیشنهادی، audit، registry و runbook = کم‌ریسک‌تر.
- publish/send/spend/trade/lodge/pay/create-account/deploy/live-wire = hard-gated.
- Project-F همیشه containment دارد: بیرون از پوشه فقط `Project-F`.

---

## چهار رنگ

| رنگ | معنی | مجاز برای ایجنت | نیازمند verdict انسانی؟ | مثال |
|---|---|---|---|---|
| 🟢 Green | فقط خواندن/گزارش/فایل نو | بله | نه، اگر بدون PII/secret باشد | audit، inventory، ساخت RUNBOOK |
| 🟡 Yellow | ویرایش کم‌ریسک داخل docs/registry | بله، با لاگ و rollback note | معمولاً نه، مگر rule تغییر کند | sync کردن INDEX، اضافه کردن OpenQuestions |
| 🟠 Orange | تغییر contract/policy یا آماده‌سازی live | فقط propose/shadow | بله | تغییر MANIFEST hard_rules، فعال‌سازی adapter، اتصال NBB |
| 🔴 Red | اثر بیرونی/مالی/حقوقی/امنیتی | نه | همیشه | پرداخت، lodge، trade، publish، ساخت اکانت، secret rotation |

---

## Autonomy floors برای tenantها

| پروژه | risk فعلی | کف خودمختاری | دلیل |
|---|---:|---|---|
| Accounting | high | read-only / draft-only | مالیات، ATO/ASIC، PII مالی |
| Lead-نقاشی | medium | propose-only | outreach/spam/DNCR/ACL |
| Mining | medium | INFORM-only | wallet/rig/deploy/trade ممنوع |
| Crypto-eToro | critical | alert-only | exchange keys، BUY/SELL انسانی |
| Ziman | low | propose-only | publish/spend/capacity gate |
| Project-F | high | contained propose-only | privacy/consent/identity containment |
| app/NBB-CP | critical brain | shadow/control-plane only | حاکمیت و invariants |
| 4d_system | high research | owner-approved run only | self-code / no OS sandbox |
| نقشه اختاپوس | low tool | read-only | scanner diagnostic |

---

## Security Gate وضعیت فعلی

طبق context جدید مالک از `Brain.md` و `HANDOFF.md`:

```text
Security Gate = LIFTED 2026-07-06
```

اما:

- secretها هرگز وارد چت/فایل نمی‌شوند.
- HIGH/MED rotationها backlog هفتگی‌اند.
- هر مسیر بیرونی همچنان verdict می‌خواهد.

---

## قانون rollback

هر ویرایش Yellow/Orange باید یکی از این‌ها را داشته باشد:

- فایل جدید باشد، نه overwrite پرریسک؛ یا
- در `DecisionLog.md` ثبت شود؛ یا
- در صورت تغییر contract، مسیر برگشت/علت در همان فایل نوشته شود.

---

## اجرای فعلی

در این مرحله فقط کارهای 🟢 و 🟡 انجام می‌شود:

- registry alignment
- runbookها
- verdict queueها
- تکمیل OpenQuestions
- sync indexها

کارهای 🟠/🔴 فقط پیشنهاد می‌شوند.
