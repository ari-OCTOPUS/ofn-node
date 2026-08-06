---
type: dashboard
status: active
tags: [dashboard, domains]
created: 2026-07-03
updated: 2026-08-07
---

# Domains Status — وضعیت دامنه‌ها (روی فرانت‌متر PROJECT.md)

## ویوی زنده (Bases)

> ✅ **اصلاح ۲۰۲۶-۰۸-۰۷:** پلاگین core «Bases» **فعال است** — تأیید مستقیم از `.obsidian/core-plugins.json` (`"bases": true`) + سه فایل `.base` موجود در همین پوشه (`Projects.base`، `Inbox.base`، `Scout Digests.base`). ادعای قبلیِ «هنوز فعال نیست» دیگر درست نیست. سینتکسِ بلوکِ زیر با همان فرمتِ `Projects.base` (که خودکار کار می‌کند) هم‌راستاست؛ تأیید نهاییِ رندرِ بصری در اپ Obsidian با مالک.

```base
filters:
  and:
    - file.name == "PROJECT"
views:
  - type: table
    name: Domains
    order:
      - file.path
    columns:
      - status
      - risk_level
      - autonomy_level
      - updated
```

## جدول ایستا (پشتیبانِ دستی — Bases فعال است، این جدول برای دورانِ گذار نگه داشته شده)

| دامنه | status | risk | autonomy مؤثر | بلاکر اصلی |
|---|---|---|---|---|
| [[03 - Projects/Accounting/PROJECT\|Accounting]] | active | high | read-only ⛔ | رجیستر انطباق خالی؛ حسابدار ندارد |
| [[03 - Projects/Lead-نقاشی/PROJECT\|Lead-نقاشی]] | active | medium | read-only ⛔ | rotation کلیدها؛ آزمایش #۱ شروع نشده |
| [[03 - Projects/Mining/PROJECT\|Mining]] | active | medium | read-only ⛔ | چرخش wallet؛ رجیستری نودها خالی |
| [[03 - Projects/Crypto - etoro/PROJECT\|Crypto-etoro]] | active | critical | read-only ⛔ | کلیدهای exchange؛ رجیستری خالی |
| [[03 - Projects/Ziman Galerry/PROJECT\|Ziman]] | active | low | read-only ⛔ | عدد ظرفیت ثبت نشده |
| [[03 - Projects/اونلی فنز/PROJECT\|Project-F]] 🔒 | active | high | read-only ⛔ | Track A/B/C شروع نشده؛ مرز body باز |
| [[04 - Architect System/architect/PROJECT\|architect]] | active | critical | read-only ⛔ | TOP-5 آدیت اجرا نشده؛ گیت بسته |
| [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/PROJECT\|هیپنوتیزم]] | active | low | read-only | بازبینی برچسب‌های epistemic |

**⛔ = §Security Gate:** همه read-only تا چرخش ۴ ردیف CRITICAL در [[ROTATION_CHECKLIST]]. بعد از rotation، autonomy هدف هر دامنه در [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]].
