# -*- coding: utf-8 -*-
from __future__ import annotations
import json, time
from pathlib import Path

ROOT = Path(r"F:/backup")
EVID = ROOT / "06-EVIDENCE"
OUT = EVID / "OCTOPUS-GAP-INVENTORY-2026-08-23"
LOOP = EVID / "OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23"
OUT.mkdir(parents=True, exist_ok=True)
LOOP.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y-%m-%dT%H:%M:%S+10:00")

gaps = []

def add(gid, title, kind, severity, status, cite, note=""):
    gaps.append({
        "id": gid,
        "title": title,
        "kind": kind,  # unfinished|disconnected|missing|policy_hold|dual_path
        "severity": severity,
        "status": status,
        "evidence": cite if isinstance(cite, list) else [cite],
        "note": note,
        "source_agent": "Ios",
    })

# --- CONNECTOR-GAP ---
cpath = EVID / "OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23" / "CONNECTOR-GAP-REGISTRY.json"
if cpath.exists():
    try:
        reg = json.loads(cpath.read_text(encoding="utf-8"))
        items = reg.get("gaps") or reg.get("connectors") or reg.get("items") or []
        if isinstance(reg, dict) and not items:
            # try nested
            for k,v in reg.items():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    items = v
                    break
        for i, it in enumerate(items if isinstance(items, list) else []):
            name = it.get("name") or it.get("id") or it.get("connector") or f"connector-{i}"
            st = it.get("status") or it.get("state") or "GAP"
            add(f"CONN-{name}", f"Connector gap: {name}", "missing", "high" if str(st).upper()=="GAP" else "med",
                str(st), str(cpath), it.get("note") or it.get("marks_gap_until_oauth") or "")
    except Exception as e:
        add("CONN-REGISTRY-READ", "CONNECTOR-GAP-REGISTRY read issue", "unfinished", "low", "ERROR", str(cpath), type(e).__name__)

# --- CONTINUOUS MISSION PARTIAL ---
stpath = EVID / "OCTOPUS-CONTINUOUS-MISSION-2026-08-23" / "STATUS.json"
if stpath.exists():
    st = json.loads(stpath.read_text(encoding="utf-8"))
    for row in st.get("PARTIAL_BLOCKED") or []:
        add(f"MISSION-{row.get('id')}", row.get("id"), "unfinished", "med", row.get("status"), str(stpath), row.get("note") or "")
    for row in st.get("NEXT") or []:
        if row.get("gate") == "optional":
            add(f"NEXT-{row.get('id')}", row.get("id"), "unfinished", "med", "OPTIONAL", str(stpath), row.get("action") or "")
    # epistemics advisory not phenomenal — note as architecture boundary not gap
    if st.get("epistemics_wire"):
        add("EPISTEMICS-ADVISORY-ONLY", "Epistemics ON_ADVISORY_LIVE (not TG path / not self-aware claim)", "policy_hold", "low",
            st.get("epistemics_wire"), str(stpath), "Do not treat as intelligence unlock")

# --- laptop contradiction scan C-list still open ---
cscan = EVID / "OCTOPUS-CONTRADICTION-SCAN-2026-08-23" / "CONTRADICTIONS.json"
if cscan.exists():
    d = json.loads(cscan.read_text(encoding="utf-8"))
    for it in d.get("contradictions") or []:
        cid = it.get("id") or ""
        # mark which were addressed
        addressed = {
            "C02-LIVE-FLAG-ENABLED-BUT-PATHS-DRY-RUN": "WIRED_PARTIAL (gate+organ; center reload PASS live_mode=true send=false)",
            "C03-SENDERBRIDGE-DEFAULT-OFF-NOT-IMPORTED-BY-CENTER": "WIRED_PARTIAL (owner_gated helper default-off; not poll-loop)",
            "C01-A18-TRUTH-BLOCKED-VS-CANARY-PASS": "RECONCILED_PARTIAL (labels/sidecars)",
        }
        status = addressed.get(cid, "OPEN")
        if status == "OPEN" and cid.startswith("C"):
            add(cid, it.get("claim", cid)[:120], "disconnected", it.get("severity") or "med", status,
                it.get("evidence_paths") or [str(cscan)], (it.get("suggested_fix") or "")[:200])
        elif status != "OPEN":
            add(cid, it.get("claim", cid)[:120], "disconnected", "low", status,
                it.get("evidence_paths") or [str(cscan)], "post wire-fix / reconcile")

