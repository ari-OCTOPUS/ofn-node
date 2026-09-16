---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, codex, approval, security]
created: 2026-07-18
updated: 2026-07-18
created_by: agent
---

> **for:** Codex · **risk:** medium (safety substrate — additive, flag-compatible)

# CODEX PROMPT 2/5 — Approval Binding (scope-hash + expiry + idempotency)

> نقش تو: **Authorization Hardening Engineer**. صفِ تأیید کار می‌کند ولی approval فعلاً به «شناسهٔ job» بسته است، نه به «محتوای دقیق کاری که تأیید شد». تو approval را به scope واقعی گره می‌زنی تا bait-and-switch ساختاراً ناممکن شود.

## 0) حقیقت زمین (verified 2026-07-18)

- Repo: `F:\backup` · master · HEAD `c9b9a03`؛ کد در commit `7742486`.
- `_ops/telegram_center/approval_store.py` (۱۴ تست سبز) — نقشهٔ فعلی:
  - `_load_octopus_approvals()` (خط ~۶۲) / `_save_octopus_approvals()` (خط ~۸۴) — پل دو-مخزنه: `_octopus/state` ↔ `_ops/state/telegram`
  - `add_pending(job) -> jid` (خط ~۱۱۳) · `_move(jid, from_list, to_list)` (خط ~۱۴۵) · `approve(jid)` (خط ~۱۶۷) · `reject(jid)` · `mark_done(jid)` · `load_pending()` · `get(jid)` · `summary()` · `sync_to_octopus_state()` (خط ~۲۰۷) · `record_legacy_verdict(jid, verdict, source)` (خط ~۲۳۴) · `_audit(event, detail)`
- مصرف‌کننده‌ها: `center.py` (callbackهای `ap:*` و `ms:approve/reject:<id>`) · `mission.py::set_owner_verdict`
- ماتریس تهدید که باید ببندی (از blueprint §۶): (۳) آیا approval به action + exact scope + exact diff بسته است؟ **الان نه.** (۴) آیا بعد از تغییر diff، approval قدیمی invalid می‌شود؟ **الان نه.** (۵) آیا retry باعث اجرای دوبارهٔ action حساس می‌شود؟ **بررسی‌نشده.** (۶) آیا state corruption/restart می‌تواند approval را bypass کند؟ **بررسی‌نشده.**

## 1) مأموریت (additive — سازگار با دیتای موجود)

در `approval_store.py` و نقاط اتصالش:

1. **scope_hash:** `sha256` روی نمایش canonical از `{action_ids, paths, diff_sha یا payload_hash, mission_id}` → در `add_pending` ذخیره شود (`approval_scope_hash`). jobهای قدیمی بدون hash باید همچنان load شوند (backward-compatible) ولی برای **approve شدنِ جدید** hash اجباری است.
2. **binding:** `approve(jid, scope_hash=None)` — اگر hash داده شود باید برابر رکورد باشد؛ mismatch → reject + audit `approval_scope_mismatch`. مسیر UI (center.py) hash رکورد را pass کند.
3. **invalidate-on-mutate:** هر تغییر در payload/scope یک job → status به `expired` + audit. تابع کمکی `revalidate(jid, current_scope_hash)`.
4. **expiry:** فیلد `expires_at` (پیش‌فرض ۲۴h — به‌عنوان `OWNER-DECISION` در گزارش بیاور). `load_pending` و `approve` منقضی‌ها را fail-closed کنند.
5. **idempotency:** dedupe روی `callback_id/update_id` تلگرام برای اکشن‌های حساس — دوبار کلیک/retry شبکه = یک اثر. store کوچک `_ops/state/telegram/callback-dedupe.json` با `_atomic_write_json`-style و پنجرهٔ زمانی.
6. **crash-safety:** نوشتن اتمیک (tmp+replace — الگوی `mission.py::_atomic_write_json`) در هر دو مخزن؛ اگر یکی از دو مخزن corrupt بود → fail-closed با audit، نه سکوت.

## 2) تست‌های اجباری
گسترش `_ops/tests/test_tg_approval_store.py` (الان ۱۴ سبز — همه باید سبز بمانند) + سناریوهای نو: scope-mismatch رد می‌شود · mutation → expired · approve منقضی → رد · duplicate callback → تک‌اثر · corrupt JSON در هر مخزن → fail-closed بدون traceback در UI · هیچ token/متن contained در audit («Project-F» فقط).

## 3) قانون اساسی
مثل همیشه: اول `git status --short`؛ کار uncommitted دیگران دست نزن؛ commit اتمیک بدون `git add -A`؛ state-churn و `_octopus/` commit نمی‌شوند (gitignored از `7742486`)؛ هر ادعا با اجرای واقعی `python -X utf8 _ops\tests\test_tg_approval_store.py` و بعد `run_all.py` در worktree تازه؛ درخت زنده read-only مگر commit نهایی.

## 4) خروجی نهایی
1. کد + تست سبز (خروجی paste) 2. `_agent_reports/APPROVAL-BINDING-REPORT-<date>.md` — جدول تهدید→بسته‌شد + `OWNER-DECISIONS-REQUIRED` (expiry چند ساعت؟ apply فقط CLI یا Telegram double-click؟) 3. یک بولت HANDOFF + یک بولت PROJECT architect 4. verdict: `HARDENED / HARDENED WITH GAPS / BLOCKED`.
