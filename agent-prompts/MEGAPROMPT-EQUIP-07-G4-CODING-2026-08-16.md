---
megaprompt_title: EQUIP موج D1 — گروه ۴ کدنویسی خودمختار امن
version: "1.0"
sequence: 7
group: 4
wave: D
requires: "Wave C SCAN not FAIL"
next: "MEGAPROMPT-EQUIP-08-G5-INFRA-2026-08-16.md"
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g4-coding-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.

# ماموریت: Safe Autonomous Coding Capability

مسیر تولید، ویرایش، تست و commit کد توسط agentها را کشف کن.

هدف: coding agent در worktree ایزوله تغییر کوچک بسازد، تست کند و PR آماده
کند؛ نتواند مستقیم merge، deploy یا secret بخواند.

## حقیقت این vault

- ایجنت‌ها همین حالا روی `F:\backup` زنده کار می‌کنند — این خطر است.
  slice تو باید worktree جدا + filesystem jail را **برای عامل کدنویس**
  اجباری کند، نه اینکه خودش روی master بنویسد.
- `_ops/octopus_mcp`: read + propose_action فقط.
- protected: safety، credentials، policy، CI secrets، kill switch،
  `trust-boundary.json`، `_PROJECT_INSTRUCTIONS.md`، `.agentignore`.
- تست نو نام‌یکتا؛ `run_all.py` را ویرایش نکن.
- auto-merge/auto-deploy ممنوع.

## الزامات vertical slice

- هر task: git worktree + branch مجزا.
- shell allowlist + filesystem jail. network پیش‌فرض بسته.
- command: timeout + output limit. patch قبل از apply validate شود.
- تغییر protected paths = owner approval.
- pytest + (در صورت وجود) Hypothesis / Ruff / mypy در pipeline.
  mutation test فقط روی ماژول policy/memory اگر هزینه معقول است.
- generated code: diff محدود و reversible.
- commit message شامل Task ID + evidence.
- agent حق ندارد failing test را skip/xfail/حذف کند مگر تأیید صریح.

## سناریوی acceptance

یک bug واقعی کم‌ریسک انتخاب کن. regression test شکست‌خورده بساز، fix را در
worktree اعمال کن، نشان بده test قبل از fix شکست و بعد موفق است.
merge/push نکن مگر مالک بگوید.

## اسکن تخصصی

command injection · path traversal · symlink escape · secret access ·
unsafe subprocess · test deletion · hidden generated files ·
dependency confusion · malicious package scripts · unauthorized push/merge.

## TECHNOLOGY OPTIONS — GROUP 4

تحقیق جدا 2026-08-16.

PRIMARY:

- Isolated worktree (git) اول؛ sandbox بعد.
- tupper — E2B-alternative محلی، Firecracker، MCP.
  https://github.com/lightbearco/tupper
- rivet-dev/sandbox-agent — HTTP-controlled sandboxes (Daytona/E2B).
  https://github.com/rivet-dev/sandbox-agent
- E2B microVM / Daytona — اگر remote ephemeral لازم است.
  قوانین: بدون ambient credentials، egress default-deny، timeout سخت،
  sandbox پس از task حذف، mount فقط read-only.
- pytest + Hypothesis + Ruff/mypy — اگر در tree هستند همان را وصل کن.

PAPERS (research only):

- Ouroboros 2608.08311 (2026-08-08) — self-developing harness via reviewed
  commits. https://huggingface.co/papers/2608.08311
  **RESEARCH ONLY.** حق بازنویسی NBB-CP / kill / policy / credentials ندارد.
- AutoDesign 2608.13560 · Long-Horizon-Terminal-Bench 2607.08964
- Agent READMEs 2511.12884

DO

- worktree + default-deny network + protected paths.
- failing tests را حذف نکن.

DO NOT

- Ouroboros را runtime کن. auto-merge. `git add -A`.

## خروجی

`06-EVIDENCE/EQUIP-G4-CODING-2026-08-16.md`.
