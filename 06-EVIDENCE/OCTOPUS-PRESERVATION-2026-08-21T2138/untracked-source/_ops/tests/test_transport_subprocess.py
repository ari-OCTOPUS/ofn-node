#!/usr/bin/env python3
"""Subprocess transport — terminable DNS+HTTP (flag-gated)."""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import harness

ENV = harness.setup("transport-subprocess")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import transport_subprocess as ts  # noqa: E402


class _H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok": true, "result": []}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def t_a_off_by_default():
    os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)
    assert ts.enabled() is False


def t_b_subprocess_fetches_local_server_within_deadline():
    server = HTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    os.environ["OCTOPUS_TG_TRANSPORT_SUBPROCESS"] = "1"
    try:
        blob = ts.call(f"http://127.0.0.1:{port}/x", 5.0)
        assert blob is not None and b'"ok": true' in blob
    finally:
        os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)
        server.shutdown()


def t_c_unreachable_host_returns_none_or_fails_soft():
    os.environ["OCTOPUS_TG_TRANSPORT_SUBPROCESS"] = "1"
    try:
        blob = ts.call("http://127.0.0.1:1/x", 2.0)
        assert blob is None  # connection refused -> worker returns None
    finally:
        os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_transport_subprocess: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
