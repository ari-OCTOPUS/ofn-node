# ACCEPTANCE-TESTS — v4 Wave-2 snapshot (هر تست: وضعیت فعلی + شرط PASS)

| ID | تست | وضعیت الان | PASS وقتی |
|---|---|---|---|
| AC-CENSUS-01 | no LIVE without L3 | **PASS** (۴ LIVE همگی entry-anchored به ofn.run@systemd) | ابزار فقط با شاهد L3 برچسب LIVE بزند |
| AC-CENSUS-02 | scanner read-only | **PASS** (drift_check.worktree_mutated=false) | worktree قبل/بعد hash یکسان |
| AC-T0-01 | یک llama روی 8081 | **PASS** (pid 170941، ollama=0) | listener_count==1 همیشه |
| AC-T0-02 | model hash guard | **PASS** (ExecStartPre sha256sum --check سالم + sha سومین تأیید) | guard دست‌نخورده |
| AC-T0-03 | KV/FA/offline truth | **PARTIAL** (FA=auto نه forced؛ честانه ثبت) | FA واقعی از log/metrics خوانده شود (موج ۳) |
| AC-CHAIN-01 | no new run | **PASS** (new_runs_created=0) | تا بستن زنجیره برقرار |
| AC-CHAIN-02 | source hash continuity | **PASS** (950f8d0e در proposal آمده) | echo در همه‌ی مراحل بعدی |
| AC-CHAIN-03 | proposal schema | **NOT_RUN** (validator روی کپی sandbox — موج ۳) | ولیدیشن سبز بدون تغییر contract |
| AC-CHAIN-04 | 138 receipt | **BLOCKED_GO-E** (پس از پچ) | mint receipt واقعی |
| AC-CHAIN-05 | 182 content receipt | **BLOCKED_GO-E** | رسید محتوایی مستقل |
| AC-IDEMP-01 | duplicate suppression | **PASS-by-design** (outbox._seen + processed_ids؛ تست runtime در موج ۵) | resend→duplicate بی‌اثر دوم |
| AC-XV-01 | vendor_id متفاوت | **DESIGN-READY** (قاعده ثبت؛ اجرا در موج ۶) | reviewer.vendor_id≠author |
| AC-XV-02 | dialect≠vendor | **DESIGN-READY** (تست anthropic-endpoint→deepseek) | api.deepseek.com/anthropic→vendor_id=deepseek |
| AC-PREFIX-01 | deterministic prefix hash | **FIXTURE-READY** (lab 44/48→regression fixture طبق فرمان §12) | hash پایدار بین اجراها |
| AC-PREFIX-02 | volatile suffix-only | **DESIGN-READY** | run_id/ts فقط suffix |
| AC-BUDGET-01 | reserve-before-call | **SCHEMA-READY** (budget_reservation.v1) | reservation قبل از هر تماس |
| AC-BUDGET-02 | reconcile-after-call | **SCHEMA-READY** | reconciliation پس از پاسخ؛ crash→BLOCKED_UNTRACKED |
| AC-SAFETY-01 | fail-closed بدون فلگ | **DESIGN-READY** (موج ۶ router 191) | مسیر پول بدون فلگ→رفض |
| AC-SAFETY-02 | no external effect بدون GO | **PASS** (external_effects=0) | تا Wave-8 برقرار |

جمع‌بندی: ‏۹ PASS · ‏۱ PARTIAL · ‏۲ BLOCKED_GO-E · ‏۷ DESIGN/SCHEMA-READY (پیاده‌سازی موج ۶-۷) · ‏۱ NOT_RUN (موج ۳).
