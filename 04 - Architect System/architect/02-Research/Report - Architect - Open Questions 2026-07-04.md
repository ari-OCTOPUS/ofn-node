---
type: report
status: done
created: 2026-07-04
updated: 2026-07-04
---

# Report - Architect - Open Questions 2026-07-04

> Short findings note from the scheduled research run (Cowork, 2026-07-04). Source of questions: [[04 - Architect System/architect/02-Research/SCOUT-SUMMARY|SCOUT-SUMMARY]] §3 GAPS — only the web-answerable ones (4/13). Hardware benches and human actions untouched per run constraints.

## GAP 7 — KILLBENCH (arXiv:2511.13725) ✅ RESOLVED

Paper is real and current: **"Can We Stop Malicious AI? KILLBENCH: A Benchmark for External AI Kill Switch Feasibility"** — Sechan Lee, Hyounghun Kim, Sangdon Park; submitted 2025-09-26, **v4 revised 2026-06-14**. Scope: web agents; external kill-switch *payloads embedded in the agent's web environment* halt a malicious agent with zero access to internals; 4 agent configs (incl. uncensored LLM), 8 harmful scenarios, 10 jailbreak patterns. [abs](https://arxiv.org/abs/2511.13725) · [HTML v3](https://arxiv.org/html/2511.13725v3)
**Relevance:** this is a *third* external-halt layer alongside SCOUT ⑤ (heartbeat-lease + WDT): environment-embedded stop signals. Remove [Unverified] tag from the SCOUT gap on next triage.

## GAP 8 — Calibrated confidence for escalation gating ✅ strong leads

The pattern exists and is maturing fast: conformal prediction gives statistically guaranteed uncertainty sets (not raw scores) for route/escalate decisions. Key items: **CP-Router** (route standard-LLM vs reasoning-LLM by conformal uncertainty), **SConU** (ACL 2025, conformal p-values), **UCCI** cost-optimal cascade routing ([arXiv](https://arxiv.org/html/2605.18796)), and a direct evaluation of escalation behavior: ["Act or Escalate?"](https://arxiv.org/pdf/2604.08588). Practical recipe reported: calibrate first (small isotonic fit on held-out set), threshold second — raw token confidence is miscalibrated. Survey: [Dynamic model routing & cascading](https://arxiv.org/pdf/2603.04445).
**Relevance:** architect's human-gate could escalate on conformal set size instead of vibes — pairs with SCOUT ⑥ anti-fatigue design.

## GAP 9 — Witness Network for small private logs ⚠️ partially answered

The [Witness Network](https://blog.transparency.dev/can-i-get-a-witness-network) is a *shared, community-vetted* config process — i.e. built around known/public logs (OmniWitness ships preconfigured with a [logs.yaml](https://github.com/transparency-dev/witness/blob/main/omniwitness/logs.yaml) of known logs). For a small **private** ledger the realistic path is NOT joining the public network but: run your own witness ([transparency-dev/witness](https://github.com/transparency-dev/witness), implements [C2SP tlog-witness](https://github.com/C2SP/C2SP/blob/main/tlog-witness.md)) or dedicated hardware ([armored-witness](https://github.com/transparency-dev/armored-witness)) — plus the OTS/git-remote anchors already planned (SCOUT ③). Exact public-network acceptance criteria for niche logs: still not documented — **remaining ambiguity**.

## GAP 10 — GitOps for <50-node fleet without k8s ✅ pattern confirmed, no canonical tool

No single reference project; the documented pattern is exactly what SCOUT ⑦ implies: **systemd timer + `Type=oneshot` git-pull unit** per node ([worked example + journalctl bug caveat](https://admin.brennt.net/creating-a-systemd-timer-to-regularly-pull-git-repositories-and-getting-to-know-an-uncomfortable-systemd-journalctl-bug-along-the-way)), then idempotent apply (pyinfra `--dry` from SCOUT) or `docker compose up -d` ([non-k8s GitOps homelab writeup](https://shadybraden.com/articles/gitopshomelab/)). Conclusion: build the thin glue ourselves; k8s remains SKIP (consistent with SCOUT contradictions section).

## Not touched (need hardware/human)

RK3588 hash benches (GAPS 1-3), Restate/Ditto ARM RAM (GAP 4 — benchable locally), srt+OPA recipe (GAP 5 — build item), delayed-lock two-person question (GAP 6 — design decision), premine scraping automation (GAP 11), coin-survival model (GAP 12), ESP32 PoW (GAP 13 — covered by Mining Prompt 2 in the pack).
