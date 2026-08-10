---
tags: [ofn, handoff, panels, scan, ui]
aliases: [اسکن پنل‌ها ۲۰۲۶-۰۸-۱۰]
updated: 2026-08-10
scan_session: panel-upgrade phase 1
---

# اسکن کامل چهار کنترل‌پنل — ۲۰۲۶-۰۸-۱۰

> شاهد زنده قبل از ارتقا. هر ویرایش UI باید این ماتریس را به‌روز کند.
**پیوندها:** [[AGENT-NEXT-PANEL-UPGRADE]] · [[INDEX]] · [[HANDOFF]] ·
[[MEGAPROMPT-MARKETING-PLATFORM-INTEGRATION]]

---

## وضعیت سرویس هنگام اسکن (زنده)

```
HEAD          450d685 (docs) ← d140756 (connector infra)
pytest        1657 collected · 1652 passed · 5 skipped
سرویس‌ها       ofn · hypno-fugu-mini · cloudflared  → هر سه active
پورت‌ها        panel:8794 · ziman:8791 · lead:8792 · studio:8793  → همه 200
sabaapp       200
گیت‌ها         secret_rotation 🔒 · partner_precondition 🔒 · miner_isolation 🔒
WIRE          outbound خاموش · email/publish در env ولی کد Python نمی‌خواند
```

---

## ۱) panel.html — مالک (آری)

**عنوان:** ارگانیسم — کنترل پنل آری · **پورت:** ۸۷۹۴ · **دامنه:** panel.master-painting.com · **بایت سرو‌شده:** ۹۶۲۲۰

### بخش‌های موجود (۱۱ بخش اصلی)

| # | بخش (h2) | id کلیدی | API | وضعیت |
|---|---|---|---|---|
| ۱ | توقف اضطراری / بنر kill | `killBtn` `killBanner` `killReleaseRow` | `owner/kill` `owner/kill/release` | ✅ سالم |
| ۲ | نقاشی ساختمان — لید و مارکتینگ | `paintDesk` `paintBody` `paintTabs` | `owner/painting/dashboard` + ۱۱ endpoint | ✅ سالم (۵ تب) |
| ۳ | صف تصمیم | `cnt` `stale` `q` `qmemo` | `queue` | ✅ سالم |
| ۴ | قلب — انرژی Fugu | `vital` `vitaltx` `brainline` | `owner/brain` | ✅ سالم |
| ۵ | بوت — چک‌ها | `bootchip` | (از snapshot) | ✅ سالم |
| ۶ | سلامت برد — زنده | `metricsBody` `metricsSync` `unmeasured` | `owner/metrics` | ✅ سالم |
| ۷ | سیستم عصبی | `nerve` | (از snapshot) | ✅ سالم |
| ۸ | دریچه‌ها | `valves` `flows` | (از snapshot) | ✅ سالم |
| ۹ | درِ خروج — outbox | `outbox` `outboxChip` | (از snapshot) | ✅ سالم |
| ۱۰ | زنجیرهٔ لجر | `chain` `chainChip` | `owner/ledger/summary` | ✅ سالم |
| ۱۱ | سطوح | `surfaces` `surfChip` | (از snapshot) | ✅ سالم |

### شکاف نسبت به بک‌اند (d140756)

| بخش UI | وضعیت | اقدام |
|---|---|---|
| صندوق ورودی وب‌هوک / وضعیت کانال‌ها | ❌ غایب ولی بک‌اند هست | **اضافه کن** — کارت تازه |
| سلامت اتصال‌ها (connector health) | ❌ غایب ولی بک‌اند هست | **اضافه کن** — کارت تازه |
| پیوند inbox held ↔ outbox held | ❌ غایب | **اضافه کن** — کنار outbox |
| جست‌وجوی correlation ID | ❌ غایب | **اضافه کن** — فیلد اختیاری |
| endpoint observability | ❌ غایب | **ساخته شود** فاز ۲ |

### ممنوع‌حذف (حذف هر کدام = شکست مأموریت)

