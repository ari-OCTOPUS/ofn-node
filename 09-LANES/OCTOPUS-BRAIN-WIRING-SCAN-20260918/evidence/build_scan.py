#!/usr/bin/env python3
"""Build BRAIN-WIRING-SCAN deliverables from measured evidence (2026-09-18)."""
import csv
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent
NOW = "2026-09-18T02:00:00Z"

# ---------------------------------------------------------------- brains
BRAINS = [
 # id, name, kind, provider/model, callers, calls_per_day, cost, evidence
 ("BR-01", "deepseek-flash (primary paid)", "external", "deepseek", "api_budget.reserve/settle via broker", 28, "$0.80/mo",
  "138:state/api-budget/budget-ledger.jsonl (28 reserve rows)"),
 ("BR-02", "sakana-fugu", "external", "sakana-fugu/fugu", "providers.py, think_pool.py, api_budget.py (+4)", 5, "included",
  "138:budget-ledger (5 rows) + grep consumers=7"),
 ("BR-03", "gpt-5.6-terra", "external", "openai", "api_budget failover", 5, "included", "138:budget-ledger (5 rows)"),
 ("BR-04", "claude-sonnet-5", "external", "anthropic", "api_budget failover", 4, "included", "138:budget-ledger (4 rows)"),
 ("BR-05", "gemini-3.8-flash", "external", "gemini", "api_budget failover", 3, "included", "138:budget-ledger (3 rows)"),
 ("BR-06", "local tier (free)", "local", "local-insufficient route", "api_budget.py (1 consumer)", 0, "$0",
  "138:grep local-insufficient → 1 file"),
 ("BR-07", "ops_agent decision-code", "decision-code", "python", "octopus-ops-agent.timer (~5min)", 288, "$0",
  "138:state/ops-agent/ops_agent.py 1342 lines, mtime 09-18T01:51"),
 ("BR-08", "owner_reply (owner vote brain)", "decision-code", "python", "octopus-owner-reply.timer (1min)", 1440, "$0",
  "138:state/revenue-drive/owner_reply.py, alive"),
 ("BR-09", "owner_ask (card builder)", "decision-code", "python", "octopus-owner-ask.timer (10min)", 144, "$0", "138:owner_ask.py"),
 ("BR-10", "action_executor (unforeseen-work)", "decision-code", "python", "owner_reply dispatch + proposal_intake", "?", "$0",
  "138:action_executor.py (deployed 09-18)"),
 ("BR-11", "proposal_intake (U-WORK)", "decision-code", "python", "manual/loops", "?", "$0", "138:proposal_intake.py"),
 ("BR-12", "money_tools / money_executor", "decision-code", "python", "owner vote (money executor gate 13 rules)", "?", "$0",
  "138:money_executor.py + money_tools.py"),
 ("BR-13", "revenue_state (meter)", "decision-code", "python", "octopus-revenue-drive.timer (6h)", 4, "$0", "138:revenue_state.py"),
 ("BR-14", "deep_scan_tick (guard)", "decision-code", "python", "octopus-deep-scan.timer (Mon 04:00Z)", 0.14, "$0",
  "138:deep_scan_tick.py 535 lines (findings 573)"),
 ("BR-15", "cognition_factory", "decision-code", "python", "FROZEN (last write 09-15T08:33)", 0, "$0",
  "138:state/cognition/ 877 lines, last_write 09-15"),
 ("BR-16", "self-model producer", "decision-code", "python", "octopus timers", "?", "$0", "138:state/self-model alive 01:46"),
 ("BR-17", "fleet-compute think_pool", "decision-code", "python", "consumer check INCONCLUSIVE (grep mismatch)", "?", "$0",
  "138:state/fleet-compute/think_pool.py (evidence-based provider health)"),
 ("BR-18", "glass_runner (owner message intake)", "decision-code", "python", "octopus-glass.timer (1min)", 1440, "$0",
  "138:ofn/agents/glass_runner.py 374 lines; state/glass FROZEN 09-16"),
 ("BR-19", "imap_listener", "decision-code", "python", "octopus-imap.timer (15min)", 96, "$0", "138:ofn/agents/imap_listener.py alive"),
 ("BR-20", "reply_alert", "decision-code", "python", "octopus-reply-alert.timer", "?", "$0", "138:reply_alert.py alive 00:36"),
 ("BR-21", "b2b_discovery agent", "decision-code", "python", "ofn/agents (merge #259)", "?", "$0", "repo:ofn/agents/b2b_discovery.py"),
 ("BR-22", "coding-worker", "decision-code", "python", "octopus-coding-worker.timer", "?", "$0", "138:state/coding-worker alive 01:47"),
 ("BR-23", "fleet-scheduler", "decision-code", "python", "octopus-scheduler.timer", "?", "$0", "138:state/fleet-scheduler alive 01:50"),
 ("BR-24", "octopus-mesh control_router", "mesh", "python", "octopus-control-router.service (RUNNING)", "?", "$0",
  "138:/home/ari/octopus-mesh/bin/octopus_control_router.py"),
 ("BR-25", "octopus-mesh router", "mesh", "python", "octopus-router.service (RUNNING)", "?", "$0", "138:octopus_router.py"),
 ("BR-26", "octopus-mesh supervisor", "mesh", "python", "octopus-supervisor.service (RUNNING)", "?", "$0", "138:octopus_supervisor.py"),
 ("BR-27", "octopus-mesh verify_dispatcher", "mesh", "python", "octopus-verify-dispatcher.service (RUNNING)", "?", "$0",
  "138:octopus_verify_dispatcher.py"),
 ("BR-28", "octopus-mesh cycle_settler", "mesh", "python", "octopus-cycle-settler.service (RUNNING)", "?", "$0", "138:octopus_cycle_settler.py"),
 ("BR-29", "octomesh_* transport kit", "mesh", "python", "send/receive/consume/process/bridge/calibration/selftest/status",
  "?", "$0", "138:/home/ari/octopus-mesh/bin/octomesh_*.py (9 modules)"),
 ("BR-30", "budget ledger (memory brain)", "memory", "jsonl", "api_budget + monitor", "cont", "$0.85/mo", "138:budget-ledger 89 rows"),
 ("BR-31", "deep-scan findings register (memory)", "memory", "json", "deep_scan_tick + guard", "?", "$0", "138:findings-current 573 rows"),
 ("BR-32", "decision ledger + consumption (memory)", "memory", "jsonl", "owner_reply/ops_agent", "cont", "$0",
  "138:owner_dialogue/{owner_decision,decision_consumption}.jsonl"),
]

