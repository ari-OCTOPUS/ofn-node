---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, codex, mission-runner]
created: 2026-07-18
updated: 2026-07-18
created_by: agent
---

> **for:** Codex · **risk:** high (execution layer — but propose-only boundaries enforced)

# CODEX PROMPT 1/5 — Mission Runner v0 (Isolated Executor)

> نقش تو: **Bounded Executor Engineer** برای اختاپوس. تو حلقهٔ مفقودهٔ «Mission → اجرای واقعیِ ایزوله → Evidence» را می‌سازی. تو ایجنتِ آزاد نیستی؛ یک executor محدود، deterministic و evidence-driven می‌سازی.

## 0) حقیقت زمین (verified 2026-07-18 — به این اعتماد کن، ولی دوباره چک کن)

- Repo: `F:\backup` · branch: `master` · HEAD: `c9b9a03` (داک‌ها) ← `7742486` (کد اختاپوس) ← `5cad78f` ← `f890456` ← `76f64f0` ← merge `7ad1ce4`
- **همهٔ کد اختاپوس commit شده است** — هیچ کار معلقی در `_ops/telegram_center/` نیست.
- ماژول‌های موجود (همه stdlib-only، fail-soft، import-time خالص):
  - `_ops/telegram_center/mission.py` — توابع کلیدی: `create_mission(owner_intent, *, source, ...)` · `infer_mission_type(text)` · `actions_for_type(mt)` · `build_plan(mt)` · `set_state(mid, new_state, note)` · `record_test(mid, name, passed, detail)` · `record_review(mid, reviewer, ok, detail)` · `set_owner_verdict(mid, approved)` · `compute_fitness(mission)` · `refresh_fitness(mid)` · `cockpit_summary(limit)` · `mission_card(mid)` · `_atomic_write_json` · `_load_state/_save_state` · `_audit`
  - `_ops/telegram_center/action_graph.py` — `ActionSpec` (خط ۲۲) · رجیستری `_ACTIONS` (خط ۴۴) · `all_actions()` · `get(action_id)` (ناشناس = fail-closed) · `requires_owner_approval` · `risk_rank/max_risk` · `allowed_at_level`
  - `_ops/telegram_center/approval_store.py` — `add_pending` · `approve/reject/mark_done` · `load_pending` · `summary` · `sync_to_octopus_state` (پل `_octopus` ↔ `_ops/state/telegram`)
  - `_ops/telegram_center/intent.py` — `classify(text)` (۹ intent) · `is_read_only(intent_name)`
  - `_ops/telegram_center/center.py` — `_handle_ask` (متن آزاد → mission) · صفحهٔ `mn:ms` · callbackهای `ms:open/test/review/approve/reject:<id>` · فرمان `/missions`
- چرخهٔ state فعلی mission: `created→planned→patched→tested→reviewed→awaiting_owner→approved→applied→monitored→done/reverted/rejected`
- تست‌های سبزِ runtime (اجراشده روی ویندوز، 2026-07-18): intent ۱۶ · metadata_scan ۱۱ · approval_store ۱۴ · actions ۱۰ · mission ۱۳ · render ۱۶ · center ۲۲ · tg_api ۱۸ = **۱۲۰ سبز**
- نکتهٔ صداقت (از گزارش رسمی): `ms:test` و `ms:review` **فقط درخواست را ثبت می‌کنند** — هیچ تست/دکتری واقعاً اجرا نمی‌شود. **این گپ، مأموریت توست.**

## 1) مأموریت

بساز: `_ops/telegram_center/mission_runner.py` + `_ops/tests/test_tg_mission_runner.py` و ثبت در `_ops/tests/run_all.py`.

Runner v0 این چرخه را واقعی می‌کند:

```text
mission (state=planned|approved_for_isolated_run)
→ worktree ایزوله از SHA صریح (git worktree add)
→ اجرای فقط actionهای allowlisted: code.plan / code.test / code.diff / doctor.review / epistemics.review
→ ثبت artifact (خروجی، exit code، SHA، duration) در _agent_reports/missions/<mission_id>/run-<ts>/
→ mission.record_test / record_review / refresh_fitness (فقط از روی artifact واقعی، نه ادعا)
→ برگرداندن mission به awaiting_owner + cleanup worktree
```

### مجاز (بستهٔ کامل — چیزی اضافه نکن)
- `git worktree add <tmp> <sha>` و remove همان worktree پس از ثبت شواهد
- اجرای تست‌های allowlisted با `python -X utf8` و `REAL_VAULT=<worktree>` (الگوی harness موجود در `_ops/tests/`)
- تولید diff/گزارش read-only · ثبت audit event با همان الگوی `_audit` موجود

### ممنوع (fail-closed — تستش کن)
`git push` · merge/delete branch · commit به master · `code.apply` · تغییر secret/token/env · shell آزاد از متن کاربر · network call · تغییر live vault · self-expanding scope · اجرای دوباره در retry/crash (idempotency با run_id)

### اصل دوکلیدی
هر مسیرِ منتهی به اثرِ زنده باید هر دو کلید را بخواهد: **Key1 evidence-gate** (تست سبز + no-secret-leak + no-forbidden-path + rollback ref) و **Key2 owner-gate** (`set_owner_verdict` روی همان scope). بدون هر دو: apply = impossible (در v0 اصلاً پیاده نمی‌شود).

## 2) تست‌های اجباری (حداقل ۱۰)
از ماتریس ۱۵گانهٔ blueprint، این‌ها الزامی: (۱) غیرمالک → سکوت مطلق (۲) mission ساخته می‌شود ولی apply نمی‌شود (۳) approve → فقط isolated (۴) تغییر scope بعد از approval → invalid (۵) action ناشناس → fail-closed بدون traceback/token (۶) شکست تست → `verification_failed` و بستن مسیر apply (۷) crash/restart → نه falsely-passed نه silently-lost (۸) status=passed بدون artifact → reject توسط invariant (۹) duplicate callback → اجرای حساس دوبار رخ ندهد (۱۰) redaction/containment در artifact و کارت (اصطلاح «Project-F» فقط؛ الگوی `_BANNED_ECHO` موجود در center.py را دنبال کن).

## 3) قانون اساسی (تغییرناپذیر)
- قبل از هر کاری: `git status --short` · اگر کار uncommitted از جلسهٔ دیگر دیدی: نه commit نه revert — فقط گزارش.
- commit اتمیک، `git add -A` ممنوع، state-churn (`_ops/state/*`, `_ops/budget/*`, `_octopus/`) هرگز commit نمی‌شود.
- static review را runtime جا نزن — هر ادعا: مسیر + خروجی واقعی + exit code.
- توکن/secret هرگز در log/artifact/کارت (الگوی `token_source` در `tg_api.py::diagnostics`).
- سوئیت کامل: `python -X utf8 _ops\tests\run_all.py` در **worktree تازه** (نه درخت زنده). درخت زنده فقط read-only.

## 4) خروجی نهایی
1. کد + تست‌ها سبز (خروجی واقعی paste کن) 2. `_agent_reports/MISSION-RUNNER-V0-REPORT-<date>.md` با جدول claim↔evidence 3. آپدیت `01 - Dashboard/HANDOFF.md` (یک بولت) + `04 - Architect System/architect/PROJECT.md` (Active Context) 4. verdict صریح: `READY FOR RUNNER v1 / READY WITH BLOCKERS / NOT READY` + دقیقاً یک next-action کم‌ریسک.
