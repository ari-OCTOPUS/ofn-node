# LINEAGE-MAP — آشتی سه تاریخچه (تأییدشده با GitHub API، 2026-08-31)

روش راستی‌آزمایی: `gh api` روی `ari-OCTOPUS/ofn-node` (compare/branches/commits) + git محلی. هیچ merge/force/rebase/حذفی اجرا نشده است.

## گرهٔ بنیادین

**`c1969bc` = `backup/board138-20260830`** — نیای مشترک تأییدشدهٔ هر سه مسیر گیت.
(R-13 ادعا کرده merge-base خط C نسبت به A صفر است؛ این ادعا فقط در سطح «دو repo متفاوت» درست است — والت Obsidian یک repository جدا با تاریخچهٔ بی‌ربط است. روی org، هر دو شاخهٔ surgery دارای `merge_base = c1969bc` هستند → نسخهٔ تجویزی OWNER-02 (export روی شاخهٔ هم‌تاریخچه) از قبل قابل‌اجراست.)

## A — main (منتشرشده، protected)

- HEAD: **`1960c364`** «H1: buy.nsw tender adapter (fixture-driven, read-only) (#10)»
- ۵ کامیت جلوتر از `c1969bc`:
  - `7442c2a` observation.v1 contract (#6)
  - `14ef298` observatory fixture scoring pipeline (#7)
  - `8d49815` disposable backup restore integrity (#8)
  - `c751455` repo reorg: agent context/prompts (#9)
  - `1960c36` H1 tender adapter (#10)
- دارد که B ندارد: تست‌های observatory/restore، `docs/octopus-rapid/`، workflowهای قدیمی، بازسازی docs ریشه.
- ندارد که B دارد: کل زنجیرهٔ Owner→Brain P0 و portability ویندوز.

## B — lineage برد (runtime مستقر)

- ریشه: `ebf8b7e8` (truth-record 20260828 + sync سه‌نودی) — فرزند `c1969bc` از مسیر تاریخچهٔ برد
- `work/owner-brain-p0-fix` = `ebf8b7e8 → e4f4d50 → d6051784 → 6974153 → 570c856` (سند runtime مستقر؛ board138 از آن اجرا می‌شود)
- `work/r1-portability` = `ebf8b7e8 → 4565624` (تک‌والد، تأییدشده)
- **PR #11**: شاخهٔ `integration/owner-brain-p0-plus-win-20260831`، HEAD **`26ed609`** (زنجیرهٔ بازسازی‌شدهٔ تمیز: `4565624 + 108cce5 + 06257f5 + 26ed609`)؛ `ahead 8 / behind 5` نسبت به main بر پایهٔ `c1969bc`؛ `mergeable: MERGEABLE`؛ ۱۵/۱۵ check سبز؛ ۳۲ فایل؛ تاریخچهٔ first-cut (`e11aae7`) دیگر روی سر شاخه نیست (فقط در `work/owner-brain-p0-fix` و fork).
- رابطه با A: **هم‌نیا با فاصلهٔ کم (8/5)** — نه تاریخچه‌های بیگانه.

## C — والت Obsidian → شاخه‌های export

- والت: `F:\backup` (repository جدا؛ merge-base با ofn-node در سطح repo صفر — همان که R-13 ثبت کرده)
- پل رسمی (تجویز OWNER-02، هر دو روی `c1969bc` سوارند):
  - `export/octopus-surgery-20260830` = `526613e` (ahead 1 / behind 5)
  - `export/octopus-surgery-20260830-193052` = `59ea2fb` (ahead 6 / behind 5)
- OWNER-01 BLOCKED سالم است: HEAD والت هرگز push/PR نشده ✓
- وضعیت انتقال: surgery file list هنوز به main منتقل نشده؛ تازه‌ترین export مقدم بر merge B است (behind=5).

## شاخه‌های نگه‌داری (موضوع Q4)

| گروه | شاخه‌ها | SHA |
|---|---|---|
| archive (1) | archive/board180-unprotected-20260830 | c6d6a47 |
| audit (3) | audit/cursor-20260828، audit/senior-auditor-20260828-138، audit/zcode-20260828 | d94c42c، f09681a، 678975b |
| backup (4) | backup/board138-20260830 (**= نیای مشترک c1969bc**)، board180، board182، hypno-fugu-mini | c1969bc، 28209ef، 294d51c، 0f22557 |
| chore (2) | untrack-evidence-inbox، untrack-runtime-artifacts | 836f7bb، db6b0ec |
| export (5) | observatory-fixture، octopus-surgery ×2، restore-drill، (سه اولیّ موضوع Q2) | fa2a4c1، 526613e، 59ea2fb، 805a0ba |

(جمع گروه‌های بالا ۱۵ است؛ عدد «۱۳» سند مالک احتمالاً بدون chore و یکی از exportها بوده — شمارش دقیق با SHA جایگزین شد.)

## ماتریس واگرایی (تأییدشده)

| مسیر | merge-base | ahead/behind |
|---|---|---|
| main ↔ integration (PR #11) | c1969bc | 8/5 |
| main ↔ export/octopus-surgery-20260830 | c1969bc | 1/5 |
| main ↔ export/octopus-surgery-20260830-193052 | c1969bc | 6/5 |
| والت ↔ هر شاخهٔ org | — (repo جدا؛ فقط از مسیر export) | n/a |

## پرسش‌های باز (Q1–Q6)

- Q1 merge PR #11؟ روش؟ → **پاسخ مالک: بله؛ ابتدا merge-commit (قفل شد توسط required_linear_history) → نهایی: Squash. PR #11 توسط خود مالک squash-merge شد: main = f77b68e7 «Owner-authorized squash (Q1)».**
- Q2 الگوی export/octopus-surgery-* رسمی باشد؟ → **پاسخ مالک: تأیید — الگوی موجود رسمی است؛ export بعدی از mainِ پس‌از-merge.**
- Q3 R-13؟ → **پاسخ مالک: بله، پس از merge. ثبت شد: R-13: BLOCKED → PARTIALLY_RECONCILED (B merged via PR #11 squash f77b68e7; vault export pending — الگوی surgery-* تأییدشده).**
- Q4 سرنوشت شاخه‌های نگه‌داری؟ → **پاسخ مالک: تگ + نگه‌داری. ۱۴ تگ archive/<name>-<sha7> ساخته شد (شامل تگ نیای مشترک c1969bc).**
- Q5 canonical؟ → **پاسخ مالک: main پس از merge. main = f77b68e7 (شامل کل P0 + portability؛ CONTROL_SCOPE تأیید شد). مرجع بعدی هر تغییر: PR به main.**
- Q6 محل نقشه؟ → **پاسخ مالک: docs/lineage روی main.** این فایل به همان مسیر ارسال شد (PR docs/lineage-map).

## ترتیب عملیات پیشنهادی (پیش از پاسخ Q1/Q5 هیچ merge ای ممنوع)

1. Q1+Q5 → merge PR #11 (پیشنهاد: merge-commit تا SHAهای runtime برد مثل `570c856` در تارخچهٔ main به‌عنوان نیا بمانند و dossier به آن‌ها استناد کند).
2. پس از merge: R-13 (با اجازهٔ Q3) + board در پنجرهٔ deploy بعدی از main ادغام/ff کند (main ۵ کامیت دارد که برد ندارد؛ هیچ فایلی دستی حذف نمی‌شود — reorg خود main مرجع است).
3. Q2 → شاخهٔ export تازه از mainِ پس‌از-merge فقط با فهرست فعلی surgery (۱۵۵ فایل)؛ در والت انتقال به `99-ARCHIVE`؛ HEAD والت هرگز push نمی‌شود.
4. Q4 → تگ `archive/<name>@<sha>` برای همهٔ شاخه‌های نگه‌داری؛ حذف شاخه فقط پس از تصمیم Q5.
5. Q6 → commit این نقشه به `docs/lineage/LINEAGE-MAP.md` + قاعدهٔ به‌روزرسانی: هر تغییر HEAD در همین فایل.


---

# به‌روزرسانی فصل 2026-09-01 (قاعدهٔ «هر تغییر HEAD همین‌جا ثبت شود»)

- main: `1960c364` → **`0a7afefebe3d62882ef33705dadfa45e5b99c62e`** — squash‌های مالک‌مجاز: PR #11 (owner→brain P0)، #12–#15 (docs)، #16 (S2b piece 1 پس از laneهای A/B/C روی شاخهٔ آن)، #18 (S6-D01..D05)، #22 (receiptهای backfill). CI روی main سبز.
- شاخهٔ runtime برد: `work/owner-brain-p0-fix @ 570c856` همچنان سند runtime مستقر (بدون تغییر؛ اکنون نیای main از مسیر squash).
- R-13: در والت به **PARTIALLY_RECONCILED** ارتقا یافت (Q3)؛ نیمهٔ باقی‌مانده = export فایل‌های surgery از main جدید (Q2 تصویب‌شده).
- PRهای #1–#4: CLOSED_SUPERSEDED با کامنت (lane E).
- بقا: ۱۴ تگ `archive/<name>-<sha>` بدون تغییر.
