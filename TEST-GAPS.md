# TEST-GAPS — شکاف‌های تست

> Branch: `audit/zcode-20260828` · Date: 2026-08-28

## `langar` — وضعیت: 28 چک سبز، شکاف‌های بزرگ

موجود: test_langar.py (13 تست DB/HRV/coach/muse) + test_upgrades.py (15 چک retrieval/router/ACE) + _verify/test_arch.py (7 چک — روی کپی‌های کهنه!).

غایب:
- **صفر تست برای bot.py** (1916 خط: همهٔ handlerها، ConversationHandlerها، decoratorها)
- صفر تست async (بات کاملاً async است)
- صفر برای pro_client، ailab، budget، world_model، contract، patch_manager، rollback، tracer، event_log
- تست‌های HEAD صفر پوشش core pipeline با LLM واقعی (قابل فهم، ولی probe شبیه‌سازی‌شده هم نیست)
- test_upgrades.py:124 خطای نحویِ خفیف (check بی‌閉) — یک چک هرگز اجرا نمی‌شود
- تله: _verify/test_arch.py روی db نسخهٔ v3 اجرا می‌شود ⇒ سبزش گرین کاذب است

## `ofn-node` — وضعیت: 24 سوییت قوی، سه شکاف مشخص

- **test_shell_contract.py:278 گیت `partner_precondition` را در انتظارِ تست hardcode کرده** ⇒ تستِ سبز، گیتِ واقعاً-بسته را ادعا می‌کند در حالی که config.py:112 آن را در base_closed_gates ندارد (تست، باگ را پوشانده).
- شمارش تست در مستندات: 377/492/536/1229 در چهار سند مختلف — هیچ‌کدام با اجرای ثبت‌شدهٔ فعلی match نیست؛ `ofn/__init__.py __version__=0.1.0` در برابر v0.8.0 مستندات.
- تست‌های web/shell: HTML واقعی چک می‌شود ولی مسیر FE در براوزر (خودکار) تست نمی‌شود.

## درخت زندهٔ `_ops` — وضعیت: run_all 240 فایل سبز + 16 شکست ازپیش‌موجود

- [FACT TEST-COUNT.md 2026-08-15]: 2931/2931 چک سبز در 240 فایل + 16 failure شناخته‌شده که بدهی فنی‌اند و باید بسته شوند نه نادیده.
- تله‌های ثبت‌شدهٔ خودِ والت: pytest از ریشهٔ ریپو = INTERNALERROR (روش غلط شمارش)؛ «سبز از fake» و «سبز بدون قرمزِ قبلی» هر دو در قوانین 00-README ممنوع شده‌اند.
- ادعای 1229 تست OFN روی برد: هرگز از بیرون راستی‌آزمایی نشده [UNKNOWN] — PC به برد دسترسی SSH دارد ولی اجرای سوییت نیازمند هماهنگی است (پیشنهاد: receipt سبز روی برد در EVIDENCE).

## پیشنهاد کمینه (برای PRهای بعدی)
1. یک تست منفی واقعی برای partner_precondition (غیاب در base_closed_gates باید قرمز شود).
2. حذف/جابه‌جایی _verify/test_arch.py به کپی زنده.
3. بستن 16 شکستِ run_all یا مستندسازی صریح هرکدام به‌عنوان known-red با شماره.
4. شمارش تست واحد در یک فایل truth واحد (TEST-COUNT.md والت) به‌عنوان مرجع همهٔ مستندات.
