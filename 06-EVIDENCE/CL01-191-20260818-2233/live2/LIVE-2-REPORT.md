# LIVE-2 REPORT — 2026-08-18 23:24–23:48 +10:00 (23.8min از سقف 2h) · exit=0 · trace cl1-live2
پنجره/سقف‌ها: concurrency=1 · provider فقط از ProviderRouter · هزینهٔ واقعی ۰ AUD (fugu free-tier؛ هویت عیناً ثبت شد، ادعای DeepSeek نشد) · صفر تماس برد/شبکه/شل.
- پیش‌بینی‌ها: ۲۰ ثبت‌شده قبل از outcome · ۲۰ outcome (≥۱۰ ✓ → INSUFFICIENT_OUTCOMES نگرفت)
- Hits=13/20 · Brier=0.1195 (مرجع بدون-مهارت: 0.25)
- کالیبراسیون به تفکیک: A(conf.90)→8/8 ✓ · B(conf.10)→0/4 ✓ دقیق · C(conf.70)→3/3 (کم‌اعتمادی) · proposal(conf.80)→2/5 ⚠ آلوده (بند INCIDENT)
- تزریق‌ها: ۵/۵ fail-closed پاس (duplicate=IDEMPOTENT_SKIP · contradiction=QUARANTINED · expired=فیلترشد · metadata=REJECTED · provider-fail=fail-closed)
- دیمون ۴d: PID 18020 زنده در کل پنجره · صفر HALT
- توقف سخت فعال‌شده: نرخ خطای provider 3/10 (≥5% پس از ۱۰ فراخوانی) → فراخوانی‌های provider متوقف شدند؛ بخش غیر-provider (پیش‌بینی‌های دیمون) طبق طراحی ادامه یافت و شواهد حفظ شد
