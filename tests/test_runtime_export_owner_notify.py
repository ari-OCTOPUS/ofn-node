"""Paired test for the exported R1 notify retry (RUNTIME-EXPORT PR).

Red against canonical (no _urlopen_retry), green with the exported runtime
file. The 44 notify.failed events behind the fix were transient URLErrors;
one retry turns a blip into a delivered notification while persistent
failure still raises for the caller to record.
"""
import time

import pytest

from ofn.agents import owner_notify


def test_retries_once_then_succeeds(monkeypatch):
    calls = []

    def flaky(req, timeout=None):
        calls.append(timeout)
        if len(calls) == 1:
            raise OSError("transient hiccup")
        return "delivered"

    sleeps = []
    monkeypatch.setattr(owner_notify.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    out = owner_notify._urlopen_retry("req", timeout=15, attempts=2)
    assert out == "delivered"
    assert calls == [15, 15]
    assert sleeps == [5]


def test_persistent_failure_raises_last(monkeypatch):
    def always_fail(req, timeout=None):
        raise OSError("down")

    monkeypatch.setattr(owner_notify.urllib.request, "urlopen", always_fail)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(OSError):
        owner_notify._urlopen_retry("req", timeout=15, attempts=2)


def test_single_attempt_never_sleeps(monkeypatch):
    def fail(req, timeout=None):
        raise OSError("down")

    sleeps = []
    monkeypatch.setattr(owner_notify.urllib.request, "urlopen", fail)
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    with pytest.raises(OSError):
        owner_notify._urlopen_retry("req", timeout=15, attempts=1)
    assert sleeps == []
