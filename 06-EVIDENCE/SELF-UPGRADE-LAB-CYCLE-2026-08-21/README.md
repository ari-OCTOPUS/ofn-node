---
type: evidence
status: active
tags: [self-upgrade-lab, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# SELF-UPGRADE LAB CYCLE — 2026-08-21

اثبات AGI / consciousness نیست. `LAB_PASS` یعنی تست هدف در worktree سبز شد، نه بستن حلقه در L6.

نوت دانش: [[../../07 - Knowledge/شناخت-اختاپوس/79-SELF-UPGRADE-LAB-CYCLE-2026-08-21|نوت ۷۹]]

## نتیجهٔ سیکل (worktree)

| لایه | تصمیم | شاهد |
|------|--------|------|
| memory | `ALREADY_FIXED` | `test_memory_gate` ۱۲/۱۲ روی HEAD |
| heart | `LAB_PASS` | شاخه `sul/heart-c1` کامیت `0dabb28` |
| brain | `LAB_PASS` | شاخه `sul/brain-c1` کامیت `1a6b433` |

Worktree با `--no-checkout` + sparse مخروط `_ops` ساخته می‌شود (checkout کامل vault بیش از ۱۳ دقیقه طول می‌کشید).

## ادغام زنده (بعد از LAB_PASS)

- `observe_only` روی `_ops/orphan_watchdog.py` و هوک observe در `_ops/organism.py`
- تست‌های t_g / t_h در `_ops/tests/test_orphan_watchdog.py`
- `_ops/tests/test_improve_reads_calibration.py` روی live (improve از قبل calibration می‌خواند)

`test_improve_reads_calibration.py` هنوز در `run_all.py` ثبت نشده — نام را گزارش کن؛ خودت به WORKLOCK دست نزن.

## این بسته

- `LAB-CYCLE.json` — خلاصهٔ milestone بدون stdout تست
