#!/usr/bin/env python3
"""apply_emit_points.py — EVENT-DRIVEN-OCTOPUS 2026-09-18 (Phase 2a).

Adds best-effort domain-event emits to the existing money runners. No logic is
changed: every emit is appended after the runner's own durable write, wrapped so
a bus failure can never break the money code. Per file: preimage (.pre-eventbus-<ts>),
exactly-one anchor assertion, py_compile check, revert on any failure.
"""
import pathlib
import py_compile
import shutil
import sys
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
OFN = pathlib.Path("/home/ari/ofn")
EV_IMPORT = 'import sys as _es; _es.path.insert(0, "/home/ari/ofn/tools"); import octopus_events as _oe'

PATCHES = [
    # ---- reply_alert.py: inbound_reply -------------------------------------
    (OFN / "state/revenue-drive/reply_alert.py", [
        ("            log_inbox(row)\n",
         "            log_inbox(row)\n"
         "            try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: inbound_reply domain event\n"
         "                " + EV_IMPORT + "\n"
         "                _oe.emit(\"inbound_reply\", \"uid:%d\" % uid,\n"
         "                         {\"from_domain\": domain, \"subject\": subj[:120],\n"
         "                          \"packet_id\": packet, \"src\": \"reply_alert\"})\n"
         "            except Exception:\n"
         "                pass\n"),
    ]),
    # ---- imap_listener.py: communication.* -> domain events ----------------
    (OFN / "ofn/agents/imap_listener.py", [
        ('        "payload": payload})\n',
         '        "payload": payload})\n'
         '    try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: map classification to domain events\n'
         '        ' + EV_IMPORT + '\n'
         '        _map = {"communication.reply": "inbound_reply",\n'
         '                "communication.quote_requested": "quote_requested",\n'
         '                "communication.acceptance": "quote_accepted",\n'
         '                "communication.opted_out": "opted_out",\n'
         '                "communication.bounce": "bounce",\n'
         '                "communication.autoreply": "autoreply"}\n'
         '        _k = _map.get(event_type)\n'
         '        if _k:\n'
         '            _oe.emit(_k, str(corr or ""), {"detail": payload, "src": "imap_listener"})\n'
         '    except Exception:\n'
         '        pass\n'),
    ]),
    # ---- send_queue.py: draft_ready (staging) ------------------------------
    (OFN / "state/revenue-drive/send_queue.py", [
        ('    rcpt("PACKET_STAGED", packets=staged, count=len(staged), why="email-bearing packets staged for authorised send")\n',
         '    rcpt("PACKET_STAGED", packets=staged, count=len(staged), why="email-bearing packets staged for authorised send")\n'
         '    try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: draft_ready per staged packet\n'
         '        ' + EV_IMPORT + '\n'
         '        for _p in staged:\n'
         '            _oe.emit("draft_ready", _p, {"src": "send_queue.stage"})\n'
         '    except Exception:\n'
         '        pass\n'),
        ('        with SENTLOG.open("a", encoding="utf-8") as f:\n'
         '            f.write(json.dumps(rec, sort_keys=True) + "\\n")\n',
         '        with SENTLOG.open("a", encoding="utf-8") as f:\n'
         '            f.write(json.dumps(rec, sort_keys=True) + "\\n")\n'
         '        try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: packet_sent/packet_failed\n'
         '            ' + EV_IMPORT + '\n'
         '            _oe.emit("packet_sent" if p in sent_ids else "packet_failed", p,\n'
         '                     {"payload_sha16": h, "outcome": rec["outcome"], "src": "send_queue"})\n'
         '        except Exception:\n'
         '            pass\n'),
    ]),
    # ---- lead_enrich.py: lead_enriched -------------------------------------
    (OFN / "state/revenue-drive/lead_enrich.py", [
        ('        with FOUND.open("a", encoding="utf-8") as fh:\n'
         '            fh.write(json.dumps(found[-1], sort_keys=True, ensure_ascii=False) + "\\n")\n',
         '        with FOUND.open("a", encoding="utf-8") as fh:\n'
         '            fh.write(json.dumps(found[-1], sort_keys=True, ensure_ascii=False) + "\\n")\n'
         '        try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: lead_enriched (no raw email on the bus)\n'
         '            ' + EV_IMPORT + '\n'
         '            import hashlib as _hl\n'
         '            _oe.emit("lead_enriched", name,\n'
         '                     {"email_domain": pick.split("@")[-1],\n'
         '                      "email_sha12": _hl.sha256(pick.encode()).hexdigest()[:12],\n'
         '                      "src": site})\n'
         '        except Exception:\n'
         '            pass\n'),
    ]),
    # ---- go_b3_owner_bind.py: card_resolved --------------------------------
    (OFN / "ofn/agents/go_b3_owner_bind.py", [
        ('        f.flush()\n        os.fsync(f.fileno())\n    return body\n',
         '        f.flush()\n        os.fsync(f.fileno())\n'
         '    try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: card_resolved domain event\n'
         '        ' + EV_IMPORT + '\n'
         '        _oe.emit("card_resolved", str(bound or verdict),\n'
         '                 {"verdict": verdict, "src": "go_b3_owner_bind",\n'
         '                  "request_payload_sha256": bound})\n'
         '    except Exception:\n'
         '        pass\n'
         '    return body\n'),
    ]),
    # ---- discovery_runner.py: lead_found (diff of leads_master) ------------
    (OFN / "state/revenue-drive/discovery_runner.py", [
        ('def main():\n    if (RD / "SEND-PAUSED").exists():\n        rcp("DISCOVERY_SKIPPED", why="paused"); return\n',
         'def _names(path):\n'
         '    try:\n'
         '        import json as _j\n'
         '        return {a.get("business_name") for a in _j.loads(path.read_text(errors="replace")).get("accounts", [])\n'
         '                if a.get("business_name")}\n'
         '    except Exception:\n'
         '        return set()\n'
         '\n'
         '\n'
         'def main():\n    if (RD / "SEND-PAUSED").exists():\n        rcp("DISCOVERY_SKIPPED", why="paused"); return\n'
         '    _before = _names(ROOT / "tools/leads_master.json")\n'),
        ('    rc1, out1 = run("tools/harvest_b2b_accounts.py", ("--max-candidates", "60"))\n'
         '    rcp("DISCOVERY_HARVEST", rc=rc1, out=out1)\n',
         '    rc1, out1 = run("tools/harvest_b2b_accounts.py", ("--max-candidates", "60"))\n'
         '    rcp("DISCOVERY_HARVEST", rc=rc1, out=out1)\n'
         '    try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: lead_found per genuinely new lead\n'
         '        ' + EV_IMPORT + '\n'
         '        _new = sorted(_names(ROOT / "tools/leads_master.json") - _before)\n'
         '        for _n in _new:\n'
         '            _oe.emit("lead_found", _n, {"src": "discovery_runner"})\n'
         '        rcp("DISCOVERY_EMITTED", new_leads=len(_new))\n'
         '    except Exception as _e:\n'
         '        rcp("DISCOVERY_EMIT_ERROR", err=type(_e).__name__)\n'),
    ]),
    # ---- revenue_drive.py: revenue_review (idle-driven review loop) --------
    (OFN / "state/revenue-drive/revenue_drive.py", [
        ('print(json.dumps(review))\nprint("owner_review_items:", [i["id"] for i in items])\n',
         'print(json.dumps(review))\n'
         'print("owner_review_items:", [i["id"] for i in items])\n'
         'try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: review receipt as a domain event\n'
         '    ' + EV_IMPORT + '\n'
         '    _oe.emit("revenue_review", NOW, {"zero_order_streak": streak,\n'
         '                                     "items": [i["id"] for i in items],\n'
         '                                     "src": "revenue_drive"})\n'
         'except Exception:\n'
         '    pass\n'),
    ]),
]


def main() -> int:
    ok = True
    for path, pairs in PATCHES:
        if not path.exists():
            print("MISSING %s" % path)
            ok = False
            continue
        orig = path.read_text(encoding="utf-8")
        new = orig
        good = True
        for old, rep in pairs:
            n = new.count(old)
            if n != 1:
                print("ANCHOR-FAIL %s (count=%d): %r" % (path.name, n, old[:60]))
                good = False
                break
            new = new.replace(old, rep, 1)
        if not good:
            ok = False
            continue
        bak = path.with_name(path.name + ".pre-eventbus-" + TS)
        shutil.copy2(str(path), str(bak))
        path.write_text(new, encoding="utf-8", newline="\n")
        try:
            py_compile.compile(str(path), doraise=True)
            print("PATCHED %s (preimage %s)" % (path.name, bak.name))
        except py_compile.PyCompileError as exc:
            shutil.copy2(str(bak), str(path))
            print("SYNTAX-FAIL %s -> reverted: %s" % (path.name, exc))
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
