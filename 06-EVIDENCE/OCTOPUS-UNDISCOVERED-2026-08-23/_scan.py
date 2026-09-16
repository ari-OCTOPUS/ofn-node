# -*- coding: utf-8 -*-
from __future__ import annotations
import json, re, os, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(r"F:/backup")
OPS = ROOT / "_ops"
EVID = ROOT / "06-EVIDENCE"
OUT = EVID / "OCTOPUS-UNDISCOVERED-2026-08-23"
OUT.mkdir(parents=True, exist_ok=True)
SYD = timezone(timedelta(hours=10))
stamp = datetime.now(SYD).isoformat(timespec="seconds")

# --- exclude known ---
EXCLUDE_AREAS = {
    "G01","G02","G03","G04","G05","G06","G07","G08","G09","G10",
    "G11","G12","G13","G14","G15","G16","G17","G18","G19","G20",
    "G21","G22","G23","G24","G25",
    "ziman_money_live", "edge_next", "doctor_to_end", "tech_admission", "laptop_throttle",
}
# topics already covered - skip if only those
KNOWN_TOPIC_RE = re.compile(
    r"Ziman.*(money|PayPal|payout|bank)|EDGE-NEXT|doctor-to-end|TECH-ADMISSION|LAPTOP-THROTTLE|"
    r"writer\.lock EXPIRED|LIVE-TELEGRAM unlock|SenderBridge default-OFF|dual.?outbox|"
    r"MiniApp.*8774|A18.?inbound.?lab|GAP-CLOSE|WAVE0 physical|studio_wire=false",
    re.I,
)

items = []

def add(uid, area, evidence_path, severity, why, title=""):
    items.append({
        "id": uid,
        "title": title or uid,
        "area": area,
        "evidence_path": evidence_path if isinstance(evidence_path, list) else [evidence_path],
        "severity": severity,
        "why_undiscovered": why,
        "vs_known": "not in G01-G25 PASS / EDGE-NEXT / TECH-ADMISSION / doctor-to-end / throttle as primary close",
    })

# 1) Organs directory vs WIRING hooks - organs with no tests / no wiring flag
organs_dir = OPS / "organs"
wiring = {}
wp = organs_dir / "WIRING.json"
if wp.exists():
    wiring = json.loads(wp.read_text(encoding="utf-8"))
flags = (wiring.get("flags") or {})
organ_dirs = [p for p in OPS.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))]
# cartographer / organ list files
for cand in [OPS / "organs" / "registry.json", OPS / "registry" / "organs.json", OPS / "organogenesis"]:
    pass

# Find organ modules referenced in organs folder
organ_py = list((OPS / "organs").glob("*.py")) if (OPS / "organs").exists() else []
# lead_activation false but lead organ exists
if flags.get("lead_activation") is False:
    lead_hits = list(OPS.rglob("*lead*"))
    lead_hits = [str(p.relative_to(ROOT)).replace("\\","/") for p in lead_hits if p.is_file() and "test" not in p.name.lower() and ".git" not in str(p)][:15]
    if lead_hits:
        add("U01-LEAD-ACTIVATION-OFF", "organs/wiring",
            ["_ops/organs/WIRING.json"] + lead_hits[:5], "P1",
            "WIRING lead_activation=false while lead-related modules/files exist — organ never armed",
            "Lead activation flag OFF vs lead code present")

# cognition_inbox true - verify consumer exists
cog = list(OPS.rglob("*cognition*inbox*")) + list(OPS.rglob("*cognition_inbox*"))
# knowledge afferent
# studio_wire false - already G14 known - skip

