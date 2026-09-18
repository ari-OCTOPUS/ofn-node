#!/usr/bin/env python3
"""money_executor.py — stop re-preparing leads that were already emailed; deterministic packet ids.

EVENT-DRIVEN-OCTOPUS 2026-09-18. Live finding: `todo` was filtered only by
quote-fingerprints.jsonl (1 entry), so every run re-picked the SAME top-ranked leads
and built packets with a NEW id each time (ids come from Python's per-process string
hash). Live result: 131 staged packets for 5 distinct recipients, all 5 already
emailed on 09-15/09-16 — the owner-approved "wave" would have spammed 5 businesses
~25 times each. The recipient guard in send_queue now blocks those sends; this patch
makes the PREPARATION honest too:

  * exclude any lead whose recipient email is already in the durable send ledger
    (lead-send-ledger.jsonl) or in sent-log history;
  * packet id from sha256(business_name) instead of hash(name) — idempotent across runs.
"""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/money_executor.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
orig = p.read_text(encoding="utf-8")

OLD_IDS = '''fresh = [a for a in accounts
         if a.get("business_name") and ("lead:" in str(a) or True)
         and not any(a.get("business_name", "") in (d or "") for d in [])]
todo = sorted([a for a in fresh
               if not any((a.get("id") or a.get("business_name")) == d for d in done)],
              key=rank)[:5]
'''
NEW_IDS = '''fresh = [a for a in accounts
         if a.get("business_name") and ("lead:" in str(a) or True)
         and not any(a.get("business_name", "") in (d or "") for d in [])]

# EVENT-DRIVEN-OCTOPUS 2026-09-18: never re-prepare for an already-emailed recipient.
# Without this, the top-ranked leads were picked on every run forever (see lane report).
import re as _re
import hashlib as _hl
_EMAIL = _re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
_contacted = set()
_LEDGER = ROOT / "lead-send-ledger.jsonl"
try:
    if _LEDGER.exists():
        for _l in _LEDGER.read_text(errors="replace").splitlines():
            try:
                _contacted.add(str(json.loads(_l)["email"]).lower())
            except (ValueError, KeyError):
                pass
    for _l in (ROOT / "sent-log.jsonl").read_text(errors="replace").splitlines():
        try:
            _r = json.loads(_l)
        except ValueError:
            continue
        if _r.get("outcome") == "sent" and _r.get("kind", "quote") == "quote" and _r.get("packet"):
            for _d in (ROOT / "send-queue", PACKETS):
                _f = _d / (_r["packet"] + ".json")
                if _f.exists():
                    _m = _EMAIL.search(str((json.loads(_f.read_text(errors="replace")).get("lead") or {}).get("contact_channel") or ""))
                    if _m:
                        _contacted.add(_m.group(0).lower())
                    break
except OSError:
    pass


def _already_contacted(a):
    m = _EMAIL.search(str(a.get("contact_channel") or ""))
    return bool(m) and m.group(0).lower() in _contacted


todo = sorted([a for a in fresh
               if not any((a.get("id") or a.get("business_name")) == d for d in done)
               and not _already_contacted(a)],
              key=rank)[:5]
if not todo:
    RECEIPTS_ROW = {"schema": "octopus.money-executor.v1", "at": NOW,
                    "kind": "EXECUTOR_NO_FRESH_LEAD",
                    "why": "every lead with a contact channel was already emailed; "
                           "nothing new is prepared (no duplicate packets)"}
    with RECEIPTS.open("a", encoding="utf-8") as _fh:
        _fh.write(json.dumps(RECEIPTS_ROW, sort_keys=True, ensure_ascii=False) + "\\n")
'''
OLD_PID = '    pid = "QP-%s-%s" % (time.strftime("%Y%m%d"), abs(hash(name)) % 10000)\n'
NEW_PID = '    pid = "QP-%s-%s" % (time.strftime("%Y%m%d"), _hl.sha256(name.encode()).hexdigest()[:6])\n'

assert orig.count(OLD_IDS) == 1, "todo anchor %d" % orig.count(OLD_IDS)
assert orig.count(OLD_PID) == 1, "pid anchor %d" % orig.count(OLD_PID)
new = orig.replace(OLD_IDS, NEW_IDS, 1).replace(OLD_PID, NEW_PID, 1)
bak = p.with_name(p.name + ".pre-freshleads-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(new, encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("PATCHED money_executor.py fresh-lead filter + deterministic pid (preimage %s)" % bak.name)
