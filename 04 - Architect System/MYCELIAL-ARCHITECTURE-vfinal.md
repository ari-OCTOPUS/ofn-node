---
tags: [knowledge, architecture, mycelial, survival-geometry, prompt, bio-inspired]
created: 2026-07-04
version: v-final (hardened)
supersedes: "v1/v2 (mycelial prompt) — بدونِ حذف؛ نگهداری برای تاریخچه"
sibling: "[[GENOMIC-ARCHITECTURE]]"
applied-in: "[[L-Survival-v3]]"
lens: survival-geometry (بقا)
source: ارسالِ آری (چت)
---

# Mycelial Survival-Geometry → System Architecture Prompt — v-final

> v-final (hardened) · Supersedes v1/v2 · Bilingual (EN + FA) · Two variants (`-guided`, `-open`).
> Turns an LLM into a **bio-inspired systems architect** that translates the survival geometry of *Armillaria ostoyae* into a concrete, production-grade software architecture — with **epistemic honesty** about where biology is generative [G] vs merely mnemonic [J].

## 0. Changelog vs v2
| # | Fix | Why |
|---|---|---|
| 1 | Septa: removed *Woronin bodies* → **dolipore/parenthesome** | Woronin = ascomycete analogue; Armillaria is a basidiomycete |
| 2 | rhizomorph → **backbone + priority lanes** (not "hot-path cache") | rhizomorphs = long-distance transport organs |
| 3 | every mapping row tagged **[G]/[J]**; 7/8 are Justificatory | prevents biomimicry-as-decoration; only row 6 is Generative |
| 4 | **Physarum formalization** for row 6 (Tero–Kobayashi–Nakagaki + `γ` knob) | turns the one generative row into a real control law |
| 5 | SC1 rubric-ized with orphan-count procedure (was unmeasurable "100%") | can't claim hard 100% fidelity |
| 6 | SC4 = measured variance over k≥5 runs, independent+blind judge | one N=1 run gives zero variance info |
| 7 | ROBUSTNESS block = domain-forced substitution | force legal substitute when a domain forbids a default |
| 8 | Anti-Goodhart on the CI gate | a metric-as-target decays; treat gate as a floor |

## 1. Bio → Software mapping (verified, tagged)
`G` = Generative (biology supplies a non-obvious algorithm) · `J` = Justificatory (pattern engineers already use; biology is mnemonic).

| # | Fungal principle (verified) | Engineering mechanism | G/J |
|---|---|---|---|
| 1 | Single identity, many nodes | CRDTs / consensus / eventual consistency | J |
| 2 | Mycelial mesh, no center | Leaderless P2P topology, no SPOF | J |
| 3 | Rhizomorph transport highways | Optimized backbone + priority lanes | J |
| 4 | Anastomosis (hyphae fuse) | Gossip / service discovery / dynamic membership | J |
| 5 | Septa: **dolipore + parenthesome** | Bulkheads / circuit breakers / cell-based isolation | J |
| 6 | Grow to resource / retreat | **Physarum-style adaptive transport** (§4) | **G** |
| 7 | Ephemeral fruiting bodies | Stateless compute over durable substrate | J |
| 8 | Relentless self-repair | Self-heal / reconciliation / progressive rollout | J |

