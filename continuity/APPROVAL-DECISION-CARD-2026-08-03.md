---
type: approval-decision-card
date: 2026-08-03
status: HOLD
decided_by: owner-via-session
scope: 3 live pending approvals in _octopus/state/approvals.json
---

# کارت تصمیم — ۳ approval زنده (2026-08-03)

## خلاصهٔ وضعیت

پس از بستن ۱۰۳ approval منقضی، **۳ مورد pending** باقی مانده:

| # | id | type | risk | source | created |
|---|---|---|---|---|---|
| ۱ | `sgc-mission-mis-1c23c01e91e00a8f30e9` | sgc_action | medium | mission_approval_bridge | ۰۰:۰۳ |
| ۲ | `sgc-mission-mis-c1a32c8b4dee05705752` | sgc_action | medium | mission_approval_bridge | ۱۵:۴۳ |
| ۳ | `M-20260803-204308-3e466908` | mission | **high** | telegram | ۲۰:۴۳ (امروز) |

---

## کارتِ جزئیاتِ هر approval

### A) `sgc-mission-mis-1c23c01e91e00a8f30e9`

| فیلد | مقدار |
|---|---|
| **title** | بررسیِ لیدهای باز و آمادهٔ claim از مسیرِ proposal router |
| **risk** | medium |
| **action** | `request_qualified_lead_review` |
| **target** | `owner:qualified-lead-review` |
| **class** | A3 (OWNER_GATE) |
| **external_effect** | ❌ no — فقط owner-review card می‌سازد |
| **writes_state** | ✅ بله — owner-card روی دیسک stage می‌شود (نه claim، نه outbound) |
| **touches claim/money/outbound** | ❌ no |
| **duplicate_of** | ⚠️ نامزد duplicate با B (همان intent، همان action) |

### B) `sgc-mission-mis-c1a32c8b4dee05705752`

| فیلد | مقدار |
|---|---|
| **title** | پیشنهادِ صریح به مالک برای ثبتِ attribution.claim روی یک لیدِ مشخصِ تأییدشده |
| **risk** | medium |
| **action** | `request_qualified_lead_review` |
| **target** | `owner:qualified-lead-review` |
| **class** | A3 (OWNER_GATE) |
| **external_effect** | ❌ no |
| **writes_state** | ✅ بله — owner-card stage |
| **touches claim/money/outbound** | ❌ no — صراحتاً «کارتِ تلگرام، نه اجرای خودکار» |
| **duplicate_of** | ⚠️ نامزد duplicate با A |

### C) `M-20260803-204308-3e466908` (جدید — امروز ۲۰:۴۳)

| فیلد | مقدار |
|---|---|
| **title** | «یه لطفی بکن و وضعیتو یه نگاه بنداز ببین چیزی هست» |
| **risk** | **high** |
| **action** | (null dry_run — telegram free-text mission) |
| **target** | (نامشخص) |
| **class** | نامشخص (dry_run_report = null) |
| **external_effect** | ⚠️ unknown — بدون dry_run نمی‌توان قضاوت کرد |
| **touches claim/money/outbound** | ⚠️ unknown |

---

## تحلیل

### A و B: duplicate/تکراری
هر دو `action` و `target` یکسان دارند (`request_qualified_lead_review` → `owner:qualified-lead-review`). هر دو class A3 هستند که فقط **owner-review card** می‌سازند — نه claim واقعی، نه outbound، نه money. این مطابقِ قاعدهٔ سختِ شماست:

> ✅ هیچ attribution.claim واقعی  
> ✅ هیچ ارسال به customer  
> ✅ هیچ money/outbound

**ولی** هر دو intent یکسان دارند. یکیشان duplicate/superseded است.

### C: ریسکِ ناشناخته
این mission از تلگرام اومده با free-text و `dry_run_report = null`. ریسک high. بدونِ dry-run نمی‌توان قضاوت کرد چه می‌کند.

---

## پیشنهاد تصمیم

| approval | پیشنهاد | علت |
|---|---|---|
| **A** (`1c23c01e`) | **HOLD** | اولویتِ فعلی معماری/ادغام است، نه درآمد. owner-review card ساختن وسطِ کارِ معماری، صفِ عملیاتی باز می‌کند. |
| **B** (`c1a32c8b`) | **REJECT** (reason: duplicate/superseded) | با A یکسان است (همان action/target/intent). یکی کافی است. |
| **C** (`M-20260803-204308`) | **HOLD** | risk=high + dry_run=null. بدون dry-run، تصمیم‌گیری ناامن است. اول باید dry-run اجرا شود، بعد تصمیم. |

### قاعدهٔ سختِ رعایت‌شده
- ❌ هیچ attribution.claim واقعی (هیچ‌کدوم claim نمی‌زنند)
- ❌ هیچ ارسال به customer (هیچ‌کدوم)
- ❌ هیچ money/outbound (هیچ‌کدوم)
- ✅ همه فقط owner-card/owner-review می‌سازند (و یا نامشخص)

---

## اقدامِ پیشنهادی (با تأییدِ مالک)

اگر با HOLD + REJECT-B موافقی:

```text
A → HOLD (ماندگار در صف، تصمیم بعدی)
B → REJECT (reason: duplicate/superseded of A)
C → HOLD (تا زمانی که dry_run تولید شود)
```

این **هیچ مأموریتی اجرا نمی‌کند**. فقط state hygiene است (مثل expire قبلی).

---

## rollback

`continuity/backups/approvals.before-expire-20260803T094822Z.json` (snapshotِ قبل از expire)  
`continuity/backups/approvals.before-decision-20260803T*.json` (snapshotِ قبل از این تصمیم — اگر اجرا شود)