# ---------------------------------------------------------------- wiring edges
E = []  # id, domain, producer, consumer, trigger, state, proof
def e(i, dom, prod, cons, trig, state, proof):
    E.append({"edge_id": i, "domain": dom, "producer": prod, "consumer": cons, "trigger": trig,
              "state": state, "proof": proof})

e("W-001","business","painting_call_log (#248 table)","—","—","DANGLING","138:grep painting_call_log consumers=0")
e("W-002","business","v_account_last_call (view)","—","—","DANGLING","138:grep v_account_last_call consumers=0")
e("W-003","business","AUTO_DISCOVERY_TAG","—","—","DANGLING","138:grep consumers=0 (digest --include-unverified absent in runtime)")
e("W-004","business","revenue_drive quote packets","send-queue / owner-ask","6h timer","WIRED-LIVE","138:sent-log 39 rows; receipts SEND_HELD")
e("W-005","business","owner_ask cards","Telegram owner chat","10min timer","WIRED-LIVE","138:receipts owner-ask http_200 09-18")
e("W-006","business","owner taps / typed votes","glass spool → owner_reply","1min timers","WIRED-LIVE","138:receipts OWNER_DECISION_* 09-18 (fixed today)")
e("W-007","business","owner_reply approve","money_tools/action_executor","on vote","WIRED-LIVE","138:OWNER_DECISION_EXECUTED receipts")
e("W-008","business","money_tools send","Gmail SMTP","on approved batch","WIRED-LIVE","138:MONEY_BATCH_EMAIL_SENT receipts (16)")
e("W-009","business","imap replies","reply_alert → owner chat","15min timer","WIRED-LIVE","138:reply-alert-cursor advancing 00:36")
e("W-010","business","lead enrichment run","lead-emails.jsonl","manual/loop","WIRED-LIVE","138:lead-emails 68 rows, mtime 09-16")
e("W-011","business","lead-emails.jsonl","outreach packets","revenue loop","WIRED-LIVE","138:68 emails → packets staged")
e("W-012","business","outbound sends","outbound-effects.sqlite3","on send","WIRED-DARK","138:file exists 0 bytes")
e("W-013","business","quote packets (137)","packet-state counters","—","WIRED-DARK","138:funnel_reconcile: 0 packets marked sent")
e("W-014","business","campaign dir","nothing","—","DANGLING","138:campaign/ empty since 09-13")
e("W-015","business","ziman Shopify","shopify-watch checks","timer","WIRED-LIVE","138:482 zero-order checks counted")
e("W-016","business","ziman store traffic","any acquisition loop","—","MISSING","no ads/seo/social file anywhere")
e("W-017","business","studio consent chain","publish path","owner signatures","ORPHAN","14/14 unsigned (F-023)")
e("W-018","business","painting call outcomes","CRM/stage display","—","DANGLING","v_account_last_call unread")
e("W-019","module","proposal_intake proposals","action_executor (green) / cards (red)","submit","WIRED-LIVE","138:UWORK receipts 09-18")
e("W-020","module","action_executor receipts","receipts.jsonl","on action","WIRED-LIVE","138:ACTION_EXECUTED receipts")
e("W-021","module","deep_scan findings","guard timer + vault dashboard","Mon 04:00Z","WIRED-LIVE","138:findings 573; DASHBOARD 09-15 (stale)")
e("W-022","module","deep_scan dashboard","—","—","WIRED-DARK","generated_at 09-15T08:03 vs today")
e("W-023","module","env enrichment package","digest/reports","merge #259","WIRED-LIVE","repo 88840181 merged; modules on main")
e("W-024","module","digest mobile regex fix","digest call list","merge #260","WIRED-LIVE","repo 3d74b757; 6 regex tests pass")
e("W-025","module","NATS JetStream OCTOPUS_EVENTS","fleet-vault-consumer (vault-pulse)","durable","WIRED-LIVE","heartbeat matrix auto-maintained 00:12")
e("W-026","module","NATS job bus","consumers per job type","—","WIRED-DARK","F-042 consumers=0 recorded; fleet_jobs 144/150 closed")
e("W-027","module","114 evaluator","no systemd unit (staged)","—","MISSING","F-003 staged-not-installed")
e("W-028","module","160 ingestion","no systemd unit (staged)","—","MISSING","F-003 staged-not-installed")
e("W-029","module","state/legs/lead-inbox/events.jsonl","glass error path writes there","error only","MISSING","138:directory absent; glass target")
e("W-030","module","self-model shadow journal","consumers unknown","timer","WIRED-DARK","state/self-model alive but no reader found")
e("W-031","module","fleet-memory facts/decisions","—","—","WIRED-DARK","state/fleet-memory FROZEN 09-16")
e("W-032","module","fleet-nodes registry","fleet probes","—","WIRED-DARK","state/fleet-nodes FROZEN 09-16")
e("W-033","module","of-draft-queue","senders","—","WIRED-DARK","state/of-draft-queue FROZEN 09-16")
e("W-034","module","durability lane","—","—","WIRED-DARK","state/durability FROZEN 09-15")
e("W-035","module","cognition_factory","—","—","WIRED-DARK","state/cognition FROZEN 09-15 (877 lines idle)")
e("W-036","module","glass state dir","owner intake","—","WIRED-DARK","state/glass FROZEN 09-16 (runner lives in ofn/)")
e("W-037","module","provider health (provider-health.jsonl)","think_pool classification","probe","WIRED-LIVE",".provider-probe timer; think_pool derives from evidence")
e("W-038","module","think_pool health results","api_budget route","—","ORPHAN","consumer grep inconclusive → needs re-probe")
e("W-039","module","local-insufficient route","local tier brain","budget decision","WIRED-LIVE","api_budget.py single consumer")
e("W-040","module","fleet-jobs bus","job consumers","timers","WIRED-LIVE","144/150 CLOSED at 00:0x")
e("W-041","blackbox","ops_agent decisions consume","task resume","5min","WIRED-LIVE","consume_decisions fixed 09-18 (spin→0)")
e("W-042","blackbox","octopus-mesh control_router","router/supervisor flow","daemon","WIRED-DARK","running service, consumer/output not traced")
e("W-043","blackbox","octopus-mesh verify_dispatcher","witness path","daemon","WIRED-DARK","running; no receipt trail found in state/receipts")
e("W-044","blackbox","octomesh_* kit (9 modules)","send/receive between nodes","?","WIRED-DARK","module set exists; producers/consumers untraced")
e("W-045","blackbox","octopus_bridge","ofn bridge watchdog","timer","WIRED-LIVE","octopus-bridge.service active + ofn-bridge-watchdog.timer")
e("W-046","blackbox","self-model producer","operator card / dashboards","daily","WIRED-DARK","three divergent bodies known (DC-03D)")
e("W-047","blackbox","coding-worker","patch pipeline","timer","WIRED-LIVE","state/coding-worker alive 01:47")
e("W-048","blackbox","fleet-scheduler feedback","scheduler inputs","timer","WIRED-LIVE","state/fleet-scheduler alive 01:50")
e("W-049","blackbox","glass owner intake","owner_reply spool","1min","WIRED-LIVE","tg-inbox rows appended (fixed 09-18)")
e("W-050","blackbox","receipts.jsonl","audit readers","on action","WIRED-LIVE","666 objects (repaired 09-18)")

