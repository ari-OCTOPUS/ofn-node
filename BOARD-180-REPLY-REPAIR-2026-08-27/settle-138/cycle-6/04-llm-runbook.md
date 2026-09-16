# Cycle-6 LLM — OCTOPUS reconnect runbook
run_id: revenue-cycle-6-20260827
task_id: C6-LLM-RUNBOOK
idempotency_key: cycle6:llm:three-live-bind
claim_level: C5 04-llm-route.md + 138 Cycle-5 evidence
HOLD_EXTERNAL=yes | no new unit | no secrets in files

## Memory inputs

- C5 04-llm-route.md (three LIVE / DEAD list)
- ofn/helpers/brainport.py (Board2 / OFN-Board)
- AGENT-NEXT-DEEPSEEK-V4-FAST.md
- Fugu brain/BRAINPORT.md + DEEPSEEK-CUTOVER.md (cutover doc only)
- laptop F:\\backup\\_ops\\cortex\\model_router.py collab_chat=deepseek-v4-flash

## Three LIVE binds (no fifth path)

1) 138 127.0.0.1:8895 hypno-fugu-mini probe 200. BRAIN_PROVIDER=fugu.
   brainport.ask default tier → this port.
   DeepSeek is NOT proven on :8895. Do not point this port at DeepSeek.
   Do NOT systemctl start/enable. Do NOT start hypno.service (dead name; fights :8895).

2) 180 127.0.0.1:8081 octopus-llama-lab qwen3-0.6b-q4_0.
   brainport.ask tier="local" → this only.
   No second llama. No ollama :11434.

3) Laptop Center DeepSeek
   model_router.py collab_chat=deepseek-v4-flash.
   Documented flip only: BRAIN_PROVIDER=deepseek after DEEPSEEK_API_KEY exists in vault secrets (not chat, not this file).
   Pipelines stay the same. Smoke later: ask(business=ziman) once, compare to Fugu COPY-DRAFTS. Not this cycle if key absent.

## Lane wiring (one function, three stores)

```
ask(business="painting", pipeline="quote_draft", ...) → painting/inbox → painting/outbox
ask(business="ziman",    pipeline="listing_copy", ...) → COPY-DRAFTS.json (prefer existing 11)
ask(business="studio",   pipeline="listing_draft", ...) → LISTINGS-READY / NS-FF-08
```

ALLOW already {painting, ziman, studio, lab}. DENY mining/wlos/etoro/architect_sys.

## DEAD — leave dead

hypno.service | /brain/ask | octopus-wire | ofn-backup | ollama :11434 | 182 no LLM

OCTOPUS executes this runbook. 180 does not start units and does not send.
