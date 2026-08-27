# ROADMAP — کوتاه، اجرایی، پول‌محور

> Branch: `audit/zcode-20260828` · Date: 2026-08-28
> قواعد مالک: refactor بزرگ در NOW ممنوع؛ هر کار به درآمد/اطمینانِ مسیر درآمد/ایمنی وصل است؛ کارِ وصل‌نشده → LATER.

## NOW — ۷۲ ساعت (حداکثر ۵ کار)

| # | کار | تعریفِ انجام‌شده (DoD) | شاهد | وصل به |
|---|---|---|---|---|
| N1 | **Checkout E2E زیمان** — یک سفارش آزمایشی واقعی از مرورگر تا تأیید پرداخت (حالت تست مالک‌تأیید) | paid_order_count ≥ 1 در products.sqlite یا دلیلِ دقیقِ بلاک ثبت شود | ردیف orders + receipt + اسکرین‌شات/لاگ | اولین مسیر پول نصف‌بسته |
| N2 | **ارسالِ یک quote واقعی Painting** از outbox با تأیید مالک (فرستندهٔ موجود، ارسالِ یگانه با idem-key) | یک ارسال ثبت‌شده در send-log با receipt و پاسخِ مشتری پیگیری شود | outbox SENT + ledger | اولین اثر بیرونی درآمدی |
| N3 | **پچ‌های P0 ایمنی**: bind llama 180 به 127.0.0.1 + افزودن partner_precondition به base_closed_gates (+تست منفی) | ss فقط 127.0.0.1 نشان دهد؛ تست قرمز→سبز | diff + تست + ss-output | ایمنی |
| N4 | **بهداشت بازتولیدپذیری**: کامیت دسته‌ایِ 1149 فایل (تفکیک state/evidence) + رهانیدن governor.py از untracked | `git status` زیر ۱۰۰؛ شاخهٔ rescue با master merge-آماده | git log/diff | امکان SIG-IV و هر راستی‌آزمایی |
| N5 | **جلسهٔ راستی‌آزمای مستقل SIG-IV** (سشن جدا از سازنده) روی head جدید | INDEPENDENT_VERDICT.json با verifier_independent=true | فایل رأی | بازکردن گیت‌های معطل WAVE1 |

## NEXT — ۲ هفته (حداکثر ۷ کار)

| # | کار | DoD | وصل به |
|---|---|---|---|
| X1 | پول تسویه‌شدهٔ اول: bank payout زیمان → CSV reconcile → CONFIRMED (نه claimed) | یک ردیف confirmed در ledger پول | درآمد واقعی |
| X2 | حلقهٔ فرمان مالک: گسترش A18 از کاناری به مسیر owner-approved با سقف روزانه | فرمان تلگرام → اقدام → receipt بدون مداخلهٔ ایجنت خارجی | خودمختاری |
| X3 | مینی‌اپ عمومی: OCTOPUS_MINIAPP_URL + OCTOPUS_TG_MINIAPP=1 (مالک) + TTL/kill تست | دکمهٔ web_app از گوشی مالک باز شود | کانال کنترل |
| X4 | FF KYC clearance استودیو → آپلود 9 پک واترمارک‌شده | 9/9 روی FeetFinder | مسیر درآمد دوم |
| X5 | ofn-backup فعال روی 138 + receipt | سرویس active + فایل بکاپ verify شده | تاب‌آوری مسیر پول |
| X6 | بستن 16 شکستِ run_all (یا known-red مستند) | شمارش سبز/قرمز ثبت در TEST-COUNT | اطمینان |
| X7 | merge rescue→master + sync سه مخزن گیت‌هاب با وضعیت زنده (فقط additive) | germline lag < 1h؛ HEAD master = درخت زنده | بازتولیدپذیری |

## LATER — پس از اولین پول

- یکپارچه‌سازی سه‌مخزنی طبق طرح مالک: `octopus-contracts` (CognitiveEvent/GoalEnvelope/ActionIntent…) + event spine + inbox استاندارد — شاخهٔ feat/octopus-unified-spine؛ فاز اول فقط قرارداد+تست، بدون اقدام خارجی.
- تجزیهٔ center.py به interfaces/ (تنها با پروتکل duplication اثبات‌شده)؛ ادغام researcher×3 و constitution×2 و بانک سؤال×2 در langar.
- وصل قابلیت‌های خفته (conversation_hub، epistemic runtime، حافظهٔ معنایی) — هرکدام فقط وقتی به یکی از سه هدف NOW/NEXT وصل شوند.
- حافظهٔ چندلایه + retention per-beat (C-046) + tip-commit (C-028).
- مدل‌سازی VOI/شبیه‌ساز خلاف‌واقع (بعد از دادهٔ واقعی مشتری، نه قبل).

## کارهای مالک (صریح)
GO/NO-GO برای: سفارش تست زیمان (N1) · ارسال quote (N2) · merge شاخه‌های audit این ممیزی · merge rescue→master (X7) · MINIAPP_URL (X3) · رأی به VOTE 4 و امضای B1 (C-037) و تأیید C-054.
