---
type: reference
status: active
project: "[[04 - Architect System/architect/PROJECT]]"
tags: [design, sync, obsidian, ops]
created: 2026-07-03
updated: 2026-07-03
---

# OBSIDIAN-SYNC — سینک vault بین لپ‌تاپ، گوشی و VPS

> طراحی درخواست اپراتور (2026-07-03). ثبت تصمیم: [[DECISIONS]] D-29. اقدام‌ها: [[BACKLOG]] #23–#24. قید حاکم: منشور §۶ — دادهٔ شخصی به VPS نمی‌رود (O-04).

## ⛔ قانون ترتیب (غیرقابل مذاکره)

**تا بسته شدن BACKLOG-01 (چرخش کلیدهای نشت‌کرده + خروج کامل secrets از درخت vault) هیچ سینک ابری/دستگاهی فعال نمی‌شود.** سینکِ vault آلوده = تکثیر نشت روی هر دستگاه و هر سرور واسط. `secrets-export/` قبلاً از `04 - Architect System` خارج شده — قبل از فعال‌سازی سینک، با `gitleaks`/جستجوی دستی تأیید کن هیچ secret دیگری در درخت نیست.

## توپولوژی هدف — سه ضلع، دو مکانیزم جدا

```
گوشی 📱 ←—— Obsidian Sync (E2E) ——→ 💻 لپ‌تاپ (master) ←—— git pull (یک‌طرفه) ——— 🖥 VPS
                کل vault منهای exclusions              فقط پوشهٔ agent-outbox
```

1. **لپ‌تاپ = master.** ریشهٔ واقعی vault = پوشهٔ `backup` (طبق `ROOT` اسکریپت‌های validation و wikilink‌هایی که به پوشهٔ «03 - Projects» اشاره می‌کنند)، نه `architect` به‌تنهایی. ⚠️ `architect/.obsidian` تودرتو = باقی‌ماندهٔ config قدیمی — کاندید پاکسازی (فقط تنظیمات است، نه محتوا؛ vault تودرتو رفتار سینک را غیرقابل‌پیش‌بینی می‌کند).
2. **گوشی ↔ لپ‌تاپ:** کل vault (منهای exclusions پایین) با ابزار انتخابی جدول زیر.
3. **VPS → لپ‌تاپ:** کل vault **هرگز** روی VPS نمی‌رود (منشور §۶، O-04: HRV، هیپنوتیزم، Project-F). بات روی VPS خروجی‌هایش (گزارش، نوت تحقیق) را در repo خصوصی `agent-outbox` می‌نویسد (append-only، markdown + frontmatter) → لپ‌تاپ ساعتی pull می‌کند داخل `04 - Architect System/architect/05-Agent-Outbox/`. جهت معکوس (لپ‌تاپ→VPS) فقط فایل‌های دستورالعمل عمومی (پرامپت/skill بدون دادهٔ شخصی) از همان مسیر repo + deploy gate (D-20).
4. **فاز MVP (D-12، بات روی لپ‌تاپ):** ضلع VPS اصلاً وجود ندارد — بات مستقیم در پوشهٔ vault می‌نویسد؛ فقط سینک گوشی لازم است.

## Exclusions — در هر ابزاری اجباری

| مسیر | چرا |
|---|---|
| `architect/_code/**` | ریپوهای git + **`langar.db` زنده — سینک SQLite در حال نوشتن = ریسک corruption** + حجم |
| `.obsidian/workspace*`، cache پلاگین‌ها | state محلی هر دستگاه؛ منبع اصلی conflict |
| `secrets-export/**` (هرجای درخت) | هرگز روی هیچ کانال سینک |
| `_meta/*.zip`، `.git/**` | بکاپ/تاریخچه — جای سینک نیست |

## مقایسهٔ ابزارها (گوشی ↔ لپ‌تاپ)

| معیار | **Obsidian Sync** | **Syncthing(-Fork)** | **obsidian-git** | iCloud/OneDrive |
|---|---|---|---|---|
| هزینه | $4/ماه (سالانه؛ $5 ماهانه) — پلن واحد، 1GB، E2E | رایگان | رایگان (repo private) | ~رایگان |
| موبایل | iOS + Android رسمی | ⚠️ اپ رسمی اندروید discontinued؛ **Syncthing-Fork** فعال (F-Droid)؛ iOS ندارد (Möbius پولی) | ⛔ روی موبایل unstable (isomorphic-git) — توصیه نمی‌شود | دارد ولی خرابی شناخته‌شده با vault |
| پیچیدگی/نگهداری (P7) | ~صفر | متوسط (نصب دو سمت، .stignore، fork ثالث) | بالا در موبایل | کم ولی conflict مبهم |
| امنیت | E2E encrypted | P2P، بدون cloud (بهترین حریم) | بستگی به repo host | بدون E2E واقعی |
| Lock-in | کم — فایل‌ها markdown محلی می‌مانند | صفر | صفر | متوسط |
| Conflict برای اپراتور تک‌نفره | merge خودکار + نسخه‌ها (۱ ماه history) | فایل‌های `.sync-conflict` دستی | merge دستی git | بدترین |
| **جمع (۱–۱۰ برای این use-case)** | **9** | 7 (اندروید) / 4 (iOS) | 3 | 4 |

**توصیه (D-29):** ستون شخصی = **Obsidian Sync** — بالاترین ROI برای اپراتور تک‌نفره (P7: بودجهٔ پیچیدگی خرج core شود، نه ابزار سینک)؛ زیر ستون اشتراک فلت D-25 هم می‌گنجد. جایگزین رایگان اگر گوشی اندروید است و هزینه مهم شد: Syncthing-Fork با `.stignore`. ضلع VPS در هر دو حالت **git است، نه sync دوطرفه**.

## گام‌های راه‌اندازی

**فاز الف — الان (بعد از BACKLOG-01):**
1. `gitleaks detect` روی کل درخت vault → صفر یافته.
2. حذف `architect/.obsidian` تودرتو (بعد از یک بکاپ zip).
3. فعال‌سازی Obsidian Sync روی لپ‌تاپ: ساخت remote vault، انتخاب Selective sync و **حذف exclusions جدول بالا**؛ چک حجم <1GB.
4. نصب Obsidian روی گوشی → اتصال به همان remote vault → تست دوطرفه با یک نوت.

**فاز ب — همراه استقرار VPS (v1-فاز، BACKLOG-24):**
5. ساخت repo خصوصی `agent-outbox` (private از روز اول + history پاک — D-27).
6. بات: `write_note(path, frontmatter, body)` فقط داخل outbox؛ hook در deploy pipeline.
7. لپ‌تاپ: pull ساعتی (Scheduled Task ویندوز یا پلاگین obsidian-git فقط-دسکتاپ) به `05-Agent-Outbox/`.
8. تست: نوت تولیدی VPS ظرف ≤۱ ساعت روی گوشی دیده شود؛ هیچ فایلی از vault به VPS نرفته باشد (بازرسی دستی).

## منابع خارجی (2026-07-03)

- [Obsidian Pricing](https://obsidian.md/pricing) — پلن واحد Sync: $4/ماه سالانه، $5 ماهانه، 1GB، E2E
- [Syncthing Android app discontinued — Forum](https://forum.syncthing.net/t/what-would-it-require-to-get-official-android-support/26002) و وضعیت [Syncthing-Fork](https://forum.syncthing.net/t/does-anyone-know-why-syncthing-fork-is-no-longer-available-on-github/25661/251)
- [obsidian-git — GitHub](https://github.com/Vinzent03/obsidian-git) — «Git implementation on mobile is very unstable»
