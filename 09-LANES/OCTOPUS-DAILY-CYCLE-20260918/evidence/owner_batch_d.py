#!/usr/bin/env python3
"""Owner batch D: (a) bounce-triggered auto-pause + owner alert, (b) day-3/day-7
follow-up runner + daily timer. Pre-image + receipt for every write."""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
MT = RD / "money_tools.py"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def rcp(kind, **kw):
    with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"schema": "octopus.fix-receipt.v1", "at": NOW, "kind": kind, **kw},
                            ensure_ascii=False, sort_keys=True, default=str) + "\n")


# ---------- a. bounce auto-pause inside the send path ----------
pre_mt = str(MT) + ".pre-autopause-" + TS
shutil.copy2(MT, pre_mt)
s = MT.read_text(encoding="utf-8")
if "_autopause_if_bounced" not in s:
    helper = '''def _autopause_if_bounced(failed):
    """Owner 2026-09-18: on the first delivery failure, pause sending and tell the
    owner (losing the Gmail account would cost the whole channel)."""
    import json as _j, pathlib as _p, time as _t
    if not failed:
        return False
    base = _p.Path(__file__).resolve().parent
    (base / "SEND-PAUSED").write_text(
        _j.dumps({"at": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()), "reason": "delivery_failure",
                  "failed": failed[:3]}, ensure_ascii=False), encoding="utf-8")
    try:
        import sys as _s
        _s.path.insert(0, str(base))
        import owner_reply as _or
        _or.send_owner_text("\\u26d4 \\u0627\\u0631\\u0633\\u0627\\u0644 \\u0645\\u062a\\u0648\\u0642\\u0641 \\u0634\\u062f: "
                            "\\u06cc\\u06a9 \\u0634\\u06a9\\u0633\\u062a \\u062a\\u062d\\u0648\\u06cc\\u0644 \\u062f\\u06cc\\u062f\\u0647 \\u0634\\u062f "
                            "(\\u062c\\u0644\\u0648\\u06af\\u06cc\\u0631\\u06cc \\u0627\\u0632 \\u0628\\u0633\\u062a\\u0647\\u200c\\u0634\\u062f\\u0646 \\u062d\\u0633\\u0627\\u0628). "
                            "\\u0644\\u063a\\u0648: \\u067e\\u0627\\u06a9 \\u06a9\\u0631\\u062f\\u0646 SEND-PAUSED")
    except Exception:
        pass
    return True


'''
    s = s.replace("def execute_money_batch(packets, email_authorized):",
                  helper + "def execute_money_batch(packets, email_authorized):")
    old = "        _record_send_ledgers(sent, ab_variants)"
    new = ("        _record_send_ledgers(sent, ab_variants)\n"
           "        _autopause_if_bounced(failed)")
    if s.count(old) == 1:
        s = s.replace(old, new)
    # the standing authorization must respect the pause
    old2 = '    if (base / "AUTH-REVOKED").exists():'
    new2 = ('    if (base / "SEND-PAUSED").exists():\n'
            '        return False, "SEND_PAUSED"\n'
            '    if (base / "AUTH-REVOKED").exists():')
    if s.count(old2) == 1:
        s = s.replace(old2, new2)
        print("auto-pause wired:", sha(MT)[:12])
    else:
        print("!! pause anchor not found (probe)")
    MT.write_text(s, encoding="utf-8", newline="\n")
else:
    print("auto-pause already present")

