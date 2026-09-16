# Migration plan (no deploy)

1. Keep `_ops/shadow_homeostasis` lab-only.
2. Do not import from `organism.py` until owner votes.
3. Optional later: after arbiter.persist, pass color+period into a **shadow** emit (not replacing life_currency.py).
4. T22 jsonl may later sit beside pulse/ as `history/life-currency.jsonl` — requires owner + no cron in this WAVE0.
5. Live C-044 / C-045 code fixes are **out of this slice**.
6. Orange Pi / load generator: never.
7. Close GAP-001 and sign K9 are independent owner acts.

No runtime restart/deploy in this mission.
