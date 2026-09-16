import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

out = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23")
out.mkdir(parents=True, exist_ok=True)
AEST = timezone(timedelta(hours=10))
stamp = datetime.now(AEST).strftime("%Y-%m-%dT%H:%M:%S+10:00")

known_excluded = [
    "OCTOPUS-GAP-CLOSE-2026-08-23 (G01-G25)",
    "OCTOPUS-GAP-INVENTORY-2026-08-23",
    "ZIMAN money foot LIVE / BOARD2-ZIMAN-BIZ-FOOT",
    "OCTOPUS-DOCTOR-TO-END",
    "OCTOPUS-EDGE-NEXT (M1-M4 done; residual HOLDS listed separately)",
    "OCTOPUS-SOFT-UNLOCK-RESIGN",
    "OCTOPUS-HOMEO-MIRROR-ALIGN (authority PASS; residual homeo_ok flap listed)",
    "OCTOPUS-TECH-ADMISSION-REFRESH (save-only pack; unfinished TDR backlog listed)",
    "OCTOPUS-LAPTOP-THROTTLE",
    "A18 lab fake PASS (live inbound listed as known-still-open)",
]

items = [
  {"id":"U01","title":"A18 LIVE owner inbound Full Loop still OPEN (lab fake PASS only)","area":"telegram_full_loop","severity":"P0","evidence_paths":[r"06-EVIDENCE\OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23\A18-INBOUND-LAB-FAKE\RESULT.json",r"06-EVIDENCE\OCTOPUS-CONTINUOUS-MISSION-2026-08-23\STATUS.json",r"_ops\state\telegram\poll-health.json"],"status":"PARTIAL","next_safe_probe":"Read-only: compare durable loop/outbox+events for a real owner /remember + /correct-invalid receipt after live inbound; do not sendMessage; do not restart center."},
  {"id":"U02","title":"WIRING connector_gap_hook=true with no organism/wiring beat consumer","area":"wiring_organs","severity":"P1","evidence_paths":[r"_ops\organs\WIRING.json",r"_ops\evidence_plane\connector_gap_loader.py",r"_ops\evidence_plane\__init__.py"],"status":"FLAG_DRIFT","next_safe_probe":"rg consumers of mark_oauth_gaps/load_registry outside evidence_plane; dry-import mark_oauth_gaps() once; do not invent OAuth."},
  {"id":"U03","title":"synthesis_node_packs_hook ON + pointer enabled; packs orphaned from live beat","area":"wiring_organs","severity":"P1","evidence_paths":[r"_ops\organs\WIRING.json",r"_ops\evidence_plane\SYNTHESIS-NODE-PACKS.pointer.json",r"06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\node-packs"],"status":"UNWIRED","next_safe_probe":"Confirm no wiring.py/organism import of pointer/packs; propose read-only beat card only; no restart."},
  {"id":"U04","title":"CONNECTOR-GAP CG-001/002/003 still WAITING_OWNER_OAUTH (GA4/GSC/Ads)","area":"connectors","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\CONNECTOR-GAP-REGISTRY.json",r"_ops\organs\WIRING.json"],"status":"PARTIAL","next_safe_probe":"Owner OAuth/signoff only; until then keep metrics_allowed=false; registry hygiene RFC only."},
  {"id":"U05","title":"Connector probe queue never runtime-probed (Similarweb/Statista/CB Insights/Finance/GitHub/HF)","area":"connectors","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\CONNECTOR-GAP-REGISTRY.json"],"status":"UNWIRED","next_safe_probe":"Read-only probe plan with estimate labels; no paid unlock; no invent facts."},
  {"id":"U06","title":"Arch-loop DESIGN backlog not fully sliced (CONNECTOR-GAP hygiene + MiniApp lab UI still uncut)","area":"arch_loop","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23\DESIGN.md",r"06-EVIDENCE\OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23\A18-INBOUND-LAB-FAKE",r"06-EVIDENCE\OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23\C05-DUAL-OUTBOX-CONTRACT",r"06-EVIDENCE\OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23\CENTER-BRIDGE-ATTACH-DEFAULT-OFF"],"status":"PARTIAL","next_safe_probe":"Open propose-only slices 4-5 under ARCH-EVOLUTION evidence; human/ari merge gate only."},
  {"id":"U07","title":"MiniApp triple-URL residual: state named-tunnel + env trycloudflare + docs localhost primary","area":"miniapp_public_url","severity":"P1","evidence_paths":[r"_ops\state\telegram\miniapp-url.json",r"06-EVIDENCE\OCTOPUS-MINIAPP-DOC-RECONCILE-2026-08-23\RESULT.json"],"status":"FLAG_DRIFT","next_safe_probe":"Re-measure cloudflared/miniapp_gateway PIDs; document single truth card; no Telegram menu mutate without owner GO."},
  {"id":"U08","title":"Telegram poll alive but inbound update SoT stale (empty polls dominate; last_update old)","area":"telegram_full_loop","severity":"P0","evidence_paths":[r"_ops\state\telegram\poll-health.json",r"_ops\state\telegram\inbound-log.jsonl",r"_ops\state\telegram\process-identity.json"],"status":"PARTIAL","next_safe_probe":"Read-only diff last_update_received_at vs last_ok_ts vs inbound-log mtime; no restart; no send."},
  {"id":"U09","title":"Board2 ports 8791/8792/8793 not listening on laptop (business node remote-liveness blind)","area":"cross_surface","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\node-packs\NODE-PACK-BUSINESS.json"],"status":"UNKNOWN","next_safe_probe":"Owner-authorized remote health read of Board2; do not invent listening services on laptop."},
  {"id":"U10","title":"Laptop NATS:4222 direct connect timed out (EDGE E2E stayed on-Pi)","area":"cross_surface","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-EDGE-NEXT-2026-08-23\RECEIPT.json"],"status":"PARTIAL","next_safe_probe":"Read-only LAN/firewall/NATS listener check; no ARM; no PWM; no secret print."},
  {"id":"U11","title":"WAVE-B uncommitted-wave-b.patch still orphaned on disk","area":"handoffs_registries","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-WAVE-B-HANDOFF-2026-08-21\uncommitted-wave-b.patch",r"06-EVIDENCE\OCTOPUS-WAVE-B-HANDOFF-2026-08-21\HANDOFF.md"],"status":"PARTIAL","next_safe_probe":"Owner sparse-commit decision or quarantine note; do not mass-commit dirty tree."},
  {"id":"U12","title":"4d ConsolidationCycle still NEVER-WIRED into daemon (Aug-16 UNWIRED remains real)","area":"unwired_code","severity":"P2","evidence_paths":[r"06-EVIDENCE\UNWIRED-4d-consolidation-2026-08-16.md",r"4d_system\brain\daemon.py",r"4d_system\brain\consolidation.py"],"status":"UNWIRED","next_safe_probe":"rg ConsolidationCycle in 4d_system; keep contained; docstring ERRATA only unless owner GO to wire."},
  {"id":"U13","title":"self_audit evidence_bound Done probes with evidence_json=null (gate soft spot)","area":"epistemics_self_audit","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-SELF-AUDIT-PROBE-2026-08-23\STATUS.json",r"_ops\cortex\self_audit.py"],"status":"PARTIAL","next_safe_probe":"Bind an existing prove RESULT.json as evidence_json for one audit item; fail-closed dry run."},
  {"id":"U14","title":"self_insight full live self_scan path not executed (fixture --once only)","area":"epistemics_self_audit","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-SELF-INSIGHT-EPISTEMICS-2026-08-23\RESULT.json",r"_ops\self_insight.py"],"status":"PARTIAL","next_safe_probe":"Optional timed self_insight --json --no-journal under owner GO; no phenomenal claims."},
  {"id":"U15","title":"Epistemics advisory live but ident/channel/levels/self_reference still non-authoritative null samples","area":"epistemics_self_audit","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-SELF-INSIGHT-EPISTEMICS-2026-08-23\RESULT.json",r"06-EVIDENCE\OCTOPUS-EPISTEMICS-WIRE-ON-2026-08-23",r"_ops\epistemics"],"status":"PARTIAL","next_safe_probe":"Natural sample accrual plan; do not lower MIN_SAMPLES; keep advisory_only=true."},
  {"id":"U16","title":"evelab/self_upgrade promoter exists but no continuous promote schedule","area":"evelab_promote","severity":"P1","evidence_paths":[r"_ops\self_upgrade_lab\promoter.py",r"_ops\doctor\lab_bridge.py",r"06-EVIDENCE\OCTOPUS-EVELAB-DOCTOR-WIRE-2026-08-23\RESULT.json"],"status":"PARTIAL","next_safe_probe":"Keep propose-only; document absence of Windows cron; human [merge]/reject] only."},
  {"id":"U17","title":"Chroma vault_whole collection documented not-yet-wired","area":"docs_no_code","severity":"P2","evidence_paths":[r"4d_system\memory\vectorstore.py",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\AUDIT.json"],"status":"UNWIRED","next_safe_probe":"Read-only confirm OCTOPUS_WIRE_VAULT_RAG still unarmed; no new vector DB install."},
  {"id":"U18","title":"MCP 2026-07-28 Mcp-Method/Mcp-Name headers not implemented; initialize handshake still present","area":"docs_no_code","severity":"P1","evidence_paths":[r"_ops\octopus_mcp\server.py",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\AUDIT.json",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\DECISIONS.json"],"status":"DOC_ONLY","next_safe_probe":"Draft MCP-adapter-headers TDR scoped to server.py only; no code until owner TDR GO."},
  {"id":"U19","title":"SSE O-E4 endpoint live but heartbeat/resume-after-disconnect tests missing","area":"miniapp_public_url","severity":"P2","evidence_paths":[r"_ops\telegram_center\miniapp_gateway.py",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\AUDIT.json"],"status":"PARTIAL","next_safe_probe":"Write verification tests for /api/runs/{id}/events?after=N; no menu publish."},
  {"id":"U20","title":"OTel GenAI mapping TRIAL + DBOS Run Store TRIAL still save-only backlog","area":"docs_no_code","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\DECISIONS.json",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\SAVE-ONLY.md",r"_ops\cognitive\event_stream.py",r"_ops\evidence_plane\event_log.py"],"status":"DOC_ONLY","next_safe_probe":"TDR first: map gen_ai.* onto event_stream; compare DBOS trial vs existing event_log before claiming gap."},
  {"id":"U21","title":"conversation_hub located but not deep-read / wiring status UNKNOWN after TECH-ADMISSION step1","area":"wiring_organs","severity":"P2","evidence_paths":[r"_ops\conversation_hub",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\AUDIT.json"],"status":"UNKNOWN","next_safe_probe":"Read-only map router/service/shadow_rollout to MiniApp/MCP; no behavior change."},
  {"id":"U22","title":"04-SYSTEMS/TYPED-EVENTS.md still phantom-name doc trap in tree","area":"docs_no_code","severity":"P2","evidence_paths":[r"04-SYSTEMS\TYPED-EVENTS.md",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\AUDIT.json"],"status":"DOC_ONLY","next_safe_probe":"Keep phantom label; cite _ops/cognitive/event_stream.py in any OTel TDR; do not register nbb_cp ledger as match."},
  {"id":"U23","title":"homeo_ok intermittent false after HOMEO-MIRROR-ALIGN (soak DEGRADED residual)","area":"cross_surface","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-HOMEO-MIRROR-ALIGN-2026-08-23\RECEIPT.json",r"06-EVIDENCE\OCTOPUS-EDGE-NEXT-2026-08-23\RECEIPT.json"],"status":"PARTIAL","next_safe_probe":"Read-only Pi homeostasis latest freshness envelope; keep ARMED=false; no PWM."},
  {"id":"U24","title":"NODE-PACK laptop open gates still dark: gap002_registry blocking + GitHub DietPi PAT pending","area":"handoffs_registries","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\node-packs\NODE-PACK-LAPTOP.json"],"status":"PARTIAL","next_safe_probe":"Owner-only PAT/signature actions; agents only document blockers; no key export."},
  {"id":"U25","title":"Pi LAN:9101 firewall verify still pending (sensorium NODE-PACK open question)","area":"cross_surface","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\node-packs\NODE-PACK-SENSORIUM.json",r"06-EVIDENCE\OCTOPUS-ORANGEPI-LAN-9101-2026-08-22"],"status":"UNKNOWN","next_safe_probe":"Read-only connectivity check laptop->Pi :9101; no MQTT open; no WAVE0 unlock."},
  {"id":"U26","title":"ACTIVATION-* flag sprawl residual (beyond CORTEX-PAID disarm) still present under _ops","area":"flag_drift","severity":"P2","evidence_paths":[r"_ops\arm_gate.py",r"_ops\flag_drift.py",r"_ops\ACTIVATION-FLAGS.md"],"status":"FLAG_DRIFT","next_safe_probe":"Run flag_drift dry inventory; propose cleanup checklist only; do not arm paid."},
  {"id":"U27","title":"TECH-ADMISSION immediate_week TDRs not drafted (MCP headers / SSE tests / gen_ai mapping)","area":"docs_no_code","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\DECISIONS.json",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\SAVE-ONLY.md",r"06-EVIDENCE\OCTOPUS-TECH-ADMISSION-REFRESH-2026-08-23\EXEC-GUIDE-CONSERVATIVE.md"],"status":"DOC_ONLY","next_safe_probe":"Write TDRs under save-only rule; no installs; measured problem + rollback required."},
  {"id":"U28","title":"SenderBridge attach path exists default-OFF; live poll-loop still not owner-attached","area":"telegram_full_loop","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23\CENTER-BRIDGE-ATTACH-DEFAULT-OFF\RESULT.json",r"_ops\telegram_center\poll_sender_bridge_attach.py"],"status":"PARTIAL","next_safe_probe":"Keep attach OFF; owner GO + send_exceptions required before env/flag enable."},
]

doc = {
  "schema": "octopus-undiscovered/1",
  "stamp_local": stamp,
  "timezone": "Australia/Sydney",
  "path": str(out),
  "constraints": {"no_invent": True, "no_live_sendMessage": True, "no_money_unlock": True, "no_PWM": True, "no_secrets_in_report": True},
  "known_excluded_reference_only": known_excluded,
  "scan_focus": ["WIRING/organs/legs","flags vs consumers","docs/playbooks without code","UNWIRED lists / tests","MiniApp/cloudflared/public URL","Telegram Full Loop inbound durable SoT","Arch-loop DESIGN backlog","handoffs/registries/NODE-PACKs","Pi/Board2/laptop cross-surface","epistemics/self_audit/evelab promote"],
  "counts": {"items": len(items), "P0": sum(1 for i in items if i["severity"]=="P0"), "P1": sum(1 for i in items if i["severity"]=="P1"), "P2": sum(1 for i in items if i["severity"]=="P2")},
  "items": items,
  "top25_ids": [f"U{i:02d}" for i in range(1,26)],
}
(out/"UNDISCOVERED.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

lines = [
"# OCTOPUS UNDISCOVERED — SUMMARY (top 25)",
f"**Stamp (AEST):** {stamp}",
f"**Path:** `{out}`",
"**Constraints:** no invent · no live sendMessage · no money · no PWM · no secrets",
"",
"## Scope",
"Still-dark / unfinished after 2026-08-23 waves. Known G01–G25 + named packs are reference-only (not re-scored as new).",
"",
f"## Counts (all items in UNDISCOVERED.json): P0={doc['counts']['P0']} P1={doc['counts']['P1']} P2={doc['counts']['P2']} total={doc['counts']['items']}",
"",
"| Rank | ID | Sev | Status | Title |",
"|---:|---|---|---|---|",
]
for i, it in enumerate(items[:25], 1):
    lines.append(f"| {i} | {it['id']} | {it['severity']} | {it['status']} | {it['title']} |")
lines += [
"",
"## Category rollup",
"- **Telegram Full Loop:** U01/U08 still open on LIVE durable SoT; U28 attach remains OFF.",
"- **WIRING/flags:** U02/U03 hooks ON without live consumers; U26 ACTIVATION sprawl residual.",
"- **Connectors / NODE-PACKs:** U04–U05 OAuth+probe queue; U03/U24 packs/gates orphaned or owner-blocked.",
"- **MiniApp / public URL:** U07 triple-URL residual; U19 SSE tests missing.",
"- **Cross-surface:** U09 Board2 ports blind; U10 laptop NATS timeout; U23 homeo_ok flap; U25 LAN:9101.",
"- **Epistemics / evelab:** U13–U16 self_audit/insight/promote gaps still real.",
"- **Docs-only / tech admission:** U17–U22, U27 TDRs/save-only backlog.",
"- **Arch-loop / handoffs:** U06 unsliced DESIGN; U11 Wave-B patch; U12 4d consolidation UNWIRED.",
"",
"## Forbidden reminders",
"Do not invent OAuth/captions/money unlocks; do not live sendMessage; do not ARM/PWM; do not put secrets in evidence.",
"",
]
(out/"SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

method = f"""# METHOD — OCTOPUS-UNDISCOVERED-2026-08-23

**Stamp (AEST):** {stamp}  
**Executor:** grok-bot executor subagent  
**Root scanned:** `F:\\backup`  
**Output:** this folder

## How scanned (read-only)

1. **Baseline exclude:** loaded `OCTOPUS-GAP-INVENTORY-2026-08-23/SUMMARY.md` + `OCTOPUS-GAP-CLOSE-2026-08-23/CLOSE-MATRIX.md` so G01–G25 and named known packs are reference-only, not re-discovered.
2. **WIRING / organs:** read `_ops/organs/WIRING.json` flags+hooks; located `connector_gap_loader.py`, `SYNTHESIS-NODE-PACKS.pointer.json`, node-packs; searched consumers — loader exported from `evidence_plane` only (no organism beat hit).
3. **Flags:** inventoried `_ops/ACTIVATION-*` + `arm_gate.py` / `flag_drift.py` references; residual sprawl beyond CORTEX-PAID disarm noted.
4. **Arch-loop:** read `OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/DESIGN.md` + three slice RESULT.json (A18 lab fake, C05, CENTER-BRIDGE); noted unsliced candidates.
5. **Telegram / MiniApp:** read `poll-health.json`, `miniapp-url.json`, `process-identity.json`, MiniApp reconcile RESULT; compared inbound freshness vs empty-poll counters.
6. **Cross-surface:** EDGE-NEXT RECEIPT HOLDS (laptop NATS timeout, homeo residuals); HOMEO-MIRROR-ALIGN RECEIPT soak DEGRADED; NODE-PACK business/laptop/sensorium open_gates/open_questions.
7. **Epistemics / evelab / self_audit:** SELF-AUDIT STATUS, SELF-INSIGHT-EPISTEMICS RESULT, EVELAB-DOCTOR-WIRE RESULT, `self_upgrade_lab/promoter.py` gate (owner lock + verifier; no cron).
8. **Tech admission:** TECH-ADMISSION-REFRESH AUDIT.json + DECISIONS.json (MCP headers gap, SSE tests, vault_whole, phantom TYPED-EVENTS, conversation_hub unread, DBOS/OTel trials).
9. **UNWIRED / handoffs:** Aug-16 UNWIRED packs (STALE-marked) re-checked — ConsolidationCycle still absent from `4d_system/brain/daemon.py`; Wave-B `uncommitted-wave-b.patch` still present.
10. **Ports:** netstat probe for 8765/8791-8793/9101/1883/12220 returned no matches at scan time (supports Board2 remote-blind + local port uncertainty).

## What was NOT done

- No live Telegram sendMessage / menu mutate
- No money / bank / PayPal / paid unlock
- No PWM / ARM / WAVE0 physical mutate
- No secrets copied into report
- No inventing OAuth, captions, or public URLs
- No destructive git commits

## Severity rubric

- **P0:** LIVE inbound/full-loop truth still open or inbound SoT stale while center claims healthy
- **P1:** Flag/wiring drift, cross-surface blind, owner-blocked connectors, unfinished tech-admission blockers
- **P2:** Doc-only / test-missing / soak residuals / orphan patches

## Artifacts

- `UNDISCOVERED.json` — full item list with fields
- `SUMMARY.md` — top 25 table
- `METHOD.md` — this file
"""
(out/"METHOD.md").write_text(method, encoding="utf-8")
print("WROTE", out)
print("counts", doc["counts"])
for it in items[:15]:
    print(f"{it['id']} [{it['severity']}/{it['status']}] {it['title']}")