# --- Ios surface ---
add("IOS-NO-PHONE-PAIR", "Ios agent has no direct phone/iOS device connector", "missing", "med", "OPEN",
    "agent profile empty + GetMcpServerStatus Phantom-only", "Phone media only via browser proxies")
add("IOS-WHATSAPP-UNAUTH", "WhatsApp Web phone-login never completed for photo access", "unfinished", "low", "OPEN",
    "Ios audit.jsonl web.whatsapp.com nav", "User session abandoned / interrupted")
add("MINIAPP-PUBLIC-URL", "MiniApp public/Telegram URL CONFIG_NEEDED (localhost:8774 live)", "missing", "med", "DOCUMENTED",
    str(EVID / "OCTOPUS-MINIAPP-DOC-RECONCILE-2026-08-23" / "RESULT.json"), "process live ≠ public URL")
add("A18-INBOUND-FULL-LOOP", "A18 Full Loop inbound durable_loop CLOSED not proven (outbound canary PASS)", "unfinished", "high", "OPEN",
    str(EVID / "OCTOPUS-A18-OWNER-CHAT-CANARY-2026-08-23" / "VERIFY.json"), "optional NEXT gate")
add("C05-DUAL-OUTBOX", "Canary sqlite vs durable loop outbox dual path", "dual_path", "high", "BY_DESIGN_OPEN",
    str(cscan), "Do not merge; durable is SoT for organism LIVE claims")
add("TG-SEND-STILL-GATED", "live_mode_allowed=true but send_allowed=false without send_exceptions", "policy_hold", "med", "INTENDED",
    str(EVID / "OCTOPUS-CENTER-RELOAD-TG-GATE-2026-08-23") if (EVID / "OCTOPUS-CENTER-RELOAD-TG-GATE-2026-08-23").exists() else str(EVID / "OCTOPUS-TELEGRAM-WIRE-FIX-2026-08-23" / "RESULT.json"),
    "Unlock ≠ send")
add("MONEY-WIRES-OFF", "Mining/crypto/accounting money unlock forbidden", "policy_hold", "high", "LOCKED_OFF",
    "writer lock forbidden paid + owner policy", "Arch loop must NOT unlock money")
add("WAVE0-ACTUATORS", "WAVE0 actuators observe-only / no physical e-stop unlock in loop", "policy_hold", "high", "LOCKED",
    "user memory + Orange Pi receipts", "Arch loop lab-only")
add("STUDIO-CAPTIONS", "Studio captions still open / batch held", "unfinished", "low", "PARTIAL",
    str(stpath), "Board2 lane")
add("ZIMAN-BANK-NOON", "Ziman bank/PayPal/ABN pending Maliheh noon", "unfinished", "med", "PARTIAL_PENDING",
    str(stpath), "Business not architecture")

