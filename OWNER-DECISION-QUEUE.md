# OWNER-DECISION-QUEUE — مستقر از LOOP-01 (2026-08-19)

مواردی که ایجنت رویشان متوقف شد چون TCB/credential/غیرقابل‌بازگشت/مالک‌محورند. هر مورد: مدرک + پیشنهاد ایجنت.

| # | مورد | چرا مالک | پیشنهاد ایجنت | مدرک |
|---|---|---|---|---|
| Q1 | **C2 — واگرایی ریاضی TCB**: `core/model.py` بدون گارد DARE (ZeroDivision در ρ=1) در برابر `_ops/heart/sog_math` گارددار؛ I_pred هم در run_self_test چک نمی‌شود | تغییر TCB + امضای مجدد trust-boundary | همان VOTE A/B سند Improve: گارد additive در TCB + کلید I_pred در ANCHORS + re-sign | Deep-Seams/Improve ledgers؛ AUDIT §B10 |
| Q2 | **C3 — سه‌گانهٔ مسیریابی LLM**: model_router زنده + `4d_system/llm/router.py` + survival-gateway (هر دو dormant) | یکسان‌سازی یعنی لمس automation/daemon (TCB) | canonical = model_router بماند؛ دو dormat با بنر RETIRE؛ حذف منطق تکراری فقط با مراسم TCB | ARCHITECTURE-SOT؛ AUDIT §F1 |
| Q3 | **B1-fix — حلقهٔ prediction دیمن**: در brain اصلاً مسیرِ نوشتنِ prediction وجود ندارد (صفر ارجاع در کل لاگ/کد)؛ نوویسالت‌گیت هم «0.0 < 0.0» را بلاک می‌کند (ناهنجاری مقایسه) | wiring به automation.py/daemon.py = TCB | ماژول prediction_writer غیر-TCB + یک خط فراخوان در TCB با مراسم؛ + ریشه‌یابی مقایسهٔ نوویسالت در self_evolve | لاگ daemon 4942-4983؛ grep صفر-ارجاع |
| Q4 | **B3 — Councils**: DEAD-BY-DESIGN | تصمیم معماری صریح | همان‌طور بمانند (سایه) یا بنر CLOSE رسمی | کاتالوگ 08-16 |
| Q5 | **B4 — control_plane/supervisor** (never-wired، بدون schtask) | wire = پروسهٔ ماندگار ۲۴/۷ | RETIRE رسمی یا راه‌اندازی دستیِ موردی — نه schtask | کاتالوگ |
| Q6 | **E3 — OWNER_KEY / امضای D1 ممیزی مستقل** | سیستمی مالک | یادآوری طبق چک‌لیست | OPEN-GATES |
| Q7 | **TASKS-PATH** — سه تسک ویندوزی با لانچر `py` (FILE_NOT_FOUND) | تغییر schtasks = قلمرو مالک | Action → python.exe مطلق (الگوی Observatory سبز) | کاتالوگ 1-3 |
| Q8 | **A3-آینده** — اگر auto_experiment روزی لازم شود | wiring در TCB | از Island با benchmark | بنر RETIRE امروز |

## شناسهٔ تناقض بعدی (E1، grep-verified)
**C-035** — بالاترین تخصیص‌یافته: C-034 (۱۰۶ ارجاع). ادعاهای کهنهٔ C-025/029/031 لایه‌های تاریخی همان دفترند.
PHANTOM-DOCUMENTS.md (E2): با این نام پیدا نشد — یا نامش عوض شده یا موجود نیست؛ تیم‌های Island ارجاعی بهش ندارند.
