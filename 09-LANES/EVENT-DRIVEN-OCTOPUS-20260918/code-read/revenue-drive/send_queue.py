#!/usr/bin/env python3
"""send_queue.py v3 (2026-09-15, SEASON-CORRECTION 1.3).

v2: terminal-fail handling + honest sent-log. v3 closes the last funnel break:
nothing ever moved new packets from quote-packets/ into send-queue/ (the 09-13
batch was staged by hand). Before the send logic runs, v3:
  (1) syncs emails found by enrich/websearch (lead-emails.jsonl) back into
      leads_master.json contact_channel fields (idempotent, receipted);
  (2) refreshes prepared QP packets whose lead gained an email after preparation;
  (3) stages email-bearing QP packets into send-queue/ (phone-only never staged).
Gates unchanged: authorization + not-revoked + kill-switch + daily cap.
"""
import json, pathlib, re, shutil, time, hashlib

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
AUTH = ROOT / "channel-authorization.json"
REVOKED = ROOT / "CHANNEL-REVOKED"
QUEUE = ROOT / "send-queue"
TERMINAL = QUEUE / "terminal"
SENTLOG = ROOT / "sent-log.jsonl"
RECEIPTS = ROOT / "receipts.jsonl"
LEADS = pathlib.Path("/home/ari/ofn/tools/leads_master.json")
PACKETS = ROOT / "quote-packets"
KILL = pathlib.Path("/home/ari/ofn/state/autonomy/STOP-AUTONOMY")
HALT = pathlib.Path("/etc/octopus-ops-halt")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

def rcpt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(schema="octopus.send-queue.v1", at=NOW, kind=kind, **kw),
                           sort_keys=True, ensure_ascii=False) + "\n")

if not AUTH.exists() or REVOKED.exists():
    rcpt("SEND_SKIPPED", why="no authorization or revoked"); print(json.dumps({"sent": 0, "why": "no-auth"})); raise SystemExit
if KILL.exists() or HALT.exists():
    rcpt("SEND_BLOCKED_KILL_SWITCH"); print(json.dumps({"sent": 0, "why": "kill"})); raise SystemExit

# ---- (1) email sync: lead-emails.jsonl -> leads_master.json -----------------
emails_by_name = {}
if (ROOT / "lead-emails.jsonl").exists():
    for line in (ROOT / "lead-emails.jsonl").read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
            emails_by_name.setdefault(r["business_name"], r["email"])
        except (ValueError, KeyError):
            pass
