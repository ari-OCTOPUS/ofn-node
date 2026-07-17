# Plan: Cross-System Duplication & Waste Analysis

## Objective
Identify all duplications, copied code, wasted data, energy waste, and parallel unnecessary architectures in Octopus system at F:/backup/.

## Stage 1: Parallel Research (explore agents)
- Agent A (_ops): Analyze _ops/ for duplicate ledgers, state files, telegram paths, HTTP servers, copied leg code, telemetry, doctor/cortex overlap, config layers, watchdogs
- Agent B (app_vs_ops): Compare app/ (NBB-CP) with _ops/organism.py for dual control planes, governors, APIs, ledgers, READMEs, invariants
- Agent C (4d_system): Analyze 4d_system/ for duplicate LLM routing, daemon, config, extractors, .env files
- Agent D (dashboards_extractors): Analyze nervous-system/, OCTOPUS/, _ops/dashboard/, _ops/live/, _ops/panel/ for duplicate dashboards and extractors
- Agent E (config_env): Scan all .env, budgets.yaml, MANIFEST.yaml, adapter.yaml, flag files, env var naming inconsistencies
- Agent F (cross_system): Compare ledger formats, state storage, Telegram config, LLM routing, DB usage, budget definitions across all systems

## Stage 2: Synthesis & Report Writing
- Integrate all findings into cross_system_report.md
- Rate each duplication with 🔴 (critical), 🟡 (medium), 🟢 (low)
- Provide exact file paths and line numbers where possible
