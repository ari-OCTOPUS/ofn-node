"""glass_runner — اجراکنندهٔ شیشهٔ تلگرام (ماده-۱۰ لین ۴، PR #114→main).

حلقهٔ گمشدهٔ شیشه بود: telegram_glass کاملاً خالص است (route + render +
snapshot builderها) ولی هیچ چیز آپدیت‌های بات را نمی‌خواند و جواب نمی‌داد.
این runner: getUpdates با offset پایدار → فرمان‌های / شیشه → snapshot درست
→ route → render_text → sendMessage به همان چت فرستنده.

قواعد:
  · فقط توکن OWNER (همان مجازِ رأی Q7) — پاسخ فقط به چت‌های مجاز
  · فقط-خواندنی برای دیتا؛ هرگز route خارج از شیشه، هرگز اجرا
  · offset در state/pulse/glass-offset.txt ماندگار تا پیام تکرار نشود
  · بدون توکن/چت = خروج صادقانه با رسید jsonl، نه کرش
  · خیلی-کوش: هر خطا = ردِ آن آپدیت + ادامه؛ سیکل هرگز worker را نمی‌کشد
"""

from __future__ import annotations

import http.client
import json
import os
import re
import socket
import ssl
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parents[1]))
import opslib  # noqa: E402
import owner_notify  # noqa: E402  (secrets loader الگو می‌گیرد)

SCHEMA = "octopus.glass-runner.v1"
OFFSET_FILE = "glass-offset.txt"

# مسیرهای snapshot — فقط از درخت/state مجاز
_DOCTOR_REPORT = Path.home() / "ofn/data/state/doctor/report.json"
_OWNER_QUEUE = opslib.STATE_DIR / "OWNER-QUEUE.md"


class _IPv4HTTPSConnection(http.client.HTTPSConnection):
    """Prefer IPv4: DietPi often resolves api.telegram.org to broken IPv6 first."""

    def connect(self):
        infos = socket.getaddrinfo(self.host, self.port, socket.AF_INET, socket.SOCK_STREAM)
        raw = socket.create_connection(infos[0][4], self.timeout)
        self.sock = ssl.create_default_context().wrap_socket(
            raw, server_hostname=self.host)


class _IPv4HTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_IPv4HTTPSConnection, req)


_TG_OPENER = urllib.request.build_opener(_IPv4HTTPSHandler())


def _tg(token: str, method: str, params: dict | None = None,
        timeout: int = 20, retries: int = 2) -> dict | None:
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    last: Exception | None = None
    for attempt in range(max(1, retries + 1)):
        try:
            with _TG_OPENER.open(url, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                ConnectionError, OSError) as e:
            last = e
            # HTTP 409 = another getUpdates in flight; do not hammer
            if isinstance(e, urllib.error.HTTPError) and e.code == 409:
                raise
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise
    if last:
        raise last
    return None


def _owner_token() -> str:
    for line in (Path.home() / ".config/ofn/secrets.env") \
            .read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        if k.strip() == "OFN_BOT_TOKEN_OWNER":
            return v.strip()
    return ""


def _allowed_chats() -> set[str]:
    env = dict(os.environ)
    for line in (Path.home() / ".config/ofn/secrets.env") \
            .read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return {c.strip() for c in (env.get("OFN_OWNER_USER_IDS") or
                                "").split(",") if c.strip()}


def build_snapshot(command: str) -> dict:
    """snapshot درست برای هر فرمان — از منابع مجاز فقط-خواندن."""
    from ofn.adapters import telegram_glass as tg
    if command == "/status":
        return tg.build_status_snapshot()
    if command == "/money":
        return tg.build_learning_snapshot(
            Path.home() / "ofn/09-LANES/ECONOMIC-LEARNING/runs")
    if command == "/self":
        return tg.build_self_snapshot()
    if command == "/doctor":
        try:
            r = json.loads(_DOCTOR_REPORT.read_text(encoding="utf-8"))
            return {"doctor_snapshot": r, "failed_units":
                    r.get("counts", {}).get("failed", 0)}
        except (OSError, ValueError):
            return {}
    if command == "/queue":
        try:
            return {"owner_queue": _OWNER_QUEUE.read_text(
                encoding="utf-8")[:1500]}
        except OSError:
            return {}
    return {}  # /receipts — receipt های خود شیشه داخل پاسخ‌اند



# ------------------------------------------------------------------ G8 routing
# Owner order 2026-09-13: a B3 card confirm must never reach the money consumer.
# The decision is made from the VALIDATED IDENTITY OF THE REQUEST - a hash that
# resolves to a registered B3 card - never from words the sender chose.
_LANES = {
    "B3": Path("/home/ari/ofn/state/owner_dialogue/go_b3_inbox.jsonl"),
    "MONEY": Path("/home/ari/ofn/state/revenue-drive/tg-inbox.jsonl"),
}
_B3_REGISTRY = Path("/home/ari/ofn/state/owner_dialogue/go_b3_pending_registry.json")
_CONFIRM_PAT = re.compile(r"(confirm(?:ing)?|\bpi\b|4\s*\+\s*1|تایید|تأیید)", re.I)
_HEX_PAT = re.compile(r"\b([a-f0-9]{8,64})\b", re.I)
_LONG_HASH_MIN = 32


