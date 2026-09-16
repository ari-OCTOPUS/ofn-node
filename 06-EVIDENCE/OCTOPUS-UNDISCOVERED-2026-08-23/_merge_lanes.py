import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

out = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23")
AEST = timezone(timedelta(hours=10))
stamp = datetime.now(AEST).strftime("%Y-%m-%dT%H:%M:%S+10:00")

# reload laptop base
base = json.loads((out/"UNDISCOVERED.json").read_text(encoding="utf-8-sig"))
items = list(base["items"])
have = {i["id"] for i in items}

extras = [
  {"id":"U29","title":"MiniApp public Telegram menu URL not LIVE / not owner-published (reconcile P0)","area":"miniapp_public_url","severity":"P0","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\RECONCILE.json",r"_ops\state\telegram\miniapp-url.json",r"06-EVIDENCE\OCTOPUS-MINIAPP-DOC-RECONCILE-2026-08-23\RESULT.json"],"status":"PARTIAL","next_safe_probe":"Do not invent menu URL; verify tunnel metadata vs localhost primary; owner GO before BotFather/menu mutate.","lane":"reconcile"},
  {"id":"U30","title":"WIRING lead_activation=false while lead_* leg code present (flag OFF / consumer dark)","area":"wiring_organs","severity":"P1","evidence_paths":[r"_ops\organs\WIRING.json",r"_ops\legs\lead_leg.py",r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\RECONCILE.json"],"status":"FLAG_DRIFT","next_safe_probe":"Map lead_* modules vs lead_activation flag; keep OFF unless owner GO; no outbound lead send.","lane":"laptop"},
  {"id":"U31","title":"Board2: Instagram/GBP/Layer-C socials DOC-ONLY (registry claims, zero runtime adapters)","area":"board2","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json",r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED-TOP10-DEEP.md"],"status":"DOC_ONLY","next_safe_probe":"Keep adapters absent; registry hygiene note only; no invent social posts.","lane":"board2"},
  {"id":"U32","title":"Board2: ShopifyConnector scaffold never imported/registered into node","area":"board2","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json",r"06-EVIDENCE\BOARD2-SHOPIFY-DOMAIN-2026-08-23\RESULT.json"],"status":"UNWIRED","next_safe_probe":"Read-only import graph; no OAuth invent; no money unlock.","lane":"board2"},
  {"id":"U33","title":"Board2: OFN_WIRE_EMAIL/PUBLISH=1 dead flags (no .py readers)","area":"board2","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json"],"status":"FLAG_DRIFT","next_safe_probe":"Confirm env keys unread; propose disarm or wire doc; no live publish.","lane":"board2"},
  {"id":"U34","title":"Board2: Studio OF/adult-platform adapter ABSENT (telegram_channel-only publish)","area":"board2","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json",r"06-EVIDENCE\BOARD2-STUDIO-BATCH-QUEUE-2026-08-23"],"status":"UNWIRED","next_safe_probe":"Document absent adapters; do not invent OF/Fansly paths.","lane":"board2"},
  {"id":"U35","title":"Board2: ofn-marketing.timer present but disabled","area":"board2","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json"],"status":"PARTIAL","next_safe_probe":"Leave disabled unless owner GO; no auto studio cycle.","lane":"board2"},
  {"id":"U36","title":"Board2: hypno-fugu-mini /healthz 404 while /health 200","area":"board2","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json"],"status":"PARTIAL","next_safe_probe":"Align health contract or document /health as SoT; no secrets.","lane":"board2"},
  {"id":"U37","title":"Board2: Bluesky adapter scaffold never imported into node","area":"board2","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json"],"status":"UNWIRED","next_safe_probe":"Leave scaffold; no auto-post.","lane":"board2"},
  {"id":"U38","title":"Board2: Google Merchant Center / Content API sync path ABSENT","area":"board2","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2\UNDISCOVERED.json"],"status":"UNWIRED","next_safe_probe":"Do not invent merchant sync; catalog stays local until owner TDR.","lane":"board2"},
  {"id":"U39","title":"Pi: MQTT loopback SoT LIVE (127.0.0.1:1883 auth) vs stale CLOSED docs risk","area":"pi","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\PI\UNDISCOVERED.json"],"status":"FLAG_DRIFT","next_safe_probe":"Confirm LOCAL_LOOPBACK_AUTH_OPEN__WAN_KEEP_CLOSED SoT; refresh stale CLOSED docs; keep WAN closed.","lane":"pi"},
  {"id":"U40","title":"Pi: gateway allowlist freeze leaves non-diag cmds dark; laptop NATS client flaky","area":"pi","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\PI\UNDISCOVERED.json",r"06-EVIDENCE\OCTOPUS-EDGE-NEXT-2026-08-23\RECEIPT.json"],"status":"PARTIAL","next_safe_probe":"Keep allowlist freeze; optional laptop NATS path diagnose read-only; no ARM.","lane":"pi"},
  {"id":"U41","title":"Pi: doctor residual metrics_observation_age fail + ancient boot_report","area":"pi","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\PI\UNDISCOVERED.json"],"status":"PARTIAL","next_safe_probe":"Read-only doctor latest; refresh boot_report only with owner GO.","lane":"pi"},
  {"id":"U42","title":"Pi: THERMAL RANGE_CHECK quarantine residue still on disk","area":"pi","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\PI\UNDISCOVERED.json"],"status":"PARTIAL","next_safe_probe":"Confirm quarantine auto-clear vs hold; no PWM.","lane":"pi"},
  {"id":"U43","title":"Pi: NATS ACL / octopus-core E2E creds lifecycle + production ACL still open design","area":"pi","severity":"P1","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\PI\UNDISCOVERED.json"],"status":"PARTIAL","next_safe_probe":"Optional rotate if exposed; do not print secrets; design-only ACL expand.","lane":"pi"},
  {"id":"U44","title":"Pi: ESP32 Phase B / physical sensors still deferred","area":"pi","severity":"P2","evidence_paths":[r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\PI\UNDISCOVERED.json"],"status":"PARTIAL","next_safe_probe":"Keep deferred; software WAVE0 only until owner buy/estop.","lane":"pi"},
]

for e in extras:
    if e["id"] not in have:
        items.append(e)

# ranked top25 across lanes (manual priority)
top25_order = [
  "U01","U08","U29",  # P0 telegram/miniapp
  "U02","U03","U04","U07","U30",  # wiring/flags/connectors/miniapp
  "U09","U10","U39","U40","U43",  # cross-surface / pi
  "U31","U32","U33","U38",  # board2
  "U15","U16","U18","U27",  # epistemics/tech
  "U24","U06","U12",  # packs/arch/unwired
]
# ensure exist
ids = {i["id"]: i for i in items}
top25 = [ids[i] for i in top25_order if i in ids][:25]
# pad if needed
for i in items:
    if len(top25) >= 25: break
    if i["id"] not in {x["id"] for x in top25}:
        top25.append(i)

doc = {
  "schema": "octopus-undiscovered/1",
  "stamp_local": stamp,
  "timezone": "Australia/Sydney",
  "path": str(out),
  "constraints": base.get("constraints"),
  "known_excluded_reference_only": base.get("known_excluded_reference_only"),
  "lanes_merged": ["laptop", "board2", "pi", "reconcile"],
  "lane_sources": {
    "board2": r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\BOARD2",
    "pi": r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\PI",
    "reconcile": r"06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\RECONCILE.json",
  },
  "scan_focus": base.get("scan_focus"),
  "counts": {
    "items": len(items),
    "P0": sum(1 for i in items if i["severity"]=="P0"),
    "P1": sum(1 for i in items if i["severity"]=="P1"),
    "P2": sum(1 for i in items if i["severity"]=="P2"),
  },
  "top25_ids": [i["id"] for i in top25],
  "items": items,
}
(out/"UNDISCOVERED.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

lines = [
"# OCTOPUS UNDISCOVERED — SUMMARY (top 25)",
f"**Stamp (AEST):** {stamp}",
f"**Path:** `{out}`",
"**Constraints:** no invent · no live sendMessage · no money · no PWM · no secrets",
"",
"## Scope",
"Still-dark after 2026-08-23 waves. Merges laptop scan + BOARD2/ + PI/ lane packs + RECONCILE.md. Known G01–G25 / named packs = reference only.",
"",
f"## Counts (all items): P0={doc['counts']['P0']} P1={doc['counts']['P1']} P2={doc['counts']['P2']} total={doc['counts']['items']}",
"",
"| Rank | ID | Sev | Status | Area | Title |",
"|---:|---|---|---|---|---|",
]
for n, it in enumerate(top25, 1):
    lines.append(f"| {n} | {it['id']} | {it['severity']} | {it['status']} | {it.get('area','')} | {it['title']} |")
lines += [
"",
"## Category rollup",
"- **Telegram/MiniApp P0:** U01/U08/U29 live inbound + menu/public URL still dark.",
"- **WIRING/flags:** U02/U03/U30 hooks ON or consumers missing; Board2 U33 dead env flags.",
"- **Connectors:** U04 OAuth waiting; U05 probe queue.",
"- **Cross-surface:** U09 Board2 ports blind; U10/U40 laptop↔Pi NATS; U39 MQTT SoT; U43 NATS ACL.",
"- **Board2 business:** U31–U38 socials/Shopify/Merchant/marketing.timer/healthz.",
"- **Epistemics/evelab/tech:** U15–U16/U18/U27.",
"- **Arch/handoffs:** U06 unsliced DESIGN; U11 Wave-B patch; U12 4d consolidation.",
"",
"## Sibling lane packs",
"- `BOARD2/` — DietPi OFN deep refine",
"- `PI/` — OrangePi/sensorium after EDGE+HOMEO",
"- `RECONCILE.md` / `RECONCILE.json` — supersede notes",
"",
]
(out/"SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

method = (out/"METHOD.md").read_text(encoding="utf-8-sig")
if "lanes_merged" not in method:
    method += f"""

## Multi-lane merge ({stamp})
Also ingested parallel lane packs already present under this folder:
- `BOARD2/UNDISCOVERED.json` (OFN DietPi deep refine)
- `PI/UNDISCOVERED.json` (OrangePi after EDGE-NEXT + HOMEO-MIRROR-ALIGN)
- `RECONCILE.md` / `RECONCILE.json` (supersede + hot P0/P1 picks)

Laptop executor scan wrote root `UNDISCOVERED.json` + `SUMMARY.md` + `METHOD.md`, then merged unique Board2/Pi/reconcile items as U29–U44 without inventing.
"""
    (out/"METHOD.md").write_text(method, encoding="utf-8")

print("merged items", len(items), "top25", [i["id"] for i in top25])
for i in top25[:15]:
    print(f"{i['id']} [{i['severity']}/{i['status']}] {i['title']}")
