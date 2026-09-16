---
type: strategy
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[MASTER-BUILD-2026-07-04]]"
  - "[[Feet-Content-Business-Master-Playbook]]"
  - "[[research-results/12-prelaunch-verification-2026-07-05]]"
  - "[[THREAD-CLOSURE-D-2026-07-10]]"
tags: [project-f, brand, naming, decision]
aliases: ["Project-F Brand Name Decision", "تصمیم نام برند"]
---

# BRAND-NAME-DECISION — Project-F (propose-only, HARD-GATED)

> ماتریسِ تصمیمِ نام. **انتخابِ نهایی = verdict دونفرهٔ A+C (سؤال #۶)، و به #۹ گره خورده.** ساختِ اکانت/رجیسترِ هندل = hard-gated، فقط مالک. چک‌های live (handle/domain/IP-AU trademark) = **DEFERRED به لحظهٔ signup** — اینجا هرگز «انجام‌شده» علامت نمی‌خورند.

## ماتریسِ کاندیدها
| کاندید | منبع/رتبه | Pros | Cons | Collision (12-prelaunch) | Persian متنی؟ | City-geo؟ | وضعیت |
|---|---|---|---|---|---|---|---|
| **Anar Soles** | MASTER #۱ | خوش‌آهنگ؛ چشمکِ دیاسپورا؛ کوتاه/برندپذیر؛ لور آماده | تلفظِ EN نامطمئن | 🟢 **صفر — قوی‌ترین** | نرم/مبهم («anar means pomegranate—that's all you get») | نه | **پیشنهادِ #۱** (THREAD-CLOSURE/DecisionLog، منتظر verdict) |
| **Yalda Arch** | reserve (جدید) | «بلندترین شب» لورِ شب‌محور + arch | Yalda اسمِ دخترانه؛ **لیکِ Persian صریح** (جشنِ ایرانی) | 🟢 clear | **صریح** | نه | reserve (پیشنهاد) — پشتِ #۹ |
| **Saffron Steps** | reserve ۲ | زعفران=گرما/لوکس؛ آلیتراسیون | کمی «فروشگاهی» | 🟢-ish | متوسط (زعفران=ادویهٔ قابل‌انکار) | نه | جایگزین |
| **Arch & Amber** | Playbook #۱ | soft-luxury؛ بدونِ کلمهٔ پرریسک؛ صفر Persian | همسایهٔ amberarch.com (شرکتِ بریتانیایی، ۱۹۹۵) | 🟡 RISKY-LOW | نه | نه | Playbook #۱ (تنزل‌یافته) |
| **The House Red** | MASTER reserveِ قدیمی | لاکِ burgundy امضا + شوخیِ شراب؛ صفر Persian | SEO همیشه «wine» (discoverability) | 🟡 RISKY | نه | نه | یک پله پایین |
| ~~Softly Sydney / Harbour Soles / Sunlit Soles~~ | Playbook | — | **شهر در نام/چارچوب** | — | نه | **بله — نقضِ #۶** | ⛔ **حذف از شورت‌لیستِ عمومی** (فقط رفرنسِ داخلیِ زیبایی‌شناختی؛ مستقل از #۹) |

## تعارض‌های حل‌شده (به‌صورت پیشنهاد، نه تصمیم)
- **#۱ بین دو master فرق داشت:** MASTER=Anar Soles ↔ Playbook=Arch & Amber. reconcile ‏2026-07-10 به نفعِ Anar Soles (صفر collision) — Arch & Amber به‌خاطرِ amberarch.com به 🟡 تنزل.
- **reserve drift:** MASTER قدیمی=The House Red ↔ جدید=Yalda Arch. 12-prelaunch سمتِ Yalda را (genericness رقیب) تقویت می‌کند؛ ولی Yalda لیکِ Persianِ صریح دارد.

## توصیه [PROPOSAL]
1. **#۱ = Anar Soles**، **reserve = Yalda Arch** — هم‌راستا با پیشنهادِ استاندارِ 07-05/07-10 و تنها گزینهٔ صفر-collision.
2. **هشدارِ #۹ (گِری‌زون):** یک نامِ واژه‌فارسی (Anar/Yalda) خودش سیگنالِ قومیِ **متنی**ِ خفیف است — پیشنهاد به این دلیل «منطبق» تلقی شده که برای بیگانه اسمِ خاصِ خنثی می‌خواند، ولی این تنها جایی است که «visual-only» به واژهٔ نوشته می‌رسد. Anar لیکِ نرم، Yalda لیکِ صریح دارد → دو سرِ #۹. **مالک باید هنگام انتخاب این framing را تأیید کند و #۹ را حل کند.**
3. **اگر مالک صفر-مواجههٔ Persian-متنی بخواهد:** The House Red (نیازِ mitigationِ discoverability) یا Arch & Amber (نیازِ clearanceِ amberarch.com) گزینه‌های بدونِ لیک‌اند.
4. **پیش‌نیازهای اثبات‌نشده (owner-run، پیش از قفل):** availabilityِ live هندل در X/Reddit/OF + domain/RDAP + جستجوی دستیِ IP Australia trademark. هیچ‌کدام انجام نشده = `[DEFER-TO-SIGNUP]`.

## Verdict (owner)
```yaml
PF-BRAND-NAME:
  question: "نامِ #۱ و reserve قفل شود؟ (verdict دونفرهٔ A+C)"
  standing_proposal: "#1 Anar Soles · reserve Yalda Arch"
  coupled_to: "#9 (Persian/Sydney in public copy) — Yalda reserve پشتِ #9 قفل"
  options: [lock-anar-yalda, lock-anar-different-reserve, pick-non-persian(HouseRed/ArchAmber), defer-until-#9]
  hard_gated: "account creation / handle registration = owner only; agent never registers"
  default: defer-until-#9
```