def _parse_ts(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def b3_hashes(registry_path=None):
    path = registry_path or _B3_REGISTRY
    try:
        reg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(x["payload_sha256"]) for x in reg.get("requests", []) if x.get("payload_sha256")]


def _hash_matches(token, payload_sha):
    t, p = (token or "").lower(), (payload_sha or "").lower()
    if not t or not p:
        return False
    return p.startswith(t) or t.startswith(p[: len(t)])


def _route_owner_message(text, known=None):
    """MONEY | B3, decided by REQUEST IDENTITY first and vocabulary last."""
    t = (text or "").strip()
    if not t:
        return {"route": None, "reason": "empty", "matched": []}
    tokens = [h.lower() for h in _HEX_PAT.findall(t)]
    if not tokens:
        return {"route": "MONEY", "reason": "not_b3_shaped", "matched": []}
    known = [str(p).lower() for p in (b3_hashes() if known is None else known)]
    matched = sorted({tok for tok in tokens if any(_hash_matches(tok, p) for p in known)})
    if matched:
        return {"route": "B3", "reason": "resolves_to_registered_b3_card", "matched": matched}
    if any(len(tok) >= _LONG_HASH_MIN for tok in tokens):
        return {"route": "B3", "reason": "carries_payload_length_hash", "matched": []}
    if _CONFIRM_PAT.search(t):
        return {"route": "B3", "reason": "card_confirm_language", "matched": []}
    return {"route": "MONEY", "reason": "not_b3_shaped", "matched": []}


