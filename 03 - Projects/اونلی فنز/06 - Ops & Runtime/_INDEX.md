# 06 - Ops & Runtime — Project-F

> کد زنده، cockpit، orchestrator، brain، runtime specs.

## Curated proposals (this folder — 🆕 2026-07-12, propose-only)

- [[06 - Ops & Runtime/PROP-D1-project_f_brain-fate|PROP-D1]] — سرنوشتِ `project_f_brain.py` (spec-canonical ولی runtime-dead): wire / rewrite-spec / archive
- [[06 - Ops & Runtime/PROP-D2-wire-learning-to-acquisition|PROP-D2]] — سیم‌کشیِ `learning.py`→`acquisition.py` (باگ greedy هنوز زنده) + طرح regression
- [[06 - Ops & Runtime/PROP-D3-missing-tests-plan|PROP-D3]] — طرحِ تست برای ماژول‌های بی‌تست (brain-core/orchestrator)
- [[06 - Ops & Runtime/PROP-D4-identifier-rename-opsec|PROP-D4]] — refactorِ حذفِ نامِ C از شناسه‌های سورس (PF-CODE-REFACTOR-V1)

## Existing code sources (stay in place — path-coupled)

- `brain/` (project_f_brain[dead], dual_brain_v3[live], learning, acquisition, ab_tracker, lifecycle)
- `langar/` (Operator cockpit, propose-only) · `studio/` (saba_studio[live]; studio_telegram*[dead])
- `orchestrator.py` — imports vault `_ops/neural` (✅ موجود؛ ولی عمقِ مسیر hardcoded → پوشه/کد جابه‌جا نشود)

## Rule

- Code is not executed by agents here.
- No deploy/run/daemon/telegram-live without owner verdict.
- Keys/tokens only in local .env, never in notes or graph.