# ---------- b. follow-up runner (day 3 / day 7), daily timer ----------
FU = RD / "followup_runner.py"
FU.write_text('''#!/usr/bin/env python3
"""Follow-up runner (owner 2026-09-18): for every lead that received a quote and has
not replied, send a short reminder on day 3 and day 7, then stop. Honours the standing
authorization, SEND-PAUSED and AUTH-REVOKED. One receipt per attempt."""
import json, pathlib, re, smtplib, time
from email.message import EmailMessage

RD = pathlib.Path(__file__).resolve().parent
SEC = pathlib.Path("/home/ari/.config/ofn/secrets.env")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def env(n):
    m = re.search(r"^%s=(.+)$" % n, SEC.read_text(), re.M) if SEC.exists() else None
    return m.group(1).strip().strip('"') if m else ""


def rcp(kind, **kw):
    with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"schema": "octopus.followup.v1", "at": NOW, "kind": kind, **kw},
                            ensure_ascii=False, sort_keys=True, default=str) + "\\n")


def main():
    if (RD / "SEND-PAUSED").exists() or (RD / "AUTH-REVOKED").exists():
        rcp("FOLLOWUP_SKIPPED", why="paused_or_revoked"); return
    auth = json.loads((RD / "standing-authorization.json").read_text(encoding="utf-8"))
    if NOW > auth["scope"]["expires_at"]:
        rcp("FOLLOWUP_SKIPPED", why="authorization_expired"); return
    sid = json.loads((RD / "sender-identity.json").read_text(encoding="utf-8"))
    sent = [json.loads(l) for l in (RD / "sent-log.jsonl").read_text().splitlines() if l.strip()]
    replied = {r.get("packet") for r in sent if str(r.get("kind", "")).startswith("reply")}
    seend = json.loads((RD / "followup-state.json").read_text()) if (RD / "followup-state.json").exists() else {}
    todo = []
    for r in sent:
        if r.get("kind") != "quote" or not r.get("outcome") == "sent":
            continue
        pid = r.get("packet"); at = str(r.get("at", ""))
        if pid in replied or not pid:
            continue
        try:
            days = (time.time() - time.mktime(time.strptime(at, "%Y-%m-%dT%H:%M:%SZ")) -
                    0) / 86400.0
        except Exception:
            continue
        stage = "d7" if days >= 7 else ("d3" if days >= 3 else None)
        if not stage or seend.get(pid) == stage or seend.get(pid) == "d7":
            continue
        pf = RD / "quote-packets" / (pid + ".json")
        if not pf.exists():
            continue
        d = json.loads(pf.read_text(encoding="utf-8"))
        em = re.search(r"[\\w.+-]+@[\\w-]+\\.[\\w.]+", str((d.get("lead") or {}).get("contact_channel") or ""))
        if not em:
            continue
        todo.append((pid, em.group(0), stage, d))
    addr, pw = env("GMAIL_ADDRESS"), env("GMAIL_APP_PASSWORD")
    n = 0
    for pid, to, stage, d in todo[:10]:
        if not (addr and pw):
            rcp("FOLLOWUP_FAILED", packet=pid, why="NO_CREDS"); continue
        subj = ("Re: Painting services quote - %s" % str((d.get("lead") or {}).get("business_name") or "")[:40]) \\
            if stage == "d3" else "Following up on the painting quote (quick question)"
        body = ("Hi,\\n\\nJust following up on the quote we sent - happy to answer anything or attend for a "
                "free site walk at a time that suits you.\\n\\n" if stage == "d3" else
                "Hi,\\n\\nLast quick note from us on the painting quote. If the timing is not right, tell me "
                "when suits and I will come back then.\\n\\n")
        body += "Kind regards,\\n%s\\n%s\\n%s\\n" % (sid["signature_name"], sid["from_email"],
                                                    sid.get("business_mobile") or sid.get("contact_phone") or "")
        msg = EmailMessage(); msg["From"] = "%s <%s>" % (sid["signature_name"], addr)
        msg["To"], msg["Subject"] = to, subj; msg.set_content(body)
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
                s.login(addr, pw); s.send_message(msg)
            seend[pid] = stage; n += 1
            with (RD / "sent-log.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"at": NOW, "kind": "followup_" + stage[-1], "packet": pid, "outcome": "sent",
                                     "to_domain": to.split("@")[-1]}, ensure_ascii=False, sort_keys=True) + "\\n")
            rcp("FOLLOWUP_SENT", packet=pid, stage=stage, to_domain=to.split("@")[-1])
        except Exception as exc:
            rcp("FOLLOWUP_FAILED", packet=pid, stage=stage, why=type(exc).__name__)
    (RD / "followup-state.json").write_text(json.dumps(seend, indent=1), encoding="utf-8")
    print(json.dumps({"at": NOW, "candidates": len(todo), "sent": n}))


if __name__ == "__main__":
    main()
''', encoding="utf-8")

unit = "/etc/systemd/system/octopus-followup.service"
timer = "/etc/systemd/system/octopus-followup.timer"
svc = ("[Unit]\nDescription=OCTOPUS follow-up runner (day 3 / day 7)\nAfter=network-online.target\n\n"
       "[Service]\nType=oneshot\nUser=ari\nWorkingDirectory=/home/ari/ofn\n"
       "ExecStart=/usr/bin/python3 /home/ari/ofn/state/revenue-drive/followup_runner.py\n")
tmr = ("[Unit]\nDescription=OCTOPUS follow-up timer (daily 01:20Z)\n\n[Timer]\n"
       "OnCalendar=*-*-* 01:20:00\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n")
try:
    pathlib.Path(unit).write_text(svc, encoding="utf-8")
    pathlib.Path(timer).write_text(tmr, encoding="utf-8")
    import subprocess
    subprocess.run(["sudo", "-n", "systemctl", "daemon-reload"], timeout=60)
    subprocess.run(["sudo", "-n", "systemctl", "enable", "--now", "octopus-followup.timer"], timeout=60)
    out = subprocess.run(["systemctl", "is-active", "octopus-followup.timer"],
                         capture_output=True, text=True).stdout.strip()
    print("followup timer:", out)
except Exception as exc:  # noqa: BLE001
    print("timer install issue:", type(exc).__name__, str(exc)[:80])

rcp("OWNER_BATCH_D", autopause="wired", followup_runner=str(FU), timer="octopus-followup.timer daily 01:20Z",
    preimages=[pre_mt], followup_requires=["standing-authorization valid", "no SEND-PAUSED", "no reply yet"])
print("DONE")
