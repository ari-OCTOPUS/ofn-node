# ROADMAP

writer: Cursor on 180 · 2026-08-27T23:03Z  
rules: no big refactor in NOW · each NOW/NEXT item ties to money, money-path reliability, or required safety

## NOW — 72 hours

Goal: first **real external owner-visible effect** = one Telegram decision message for one lane, and/or first customer-facing follow-up **only after APPROVE**. Not a new platform.

| # | work | done when | evidence | owner |
|---|---|---|---|---|
| 1 | Pick **one** Telegram owner channel (OFN bridge vs fugu). Enable that one. Do not add a bot. | systemctl active; one message to owner containing painting `decision_id` | 138 journal + owner screenshot | owner |
| 2 | 138 mint three `witness_request` from bizop packets to 182 | 182 verdicts PASS/DISPUTED/UNRESOLVED back as task/proposal (not result on 180) | 182 journal + 180 inbox type | 138 operator after owner GO |
| 3 | Replace painting fixture with **one live lead** from 138 `packs/lead.yaml` / store (facts only) | cycle artifact has suburb or explicit UNKNOWN still, but `source=live_138` not shadow | new run_id RECEIPT | 138 exports; 180 scores |
| 4 | Compact 180 ping inbox (dry-run then delete only processed pings) | inbox files < 200 or ping share < 20% | ls inbox counts | 180 with owner GO |
| 5 | Disk: archive bulky `/opt/octopus/lab/evidence` copies to 138/PC, keep hashes | df < 85% | df -h + archive sha256 | owner |

No refactor. No ofn-l4 bring-up. No Armin rewrite. No langar integration.

## NEXT — 2 weeks

Goal: repeatable three lanes + **first settled money on 138 ledger** (180 still does not write revenue).

| # | work | money/safety join |
|---|---|---|
| 1 | Idempotent 138 executor path for one APPROVE exact_payload | money |
| 2 | Reconcile 182 policy.json to canonical signed hash | safety/transport |
| 3 | Put octopus-mesh under git (one repo, three node checkouts) or documented rsync | reliability |
| 4 | Live ziman row with known cost+price or honest UNKNOWN | money |
| 5 | Studio only `sensitivity=general` offers | safety |
| 6 | Witness required before Telegram (138 gate) | safety |
| 7 | Push or discard 180 commit 76db516 via 138, never force-push | reliability |

## LATER — after money

- ofn-l4 kernel, vLLM, MiniMax, langar merge, Armin rebuild, megaprompt cleanup, 0.0.0.0 bind restriction, organism world_hosts enroll 182, 100-replay metric, PC_worker if it exists on laptop.

## Explicitly not NOW

Rewriting ofn/config.py, new orchestrator, new model, new listener, merging this PR without owner, claiming SENT/booking on 180.
