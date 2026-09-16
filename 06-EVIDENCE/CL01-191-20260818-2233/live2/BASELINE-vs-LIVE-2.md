# BASELINE vs LIVE-2
baseline منجمد (Live-1، هش 89247d54…): brier=null (بدون outcome) · coverage: prov/ts/exp=100% conf=91.7% کل 97.93%
LIVE-2: brier=0.1195 (n=20) · coverage: prov/ts=100% conf=91.77% expiry=99.59% کل 97.84% (admitted 482→486)
- بهبود نسبت به baseline عددی «تعریف‌نشده» است (baseline=null) — قاعدهٔ مالک شرط۲ را literal می‌بندد
- مرجع کمکی (بدون-مهارت 0.25): LIVE-2 بهتر (0.1195) — سیگنال مثبت، ادعای VERIFIED نمی‌سازد
- degradação کالیبراسیون: در proposal-diff (80% ادعا vs 40% واقعی) اما 3/5 آن خطای provider بود (کانفاند)؛ سیگنال تمیز 2/2