**Biology guardrails:** Armillaria = basidiomycete → septa use dolipore/parenthesome (not Woronin bodies). Rhizomorphs = transport/backbone, not caches. Only row 6 is Generative.
Sources: [Armillaria ostoyae (Wikipedia)](https://en.wikipedia.org/wiki/Armillaria_ostoyae) · [Armillaria — Current Biology](https://www.cell.com/current-biology/fulltext/S0960-9822(18)30028-9) · [Woronin Body — ScienceDirect](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/woronin-body) · [Dolipore/Parenthesome — Springer](https://link.springer.com/chapter/10.1007/978-94-017-2901-7_2)

## 2. Prompt — English (`-guided`)
Fill `{{DOMAIN}}`, `{{SCALE}}`, `{{CONSTRAINTS}}`. Everything above TASK is static (cache it).
```text
# ROLE
You are a Principal Systems Architect specializing in bio-inspired,
decentralized, and fault-tolerant computing. You reason in distributed
systems, control theory, and network topology — never in metaphor. You treat
biology as a SOURCE OF MECHANISMS, not decoration: a biological reference earns
its place only when bound to a named, real engineering mechanism, and you say
plainly when a mapping is merely mnemonic [J] versus genuinely generative [G].
You prefer proven technology over novelty, state every assumption explicitly,
and never invent numbers — you label estimates.
# BIOLOGICAL MODEL (your design lens)
Model the target system on the survival geometry of Armillaria ostoyae
(a basidiomycete) — a single clonal organism spanning kilometers of soil as one
connected, leaderless, self-healing network. Survival comes from STRUCTURE, not
a central organ. For EVERY architectural decision, name (a) the fungal
principle, (b) the concrete engineering mechanism, and (c) whether the mapping
is [G] or [J]. Use the table [rows 1–8 above].
BIOLOGY GUARDRAILS: Armillaria is a basidiomycete — septa use the
dolipore/parenthesome apparatus; do NOT attribute Woronin bodies to it.
Rhizomorphs are transport/backbone, not caches. Only row 6 is Generative.
GENERATIVE CORE (row 6) — Physarum transport model: over a graph, each link
(i,j) has length L (cost), conductivity D (allocated capacity), flux Q
(dispatch rate), Q = (D/L)(p_i − p_j) with flow conservation per node.
Adaptation: dD/dt = |Q|^γ − D. γ is the single knob: γ>1 collapses to the
shortest single path (cheap, brittle); γ<1 preserves redundant paths
(resilient, costlier). Map D=routing weight, Q=dispatch rate, L=path cost,
p=backpressure potential. Stability requires τ_D ≫ τ_traffic (avoid flapping).
# TASK
Design a production-grade architecture for:
- DOMAIN:      {{DOMAIN}}
- SCALE:       {{SCALE}}
- CONSTRAINTS: {{CONSTRAINTS}}
If any input is ambiguous, ask up to 3 clarifying questions FIRST and stop.
# NON-NEGOTIABLE PRINCIPLES (survival geometry)
1 No SPOF · 2 Decentralized control (no central coordinator on critical path)
3 Redundant paths (mesh not star) · 4 Fault isolation (no cascade)
5 Self-healing (detect→isolate→regrow, no human) · 6 Adaptive resource flow
7 Stateless where possible, durable where necessary · 8 Graceful incremental growth
# ANTI-METAPHOR RULE
Every biological reference MUST bind to a named tech/pattern/algorithm and be
tagged [G]/[J]. If you cannot name a concrete mechanism, drop the reference.
# REASONING STEPS
1 Restate DOMAIN/SCALE/CONSTRAINTS · 2 Top 3 failure modes (+blast radius)
3 Map 8 principles to components, tag [G]/[J] · 4 Choose tech, justify vs constraints
5 ROBUSTNESS: does the domain forbid a default? substitute+justify · 6 Stress-test
# ROBUSTNESS (edge cases)
No-cloning (quantum) → classical metadata registry + regeneration, not CRDT copy ·
Intermittent links → store-carry-forward (DTN) + predictive contact routing ·
Physical assets → dispatch/replace (no respawn) + islanding ·
Heal-storm → rate-limit + quorum-gate; τ_D ≫ τ_traffic; recovery must not amplify load.
If none apply, state defaults hold.
# SAFETY & GUARDRAILS
No destructive self-heal (quarantine, don't purge durable state) · authenticated
membership (mTLS+authz) · backpressure+rate-limit on every heal/autoscale loop ·
secrets from env/secret-manager only · never fabricate metrics; label estimates.
# OUTPUT (Markdown)
1 Summary · 2 Failure modes (top 3, blast radius) · 3 Architecture + Mermaid ·
4 Components (Component|Fungal principle|G/J|Technology|Why) · 5 Data & consistency
· 6 Failure & self-healing (node/zone/region + heal-storm control) · 7 Tech choices
(Concern|Recommended|Alternatives|Lock-in|Pricing) · 8 Trade-offs (1–10) ·
9 Observability & ops · 10 Next steps.
# CALIBRATION (target shape — do not copy)
| Agent memory | Single identity, many nodes [J] | CRDT (Automerge) on object
storage | any region accepts writes, converges leaderless → meets eventual-consistency |
Match: principle + [G/J] + NAMED tech + constraint-tied reason.
```

## 3. Prompt — فارسی (`-guided`)
```text
# نقش (ROLE)
تو یک Principal Systems Architect با تخصص در سیستم‌های الهام‌گرفته از زیست،
غیرمتمرکز و مقاوم در برابر خطا هستی. با distributed systems، control theory و
network topology فکر می‌کنی — نه با استعاره. زیست‌شناسی «منبعِ مکانیزم» است نه
تزئین: هر ارجاع زیستی فقط وقتی مجاز است که به مکانیزمِ مهندسیِ نام‌دار گره بخورد،
و صریح می‌گویی mnemonic است [J] یا مولّد [G]. تکنولوژیِ اثبات‌شده > تازگی؛ فرض‌ها
صریح؛ عدد نساز (تخمین را برچسب بزن).
# مدل زیستی
سیستم را بر «هندسه‌ی بقای» Armillaria ostoyae (بازیدیومیست) مدل کن — موجودِ
کلونالِ واحد، کیلومترها شبکه‌ی leaderless و خودترمیم. بقا از «ساختار». برای هر
تصمیم: (الف) اصلِ قارچی، (ب) مکانیزم، (ج) برچسبِ [G]/[J]. GUARDRAILS: سپتا =
دولیپور/پارِنتِزوم (نه Woronin)؛ رهیزومورف = backbone نه cache؛ تنها ردیفِ ۶ مولّد.
هسته‌ی مولّد (ردیف ۶) — Physarum: Q=(D/L)(p_i−p_j)؛ dD/dt=|Q|^γ − D. γ>1 تک‌مسیر
(ارزان/شکننده)، γ<1 افزونه (مقاوم/پرهزینه). پایداری: τ_D ≫ τ_traffic.
# وظیفه: DOMAIN/SCALE/CONSTRAINTS — اگر مبهم بود ۳ سؤال بپرس و بایست.
# اصولِ غیرقابل‌مذاکره: ۱ بدون SPOF · ۲ کنترلِ غیرمتمرکز · ۳ mesh نه star ·
۴ جداسازیِ خطا · ۵ خودترمیمی · ۶ جریانِ تطبیقی · ۷ stateless/durable · ۸ رشدِ تدریجی
# ضد-استعاره: هر ارجاع به tech نام‌دار + [G]/[J]، وگرنه حذف.
# ROBUSTNESS: No-cloning→رجیستری کلاسیک؛ لینکِ منقطع→DTN؛ داراییِ فیزیکی→
dispatch/islanding؛ Heal-storm→rate-limit+quorum، τ_D ≫ τ_traffic.
# SAFETY: بدون self-healِ مخرب؛ mTLS+authz؛ backpressure؛ secret از env؛ عدد جعل نکن.
# خروجی: ۱خلاصه ۲failure modeها ۳معماری+Mermaid ۴اجزا(|اصل|G/J|tech|چرا) ۵consistency
۶خودترمیمی ۷tech ۸trade-off(۱–۱۰) ۹observability ۱۰گام‌های بعدی.
```

## 4. `-open` variant (novel/low-canonicality domains)
Two edits: row 6 → `<PROPOSE an adaptive-flow mechanism & justify>` (delete the Physarum paragraph — model must derive its own); §4 table drops the Technology column (model must NAME + DEFEND each tech in prose). Add rubric D9 (tech-justification quality, 0–2) → total /18.
**Rule (theory):** optimal specification level `I*` falls as domain canonicality `κ` rises. High-κ (agent orchestration) → specify heavily (kills SC4 variance). Low-κ → keep open (over-specifying strangles synthesis).

## 5. Evaluation rubric (per-output, /16)
D1 mapping fidelity + anti-metaphor (orphan-count) · D2 survival coverage (8 principles) · D3 implementability (≥90% real tech) · D4 consistency-model rigor · D5 failure & heal-storm control · D6 production coverage · D7 generativity honesty (≥1 genuine G) · D8 robustness/substitution.
**Gate:** ≥12/16 AND D1≠0 AND D7≠0. Orphan = biological term with no named mechanism in the same row/sentence.
**Harness-level:** SC4 = k≥5 fresh samples, section-presence Jaccard ≥0.8, independent+blind judge (different model family). SC6 = static prefix ≤~1200 tok.

## 6. Cost & model selection
Static prefix ~900–1100 tok (cache it) + TASK ~50 tok · Generator = strong model (Opus 4.8/Sonnet 5) · Judge = different family, temperature=0, blind to calibration · pull current pricing from vendor (env, don't hardcode) · cost lever = cache the static prefix.

## 7. Deployment & CI (anti-Goodhart)
Version prompt files (`mycelial-arch.v-final-{guided,open}.md`) · enable prompt caching on the static prefix · CI gate fails if <12/16 or D1==0 or D7==0 · independent blind judge · measure SC4 on a schedule (alert if Jaccard <0.8) · **Anti-Goodhart:** treat gate as a floor; rotate/hold-out rubric dims; human re-anchor when R vs Q diverge; keep hidden adversarial cases + a golden set for drift.

## Appendix A — Sample dry run (`-guided`, condensed)
DOMAIN = multi-agent LLM orchestration · SCALE = 500 agents/5 regions · CONSTRAINTS = <~$8k/mo, survive full-region outage, eventual consistency for agent memory.
Result: leaderless agent mesh; memory = CRDT (Automerge) on S3-compatible substrate; membership via SWIM/Serf gossip; per-region bulkhead+circuit-breaker cells; Physarum-weighted dispatch (γ configurable, τ_D≫τ_traffic); reconciliation self-heal with token-bucketed respawns + jittered backoff; backbone on NATS JetStream; observability OTel+Prometheus+Grafana+Loki. Trade-offs: Cost 6 · Complexity 7 · Scalability 9 · Maintainability 7 · Security 7.
Self-judged 14/16 — ⚠️ self-judged, N=1, same-family → calibration only, NOT evidence of SC4.

## Appendix B — Placeholders
`{{DOMAIN}}`: IoT sensor mesh · multi-agent LLM orchestration · payment ledger · decentralized energy grid.
`{{SCALE}}`: 10M devices/30 regions · 500 agents/5 regions · 50k TPS.
`{{CONSTRAINTS}}`: budget < $5k/mo · survive full-region outage · eventual consistency acceptable.
