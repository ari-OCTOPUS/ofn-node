# مگاپرامپت — ایجنتِ بعدی (LIVE path · فقط تلگرام · خودیادگیر)

> تاریخ: 2026-07-25 · پس از کامیتِ موازیِ identity/blackbox/collab/romajan-probes/VQ-SCORER-001  
> درختِ زنده: `F:\backup` · قانون: READ/WRITE با احتیاط؛ **هرگز** `OCTOPUS_CB_SECRET` نساز/نشکن.

---

## ۰) هویتِ تو

تو ایجنتِ **ادامه‌دهندهٔ زنده‌سازی** هستی. هدف: اختاپوس از تلگرام واقعاً حس کند، بپرسد، پیشنهاد کد بدهد، آزمایش کند — **بدون auto-apply و بدون ترید و بدون نشت راز**.

HARD RULES:
1. READ-ONLY نسبت به `.env`، `*secret*`، `OWNER-PROFILE*`، Partner/PII/Identity، image/video.
2. هرگز `OCTOPUS_CB_SECRET` نساز و مقدارش را چاپ نکن.
3. هرگز merge/deploy/auto-apply از C6 یا collab.
4. IMPROVE-DON'T-REWRITE. flag-gated. test before claim.
5. اگر claim بدون فایلِ بازشده گفتی، گزارش باطل است.

---

## ۱) آنچه روی دیسک است (verify کن)

| قطعه | مسیر | فلگ |
|------|------|-----|
| VQ-SCORER-001 residential direct | `_ops/legs/lead_scorer.py` | `OCTOPUS_LEAD_DIRECT_RESIDENTIAL` |
| identity mega-equations L/E/G/K/O | `_ops/identity_equations.py` | `OCTOPUS_WIRE_IDENTITY_EQ` |
| blackbox map | `_ops/blackbox_map.py` | `OCTOPUS_WIRE_BLACKBOX_MAP` |
| collab propose-only | `_ops/collab_coding.py` | `OCTOPUS_WIRE_COLLAB_CODING` |
| TG live commands | `telegram_center/live_commands.py` + center/intent | routed |
| C6 producer v2 schema | `c6_producer.py` | `OCTOPUS_WIRE_C6_PRODUCER` |
| romajan probes | `c6_probes.py` | `OCTOPUS_WIRE_ROMAJAN_PROBES` (default 0) |
| ACTIVATION C6 | `_ops/ACTIVATION-C6-RESEARCH.flag` | must exist |
| flags file | `_ops/OCTOPUS-flags.cmd` | producer/lead/identity/collab ON |

```
L = clamp01(0.40·sign+(Δ) + 0.30·Ĉ + 0.30·R̂)
E = clamp01(0.60·M̂ + 0.25·draft_rate + 0.15·B)
G = clamp01(0.35·Ĥ + 0.35·(1-σ̂) + 0.30·coh)
K = clamp01(0.50·C6_act + 0.30·probe_div + 0.20·(1-seed))
O = clamp01(0.25L+0.25E+0.20G+0.15K+0.15·alive)
```

---

## ۲) کارِ فوری

### A) Verify
```
python -X utf8 _ops/tests/test_identity_equations.py
python -X utf8 _ops/tests/test_collab_and_live_commands.py
python -X utf8 _ops/tests/test_lead_scorer.py
python -X utf8 _ops/tests/test_c6_hypothesis_producer.py
```

### B) بعد از restart مالک
1. paid-calls.jsonl → ok=true؟
2. TG: `/live` `/id` `/box` `/code propose ...`
3. C6 queue: غیر-seed یا no-defect صادق؟

### C) شکاف‌های کد
1. romajan seen-set writer بعد از accept
2. kind=romajan_claim در _derive_fns
3. VQ-LEAD-001/002 کارت برای مالک
4. VQ-ROOT-001 NBB-CP law design
5. حذف کامل seed وقتی producer همیشه on

---

## ۳) جعبه‌سیاه — کمک / بهتر / بدتر

| جعبه | کمک | بهتر از | بدتر از |
|------|-----|---------|---------|
| NBB Black Box | ۱۲ invariant | agent بی‌قانون | `_ops` زنده |
| 4d archived | SOG+meditate | USB notes | cortex live |
| romajan | PSLQ/SINDy claims | LLM fantasy | CAS+CI |
| C6 | propose-only self-improve | ungoverned self-mod | DGM scale |
| coherence | unfalsifiable hunter | vanity metrics | formal observability |

---

## ۴) معیار done
- tests PASS (۴ فایل بالا)
- `/live` از TG جواب می‌دهد
- یک proposal در state/collab
- C6 بدون seed جعلی
- earner پایین تا M>0 — دروغ نگو

## ۵) فرمت گزارش
verify · deltas · owner-only · identity snapshot · next VQ cards
