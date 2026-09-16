"""G27-v2 producer fixes (2026-09-14, lane OCTOPUS-COMMANDER-G28-20260914).

Owner-mission corrections onto artifact 68132b86:
 1. cross-lane dedupe - a registry change must not re-route a replayed update
    into a different lane (duplicate effect);
 2. re-fsync on dedupe-hit - a row found after a crash between write and fsync
    is only treated as durable AFTER a fresh fsync (dedupe must not "prove"
    unproven durability);
 3. torn-tail repair - an incomplete final line is truncated (a JSONL row's
    commit point is its terminating newline + fsync) with an event; a corrupt
    complete line is evented, never silently ignored; never blind-append onto
    a torn tail;
 4. cursor directory-fsync failure is recorded (not silent);
 5. transport response validation - malformed/error responses yield an explicit
    disposition, cursor untouched, no fabricated success;
Boundary naming: received -> durably persisted -> local checkpoint -> remote
confirmation (the last happens implicitly on the NEXT getUpdates(offset)).
Anchored byte-mode replace; preimage kept; ast.parse gate.
"""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py")
PRE = P.parent / "glass_runner.py.pre-g27v2"

START = "def _lane_append(spool: Path, row: dict, update_id: int) -> bool:"
END = "\ndef main() -> int:"

NEW = '''def _lane_complete_ids(path: Path):
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
    if not data.endswith(b"\\n"):
        cut = data.rfind(b"\\n")
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
            _cut = _data.rfind(b"\\n")
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
    if not isinstance(res, dict) or res.get("ok") is not True or \\
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

'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
i, j = old.find(START), old.find(END)
if i < 0 or j < 0 or j <= i:
    sys.exit("ABORT: anchors not found")
if old.count(START) != 1 or old.count(END) != 1:
    sys.exit("ABORT: anchors not unique")
if "_lane_complete_ids" in old:
    sys.exit("ABORT: v2 already applied")
shutil.copy2(P, PRE)
new = old[:i] + NEW + old[j + 1:]
ast.parse(new)
P.write_bytes(new.encode("utf-8"))
print("preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v2       :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
bad = [c for c in P.read_bytes() if c < 0x20 and c not in (0x0a,)]
print("control-bytes (excl LF):", len(bad))