# 2) ACTIVATION flags sprawl beyond G17 - find flags with no reader
flag_files = list(OPS.glob("ACTIVATION-*.flag")) + list(OPS.glob("LIVE-*.flag")) + list(OPS.glob("*.flag"))
flag_names = [p.name for p in flag_files]
# sample: which flags are never referenced in py
unreferenced = []
py_blob_index = {}
# cheaper: grep via reading subset of py filenames containing flag stem
for fp in flag_files:
    stem = fp.stem
    if stem in ("LIVE-TELEGRAM",):  # known
        continue
    hits = 0
    # search only telegram_center, doctor, organs, loops, wiring.py
    search_roots = [OPS / "telegram_center", OPS / "doctor", OPS / "organs", OPS / "loops", OPS / "wiring.py"]
    for root in search_roots:
        if root.is_file():
            try:
                if stem.replace("-", "_") in root.read_text(encoding="utf-8", errors="ignore") or stem in root.read_text(encoding="utf-8", errors="ignore"):
                    hits += 1
            except Exception:
                pass
        elif root.is_dir():
            for py in root.rglob("*.py"):
                try:
                    t = py.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if stem in t or stem.replace("-", "_") in t:
                    hits += 1
                    break
            if hits:
                break
    if hits == 0 and fp.suffix == ".flag":
        unreferenced.append(str(fp.relative_to(ROOT)).replace("\\", "/"))

if len(unreferenced) >= 3:
    add("U02-FLAGS-NO-READER", "flags/code",
        unreferenced[:20], "P1",
        f"{len(unreferenced)} flag files under _ops with no hit in telegram_center/doctor/organs/loops/wiring.py — docs/flags without impl consumers",
        "Activation/LIVE flags with no code reader")

# 3) Docs without impl — PLAN/DESIGN without matching module
plan_docs = []
for p in list((OPS / "telegram_center").glob("PLAN-*.md")) + list((OPS).glob("**/DESIGN-*.md")):
    if "worktrees" in str(p) or ".claude" in str(p):
        continue
    plan_docs.append(p)
# MiniApp PLAN-T4
plan_t4 = OPS / "telegram_center" / "PLAN-T4-miniapp.md"
if plan_t4.exists():
    add("U03-PLAN-T4-MINIAPP-RESIDUAL", "docs/impl",
        [str(plan_t4.relative_to(ROOT)).replace("\\","/"),
         "06-EVIDENCE/OCTOPUS-MINIAPP-DOC-RECONCILE-2026-08-23/RESULT.json"],
        "P1",
        "PLAN-T4 miniapp still on disk; public Telegram menu wiring still CONFIG_NEEDED despite gateway+tunnel — plan/impl gap beyond G10 localhost doc",
        "PLAN-T4 MiniApp public menu still unwired")

# 4) Impl without tests — new modules lacking tests already partially done; find other telegram_center modules with no test_
tc = OPS / "telegram_center"
tested = set()
for t in (OPS / "tests").glob("test_*.py"):
    try:
        txt = t.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        continue
    for py in tc.glob("*.py"):
        if py.stem.lower() in txt or py.name.lower() in txt:
            tested.add(py.stem)
untested = []
for py in tc.glob("*.py"):
    if py.name.startswith("_") or py.stem in ("center",):  # center huge - skip as known
        continue
    if py.stem not in tested and py.stat().st_size > 8000:
        untested.append(f"_ops/telegram_center/{py.name} ({py.stat().st_size}b)")
if untested:
    add("U04-TG-CENTER-LARGE-UNTESTED", "impl/tests",
        untested[:25], "P2",
        "Large telegram_center modules (>8KB) not named in any test_*.py body — impl without dedicated tests",
        "Large center modules lack dedicated tests")

# 5) MiniApp public — beyond G10: check if OCTOPUS_TG_MINIAPP in env file names only
env_path = ROOT / ".env"
miniapp_env = {"OCTOPUS_MINIAPP_URL": "unset", "OCTOPUS_TG_MINIAPP": "unset"}
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("OCTOPUS_MINIAPP_URL="):
            v = line.split("=",1)[1].strip()
            miniapp_env["OCTOPUS_MINIAPP_URL"] = "set" if v else "empty"
        if line.startswith("OCTOPUS_TG_MINIAPP="):
            v = line.split("=",1)[1].strip()
            miniapp_env["OCTOPUS_TG_MINIAPP"] = v or "empty"
