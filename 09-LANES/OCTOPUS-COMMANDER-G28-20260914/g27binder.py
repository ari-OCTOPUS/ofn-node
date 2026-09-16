"""One binder cycle in an isolated subprocess against the shared fake server.

usage: g27binder.py <old|new> <fixture_root> <server_file> <mode>
  old = live bytes  /home/ari/ofn/ofn/agents/go_b3_owner_bind.py
  new = candidate   .../stage/TASK-W24-BINDER-SPOOL-006/go_b3_owner_bind.py
modes:
  poll                old binder: one poll_telegram_once()
  slow_poll           old binder: spool_append sleeps 5s first (cutover overlap)
  crash_before_spool  old binder: os._exit(9) at first spool_append
  consume             candidate: one consume_glass_spool_once()
The fake urlopen is installed for BOTH variants: if the candidate EVER tries
to poll, the attempt lands in the server log tagged binder-new instead of the
real Telegram API.
"""
import importlib.util
import io
import json
import os
import pathlib
import sys
import time
import urllib.request

which, fx_s, server, mode = sys.argv[1:5]
fx = pathlib.Path(fx_s)
for p in ("/tmp", "/home/ari/ofn", "/home/ari/ofn/ofn",
          "/home/ari/ofn/ofn/agents", "/home/ari/ofn/ofn/budget"):
    sys.path.insert(0, p)
import g27server  # noqa: E402

OLD = "/home/ari/ofn/ofn/agents/go_b3_owner_bind.py"
NEW = ("/home/ari/ofn/state/coding-worker/stage/TASK-W24-BINDER-SPOOL-006/"
       "go_b3_owner_bind.py")
TAG = "binder-old" if which == "old" else "binder-new"

if which == "new":
    os.environ["GO_B3_BIND_STATE"] = str(fx / "owner_dialogue")
    os.environ["GO_B3_GLASS_SPOOL"] = str(fx / "lanes/b3/go_b3_inbox.jsonl")


class _Resp:
    def __init__(self, data):
        self._d = data

    def read(self):
        return self._d

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(url, timeout=20):
    import urllib.parse as up
    q = up.parse_qs(up.urlsplit(url).query)
    off = int(q.get("offset", ["0"])[0])
    res = g27server.getupdates(server, off, tag=TAG)
    return _Resp(json.dumps(res).encode())


urllib.request.urlopen = _fake_urlopen

spec = importlib.util.spec_from_file_location("binder_" + which,
                                              OLD if which == "old" else NEW)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

od = fx / "owner_dialogue"
od.mkdir(parents=True, exist_ok=True)
if which == "old":
    b.STATE = od
    b.REGISTRY = od / "go_b3_pending_registry.json"
    b.SPOOL = od / "go_b3_tg_spool.jsonl"
    b.OFFSET = od / "go_b3_tg_offset.txt"
    b.DECISIONS = od / "owner_decision.v1.jsonl"
b._secrets = lambda: {"OFN_BOT_TOKEN_OWNER": "fixture-token"}
b.owner_chat_ids = lambda: ["6150431610"]
if not b.REGISTRY.exists():
    b.REGISTRY.write_text(json.dumps({"requests": []}), encoding="utf-8")

if mode == "crash_before_spool":
    def _die(obj):
        sys.stdout.flush()
        os._exit(9)
    b.spool_append = _die
elif mode == "slow_poll":
    _real_append = b.spool_append

    def _slow(obj):
        time.sleep(5)
        _real_append(obj)
    b.spool_append = _slow

if mode == "consume":
    r = b.consume_glass_spool_once()
else:
    r = b.poll_telegram_once()
print(json.dumps(r, ensure_ascii=False))
sys.exit(0)
