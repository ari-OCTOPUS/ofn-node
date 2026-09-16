# Cycle-6 artifacts — INTERNAL runbook/policy
run_id: revenue-cycle-6-20260827
deadline_utc: 2026-08-27T14:00:00Z
baseline: Cycle-5 CLOSED PASS. Do not rebuild C5. C1-C4 stay closed.
kill: HOLD_EXTERNAL; teacher only; no systemctl start/enable; no new unit; no fifth path
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message

builder: 180
ts_utc: 2026-08-27T03:49:00Z
claimed_mesh: no
kind: INTERNAL_RUNBOOK (not a sales pack)
executor: OCTOPUS on Board2. External agents = teacher only.

Embedded claims (empty=INVALID):
- painting: C3 01-painting.md + C4 01-painting-snapp-contact.md + Fugu painting/DAY1.md + INTAKE.json
- ziman: C4 02-ziman-gallery-cogs.md + Fugu RESULT.json + ziman/COPY-DRAFTS.json
- studio: C4 03-studio-ns-ff-08-price.md + LISTINGS-READY.md + FEETFINDER-STATUS.md
- llm: C5 04-llm-route.md + ofn/helpers/brainport.py + 138 evidence 8895 hypno-fugu-mini + 180 :8081 qwen3-0.6b-q4_0 + model_router.py deepseek-v4-flash

Policy:
1) brainport.ask binds to the three existing stores below. No new inbox.
2) 8895 = existing hypno-fugu-mini only. Do NOT systemctl start/enable (hypno.service is a dead name and fights :8895).
3) DeepSeek = BRAIN_PROVIDER flip documented. Do not write secrets.
4) 180 :8081 = local tier only. No second llama. No ollama :11434.
5) C1-C5 receipts are memory inputs. Internalize. Do not rebuild.

Files: 00-INDEX.md 01-painting-runbook.md 02-ziman-runbook.md 03-studio-runbook.md 04-llm-runbook.md