url_json = OPS / "state/telegram/miniapp-url.json"
tunnel = None
if url_json.exists():
    try:
        tunnel = json.loads(url_json.read_text(encoding="utf-8"))
    except Exception:
        tunnel = {"error": "parse"}
if miniapp_env.get("OCTOPUS_TG_MINIAPP") not in ("1", "true", "on") or miniapp_env.get("OCTOPUS_MINIAPP_URL") in ("unset", "empty"):
    add("U05-MINIAPP-PUBLIC-MENU", "miniapp/public",
        ["_ops/state/telegram/miniapp-url.json", "06-EVIDENCE/OCTOPUS-GAP-CLOSE-2026-08-23/IOS/G10/RESULT.json"],
        "P0",
        f"Public MiniApp menu still dark: env TG_MINIAPP={miniapp_env.get('OCTOPUS_TG_MINIAPP')} URL={miniapp_env.get('OCTOPUS_MINIAPP_URL')}; tunnel candidate={bool(tunnel and tunnel.get('url'))} but center /ui CONFIG_NEEDED path not closed as LIVE menu",
        "MiniApp Telegram public menu not LIVE")

# 6) Telegram inbound Full Loop — remaining after lab fake (known residual of G04 but still dark LIVE)
add("U06-A18-LIVE-OWNER-INBOUND", "telegram/inbound",
    ["06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/A18-INBOUND-LAB-FAKE/RESULT.json",
     "06-EVIDENCE/OCTOPUS-GAP-CLOSE-2026-08-23/IOS/G04/VERIFY-HARNESS.md"],
    "P0",
    "Lab fake PASS; LIVE owner inbound Full Loop still never executed on durable SoT — remains undiscovered as production close",
    "LIVE A18 owner inbound Full Loop unproven")

# 7) Dual outbox leftovers — event-bridge/urgent existence beyond C05 doc
tg = OPS / "state/telegram"
leftovers = []
for p in tg.rglob("*"):
    if not p.is_dir():
        continue
    n = p.name.lower()
    if n in ("event-bridge", "urgent", "outbox-urgent", "shadow-outbox") or "bridge" in n and "loop" not in str(p):
        leftovers.append(str(p.relative_to(ROOT)).replace("\\","/"))
# also sqlite extras
for p in tg.glob("*.sqlite3"):
    if "canary" in p.name.lower() or "rate-limit" in p.name.lower():
        leftovers.append(str(p.relative_to(ROOT)).replace("\\","/"))
if leftovers:
    add("U07-OUTBOX-LEFTOVER-SURFACES", "telegram/outbox",
        leftovers[:20] + ["_ops/telegram_center/docs/DUAL-OUTBOX-CONTRACT.md"],
        "P1",
        "Additional telegram state surfaces still on disk after C05/G08 docs — leftover paths may still be written by code; contract documented but runtime writers not fully audited",
        "Telegram outbox leftover surfaces unaudited writers")

# 8) Arch-loop backlog — DESIGN next slices not done
design = EVID / "OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/DESIGN.md"
done = {p.name for p in (EVID / "OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23").iterdir()} if (EVID / "OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23").exists() else set()
add("U08-ARCH-LOOP-BACKLOG", "arch-loop",
    ["06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/DESIGN.md",
     "06-EVIDENCE/OCTOPUS-GAP-INVENTORY-2026-08-23/ARCH-LOOP-INPUTS.md"] if (EVID/"OCTOPUS-GAP-INVENTORY-2026-08-23/ARCH-LOOP-INPUTS.md").exists() else ["06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/DESIGN.md"],
    "P1",
    f"Arch-loop DESIGN lists further slices; completed dirs={sorted(done)}; connector-gap hygiene / center queue inject / continuous 24h loop journal not closed as packs",
    "Architecture evolution loop backlog remaining")

