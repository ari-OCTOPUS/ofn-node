# CORE-AUTO-DEBUG-01 HANDOFF — 2026-08-19
A) COST-OBS-1: PROMOTED+VERIFIED (گزارش/دیف/رول‌بک پیوست؛ ۱۱/۱۱ تست؛ صفر فراخوانی live؛
   REPORTED ثبت می‌شود، AUD تا pin شدن fx بسته — طبق قاعدهٔ مالک)
B) INC1: FIXED_VERIFIED — اولین incident واقعی از telemetry (نویسندهٔ کم‌متادیتا) با چرخهٔ کامل
   کشف→ریشه→وصلهٔ قرنطینه→تست→پروموشن→re-run
مرزها: /sh مسلح‌مانده (CARD-A باز) · صفر تماس برد/شبکه/scheduler/TCB/credential · PROPOSE_ONLY
LIVE-4: پیش‌شرط‌های پرفلایت برای مالک — ① fx pinned (توصیه: نرخِ روزانهٔ ثابت از منبعِ مشخص؛
  تا provider بومی AUD بدهد عملاً هیچ‌وقت — RAI Doesn't exist) ② allowlist provider/model ③ budget-gate smoke receipt
  ④ پروتکل ارزیابی منجمد (۲۰ برد از ۳۰ جفت معتبر — ثبت عددی، نه «66.67%») ⑤ پروتکل داوری کور ⑥ وضعیت F3
F3 (کارت جدا): fail-closed متادیتا در MemoryStore.insert برای رکوردهای ارزیابی‌پذیر؛ raw در namespace جدا با eligible=false