# ---------------------------------------------------------------- boards
BOARDS = [
 ("138","Revenue Engine",".138", "1.0–1.5 (heartbeat pulses)", 8, "-", "45+ units, 25 timers", "busiest of the fleet; runs the revenue loop", "no spare for heavy batch"),
 ("182","Remote Witness & Audit Latch",".182","1.68 / 1.47 / 1.45", 8, "31G free", "27 services running", "very busy; witness duty + audit latch", "keep as witness, avoid adding"),
 ("180","Fleet Telemetry & Observatory",".180","1.26 / 0.53 / 0.28", 8, "43G free", "24 services", "moderate; telemetry + llama-lab history", "can take light batch"),
 ("114","Hardware Discovery",".114","0.39 / 0.19 / 0.22", 8, "54G free", "14 services", "light; evaluator staged-not-installed (F-003)", "install unit → +1 compute lane"),
 ("160","Shadow Verification & Watchdog",".160","0.34 / 0.24 / 0.15", 8, "53G free", "14 services", "light; ingestion staged-not-installed (F-003)", "install unit → +1 ingest lane"),
 ("193","Hypothesis & Market Research",".193","0.47 / 0.20 / 0.12", 8, "54G free", "15 services", "light; research role under-used", "best candidate for model/research work"),
 ("100","Coding Worker & Sandbox",".100","0.02 / 0.05 / 0.08", 8, "48G free", "16 services", "essentially IDLE (load 0.02)", "the fleet's spare capacity — use first"),
]