synced = []
if LEADS.exists() and emails_by_name:
    lm = json.loads(LEADS.read_text(errors="replace"))
    for a in lm.get("accounts", []):
        n = a.get("business_name")
        e = emails_by_name.get(n)
        if e and not EMAIL_RE.search(str(a.get("contact_channel", ""))):
            a["contact_channel"] = (str(a.get("contact_channel", "")).strip(" |") + " | " + e).strip(" |")
            synced.append(n)
    if synced:
        bak = LEADS.with_name("leads_master.json.pre-email-sync-20260915")
        if not bak.exists():
            bak.write_bytes(LEADS.read_bytes())
        LEADS.write_text(json.dumps(lm, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rcpt("LEAD_EMAIL_SYNC", synced=synced, count=len(synced),
             rollback="restore leads_master.json.pre-email-sync-20260915")

# ---- (2)+(3) packet refresh + staging ---------------------------------------
staged = []
if PACKETS.exists():
    for q in sorted(PACKETS.glob("QP-*.json")):
        try:
            pkt = json.loads(q.read_text(errors="replace"))
        except ValueError:
            continue
        lead = pkt.get("lead") or {}
        name = lead.get("business_name", "")
        if not name:
            continue
        e = emails_by_name.get(name) or EMAIL_RE.search(str(lead.get("contact_channel", "")) or "")
        if not e:
            continue  # phone-only / no contact: never staged
        if not EMAIL_RE.search(str(lead.get("contact_channel", ""))):
            lead["contact_channel"] = str(lead.get("contact_channel", "")).strip(" |") + " | " + (e if isinstance(e, str) else e.group(0))
            lead["contact_refreshed_at"] = NOW
            q.write_text(json.dumps(pkt, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        dst = QUEUE / q.name
        if not dst.exists():
            QUEUE.mkdir(exist_ok=True)
            shutil.copy(str(q), str(dst))
            staged.append(q.stem)
if staged:
    rcpt("PACKET_STAGED", packets=staged, count=len(staged), why="email-bearing packets staged for authorised send")

# ---- v2 logic: cap, census, terminal, send ----------------------------------
auth = json.loads(AUTH.read_text())
cap = int(auth.get("envelope", {}).get("daily_send_cap", 0))
today = time.strftime("%Y-%m-%d", time.gmtime())
sent_today = 0
if SENTLOG.exists():
    for line in SENTLOG.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("at", "").startswith(today) and r.get("outcome", "sent") == "sent":
            sent_today += 1
room = max(0, cap - sent_today)

already, fail_count, fail_reason = set(), {}, {}
try:
    for line in RECEIPTS.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        for pk in (r.get("sent") or []):
            already.add(pk)
        for f in (r.get("failed") or []):
            pk = f.get("packet") if isinstance(f, dict) else f
            if not pk:
                continue
            fail_count[pk] = fail_count.get(pk, 0) + 1
            if isinstance(f, dict) and f.get("reason"):
                fail_reason[pk] = f["reason"]
except OSError:
    pass

TERMINAL.mkdir(exist_ok=True)
terminal_now = []
for pk, n in fail_count.items():
    if pk in already:
        continue
    if n >= 3 or fail_reason.get(pk) == "NO_EMAIL_ADDRESS_OR_CREDS":
        src = QUEUE / (pk + ".json")
        if src.exists():
            shutil.move(str(src), str(TERMINAL / src.name))
        terminal_now.append(pk)

if SENTLOG.exists():
    for line in SENTLOG.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("kind", "quote") == "quote":
            already.add(r.get("packet"))
if terminal_now:
    rcpt("SEND_TERMINAL", packets=terminal_now,
         why="unsendable (>=3 fails or NO_EMAIL_ADDRESS_OR_CREDS); moved to send-queue/terminal/",
         rollback="move files back from send-queue/terminal/")

import sys
# --- I7_NO_AUTO_CUSTOMER_SEND_GATE (SEC-I7-REVENUE-DRIVE 2026-09-16) ---
# auto_stage may stage packets; MUST NOT auto customer email/TG/SMS.
_i7 = ROOT / "i7-runtime.json"
_i7_hold = False
_i7_mode = None
try:
    import os as _os
    if _os.environ.get("OFN_NO_AUTO_CUSTOMER_SEND", "").lower() in ("1", "true", "yes"):
        _i7_hold = True
    if _i7.exists():
        _i7doc = json.loads(_i7.read_text(encoding="utf-8"))
        _i7_mode = _i7doc.get("mode")
        if _i7doc.get("no_auto_customer_send") is True or _i7doc.get("customer_send") is False:
            _i7_hold = True
        if _i7_mode in ("auto_stage", "prepare_only", "owner_cards_live"):
            if _i7doc.get("no_auto_customer_send", True) is True:
                _i7_hold = True
except Exception as _e:  # noqa: BLE001
    _i7_hold = True  # fail closed on parse error
    rcpt("SEND_HELD_I7_PARSE_ERROR", error=str(_e)[:200])
if _i7_hold:
    rcpt("SEND_HELD_NO_AUTO_CUSTOMER_SEND",
         mode=_i7_mode or "unknown",
         staged=staged,
         terminal_blacklisted=terminal_now,
         synced=len(synced),
         why="SEC-I7 R3 no_auto_customer_send=true; staging allowed; public send RED")
    print(json.dumps({"sent": 0, "why": "no_auto_customer_send", "mode": _i7_mode,
                      "staged": len(staged), "synced": len(synced)}))
    raise SystemExit
# --- end I7 gate ---
sys.path.insert(0, str(ROOT))
import money_tools as MT
pkts = [p.stem for p in sorted(QUEUE.glob("QP-*.json"))
        if p.stem not in already and p.stem not in terminal_now][:room]
if not pkts:
    rcpt("SEND_QUEUE_EMPTY", staged=staged, terminal_blacklisted=terminal_now, synced=len(synced))
    print(json.dumps({"sent": 0, "why": "empty", "staged": len(staged), "synced": len(synced)})); raise SystemExit
if room == 0:
    rcpt("SEND_CAPPED", daily_cap=cap, sent_today=sent_today, staged=staged)
    print(json.dumps({"sent": 0, "why": "daily-cap", "staged": len(staged)})); raise SystemExit
res = MT.execute_money_batch(packets=pkts, email_authorized=True)
sent_ids = res.get("email_sent") or []
failed = res.get("failed") or []
for p in pkts:
    payload = (QUEUE / (p + ".json")).read_bytes() if (QUEUE / (p + ".json")).exists() else b""
    h = hashlib.sha256(payload).hexdigest()[:16] if payload else ""
    rec = {"at": NOW, "packet": p, "kind": "quote", "outcome": "sent" if p in sent_ids else "failed",
           "ab_variant": (res.get("ab_variants") or {}).get(p, ""),
           "payload_sha16": h, "authorization": "channel-authorization.json",
           "daily_cap": cap, "sent_today_before": sent_today}
    with SENTLOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
rcpt("SEND_CYCLE", attempted=len(pkts), sent=sent_ids, failed=failed,
     post_witness="state advanced by revenue_state.py")
print(json.dumps({"sent": len(sent_ids), "failed": len(failed), "staged": len(staged),
                  "synced": len(synced), "room_before": room}, ensure_ascii=False))
