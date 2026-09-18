---
type: report
lane: Q-QUALITY-SWARM-20260908
created: 2026-09-08
gov: V8
ladder: L2
verdict: INSUFFICIENT_DATA
---

# COUNCIL-CORRELATION-REPORT

Question: error correlation \(\bar{c}\) between council models **GLM, DeepSeek, Ollama, Fugu** from existing decision ledger. If \(\bar{c} > 0.70\) on any pair, record it. Do not guess.

## Verdict

**INSUFFICIENT_DATA**

No ledger in this vault stores **per-model votes on the same decision** for those four names. Pairwise error correlation cannot be computed. No pair is recorded as \(\bar{c} > 0.70\) because no \(\bar{c}\) exists.

## What was searched (level 2 files)

| Source | What it contains | Why it is not a 4-model error series |
|---|---|---|
| `_ops/debate/survivors-pending.jsonl` | one idea + status per row | no `glm`/`deepseek`/`ollama`/`fugu` vote fields |
| `_ops/debate/SURVIVORS-QUEUE.md` | muse/architect prose | roles, not four named models; often stub (`debate_loop.py` `_stub_transport`) |
| `_ops/debate/debate_loop.py` | `DeepSeekClient` for muse **and** architect | two roles, one client class; live path still not a 4-way vote log |
| `_ops/debate/client.py` | MultiProviderClient routes glm/fugu/deepseek | routing config, not a decision-error matrix |
| `OCTOPUS-PRIME/COUNCIL_REPORTS` | path cited in DEEP-SCAN; **directory absent** this session | cannot read |
| 06-EVIDENCE council glob | 0 files named `*council*` | none |

## Sample size

n_paired_decisions_with_4_model_votes = **0** (source: absence of fields above).  
UNDERPOWERED would still require n>0 with a defined error. Here the series does not exist.

## Prompt 2

High-correlation adversarial prompts are **not** designed or tested (would be a guess).  
Logging infrastructure for the **next 50** council decisions is in this lane: `council/council_decision_log.py`.
