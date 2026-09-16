---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, codex, git, tests]
created: 2026-07-18
updated: 2026-07-18
created_by: agent
---

> **for:** Codex · **risk:** low (read-only triage + bounded test refactor؛ صفر merge)

# CODEX PROMPT 5/5 — Branch Triage (رأی‌ساز، نه merge) + بستن نشت REAL_VAULT

> نقش تو: **Repo Surgeon (read-only) + Test Hygienist**. دو بدهی مشخص مانده: (الف) ~۱۵ شاخهٔ unmerged ارزشمند که فقط مالک حق رأی merge دارد — تو «کارت رأی» می‌سازی؛ (ب) ~۱۵ فایل تست legacy که `REAL_VAULT` را به `sys.path` نشت می‌دهند (footgun توسعه‌دهنده، chip `task_0f9991fc`) — تو با الگوی اثبات‌شده می‌بندی.

## 0) حقیقت زمین (verified 2026-07-18)

- Repo: `F:\backup` · master · HEAD `c9b9a03`. بعد از هرس 2026-07-18: شاخه‌ها ~۴۰، worktreeها ~۲۸.
- شاخه‌های ایمنی که **دست نمی‌زنی**: `backup/*` · `unify/octopus-2026-07-18` · `integration-debug-2026-07-18`.
- شاخه‌های unmerged ارزشمند (از گزارش unify — خودت با `git branch --no-merged master` بازتولید کن): بستهٔ PF (~۱۶۶ تست، containment: فقط «Project-F» در هر خروجی) · Painting-OS (اینوویس/کوت/ایمیل) · email-inbound · mom-bot · سخت‌سازی M1–M7 · pulse-arbiter · و بقیه.
- **الگوی فیکس نشت (اثبات‌شده در commit `fc53252`):** تست باید کد زیر تست را از درخت خودش بردارد — `Path(__file__).parents[1]`-based، env-first (`REAL_VAULT` فقط وقتی صریحاً ست شده). نمونهٔ سالم: `_ops/tests/test_tg_center.py` سرِ فایل. ضدالگو: `_LEGS = harness.REAL_VAULT / "_ops" / "legs"`.
- لیست دقیق ۱۵ فایل نشت‌دار را خودت دربیاور: `grep -n "REAL_VAULT" _ops/tests/*.py` و آن‌هایی که به `sys.path` تزریق می‌کنند یا مسیر import را از vault زنده می‌سازند.

## 1) مأموریت الف — Branch Triage (صفر write روی شاخه‌ها)

برای **هر** شاخهٔ `--no-merged master`:
```text
| branch | tip SHA | آخرین commit (تاریخ/پیام) | ahead/behind master | فایل‌های یکتا (top 5) |
| conflict بالقوه با master (dry-run: git merge-tree) | تست‌های ادعایی | ریسک containment |
| توصیه: MERGE-NOW / CHERRY-PICK(کدام SHA) / KEEP-FROZEN / ARCHIVE-TAG+DELETE | چرا (۲ خط) |
```
ابزار مجاز: `git log/diff --stat/merge-base/merge-tree` (همه read-only). **هیچ merge/rebase/delete/checkout روی این شاخه‌ها.** خروجی: `_agent_reports/BRANCH-TRIAGE-2026-07-18.md` + بخش `OWNER-DECISIONS-REQUIRED` (هر شاخه یک سطر رأی: ✅/❌/⏸). برای بستهٔ PF فقط متادیتا (تعداد کامیت/تست) — نه نام فایل‌های داخلی، نه محتوا.

## 2) مأموریت ب — بستن نشت REAL_VAULT (bounded)

1. لیست نشت‌دارها را با grep دربیاور و در گزارش بیاور (انتظار: ~۱۵؛ اگر عدد فرق داشت، عدد واقعی حاکم است).
2. فقط فایل‌هایی را دست بزن که واقعاً الگوی import/sys.path نشت دارند — «خواندن دیتای read-only از REAL_VAULT» نشت نیست، به آن‌ها دست نزن.
3. هر فایل: به الگوی `fc53252` مهاجرت بده؛ بعدش تک‌تک اجرا: `python -X utf8 _ops\tests\<file>.py` — سبز.
4. آخر: `run_all.py` کامل در worktree تازه از master — باید همان تعداد قبلی سبز بماند (رگرسیون صفر).
5. commit اتمیک فقط همان فایل‌های تست + بستن chip `task_0f9991fc` در گزارش.

## 3) قانون اساسی
درخت زنده read-only مگر commit نهایی بخش ب؛ کار uncommitted دیگران دست‌نخورده؛ `git add -A` ممنوع؛ state-churn/`_octopus/` commit نمی‌شود؛ هیچ push؛ containment «Project-F» در تمام خروجی‌ها؛ هر عدد در گزارش = خروجی دستور واقعی (SHA/command paste).

## 4) خروجی نهایی
1. BRANCH-TRIAGE + OWNER-DECISIONS (الف) 2. کامیت فیکس تست‌ها + خروجی سبز (ب) 3. بولت HANDOFF + PROJECT architect 4. verdict: تعداد شاخهٔ هر توصیه + «کوچک‌ترین merge پرارزش برای رأی مالک کدام است؟»
