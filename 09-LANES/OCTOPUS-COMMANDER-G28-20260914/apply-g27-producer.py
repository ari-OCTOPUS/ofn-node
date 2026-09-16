"""G27 producer-durability patch (2026-09-14, lane OCTOPUS-COMMANDER-G28-20260914).

Builds W24-G8G27-PRODUCER/glass_runner.py from the accepted G8 candidate
(69c8ec8f) by replacing the process_updates..cycle region with the durable
contract. Byte mode; anchor boundaries asserted unique; ast.parse + import smoke
run by the battery script.
"""
import ast
import hashlib
import pathlib
import shutil
import sys

SRC = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/W24-G8-ROUTING-v2/glass_runner.py")
DST_DIR = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER")
DST = DST_DIR / "glass_runner.py"

START = "def process_updates(updates: list[dict], token: str) -> dict:"
END = "\ndef main() -> int:"

NEW = '''def _lane_append(spool: Path, row: dict, update_id: int) -> bool:
    """G27: idempotent durable lane append. Returns True when a NEW row was
    written, False when update_id is already spooled (replay after a lost
    checkpoint). Raises on IO failure - the caller must NOT confirm then."""
    if spool.exists():
        for line in spool.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                if json.loads(line).get("update_id") == update_id:
                    return False
            except ValueError:
                continue
    spool.parent.mkdir(parents=True, exist_ok=True)
    with spool.open("a", encoding="utf-8") as _f:
        _f.write(json.dumps(row, ensure_ascii=False) + chr(10))
        _f.flush()
        os.fsync(_f.fileno())
    return True


def _write_cursor(off_path: Path, value: int) -> None:
    """G27: durable cursor checkpoint - temp file + fsync + atomic replace +
    best-effort directory fsync. A crash between spool-write and this checkpoint
    re-delivers on the next cycle and is deduped by update_id."""
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
    except OSError:
        pass


def process_updates(updates: list[dict], token: str) -> dict:
    """G27: an update is confirmed ONLY after its durable copy exists (or a
    deterministic final disposition). Processing stops at the FIRST persistence
    failure, so the confirmed prefix ends there and Telegram re-delivers from
    the unconfirmed update next cycle. A success later in a batch never
    confirms an earlier unconfirmed update."""
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
                    if _lane_append(_sp, _row, uid):
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
    updates = (res or {}).get("result", [])
    stats = process_updates(updates, token)
    new_cursor = offset
    if stats.get("confirmed_upto") is not None:
        new_cursor = max(offset, int(stats["confirmed_upto"]))
    if new_cursor != offset:
        try:
            _write_cursor(off_path, new_cursor)
        except Exception as _exc:  # G27: checkpoint failure is a disposition,
            # not data loss: lane rows are durable and deduped by update_id, so
            # the next cycle re-fetches and re-confirms without duplicates.
            stats["stop_reason"] = stats.get("stop_reason") or "checkpoint_failed"
            stats["checkpoint_error"] = type(_exc).__name__
            new_cursor = offset
    stats["offset"] = new_cursor
    return {"schema": SCHEMA, "ok": True, **stats}

'''

raw = SRC.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
i = old.find(START)
j = old.find(END)
if i < 0 or j < 0 or j <= i:
    sys.exit("ABORT: anchors not found (i=%d j=%d)" % (i, j))
if old.count(START) != 1 or old.count(END) != 1:
    sys.exit("ABORT: anchors not unique")
if "G27:" in old:
    sys.exit("ABORT: already patched")
DST_DIR.mkdir(parents=True, exist_ok=True)
new = old[:i] + NEW + old[j + 1:]
ast.parse(new)
DST.write_bytes(new.encode("utf-8"))
shutil.copy2(SRC, DST_DIR / "glass_runner.py.pre-g27")
print("base artifact :", hashlib.sha256(SRC.read_bytes()).hexdigest()[:16])
print("g27 artifact  :", hashlib.sha256(DST.read_bytes()).hexdigest()[:16])
