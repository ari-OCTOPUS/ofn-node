# EXEC-GUIDE for next agent (CONSERVATIVE) — 2026-08-23

Owner: Aroma / ari coordination.  
Other agent: you may EXECUTE only inside this guide.  
Tone: **احتیاطاً** — prefer TDR + prove over shipping; no fan-out; no invent.

## Scope IN
- `octopus-unified-chat` / owner-chat / Tool Registry / Run Store / SSE / MCP **adapter** only.
- Technology Admission Gate items from owner report (MCP, SSE, OTel mapping, DBOS-style trial, Chroma baseline).

## Scope OUT (do not touch unless owner GO)
- Ziman / Shopify / PayPal / gallery / Studio / OnlyFans
- Mining
- ARMED=true, PWM, physical e-stop purchase
- Force-git, unrestricted Telegram live send, invent captions/photos/secrets
- Migrating Chroma→Qdrant, adopting Temporal, NATS/Kafka, WebSocket — all **DEFER/REJECT** until TDR + measured need

## Already DONE this session (do not redo as "discovery")
- Pi DOCTOR-TO-END PASS + soft-unlock ROOT-V2 re-sign PASS
- EDGE-NEXT PASS_WITH_HOLDS (command-trust VERIFIED, obs harden, allowlist freeze, soak DEGRADED)
- Homeo mirror align PASS_WITH_HOLDS
- Laptop OCTOPUS throttle (BelowNormal/Idle) — keep; do not raise priority
- Tech report SAVED at this folder — owner previously said save-only; now another agent may execute **per this guide**

Evidence roots:
- `F:\backup\06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\` (this pack)
- Pi packs under `F:\backup\06-EVIDENCE\OCTOPUS-DOCTOR-TO-END-2026-08-23\`, `OCTOPUS-EDGE-NEXT-2026-08-23\`, `OCTOPUS-SOFT-UNLOCK-RESIGN-2026-08-23\`, `OCTOPUS-HOMEO-MIRROR-ALIGN-2026-08-23\`

## Decision table (proposed — still needs TDR before install)
| Tech | Status | Note |
|------|--------|------|
| MCP 2026-07-28 stateless | ADOPT as **adapter only** | Headers `Mcp-Method`/`Mcp-Name`; no new authority; drop session state if present |
| SSE O-E4 | ADOPT | `GET /api/runs/{run_id}/events` + heartbeat + resume |
| WebSocket | DEFER | Only voice/HITL realtime |
| Chroma | KEEP | Baseline real Vault before any Qdrant talk |
| Qdrant | DEFER | After failed Chroma baseline only |
| DBOS-style on existing Postgres | TRIAL | Run Store O-T0 criteria |
| Temporal | REJECT now | Until multi-service fan-out proven |
| OTel GenAI | TRIAL mapping only | Map to existing typed events; no heavy collector |
| NATS/Kafka | DEFER | Until >1 independent consumers |

## Conservative execution order (stop on red)
1. **Read-only audit** (no code change): locate MCP tool registry, run event API, typed event schema, vault/chroma paths. Write `AUDIT.json` here.
2. **Draft TDRs** (markdown, no install): one each for MCP-adapter-headers, SSE-O-E4, OTel-mapping, DBOS-runstore-trial. Each must include: measured problem, why current insufficient, trial threshold, rollback.
3. **Owner/ari merge gate**: ping ari with TDR paths; **do not merge/enable** until GO.
4. Only after GO: implement **one** slice at a time with tests + evidence pack dated folder under `06-EVIDENCE\`.
5. Prefer lab/worktree if arch-loop rules apply; no money; no force push.

## Hard locks from this session
- MCP = interface adapter; **never** new authority
- Cite-before-claim / typed events stay SoT for truth layer
- Pi: ARMED=false; command-trust already VERIFIED; do not weaken allowlist
- Laptop hitch mitigation: keep process priorities low

## How to report back
- Write under this folder: `AUDIT.json`, `TDR-*.md`, `NEXT-ACTION.md`
- Ping **ari** (not user spam) with PASS/FAIL + paths
- If blocked: STOP with precise blocker, last evidence path, no silent workaround

## Explicit NON-goals this run
- Do not "improve" Ziman
- Do not buy hardware
- Do not enable Temporal/NATS/Qdrant/WebSocket
- Do not claim self-awareness / paid unlock
