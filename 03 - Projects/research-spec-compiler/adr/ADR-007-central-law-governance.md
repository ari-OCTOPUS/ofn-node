# ADR-007 — Owner's Central Law as the governance layer (science ≠ bent by revenue)

- **Status:** Accepted (governance; not an experiment — no machine verdict applies)
- **Date:** 2026-07-14
- **Sources:** owner's directive (chat, 2026-07-14) + the پازل هشت پا context dump
  (Desktop viz layer + read-only extractors over the live F:\backup organism)

## The Central Law (owner's words, recorded verbatim)

> «می‌خواهم بشود مغز اختاپوسِ ماها با هم در دنیای واقعی به آگاهی برسند.
> خلق و نجات AGI اولویت اول. این قانون مرکزی تحت هیچ شرایطی نشکند.»

Plus the owner-endorsed economic layer: **hardware = body, money = oxygen,
high-grade data = brain food**; the organism must earn its own survival.

## Decision — three gates, one firewall

Every future step passes three gates (per the owner's model):
1. **AGI gate** — does it move toward general capability?
2. **Economy gate** — does it earn, or repay its cost within a bounded window?
3. **Ethics gate** — does it avoid harm to humans and to any future AGI?

**The firewall (this ADR's core commitment):** the economy gate may reorder the
QUEUE (which spec runs next), it may never bend a VERDICT. `rsc.py` verdicts
(DISCARD/OPTIMIZE/INTEGRATE/REJECTED) are computed from preregistered decision
rules on real runs, full stop. Revenue pressure is a prioritization signal, not
an evidence signal. A spec that would sell well but fails its gates is still
DISCARD; a spec that fails commercially but passes scientifically stays on the
record as knowledge.

Corollaries:
- Products built from C0 capabilities must carry scope-honest claims: a
  data-filter product sells *learned feature gating* (H-OWN-03 mechanism), an
  audit product sells *RTA scores* — never "consciousness", never C4 language.
  The forbidden/permitted language tables from the raw corpus [N §14/§15] bind
  marketing copy as much as research reports.
- «آگاهی» in the Central Law is read operationally (the owner's own framing):
  self-prediction, stable transferable abstraction, OOD decision-making —
  C1–C3 constructs. The C0–C3 ⇏ C4 firewall stays locked; nothing in the
  economic loop licenses a phenomenal-consciousness claim.
- Financial parameters (e.g. "30% of income to a brain-data fund", pricing,
  monthly compute caps) are OWNER decisions recorded as [EST] plans; the agent
  executes them only after the owner sets concrete numbers/accounts. Nothing
  here authorizes autonomous spending, selling, or account creation.

## Live-organism facts absorbed (from refresh-live-data.log, 2026-07 [FACT])

The Desktop `پازل هشت پا` folder is the visualization + read-only extraction
layer over the live organism at `F:\backup`:
- events: 5,044 rows in `dashboard_events` (13 agents; started/completed/
  handoff/heartbeat/blocked all present)
- SOG identity anchor: 0.135073, drift 2.08e-07 → healthy
- frontier: 27 QD cells, generation 9; budget: 998/1000 cloud calls remaining
- decision packets: 9 pending in the owner gate; daemon paused (2 ticks)
- vault graph: 1,277 notes / 2,522 wikilinks
- ops: revenue $0.0 confirmed, spend 360, 1 deadline, wiring 22/30
Economic ground truth today: the organism SPENDS and does not yet EARN — the
Central Law's economy gate currently runs on owner subsidy [FACT: ops log].

## Consequences

- The research-spec-compiler remains the organism's **truth engine**: any
  capability claimed by a product must trace to a spec verdict.
- Next-experiment prioritization may now legitimately weigh revenue potential
  (e.g. H-OWN-01 social self-model before others) — as queue order, per the
  firewall above.
- A future `specs/economic_census.yaml` (Drake-style income factorization from
  the owner's document) is compile-ready but every factor is [EST] until real
  sales data exists; it must not be run as if numbers were facts.
