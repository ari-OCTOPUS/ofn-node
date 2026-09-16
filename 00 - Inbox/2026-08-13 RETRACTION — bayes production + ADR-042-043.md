---
type: retraction
status: active
created: 2026-08-13
created_by: agent
tags: [octopus, bayes, telegram, nase, adr-042, adr-043]
---

# پس‌گیری و ADR-042/043 — 2026-08-13

## پس‌گیری `bayes.py` به‌عنوان استدلال زنده

`production_caller: NOT_FOUND`.

شاهد `rg` روی `_ops`, `4d_system`, `03 - Projects` (خروجی قبل از git-hang):

- `_ops/epistemics/benchmark.py:27` `from .bayes import update_bayesian`
- `_ops/epistemics/benchmark.py:323` `from .bayes import posterior_from_delta`
- `_ops/tests/test_epistemic_bayes.py:21` `import epistemics.bayes as B`

`wiring.epistemics_beat` (`wiring.py:1154`) → `run_offloop.compute_all` نه bayes.
`epistemics/__init__.py` bayes را eager-import نمی‌کند.

ثبت: `_ops/capabilities/bayes-engine.json` status=hypothesis.

اطلس `00 - Inbox/2026-08-13 SELF-CONTAINED — Math Atlas Complete for Research.md` خانوادهٔ ۷ بند ۲۱ را برای **production apply** نباید خواند.

اسکن کل دیسک خارج این سه ریشه: **NOT VERIFIED** (timeout).

## ADR-042 Phase 0

`proven_rate=0.0` = هیچ `topic_id` لیترال؛ نه «ارسال هرگز فایر نشده».
هوک روی دو فرستنده (نه ۸۴ پچ `center.py`). فلگ `OCTOPUS_TG_SITE_FIRE_LOG=1`.
۴۸ ساعت هنوز نگذشته — `python _ops/scripts/tg_site_fire_report.py`

## ADR-043

روی همان ۱۰۰ ردیف: min 6µs · median 11.5µs · max 9.726ms · stdev 971µs.
طبق شرط پذیرش: نسبت به ضربان سیستم stdev≈0 → ساعت‌ها **مستقل معنادار نیستند** تا خلافش ثابت شود.
