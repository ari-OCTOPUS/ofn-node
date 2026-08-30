# -*- coding: utf-8 -*-
"""تست پروب با connection تزریقی — بدون شبکه، بدون خرج."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_probe_v2 import execute_probe  # noqa: E402


class FakeConn:
    """پاسخ معتبر با nonce درست — شبیه‌سازی http.client."""

    def __init__(self, created_offset_s: float = -1.0, status: int = 200,
                 nonce_ok: bool = True, include_usage: bool = True):
        self._created = int(time.time() + created_offset_s)
        self._status = status
        self._nonce_ok = nonce_ok
        self._usage = include_usage

    def request(self, *a, **kw):
        self.body = kw.get("body") or (a[2] if len(a) > 2 else "")

    def getresponse(self):
        body_obj = {"model": "deepseek-v4-flash", "created": self._created,
                    "choices": [{"message": {"content":
                                json.loads(self.body)["messages"][0]["content"].split(": ")[-1]
                                if self._nonce_ok else "WRONG"},
                                "finish_reason": "stop"}]}
        if self._usage:
            body_obj["usage"] = {"prompt_tokens": 12, "completion_tokens": 6,
                                 "total_tokens": 18}
        raw = json.dumps(body_obj).encode()
        return type("R", (), {"status": self._status,
                              "read": lambda s: raw,
                              "headers": {"get": lambda k, d="": d}})()


def _run(conn):
    return execute_probe(run_id="test-run", receipt_id="test123",
                         fx_rate=1.4144, lease_id="test", _conn=conn)


def test_valid_response_pass():
    r = _run(FakeConn())
    assert r["verdict"] == "PROBE_PASS"
    assert r["result"]["calls_attempted"] == 1 and r["result"]["retry_count"] == 0
    assert r["response"]["nonce_match"] is True
    assert r["response"]["semantic_interpretation"] == "COMPLETION_CREATED_TIMESTAMP"
    assert r["response"]["exact_server_stage"] == "UNKNOWN"
    assert r["timing"]["created_minus_send_ms"] is not None


def test_wrong_nonce_invalid_but_counted():
    r = _run(FakeConn(nonce_ok=False))
    assert r["verdict"] == "PROBE_RESPONSE_INVALID"
    assert r["result"]["calls_attempted"] == 1 and r["result"]["calls_succeeded"] == 1


def test_missing_usage_invalid():
    r = _run(FakeConn(include_usage=False))
    assert r["verdict"] == "PROBE_RESPONSE_INVALID"


def test_http_failure_no_retry():
    r = _run(FakeConn(status=500))
    assert r["verdict"] == "PROBE_HTTP_FAILED"
    assert r["result"]["calls_attempted"] == 1 and r["result"]["retry_count"] == 0


def test_future_created_flags_skew():
    r = _run(FakeConn(created_offset_s=+120))
    assert r["timing"]["clock_skew_suspected"] is True
