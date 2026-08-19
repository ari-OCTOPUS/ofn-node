# P1 COMPLETION REPORT — Writer/Reader Census + Bypass Verdicts + Corrected Reality

run: CL01-191-20260818-2233 (زیر CORE-LIVE-LEARNING-01 / EXECUTION CONTINUATION) · 2026-08-18 ~22:33–23:0x +10:00
حالت: فقط‌خواندن (census) — پچ‌ها در بلوک بعدی در worktree قرنطینه.

## ۱. جدول کامل writer/readerهای حافظه

| # | مسیر کد | تابع/کلاس | نوع | مسیر داده | نقش |
|---|---|---|---|---|---|
| W1 | `4d_system/brain/automation.py:455` (TCB) | save_hypothesis | write | `4d_system/outputs/4d_experiments.db` | پژوهشی |
| W2 | `4d_system/brain/auto_experiment.py:72` | save_hypothesis | write | همان | پژوهشی |
| W3 | `4d_system/brain/hypotheses.py:199` | save_hypothesis | write | همان | پژوهشی |
| W4 | `4d_system/brain/reflection.py:121` | save_reflection | write | همان | پژوهشی |
| W5 | `4d_system/brain/tools.py:151` | save_hypothesis | write | همان | پژوهشی |
| W6 | `4d_system/brain/research_agenda.py:75` | save_hypothesis | write | همان | پژوهشی |
| R1 | `4d_system/brain/auto_experiment.py:83` | get_pending_hypotheses | read | همان | پژوهشی |
| R2 | `4d_system/brain/nodes.py:48` | query_experiments | read | همان | پژوهشی |
| R3 | `4d_system/brain/memory_read_patch.py:68/84` | query_experiments · get_pending | read | همان | **WIRED در automation×4** (377/436/467/623) |
| W7 | `_ops/c6_trigger.py:221` (caller: `brain_worker.py:303` با `state_dir=opslib.STATE_DIR`) | `class MemoryStore` (graded, FSM: PENDING/ADMITTED/RETRACTED) | write | **`_ops/state/memory/memory.db` = canonical** | کانونی |
| W8 | `_ops/outcomes/verdict_recorder.py:162` | `class MemoryStore` + `MemoryGate` + `DecisionReceiptStore` | write | canonical + receipts.db | کانونی — **گیت‌دار و receiptدار** (کامنت C7-S2) |
| W9 | `_ops/memory/self_loop_ingest.py` | ingest خام | write | `self-loop-ingest.jsonl` (raw، نه DB) | خام |
| R4 | `_ops/memory/owner_recall.py` | خواندن ingest + memory | read | raw + canonical | **READABLE — اصلاح حکم R01** |
| R5 | `_ops/memory/retrieval_router.py` | مسیریابی بازیابی | read | canonical | بازیابی |

## ۲. حکم دو «bypass» گزارش‌شده (شرط پذیرش P1 مالک)

```yaml
c6_trigger.py:221:       NOT_A_BYPASS — می‌نویسد از طریق graded MemoryStore به canonical،
                         با state_dir تولیدی = opslib.STATE_DIR (caller: brain_worker.py:303)
verdict_recorder.py:162: NOT_A_BYPASS — همان مسیر + MemoryGate + DecisionReceipt
                         (رسید الزامی روی مسیر زندهٔ رأی؛ کامنت C7-S2/GAP-2/GAP-3)
دو store، دو نقش، دو مسیر — بدون تداخل write:
  canonical graded:  _ops/state/memory/memory.db   (483 سطر، FSM admission)
  research/experiments: 4d_system/outputs/4d_experiments.db  (سنگین، حجیم)
```

## ۳. bypass واقعی که پیدا شد (به‌جای آن دو)

```yaml
item: MemoryGate پیش‌فرض خاموش است
evidence: _ops/memory/gate.py:30 FLAG="OCTOPUS_WIRE_MEMORY_GATE"؛
          gate.py:59 فقط با 1/true/yes/on فعال؛ docstring: «پیش‌فرض خاموش → no-op، صفر DB»
impact: مسیر کانونی در حالت پیش‌فرض بدون اعمال FSM گیت کار می‌کند
P2-action: تست‌ها در worktree با FLAG=1 اجرا می‌شوند؛ روشن‌کردن live = فقط مراسم
           OWNER_PROMOTE_CORE_LIVE_1 (طبق NOT-YET-AUTHORIZED مالک)
second_gap: contradiction_radar.py فقط در تست‌ها استفاده می‌شود — در جریان gate.py
           統合 نشده → ادغامش بخش P2 است (تنها تکهٔ واقعاً جدید)
```

## ۴. گزارش واقعیت اصلاح‌شده (طبق فرمان مالک — عیناً)

```text
memory_read_patch = WIRED              (automation.py ×4 + تست‌های C012/R16)
self-loop-ingest  = READABLE           (owner_recall.py) — «write-only» R01 رد شد
learning_engine   = NOT_RUNNING while 4d is down
4d daemon         = PROTECTIVE_HALT 2026-08-16T15:39:45+10:00 (لاگ: TCB trust-boundary
                    violation → «daemon: protective HALT (invariant violation) → stopping»؛
                    ticks=448 · proposals=0 · errors=0 · یک decision-packet [approve]
                    در صفِ not-configured ماند)
پاکیت service-inventory 2026-08-18T02:40 برای 4d_daemon PID=24588 ثبت کرده که با لاگ‌ها
تأیید نمی‌شود (جدیدترین لاگ = Aug 16) → UNKNOWN/UNVERIFIED ثبت شد.
```

## ۵. شواهد اجرایی

- نویسنده/خواننده‌ها: p1-writer-reader-census.txt (A–E) · p1b-wiring-check.txt (F–H)
- هویت bypassها: p1c (I–K) · پشتهٔ گیت و مسیرها: p1d (L–O), p1e (P–T)
- فلگ گیت + لاگ دیمون: p1f (U–W) — شامل tail کامل لاگ HALT
- همه فقط-خواندن؛ صفر نوشتن خارج از پوشهٔ شاهد؛ صفر شبکه.

## ۶. باقی‌مانده برای گیت P1 (بعد از این گزارش)

1. تست ماشین‌نما (machine-check) برای «هیچ direct-open ناشناخته به canonical» — یک تست که هر `sqlite3.connect`/`MemoryStore(path=…)` خارج از `_ops/memory/memory_store.py` به مسیر canonical را رد کند (در worktree، همراه P2).
2. ادغام contradiction_radar در جریان گیت (P2).
