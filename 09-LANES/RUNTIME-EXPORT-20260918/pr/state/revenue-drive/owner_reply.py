#!/usr/bin/env python3
"""owner_reply.py — the octopus READS the owner's Telegram answers and acts.

Owner order 2026-09-13: «کامل بساز جوابمو بخونه و عملکرد درست رو تشخیص بده
خودش برای خودش ابزار بسازی و انجام بده».

Loop (every cycle): poll the glass spool (owner bot updates; offset persisted,
owner chat only) -> match each reply to a PENDING card -> recognise the decision
-> dispatch to money_tools -> record receipts -> resolve the card -> confirm back
to the owner in the same Telegram chat. The token stays in-process; nothing is
ever printed.

Owner order 2026-09-18: «ارسالم یک‌کاری کن اختاپوس خودکار هر وقت نیاز دید تایید
بگیره و بفرسته در تلگرام» — so an inline-button tap now counts as the per-item
approval. `go:<did>:email` (button label «تأیید و ارسال ایمیل») carries BOTH the
card identity (8-hex decision id from owner-ask-registry.json) and the channel,
which is exactly what the retired-email ruling demands before a send.

Decision recognition (deterministic keyword intents, Persian + English):
  APPROVE  : بفرست، ارسال، تایید، تأیید، آره، بله، yes, approve, go, ok
  REJECT   : نه، نکن، نمی‌خوام، no, reject, stop
  RATE_CARD: any message containing 'rate' or 'تعرفه' or digit+price/rate tokens
  CHANNEL  : any other short text = the named market/channel for TRAFFIC-DECISION
"""
import hashlib
import json
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
REVIEW = ROOT / "owner-review.json"
SENT = ROOT / "owner-ask-sent.json"
REGISTRY = ROOT / "owner-ask-registry.json"
RECEIPTS = ROOT / "receipts.jsonl"
OFFSET = ROOT / "tg-offset.txt"
DECISIONS = ROOT / "owner-decisions.jsonl"
SECRETS = pathlib.Path("/home/ari/.config/ofn/secrets.env")

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
APPROVE_PAT = re.compile(r"(بفرست|ارسال|تایید|تأیید|آره|بله|yes|approve|\bgo\b|\bok\b)", re.I)
REJECT_PAT = re.compile(r"(نکن|نه|نمی.?خوام|no|reject|stop)", re.I)
RATE_PAT = re.compile(r"(rate.?card|تعرفه|(\d+(\.\d+)?)\s*(\$|aud|دلار|/(h|hr|ساعت|m2|متر)))", re.I)
CALLBACK_PAT = re.compile(r"^(go|no|later|opt):([0-9a-f]{8})(?::([a-z0-9]+))?$", re.I)
CHANNEL_WORD_PAT = re.compile(r"(ایمیل|email)", re.I)


def env_val(name):
    for line in SECRETS.read_text().splitlines():
        m = re.match(r"%s=(.+)" % name, line.strip())
        if m:
            return m.group(1).strip().strip('"')
    return ""


