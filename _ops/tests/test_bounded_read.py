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
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 42})
    text = center._bounded_read_text(p, timeout_s=3.0)
    assert text is not None and '"last_offset"' in text


def t_b_bounded_read_stall_returns_none_without_blocking():
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"x": 1})
    real_read = Path.read_text

    def stalled(self, *a, **k):
        time.sleep(30)  # simulate an antivirus byte-range lock
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
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 7})
    center._CONFIG_CACHE, center._CONFIG_CACHE_KEY = {}, None
    cfg = center._load_config()
    assert cfg.get("last_offset") == 7
    real_read = Path.read_text

    def stalled(self, *a, **k):
        time.sleep(30)
        return real_read(self, *a, **k)

    Path.read_text = stalled
    try:
        start = time.time()
        cfg2 = center._load_config()
        elapsed = time.time() - start
        # unchanged (mtime,size) -> served from cache without any read
        assert cfg2.get("last_offset") == 7
        assert elapsed < 5.0
    finally:
        Path.read_text = real_read


def t_d_save_config_updates_the_read_cache():
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 1})
    center._CONFIG_CACHE, center._CONFIG_CACHE_KEY = {}, None
    assert center._load_config().get("last_offset") == 1
    center._save_config({"last_offset": 2})
    # cache updated write-through even before any re-read
    assert center._CONFIG_CACHE.get("last_offset") == 2


def t_e_stale_cache_on_unknown_stall_is_served_not_empty():
    root = Path(ENV["ops"]) / "state"
    p = _fake_config(root, {"last_offset": 9})
    center._CONFIG_CACHE, center._CONFIG_CACHE_KEY = {}, None
    assert center._load_config().get("last_offset") == 9
    p.write_text(json.dumps({"last_offset": 10}), encoding="utf-8")
    real_read = Path.read_text

    def stalled(self, *a, **k):
        time.sleep(30)
        return real_read(self, *a, **k)

    Path.read_text = stalled
    try:
        cfg = center._load_config()  # mtime/size changed -> would read; stalls
        assert cfg.get("last_offset") == 9, "stale cache beats frozen loop"
    finally:
        Path.read_text = real_read


def t_f_bounded_http_stall_returns_none_without_blocking():
    import telegram_center.tg_api as tg
    real_open = tg.urllib.request.urlopen

    def stalled(*a, **k):
        time.sleep(30)  # simulate a DNS getaddrinfo block
        return real_open(*a, **k)

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
    import telegram_center.tg_api as tg
    real_open = tg.urllib.request.urlopen

    def stalled(*a, **k):
        time.sleep(30)
        return real_open(*a, **k)

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
    import bounded_io as bio
    root = Path(ENV["ops"]) / "state"
    target = root / "hot.json"
    real_write = Path.write_text

    def stalled(self, *a, **k):
        time.sleep(30)
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
    import telegram_center.tg_api as tg
    root = Path(ENV["ops"]) / "state"
    real_write = Path.write_text

    def stalled(self, *a, **k):
        time.sleep(30)
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

if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_bounded_read: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