1. توقف اضطراری (killBtn + killBanner + release)
2. میز نقاشی و همهٔ ۵ تب آن
3. صف تصمیم (cnt/stale/q)
4. داشبورد سلامت برد (metrics)
5. درِ خروج outbox

---

## ۲) lead.html — لید نقاشی (عباس)

**عنوان:** لید نقاشی · **پورت:** ۸۷۹۲ · **دامنه:** lead.master-painting.com · **بایت سرو‌شده:** ۳۶۰۶۸

### بخش‌های موجود

| # | بخش | id کلیدی | API | وضعیت |
|---|---|---|---|---|
| ۱ | سؤال‌های کرنل | `state` `live` | `questions` `answers` `status` | ✅ سالم |
| ۲ | CRM پارتنر | `leadcrm` `leadlist` `hnm` | `painting/dashboard` `painting/leads` | ✅ سالم (روی boot) |
| ۳ | جستجو/فیلتر | `leadlist` | `painting/leads?q=&status=` | ✅ سالم |
| ۴ | جواب لید | sheet | `painting/leads/{id}/reply` | ✅ سالم |
| ۵ | قیمت لید | sheet | `painting/leads/{id}/quote` | ✅ سالم |
| ۶ | تغییر وضعیت | `<select>` | `painting/leads/{id}` PATCH | ✅ سالم |
| ۷ | ثبت لید دستی | | `painting/leads` POST | ✅ سالم |

### شکاف / بهبود

| بخش UI | وضعیت | اقدام |
|---|---|---|
| امتیاز/اولویت روی کارت لید | ❌ غایب ولی `score_json` هست | **اضافه کن** — برچسب انسانی |
| empty-state وقتی لیست خالی است | ⚠️ ناقص | **بهبود** — متن گرم + دکمه ثبت |
| پیام خطای reply/quote گرم | ⚠️ ناقص | **بهبود** |
| هدر آمار بدون عدد دروغ | ✅ سالم | حفظ |

### ممنوع‌حذف

1. CRM روی boot (`refreshLeadCrm`)
2. جستجو/فیلتر
3. جواب/قیمت (sheet)
4. ثبت لید دستی
5. سؤال‌های کرنل

---

## ۳) studio.html — استودیو (سبا)

**عنوان:** چیدمان · **پورت:** ۸۷۹۳ · **دامنه:** studio.master-painting.com + `/sabaapp` · **بایت سرو‌شده:** ۱۲۵۱۲۷

### بخش‌های موجود

| # | بخش | id کلیدی | API | وضعیت |
|---|---|---|---|---|
| ۱ | ناوبری ۵ نما | `view-today` `view-archive` `view-gallery` `view-business` `view-marketing` | — | ✅ سالم |
| ۲ | امروز / آرشیو | `front` `behind` `startarc` `arc-*` | `shell/boot` `status` | ✅ سالم |
| ۳ | گالری | `grid` `gallery-empty` `tagpanel` `tray` | `studio/gallery` `studio/albums` | ✅ سالم |
| ۴ | آپلود + حذف | `add-photo-*` `delete-photo` `delete-album` | `studio/media` | ✅ سالم |
| ۵ | دستیار چت | `assistant-card` `assistant-log` `assistant-input` | `studio/assistant/*` | ✅ سالم |
| ۶ | مارکتینگ بورد | `mkt-*` (۲۰+ id) | `studio/board` `studio/marketing` | ✅ سالم |
| ۷ | انتشار | `go-publish` | `studio/drafts` | ✅ سالم |
| ۸ | shell/boot | | `shell/boot` | ✅ سالم |

### شکاف / بهبود

| بخش UI | وضعیت | اقدام |
|---|---|---|
| `tg().setHeaderColor` / `setBackgroundColor` | ❌ غایب | **اضافه کن** |
| خلاصهٔ وضعیت انتشار گرم | ⚠️ ناقص | **ادغام** از board/status |
| empty-state گرم‌تر | ⚠️ ناقص | **بهبود** بدون حذف دکمه |
| async بدون `.catch` | ⚠️ ممکن | **بررسی** |

