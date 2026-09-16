---
type: decision
decision_id: OWNER-DIRECTIVE-13
status: ACTIVE — حاکم بر #۱..#۱۲؛ تمرکز واحد: حلقهٔ بستهٔ واقعی Telegram
created: 2026-08-20
created_by: OWNER — ثبت condensed توسط ایجنت B (متن کامل در پیام/پیست مالک)
---

# مگا‌دستور #۱۳ (چکیدهٔ نافذ — متن کامل مالک مرجع است)

مأموریت: پیام واقعی مالک → ingest دوزمانی → بازیابی حافظه → HC → WM →
Metacontrol → DeepSeek امضاشده → پاسخ advisory فقط به همان مالک → ثبت حافظه →
استفادهٔ واقعی در turn بعدی. توسعهٔ جانبی (parser جدید، LAB-1 فاز۲، pymdp،
ablation، merge، سخت‌افزار، frontmatter، scheduler، سقف‌ها) تا پایان تست متوقف.

## مجوز تلگرام (استثنای محدود)
TELEGRAM_OWNER_REPLY: فقط same owner chat_id/user_id پین‌شده · advisory_text ·
max 1 reply/input · بدون file/forward/ثالث/خرج/اجرای · footer الزامی:
`[ADVISORY · turn=<id> · memory=<n> · gate=<mode>]` · LIVE-E را باز نمی‌کند.
executable=true فقط allowlist محافظ ADR-035.

## قفل‌های حکمرانی (§۲)
write زیر lease · شاخه/نویسندهٔ واحد · no amend/rebase · **هیچ CronCreate/
CronUpdate/Task Scheduler حتی read** · ریاستارت daemon فقط با supervisor احراز+
baseline · رأی چت≠امضا · فراخوان پولی فقط کارت امضاشده+FX+task/run receipt ·
بدون token/secret در log · life_credit≠AUD · Judge-Bias هم‌زمان با Full-Loop ممنوع.

## ماشین حالت turn (§۳)
RECEIVED→INGESTED→MEMORY_RETRIEVED→SELF_ASSESSED→WORLD_MODELED→GATED→
MODEL_INTENT_RECORDED→(MODEL_COMPLETED|FAILED)→RESPONSE_PROPOSED→
(TELEGRAM_SENT|SEND_FAILED)→MEMORY_COMMITTED→OUTCOME_PENDING→(FEEDBACK|EXPIRED)
→CONSOLIDATED. SENT بدون COMMIT = TURN_PARTIAL_OUTPUT_NOT_LEARNED + reconcile
در شروع بعد (intents/outbox/sent-without-commit).

## حافظه (§۶)
سه read قبل از مدل (query_experiments/get_pending_hypotheses/search_vault همگی
decision_time) · سه لایهٔ پس از پاسخ (episodic immutable / semantic candidate
تأییدنشده تا /good|/correct|شاهد دوم / skill-outcome) · اثبات یادگیری: ID مشخص
در context turn بعد + اثر مشاهده‌پذیر؛ حکم‌ها: READ_BACK_USED ·
READ_BACK_RETRIEVED_NOT_USED · MEMORY_MISSED · MEMORY_FUTURE_LEAK.

## HC/WM (§۷) و Gate (§۸)
هر turn دو تصمیم آفلاین A=با HC/WM و B=بدون (بدون call دوم)؛ هم‌انگه‌دائمی =
HC_WM_DECORATIVE_PATH → FAIL. WM فقط facts/hypotheses/uncertainties.
Gate: provenance ناقص/future/conflict→BLOCK · warm-up→حداکثر SHADOW ·
judge→advisory (D6) · BLOCK=بدون call · SHADOW=ثبت+ارسال با هشدار.

## DeepSeek (§۹) + Outbox (§۱۰)
شرط شروع: LIVE-B ≥ CLOCK_CAVEAT + کارت verify + FX تازه + ≤12 call/AU$0.50/
concurrency1. write-ahead intent (hash(card+run+turn+prompt))؛ یک intent یک
call؛ timeout=FAILED_UNKNOWN_MAY_HAVE_SPENT بدون retry. OUTBOX_PENDING→SENT؛
SEND_UNKNOWN بدون resend کور؛ یک input یک پاسخ.

## LIVE-B حداقلی (§۱۱) + تست ۱۲تایی (§۱۲-۱۳) + evidence pack (§۱۵)
LIVE-B: تلگرام message.date + probe server_created + suite واقعی + حکم خودکار
(#۱۲§۱۱)؛ CLOCK_CAVEAT کافی برای شروع advisory. ماتریس ۱۲ task (status تا
synthesis؛ ≥2 وابسته به خروجی قبلی). معیار PASS: 12 turn کامل · reads≥3 ·
≥10 turn با حافظه · ≥2 اثبات بین‌چرخه‌ای · future=0 · UNKNOWN→0=0 · duplicate=0 ·
attribution=100% · pending=0 · incident جدید=0. حکم‌ها: REAL_CLOSED_LOOP_PASS ·
PASS_WITH_FINDINGS · INCOMPLETE · FAIL · ABORTED. هیچ‌کدام GAP-001/LIVE-E را
نمی‌بندد.

## پس از PASS (§۱۴) · توقف مجاز واحد (§۱۶)
adapter در daemon موجود (scheduler جدید نه) · rate ۳۰/h · status ساده محلی ·
fallback با برچسب · /stop فوری بدون قفل رفلکس. تنها پیام توقف قبل از تست:
`TELEGRAM READY — SEND: /status`
