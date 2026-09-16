---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, control-plane, snapshot, observability, web-app, megaprompt]
created: 2026-08-08
updated: 2026-08-08
created_by: agent
sources:
  - "control-plane snapshot megaprompt (third of three), 2026-08-08"
---

# control_plane.live_snapshot.snapshot() — جمع‌کنندهٔ واحدِ حالت — ۲۰۲۶-۰۸-۰۸

> اختاپوس ۷ لایه داشت ولی هیچ جمع‌کنندهٔ واحدی نبود — هیچ تابعی که کلِ حالت را در یک
> JSON برگرداند. نتیجه: مالک نمی‌توانست وضعیت را ببیند، وب‌اپ داده نداشت، و هر کارتِ
> تلگرامی منبعِ خودش را جدا می‌خواند. این تابع آن شکافِ «نمی‌شه دید» را می‌بندد و پایهٔ
> وب‌اپ و هر dashboardی می‌شود.

## کجا و چطور

- **فایل:** `_ops/control_plane/live_snapshot.py` — تابع: `snapshot(use_cache=True) -> dict`.
- **دسترسی:** `from control_plane import live_snapshot; live_snapshot.snapshot()`.
- **CLI:** `python -X utf8 _ops/control_plane/live_snapshot.py`.

## قراردادِ سخت (تست‌شده)

- کاملاً **read-only**، صفر LLM call (**$0**)، stdlib-only.
- **fail-soft کامل:** هر بخشی که خطا دهد → `{"status":"unknown","reason":"..."}`، نه crash.
  snapshot هرگز exception پرتاب نمی‌کند (تست: فایلِ خراب → بدون crash).
- **cache سبک:** TTL ۵s، در-پروسه (تست: دو فراخوانی = همان شیء؛ cache_clear = تازه).
- **نمایِ ثابت:** کلیدهای پایدار، JSON-serializable (تست: json.dumps موفق).

## ۸ بخش (همه از `_ops/state/*.json` خوانده می‌شوند)

| بخش | منبع | نمونهٔ زنده (۲۰۲۶-۰۸-۰۸) |
|---|---|---|
| organism | ORGANISM-STATE.json | beat=28709, frozen=False, n_legs=8 |
| budget | telemetry-latest + fugu-quota + budget-state | fugu 11/60, monthly_cap=30 AUD |
| brain | daemon_state + model_router.keys_present/paid_gate + paid-calls.jsonl | local_reachable=True, keys={fugu,glm}, paid_gate=open |
| flags | flags-loaded-*.json | 215 armed / 244 total |
| approvals | unified-approval-queue.json | 0 pending |
| memory | bcm-weights + hebbian + consolidation + self-model | bcm 96 keys, consolidation 583 cycles, self_awareness 97.6% |
| health | orphan-scan-latest (اگر هست) | unknown (reach_probe باید اجرا شود) |
| processes | flags-loaded-*.json + pid-alive check | **5/5 alive** |

## یافتهٔ تشخیصی مهم — تلهٔ تشخیصِ pid روی ویندوز

اولین نسخه از `os.kill(pid, 0)` استفاده می‌کرد برای تشخیصِ زنده‌بودنِ pid. روی ویندوز
این **غلط** است: `WinError 87 ("The parameter is incorrect")` می‌دهد (signal 0 یک مفهومِ
POSIX است که ویندوز آن را پشتیبانی نمی‌کند) که به‌اشتباه «غیرِزنده» تفسیر می‌شد. نتیجه:
**همهٔ ۵ پروسه alive=False** می‌زدند در حالی که واقعاً زنده بودند (tasklist تأیید کرد).

**فیکس:** `_pid_alive()` با `ctypes.windll.kernel32.OpenProcess` (PROCESS_QUERY_LIMITED_
INFORMATION؛ handle≠0 = زنده) روی ویندوز، و `os.kill(pid,0)` روی POSIX. حالا همهٔ ۵ = True.

## کشفِ معماری — collision با پکیجِ موجود

مگاپرامپت گفت «`_ops/control_plane.py` (فایلِ نو)»، ولی یک **پکیجِ `control_plane/`** از
۲۰۲۶-۰۸-۰۳ وجود داشت (`collector.py`/`supervisor.py` — کارِ مالکیتِ حالتِ فقط‌خواندنی،
تست‌شده در `test_control_plane.py`). فایلِ من با آن namespace collision می‌کرد (Python
package را بر module ترجیح می‌دهد). طبقِ مرزِ سخت «به چیزی که خودت نساخته‌ای دست نزن»،
پکیجِ موجود را بازنویسی نکردم — فایلِ من به‌عنوانِ `live_snapshot.py` درونِ همان پکیج
نشست. تفاوت: `collector.snapshot()` متمرکز روی processes/boot_flags/queues/halt/
governance با age_minutes؛ `live_snapshot.snapshot()` متمرکز روی ۸ بخشِ قراردادیِ وب‌اپ
(organism/budget/brain/flags/approvals/memory/health/processes). **مکمل‌اند، نه جایگزین.**

## تأیید

- `test_control_plane_live_snapshot.py`: **10/10 سبز** (همهٔ ۸ بخش، fail-soft روی فایلِ
  خراب، cache TTL، read-only، JSON-serializable، mutation-trap).
- `validate_contract.py`: PASS (6 capability manifests).
- frontmatter validator: اجرا شد (31 errors، baseline 27 — تغییری ندادم).

## commit
`feat(control_plane): snapshot() — جمع‌کنندهٔ واحدِ حالتِ زنده (۸ بخش، پایهٔ وب‌اپ)`
