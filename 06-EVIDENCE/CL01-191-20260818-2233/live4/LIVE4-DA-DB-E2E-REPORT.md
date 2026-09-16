# LIVE4-DA-DB-E2E-REPORT (LIVE4-DEFECT-CLOSURE-AND-E2E-01) — 2026-08-19 ~11:4x +10:00
## D-A — ریشه‌یابی و رفع (FIXED_VERIFIED)
بازتولید از trace اصلی (live4-b1-base-*): بازتولید نشان داد ask_fugu هیچ tier نمی‌داد →
TASK_TIERS.get(task,"local") → بازوی baseline روی qwen محلی می‌رفت (7/15 شکستِ کیفیت‌گیت +
بقیه garbage لوکال) درحالی‌که cond روی deepseek بود — عدم‌تقارن ممنوعِ بازوها، نه خطای provider.
رفع: tier="primary" صریح در هر دو بازو (فقط ریشهٔ اثبات‌شده). regression: اجرای ۴case — هر دو بازو
deepseek-v4-flash، رسید COMPLETE متمایز، هیچ local امتیاز نخورد.
## D-B — قرارداد داوری (IMPLEMENTED؛ E2E = 3/4)
judge_contract در harness: verdict=A|B|TIE|UNREADABLE + rationale_hash + judge_provider/model +
trace_id؛ ناخوانا=VOID بی‌حدس؛ هر دو جهت A/B در تست و در اجرا دیده شد (WIN در B و WIN در A).
پرامپت داوری انگلیسیِ تک‌حرفی شد. باقی‌مانده: ۱ از ۴ case هنوز UNREADABLE (case3) → گیتِ «هر چهار» سبز نشد.
## E2E Gate نتیجه
سنتزی: 3/3 پاس (تفکیک/تصادفی‌سازی/قرارداد/یک‌بار‌شماری/duplicate). زندهٔ ۴تایی: 3 valid (همه WIN) · 1 VOID(judge) ·
spent=$0.0006 · هیچ local-scoring · رسیدها کامل.
## حکم صریح
D_A_BASELINE_ARM = FIXED_VERIFIED · D_B_JUDGE_CONTRACT = OPEN_JUDGE_UNREADABLE_1_OF_4 ·
LIVE4_SCORING = BLOCKED (تا ۴/۴) — batch کامل اجرا نشد، طبق حکم مالک.
## قدم بعدی (یک تکرار)
خروجی داوری JSON-اجباری ({"choice":"A|B|TIE"}) + در صورت UNREADABLE یک re-ask مجاز داخلِ سقف تلاش؛
سپس ۴case تازه؛ ۴/۴ ⇒ آزادسازی batch کامل (2×15 primary + تأییدی).
