"""One producer cycle in an isolated subprocess (real process boundary).

usage: g27runner.py <artifact> <fixture_root> <server_file> <mode> [fsync_log]
modes:
  normal                          plain cycle
  crash_before_checkpoint         os._exit(9) inside _write_cursor (after lane fsync)
  crash_after_write_before_fsync  os._exit(9) on the FIRST lane-file fsync
                                  (row written+flushed, never fsynced)
  count_fsync                     log every os.fsync fd->path to fsync_log
  dirfsync_fail                   fsync raises for the pulse DIRECTORY fd
  transport_none | transport_not_ok | transport_malformed
                                  _tg returns None / {"ok":false} / a list
"""
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys

artifact, fx_s, server, mode = sys.argv[1:5]
fx = pathlib.Path(fx_s)
for p in ("/home/ari/ofn", "/home/ari/ofn/ofn", "/home/ari/ofn/ofn/agents",
          "/home/ari/ofn/ofn/budget", "/tmp"):
    sys.path.insert(0, p)

import g27server  # noqa: E402

if mode == "count_fsync":
    _log = pathlib.Path(sys.argv[5])
    _real = os.fsync

    def _fsync_log(fd):
        try:
            p = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            p = "?"
        with _log.open("a", encoding="utf-8") as f:
            f.write(p + "\n")
        return _real(fd)
    os.fsync = _fsync_log
elif mode == "crash_after_write_before_fsync":
    _real = os.fsync

    def _fsync_kill(fd):
        try:
            p = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            p = "?"
        if p.endswith(".jsonl") and "/lanes/" in p:
            os._exit(9)  # hard death between write() and fsync()
        return _real(fd)
    os.fsync = _fsync_kill

if artifact.endswith(".py"):
    spec = importlib.util.spec_from_file_location("glass_prod", artifact)
else:  # preimage files carry no .py suffix; give the loader explicitly
    spec = importlib.util.spec_from_file_location(
        "glass_prod", artifact,
        loader=importlib.machinery.SourceFileLoader("glass_prod", artifact))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def _tg(token, method, params=None, timeout=20):
    if method == "getUpdates":
        return g27server.getupdates(server, params["offset"],
                                    params.get("limit", 20), tag="glass")
    if method == "sendMessage":
        return g27server.sendmessage(server, params)
    raise AssertionError(method)


if mode in ("transport_none", "transport_not_ok", "transport_malformed"):
    _bad = {"transport_none": None,
            "transport_not_ok": {"ok": False, "description": "fixture"},
            "transport_malformed": ["garbage"]}  # type: ignore[assignment]
    _orig_tg = _tg

    def _tg(token, method, params=None, timeout=20):  # noqa: F811
        if method == "getUpdates":
            return _bad[mode]
        return _orig_tg(token, method, params, timeout)


class _Ops:
    STATE_DIR = fx / "ops-state"

    def now_iso(self):
        return "2026-09-14T00:00:00Z"

    def append_jsonl(self, path, obj, **kw):
        with (fx / "opslib-events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        return {}


g._tg = _tg
g._owner_token = lambda: "fixture-token"
g._allowed_chats = lambda: {"6150431610"}
g.opslib = _Ops()
g._LANES = {"B3": fx / "lanes/b3/go_b3_inbox.jsonl",
            "MONEY": fx / "lanes/money/tg-inbox.jsonl"}
g._B3_REGISTRY = fx / "registry.json"

if mode == "crash_before_checkpoint":
    def _wc(off_path, value):
        os._exit(9)  # hard death after persistence, before any cursor byte
    g._write_cursor = _wc
elif mode == "dirfsync_fail":
    _real2 = os.fsync

    def _fsync_dirfail(fd):
        try:
            p = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            p = "?"
        if p == str(fx / "pulse"):
            raise OSError("injected directory-fsync failure")
        return _real2(fd)
    os.fsync = _fsync_dirfail

r = g.cycle(fx / "pulse")
print(json.dumps(r, ensure_ascii=False))
sys.exit(0)
