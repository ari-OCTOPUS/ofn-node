# OCTOPUS INDEPENDENT VERIFIER KIT — 2026-08-21

بستهٔ آمادگی برای **مگاپرامپت ۱** (verification مستقل سر-به-سر) طبق فرمان مالک
`OCTOPUS-OWNER-ORDER-WAVE1-2026-08-21` (ثبت در `02-DECISIONS/`).

این بسته را **جلسهٔ verifier جدا** اجرا می‌کند — نه جلسهٔ پیاده‌ساز. خودِ بسته
چیزی را «تأییدشده» نمی‌کند؛ فقط بازتولید و اندازه‌گیری می‌کند و رأی را با هویتِ
اعلام‌شده ثبت می‌کند. جلسهٔ پیاده‌ساز فقط حالت `--preflight` دارد.

## هدهای مرجع

| نقش | commit | وضعیت بازتولید ۱۶۳ |
|---|---|---|
| implementation checkpoint | `fa38d16cca944a80396ae1e1a16c547ab3122f78` | — |
| evidence checkpoint (اصلی) | `d3013390d52aab2e61bd2578613aff7077f68742` | **شکست: ۱۶۲/۱۶۳** (closed-loop ۱۴/۱۵) — نقص یکپارچگی شواهد (فایلهای organs در commit نیستند) |
| **declared descendant (تعمیر)** | `cc267048075b0f64bd56c8ac59074d8a43233ae2` | **۱۶۳/۱۶۳ سبز** + side effect صفر (پیش-تأیید ۲۰۲۶-۰۸-۲۱) |
| ادعای فعلی | `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING` | — |

> ⚠️ یافتهٔ مهم: `d301339` بهتنهایی (درخت commitشدهٔ خالص) ۱۶۳/۱۶۳ را
> بازتولید نمیکند؛ شواهد قبلی در درخت زنده با فایلهای untracked اجرا شده بود.
> جزئیات: `PREFLIGHT-FINDINGS-2026-08-21.md`. هدف verification مستقل = هدِ
> تعمیر cc267048 (فرزند اعلامشدهٔ d301339).

## پروتکل اجرا (خلاصه — متن کامل در MEGAPROMPT-1.md)

1. **هویت/استقلال.** هویت و منشأ مخزن، پلتفرم، نسخهٔ Python، هش لاک‌های وابستگی،
   نام متغیرهای محیطی، و HEAD دقیق را ثبت کنید.
2. **نسب git.** `git log --oneline d301339 -10` و
   `git diff --stat fa38d16 d301339` — بسته به شواهد باید فقط فایل‌های شواهد
   (security lab) تفاوت داشته باشند.
3. **یکپارچگی شواهد.** بازمحاسبهٔ هش‌ها:
   - `06-EVIDENCE/OCTOPUS-SECURITY-LAB-2026-08-21/LAB-ARTIFACT-MANIFEST.json`
     (ده فایل، sha256 هریک)
   - بازبینی که هیچ فایل شواهدی در working tree کثیف/untracked نیست و به
     شواهد append-only دست‌نخورده است.
4. **بازرسی C3/C4** (کد): `_ops/telegram_center/tg_api.py` و
   `_ops/telegram_center/center.py` + `_ops/loops/` — نکته‌های مگاپرامپت ۱ را
   یکی‌یکی از کد اثبات کنید (attach_defer_queue پیش‌فرض OFF، کلید ۶۴-hex قطعی،
   retry_after بدون سقف، retry_not_before ماندگار، SenderBridge تک‌مالک،
   admission قبل از transport، mark قبل از send، 429→defer کامل،
   crash→UNCERTAIN_SEND_OUTCOME و بدون auto-resend، عدم import پل در Center زنده).
5. **بازرسی آزمایشگاه**: اسکیمه/حالت‌های مجاز/هش canonical/preregistration
   تغییرناپذیر/amendment/ledgerهای append-only/رد رکورد نامعتبر/۲۴ کارتِ seed
   (`_ops/state/test_cycle/prereg.jsonl` و owner_cards).