# ---------------------------------------------------------------- throughput plan
PLAN = [
 ("TP-01","write a reader for painting_call_log + v_account_last_call so the CRM stage updates","138","removes W-001/002/018 dangling edges; first CRM data visible", "low","A","no"),
 ("TP-02","install the staged systemd units on 114 (evaluator) and 160 (ingestion)","114,160","+2 always-on lanes; kills the reboot-orphan risk (F-003)","low","B(witness)","no"),
 ("TP-03","move heavy batch jobs (enrichment/digest/NPU probes) from 138 to 100","100,138","frees the revenue node; 100 sits at load 0.02","med","A","no"),
 ("TP-04","wire think_pool provider-health into the broker route (orphan BR-17/W-038)","138","stops routing to exhausted providers (the fugu 429 defect)","low","A","no"),
 ("TP-05","measure NPU usable capacity on 138+193 and publish a consumer","138,193","unknown→known; potential free local inference (F-056)","med","A","no"),
 ("TP-06","give the local tier (BR-06) a real consumer for the cheap classification tasks","138","cut paid calls for trivial work","low","A","no"),
 ("TP-07","revive cognition_factory (BR-15) or archive it — 877 idle lines","138","either +1 brain or remove dead weight (verified decision)","low","A","no"),
 ("TP-08","same decision for durability (09-15) and of-draft-queue (09-16)","138","state tier stops growing tombstones","low","A","no"),
 ("TP-09","trace the octopus-mesh services' I/O and register their receipts","138","6 running daemons currently WIRED-DARK","med","A","no"),
 ("TP-10","persist packet send_status on send (fixes 0-vs-39)","138","funnel becomes measurable end-to-end","low","A","no"),
 ("TP-11","give fleet-memory / fleet-nodes (frozen 09-16) a consumer or retire them","138","memory layer honesty","low","A","no"),
 ("TP-12","autofill + publish DASHBOARD on the 6h cycle (W-022 dark)","138","orientation data stops being 3 days stale","low","A","no"),
 ("TP-13","add JetStream consumers for the job bus types with none (F-042)","138","job durability stops being decorative","med","B","no"),
 ("TP-14","create state/legs/lead-inbox/ so glass error writes land (W-029)","138","error path becomes observable","trivial","A","no"),
 ("TP-15","route research/hypothesis jobs to 193 and coding sandbox runs to 100","193,100","uses the two most idle boards deliberately","low","A","no"),
 ("TP-16","run the restore drill (F-006) while spare capacity exists on 100","100","biggest hidden risk retired","med","B(witness)","no"),
 ("TP-17","second channel for Critical owner cards (Telegram single-point)","138","decisions survive a TG outage","low","A","yes"),
 ("TP-18","standing send-authorization policy card","138","removes the release-gate stall measured today","low","A","yes"),
 ("TP-19","witness/audit load review on 182 (27 services, load 1.68)","182","witness must not become the bottleneck","low","A","no"),
 ("TP-20","publish a weekly brain-cost table from the ledger (BR-30)","138","$/day per brain visible; waste ends","trivial","A","no"),
]

