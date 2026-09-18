#!/usr/bin/env python3
"""OWNER-LINK v2 fixes:
G1 (glass): EVERY allowed owner message is mirrored to the MONEY spool (never drop);
             B3-routed messages carry mirrored_from=B3 so the money consumer can
             still see them but won't bind them to a money card by default.
R1 (owner_reply): a tap on a SUPERSEDED card forwards to its live replacement
             (replacement_did) instead of replying "already registered".
R2 (owner_reply): a bare approval with no card identity binds to the SOLE PENDING
             money card (deterministic n=1) ; if several, reply with the open list.
R3 (owner_reply): clearer, actionable messages in every refusal path.
"""
import hashlib
import json
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
G = "ofn/agents/glass_runner.py"
RP = "state/revenue-drive/owner_reply.py"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


for p in (G, RP):
    shutil.copy2(p, p + ".pre-ownerlink2-" + TS)
h0 = {p: sha(p) for p in (G, RP)}

# ---------------- G1: mirror every allowed owner message to MONEY ----------------
s = open(G, encoding="utf-8").read()
anchor = ('                _dec = _route_owner_message(text)\n'
          '                _sp = _LANES.get(_dec["route"])\n'
          '                if _sp is not None:\n')
new = ('                _dec = _route_owner_message(text)\n'
       '                # OWNER-LINK v2 (2026-09-18): ALWAYS mirror to the MONEY spool so\n'
       '                # no owner message can be lost by lane routing; B3-routed ones are\n'
       '                # flagged so the money consumer never binds them to a money card.\n'
       '                try:\n'
       '                    _mir = _j.dumps({"chat": str(chat_id), "text": text[:600],\n'
       '                                     "at": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),\n'
       '                                     "lane": "MONEY",\n'
       '                                     "route_reason": "mirror:" + str(_dec["reason"]),\n'
       '                                     "mirrored_from": _dec["route"],\n'
       '                                     "kind": "message"}, ensure_ascii=False)\n'
       '                    with _LANES["MONEY"].open("a", encoding="utf-8") as _mf:\n'
       '                        _mf.write(_mir + chr(10))\n'
       '                except Exception:\n'
       '                    pass\n'
       '                _sp = _LANES.get(_dec["route"])\n'
       '                if _sp is not None:\n')
assert s.count(anchor) == 1, "G1 anchor=%d" % s.count(anchor)
s = s.replace(anchor, new)
open(G, "w", encoding="utf-8", newline="\n").write(s)
print("G1 applied", h0[G][:16], "->", sha(G)[:16])

# ---------------- R1..R3: owner_reply ----------------
r = open(RP, encoding="utf-8").read()

# R1: forward taps on superseded cards to the live replacement
old_dup = ('            if card and str(card.get("state")) != "PENDING":\n'
           '                receipt("DUPLICATE_TAP_IGNORED", did=did, decision=kind,\n'
           '                        card_state=str(card.get("state")))\n'
           '                send_owner_text("ℹ️ این کارت قبلاً ثبت شده بود (کد %s، وضعیت %s) — "\n'
           '                                "اقدام دوباره انجام نشد." % (did, card.get("state")))\n'
           '                continue\n')
new_dup = ('            if card and str(card.get("state")) != "PENDING":\n'
           '                _rep = card.get("replacement_did")\n'
           '                _repc = (reg.get("cards", {}) or {}).get(str(_rep)) if _rep else None\n'
           '                if _repc and str(_repc.get("state")) == "PENDING":\n'
           '                    # OWNER-LINK v2: an old button must still DO something —\n'
           '                    # forward the tap to the live replacement card.\n'
           '                    receipt("TAP_FORWARDED_TO_REPLACEMENT", did=did,\n'
           '                            replacement=str(_rep), decision=kind)\n'
           '                    card = _repc\n'
           '                    did = str(_rep)\n'
           '                    send_owner_text("↪️ این کارت جایگزین شده بود؛ دکمه‌ات روی کارت "\n'
           '                                    "فعال (کد %s) اعمال شد." % str(_rep))\n'
           '                else:\n'
           '                    receipt("DUPLICATE_TAP_IGNORED", did=did, decision=kind,\n'
           '                            card_state=str(card.get("state")))\n'
           '                    _open = [d for d, c2 in (reg.get("cards") or {}).items()\n'
           '                             if str(c2.get("state")) == "PENDING"]\n'
           '                    send_owner_text("ℹ️ این کارت بسته است (وضعیت %s). کارت‌های باز: %s\\n"\n'
           '                                    "دکمهٔ همان کارت‌ها را بزن." %\n'
           '                                    (card.get("state"),\n'
           '                                     "، ".join(_open) if _open else "—"))\n'
           '                    continue\n')
