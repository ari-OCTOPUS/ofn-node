# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

TC = Path(__file__).resolve().parents[1] / "telegram_center"
if str(TC) not in sys.path:
    sys.path.insert(0, str(TC))

import poll_sender_bridge_attach as attach


class _FakeQueue:
    def __init__(self, items=None):
        self._items = list(items or [])
        self.confirmed = []

    def due(self, *, limit: int = 10):
        return self._items[:limit]

    def admit(self, **kwargs):
        return {"allowed": True}

    def mark_delivery_attempt(self, key):
        return True

    def confirm(self, key, message_id=None):
        self.confirmed.append((key, message_id))

    def defer(self, key, retry_after=0):
        pass

    def dead_letter(self, key, reason=""):
        pass

    def reconcile_sending(self, key):
        pass


def _flag(path: Path, enabled=True):
    path.write_text(json.dumps({"schema": "live-telegram.v1", "enabled": enabled}), encoding="utf-8")


def _lock(path: Path, exceptions=None):
    path.write_text(json.dumps({
        "schema": "octopus-writer-lease/1",
        "forbidden_actions": ["live sendMessage"],
        "send_exceptions": exceptions or [],
    }), encoding="utf-8")


def test_default_off_skips(monkeypatch, tmp_path):
    monkeypatch.delenv("OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH", raising=False)
    sent = []
    out = attach.maybe_run_after_poll(
        queue=_FakeQueue([{"message_key": "k", "chat_hash": "h"}]),
        send_fn=lambda item: sent.append(item) or {"ok": True, "message_id": 1},
        flag_path=tmp_path / "nope.flag",
    )
    assert out["skipped"] is True
    assert out["reason"] == "attach_default_off"
    assert sent == []


def test_env_on_but_no_exception_refuses_send(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH", "1")
    f = tmp_path / "LIVE-TELEGRAM.flag"
    lk = tmp_path / "lock.json"
    _flag(f, True)
    _lock(lk, exceptions=[])
    sent = []
    out = attach.maybe_run_after_poll(
        queue=_FakeQueue([{"message_key": "k", "chat_hash": "h"}]),
        send_fn=lambda item: sent.append(item) or {"ok": True, "message_id": 1},
        flag=f,
        lock=lk,
    )
    assert out.get("attach_enabled") is True
    assert out.get("ran") is False
    assert out.get("blocked") is True
    assert sent == []


def test_env_on_with_exception_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH", "1")
    f = tmp_path / "LIVE-TELEGRAM.flag"
    lk = tmp_path / "lock.json"
    _flag(f, True)
    _lock(lk, exceptions=[{"expires_at": time.time() + 60}])
    sent = []
    out = attach.maybe_run_after_poll(
        queue=_FakeQueue([{"message_key": "k", "chat_hash": "h"}]),
        send_fn=lambda item: sent.append(item) or {"ok": True, "message_id": 9},
        flag=f,
        lock=lk,
    )
    assert out.get("ran") is True
    assert out.get("sent") == 1
    assert sent


def test_enabled_missing_queue_blocks(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH", "1")
    out = attach.maybe_run_after_poll(queue=None, send_fn=None, flag_path=tmp_path / "x")
    assert out["blocked"] is True
    assert out["reason"] == "missing_queue_or_send_fn"


def test_file_flag_enables_attach(monkeypatch, tmp_path):
    monkeypatch.delenv("OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH", raising=False)
    fp = tmp_path / "TG-CENTER-SENDER-BRIDGE-ATTACH.flag"
    fp.write_text("on\n", encoding="utf-8")
    assert attach.attach_enabled(flag_path=fp) is True
