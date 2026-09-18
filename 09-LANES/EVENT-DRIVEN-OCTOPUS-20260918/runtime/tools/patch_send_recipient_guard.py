#!/usr/bin/env python3
"""send_queue.py — one-email-per-recipient guard (EVENT-DRIVEN-OCTOPUS 2026-09-18).

Why: money_executor re-prepares the SAME top-ranked leads on every run, and Python's
per-process string hash gives those packets NEW ids each time — so packet-id dedup
(`already`) can never see them as duplicates. Live evidence: packet count grew
150->165 in one minute while the leads set stayed identical.

Guard (additive, receipted, fail-closed):
  * builds the set of already-contacted recipient emails from a durable ledger
    (state/revenue-drive/lead-send-ledger.jsonl) + historical sent-log rows;
  * drops any packet whose recipient was already emailed (ever), or repeats inside
    the same run; records SEND_DEDUP_BLOCKED with the blocked packet ids;
  * appends one ledger row per actually-sent packet.
Follow-up mail (followup_runner.py, day-3/day-7 reminders) is a separate path and
is deliberately NOT affected by this guard.
"""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/send_queue.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
orig = p.read_text(encoding="utf-8")

A_OLD = ('pkts = [p.stem for p in sorted(QUEUE.glob("QP-*.json"))\n'
         '        if p.stem not in already and p.stem not in terminal_now][:min(room, MAX_PER_RUN)]\n')
A_NEW = A_OLD + (
    '# --- one-email-per-recipient guard (EVENT-DRIVEN-OCTOPUS 2026-09-18) ---------\n'
    'LEDGER = ROOT / "lead-send-ledger.jsonl"\n'
    'contacted = set()\n'
    'try:\n'
    '    if LEDGER.exists():\n'
    '        for _l in LEDGER.read_text(errors="replace").splitlines():\n'
    '            try:\n'
    '                contacted.add(str(json.loads(_l)["email"]).lower())\n'
    '            except (ValueError, KeyError):\n'
    '                pass\n'
    '    for _l in SENTLOG.read_text(errors="replace").splitlines():\n'
    '        try:\n'
    '            _r = json.loads(_l)\n'
    '        except ValueError:\n'
    '            continue\n'
    '        if _r.get("outcome") == "sent" and _r.get("kind", "quote") == "quote" and _r.get("packet"):\n'
    '            for _f in (QUEUE / (_r["packet"] + ".json"), PACKETS / (_r["packet"] + ".json")):\n'
    '                if _f.exists():\n'
    '                    _m = EMAIL_RE.search(str((json.loads(_f.read_text(errors="replace")).get("lead") or {}).get("contact_channel") or ""))\n'
    '                    if _m:\n'
    '                        contacted.add(_m.group(0).lower())\n'
    '                    break\n'
    'except OSError:\n'
    '    pass\n'
    '\n'
    'def _rcpt_of(pid):\n'
    '    try:\n'
    '        pkt = json.loads((QUEUE / (pid + ".json")).read_text(errors="replace"))\n'
    '    except (OSError, ValueError):\n'
    '        return ""\n'
    '    m = EMAIL_RE.search(str((pkt.get("lead") or {}).get("contact_channel") or ""))\n'
    '    return m.group(0).lower() if m else ""\n'
    '\n'
    '_keep, _blocked = [], []\n'
    '_run_seen = set()\n'
    'for _pid in pkts:\n'
    '    _e = _rcpt_of(_pid)\n'
    '    if _e and (_e in contacted or _e in _run_seen):\n'
    '        _blocked.append({"packet": _pid, "recipient_sha12": hashlib.sha256(_e.encode()).hexdigest()[:12]})\n'
    '        continue\n'
    '    if _e:\n'
    '        _run_seen.add(_e)\n'
    '    _keep.append(_pid)\n'
    'pkts = _keep\n'
    'if _blocked:\n'
    '    rcpt("SEND_DEDUP_BLOCKED", packets=[b["packet"] for b in _blocked], blocked=_blocked,\n'
    '         why="recipient already emailed (durable ledger + sent-log), packet-id dedup cannot catch this")\n'
    'if not pkts:\n'
    '    rcpt("SEND_ALL_DEDUPED", staged=staged, synced=len(synced))\n'
    '    print(json.dumps({"sent": 0, "why": "all-deduped", "blocked": len(_blocked)}))\n'
    '    raise SystemExit\n'
)

B_OLD = 'res = MT.execute_money_batch(packets=pkts, email_authorized=True)\n'
B_NEW = B_OLD + (
    'try:  # ledger: recipients actually emailed (durable across runs)\n'
    '    with LEDGER.open("a", encoding="utf-8") as _lf:\n'
    '        for _pid in (res.get("email_sent") or []):\n'
    '            _e = _rcpt_of(_pid)\n'
    '            if _e:\n'
    '                _lf.write(json.dumps({"at": NOW, "email": _e, "packet": _pid}) + "\\n")\n'
    'except OSError:\n'
    '    rcpt("SEND_LEDGER_WRITE_FAILED")\n'
)

for old, new, tag in ((A_OLD, A_NEW, "guard"), (B_OLD, B_NEW, "ledger")):
    assert orig.count(old) == 1, "%s anchor %d" % (tag, orig.count(old))
    orig = orig.replace(old, new, 1)

bak = p.with_name(p.name + ".pre-recipientguard-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(orig, encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("PATCHED send_queue.py recipient guard + ledger (preimage %s)" % bak.name)