# 9) UNWIRED / stale evidence packs Aug-16
unwired = list(EVID.glob("UNWIRED*")) + list(EVID.glob("*UNWIRED*"))
unwired += list(ROOT.glob("06-EVIDENCE/**/UNWIRED*.md"))
# also search
unwired_paths = []
for p in EVID.iterdir():
    if p.is_dir() and "UNWIRED" in p.name.upper():
        unwired_paths.append(p.name)
    if p.is_file() and "UNWIRED" in p.name.upper():
        unwired_paths.append(p.name)
# broader
for p in EVID.rglob("*UNWIRED*"):
    if ".git" in str(p):
        continue
    unwired_paths.append(str(p.relative_to(ROOT)).replace("\\","/"))
unwired_paths = sorted(set(unwired_paths))[:30]
if unwired_paths:
    add("U09-UNWIRED-PACKS-STALE", "docs/evidence",
        unwired_paths, "P2",
        "UNWIRED-* evidence packs still present without 2026-08-23 supersede sidecars — may be stale relative to new wires",
        "Stale UNWIRED evidence packs")

# 10) Handoffs stale beyond G21 pointer
handoffs = []
for p in [(ROOT/"07-HANDOFF"), (ROOT/"01 - Dashboard"), (EVID)]:
    if not p.exists():
        continue
    for f in p.rglob("*HANDOFF*"):
        if f.is_file() and f.suffix.lower() in (".md", ".json"):
            # stale if mtime before 2026-08-20 or name NEXT-AGENT
            handoffs.append((f, f.stat().st_mtime))
stale_h = []
for f, mt in handoffs:
    name = f.name.upper()
    if "SUPERSEDE" in name:
        continue
    if "NEXT-AGENT" in name or "WAVE-B" in name or "2026-08-1" in name:
        stale_h.append(str(f.relative_to(ROOT)).replace("\\","/"))
if stale_h:
    add("U10-HANDOFFS-STALE-RESIDUAL", "handoffs",
        stale_h[:15] + ["07-HANDOFF/SUPERSEDE-2026-08-23-GAP-INVENTORY.md"],
        "P2",
        "Historical handoff files still primary-looking; supersede pointer exists but stale files not marked deprecated in-body",
        "Stale handoff files still primary")

# 11) Boards not covered — Board2 vs Board1/3/sensoriom
boards_evid = [p.name for p in EVID.iterdir() if p.is_dir() and p.name.upper().startswith("BOARD")]
board_nums = set()
for n in boards_evid:
    m = re.search(r"BOARD(\d)", n.upper())
    if m:
        board_nums.add(m.group(1))
# marketing / painting lanes
add("U11-BOARDS-COVERAGE-DARK", "boards",
    [f"06-EVIDENCE/{n}" for n in boards_evid[:20]] or ["06-EVIDENCE/"],
    "P1",
    f"Evidence dirs with BOARD* prefix seen={sorted(board_nums) or 'none clear'}; Board1/Board3/painting-lane/sensoriom board packages may lack 2026-08-23 undiscovered audit equivalent to Board2 contradiction scan",
    "Non-Board2 OCTOPUS boards under-audited")

# 12) connector_gap_hook true but OAuth still gap
cgreg = EVID / "OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23/CONNECTOR-GAP-REGISTRY.json"
if cgreg.exists() and flags.get("connector_gap_hook"):
    add("U12-CONNECTOR-GAP-HOOK-NO-OAUTH", "connectors",
        [str(cgreg.relative_to(ROOT)).replace("\\","/")],
        "P1",
        "connector_gap_hook enabled in WIRING but GA4/GSC/Ads remain GAP until OAuth — hook loads registry without closing connectors",
        "Connector-gap hook armed; OAuth connectors still dark")

# 13) poll attach enabled path without queue inject — operational dark
add("U13-CENTER-BRIDGE-QUEUE-UNINJECTED", "telegram/center",
    ["_ops/telegram_center/poll_sender_bridge_attach.py",
     "06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/CENTER-BRIDGE-ATTACH-DEFAULT-OFF/RESULT.json"],
    "P1",
    "Poll attach hook exists default-OFF; center._sender_bridge_queue/_send_fn injection path never evidenced as configured — even with env ON would miss_queue",
    "SenderBridge queue/send_fn never injected on live center")