# DISCOVER next actions if present
dpath = EVID / "OCTOPUS-CONTINUOUS-DISCOVER-2026-08-23" / "DISCOVER.json"
if dpath.exists():
    try:
        disc = json.loads(dpath.read_text(encoding="utf-8"))
        for key in ("next_action_p0", "next_actions", "open_gaps", "gaps"):
            val = disc.get(key)
            if isinstance(val, list):
                for i, row in enumerate(val[:25]):
                    if isinstance(row, dict):
                        add(f"DISCOVER-{row.get('id') or i}", str(row.get("action") or row.get("title") or row)[:140],
                            "unfinished", "med", "FROM_DISCOVER", str(dpath), str(row.get("note") or "")[:200])
                    else:
                        add(f"DISCOVER-{i}", str(row)[:140], "unfinished", "med", "FROM_DISCOVER", str(dpath), "")
            elif isinstance(val, dict):
                add(f"DISCOVER-{key}", str(val.get("action") or val)[:140], "unfinished", "med", "FROM_DISCOVER", str(dpath), "")
        # a18_wave if present
        a18 = disc.get("a18_wave") or disc.get("A18") or {}
        if isinstance(a18, dict) and a18:
            add("DISCOVER-A18", f"DISCOVER A18 status={a18.get('status') or a18.get('A18_status')}", "unfinished", "med",
                str(a18.get("status") or a18.get("A18_status") or "noted"), str(dpath), str(a18.get("code_note") or "")[:200])
    except Exception as e:
        add("DISCOVER-READ", "DISCOVER.json parse issue", "unfinished", "low", "ERROR", str(dpath), type(e).__name__)

# doctor/evelab evidence presence for design inputs
doctor_evelab = EVID / "OCTOPUS-EVELAB-DOCTOR-WIRE-2026-08-23"
add("LAB-EVELAB-DOCTOR", "EveLab↔doctor wire exists (use in 24h loop)", "unfinished" if not doctor_evelab.exists() else "disconnected",
    "med", "PRESENT" if doctor_evelab.exists() else "MISSING_PACK", str(doctor_evelab), "Simulation/lab substrate")

# de-dupe by id keep first
seen=set(); uniq=[]
for g in gaps:
    if g["id"] in seen: continue
    seen.add(g["id"]); uniq.append(g)
gaps=uniq

# rank: open high first
sev_order={"critical":0,"high":1,"med":2,"medium":2,"low":3}
stat_open={"OPEN","FROM_DISCOVER","OPTIONAL","PARTIAL","PARTIAL_PENDING","BY_DESIGN_OPEN","DOCUMENTED","ERROR","MISSING_PACK"}
ranked=sorted(gaps, key=lambda g: (0 if g["status"] in stat_open or "OPEN" in str(g["status"]) else 1, sev_order.get(str(g["severity"]).lower(), 9), g["id"]))

inventory={
    "schema": "octopus-gap-inventory/1",
    "agent": "Ios",
    "stamp_local": stamp,
    "timezone": "Australia/Sydney",
    "method": "harvest existing evidence packs; no invent; no secrets",
    "constraints": {"no_live_send": True, "no_money_unlock": True, "no_force_git": True, "no_self_aware_claims": True},
    "counts": {"total": len(gaps), "by_kind": {}, "by_status": {}},
    "gaps": ranked,
    "top_for_ari": [],
}
for g in gaps:
    inventory["counts"]["by_kind"][g["kind"]] = inventory["counts"]["by_kind"].get(g["kind"],0)+1
    inventory["counts"]["by_status"][g["status"]] = inventory["counts"]["by_status"].get(g["status"],0)+1

top=[]
for g in ranked:
    if g["status"] in ("INTENDED","LOCKED_OFF","LOCKED","WIRED_PARTIAL","RECONCILED_PARTIAL","PRESENT") and g["kind"]=="policy_hold":
        continue
    if g["severity"] in ("high","critical") or g["status"] in ("OPEN","BY_DESIGN_OPEN","OPTIONAL","FROM_DISCOVER","DOCUMENTED","PARTIAL","PARTIAL_PENDING"):
        top.append({"id": g["id"], "severity": g["severity"], "status": g["status"], "title": g["title"]})
    if len(top) >= 15: break
inventory["top_for_ari"]=top

