---
type: prompt
status: done
tags: [relationships, knowledge-graph, vault]
created: 2026-07-04
updated: 2026-07-04
---

# Prompt — کشف روابط Vault (Relationship Discovery)

> **نحوه استفاده:** کل بلوک زیر را به‌عنوان پیام اول یک جلسه تازه Cowork/Claude Code روی ریشه vault بده. کار کاملاً داخلی است (بدون web search). حالت پیش‌فرض **REPORT-ONLY** است: هیچ نوت موجودی ویرایش نمی‌شود؛ خروجی فقط یک گزارش جدید در `00 - Inbox` + یک خط لینک در HANDOFF.
> **⚠️ امنیت:** این پرامپت عمداً بدون secret و هویت نوشته شده — چیزی به آن اضافه نکن.
> **منشأ:** ساخته‌شده از تحلیل کامل ۱۸ جلسه Cowork این پروژه (2026-07-04). جدول seed داخل پرامپت، روابطی است که از چت‌ها استخراج شد و اجراکننده باید داخل vault راستی‌آزمایی و تکمیلشان کند.

```text
# ماموریت: کشف روابط پنهان Vault (Relationship Discovery)

تو «کارتوگراف دانش» این vault ابسیدین هستی. ماموریت: کشف روابطی که در نوت‌ها هست اما هنوز لینک/ثبت نشده — بین پروژه‌ها، تصمیم‌ها، گزارش‌ها، کد، مفاهیم و اشخاص — و تحویل یک نقشه روابط مستند با evidence. تو فقط کشف و پیشنهاد می‌کنی؛ اعمال لینک‌ها با verdict آری است.

## فاز ۰ — Preflight (الزامی، به همین ترتیب)
1. بخوان: `_PROJECT_INSTRUCTIONS.md` → `CLAUDE.md` → `01 - Dashboard/HANDOFF.md` → `01 - Dashboard/Home.md`.
2. چک گیت: اگر ردیف‌های CRITICAL در ROTATION_CHECKLIST هنوز باز است → MODE=REPORT-ONLY (پیش‌فرض). حتی اگر گیت باز بود، بدون تایید صریح آری در چت، MODE را عوض نکن.
3. محدوده منفی مطلق: `_Archive`، `_Duplicates`، `.git`، `09 - People`، `secrets-export/`، هر `wallet*`/`.env`/فایل کلید (از جمله `Mining/Mining-1`) — نه باز کن، نه echo. اگر به secret برخوردی: فقط «مسیر» را در بخش security-flags ثبت کن و رد شو.
4. قاعده هویت: پروژه «اونلی فنز» خارج از پوشه خودش فقط «Project-F»؛ نام پارتنر هرگز در گزارش نیاید.
5. STOP: اگر فایل‌های بند ۱ خوانا نبودند → توقف و گزارش کوتاه.

## فاز ۱ — Inventory گراف موجود (baseline)
- با ripgrep همه wikilinkهای موجود را استخراج کن، مثلا:
  rg -o "\[\[[^\]]+\]\]" -g "*.md" --no-filename | sort | uniq -c | sort -rn
- بشمار: تعداد نوت per پوشه، لینک‌های موجود، نوت‌های orphan (بدون هیچ لینک ورودی/خروجی)، هاب‌های فعلی.
- نوت‌های حجیم را full-read نکن؛ فقط اسکن هدفمند با rg (پرهیز از سوزاندن کانتکست).

## فاز ۲ — استخراج موجودیت‌ها (Entity Extraction)
ترتیب اولویت خواندن: همه PROJECT.md ها → DECISIONS و BACKLOG و GAPS (architect) → گزارش‌ها و پرامپت‌های `00 - Inbox` → ایندکس‌ها و نوت‌های کلیدی `07 - Knowledge` → ARCHITECT_CHARTER و SYSTEM_MAP و ECOSYSTEM (`06 - Architecture Maps`).
انواع موجودیت: پروژه، شخص (فقط نام مجاز/مستعار)، ابزار/سرویس، سخت‌افزار، تصمیم (D-xx / O-xx / BACKLOG-xx / GAP-x)، مفهوم، فایل/ریپوی کد، سند compliance (ATO, Spam Act, DNCR, …).
برای هر نوت epistemic_status را ثبت کن — نوت‌های fiction-canon جدا پرچم بخورند.

## فاز ۳ — استنتاج یال‌ها (Edge Inference)
هر رابطه یک ردیف با این ستون‌ها: از | به | نوع | evidence (مسیر فایل + نقل‌قول ≤۱ خط) | اطمینان [FACT]/[EST]/[SPEC] | وضعیت (already-linked / new-discovery).
تایپولوژی یال‌ها (۱۲ نوع):
1. blocked-by / depends-on (وابستگی و گیت)
2. budget-governed-by (تصمیم بودجه → پروژه)
3. implements (نوت طراحی → کد/سیستم واقعی)
4. evidences (گزارش → ادعا در PROJECT.md/blueprint)
5. contradicts (دو منبع ناسازگار)
6. duplicates / near-duplicate (با تعیین canonical)
7. evolves-into (نسخه‌ها: v1→v2→v3)
8. bridges-fiction↔reality (پل داستان↔سیستم واقعی — الزاماً [SPEC] + پرچم فایروال)
9. shares-resource (سخت‌افزار/سرور/بات مشترک)
10. pending-injection (گزارش Inbox → PROJECT.md مقصد که هنوز تزریق نشده)
11. same-entity (یک شخص/ابزار/مفهوم در چند نوت با نام‌های متفاوت)
12. constrained-by (الزام قانونی/compliance → پروژه)

### جدول Seed (از تحلیل ۱۸ چت — اول اینها را در خود vault راستی‌آزمایی کن، بعد گسترش بده)
| # | از | به | نوع | نکته |
|---|---|---|---|---|
| 1 | ROTATION_CHECKLIST (۴ ردیف CRITICAL) | کل اکوسیستم + Phase 4 | blocked-by | گلوگاه یکتا؛ charter §Security Gate |
| 2 | DECISIONS D-25 (سقف AU$30) | Crypto-etoro scraper، langar bot، پرامپت‌های تحقیق | budget-governed-by | یک تصمیم، حداقل ۳ پروژه |
| 3 | Langar-zād (Fusion-World، fiction-canon) | Anchor Ledger / fusion-mvp | bridges-fiction↔reality | در ۳ جلسه مستقل ظاهر شد — [SPEC] |
| 4 | Report - Adversarial Review v3 | SYSTEM-BLUEPRINT-v3-proposal §6.5 | evidences | ۶ دلتا منتظر verdict آری |
| 5 | گزارش P2 (research-results Project-F) | گزارش P8 + research-track-BC | contradicts | برنامه X «ACC/ID-verification»: جعلی vs واقعی |
| 6 | Orange Pi 5 Pro | Mining + architect (watchdog/lease) | shares-resource | یک برد، دو پروژه |
| 7 | Cardew | چک‌لیست مجهول‌ها (Knowledge) + Report - Cardew | same-entity + evidences | نام کامل هنوز یافت‌نشد (Trove/BDM) |
| 8 | Report - Tax Map FY2025-26 | Accounting + Lead-نقاشی (خرید ابزار) | constrained-by | سقف instant asset write-off → $1,000 از 1 Jul 2026 |
| 9 | AiFarm-Lead (canonical) | AiFarm-Lead1/2 | duplicates | طبق قانون اساسی vault |
| 10 | یافته DNCR (business numbers مستثنا) | آزمایش SEGMENT-DISCOVERY نقاشی + bot کاریابی | constrained-by | cold-call به builder/strata مجاز شد |
| 11 | همه `Report - *` در Inbox | PROJECT.md پروژه مربوطه | pending-injection | triage بعد از گیت |
| 12 | BLUEPRINT v1 → v2 (فعال) → v3-proposal | — | evolves-into | v2 فعال، v3 فقط proposal |
| 13 | Accounting | پروژه‌های درآمدی | depends-on | «پیش‌نیاز کارهای بزرگ» |

## فاز ۴ — تحلیل گراف
- هاب‌ها (بیشترین degree)، جزیره‌ها/orphanها، حلقه‌های وابستگی، single-point-of-failure ها.
- شکاف‌ها: ۲۰ لینک پیشنهادیِ پرارزش، رتبه‌بندی‌شده بر اساس ارزش عملی (نه صرفاً شباهت واژگانی).
- تناقض‌ها: هر contradicts + کوتاه‌ترین مسیر حل (چه چیزی باید verify شود، کجا).

## فاز ۵ — خروجی‌ها (همه در MODE=REPORT-ONLY)
1. `00 - Inbox/Report - Vault Relationship Map <تاریخ امروز>.md` شامل:
   - جدول کامل یال‌ها (ستون‌های فاز ۳)
   - متریک‌ها: تعداد نوت/لینک موجود/orphan/کشف جدید
   - نمودار Mermaid سطح ۱ (پروژه‌ها و گیت‌ها) + حداکثر ۳ زیرنقشه پرتراکم — مقصد نهایی پیشنهادی: `06 - Architecture Maps` کنار SYSTEM_MAP (فعلاً داخل گزارش بماند)
   - بخش «Proposed Wikilink Diff»: برای هر لینک پیشنهادی، فایل هدف + خط دقیق قابل‌افزودن زیر `## Related` — **اعمال نکن**
   - بخش security-flags (فقط مسیرها)
   - بخش تناقض‌ها + مسیر حل
2. یک خط wikilink به این گزارش در HANDOFF §کانتکست (تنها ویرایش مجاز خارج از Inbox).
3. frontmatter گزارش را schema-compliant بساز (مطابق `06 - Architecture Maps/Property Schema.md`).

## معیار پذیرش
- صفر یال بدون evidence؛ صفر secret در خروجی؛ تفکیک new-discovery از already-linked.
- حداقل ۱۵ کشف جدید معنادار، یا توضیح صریح چرا کمتر شد.
- هر یال fiction↔reality دارای [SPEC] و پرچم فایروال (داستان هرگز مبنای تصمیم واقعی نیست).
- فارسی با حفظ اصطلاحات انگلیسی؛ جدول‌ها مرتب.

## پایان جلسه
هر دو اسکریپت `04 - Architect System/scripts/` (find_broken_links.py و validate_frontmatter.py) را اجرا و نتیجه را گزارش کن — ۵۵ خطای پیش‌موجود schema-drift را از خطاهای جدید جدا کن. حذف/بازنویسی هیچ فایلی مجاز نیست.
```