assert r.count(old_dup) == 1, "R1 anchor=%d" % r.count(old_dup)
r = r.replace(old_dup, new_dup)

# R2: sole-pending binding for bare approvals (deterministic n=1)
old_noid = ('        if target is None:\n'
            '            receipt("OWNER_DECISION_NO_IDENTITY", decision=kind)\n'
            '            continue\n')
new_noid = ('        if target is None:\n'
            '            # OWNER-LINK v2: a bare «تأیید» with no card named binds to the\n'
            '            # SOLE pending money card (deterministic n=1, never positional\n'
            '            # guessing); mirrored B3 rows are excluded from this binding.\n'
            '            _pend = [(d, c2) for d, c2 in (reg.get("cards") or {}).items()\n'
            '                     if str(c2.get("state")) == "PENDING"\n'
            '                     and str(c2.get("id")) != "TEST-DEBUG-OPT"]\n'
            '            _mirrored = str(m.get("mirrored_from") or "")\n'
            '            if len(_pend) == 1 and not _mirrored:\n'
            '                _d1, _c1 = _pend[0]\n'
            '                target = {"id": _c1.get("id"), "packets": _c1.get("packets") or []}\n'
            '                cb = None\n'
            '                option_chosen = None\n'
            '                channel_from_button = None\n'
            '                receipt("OWNER_DECISION_BOUND_SOLE_PENDING", did=_d1,\n'
            '                        decision=kind, item=str(_c1.get("id")))\n'
            '            else:\n'
            '                receipt("OWNER_DECISION_NO_IDENTITY", decision=kind,\n'
            '                        open_cards=[d for d, _ in _pend][:6],\n'
            '                        mirrored_from=_mirrored or None)\n'
            '                send_owner_text("🤔 نفهمیدم کدام کارت. کارت‌های باز: %s\\n"\n'
            '                                "دکمهٔ همان کارت را بزن (یا بنویس: تأیید <کد>)." %\n'
            '                                ("، ".join(d for d, _ in _pend) if _pend else "—"))\n'
            '                continue\n')
assert r.count(old_noid) == 1, "R2 anchor=%d" % r.count(old_noid)
r = r.replace(old_noid, new_noid)

# also: mirrored rows that DO name a card are dispatched normally (already the case);
# keep a receipt marker so audits can see the mirror origin
old_led = ('                                 "option": option_chosen,\n')
new_led = ('                                 "option": option_chosen,\n'
           '                                 "mirrored_from": str(m.get("mirrored_from") or ""),\n')
assert r.count(old_led) == 1
r = r.replace(old_led, new_led)

open(RP, "w", encoding="utf-8", newline="\n").write(r)
print("R1..R3 applied", h0[RP][:16], "->", sha(RP)[:16])

json.dump({"schema": "octopus.fix-receipt.v1", "id": "OWNERLINK2-" + TS,
           "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
           "files": [{"file": G, "preimage": G + ".pre-ownerlink2-" + TS,
                      "sha_before": h0[G], "sha_after": sha(G),
                      "what": "every allowed owner message mirrored to MONEY spool (never drop); "
                              "B3-routed rows flagged mirrored_from"},
                     {"file": RP, "preimage": RP + ".pre-ownerlink2-" + TS,
                      "sha_before": h0[RP], "sha_after": sha(RP),
                      "what": "superseded-card taps forward to the live replacement; bare "
                              "approvals bind to the sole pending card; actionable refusals"}],
           "rollback": "cp <preimage> <file>"},
          open("state/receipts/OWNERLINK2-%s.json" % TS, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("receipt written")