(OUT/"IOS-GAPS.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(OUT/"GAPS.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

design = f'''# OCTOPUS Architecture Evolution Loop — DESIGN outline
stamp_local: {stamp}
author_contrib: Ios (laptop child) — ari synthesizes / owns merge gate
schema: octopus-arch-evolution-loop-design/0.1

## Goal (24h, SAFE)
Run a bounded **internal architecture-improvement loop** using doctor + evelab + simulation in a **lab worktree**.
Produce **proposed patches + tests**. **Human/ari merge gate** only.
Improve wiring, contracts, evidence hygiene, and dry-run fidelity — **not** "become smarter / self-aware".

## Hard NO
- NO money unlock (mining/crypto/accounting/paid)
- NO auto `git push` / force-push / history rewrite
- NO claims of becoming smarter, conscious, or self-aware
- NO WAVE0 actuator unlock / physical e-stop purchase lane
- NO unrestricted live Telegram `sendMessage` (flag unlock ≠ send; need send_exceptions)
- NO secrets in evidence

## YES / allowed substrate
- Lab worktree under F:/backup (or dedicated worktree) — reversible
- doctor uniqueness / EveLab doctor wire (cite `06-EVIDENCE/OCTOPUS-EVELAB-DOCTOR-WIRE-2026-08-23`)
- Simulation / dry-run transports (fake send_fn, fixture outbox)
- `live_telegram_gate` evaluate-only + SenderBridge dry refused path
- Epistemics **advisory metrics only** (no phenomenal claims)
- Patch proposals with pytest; evidence packs under `06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/`

## Loop cadence (24h sketch)
1. **Select** ≤3 GAPs from inventory (prefer disconnected/unfinished architecture, not business noon tasks)
2. **Simulate** in lab: doctor tick + evelab scenario + dry TelegramOrgan/SenderBridge gate
3. **Propose** minimal reversible patch + tests in worktree
4. **Evidence** RESULT.json (pass/fail, no secrets)
5. **Stop** for ari/owner merge gate — no auto merge/push
6. **Repeat** until wall clock 24h or 3 merges proposed

## Candidate first slices (from inventory)
1. A18 inbound Full Loop prove path (durable_loop CLOSED) — lab fake inbound first
2. Center poll-loop optional attach to `owner_gated_sender_bridge_run_once` still default-off + tests
3. C05 documentation/contract: durable outbox SoT vs canary sqlite non-SoT (no merge)
4. CONNECTOR-GAP GA4/GSC/Ads — registry hygiene only (no OAuth invent)
5. MiniApp: keep localhost documented; optional lab UI smoke without publishing URL

## Success metrics (architecture, not IQ)
- New tests green in lab
- Fewer OPEN high-severity architecture GAPs
- Gate invariants hold: `live_mode_allowed` may be true while `send_allowed` false without exceptions
- Zero money/WAVE0/force-git violations in loop journal

## Rollback
- Delete lab worktree branch / restore `.bak-*`
- Do not touch production center PID unless owner GO (already demonstrated reload path)

## References
- Gap inventory: `06-EVIDENCE/OCTOPUS-GAP-INVENTORY-2026-08-23/IOS-GAPS.json`
- TG wire fix: `06-EVIDENCE/OCTOPUS-TELEGRAM-WIRE-FIX-2026-08-23/RESULT.json`
- Center reload gate: `06-EVIDENCE/OCTOPUS-CENTER-RELOAD-TG-GATE-2026-08-23` (if present)
- Contradiction scan: `06-EVIDENCE/OCTOPUS-CONTRADICTION-SCAN-2026-08-23/CONTRADICTIONS.json`
- Continuous mission: `06-EVIDENCE/OCTOPUS-CONTINUOUS-MISSION-2026-08-23/STATUS.json`

## Open for ari
- Confirm lab worktree path naming
- Confirm max parallel slices (recommend 1–2)
- Owner GO before any center reload during loop
'''
(LOOP/"DESIGN.md").write_text(design, encoding="utf-8")

print("gaps", len(gaps))
print("top", json.dumps(top, ensure_ascii=False, indent=2))
print("WROTE", OUT/"IOS-GAPS.json")
print("WROTE", LOOP/"DESIGN.md")