6. **بازتولید کامل سویییت (۱۶۳)** — هدف: هدِ تعمیر `cc267048…` (فرزند d301339؛
   چون d301339 بهتنهایی ۱۶۳ را بازتولید نمیکند — ببینید PREFLIGHT-FINDINGS):

```bash
# در worktree دقیقِ هدِ تعمیر:
git worktree add --detach <wt> cc267048075b0f64bd56c8ac59074d8a43233ae2
python -X utf8 06-EVIDENCE/OCTOPUS-INDEPENDENT-VERIFIER-KIT-2026-08-21/reproduce_suites.py \
    --worktree <wt> --head cc267048075b0f64bd56c8ac59074d8a43233ae2
```

   سویییت‌ها: security-c1-c4 (34) · lab-registry (8) · miniapp-regression (49) ·
   tg-api-regression (34) · durable-loop (15) · delivery-reconciliation (8) ·
   closed-loop (15) = **163**. خروجی: `PREFLIGHT-RECEIPTS.jsonl` +
   `PREFLIGHT-SUMMARY.json` (اینجا داخل بستهٔ خود verifier بازتولید می‌شود؛
   مقدارهای قبلی صرفاً مرجع‌اند).
   نکته: تمیزی مسیرهای تولید (state/hamemory/runtime/ledger) با snapshot
   فایل‌سیستمی سنجیده می‌شود (`os.walk`) نه `git status` — در این مخزن بزرگ
   git status چند دقیقه طول می‌کشد؛ همین دلیل کندیِ اجراهای قبلی بود.

7. **Side effect اجرای محلی** (هش حافظه/مینی‌اپ/سندلاگ قبل و بعد اجرای اختصاصی):

```bash
python -X utf8 measure_side_effects.py before --root F:\backup --out before.json
# ← اجرای سویییت اختصاصی در worktree
python -X utf8 measure_side_effects.py after  --root F:\backup --out after.json --before before.json
```

   هویت بایتی الزامی است؛ drift از ارگانیسم زنده باید طبقه‌بندی شود نه پنهان.
   مسیرها: `_ops/state/memory/research-ingest.jsonl` و `self-loop-ingest.jsonl`
   (حافظه)، `_ops/state/telegram/miniapp-hits.jsonl`، `_ops/state/tg-send-log.jsonl`.

8. **تست‌های خصمانه**: کلید تکراری، ری‌استارت پروسه، مرز ساعت، retry_after بدشکل،
   429 تکراری، خرابی صف، فراخوانی همزمان پل، کرش ارسال، کرش تأیید، دستکاری
   ledger، path traversal، نشت راز، kill switch غیرفعال، دسترسی شبکهٔ غیرمنتظره
   (همه در سویییت‌های fixture پوشش داده شده‌اند؛ verifier هرکدام را بازتولید می‌کند).

9. **رأی**:

```bash
# جلسهٔ جدا (غیر از پیاده‌ساز): statement بسازید که شامل این خط باشد:
#   INDEPENDENT_SESSION_ATTESTATION
# و هویت یکسان را نام ببرد، سپس:
python -X utf8 verdict.py --identity "<session-id>" \
    --statement <statement-file> --head cc267048075b0f64bd56c8ac59074d8a43233ae2
```

   خروجی: `INDEPENDENT-VERDICT.json`. PASS فقط وقتی همهٔ چک‌ها بازتولید شوند.
   `verifier_independent` بدون attestation هرگز true نمی‌شود.

## مرزها (از فرمان مالک)

- PASS ممکن است `WAVE1_CANARY_READY` را مجاز کند — هرگز به‌تنهایی ارسال زنده را.
- تعمیر در حین verification ممنوع؛ در صورت نیاز، FAIL + شاخهٔ تعمیر جدا.
- حذف/بازنویسی شواهد append-only ممنوع؛ خروجی‌های این بسته به همین پوشه نوشته می‌شوند.

## خروجی‌های الزامی رأی (طبق مگاپرامپت ۱)

`exact_verified_head` · `verifier_identity` · `independence_statement` ·
`suite_results` · `adversarial_results` · `side_effect_before_after_hashes` ·
`manifest_verification` · `live_capability_scan` · `failed_checks` ·
`verdict` · `authorized_next_state`