# ---------------------------------------------------------------- gaps
GAPS = []
def g(i, title, verdict, grade, proof, why):
    GAPS.append({"id": i, "title": title, "verdict": verdict, "grade": grade,
                 "proof": proof, "why": why})
g("BW-01","painting_call_log (canonical CRM table, merged #248) has zero readers","CONFIRMED","E3",
  "138:grep painting_call_log consumers=0","the CRM data the owner asked for is written but never displayed")
g("BW-02","v_account_last_call view unread → stage never updates on the card","CONFIRMED","E3",
  "138:grep consumers=0","Elahe's own note confirmed; now measured")
g("BW-03","AUTO_DISCOVERY_TAG has zero consumers in the runtime","CONFIRMED","E3",
  "138:grep consumers=0","unverified discovered leads cannot be filtered out of the call list")
g("BW-04","think_pool (evidence-based provider health) may have no consumer","UNVERIFIED","E2",
  "consumer grep returned nothing but the sakana probe listed it","provider routing may still trust a stale status")
g("BW-05","six octopus-mesh services run continuously with no receipt trail","CONFIRMED","E3",
  "138:systemctl running + no receipts in state/receipts","a second organism runs with dark I/O")
g("BW-06","cognition_factory frozen since 09-15 (877 lines)","CONFIRMED","E3","138:state/cognition last_write 09-15T08:33",
  "a brain that stopped being fed")
g("BW-07","durability + of-draft-queue + fleet-memory + fleet-nodes + glass state frozen 09-15/16","CONFIRMED","E3",
  "138:state/* last_write table","five state areas are tombstones")
g("BW-08","100 is effectively idle (load 0.02, 48G free, 8 cores) while 138 runs saturated","CONFIRMED","E3",
  "laptop probe 2026-09-18","the fleet's spare capacity is unused")
g("BW-09","182 witness runs 27 services at load 1.68","CONFIRMED","E3","laptop probe","witness headroom must be protected")
g("BW-10","outbound-effects.sqlite3 still 0 bytes (no outcome wiring)","CONFIRMED","E3","138:file size 0",
  "learning loop for outreach still open (W-012)")
g("BW-11","packet store still reports 0 sent vs 39 message rows","CONFIRMED","E3","funnel_reconcile output",
  "send path does not persist packet state")
g("BW-12","staged units on 114/160 still uninstalled (F-003)","CONFIRMED","E2","findings F-003 + 14 services each board",
  "two lanes of compute sit unused")
