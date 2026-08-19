# CORE-LIVE-1 REPORT — 2026-08-18 23:12–23:14 +10:00 (91s از پنجرهٔ 30min)
trace: cl1-live1-131246 · exit=0 · provider فقط از درِ واحدِ موجود (ProviderRouter→model_router)
- dry-receipt محلی پیش از اولین فراخوانی: ✓ (دو مورد — اجرای اول دریمِ import fail کرد پس از نوشتن dry-receipt؛ ثبت صادقانه)
- prediction پیش از outcome: ✓ cl1-pred-0001 → outcome=HIT (task.completed 5→8 در 90s)
- retrieval با provenance از canonical: ✓ (5 نمونه، provenance کامل)
- پروپوزال دوبل: ✓ evidence_changed_proposal=TRUE (baseline ≠ evidence-conditioned)
- سقف‌ها: per_call 0.50 AUD — هزینهٔ واقعی ~0 (gateway طبق D5 «fugu» را انتخاب کرد، نه deepseek؛ tokens/cost در پاسخ نبود → None ثبت شد، حدس زده نشد)
- admission: PROPOSED_NOT_CANONICAL (خروجی LLM خودش canonical نمی‌شود — گیت فعال)
- دیمون ۴d: PID 18020 از 23:08 · preflight enforcement=true/tampered=false/signature=valid · صفر HALT
- پروموشن: ۶ فایل از worktree cl01/p2-gate (diff=gate-patch.diff، تست‌ها 8/8+7/7) · rollback در promotion-record.txt
