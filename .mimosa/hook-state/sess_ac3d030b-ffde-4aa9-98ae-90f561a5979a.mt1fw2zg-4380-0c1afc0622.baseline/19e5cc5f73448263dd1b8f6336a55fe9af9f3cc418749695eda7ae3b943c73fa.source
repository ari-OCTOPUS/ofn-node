"""Offline test of the llm.py key-leak guard (no network, no API key).

The trap being guarded: elsewhere in this vault ANTHROPIC_API_KEY deliberately
carries a DeepSeek key (routed via ANTHROPIC_BASE_URL). llm.py used to hardcode
api.anthropic.com, so that key would leak there. Now the endpoint is
overridable and _real_transport refuses a non-Anthropic-looking key when the
target is api.anthropic.com -- before any network I/O.
"""
from __future__ import annotations

import importlib
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("ledger", "common", "agents"):
    sys.path.insert(0, str(ROOT / sub))

FAKE_KEY = "<REDACTED-OPENAI-KEY>"


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def main() -> int:
    # 1) default endpoint + non-Anthropic key -> RuntimeError, key never echoed
    os.environ.pop("ANTHROPIC_BASE_URL", None)
    import llm
    llm = importlib.reload(llm)
    assert llm.API_URL == "https://api.anthropic.com/v1/messages", llm.API_URL

    real_urlopen = urllib.request.urlopen

    def must_not_be_called(*a, **k):
        raise AssertionError("network I/O attempted despite leak guard")

    urllib.request.urlopen = must_not_be_called
    try:
        try:
            llm._real_transport("m", "s", "u", 10, api_key=FAKE_KEY)
            raise AssertionError("leak guard did not fire")
        except RuntimeError as e:
            assert FAKE_KEY not in str(e), "guard message echoes the key"
        print("1) guard fires on api.anthropic.com + non sk-ant- key; key not echoed")

        # 2) sk-ant- key on the default endpoint passes the guard (reaches I/O)
        def fake_ok(req, timeout=None):
            assert req.full_url == llm.API_URL, req.full_url
            return _FakeResponse(json.dumps(
                {"content": [], "usage": {}}).encode("utf-8"))

        urllib.request.urlopen = fake_ok
        out = llm._real_transport("m", "s", "u", 10, api_key="sk-ant-test")
        assert out == {"content": [], "usage": {}}, out
        print("2) sk-ant- key on default endpoint passes the guard")

        # 3) ANTHROPIC_BASE_URL override: URL rebuilt, guard stands down
        os.environ["ANTHROPIC_BASE_URL"] = "https://api.deepseek.com/anthropic/"
        llm = importlib.reload(llm)
        assert llm.API_URL == "https://api.deepseek.com/anthropic/v1/messages", llm.API_URL

        seen = {}

        def fake_capture(req, timeout=None):
            seen["url"] = req.full_url
            return _FakeResponse(json.dumps(
                {"content": [], "usage": {}}).encode("utf-8"))

        urllib.request.urlopen = fake_capture
        llm._real_transport("m", "s", "u", 10, api_key=FAKE_KEY)
        assert seen["url"] == "https://api.deepseek.com/anthropic/v1/messages", seen
        print("3) ANTHROPIC_BASE_URL override respected; non-Anthropic key allowed there")

        # 4) reverse direction: a REAL Anthropic key must never leave for another host
        urllib.request.urlopen = must_not_be_called
        try:
            llm._real_transport("m", "s", "u", 10, api_key="sk-ant-real-key-test")
            raise AssertionError("reverse leak guard did not fire")
        except RuntimeError as e:
            assert "sk-ant-real-key-test" not in str(e), "guard message echoes the key"
        print("4) sk-ant- key blocked from non-Anthropic endpoint; key not echoed")
    finally:
        urllib.request.urlopen = real_urlopen
        os.environ.pop("ANTHROPIC_BASE_URL", None)

    print("\nPASS: leak guard green (offline).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