### ممنوع‌حذف

1. آرشیو (view-archive + arc flow)
2. گالری + آپلود + حذف تک‌عکس
3. چت دستیار
4. marketing خواندنی
5. shell/boot

---

## ۴) ziman.html — زیمان (ملیحه)

**عنوان:** زیمان · **پورت:** ۸۷۹۱ · **دامنه:** ziman.master-painting.com · **بایت سرو‌شده:** ۵۷۶۵۵

### بخش‌های موجود

| # | بخش | id کلیدی | API | وضعیت |
|---|---|---|---|---|
| ۱ | سه صفحه اصلی | `s1` `s2` `s3` | — | ✅ سالم |
| ۲ | فرم قطعه | `live` | `products` POST | ✅ سالم |
| ۳ | قفسه محصولات | `pieces` | `products` GET | ✅ سالم |
| ۴ | سؤال‌های کرنل | `state` | `questions` `answers` | ✅ سالم |
| ۵ | عکس قطعه | `.ph` `pick()` | `products/{slug}/photo` | ✅ سالم |
| ۶ | toLatinDigits | (تابع ۶۷۳) | — | ✅ سالم |

### شکاف / بهبود

| بخش UI | وضعیت | اقدام |
|---|---|---|
| اسم قبل از auth | ✅ غایب (ملیحه نیست) | حفظ |
| empty-state قفسه خالی | ⚠️ ناقص | **بهبود** — کنش روی همان صفحه |
| متن گرم‌تر | ⚠️ polish | **بهبود** بدون تغییر معنا |

### ممنوع‌حذف

1. فرم قطعه (live)
2. قفسه محصولات (pieces)
3. سؤال‌های کرنل
4. عکس قطعه + toLatinDigits
5. سه صفحه اصلی (s1/s2/s3)

---

## خلاصه شکاف‌ها — اولویت‌بندی

| اولویت | پنل | شکاف | فاز |
|---|---|---|---|
| 🔴 بالا | panel | endpoint observability لازم | ۲ |
| 🔴 بالا | panel | کارت صندوق ورودی + سلامت اتصال | ۳ |
| 🟡 متوسط | lead | اولویت انسانی روی کارت لید | ۴ |
| 🟡 متوسط | studio | رنگ هدر تلگرام + وضعیت انتشار | ۵ |
| 🟢 پایین | ziman | empty-state قفسه + polish | ۶ |

---

## وضعیت بعد از ارتقا — ۲۰۲۶-۰۸-۱۰

### آنچه اضافه/ادغام شد

| پنل | فاز | چه شد | تأیید |
|---|---|---|---|
| panel | ۲ | `GET /api/v1/owner/observability` — counts per-tenant، no-store، owner-only | ۱۰ تست ✅ |
| panel | ۳ | کارت «صندوق ورودی — کانال‌ها» بعد از درِ خروج | curl ✅ |
| lead | ۴ | برچسب اولویت از `score_detail` + empty-state گرم | curl ✅ |
| studio | ۵ | `setHeaderColor`/`setBackgroundColor` در `shell()` | curl ✅ |
| ziman | ۶ | empty-state قفسه خالی گرم‌تر | curl ✅ |

### ممنوع‌حذف — همه سر جایشان (تأیید)

**panel.html:** kill · صف تصمیم · میز نقاشی · metrics · outbox · لجر · سطوح ✅
**lead.html:** CRM · جستجو/فیلتر · جواب/قیمت · ثبت لید · سؤال‌ها ✅
**studio.html:** آرشیو · گالری · چت · آپلود · مارکتینگ · shell/boot ✅
**ziman.html:** فرم قطعه · قفسه · سؤال‌ها · عکس · toLatinDigits ✅

### صحت نهایی

```
pytest      1662 passed · 5 skipped
boot        OK — 29 checks
سرویس‌ها     ofn active · پنج مسیر ۲۰۰ · sabaapp ۲۰۰
outbox      تغییر نکرد
WIRE/gates  دست‌نخورده
```

