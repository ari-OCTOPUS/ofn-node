# Research Sources

Annotated list of every external source WLOS design decisions lean on, with exactly what the product takes from each — and, just as important, what it does not claim. Sources are grouped by type; the final section separates evidence-based claims from product assumptions, because a personal-use tool must not dress engineering choices up as science. No citations beyond those listed here should appear elsewhere in the docs.

## Platform and API references (verified live)

| Source | URL | What WLOS takes |
|---|---|---|
| Sakana Fugu product page | sakana.ai/fugu/ | Model family positioning; `fugu` (default) and `fugu-ultra` (deep) as the two model tiers wired into `FuguProvider` |
| Sakana Fugu release announcement | sakana.ai/fugu-release/ | Released June 2026; capability claims treated as vendor claims, verified by our own eval suites, not assumed |
| Sakana console quickstart | console.sakana.ai/get-started | OpenAI-compatible chat-completions API at base `https://api.sakana.ai/v1`, Bearer auth — verified July 2026; exactly what `packages/fugu-provider/src/fugu.ts` implements (JSON mode, `reasoning_effort`, usage accounting) |
| Telegram Bot API | core.telegram.org/bots/api | `setWebhook` `secret_token` → `X-Telegram-Bot-Api-Secret-Token` header check; `update_id` semantics behind `ProcessedUpdate` idempotency; polling vs webhook modes; the documented fact that bot chats are not E2E-encrypted (see `docs/threat-model.md`) |
| Telegram Mini Apps | core.telegram.org/bots/webapps | `initData` HMAC validation for the sensitive-review surface; keeps high-sensitivity detail out of chat transcripts |

## Clinical and governance guidance

| Source | What WLOS takes |
|---|---|
| NICE guideline **NG246**, behavioural weight-management interventions | Multicomponent posture (diet + activity + behavioural techniques together, never diet alone); realistic rate expectations; very-low-calorie approaches belong under clinical supervision — one root of the 1200/1500 kcal floors and the "refer out, don't treat" stance |
| WHO, *Ethics & governance of artificial intelligence for health* (incl. large multi-modal model guidance) | Human oversight of consequential changes (`SelfModProposal` approval gate), data minimization (packet firewall), transparency (audit tables, confidence labels), and the bright line that AI must not diagnose |
| AGILE JITAI trial design (PubMed Central **PMC11905495**) | JITAI vocabulary made concrete: decision points → `planDay()` slots + fire-time re-evaluation; tailoring variables → `UtilityInputs`; intervention options → question bank + BCT menu; proximal outcomes → `CheckinResponse`/`StateLog`. WLOS borrows the *design frame*, not trial results — n=1 here |
| Behavioral-science agentic nutrition-coaching workflow (PubMed Central **PMC12460921**) | Pattern for LLM agents constrained by behavioral-science structure: vetted technique menus over free generation, structured extraction over chat dumps, safety layer outside the model — mirrored in `comb.ts` + clearance gate |

## Behavioral-science foundations

| Framework / source | Authors | Operationalized in |
|---|---|---|
| COM-B / Behaviour Change Wheel | Michie, van Stralen, West | `Barrier.comb*` columns; `candidatesFor()` in `packages/behavior-engine/src/comb.ts` |
| BCT Taxonomy v1 (BCTTv1) | Michie et al. | `Strategy.bctCode`; the 10-item `INTERVENTION_MENU` |
| Motivational Interviewing | Miller & Rollnick | Reflect/open-question/autonomy reply rules; change-talk detection deferred as future LLM task |
| Self-Determination Theory | Deci & Ryan | Autonomy (skip semantics, no shaming), competence (minimum-dose), relatedness (domain J + BCT 3.1) |
| Implementation intentions | Gollwitzer | If-then `Strategy` rows (BCT 1.4) |
| WOOP (mental contrasting + II) | Oettingen | Weekly-review traversal: goal → obstacle (`Barrier`) → plan (`Strategy`) |
| Relapse prevention | Marlatt & Gordon | Smallest-restart scripts; abstinence-violation pattern caught by `BehavioralFormulation`; `recent_lapse` contraindication |
| Self-compassion | Neff | No-shame recovery language; `shame_language` detection in the content guard |
| EAST framework | Behavioural Insights Team | Easy/Attractive/Social/Timely rejection filter on interventions and prompts |
| Mifflin-St Jeor equation | Mifflin et al. | `bmrMifflin()` in `packages/nutrition-engine/src/calculations.ts`, surfaced honestly as ±~10% |

See `docs/behavioral-science.md` for the full framework → code mapping; a framework with no column, score, or message rule is not claimed.

## Australian crisis and support directories

The crisis flow depends on numbers being *correct*, so they are product configuration (`packages/safety/src/resources.ts`), sourced from the services' own public listings and re-checked on the quarterly cadence:

