# tests/README — runnerهای صادق (2026-07-20)

> قانون: عددِ تست فقط وقتی معتبر است که فرمان + خروجی واقعی کنارش باشد (DL-2026-07-20-TESTS).
> هیچ suite ای توکن تلگرام یا شبکه نمی‌خواهد؛ همهٔ state در tmp هدایت می‌شود.

## چهار runner (CWD مهم است)

```bash
# ۱) suite اصلی — از ریشهٔ پروژه (این پوشه‌ی tests/):
cd "<project-root>"
python -m pytest tests/ -q

# ۲) استودیو — حتماً CWD=studio (به‌خاطر __init__.py، import از ریشه کار نمی‌کند):
cd studio
python -m pytest test_creator_studio.py test_creator_brain.py test_affirm.py -q

# ۳) مغز/پایپ‌لاین — CWD=brain:
cd brain
python -m pytest test_acquisition_pipeline.py test_learning.py -q

# ۴) کاکپیت — CWD=langar:
cd langar
python -m pytest test_langar.py test_pf_admin.py -q
```

## STOP-ORGANISM سراسری

- `_global_stop()` در langar/studio با walk-up به **اولین** `_ops` والد می‌رسد. در worktree، `_ops` خودِ worktree است (بدون STOP) → تست‌ها پاک اجرا می‌شوند.
- اگر suite را از **درخت زنده** (`F:\backup`) اجرا کنی و `_ops/STOP-ORGANISM` فعال باشد: تست‌های halt/resume استودیو fail می‌شوند چون **STOP واقعاً کار می‌کند** — این شکستِ درست است، نه باگ. STOP را برای سبز کردن تست حذف نکن؛ تست STOP-سراسری در `tests/test_state_machines.py` با monkeypatch پوشش داده شده.

## نقشهٔ suiteها

| فایل | موضوع |
|---|---|
| `tests/test_orchestrator_compliance.py` | fail-closed بودن compliance از manifest (فیکس بای‌پس 07-20) |
| `tests/test_orchestrator_standalone.py` | بوتِ orchestrator بدون `_ops/neural` (fallback stdlib) |
| `tests/test_state_machines.py` | گذارهای غیرقانونی acq/dm/studio + dedup + dryrun + audit + LinkState + KPI funnel + ChannelLocks fail-closed + STOP سراسری |
| `tests/test_dm_hitl.py` · `test_warmup_guard.py` · `test_warning_kill.py` · `test_langar_failclosed.py` · `test_store.py` · `test_layer2_integration.py` | safety nets و DataSpine (موج 07-16) |
| `studio/test_creator_studio.py` · `test_creator_brain.py` · `test_affirm.py` | UI/مغز Creator (نام‌های قدیمی فایل‌ها در 07-20 rename شدند — aliasهای کلاس/متد/env قدیمی هنوز کار می‌کنند) |
| `brain/test_acquisition_pipeline.py` · `test_learning.py` | pipeline اکتساب + بندیت |
| `langar/test_langar.py` · `test_pf_admin.py` | opsec fail-closed، kill، cost، /pf_* |

نکته: `test/` (مفرد، بدون s) پوشهٔ تست نیست — ۸ عکس در آن است (پروندهٔ PII: ‏DL-2026-07-20-PII-INCIDENT).