def send_owner_text(text):
    """Confirm back in the owner chat (sanctioned channel, receipt-only path)."""
    token = env_val("OFN_BOT_TOKEN_OWNER")
    chat = (env_val("OFN_OWNER_USER_IDS") or "").split(",")[0].strip()
    if not token or not chat:
        return False
    body = json.dumps({"chat_id": chat, "text": text[:3800],
                       "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendMessage" % token,
        data=body, headers={"Content-Type": "application/json"}, method="POST")
    for _ in (1, 2, 3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status == 200
        except Exception:  # noqa: BLE001 — transient network must not lose the ack
            time.sleep(4)
    return False


INBOX = ROOT / "tg-inbox.jsonl"
CURSOR = ROOT / "tg-inbox-cursor.txt"


def _cursor_load():
    """Consumed-row fingerprints from the previous run.

    OWNER-LINK v4 stored a LINE INDEX here, which desynchronises whenever the
    spool is rewritten and silently swallowed a real owner vote on 2026-09-18.
    The v4 comment claimed a hash set but the writer still emitted an integer,
    so every run fell back to the index path and the fix never took effect.
    This loader accepts both forms so an existing cursor upgrades in place.
    """
    if not CURSOR.exists():
        return set()
    raw = CURSOR.read_text(encoding="utf-8").strip()
    if not raw:
        return set()
    if raw.startswith("{"):
        try:
            return set(json.loads(raw).get("hashes", []))
        except json.JSONDecodeError:
            return set()
    try:  # legacy integer line index -> hashes of those lines
        n = int(raw)
    except ValueError:
        return set()
    if not INBOX.exists() or n <= 0:
        return set()
    out = set()
    for line in INBOX.read_text(errors="replace").strip().splitlines()[:n]:
        out.add(hashlib.sha256(line.encode("utf-8")).hexdigest()[:16])
    return out


def _cursor_save(hashes, keep: int = 5000):
    CURSOR.write_text(
        json.dumps({"hashes": sorted(hashes)[-keep:], "v": 4}), encoding="utf-8"
    )


def tg_get(token, chat_allow):
    """Read NEW owner messages from the glass_runner spool.

    Two separate channels write into this one file: Telegram owner updates and
    customer email replies (kind=REPLY_DETECTED, no chat field). Only a row whose
    chat is an explicit, non-empty entry of the owner allowlist may become an
    owner decision — a chat-less row must never match, including when the
    allowlist itself carries an empty entry (e.g. "123," in secrets.env).
    """
    if not INBOX.exists():
        return "OK", []
    # Filter empties: str.split on a trailing comma yields "" and an empty entry
    # would match every chat-less (email) row.
    allow = {a.strip() for a in str(chat_allow or "").split(",") if a.strip()}
    seen = _cursor_load()

    lines = INBOX.read_text(errors="replace").strip().splitlines()
    msgs, run_hashes = [], set()
    for line in lines:
        h = hashlib.sha256(line.encode("utf-8")).hexdigest()[:16]
        if h in seen or h in run_hashes:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        chat = str(d.get("chat") or "").strip()
        run_hashes.add(h)
        if not chat:                      # email/other channel: never an owner vote
            continue
        if chat not in allow:             # not the owner: ignore
            continue
        msgs.append({"chat": chat, "text": str(d.get("text", ""))[:600],
                     "at": str(d.get("at", "")),
                     "kind": str(d.get("kind", "message")),
                     "mirrored_from": str(d.get("mirrored_from") or "")})
    _cursor_save(seen | run_hashes)
    return "OK", msgs


def classify(text):
    if RATE_PAT.search(text):
        return "RATE_CARD", text
    if REJECT_PAT.search(text):
        return "REJECT", text
    if APPROVE_PAT.search(text):
        return "APPROVE", text
    return "CHANNEL", text


def review_items():
    if REVIEW.exists():
        return json.loads(REVIEW.read_text(encoding="utf-8")).get("items", [])
    return []


def save_review(items):
    REVIEW.write_text(json.dumps({"at": NOW, "items": items}, indent=1,
                                 sort_keys=True) + "\n", encoding="utf-8")


def load_registry():
    if REGISTRY.exists():
        try:
            return json.loads(REGISTRY.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"cards": {}}


def save_registry(reg):
    REGISTRY.write_text(json.dumps(reg, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")


def receipt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(schema="octopus.owner-reply.v1", at=NOW,
                                 kind=kind, **kw), sort_keys=True) + "\n")


def _dispatch_card(it, kind, raw, channel_from_button=None):
    """Run the typed tool for one identified card. Returns (acted, note)."""
    import money_tools
    iid = str(it.get("id"))
    if kind == "REJECT":
        return {"action": "rejected-by-owner"}, "رد شد — هیچ اقدامی انجام نشد."
    if kind == "APPROVE" and it.get("action"):
        # U-WORK v1: unforeseen work. The card carries an action spec; the
        # generic executor runs it (allowlist + preimage + receipt + rollback)
        # and refuses anything outside the allowlist or beyond the red boundary.
        import action_executor
        _res = action_executor.execute(it.get("action") or {}, via="owner_card",
                                       card_id=iid,
                                       risk=str(it.get("risk") or "internal_green"))
        return _res, (_res.get("note") or "اجرا شد.")
    if kind == "RATE_CARD":
        return money_tools.record_rate_card(raw), "نرخ ثبت شد."
    if kind == "APPROVE" and iid.startswith("MONEY-BATCH"):
        email_ok = (channel_from_button == "email") or bool(CHANNEL_WORD_PAT.search(raw))
        acted = money_tools.execute_money_batch(packets=it.get("packets") or [],
                                               email_authorized=email_ok)
        n_sent = len(acted.get("email_sent") or [])
        if n_sent:
            note = "✅ %d بسته ارسال شد (رسید ثبت شد)." % n_sent
        else:
            note = ("⚠️ ارسال انجام نشد — دلیل: %s"
                    % str(acted.get("blocked_on") or acted.get("failed") or "?")[:200])
        return acted, note
    if kind == "APPROVE":
        return {"action": "approved-no-typed-tool", "item": iid}, "تأیید ثبت شد."
    if kind == "CHANNEL":
        return {"action": "noted", "item": iid, "text": raw[:80]}, "یادداشت شد."
    if kind == "DEFER":
        return {"action": "deferred"}, "برای بعد نگه داشته شد."
    return None, ""


def main():
    token = env_val("OFN_BOT_TOKEN_OWNER")
    chat_allow = env_val("OFN_OWNER_USER_IDS")
    if not token or not chat_allow:
        print(json.dumps({"at": NOW, "error": "NO_TOKEN_OR_CHAT"}))
        return
    status, msgs = tg_get(token, chat_allow)
    if not msgs:
        print(json.dumps({"at": NOW, "poll": status, "new_owner_messages": len(msgs)}))
        return
    items = review_items()
    reg = load_registry()
    reg_dirty = False
    for m in msgs:
        raw = m["text"]
        cb = CALLBACK_PAT.match(raw.strip())
        channel_from_button = None
        option_chosen = None
        used_registry = False
        target = None
        if cb:
            action, did, channel_from_button = cb.group(1).lower(), cb.group(2).lower(), cb.group(3)
            kind = {"go": "APPROVE", "no": "REJECT", "later": "DEFER", "opt": "APPROVE"}.get(action)
            if kind is None:
                receipt("OWNER_CALLBACK_UNKNOWN_ACTION", action=action, did=did)
                continue
            if action == "opt":
                option_chosen = channel_from_button
                channel_from_button = None
            card = reg.get("cards", {}).get(did)
            if card and str(card.get("state")) != "PENDING":
                _rep = card.get("replacement_did")
                _repc = (reg.get("cards", {}) or {}).get(str(_rep)) if _rep else None
                if _repc and str(_repc.get("state")) == "PENDING":
                    # OWNER-LINK v2: an old button must still DO something —
                    # forward the tap to the live replacement card.
                    receipt("TAP_FORWARDED_TO_REPLACEMENT", did=did,
                            replacement=str(_rep), decision=kind)
                    card = _repc
                    did = str(_rep)
                    send_owner_text("↪️ این کارت جایگزین شده بود؛ دکمه‌ات روی کارت "
                                    "فعال (کد %s) اعمال شد." % str(_rep))
                else:
                    receipt("DUPLICATE_TAP_IGNORED", did=did, decision=kind,
                            card_state=str(card.get("state")))
                    _open = [d for d, c2 in (reg.get("cards") or {}).items()
                             if str(c2.get("state")) == "PENDING"]
                    send_owner_text("ℹ️ این کارت بسته است (وضعیت %s). کارت‌های باز: %s\n"
                                    "دکمهٔ همان کارت‌ها را بزن." %
                                    (card.get("state"),
                                     "، ".join(_open) if _open else "—"))
                    continue
            if card:
                target = next((it for it in items if str(it.get("id")) == str(card["id"])),
                              {"id": card["id"], "packets": card.get("packets") or []})
                used_registry = True
            else:
                receipt("OWNER_CALLBACK_UNKNOWN_CARD", did=did, decision=kind)
                send_owner_text("⚠️ این دکمه مربوط به کارتی است که در فهرست نیست "
                                "(کد %s). هیچ اقدامی انجام نشد." % did)
                with DECISIONS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"at": m["at"], "read_at": NOW,
                                         "decision": "CALLBACK_UNKNOWN",
                                         "text": raw[:120]}, sort_keys=True) + "\n")
                continue
        else:
            kind, _ = classify(raw)
        with DECISIONS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": m["at"], "read_at": NOW, "decision": kind,
                                 "text": raw[:200], "kind": m.get("kind"),
                                 "option": option_chosen,
                                 "mirrored_from": str(m.get("mirrored_from") or ""),
                                 "decision_id": (cb.group(2).lower() if cb else None)},
                                sort_keys=True) + "\n")
        receipt("OWNER_DECISION_READ", decision=kind, at_msg=m["at"],
                source=m.get("kind"))
        if target is None:
            # a text reply may name a registered decision id — the id is the
            # identity (it resolves to a card we sent), never the wording
            for did, card in (reg.get("cards") or {}).items():
                if did in raw.lower() and str(card.get("state")) == "PENDING":
                    target = next((it for it in items
                                   if str(it.get("id")) == str(card["id"])),
                                  {"id": card["id"], "packets": card.get("packets") or []})
                    used_registry = True
                    break
        if target is None:
            # associate the reply with the card it answers: explicit id/keyword
            # match first, else refuse (no positional guessing — 2026-09-14 rule)
            KEYWORDS = {"MONEY-BATCH": ("پول", "بسته", "quote", "money"),
                        "TRAFFIC-DECISION": ("ترافیک", "تبلیغ", "traffic", "ad")}
            matches = []
            for it in items:
                if it.get("state"):
                    continue
                iid = str(it.get("id", ""))
                if iid.lower() in raw.lower() or any(k in raw.lower()
                                                     for k in KEYWORDS.get(iid, ())):
                    matches.append(it)
            if len(matches) == 1:
                target = matches[0]
            elif len(matches) > 1:
                receipt("OWNER_DECISION_AMBIGUOUS", decision=kind,
                        candidates=[str(x.get("id")) for x in matches][:4])
                continue
        if target is None:
            # OWNER-LINK v2: a bare «تأیید» with no card named binds to the
            # SOLE pending money card (deterministic n=1, never positional
            # guessing); mirrored B3 rows are excluded from this binding.
            _pend = [(d, c2) for d, c2 in (reg.get("cards") or {}).items()
                     if str(c2.get("state")) == "PENDING"
                     and str(c2.get("id")) != "TEST-DEBUG-OPT"]
            _mirrored = str(m.get("mirrored_from") or "")
            if len(_pend) == 1 and not _mirrored:
                _d1, _c1 = _pend[0]
                target = {"id": _c1.get("id"), "packets": _c1.get("packets") or []}
                cb = None
                option_chosen = None
                channel_from_button = None
                receipt("OWNER_DECISION_BOUND_SOLE_PENDING", did=_d1,
                        decision=kind, item=str(_c1.get("id")))
            else:
                receipt("OWNER_DECISION_NO_IDENTITY", decision=kind,
                        open_cards=[d for d, _ in _pend][:6],
                        mirrored_from=_mirrored or None)
                send_owner_text("🤔 نفهمیدم کدام کارت. کارت‌های باز: %s\n"
                                "دکمهٔ همان کارت را بزن (یا بنویس: تأیید <کد>)." %
                                ("، ".join(d for d, _ in _pend) if _pend else "—"))
                continue
        acted, note = _dispatch_card(target, kind, raw, channel_from_button)
        if acted is None:
            continue
        iid = str(target.get("id"))
        if option_chosen and kind == "APPROVE":
            try:
                acted["option_chosen"] = str(option_chosen)
            except Exception:
                pass
            note = "✅ «%s» ثبت شد — گزینهٔ %s انتخاب شد." % (iid, option_chosen)
        for it in items:
            if str(it.get("id")) == iid:
                it["state"] = ("REJECTED" if kind == "REJECT" else
                               "EXECUTED" if kind == "APPROVE" else
                               "RESOLVED" if kind in ("RATE_CARD", "CHANNEL") else it.get("state"))
                it["result"] = acted
                it["resolved_at"] = NOW
        if used_registry:
            for did, card in (reg.get("cards") or {}).items():
                if str(card.get("id")) == iid and str(card.get("state")) == "PENDING":
                    card["state"] = ("REJECTED" if kind == "REJECT" else
                                     "DEFERRED" if kind == "DEFER" else "EXECUTED")
                    card["resolved_at"] = NOW
                    reg_dirty = True
        receipt("OWNER_DECISION_EXECUTED", item=iid,
                result=json.dumps(acted, default=str)[:300])
        if note:
            send_owner_text(note)
    save_review(items)
    if reg_dirty:
        save_registry(reg)
    print(json.dumps({"at": NOW, "poll": status, "processed": len(msgs)}))


if __name__ == "__main__":
    main()
