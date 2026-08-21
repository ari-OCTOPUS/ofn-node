#!/usr/bin/env python3
"""Bounded state-file reads — regression for the 2026-08-21 center hang.

A third-party byte-range lock on center-config.json (antivirus scan of a
frequently os.replace'd file) froze read_text and silenced the center twice.
The fix: _load_config serves a write-through cache and never blocks the poll
loop; mission card reads are time-boxed the same way.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("bounded-read")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import center  # noqa: E402


def _fake_config(root: Path, payload: dict) -> Path:
    p = root / "telegram" / "center-config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def t_a_bounded_read_returns_content_fast():
    _drain_pool()
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 42})
    text = center._bounded_read_text(p, timeout_s=3.0)
    assert text is not None and '"last_offset"' in text


def t_b_bounded_read_stall_returns_none_without_blocking():
    _drain_pool()
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"x": 1})
    real_read = Path.read_text

    def stalled(self, *a, **k):
        time.sleep(10.0)  # simulate an antivirus byte-range lock
        return real_read(self, *a, **k)

    Path.read_text = stalled
    try:
        start = time.time()
        text = center._bounded_read_text(p, timeout_s=1.5)
        elapsed = time.time() - start
        assert text is None
        assert elapsed < 5.0, f"bounded read must not block: {elapsed:.1f}s"
    finally:
        Path.read_text = real_read


def t_c_load_config_serves_cache_when_read_stalls():
    _drain_pool()
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 7})
    center._CONFIG_MANAGER = None
    assert center._load_config().get("last_offset") == 7
    p.write_text(json.dumps({"last_offset": 8}), encoding="utf-8")
    real_read = Path.read_text

    def stalled(self, *a, **k):
        time.sleep(10.0)
        return real_read(self, *a, **k)

    Path.read_text = stalled
    try:
        start = time.time()
        cfg = center._load_config()
        elapsed = time.time() - start
        assert cfg.get("last_offset") == 7, "stale last-known-good must be served"
        assert elapsed < 8.0
    finally:
        Path.read_text = real_read
        _drain_pool()

def t_d_save_config_updates_the_read_cache():
    _drain_pool()
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 1})
    center._CONFIG_MANAGER = None
    assert center._load_config().get("last_offset") == 1
    assert center._save_config({"last_offset": 2})
    assert center._load_config().get("last_offset") == 2, "write-through must refresh snapshot"

def t_e_stale_cache_on_unknown_stall_is_served_not_empty():
    _drain_pool()
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 9})
    center._CONFIG_MANAGER = None
    assert center._load_config().get("last_offset") == 9
    p.write_text(json.dumps({"last_offset": 10}), encoding="utf-8")
    real_read = Path.read_text

    def stalled(self, *a, **k):
        time.sleep(10.0)
        return real_read(self, *a, **k)

    Path.read_text = stalled
    try:
        cfg = center._load_config()
        assert cfg.get("last_offset") == 9, "stale last-known-good beats frozen loop"
    finally:
        Path.read_text = real_read
        _drain_pool()

def t_f_bounded_http_stall_returns_none_without_blocking():
    _drain_pool()
    import telegram_center.tg_api as tg
    real_open = tg.urllib.request.urlopen

    def stalled(*a, **k):
        time.sleep(10.0)  # simulate a DNS getaddrinfo block
        raise TimeoutError("fixture DNS stall")

    tg.urllib.request.urlopen = stalled
    try:
        start = time.time()
        blob = tg._bounded_http("https://api.telegram.org/", timeout_s=1.0)
        elapsed = time.time() - start
        assert blob is None
        assert elapsed < 8.0, f"bounded http must not block: {elapsed:.1f}s"
    finally:
        tg.urllib.request.urlopen = real_open


def t_g_stalled_transport_fails_soft_on_get_and_post():
    _drain_pool()
    import telegram_center.tg_api as tg
    real_open = tg.urllib.request.urlopen

    def stalled(*a, **k):
        time.sleep(10.0)
        raise TimeoutError("fixture DNS stall")

    tg.urllib.request.urlopen = stalled
    try:
        start = time.time()
        try:
            tg._url_json_get("https://api.telegram.org/botX/getUpdates", 1.0)
            raised = False
        except TimeoutError:
            raised = True
        assert raised, "stalled get must fail soft with TimeoutError"
        try:
            tg._url_json_post("https://api.telegram.org/botX/sendMessage", {"x": 1}, 1.0)
            raised = False
        except TimeoutError:
            raised = True
        assert raised, "stalled post must fail soft with TimeoutError"
        assert time.time() - start < 20.0
    finally:
        tg.urllib.request.urlopen = real_open


def t_h_bounded_write_stall_returns_false_quickly():
    _drain_pool()
    import bounded_io as bio
    root = Path(ENV["ops"]) / "state"
    target = root / "hot.json"
    real_write = Path.write_text

    def stalled(self, *a, **k):
        time.sleep(10.0)
        return real_write(self, *a, **k)

    Path.write_text = stalled
    try:
        start = time.time()
        ok = bio.write_text(target, "{}", timeout_s=1.5)
        elapsed = time.time() - start
        assert ok is False
        assert elapsed < 6.0, f"bounded write must not block: {elapsed:.1f}s"
    finally:
        Path.write_text = real_write


def t_i_record_poll_survives_stalled_write():
    _drain_pool()
    import telegram_center.tg_api as tg
    root = Path(ENV["ops"]) / "state"
    real_write = Path.write_text

    def stalled(self, *a, **k):
        time.sleep(10.0)
        return real_write(self, *a, **k)

    Path.write_text = stalled
    try:
        start = time.time()
        state = tg._record_poll(True, "")
        elapsed = time.time() - start
        assert state.get("consecutive_failures") == 0
        assert elapsed < 6.0, f"poll health write must not block: {elapsed:.1f}s"
    finally:
        Path.write_text = real_write

def t_j_100_consecutive_dns_stalls_keep_workers_bounded():
    _drain_pool()
    import bounded_io as bio
    import telegram_center.tg_api as tg
    real_open = tg.urllib.request.urlopen

    def stalled(*a, **k):
        time.sleep(10.0)
        raise TimeoutError("fixture DNS stall")

    tg.urllib.request.urlopen = stalled
    try:
        for _ in range(100):
            start = time.time()
            blob = tg._bounded_http("https://api.telegram.org/x", timeout_s=0.5)
            assert blob is None
            assert time.time() - start < 6.0, "deadline exceeded"
        assert bio.active_worker_count() <= 4, bio.active_worker_count()
    finally:
        tg.urllib.request.urlopen = real_open


def t_k_100_consecutive_config_stalls_keep_cache_and_workers_bounded():
    import bounded_io as bio
    _drain_pool()
    root = Path(ENV["ops"]) / "state"
    pfile = _fake_config(root, {"last_offset": 1})
    center._CONFIG_MANAGER = None
    assert center._load_config().get("last_offset") == 1
    real_read = Path.read_text

    def stalled(self, *a, **k):
        time.sleep(10.0)
        return real_read(self, *a, **k)

    Path.read_text = stalled
    try:
        for i in range(100):
            pfile.write_text(json.dumps({"last_offset": i + 2}), encoding="utf-8")
            cfg = center._load_config()
            assert cfg.get("last_offset") == 1, "last-known-good must survive"
        assert bio.active_worker_count() <= 4
    finally:
        Path.read_text = real_read
        _drain_pool()

def t_l_malformed_config_never_replaces_last_known_good():
    _drain_pool()
    root = Path(ENV["ops"]) / "state"
    pfile = _fake_config(root, {"last_offset": 5})
    center._CONFIG_MANAGER = None
    assert center._load_config().get("last_offset") == 5
    pfile.write_text("{not-json", encoding="utf-8")
    cfg = center._load_config()
    assert cfg.get("last_offset") == 5, "malformed must not replace last-known-good"

def _drain_pool(max_wait=14.0):
    """Wait for the bounded worker pool to empty (order-independent tests)."""
    import bounded_io as _bio
    deadline = time.time() + max_wait
    while time.time() < deadline and _bio.active_worker_count() > 0:
        time.sleep(0.1)

if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_bounded_read: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
