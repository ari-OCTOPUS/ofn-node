"""File-backed stateful Telegram-server fake, shared across processes.

v2: every operation runs under an exclusive fcntl lock (lost-update protection
for concurrent consumers); getUpdates logs (offset, tag) pairs so the drill can
prove WHO polled; getUpdates(offset=K) confirms (drops) every queued id < K and
returns the rest, exactly like Telegram."""
import contextlib
import fcntl
import json
import pathlib


def _load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def _save(p, s):
    pathlib.Path(p).write_text(json.dumps(s), encoding="utf-8")


@contextlib.contextmanager
def _locked(p):
    lf = pathlib.Path(str(p) + ".lock")
    with lf.open("a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def new(path):
    with _locked(path):
        _save(path, {"queue": [], "server_confirmed": [], "requested_offsets": [],
                     "getupdates_calls": [], "sent": []})


def enqueue(path, uid, chat, text):
    with _locked(path):
        s = _load(path)
        s["queue"].append({"update_id": uid,
                           "message": {"chat": {"id": chat}, "text": text}})
        _save(path, s)


def getupdates(path, offset, limit=20, tag="?"):
    with _locked(path):
        s = _load(path)
        s["requested_offsets"].append(offset)
        s["getupdates_calls"].append([offset, tag])
        still, dropped = [], []
        for u in s["queue"]:
            (dropped if u["update_id"] < offset else still).append(u)
        s["queue"] = still
        s["server_confirmed"].extend(u["update_id"] for u in dropped)
        _save(path, s)
        return {"ok": True, "result": still[:limit]}


def sendmessage(path, params):
    with _locked(path):
        s = _load(path)
        s["sent"].append(params)
        _save(path, s)
        return {"ok": True}


def state(path):
    with _locked(path):
        return _load(path)
