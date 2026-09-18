#!/usr/bin/env python3
"""OWNER-LINK v5: accept owner messages by SENDER identity, not only by chat.
If the owner types in a group/other chat that holds the bot, the chat id is not
in the allowlist and the message was dropped (observed 2026-09-18: 1 ignored
update in the same batch as a captured tap). Now: a message whose SENDER is an
allowed owner id is spooled too (chat = sender id so the money consumer accepts
it), and the real chat id is recorded."""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
G = pathlib.Path("/home/ari/ofn/ofn/agents/glass_runner.py")


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


shutil.copy2(G, str(G) + ".pre-ownerlink5-" + TS)
h0 = sha(G)
s = G.read_text(encoding="utf-8")

old = ('        msg = u.get("message") or u.get("edited_message") or {}\n'
       '        chat_id = str((msg.get("chat") or {}).get("id", ""))\n'
       '        text = (msg.get("text") or "").strip()')
new = ('        msg = u.get("message") or u.get("edited_message") or {}\n'
       '        chat_id = str((msg.get("chat") or {}).get("id", ""))\n'
       '        # OWNER-LINK v5: identity = the SENDER. The owner may type from a chat\n'
       '        # (e.g. a group) whose id is not allow-listed; dropping his words there\n'
       '        # read to him as "it does not understand me" (2026-09-18).\n'
       '        sender_id = str((msg.get("from") or {}).get("id", ""))\n'
       '        from_chat = chat_id\n'
       '        if chat_id not in allowed and sender_id in allowed and sender_id:\n'
       '            chat_id = sender_id\n'
       '        text = (msg.get("text") or "").strip()')
assert s.count(old) == 1, "v5 anchor=%d" % s.count(old)
s = s.replace(old, new)

# record which chat the message actually came from, in the spooled row
old_sp = ('                        _f.write(_j.dumps({"chat": str(chat_id), "text": text[:600],')
if s.count(old_sp) == 1:
    s = s.replace(old_sp,
                  '                        _f.write(_j.dumps({"chat": str(chat_id),'
                  ' "from_chat": from_chat, "text": text[:600],')
else:
    print("!! spool-row anchor variant; checking mirror anchor instead")
    old_m = '"chat": str(chat_id), "text": text[:600],\n'
    assert s.count(old_m) >= 1
    s = s.replace(old_m, '"chat": str(chat_id), "from_chat": from_chat, "text": text[:600],\n')

# the drop logger should also record the sender
old_log = '"chat": chat_id, "chat_allowed": chat_id in allowed,'
if s.count(old_log) == 1:
    s = s.replace(old_log, '"chat": chat_id, "sender": sender_id,\n'
                           '                        "sender_allowed": sender_id in allowed,\n'
                           '                        "chat_allowed": chat_id in allowed,')
G.write_text(s, encoding="utf-8", newline="\n")
print("v5 applied", h0[:16], "->", sha(G)[:16])
json.dump({"schema": "octopus.fix-receipt.v1", "id": "OWNERLINK5-" + TS,
           "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
           "file": str(G), "preimage": str(G) + ".pre-ownerlink5-" + TS,
           "sha_before": h0, "sha_after": sha(G),
           "what": "owner messages are accepted by SENDER id, not only chat id; real chat "
                   "recorded in the spool row; drop log records sender too",
           "rollback": "cp <preimage> <file>"},
          open("/home/ari/ofn/state/revenue-drive/receipts.jsonl", "a", encoding="utf-8"),
          ensure_ascii=False)
print("receipt written")
