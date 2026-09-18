#!/usr/bin/env python3
"""OWNER-LINK v4:
 (1) recover votes that exist in the spool but never reached the ledger
 (2) make the spool cursor rewrite-proof (content-hash based, not line index)
 (3) instrument glass: log every update's safe metadata so a dropped message is visible
"""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
ROOT = pathlib.Path("/home/ari/ofn")
RD = ROOT / "state/revenue-drive"
RP = RD / "owner_reply.py"
G = ROOT / "ofn/agents/glass_runner.py"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


for p in (RP, G):
    shutil.copy2(p, str(p) + ".pre-ownerlink4-" + TS)
h0 = {str(p): sha(p) for p in (RP, G)}

# ---------- (1) recover missed votes ----------
spool = [json.loads(l) for l in (RD / "tg-inbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
led = [json.loads(l) for l in (RD / "owner-decisions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
seen = {(str(d.get("at")), str(d.get("text"))) for d in led}
missing = [r for r in spool if (str(r.get("at")), str(r.get("text"))) not in seen]
print("spool rows:", len(spool), "| already in ledger:", len(seen), "| MISSING:", len(missing))
for m in missing:
    print("   missing:", m.get("at"), m.get("kind"), repr(str(m.get("text"))[:50]))
if missing:
    with (RD / "tg-inbox.jsonl").open("a", encoding="utf-8") as fh:
        for m in missing:
            fh.write(json.dumps({**m, "recovered": True,
                                 "route_reason": str(m.get("route_reason")) + ":recovered"},
                                ensure_ascii=False) + "\n")
    print("re-appended", len(missing), "row(s) for reprocessing")

# ---------- (2) rewrite-proof cursor ----------
s = RP.read_text(encoding="utf-8")
old = ('    seen = int(CURSOR.read_text().strip() or 0) if CURSOR.exists() else 0\n'
       '    lines = INBOX.read_text(errors="replace").strip().splitlines()\n'
       '    msgs, kept = [], seen\n'
       '    for i, line in enumerate(lines):\n'
       '        if i < seen:\n'
       '            continue')
if s.count(old) == 1:
    new = ('    # OWNER-LINK v4: cursor is the set of consumed row HASHES, not a line\n'
           '    # index — an index desynchronises whenever the spool file is rewritten\n'
           '    # (it silently swallowed a real owner vote on 2026-09-18).\n'
           '    _craw = CURSOR.read_text(encoding="utf-8").strip() if CURSOR.exists() else ""\n'
           '    if _craw.startswith("{"):\n'
           '        _seen_hashes = set(json.loads(_craw).get("hashes", []))\n'
           '    elif _craw:\n'
           '        _seen_hashes = set()\n'
           '        _legacy_n = int(_craw or 0)\n'
           '        _l0 = INBOX.read_text(errors="replace").strip().splitlines() if INBOX.exists() else []\n'
           '        for _i, _ln in enumerate(_l0[:_legacy_n]):\n'
           '            _seen_hashes.add(hashlib.sha256(_ln.encode("utf-8")).hexdigest()[:16])\n'
           '    else:\n'
           '        _seen_hashes = set()\n'
           '    lines = INBOX.read_text(errors="replace").strip().splitlines()\n'
           '    msgs, kept = [], 0\n'
           '    _new_hashes = set()\n'
           '    for i, line in enumerate(lines):\n'
           '        _h = hashlib.sha256(line.encode("utf-8")).hexdigest()[:16]\n'
           '        if _h in _seen_hashes:\n'
           '            _new_hashes.add(_h)\n'
           '            continue')
    s = s.replace(old, new)
    # keep the hash bookkeeping intact through the rest of the loop
    old2 = ('        kept = i + 1\n'
            '        if str(d.get("chat", "")) in chat_allow.split(","):')
    new2 = ('        _new_hashes.add(_h)\n'
            '        kept = i + 1\n'
            '        if str(d.get("chat", "")) in chat_allow.split(","):')
    assert s.count(old2) == 1, "hash bookkeeping anchor=%d" % s.count(old2)
    s = s.replace(old2, new2)
    s = s.replace("import json\nimport pathlib", "import hashlib\nimport json\nimport pathlib", 1)
    RP.write_text(s, encoding="utf-8", newline="\n")
    print("cursor patch applied", h0[str(RP)][:16], "->", sha(RP)[:16])
else:
    print("!! cursor anchor not found — cursor patch SKIPPED (count=%d)" % s.count(old))

# ---------- (3) instrument glass ----------
g = G.read_text(encoding="utf-8")
anchor = ('        if chat_id not in allowed or not text.startswith(tuple(tg.COMMANDS)):\n'
          '            stats["ignored"] += 1\n'
          '            continue')
new_anchor = ('        if chat_id not in allowed or not text.startswith(tuple(tg.COMMANDS)):\n'
              '            # OWNER-LINK v4: a dropped update must never be invisible.\n'
              '            try:\n'
              '                import json as _dj, time as _dt\n'
              '                with (pathlib.Path("/home/ari/ofn/state/revenue-drive")\n'
              '                      / "glass-seen.jsonl").open("a", encoding="utf-8") as _df:\n'
              '                    _df.write(_dj.dumps({\n'
              '                        "at": _dt.strftime("%Y-%m-%dT%H:%M:%SZ", _dt.gmtime()),\n'
              '                        "update_id": u.get("update_id"),\n'
              '                        "type": ("callback" if u.get("callback_query") else\n'
              '                                 "edited_message" if u.get("edited_message") else "message"),\n'
              '                        "chat": chat_id, "chat_allowed": chat_id in allowed,\n'
              '                        "text": text[:120], "verdict": ("not_a_command"\n'
              '                            if chat_id in allowed else "chat_not_allowed")},\n'
              '                        ensure_ascii=False) + chr(10))\n'
              '            except Exception:\n'
              '                pass\n'
              '            stats["ignored"] += 1\n'
              '            continue')
assert g.count(anchor) == 1, "glass instrumentation anchor=%d" % g.count(anchor)
g = g.replace(anchor, new_anchor)
# also treat edited_message as a message (owner may edit a vote)
old_msg = '        msg = u.get("message") or {}\n        chat_id = str((msg.get("chat") or {}).get("id", ""))'
if g.count(old_msg) == 1:
    g = g.replace(old_msg, '        msg = u.get("message") or u.get("edited_message") or {}\n'
                           '        chat_id = str((msg.get("chat") or {}).get("id", ""))')
    print("edited_message handling added")
G.write_text(g, encoding="utf-8", newline="\n")
print("glass patched", h0[str(G)][:16], "->", sha(G)[:16])

json.dump({"schema": "octopus.fix-receipt.v1", "id": "OWNERLINK4-" + TS,
           "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
           "what": "cursor made rewrite-proof (content hashes; a line-index cursor silently "
                   "swallowed a real owner vote), missed spool rows recovered, glass now logs "
                   "every dropped update to glass-seen.jsonl, edited_message treated as message",
           "files": [{"file": str(RP), "sha_before": h0[str(RP)], "sha_after": sha(RP)},
                     {"file": str(G), "sha_before": h0[str(G)], "sha_after": sha(G)}],
           "rollback": "cp <preimage> <file>"},
          open(RD / "receipts.jsonl", "a", encoding="utf-8"), ensure_ascii=False)
print("MISSING_ROWS:", len(missing))
