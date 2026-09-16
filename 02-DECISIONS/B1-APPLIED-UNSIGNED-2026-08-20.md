---
type: proposal
status: active
tags: [octopus, b1, unsigned]
created: 2026-08-20
updated: 2026-08-20
---

# B1_APPLIED_UNSIGNED — 2026-08-20

decision_id: B1-APPLIED-UNSIGNED-2026-08-20
status: **B1_APPLIED_UNSIGNED** (نه hidden exception)
ceremony_required: proposal → simulation → falsifier → shadow → owner vote → **signed** promotion
signature: PENDING — `owner-key.enc` FOUND_AT (وجود) ولی Ed25519 این جلسه زده نشد

ledger:
- `B1_APPLIED_UNSIGNED` id `a4dc56931ca84044b754c7f1fecd0d77` hash `8a506117983cbc6d`
- `B1_SAFETY_ROLLBACK_TO_30` id `1219e24773944474b45c88badfc933b5` hash `14224c3565d56599`
- tip after notes n=12750 hash `e101f7ce313f8cd9`

## آنچه نباید پنهان شود

B1 روی runtime رفت **بدون** امضای Ed25519.

- کارت: `02-DECISIONS/PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19.md` هنوز `owner_vote: PENDING`
- `phase-gates.jsonl` خط `b1-apply` 2026-08-20T00:06:53 = `APPLIED_WITH_ROLLBACK` · `signature: PENDING — owner-key.enc unverified (recorded, not blocking)`
- زنده: اولین تخصیص غیرصفر beat **42165** · `daily_cap=1000` · ۱۱ عضو · `beat_pool=1.246`

جملهٔ «ثبت شد، نه بلاک» یعنی مراسم بریده شد. حکم درست: **`B1_APPLIED_UNSIGNED`**. اگر این برچسب نماند، استثنا رویه می‌شود.

## Rollback ایمنی (همچنان بدون امضا)

مالک: تا روشن‌شدن واحد، مقدار را به ۳۰ برگردان.

- `budgets.yaml` `life_currency_daily_cap` **1000.0 → 30.0** (این جلسه)
- لجر: `B1_SAFETY_ROLLBACK_TO_30` (unsigned overlay روی unsigned apply)
- این rollback مراسم را کامل نمی‌کند؛ فقط اندازهٔ استخر داخلی را کم می‌کند
- امضا وقتی کلید حل شود، هر دو رویداد را می‌پوشاند نه اینکه تاریخ را پاک کند. کارت آماده: [[B1-SIGNING-CARD-2026-08-20]] (UNSIGNED تا verify).

## مسیر کامل هنوز باز است

cardiac همچنان `daily_cap` نمی‌نویسد. fallback yaml زنده است. نوشتن فیلد به `cardiac.py` (B1) جداست و این جلسه انجام نشد.

## رأی پسینی مالک — 2026-08-20

رأی چت مالک (جلسهٔ ZCode، چیپ پنج‌گزینه‌ای ~13:50 +10:00): **«تأیید پسینی با ثبت چت»** —
این استثنا تأیید و پنهان نمی‌ماند؛ حکم به `B1_CHAT_APPROVED_ED25519_PENDING`
ارتقا یافت. جزئیات: [[OWNER-RULINGS-2026-08-20-CHAT]] · کارت اصلی:
[[PROPOSAL-B1-cardiac-dailycap-wiring-2026-08-19]].

## ERRATA (T34، دستور مالک #۶) — 2026-08-20 ~14:10 +10

حکم `KEY_IDENTITY_CONFIRMED_SAME`: امضای Ed25519 واقعی، معتبر و مستقل‌وریفای است
([[../06-EVIDENCE/T34-KEY-IDENTITY-2026-08-20]]). برچسب‌های
«PENDING — owner-key.enc unverified» و «ED25519 معلق به حل owner-key» در این
کارت **باطلند** — منشأ آن‌ها ندیدنِ کلید زندهٔ `~/.octopus-signing/` بود؛ فایل
enc صرفاً بکاپ رمزشده (`Salted__`) است و شرط اعتبار امضا نیست.
**وضعیت نهایی B1: `B1_SIGNED_ED25519`** (کارت امضا از 11:12 +10 SIGNED بود).
عنوان تاریخی این سند (APPLIED_UNSIGNED) به‌عنوان روایت ساعت صبح حفظ می‌شود؛
حکم نهایی همین ERRATA است.
