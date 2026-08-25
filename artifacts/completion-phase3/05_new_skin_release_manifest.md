# Phase 3 P5 — New skin release manifest

LIVE_PROCESS_PID: 12748 started 2026-08-25T08:52:03Z
LIVE_RUNTIME_HAS_NEW_SKIN: false

Git branch `feat/phase3-completion`. Source hashes below are post-P4 wiring.

| feature | source_path | tests | required_schema | live_runtime_has_it | deployment_risk | rollback | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EventKernel commit+outbox | ofn/organism/event_kernel/kernel.py | test_kernel | events,outbox | true | low | restart previous tree | live |
| Identity chain v1 | ofn/organism/identity/ledger.py | test_kernel | identity_ledger | true | low | n/a | live |
| Mandatory Memory Read | ofn/organism/memory/gate.py | test_memory_gate | memory_read_receipts, decision_evidence | false | medium: extra SELECTs/INSERTs per tick | checkout prior commit + restart | source_only |
| Memory call-site wiring | inner.py curiosity.py learn.py life_cycle.py self_model.py futures.py curriculum.py eval.py backend.py | test_memory_gate, test_life, test_raise | same | false | medium | same | source_only |
| Live schema lock | persistence/db.py LIVE_ORGANISM_DB guard | test_memory_gate | none until env set | false | high if restart without OCTOPUS_ALLOW_LIVE_SCHEMA=1: process will refuse to start | unset guard commit | source_only |
| wan_fetches table in SCHEMA | persistence/db.py | none live | wan_fetches | false | medium: created on next allowed connect(); WAN still not in ask | leave table unused | source_only |
| WAN client | cognition/wan.py | not wired | wan_fetches | false | high if later wired: network | do not import into ask | source_only_unwired |
| GET purity flag | runtime/app.py OCTOPUS_GET_PURE | test_memory_gate defaults off | none | false | low default off | leave unset | source_only |
| LAN token flag | runtime/app.py OCTOPUS_REQUIRE_LAN_TOKEN | defaults off | none | false | high if enabled without token: 401 soak | leave unset | source_only |
| WBE analysis | science/wbe_allometry.py | test_memory_gate | none | false | none: not imported by homeostasis | delete module | source_only |
| Active Inference shadow | cognition/active_inference.py | test_memory_gate | none | false | none: not in tick | delete module | source_only |
| vLLM observe BLOCKED | ofn/adapters/vllm_observe.py | test_memory_gate | none | false | none | n/a | source_only |
| OFN-L4 shadow | /opt/octopus/ofn-l4 | tests.test_shadow | ofn-l4 db only | false | do not listen 8091 | keep L4-GATE run=false | independent_off |

Migration on live DB is **not** a separate .sql file; `connect()` executes SCHEMA IF NOT EXISTS. That is the migration. It is Owner Gate.

Ask cascade still: rule → cache → local 8081 → NEEDS_OWNER. DeepSeek only via existing learn path if env set. Restarting with current start-organism.sh sets `OCTOPUS_LEARN_EXTERNAL=1` as today.
