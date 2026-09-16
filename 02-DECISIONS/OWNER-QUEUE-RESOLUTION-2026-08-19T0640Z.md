---
type: decision
decision_id: OWNER-QUEUE-RESOLUTION-2026-08-19T0640Z
status: AUTHORIZED (Q1-Q8 resolved)
created: 2026-08-19T06:40Z
created_by: owner (via advisor, verbatim) — recorded by ZCode agent
supersedes: OWNER-DECISION-QUEUE.md open items (file kept as ledger of what was asked)
---

# OWNER SIGN-OFF — صف Q1–Q8

- **Q3 (اولویت اول)**: prediction_writer غیر-TCB + یک خط فراخوان در TCB با مراسم کامل؛ ریشه‌یابی و اصلاح باگ novelty (0.0<0.0) در self_evolve؛ **probe زنده با ≥۳ چرخهٔ observe→predict→outcome→belief-update در daemon واقعی** — تا سبز نشود «یادگیری زنده در Core» = UNVERIFIED.
- **Q1**: گارد additive در core/model.py + کلید I_pred در ANCHORS + چک در run_self_test؛ شرط سخت: snapshot کامل TCB + امضای مجدد + رگرسیون هر دو مسیر؛ تست قرمز = rollback فوری.
- **Q2**: model_router canonical بماند؛ دو مسیر dormant بنر RETIRE.
- **Q4**: Councils بنر CLOSED (نه حذف، نه فعال‌سازی).
- **Q5**: supervisor بنر RETIRE؛ schtask ساخته نشود.
- **Q6**: ACKNOWLEDGED — کار مالک، بدون اقدام.
- **Q7**: Action سه تسک → python.exe مطلق؛ ریسک صفر، فوری.
- **Q8**: DEFERRED — بنر RETIRE کافی.

## اولویت اجرا
Q3 → Q7 → Q1 → Q2/Q4/Q5 → Q6/Q8

## قوانین سخت (بدون استثنا)
TCB touch = snapshot قبل + امضای مجدد بعد + rollback آماده · هیچ حذفی، فقط RETIRE با بنر و تاریخ · VERIFIED فقط با probe زنده · برخورد به gap مالک‌محور جدید = صف کن و برو بعدی · گزارش نهایی باید خط جداگانهٔ Q3-probe داشته باشد (سبز/ناسبز).
