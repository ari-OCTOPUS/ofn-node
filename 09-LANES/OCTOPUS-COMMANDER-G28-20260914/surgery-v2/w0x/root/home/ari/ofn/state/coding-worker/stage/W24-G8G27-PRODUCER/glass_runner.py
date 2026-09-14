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

import json
import os
import re
import pathlib
import sys
import time
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


def _tg(token: str, method: str, params: dict | None = None,
        timeout: int = 20) -> dict | None:
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


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
# G31 2026-09-14: no trailing boundary - a hex run longer than 64 chars
# must still yield its bounded prefix instead of silently not matching
_HEX_PAT = re.compile(r"\b([a-f0-9]{8,64})", re.I)
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


def _lane_complete_ids(path: Path):
    """Scan a lane file: return (ids, torn_tail_len, corrupt_lines).
    ids = update_ids of newline-terminated parseable rows; torn_tail_len =
    bytes of an unterminated final fragment (incomplete write); corrupt_lines
    counts newline-terminated unparseable rows (kept, evented, never silent)."""
    ids, corrupt, keep = set(), 0, 0
    if not path.exists():
        return ids, 0, 0
    data = path.read_bytes()
    if not data:
        return ids, 0, 0
    if not data.endswith(b"\n"):
        cut = data.rfind(b"\n")
        torn = len(data) - (cut + 1)
        data = data[:cut + 1] if cut >= 0 else b""
    else:
        torn = 0
    keep = len(data)
    for line in data.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        try:
            _uid = json.loads(line).get("update_id")
        except ValueError:
            corrupt += 1
            continue
        if isinstance(_uid, int):
            ids.add(_uid)
    return ids, torn, corrupt


def _refsync(path: Path) -> None:
    """G27v2: fsync an existing lane file without writing bytes, so a row found
    by dedupe after a crash between write and fsync becomes durable BEFORE it
    is trusted."""
    with path.open("a", encoding="utf-8") as _f:
        _f.flush()
        os.fsync(_f.fileno())


def _lane_append(spool: Path, row: dict, update_id: int, lanes: dict = None) -> bool:
    """G27v2: idempotent durable append across ALL lanes. True = NEW row
    written (append + flush + fsync); False = update_id already present in any
    lane (replay; the containing file is re-fsynced first). Raises on IO
    failure - the caller must NOT confirm then."""
    for _p in [spool] + [q for q in (lanes or {}).values() if q != spool]:
        _ids, _torn, _corrupt = _lane_complete_ids(_p)
        if _corrupt:
            try:
                opslib.append_jsonl(
                    opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                    {"event_type": "glass.spool_row_corrupt",
                     "occurred_at": opslib.now_iso(),
                     "payload": {"path": _p.name, "lines": _corrupt}})
            except Exception:
                pass
        if _torn and _p == spool:
            # repair by truncation: the unterminated fragment is not a
            # committed row; its update will be re-delivered unconfirmed
            _data = _p.read_bytes()
            _cut = _data.rfind(b"\n")
            _keep = _data[:_cut + 1] if _cut >= 0 else b""
            _tmp = _p.with_name(_p.name + ".repair")
            with _tmp.open("wb") as _f:
                _f.write(_keep)
                _f.flush()
                os.fsync(_f.fileno())
            os.replace(_tmp, _p)
            try:
                _dfd = os.open(str(_p.parent), os.O_RDONLY)
                try:
                    os.fsync(_dfd)
                finally:
                    os.close(_dfd)
            except OSError:
                pass
            try:
                opslib.append_jsonl(
                    opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                    {"event_type": "glass.spool_torn_tail_repaired",
                     "occurred_at": opslib.now_iso(),
                     "payload": {"path": _p.name, "truncated_bytes": _torn}})
            except Exception:
                pass
            _ids, _torn, _corrupt = _lane_complete_ids(_p)
        if update_id in _ids:
            _refsync(_p)
            return False
    spool.parent.mkdir(parents=True, exist_ok=True)
    with spool.open("a", encoding="utf-8") as _f:
        _f.write(json.dumps(row, ensure_ascii=False) + chr(10))
        _f.flush()
        os.fsync(_f.fileno())
    return True


def _write_cursor(off_path: Path, value: int):
    """G27: durable cursor checkpoint - temp file + fsync + atomic replace +
    directory fsync. Returns None on full success, or the directory-fsync
    error name (the rename itself succeeded; after power loss an un-fsynced
    directory entry may revert the cursor - replay is absorbed by dedupe)."""
    _tmp = off_path.with_name(off_path.name + ".tmp")
    with _tmp.open("w", encoding="utf-8") as _f:
        _f.write(str(value))
        _f.flush()
        os.fsync(_f.fileno())
    os.replace(_tmp, off_path)
    try:
        _dfd = os.open(str(off_path.parent), os.O_RDONLY)
        try:
            os.fsync(_dfd)
        finally:
            os.close(_dfd)
        return None
    except OSError as _e:
        return type(_e).__name__


