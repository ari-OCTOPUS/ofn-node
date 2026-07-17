# ZIMAN RISK REGISTER

- **زمان:** 2026-07-17 11:07 (+1000) · **روش:** static read-only · **مالک ریسک‌ها:** آری (مالک) مگر خلافش ذکر شود
- **مقیاس شدت:** Critical / High / Medium / Low · **وضعیت:** BLOCKED / OPEN / MITIGATED / MONITOR

| ID | ریسک | شدت | احتمال | وضعیت | شواهد (مسیر) | اقدام |
|---|---|---|---|---|---|---|
| R-01 | **درخت `_launchpad/second-brain-live`:** SEND واقعی تلگرام/WhatsApp + `.env` حقیقی + PII (chat-id) — ناقض «zero outward execution» | Critical | High | **BLOCKED** (verdict مالک) | `_launchpad/second-brain-live\` (`.env` در `control-brain\` — فقط نام) · CONFLICT-REGISTER CF-08 | مالک: اعلام وضعیت (ربات زندهٔ واقعی؟ → حاکمیت جدا + PII به `.env`) یا archive. ایجنت لمس نمی‌کند. |
| R-02 | **اختلاط پروژه‌ها در یک درخت:** painting-bot + accounting-bot + projectf-agent + ziman-agent با حافظه/اعتبار مشترک بالقوه | High | Medium | OPEN | `ls _launchpad/second-brain-live` (2026-07-17) | اعمال قاعدهٔ مرز ZIMAN/Painting (جداسازی repo، env، DB، کانال، بودجه، log). |
| R-03 | **کلید با برچسب اشتباه:** کلید DeepSeek تحت نام Anthropic در درخت launchpad — مدل/هزینه/حریم غیرشفاف | High | Medium | **BLOCKED** (چرخش/تصحیح توسط مالک) | CONFLICT-REGISTER CF-09 | مالک: rotate + تصحیح label. هرگز مقدار کلید در گزارش نیاید. |
| R-04 | **ظرفیت ۳۰/هفته تأییدنشده** — نشت عمومی عدد یا گیت fail-open → وعدهٔ کاذب به مشتری | High | Medium | MITIGATED (بخشی) | CF-01 · اصلاح content.py 2026-07-17 (۴ نقطه + ۷ تست رگرسیون) · `_ops/legs/ziman_leg.py` fail-closed | باقی: گیت `worker.py:106` (verdict) + verdict ZIM-V1. |
| R-05 | **موجودی ناشناخته** (۲۰ yaml vs ۵۰ شفاهی) — فروش کالای ناموجود | High | Medium | OPEN | CF-02 · STATUS.md §Numbers | جلسهٔ شمارش مالک → inventory_snapshot.v1 با measured_at. |
| R-06 | **قیمت/COGS null** — هر قیمت عمومی بدون ZIM-V5 جعلی است | High | Medium | OPEN | VERDICT_QUEUE ZIM-V5 | قیمت null تا verdict؛ لیستینگ بدون قیمت. |
| R-07 | **الکل/perishable در F4** — قانون NSW (مجوز فروش الکل، تحویل) | High | Medium | **BLOCKED** (سیاست مالک + بررسی حقوقی) | CATALOG.md خانواده F4 · VERDICT_QUEUE ZIM-V8/V9 | تا سیاست مالک: F4 از هر کمپین عمومی خارج. |
| R-08 | **مسیر Telegram Gifts/NFT/TON** — وضعیت حقوقی/مالیاتی/KYC-AML/ToS نامشخص؛ نوسان و کلاهبرداری بالا | Critical | High | **BLOCKED** (قانون ۵ — بررسی متخصص) | درخواست نقش فاز ۳/۴ · ifa.com.au digital-asset guidance (ارجاع در متن مالک) | در MVP فقط تحلیل/پیشنهاد؛ بدون معامله/ custody دارایی مشتری؛ مشورت حقوقی استرالیایی. |
| R-09 | **ATP fail-open روی timestamp کهنه/آینده** — وعدهٔ موجودی بر پایهٔ دادهٔ باطل | Medium | Medium | OPEN (verify) | CONFLICT-REGISTER CF-07 · product.py | بازخوانی تست‌های freshness + تست واقعی stale/future. |
| R-10 | ** drift سه درخت runtime** — رفتار متفاوت کپی‌ها | Medium | Medium | OPEN | CF-03 · find 2026-07-17 (۳ ریشه) | اعلام canonical = Projects؛ هرگز auto-sync؛ mirrorها فقط بایگانی. |
| R-11 | **نام برند حل‌نشده** (Ziman Gift / Galerry / Bloom rose-gold) — ریسک trademark/دامنه | Medium | Medium | OPEN | CF-05 · PROJECT.md §Assets | verdict ZIM-V4 + بررسی ASIC/TM Checker قبل از هر چاپ عمومی. |
| R-12 | **خرج LLM/Higgsfield بدون سقف** — هزینهٔ ناخواسته | Medium | Low | MITIGATED | budget.py (AU$15 fail-closed) · MANIFEST §budget_caps (Higgsfield TBD) | سقف اعتبار Higgsfield ثبت شود؛ هشدار مصرف؛ fallback آفلاین. |
| R-13 | **PII در prompt/log/digest** — نقض حریم | High | Low | MITIGATED | AGENT-HANDOFF §۲ · MANIFEST «صفر-PII» | ادامهٔ قاعده؛ اسکن نام‌محور انجام شد؛ نظارت. |
| R-14 | **وابستگی pytest به Python کاربر** (بدون venv پروژه) — شکست تست روی ماشین دیگر | Low | Medium | MONITOR | ls venv (ندارد) · pytest 9.1.1 در Python 3.13 | مستندسازی محیط؛ venv اختصاصی اختیاری. |
| R-15 | **Spam/ToS در DM بازار گرم** — Spam Act 2003 + قوانین پلتفرم | High | Medium | OPEN | ziman-agent content DM variants | فقط opt-in؛ ارسال دستی؛ مشورت قبل از هر کمپین انبوه. |
| R-16 | **Zero recorded sales** — هیچ اعتبارسنجی بازار واقعی | Medium | High | OPEN | STATUS.md (sales=0) | اجرای دستی کمپین گرم توسط مالک (roadmap گام ۷). |

## قواعد ثبت
- هر ریسک فقط با شواهد مسیر/سند ثبت می‌شود؛ عدد/ادعای بدون منبع نداریم.
- BLOCKED = ادامه ممنوع تا بررسی انسانی/حقوقی؛ هیچ workaround خودکار.
- این رجیستر با CONFLICT-REGISTER پروژه (CF-01..CF-10) هم‌راستاست و آن را جایگزین نمی‌کند.

**No secrets were copied or exposed.**
