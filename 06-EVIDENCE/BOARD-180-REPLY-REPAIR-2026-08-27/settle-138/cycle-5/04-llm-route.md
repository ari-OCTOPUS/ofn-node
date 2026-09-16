# Cycle-5 PLUS — three LIVE routes (discover only)
run_id: revenue-cycle-5-20260827
task_id: C5-LLM-ROUTE
idempotency_key: cycle5:llm:three-live-no-fifth
claim_level: 138 Cycle-5 evidence 2026-08-27 + prior HEALTH 8895=200
HOLD_EXTERNAL=yes | do not mint a fifth path | do NOT start hypno.service

## LIVE — reconnect these three only

1) Board2 192.168.0.138 127.0.0.1:8895
   process: hypno-fugu-mini
   probe: 200
   BRAIN_PROVIDER=fugu
   DeepSeek NOT proven on this port
   code: ofn/helpers/brainport.py
   brief: F:\\backup\\03 - Projects\\OFN-Board\\AGENT-NEXT-DEEPSEEK-V4-FAST.md
   Fugu evidence copy (not a second port): 06-EVIDENCE/FUGU-BIZ-SPRINT-2026-08-24/brain/brainport.py

2) Board 180 192.168.0.180 127.0.0.1:8081
   unit/process: octopus-llama-lab
   model: qwen3-0.6b-q4_0
   Stay on this. Do not stand up ollama :11434.

3) Laptop Center
   F:\\backup\\_ops\\cortex\\model_router.py
   collab_chat=deepseek-v4-flash
   This is the existing DeepSeek route. Not a new gateway. Do not cat keys.

## DEAD — do not revive / do not fight LIVE

- 138 hypno.service — dead name. Starting it would fight :8895. Leave it.
- /brain/ask
- octopus-wire
- ofn-backup
- ollama :11434
- 182 no LLM

## Reconnect (no new model/loop/unit)

1) Three lanes ask() through ofn/helpers/brainport.py against LIVE :8895 (fugu).
2) Hard/offline/local tier → 180 :8081 qwen3-0.6b-q4_0 only.
3) Teacher/Center DeepSeek → existing model_router.py deepseek-v4-flash. Do not point :8895 at DeepSeek until proven.
4) Internalize C1-C4 stores as lane memory. No fifth store. No fifth path.
5) 180 will not systemctl start/enable anything.

VERIFIED_CASH is the goal. This file only names the reconnect.
