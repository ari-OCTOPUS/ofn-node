# OCTOPUS-OBSIDIAN-NO-LOSS-MIGRATION-PLAN — طرح بدون‌اتلاف
# mission: OCTOPUS-UNIFIED-RECON-AND-VAULT-CANONICALIZATION-20260917 · وضعیت: PLAN ONLY (هیچ move اجرا نشده)

## اصول غیرقابل مذاکره
حذف ممنوع · overwrite ممنوع · هر move با ردیف `old_path → new_path → sha256_before → sha256_after → links_before → links_after` · mismatch = HALT فوری · rollback هر batch قبل از اجرا روی کپی تمرین شده باشد.

## وضعیت گیت‌ها (پایان این نشست)

| گیت | تعریف | وضعیت | شاهد |
|---|---|---|---|
| G0 | inventory کامل | **OPEN (جزئی)** | census کامل نشست جاری در حال اتمام؛ شمارش خام/کسرشده در CENSUS-SUMMARY.json |
| G1 | snapshot verify | **PENDING** | baseline dirty=۱۴۶۲ ثبت شد (vault-status-baseline.txt)؛ snapshot کامل نیاز به توقف sync کلاینت‌ها دارد (مالک) |
| G2 | hash manifest verify | **PENDING** | VAULT-HASH-MANIFEST.sha256 تولید شد؛ verify دوطرفه باید در نشست بعدی روی همان مانیفست اجرا شود |
| G3 | بازبینی مالکِ moveهای پیشنهادی | **PENDING** | این سند + کارت ۸ |
| G4 | dry-run بدون overwrite | PENDING | — |
| G5 | rollback روی کپی تمرین | PENDING | — |
| G6 | link-rewrite روی کپی تمرین | PENDING | — |
| G7 | GO صریح مالک | PENDING | — |

**نتیجه: هیچ migration اجرا نشد و نبود.**

## wave-1 (تنها چیزی که همین نشست ساخته — افزاینده-فقط)
فایل‌های جدید در `00-HOME/`، `03-REPOSITORIES/`، `04-BUSINESS-LEGS/`، `90-MIRRORS/`:
`OCTOPUS-HOME.md` · `REPO-MAP.md` · `CURRENT-TRUTH-INDEX.md` (پوینتر به دو نسخهٔ زنده — عمداً CURRENT-TRUTH سوم ساخته نشد) · `OPEN-DECISIONS.md` · `SUPERSESSION-INDEX.md` · ۴ MOC ریپو · ۳ MOC business leg · `MIRRORS-POINTER.md`.
**هیچ فایل موجودی move/rename/edit نشد.**

## ساختار هدف (طبق مأموریت — فقط پس از G7)
```text
F:\backup\00-HOME · 01-GOVERNANCE · 02-ARCHITECTURE · 03-REPOSITORIES{ofn-node,Armin,langar,vbaa-patches}
· 04-BUSINESS-LEGS{painting,ziman,studio} · 05-RUNTIME-NODES{board-138,board-180,board-182}
· 06-EVIDENCE · 07-INCIDENTS · 08-RESEARCH · 09-INBOX · 90-MIRRORS · 99-ARCHIVE
```

## قواعد batch (پس از G7)
- حداکثر ۵۰ artifact در هر batch؛ شمارش فایل/byte/hash/link قبل و بعد هر batch.
- move اتمیک در همان volume؛ cross-volume = copy+verify اول، مبدأ به pointer تبدیل می‌شود (delete فقط با حکم جداگانه).
- conflict → `09-INBOX/CONFLICTS`؛ encoding-مشکوک → quarantine manifest.
- لمس‌نکردنی‌ها: `.obsidian/workspace*.json`، plugin state، دیتابیس‌ها، فایل‌های رمز، key material، repoهای داخل والت (به‌عنوان فایل عادی move نشوند).
- بعد از هر batch: link graph + git status دوباره سنجیده شود.

## پذیرش نهایی
`DELETED=0 · OVERWRITTEN=0 · UNEXPLAINED_HASH_CHANGES=0 · NEW_BROKEN_LINKS=0 · UNMAPPED_MOVES=0 · SECRET_VALUES_IN_OUTPUT=0 · REMOTE_MUTATIONS=0 · ROLLBACK_REHEARSAL=PASS · COUNT_RECONCILIATION=PASS · BYTE_RECONCILIATION=PASS`
