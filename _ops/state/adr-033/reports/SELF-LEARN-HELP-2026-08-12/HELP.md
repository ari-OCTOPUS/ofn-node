# Self-Learn Help — 2026-08-12

## مشکل
- `self_knowledge.understanding = {"failed":1}` در change-gate گیر کرده بود
- `deep_dive_ran=false` · synthesis کهنه (~۱۴h) · research در شل بدون flag

## کمک انجام‌شده
1. **فیکس additive** در `doctor/self_knowledge.py`: `_understanding_usable()` — stubهای `failed/error` دیگر cache نمی‌شوند؛ LLM parse بی‌کلیدِ تشخیصی → heuristic.
2. **self_knowledge refresh:** `source=llm:local` · focus=`خواستهٔ مالک` · `deep_dive_ran=True` · pathology=3
3. **synthesis:** 3 proposal · tier=secondary · ingest commit=3
4. **web_research** (با `OCTOPUS_WIRE_WEB_RESEARCH=1`): 6 hit → memory commit
5. **improve:** 38 proposal · ingest +4 commit
6. **part_loops:** همه 🟢 · **self_model:** 603 / 96.7%

## Trails
| trail | قبل | بعد |
|---|---|---|
| self-loop-ingest | 216 | 233 |
| research-ingest | 9 | 15 |

## مرز
APPLY=0 · may_authorize=false · بدون EXTERNAL_SEND