def process_updates(updates: list[dict], token: str) -> dict:
    allowed = _allowed_chats()
    stats = {"answered": 0, "ignored": 0, "failed": 0}
    from ofn.adapters import telegram_glass as tg
    for u in updates:
        # OWNER ORDER 2026-09-18 («تایید بگیره و بفرسته در تلگرام»): an inline
        # button tap is an owner decision with identity (decision id) + channel
        # in its payload. Spool it to the MONEY lane exactly like a text reply
        # so the single consumer (owner_reply.py) sees it; never drop it.
        cb = u.get("callback_query") or {}
        if cb:
            _cq_chat = str(((cb.get("message") or {}).get("chat") or {}).get("id", ""))
            _cq_data = str(cb.get("data") or "").strip()
            try:
                if _cq_chat in allowed and _cq_data:
                    import time as _ct, json as _cj
                    _sp = _LANES["MONEY"]
                    _sp.parent.mkdir(parents=True, exist_ok=True)
                    with _sp.open("a", encoding="utf-8") as _cf:
                        _cf.write(_cj.dumps(
                            {"chat": _cq_chat, "text": _cq_data,
                             "at": _ct.strftime("%Y-%m-%dT%H:%M:%SZ", _ct.gmtime()),
                             "lane": "MONEY", "route_reason": "callback_query",
                             "kind": "callback"}, ensure_ascii=False) + chr(10))
            except Exception as _cexc:
                stats["failed"] += 1
                try:
                    opslib.append_jsonl(
                        opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                        {"event_type": "glass.callback_spool_error",
                         "occurred_at": opslib.now_iso(),
                         "payload": {"error": type(_cexc).__name__,
                                     "detail": str(_cexc)[:120]}})
                except Exception:
                    pass
            else:
                try:  # cosmetic ack; must never fail the spool contract
                    # PR fix: _tg lives in THIS module (telegram_glass has no
                    # HTTP client); the runtime patch called a name that never
                    # existed, so the ack silently never fired on the board.
                    _tg(token, "answerCallbackQuery",
                        {"callback_query_id": str(cb.get("id") or ""),
                         "text": "دریافت شد"})
                except Exception:
                    pass
            continue
    for u in updates:
        msg = u.get("message") or u.get("edited_message") or {}
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        # OWNER-LINK v5: identity = the SENDER. The owner may type from a chat
        # (e.g. a group) whose id is not allow-listed; dropping his words there
        # read to him as "it does not understand me" (2026-09-18).
        sender_id = str((msg.get("from") or {}).get("id", ""))
        from_chat = chat_id
        if chat_id not in allowed and sender_id in allowed and sender_id:
            chat_id = sender_id
        text = (msg.get("text") or "").strip()
        try:  # owner order 2026-09-13: never drop owner messages; G8 lane routing
            if chat_id in allowed and text:
                import time as _t, json as _j
                _dec = _route_owner_message(text)
                # OWNER-LINK v2 (2026-09-18): ALWAYS mirror to the MONEY spool so
                # no owner message can be lost by lane routing; B3-routed ones are
                # flagged so the money consumer never binds them to a money card.
                try:
                    _mir = _j.dumps({"chat": str(chat_id), "text": text[:600],
                                     "at": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
                                     "lane": "MONEY",
                                     "route_reason": "mirror:" + str(_dec["reason"]),
                                     "mirrored_from": _dec["route"],
                                     "kind": "message"}, ensure_ascii=False)
                    with _LANES["MONEY"].open("a", encoding="utf-8") as _mf:
                        _mf.write(_mir + chr(10))
                except Exception:
                    pass
                _sp = _LANES.get(_dec["route"])
                if _sp is not None:
                    _sp.parent.mkdir(parents=True, exist_ok=True)
                    with _sp.open("a", encoding="utf-8") as _f:
                        _f.write(_j.dumps({"chat": str(chat_id), "from_chat": from_chat, "text": text[:600],
                                           "at": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
                                           "lane": _dec["route"],
                                           "route_reason": _dec["reason"],
                                           "matched": _dec.get("matched", [])[:3]},
                                          ensure_ascii=False) + chr(10))
                    opslib.append_jsonl(
                        opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                        {"event_type": "owner_route.decided",
                         "occurred_at": opslib.now_iso(),
                         "payload": {"lane": _dec["route"], "reason": _dec["reason"],
                                     "matched_n": len(_dec.get("matched", []))}})
        except Exception as _exc:  # G13: never swallow a spool-write failure silently
            try:
                opslib.append_jsonl(
                    opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                    {"event_type": "glass.spool_write_error",
                     "occurred_at": opslib.now_iso(),
                     "payload": {"error": type(_exc).__name__,
                                 "detail": str(_exc)[:120]}})
            except Exception:
                pass
        if chat_id not in allowed or not text.startswith(tuple(tg.COMMANDS)):
            # OWNER-LINK v4: a dropped update must never be invisible.
            try:
                import json as _dj, time as _dt
                with (pathlib.Path("/home/ari/ofn/state/revenue-drive")
                      / "glass-seen.jsonl").open("a", encoding="utf-8") as _df:
                    _df.write(_dj.dumps({
                        "at": _dt.strftime("%Y-%m-%dT%H:%M:%SZ", _dt.gmtime()),
                        "update_id": u.get("update_id"),
                        "type": ("callback" if u.get("callback_query") else
                                 "edited_message" if u.get("edited_message") else "message"),
                        "chat": chat_id, "sender": sender_id,
                        "sender_allowed": sender_id in allowed,
                        "chat_allowed": chat_id in allowed,
                        "text": text[:120], "verdict": ("not_a_command"
                            if chat_id in allowed else "chat_not_allowed")},
                        ensure_ascii=False) + chr(10))
            except Exception:
                pass
            stats["ignored"] += 1
            continue
        snap = build_snapshot(text.split()[0].lower())
        try:
            resp = tg.route(text.split()[0].lower(), snap)
            out = tg.render_text(resp)
            ok = _tg(token, "sendMessage",
                     {"chat_id": chat_id, "text": out[:3800]}).get("ok")
            stats["answered" if ok else "failed"] += \
                1 if ok else 1
        except Exception as e:  # noqa: BLE001 — خیلی‌کوش
            stats["failed"] += 1
            opslib.append_jsonl(
                opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                {"event_type": "glass.error",
                 "occurred_at": opslib.now_iso(),
                 "payload": {"command": text[:30],
                             "error": type(e).__name__}})
    return stats


def cycle(state_dir: Path | None = None) -> dict:
    token = _owner_token()
    sd = state_dir or opslib.STATE_DIR
    if not token:
        return {"schema": SCHEMA, "ok": False, "reason": "not-armed"}
    off_path = sd / OFFSET_FILE
    try:
        offset = int(off_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        offset = 0
    try:
        res = _tg(token, "getUpdates",
                  {"offset": offset + 1, "timeout": 0, "limit": 20})
    except urllib.error.HTTPError as e:
        reason = "conflict" if e.code == 409 else f"http_{e.code}"
        return {"schema": SCHEMA, "ok": False, "reason": reason,
                "error": type(e).__name__, "detail": str(e)[:120]}
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        return {"schema": SCHEMA, "ok": False, "reason": "transport",
                "error": type(e).__name__, "detail": str(e)[:120]}
    updates = (res or {}).get("result", [])
    stats = process_updates(updates, token)
    # G27: only advance past updates whose lane write succeeded. A spool
    # write failure leaves the updates unconfirmed on Telegram; advancing
    # here would permanently lose them (at-most-once -> at-least-once).
    _had_error = stats.get("failed", 0) > 0 or stats.get("spool_errors", 0) > 0
    if not _had_error:
        for u in updates:
            offset = max(offset, int(u.get("update_id", offset)))
    if updates:
        off_path.parent.mkdir(parents=True, exist_ok=True)
        off_path.write_text(str(offset), encoding="utf-8")
    return {"schema": SCHEMA, "ok": True, "offset": offset, **stats}


def main() -> int:
    result = cycle()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