| Service | Number | Used for |
|---|---|---|
| Emergency services | 000 | `urgent_medical` and imminent-danger framing |
| Lifeline | 13 11 14 | Crisis-level triage responses (24/7) |
| Suicide Call Back Service | 1300 659 467 | Crisis follow-up option (24/7) |
| Beyond Blue | 1300 22 4636 | Mood/anxiety support (24/7) |
| MensLine Australia | 1300 78 99 78 | Men's counselling option |
| Kids Helpline | 1800 55 1800 | Under-25 option |
| Butterfly Foundation | 1800 33 4673 | Eating-disorder-specific support; paired with every ED-category trigger |

Every crisis message also carries the Persian medical disclaimer (`MEDICAL_DISCLAIMER_FA`): WLOS is not a substitute for professional medical, psychological, or dietetic care.

## Product-design references (mechanisms NOT claimed)

These commercial products informed *what problems to solve and how solutions feel* — WLOS makes **no claim** about their internal algorithms and copies none of their implementations.

| Product | Design idea taken |
|---|---|
| MacroFactor | The *concept* of adaptive observed-TDEE from weight trend + logged intake; WLOS's `observedTdee()` is an independent, quality-gated energy-balance estimate |
| Noom | Positioning proof that CBT/ACT-informed framing (not just calorie math) can carry a consumer coaching product; WLOS keeps the framing but stays firmly non-therapy |
| Lark | Conversational, chat-native check-in cadence as the primary interface |
| MyFitnessPal Nutrition Coach | The cost of logging friction; motivation for text-first meal entry and `nameRaw`/`nameKey` reuse |
| HealthifyMe Ria | Existence proof for a non-English-first AI coach; supports the Persian-first decision |

## Evidence-based vs product assumption

| Claim in WLOS | Status | Note |
|---|---|---|
| Mifflin-St Jeor for BMR screening | Evidence-based | Validated equation; WLOS still reports ±10% ranges, never point estimates |
| Multicomponent behavioural intervention > diet alone | Evidence-based (NG246) | Drives the whole behavior-engine investment |
| Protein 1.6–2.2 g/kg during loss | Evidence-informed | Consistent with sports-nutrition literature ranges; anchor 1.8 is a product default |
| Calorie floors 1200 F / 1500 M unsupervised | Convention + product safety choice | Common clinical convention, not individualized medicine; deliberately conservative |
| Deficit ≤25% of TDEE | Product assumption (evidence-informed) | Practice-informed guardrail; exact percentage is ours |
| Safe rate 0.25–0.75% BW/week | Product assumption (conservative) | Literature often cites up to ~1%/wk; WLOS narrows it on purpose |
| **7700 kcal ≈ 1 kg** heuristic | Product assumption, flagged | `KCAL_PER_KG` is a mixed-tissue approximation; real dynamics are non-linear. Used only inside ranged, caveated estimates (`observedTdee` carries its caveat string) |
| Activity factors 1.2–1.9 | Convention | Long-standing multiplier convention; another reason TDEE ships as a range |
| Fiber 25–32 g F / 30–38 g M | Evidence-informed | Aligned with common adequate-intake guidance |
| ±0.15% BW/week trend noise band | Product assumption | Chosen so daily scale noise cannot masquerade as progress or plateau |
| Sensitive-by-default triage (false positives OK) | Product safety choice | A false positive costs one caring message; a false negative can cost far more (`triage.ts` design note) |
| Utility weights & 0.15 send threshold | Pure product assumption | Static config, tunable via `SelfModProposal`; no claimed empirical basis |
| 20 msgs/day cap, 00:00–07:00 quiet, backoff halving | Product assumption | Burden-management engineering informed by EAST/JITAI principles, not derived from any trial |
| Any user-specific `Pattern` (e.g. cannabis → hunger) | Hypothesis only, never evidence | `notCausal=true` by default; requires evidence counts, survives counterexamples, dies on user correction |

## What each source type may justify

To keep claims honest, source types have bounded authority in design discussions:

- **Vendor pages** (Sakana, Telegram) justify *API wiring and platform constraints* only — never capability or quality assumptions, which must come from our own eval suites.
- **Clinical guidance** (NICE, WHO) justifies *guardrails and posture* (floors, referral stance, oversight requirements) — never individualized advice; WLOS is not a medical service.
- **Research papers** (AGILE, agentic-coaching workflow) justify *design frames and vocabulary* — never outcome claims for this user; n=1 outcomes come only from this user's own data under the evaluation plan.
- **Product references** justify *UX direction and problem selection* — never implementation claims about those products.
- **Framework literature** (COM-B through EAST) justifies *structure* — and only counts as implemented where `docs/behavioral-science.md` can point to a column, score, or message rule.
- **Any number in code** must trace to a row in the table above; if it cannot, it is a product assumption and gets labeled as one.

## Maintenance

Re-verify vendor URLs and API behavior quarterly (Sakana surface last verified **July 2026**). A new feature may only cite sources from this list or add its entry here first — uncited claims get treated as product assumptions by default.
