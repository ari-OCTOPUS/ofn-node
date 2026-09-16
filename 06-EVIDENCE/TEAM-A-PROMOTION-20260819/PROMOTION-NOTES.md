# TEAM-A PROMOTION — 2026-08-19 (OWNER-CONSENTS-2026-08-19T0615Z §4: «همین حالا»)

## Promoted (non-TCB, CORE-AUTO-DEBUG)
1. **رادار تناقض روی مسیر تولیدی** — wiring.py هنگام ساخت MemoryGate، `contradiction_checker` را به ContradictionRadar(store=mem) وصل می‌کند (hook موجود gate.py). هر تناقض ⇒ verb=quarantine + ردیف QUARANTINED (گذار وضعیت، بدون حذف).
2. **ستون‌های مستقیم** — evidence_ref / confidence_source / confidence_method به‌صورت ALTER افزایشی (الگوی مهاجرت v1→v3 موجود) + پر شدن از candidate در gate + INSERT در store.
3. **F3 بسته شد** — insert بدون confidence ⇒ ValueError fail-closed («F3: confidence required…»). ۴۲ ردیف تاریخیِ فاقد confidence دست‌نخورده و EXCLUDED می‌مانند.
4. **QUARANTINED به _ADMISSION_STATES اضافه شد** (قبلاً در مجموعهٔ مجاز نبود).

## Tests — 10/10 PASS (`_ops/tests/test_memory_team_a_promotion.py`)
commit تمیز · ستون‌ها persisted · F3 reject · تناقض→quarantine+retention · ADMITTED سالم · مهاجرت زنده (۳ ستون اضافه، شمار ردیف ۵۱۸ بدون تغییر توسط مهاجرت — رشد ۵۰۸→۵۱۸ در طول روز، عملکرد طبیعی ارگانیسم).

## Deferred (explicit)
PENDING-default دو مرحله‌ای برای همهٔ نویسنده‌ها (submit→PENDING→promote) — گیت از admission_state=CANDIDATE پشتیبانی می‌کند اما تغییر پیش‌فرضِ همهٔ نویسنده‌ها بدون گرسنگی‌دادنِ بازیابی، به جلسهٔ بعد با پکت جداگانه. قابِ دومرحله‌ایِ واقعیِ امروزی: رادارِ pre-commit + QUARANTINED.

## Runtime effect
از restart بعدی ارگانیسم (که wiring دوباره اجرا شود)، هر نوشتنِ متناقض قرنطینه می‌شود. تست با همان کدِ wiring (لامبدای یکسان) انجام شد.
note: gate.py/memory_store.py carried pre-existing uncommitted CL01 edits; TEAM-A-HUNKS.diff isolates this promotion's hunks (full-file diff deliberately omitted)
