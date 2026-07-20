---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, governance]
created: 2026-07-20
updated: 2026-07-20
---

# 🗳 OWNER-BALLOT — 2026-07-20 (۱۰ دقیقه، ۱۲ سؤال)

> A: جلوی هر سؤال جواب را تایپ کن (یا خط بکش). جواب‌های ۱ تا ۴ باید عیناً به [[../DecisionLog|DecisionLog]] هم منتقل شوند (خودم فرمتش را آماده کرده‌ام — فقط امضا/تاریخ). پیشنهاد من با ⭐ مشخص است. **DEFAULT** یعنی اگر سکوت کنی همین اعمال می‌شود.

> ✅ **پر شد — 2026-07-20 (رأی صریح A در چت، جلسهٔ همین روز).** نکته: ویرایش قبلی روی دیسک در ردیف ۱ («RATIFY-CONDITIONAL» داخل ستون پیشنهاد) با رأی صریح و بدون ابهامِ چت (**REVOKE**) جایگزین شد.

| # | سؤال | گزینه‌ها | پیشنهاد | جواب A |
|---|---|---|---|---|
| 1 | PF-V5 (لانچ Full Aggressive): باطل یا مشروط؟ | `APPROVED: REVOKE` / `APPROVED: RATIFY-CONDITIONAL` | ⭐ REVOKE — تا G0+توافق+تست+freeze، بعد پلن لانچ از نو | **APPROVED: REVOKE** ✅ |
| 2 | Branch/اقامت C: با چه منبعی تأیید می‌کنی؟ یا صادقانه UNKNOWN؟ | FILL در DL-2026-07-20-G0 (نوع منبع + تاریخ + Branch A/B/UNKNOWN) | ⭐ اگر سند/مدرک شخصاً ندیده‌ای: UNKNOWN | **Branch A — «مدرک را شخصاً دیده‌ام» (اظهار A در چت)**؛ نوع دقیق منبع هنوز در DL-G0 تکمیل نشده → G0 باز |
| 3 | متن توافق دونفره (DL-2026-07-20-AGREEMENT): تأیید متن؟ | YES / ویرایش می‌خواهم | ⭐ YES → بعدش امضای A + تأیید مکتوب C — **قبل از Day-Zero** | **YES + امضای A ثبت شد (چت)**؛ تأیید مکتوب C مانده |
| 4 | Body freeze (DL-2026-07-20-BODY-FREEZE): ثبت نهایی؟ | YES / NO | ⭐ YES | **YES** ✅ (تأیید کلی «موافقم با رأی‌های ثبت‌شده») |
| 5 | نام برند | `Anar Soles` / `Yalda Arch` / بعداً | ⭐ OPEN بماند | **OPEN** (طبق پیشنهاد) |
| 6 | نردبان قیمت | `EXT-04` / MASTER-BUILD / Playbook | ⭐ EXT-04، ولی بدون رأی صریح CONFLICT می‌ماند | **رأی صریح داده نشد → CONFLICT می‌ماند** (EXT-04 در فهرست قفل نهایی انتخاب نشد) |
| 7 | نقش Fansly | `mirror + discovery-first` / هم‌وزن روز-۱ | ⭐ mirror + discovery-first | **mirror + discovery-first** ✅ |
| 8 | **این repo هرگز remote داشته؟** | YES / NO / نمی‌دانم | فقط FILL | **NO — هیچ‌وقت** ✅ (چرخش فوری لازم نیست؛ قبل از هر remote آینده اول R10) |
| 9 | CHRONOS | — | ⏭ skip | — |
| 10 | فیکس کد compliance الان commit شود؟ | YES / NO | ⭐ YES | **YES** ✅ (commit ‏`ab8b8bd` + مجوز merge) |
| 11 | rename شناسه‌های حاوی نام C بماند؟ | YES / REVERT | ⭐ YES | **YES** ✅ |
| 12 | زودترین تاریخ مشروط Day-Zero | FILL | ⭐ خالی تا بسته‌شدن P0ها | **تعیین نشد = NO-GO** |

## اکشن‌های فقط-مالک خارج از رأی (یادآوری)
- تصمیم انتقال PII از tracking: دو سند + ۸ عکس `test/` → `08 - Partner (PII)/` یا `_Archive` + ‏`git rm --cached` (من طبق قانون «حذف ممنوع» فقط با رأی تو جابه‌جا می‌کنم).
- `_ops/STOP-ORGANISM` درخت زنده: دست‌نخورده مانده؛ برداشتنش فقط کار توست.
- بعد از پر کردن این برگه: جواب‌ها را در همین فایل ذخیره کن و بگو «ballot پر شد» تا DecisionLog/manifest/queues را قفل نهایی کنم.
