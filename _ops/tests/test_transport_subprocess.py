#!/usr/bin/env python3
"""Terminable subprocess transport: gate, byte fidelity, and hard deadlines."""
from __future__ import annotations

import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import harness

ENV = harness.setup("transport-subprocess")
_OPS = Path(__file__).resolve().parent.parent
for _path in (str(_OPS), str(_OPS / "telegram_center")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import transport_subprocess as ts  # noqa: E402
import transport_pool as tp  # noqa: E402

_PAYLOAD = b"\x00\xffbinary\x80payload"


class _Handler(BaseHTTPRequestHandler):
    received = b""

    def do_GET(self):
        if self.path == "/rate":
            body = b'{"ok":false,"error_code":429,"parameters":{"retry_after":75}}'
            self.send_response(429)
        else:
            body = b'{"ok":true,"result":[]}'
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        type(self).received = self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Length", str(len(_PAYLOAD)))
        self.end_headers()
        self.wfile.write(_PAYLOAD)

    def log_message(self, *_args):
        pass


def _server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def t_a_wrapper_is_off_by_default():
    os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)
    assert ts.enabled() is False
    try:
        ts.call("http://127.0.0.1:1/x", 0.1)
        raise AssertionError("off wrapper must refuse")
    except RuntimeError:
        pass


def t_b_get_fetches_local_server():
    server = _server()
    os.environ["OCTOPUS_TG_TRANSPORT_SUBPROCESS"] = "1"
    try:
        blob = ts.call(f"http://127.0.0.1:{server.server_address[1]}/x", 2.0)
        assert blob == b'{"ok":true,"result":[]}'
    finally:
        os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)
        server.shutdown()


def t_c_binary_post_and_response_round_trip_exactly():
    server = _server()
    os.environ["OCTOPUS_TG_TRANSPORT_SUBPROCESS"] = "1"
    body = b"\x00\xferequest\x81body"
    try:
        blob = ts.call(
            f"http://127.0.0.1:{server.server_address[1]}/x", 2.0,
            data=body, headers={"Content-Type": "application/octet-stream"},
        )
        assert _Handler.received == body
        assert blob == _PAYLOAD
    finally:
        os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)
        server.shutdown()


def t_d_http_429_preserves_status_body_and_retry_after():
    import urllib.error
    import tg_api

    server = _server()
    os.environ["OCTOPUS_TG_TRANSPORT_SUBPROCESS"] = "1"
    try:
        try:
            ts.call(
                f"http://127.0.0.1:{server.server_address[1]}/rate", 2.0)
            raise AssertionError("429 must be reconstructed as HTTPError")
        except urllib.error.HTTPError as exc:
            payload = tg_api._http_err_json(exc)
            assert exc.code == 429
            assert tg_api._retry_after_from_429(payload) == 75.0
    finally:
        os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)
        server.shutdown()


def t_e_unreachable_endpoint_fails_soft():
    os.environ["OCTOPUS_TG_TRANSPORT_SUBPROCESS"] = "1"
    try:
        assert ts.call("http://127.0.0.1:1/x", 0.2) is None
    finally:
        os.environ.pop("OCTOPUS_TG_TRANSPORT_SUBPROCESS", None)


def t_f_child_timeout_returns_within_bound():
    real_worker = tp._WORKER
    tp._WORKER = "import time; time.sleep(30)"
    try:
        started = time.time()
        result = tp.subprocess_transport("http://127.0.0.1:1/x", 0.1)
        elapsed = time.time() - started
    finally:
        tp._WORKER = real_worker
    assert result is None
    assert elapsed < 3.0, elapsed


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_transport_subprocess: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