g("BW-13","no reader for fleet-memory facts (frozen)","CONFIRMED","E3","state/fleet-memory last_write 09-16","memory layer dark")
g("BW-14","owner decisions still single-channel (Telegram only)","CONFIRMED","E2","today's debug: no fallback path",
  "a TG outage freezes every gated action")
g("BW-15","no standing send-authorization; every batch needs a vote","CONFIRMED","E3","today's funnel stall",
  "the measured #1 growth blocker (WHY-SLOW R1)")

# ---------------------------------------------------------------- emit
(OUT / "BRAIN-CENSUS.json").write_text(json.dumps(
    {"schema": "octopus.brain-census.v1", "generated_at": NOW, "count": len(BRAINS),
     "external": sum(1 for b in BRAINS if b[2] == "external"),
     "local": sum(1 for b in BRAINS if b[2] == "local"),
     "decision_code": sum(1 for b in BRAINS if b[2] == "decision-code"),
     "mesh": sum(1 for b in BRAINS if b[2] == "mesh"),
     "memory": sum(1 for b in BRAINS if b[2] == "memory"),
     "brains": [{"id": b[0], "name": b[1], "kind": b[2], "provider_model": b[3], "callers": b[4],
                 "calls_per_day": b[5], "cost": b[6], "evidence": b[7]} for b in BRAINS]},
    ensure_ascii=False, indent=1), encoding="utf-8")

with (OUT / "WIRING-MATRIX.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["edge_id", "domain", "producer", "consumer", "trigger", "state", "proof"])
    w.writeheader()
    for row in E:
        w.writerow(row)

(OUT / "BOARD-CAPACITY.md").write_text(
    "# BOARD-CAPACITY — ۷ برد (اندازه‌گیری 2026-09-18)\n\n"
    "| برد | نقش | load (1/5/15m) | هسته | دیسک آزاد | سرویس running | خوانش | توصیه |\n|---|---|---|---|---|---|---|---|\n"
    + chr(10).join("| " + " | ".join(str(x) for x in [b[0], b[1], b[3], b[4], b[5], b[6], b[7], b[8]]) + " |" for b in BOARDS)
    + "\n\n**جمع‌بندی:** ظرفیت خالی واقعی در ۱۰۰ (بار ۰.۰۲) و سپس ۱۱۴/۱۶۰/۱۹۳ است؛ ۱۳۸ و ۱۸۲ سرِ ظرفیت‌اند و ۱۸۰ متوسط. "
      "پس مشکل «کمبود برد» نیست — **توزیع کار** است: ۱۳۸ هم revenue loop دارد هم batch.\n"
      "> یادداشت: ۱۳۸ در این حلقه با کلید پیش‌فرض probe نشد (alias جدا)؛ بار آن از پالس‌های heartbeat گرفته شده.\n",
    encoding="utf-8")

(OUT / "THROUGHPUT-PLAN.md").write_text(
    "# THROUGHPUT-PLAN — ۲۰ آیتم برای بالا بردن بازده (رتبه‌بندی‌شده)\n\n"
    "| # | کار | برد | اثر تخمینی | هزینه | Class | رأی مالک؟ |\n|---|---|---|---|---|---|---|\n"
    + "\n".join("| %s | %s | %s | %s | %s | %s | %s |" % p for p in PLAN)
    + "\n\n**ترتیب پیشنهادی اجرا:** TP-14 → TP-10 → TP-01 → TP-04 → TP-02 → TP-03 → TP-15 (همه Class A سبک، بدون رأی) "
      "سپس TP-05/TP-09/TP-12 و در آخر دارندگان رأی (TP-17/TP-18).\n",
    encoding="utf-8")

(OUT / "GAP-REGISTER.json").write_text(json.dumps(
    {"schema": "octopus.brain-wiring-gaps.v1", "generated_at": NOW, "count": len(GAPS),
     "note": "یافته‌های تازهٔ اسکن مغز/سیم‌کشی — خارج از رجیستر ۵۷۳ ردیفی فعلی",
     "gaps": GAPS}, ensure_ascii=False, indent=1), encoding="utf-8")

print("brains:", len(BRAINS), "| edges:", len(E), "| boards:", len(BOARDS),
      "| plan:", len(PLAN), "| gaps:", len(GAPS))
from collections import Counter
print("edge states:", Counter(x["state"] for x in E).most_common())
