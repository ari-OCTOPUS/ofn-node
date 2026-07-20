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

| # | سؤال | گزینه‌ها | پیشنهاد | جواب A |
|---|---|---|---|---|
| 1 | PF-V5 (لانچ Full Aggressive): باطل یا مشروط؟ | `APPROVED: REVOKE` / `APPROVED: RATIFY-CONDITIONAL` | ⭐ REVOKE (**DEFAULT**) — تا G0+توافق+تست+freeze، بعد پلن لانچ از نو | ______ |
| 2 | Branch/اقامت C: با چه منبعی تأیید می‌کنی؟ یا صادقانه UNKNOWN؟ | FILL در DL-2026-07-20-G0 (نوع منبع + تاریخ + Branch A/B/UNKNOWN) | ⭐ اگر سند/مدرک شخصاً ندیده‌ای: **UNKNOWN** بنویس (**DEFAULT: G0 باز می‌ماند**) | ______ |
| 3 | متن توافق دونفره (DL-2026-07-20-AGREEMENT): تأیید متن؟ | YES / ویرایش می‌خواهم | ⭐ YES → بعدش امضای A + تأیید مکتوب C — **قبل از Day-Zero** | ______ |
| 4 | Body freeze (DL-2026-07-20-BODY-FREEZE): ثبت نهایی؟ | YES / NO | ⭐ YES (**DEFAULT: freeze روی دیسک اعمال شده**) | ______ |
| 5 | نام برند | `Anar Soles` / `Yalda Arch` / بعداً | ⭐ بدون تغییر: **OPEN بماند** (تصمیم برند پیش‌نیاز page نیست؛ فقط قبل از bio لازم است) | ______ |
| 6 | نردبان قیمت | `EXT-04 (VIP فریز تا G2)` / نسخهٔ MASTER-BUILD / نسخهٔ Playbook | ⭐ EXT-04 — ولی تا رأی ندهی، تگ CONFLICT می‌ماند (**DEFAULT: CONFLICT**) | ______ |
| 7 | نقش Fansly | `mirror + discovery-first` / هم‌وزن روز-۱ | ⭐ mirror + discovery-first | ______ |
| 8 | **این repo هرگز remote داشته؟** (تعیین‌کنندهٔ سرنوشت PII در تاریخچهٔ git) | YES / NO / نمی‌دانم | فقط FILL — اگر YES: چرخش شماره/بازبینی filter-repo لازم می‌شود | ______ |
| 9 | CHRONOS | — | ⏭ نامربوط — طبق دستور skip | — |
| 10 | فیکس کد compliance (orchestrator fail-closed + تست) الان commit شود؟ | YES / NO | ⭐ YES — روی برنچ این sprint انجام شده؛ merge با رأی تو | ______ |
| 11 | rename شناسه‌های حاوی نام C (studio) الان بماند؟ | YES / REVERT | ⭐ YES — انجام شده روی برنچ، تست‌ها سبز؛ REVERT یعنی برگردانم | ______ |
| 12 | زودترین تاریخ مشروط Day-Zero | FILL (تاریخ) — فقط بعد از GATE-STAMP=GO معنا دارد | ⭐ خالی بگذار تا P0ها بسته شوند (**DEFAULT: تعیین نشده = NO-GO**) | ______ |

## اکشن‌های فقط-مالک خارج از رأی (یادآوری)
- تصمیم انتقال PII از tracking: دو سند + ۸ عکس `test/` → `08 - Partner (PII)/` یا `_Archive` + ‏`git rm --cached` (من طبق قانون «حذف ممنوع» فقط با رأی تو جابه‌جا می‌کنم).
- `_ops/STOP-ORGANISM` درخت زنده: دست‌نخورده مانده؛ برداشتنش فقط کار توست.
- بعد از پر کردن این برگه: جواب‌ها را در همین فایل ذخیره کن و بگو «ballot پر شد» تا DecisionLog/manifest/queues را قفل نهایی کنم.