def process_updates(updates: list[dict], token: str) -> dict:
    """G27: an update is confirmed ONLY after its durable copy exists (or a
    deterministic final disposition). Processing stops at the FIRST persistence
    failure, so the confirmed prefix ends there and Telegram re-delivers from
    the unconfirmed update next cycle. Boundary order per update:
    received -> durably persisted (fsync) -> local checkpoint (cursor) ->
    remote confirmation (happens implicitly on the NEXT getUpdates(offset))."""
    import time as _t
    from ofn.adapters import telegram_glass as tg
    allowed = _allowed_chats()
    stats = {"received": len(updates), "spooled": 0, "replayed": 0,
             "answered": 0, "ignored": 0, "failed": 0,
             "confirmed_upto": None, "stop_reason": None}
    for u in updates:
        uid = int(u.get("update_id", 0))
        msg = u.get("message") or {}
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        try:  # owner order 2026-09-13: never drop owner messages; G8 lane routing
            if chat_id in allowed and text:
                _dec = _route_owner_message(text)
                _sp = _LANES.get(_dec["route"])
                if _sp is not None:
                    _row = {"update_id": uid, "chat": str(chat_id),
                            "text": text[:600],
                            "at": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
                            "lane": _dec["route"],
                            "route_reason": _dec["reason"],
                            "matched": _dec.get("matched", [])[:3]}
                    if _lane_append(_sp, _row, uid, _LANES):
                        stats["spooled"] += 1
                    else:
                        stats["replayed"] += 1
                try:
                    opslib.append_jsonl(
                        opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                        {"event_type": "owner_route.decided",
                         "occurred_at": opslib.now_iso(),
                         "payload": {"lane": _dec["route"], "reason": _dec["reason"],
                                     "matched_n": len(_dec.get("matched", []))}})
                except Exception:  # G27: a routing-receipt failure is a recorded
                    # disposition, never a persistence failure - do not block
                    stats["receipt_failed"] = True
        except Exception as _exc:  # G13+G27: a spool-write failure MUST NOT be
            # confirmed. Break the batch; the cursor stays at the last confirmed
            # update so Telegram re-delivers this update on the next cycle.
            stats["stop_reason"] = "spool_write_failed"
            stats["failed_update_id"] = uid
            try:
                opslib.append_jsonl(
                    opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                    {"event_type": "glass.spool_write_error",
                     "occurred_at": opslib.now_iso(),
                     "payload": {"update_id": uid,
                                 "error": type(_exc).__name__,
                                 "detail": str(_exc)[:120]}})
            except Exception:
                pass
            break
        if chat_id not in allowed or not text.startswith(tuple(tg.COMMANDS)):
            # final disposition (deterministic policy; idempotent under replay)
            stats["ignored"] += 1
            stats["confirmed_upto"] = uid
            continue
        snap = build_snapshot(text.split()[0].lower())
        try:
            resp = tg.route(text.split()[0].lower(), snap)
            out = tg.render_text(resp)
            ok = _tg(token, "sendMessage",
                     {"chat_id": chat_id, "text": out[:3800]}).get("ok")
            if ok:
                stats["answered"] += 1
            else:
                stats["failed"] += 1
        except Exception as e:  # noqa: BLE001
            stats["failed"] += 1
            try:
                opslib.append_jsonl(
                    opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                    {"event_type": "glass.error",
                     "occurred_at": opslib.now_iso(),
                     "payload": {"command": text[:30], "error": type(e).__name__}})
            except Exception:
                pass
        # the inbound is already durable in its lane; a reply failure does not
        # un-confirm it (G27: confirmation follows persistence, not the reply)
        stats["confirmed_upto"] = uid
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
    res = _tg(token, "getUpdates",
              {"offset": offset + 1, "timeout": 0, "limit": 20})
    # G27v2: validate the transport response shape explicitly. A None / error
    # / malformed response yields a disposition; the cursor is untouched and no
    # success is fabricated.
    if not isinstance(res, dict) or res.get("ok") is not True or \
            not isinstance(res.get("result"), list):
        _why = ("transport_none" if res is None else
                "transport_not_ok" if isinstance(res, dict) else
                "transport_malformed:" + type(res).__name__)
        try:
            opslib.append_jsonl(
                opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                {"event_type": "glass.transport_error",
                 "occurred_at": opslib.now_iso(),
                 "payload": {"reason": _why, "offset": offset}})
        except Exception:
            pass
        return {"schema": SCHEMA, "ok": True, "transport": "error",
                "reason": _why, "offset": offset, "received": 0}
    updates = [u for u in res["result"] if isinstance(u, dict)]
    stats = process_updates(updates, token)
    new_cursor = offset
    if stats.get("confirmed_upto") is not None:
        new_cursor = max(offset, int(stats["confirmed_upto"]))
    if new_cursor != offset:
        try:
            _dfsync_err = _write_cursor(off_path, new_cursor)
            if _dfsync_err:
                stats["cursor_dirfsync_failed"] = _dfsync_err
        except Exception as _exc:  # G27: checkpoint failure is a disposition,
            # not data loss: lane rows are durable and deduped by update_id, so
            # the next cycle re-fetches and re-confirms without duplicates.
            stats["stop_reason"] = stats.get("stop_reason") or "checkpoint_failed"
            stats["checkpoint_error"] = type(_exc).__name__
            new_cursor = offset
    stats["offset"] = new_cursor
    return {"schema": SCHEMA, "ok": True, **stats}

def main() -> int:
    print(json.dumps(cycle(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
