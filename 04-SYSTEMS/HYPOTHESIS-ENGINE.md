---
type: system-note
system: hypothesis-engine
created: 2026-08-15
sources:
  - "03 - Projects/research-spec-compiler/adr/ADR-037-hypothesis-engine.md"
  - "OCTOPUS/CURRENT-TRUTH.md (بخش 2026-08-13)"
  - "اجرای زندهٔ pytest در _ops/hypothesis_engine (2026-08-15)"
status: mixed — کد موجود، سوئیت تست در این محیط broken
---

# HYPOTHESIS-ENGINE — موتور فرضیه (ADR-037)

- **ADR:** `03 - Projects/research-spec-compiler/adr/ADR-037-hypothesis-engine.md` ✅ موجود
- **کد:** `_ops/hypothesis_engine/` — شامل `experiments/deceptive_grid.py`، تست‌ها در `tests/`
- **ADR-037 amend (CURRENT-TRUTH 2026-08-13):** `epistemics/schemas.py` دومین کابینِ Pydanticِ `_ops`

## چارچوب deceptive-grid (ادعای CURRENT-TRUTH)

۹ سناریو + ablation + red-team + verdict V0–V4 + JSONL provenance · «۵ سوییت سبز» · committed با رأی git «هردو»

## ⚠️ راستی‌آزمایی زنده (2026-08-15) — شکست

```
$ cd _ops/hypothesis_engine && py -m pytest -q
ImportError: cannot import name 'falsified_assists_at' from 'deceptive_grid'
  (F:\backup\_ops\hypothesis_engine\experiments\deceptive_grid.py)
1 error in 0.47s
```

- بازتولیدپذیر در همین محیط (Python 3.13 سراسری، بدون venv اختصاصی)
- احتمال: env-drift یا تغییر کد پس از اجرای سبز
- **تعمیر نشد** — کدنویسی خارج از مرز مأموریت است → [[../01-TRUTH/CONTRADICTIONS.md|C-003]] · پیشنهاد در [[../07-HANDOFF/NEXT-AGENT-HANDOFF.md|HANDOFF]]
- ادعای «۵ سوییت سبز»: `status: unverified`