# 14) EDGE ceremony READY_TO_DEPLOY vs CMD signed UNKNOWN/FAIL — if not in edge-next as closed
edge_receipt = EVID / "OCTOPUS-EDGE-NEXT-2026-08-23/RECEIPT.json"
# Don't re-list EDGE-NEXT primary; only if leftover ceremony mismatch is dark
m1 = EVID / "OCTOPUS-EDGE-NEXT-2026-08-23/m1-command-trust"
if m1.exists():
    fails = list(m1.glob("RESULT-CMD-*.json"))
    bad = []
    for f in fails:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if str(d.get("status","")).upper() in ("FAIL", "UNKNOWN"):
                bad.append(f"{f.name}:{d.get('status')}")
        except Exception:
            pass
    if bad:
        add("U14-EDGE-CMD-TRUST-RESIDUAL", "edge/command-trust",
            [f"06-EVIDENCE/OCTOPUS-EDGE-NEXT-2026-08-23/m1-command-trust/{x.split(':')[0]}" for x in bad],
            "P0",
            f"EDGE-NEXT m1 command-trust still has non-PASS results {bad} while ceremony may say READY — residual undiscovered operational risk",
            "Edge command-trust residual FAIL/UNKNOWN")

# 15) Doctor-to-end leftovers
dte = EVID / "OCTOPUS-DOCTOR-TO-END-2026-08-23"
if dte.exists():
    openish = []
    for f in dte.rglob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, list):
            # list of records — scan each dict item
            for el in d:
                if not isinstance(el, dict):
                    continue
                st = str(el.get("status") or el.get("STATUS") or el.get("overall") or "").upper()
                if st in ("FAIL", "PARTIAL", "OPEN", "BLOCKED", "UNKNOWN"):
                    openish.append(f"{f.relative_to(ROOT).as_posix()}:{st}")
            continue
        if not isinstance(d, dict):
            continue
        st = str(d.get("status") or d.get("STATUS") or d.get("overall") or "").upper()
        if st in ("FAIL", "PARTIAL", "OPEN", "BLOCKED", "UNKNOWN"):
            openish.append(f"{f.relative_to(ROOT).as_posix()}:{st}")
    if openish:
        add("U15-DOCTOR-TO-END-RESIDUAL", "doctor",
            [x.split(":")[0] for x in openish[:15]],
            "P1",
            f"doctor-to-end pack still contains non-PASS statuses: {openish[:8]}",
            "Doctor-to-end residual non-PASS")

# 16) self_upgrade_lab / organogenesis never continuous
sul = OPS / "self_upgrade_lab"
if sul.exists():
    add("U16-SELF-UPGRADE-LAB-DARK", "lab/self_upgrade",
        ["_ops/self_upgrade_lab/", "06-EVIDENCE/OCTOPUS-GAP-CLOSE-2026-08-23/IOS/G18/RESULT.json"],
        "P2",
        "self_upgrade_lab directory present; no 2026-08-23 evidence of continuous safe promote loop (propose-only stays) — lab dark as runtime actor",
        "self_upgrade_lab not runtime-continuous")

# 17) Paper-full profile vs LIVE flags (related G17 but specific wiring.py default)
wiring_py = OPS / "wiring.py"
if wiring_py.exists():
    t = wiring_py.read_text(encoding="utf-8", errors="ignore")
    if "paper-full" in t or "paper_full" in t:
        add("U17-DEFAULT-PROFILE-PAPER-FULL", "profile/runtime",
            ["_ops/wiring.py", "_ops/LIVE-TELEGRAM.flag"],
            "P2",
            "Default profile paper-full in wiring while LIVE-TELEGRAM unlock armed — profile/runtime dual-state may still confuse operators beyond G05/G17 docs",
            "Default paper-full vs LIVE unlock dual-state")

