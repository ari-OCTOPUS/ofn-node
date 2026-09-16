---
type: rulings-executed-receipt
created: 2026-09-02T12:30Z
rulings_source: AskUserQuestion answered by owner 12:28–12:29Z (V1=روشن کن · گام۳=الان بکش · V3=بسته را آماده کن)
executor: ZCode session (ari322 gh) + ssh board138
files_i_merged=none
---

# اجرای سه رأی مالک — همه با تأیید زنده

## ۱) V1 — enforce_admins روشن شد ✓

- اولین تلاش (PUT زیرمنبع) → 404 (همان خطای شناخته‌شده). دومین تلاش (GET-بازگردانی کامل) → 422 schema. سومین: بدنهٔ تمیز PUT شد و **پذیرفته شد**.
- تأیید زنده پس از اعمال: `enforce_admins=true · checks=[hygiene, test (ubuntu-latest), test (windows-latest), require-independent-approval] · required_approving_review_count=1 · dismiss_stale_reviews=true · require_code_owner_reviews=true · allow_force_pushes=false · allow_deletions=false`
- شفافیت: وضعیت قبلی `require_code_owner_reviews` جداگانه ثبت نشده بود؛ مقدار فعلی true است و با طراحی CODEOWNERS سازگار.
- اثر: از این پس ادمین‌ها هم شامل حمایت main می‌شوند؛ تکرار الگوی «رأی+مرج از یک حساب، بدون الهه» مثل موج ۱۲:۱۷Z دیگر از مسیر ادمین ممکن نیست.

## ۲) گام ۳ — board138 به main کشیده شد ✓ (رویهٔ شش‌خطی مصوب)

```
BLOCKED_DIRTY_BOARD=no  (فقط ۴ آیتم untracked: data/octopus-alerts.jsonl, data/state/, ofn/agi2027_runtime/, web/cockpit-v2/data/ — صفر فایل tracked-تغییریافته)
BOARD_HEAD_BEFORE=3cf9fa1  →  BOARD_HEAD=87b5ed09234db305e405540de95c4e9a34e212df  (pull --ff-only تمیز، 4 نسل)
SELF_MODEL_SHA256=7cc4e5b10729d2776087ff5da627f8edc3f6e85ceca837b92b13e8d3808c5902
SELF_MODEL_SEMANTIC_DIGEST=18777f723728eab6dead3da0c558f765427b3b2eba785e12bf36cbfcccf8fe5f
SELF_MODEL_STATUS=unverifiable (صادق: 5 absent / 14 healthy / 0 failed — درمان همچنان ممنوع تا رأی V2)
SELF_MODEL_GENERATED_AT=2026-09-02T12:27:23Z · commit=87b5ed09 ✓
VIEWER_STATUS=data present (web/cockpit-v2/data/self-model.json روی HEAD تازه)
SYSTEM-SELF-MODEL.json=absent (مطابق رأی REV-3 بند ۴ بازتولید نشد — producer با --output فقط مسیر وب را نوشت)
هیچ restart/kill/systemd change انجام نشد؛ سه یونیت failed دست‌نخورده ماندند
```

## ۳) V3 — بستهٔ buy.nsw آماده شد ✓

- سند: `BUYNWS-SUPPLIER-PACK-2026-09-02.md` (همان پوشه) — قدم‌های Supplier Hub → SCM0256 (رستهٔ Painting & Decorating درون طرح General Construction ≤ $1M) + دو PDF رسمی (Applicant Guidelines آوریل ۲۰۲۵، Scheme Conditions اکتبر ۲۰۲۵) + چک‌لیست مدارک + حلقهٔ اتصال به DET.
- اصلاح دقیق: SCM0256 طرح «نقاشی» جداگانه نیست؛ نقاشی رسته‌ای درون آن است.
- ثبت‌نام با دست مالک؛ ایجنت هیچ فرمی پر/ارسال نکرد.

## بازمانده‌ها

- V2 (درمان ۸۷۷x/۸۷۹x) هنوز باز — پیشنهاد اورکستراتور: اصلاح کانفیگ سنسور؛ منتظر رأی.
- مادهٔ ۱۰ (کدنویسی تلگرام/کنترل‌پنل) باز.
- قیمت QT-20260902-001، فیلدهای DET، توکن HF — فقط از دست مالک.
- صف review: #84/#73/#67/#66/#65 منتظر انسان مستقل (الان با enforce_admins، مسیر میان‌بُر ادمین بسته است).
