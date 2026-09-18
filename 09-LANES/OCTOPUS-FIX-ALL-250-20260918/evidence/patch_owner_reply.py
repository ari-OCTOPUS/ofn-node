#!/usr/bin/env python3
"""WHY-SLOW-250 debug patch (2026-09-18): duplicate-tap guard + option buttons."""
import hashlib, json, shutil, time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
RP = "state/revenue-drive/owner_reply.py"
AP = "state/revenue-drive/owner_ask.py"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


for p in (RP, AP):
    shutil.copy2(p, p + ".pre-whyslow250-debug-" + TS)
h0 = {p: sha(p) for p in (RP, AP)}
s = open(RP, encoding="utf-8").read()
a = open(AP, encoding="utf-8").read()


def rep(txt, old, new, tag):
    assert txt.count(old) == 1, "%s count=%d" % (tag, txt.count(old))
    return txt.replace(old, new)


s = rep(s, 'CALLBACK_PAT = re.compile(r"^(go|no|later):([0-9a-f]{8})(?::([a-z]+))?$", re.I)',
        'CALLBACK_PAT = re.compile(r"^(go|no|later|opt):([0-9a-f]{8})(?::([a-z0-9]+))?$", re.I)', "o1")
s = rep(s, "        channel_from_button = None\n        used_registry = False",
        "        channel_from_button = None\n        option_chosen = None\n        used_registry = False", "o2")
s = rep(s, '            kind = {"go": "APPROVE", "no": "REJECT", "later": "DEFER"}[action]',
        '            kind = {"go": "APPROVE", "no": "REJECT", "later": "DEFER", "opt": "APPROVE"}.get(action)\n'
        '            if kind is None:\n'
        '                receipt("OWNER_CALLBACK_UNKNOWN_ACTION", action=action, did=did)\n'
        '                continue\n'
        '            if action == "opt":\n'
        '                option_chosen = channel_from_button\n'
        '                channel_from_button = None', "o3")
s = rep(s, '            card = reg.get("cards", {}).get(did)\n            if card:',
        '            card = reg.get("cards", {}).get(did)\n'
        '            if card and str(card.get("state")) != "PENDING":\n'
        '                receipt("DUPLICATE_TAP_IGNORED", did=did, decision=kind,\n'
        '                        card_state=str(card.get("state")))\n'
        '                send_owner_text("ℹ️ این کارت قبلاً ثبت شده بود (کد %s، وضعیت %s) — "\n'
        '                                "اقدام دوباره انجام نشد." % (did, card.get("state")))\n'
        '                continue\n'
        '            if card:', "o4")
s = rep(s, '                                 "text": raw[:200], "kind": m.get("kind")},',
        '                                 "text": raw[:200], "kind": m.get("kind"),\n'
        '                                 "option": option_chosen,\n'
        '                                 "decision_id": (cb.group(2).lower() if cb else None)},', "o5")
s = rep(s, '        iid = str(target.get("id"))\n        for it in items:',
        '        iid = str(target.get("id"))\n'
        '        if option_chosen and kind == "APPROVE":\n'
        '            try:\n'
        '                acted["option_chosen"] = str(option_chosen)\n'
        '            except Exception:\n'
        '                pass\n'
        '            note = "✅ «%s» ثبت شد — گزینهٔ %s انتخاب شد." % (iid, option_chosen)\n'
        '        for it in items:', "o6")
a = rep(a, "def keyboard_for(item_id, did, channel):",
        "def keyboard_for(item_id, did, channel, options=()):\n"
        "    rows = []\n"
        "    if len(options) > 1:\n"
        "        for i, _txt in enumerate(options, 1):\n"
        "            rows.append([{\"text\": \"%d️⃣ گزینهٔ %d\" % (i, i),\n"
        "                          \"callback_data\": \"opt:%s:%d\" % (did, i)}])", "k1")
a = rep(a, "    return [[{\"text\": go_label, \"callback_data\": go_data},\n"
           "             {\"text\": \"⛔ رد\", \"callback_data\": \"no:%s\" % did},\n"
           "             {\"text\": \"⏸ بعداً\", \"callback_data\": \"later:%s\" % did}]]",
        "    rows.append([{\"text\": go_label, \"callback_data\": go_data},\n"
        "                 {\"text\": \"⛔ رد\", \"callback_data\": \"no:%s\" % did},\n"
        "                 {\"text\": \"⏸ بعداً\", \"callback_data\": \"later:%s\" % did}])\n"
        "    return rows", "k2")
a = rep(a, "                               keyboard_for(iid, did, channel))",
        "                               keyboard_for(iid, did, channel,\n"
        "                                            it.get(\"owner_one_card\") or []))", "k3")

open(RP, "w", encoding="utf-8", newline="\n").write(s)
open(AP, "w", encoding="utf-8", newline="\n").write(a)
print("ALL PATCHES APPLIED")
for p in (RP, AP):
    print(p, h0[p][:16], "->", sha(p)[:16])

rec = {"schema": "octopus.fix-receipt.v1", "id": "WHYSLOW250-DEBUG-" + TS,
       "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
       "lane": "OCTOPUS-FIX-ALL-250-20260918/debug-owner-reply",
       "fixes": [
           {"file": RP, "preimage": RP + ".pre-whyslow250-debug-" + TS,
            "sha_before": h0[RP], "sha_after": sha(RP),
            "what": "DUPLICATE_TAP_IGNORED guard before dispatch (money sends are not idempotent) "
                    "+ opt:<did>:<n> callback parsing + option/decision_id recorded in decisions ledger "
                    "+ option confirmation message"},
           {"file": AP, "preimage": AP + ".pre-whyslow250-debug-" + TS,
            "sha_before": h0[AP], "sha_after": sha(AP),
            "what": "per-option inline buttons for multi-option cards (choice unambiguous in callback data)"}],
       "rollback": "cp <preimage> <file>"}
json.dump(rec, open("state/receipts/WHYSLOW250-DEBUG-%s.json" % TS, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("receipt state/receipts/WHYSLOW250-DEBUG-%s.json" % TS)
