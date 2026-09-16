# -*- coding: utf-8 -*-
"""Tests for LIVE-TELEGRAM.flag gate + TelegramOrgan + SenderBridge attach."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
TC = OPS / "telegram_center"
LOOPS = OPS / "loops"
for p in (str(TC), str(LOOPS), str(OPS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import live_telegram_gate as gate
import center_sender_bridge as csb
import telegram_organ as organ


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


def _write_flag(path: Path, enabled: bool = True):
    path.write_text(json.dumps({"schema": "live-telegram.v1", "enabled": enabled, "note": "test"}), encoding="utf-8")


def _write_lock(path: Path, *, forbidden=True, exceptions=None):
    data = {
        "schema": "octopus-writer-lease/1",
        "agent_id": "test",
        "forbidden_actions": ["live sendMessage"] if forbidden else [],
        "send_exceptions": exceptions or [],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_flag_disabled_blocks_live_mode(tmp_path: Path):
    f = tmp_path / "LIVE-TELEGRAM.flag"
    _write_flag(f, enabled=False)
    lock = tmp_path / "lock.json"
    _write_lock(lock, exceptions=[{"expires_at": time.time() + 60}])
    st = gate.evaluate(flag=f, lock=lock)
    assert st["live_mode_allowed"] is False
    assert st["send_allowed"] is False


def test_flag_enabled_without_exception_live_mode_only(tmp_path: Path):
    f = tmp_path / "LIVE-TELEGRAM.flag"
    _write_flag(f, enabled=True)
    lock = tmp_path / "lock.json"
    _write_lock(lock, exceptions=[])
    st = gate.evaluate(flag=f, lock=lock)
    assert st["live_mode_allowed"] is True
    assert st["send_allowed"] is False
    assert st["reason"] == "no_active_send_exception"


def test_flag_plus_exception_allows_send(tmp_path: Path):
    f = tmp_path / "LIVE-TELEGRAM.flag"
    _write_flag(f, enabled=True)
    lock = tmp_path / "lock.json"
    _write_lock(lock, exceptions=[{"expires_at": time.time() + 120, "purpose": "test"}])
    st = gate.evaluate(flag=f, lock=lock)
    assert st["send_allowed"] is True


def test_organ_live_respects_canonical_flag(tmp_path: Path, monkeypatch):
    f = tmp_path / "LIVE-TELEGRAM.flag"
    _write_flag(f, enabled=True)
    monkeypatch.setenv("OCTOPUS_LIVE_TELEGRAM_FLAG", str(f))
    state = tmp_path / "state"
    o = organ.TelegramOrgan(state, allowlist={1}, live=True, transport=lambda c, t: True)
    assert o.live is True
    monkeypatch.setenv("OCTOPUS_LIVE_TELEGRAM_FLAG", str(tmp_path / "missing.flag"))
    o2 = organ.TelegramOrgan(state, allowlist={1}, live=True)
    assert o2.live is False


def test_organ_dry_when_caller_live_false_even_if_flag(tmp_path: Path, monkeypatch):
    f = tmp_path / "LIVE-TELEGRAM.flag"
    _write_flag(f, enabled=True)
    monkeypatch.setenv("OCTOPUS_LIVE_TELEGRAM_FLAG", str(f))
    o = organ.TelegramOrgan(tmp_path / "s", allowlist={1}, live=False)
    assert o.live is False


def test_sender_bridge_blocked_without_exception(tmp_path: Path):
    f = tmp_path / "LIVE-TELEGRAM.flag"
    _write_flag(f, enabled=True)
    lock = tmp_path / "lock.json"
    _write_lock(lock, exceptions=[])
    q = _FakeQueue(items=[{"message_key": "k1", "chat_hash": "abc"}])
    sent = []

    def send_fn(item):
        sent.append(item)
        return {"ok": True, "message_id": 1}

    bridge = csb.build_bridge(q, send_fn)
    out = csb.run_once_if_allowed(bridge, flag=f, lock=lock)
    assert out["ran"] is False
    assert out["blocked"] is True
    assert sent == []


def test_sender_bridge_runs_with_exception(tmp_path: Path):
    f = tmp_path / "LIVE-TELEGRAM.flag"
    _write_flag(f, enabled=True)
    lock = tmp_path / "lock.json"
    _write_lock(lock, exceptions=[{"expires_at": time.time() + 60}])
    q = _FakeQueue(items=[{"message_key": "k1", "chat_hash": "abc"}])
    sent = []

    def send_fn(item):
        sent.append(item)
        return {"ok": True, "message_id": 42}

    bridge = csb.build_bridge(q, send_fn)
    out = csb.run_once_if_allowed(bridge, flag=f, lock=lock)
    assert out["ran"] is True
    assert out["sent"] == 1
    assert sent and sent[0]["message_key"] == "k1"