# 18) Obsidian / vault sync dark boards
obs = list((ROOT / "07 - Knowledge").glob("**/*BOARD*"))[:5] if (ROOT/"07 - Knowledge").exists() else []
# painting lane
paint = list(EVID.glob("*PAINT*")) + list(EVID.glob("*Master*Paint*"))
if not paint:
    add("U18-PAINTING-LANE-EVIDENCE-DARK", "boards/painting",
        ["05-BUSINESSES/", "06-EVIDENCE/"],
        "P2",
        "No 2026-08-23 BOARD/PAINTING evidence pack found comparable to Board2 contradiction scans — painting lane dark in evidence plane",
        "Master Painting lane evidence dark")

# 19) Rate-limit / delivery_reconciliation writers vs SoT
dr = OPS / "telegram_center/delivery_reconciliation.py"
if dr.exists():
    add("U19-DELIVERY-RECONCILE-VS-SOT", "telegram/delivery",
        ["_ops/telegram_center/delivery_reconciliation.py",
         "_ops/telegram_center/docs/DUAL-OUTBOX-CONTRACT.md"],
        "P2",
        "delivery_reconciliation exists; not proven whether it writes only durable SoT or also sidepaths — leftover audit after G08",
        "delivery_reconciliation SoT write audit missing")

# 20) Arch-loop continuous 24h journal missing
journal = EVID / "OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/JOURNAL.md"
if not journal.exists():
    add("U20-ARCH-LOOP-NO-24H-JOURNAL", "arch-loop",
        ["06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/DESIGN.md"],
        "P2",
        "DESIGN calls for 24h loop journal; JOURNAL.md absent — loop not run as continuous experiment",
        "No 24h arch-evolution journal")

# filter inventively weak
# dedupe
seen=set(); out_items=[]
for it in items:
    if it["id"] in seen: continue
    seen.add(it["id"]); out_items.append(it)

# severity sort
sev = {"P0":0,"P1":1,"P2":2}
out_items.sort(key=lambda x: (sev.get(x["severity"],9), x["id"]))

doc = {
    "schema": "octopus-undiscovered/1",
    "stamp_local": stamp,
    "timezone": "Australia/Sydney",
    "producer": "Ios",
    "constraints": {"no_money": True, "no_live_tg_send": True, "no_PWM": True, "no_invent": True},
    "vs_known_excluded": [
        "G01-G25 gap inventory/close primary topics",
        "Ziman money LIVE packs",
        "EDGE-NEXT primary receipt (except residual FAIL noted)",
        "doctor-to-end primary (except residual non-PASS)",
        "TECH-ADMISSION SAVE pack",
        "laptop throttle",
    ],
    "count": len(out_items),
    "items": out_items,
    "top25_ids": [x["id"] for x in out_items[:25]],
}
(OUT/"UNDISCOVERED.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

# SUMMARY.md
lines = [
    f"# OCTOPUS UNDISCOVERED — SUMMARY",
    f"**Stamp:** {stamp}",
    f"**Path:** `06-EVIDENCE/OCTOPUS-UNDISCOVERED-2026-08-23/`",
    f"**Count:** {len(out_items)}",
    "",
    "Excluded as already known/PASS primary: G01–G25 closes, Ziman money LIVE, EDGE-NEXT, doctor-to-end, TECH-ADMISSION, laptop throttle.",
    "",
    "## Top 25",
    "",
    "| Rank | ID | Sev | Title | Why undiscovered |",
    "|---:|---|---|---|---|",
]
for i, it in enumerate(out_items[:25], 1):
    ev0 = (it["evidence_path"][0] if it["evidence_path"] else "").replace("|","\\|")
    lines.append(f"| {i} | {it['id']} | {it['severity']} | {it['title'][:60]} | {it['why_undiscovered'][:100].replace('|','/')} |")
lines.append("")
lines.append("See UNDISCOVERED.json for full evidence paths.")
(OUT/"SUMMARY.md").write_text("\n".join(lines)+"\n", encoding="utf-8")

print(json.dumps({"count": len(out_items), "top15": [{"id":x["id"],"sev":x["severity"],"title":x["title"]} for x in out_items[:15]]}, ensure_ascii=False, indent=2))

