from pathlib import Path
import json, time, shutil, subprocess, sys

ROOT = Path(r"F:/backup")
OPS = ROOT / "_ops"
TC = OPS / "telegram_center"
EVID = ROOT / "06-EVIDENCE" / "OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23" / "CENTER-BRIDGE-ATTACH-DEFAULT-OFF"
EVID.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y-%m-%dT%H:%M:%S+10:00")

center_path = TC / "center.py"
bak = Path(str(center_path) + ".bak-bridge-attach-20260823")
if not bak.exists():
    shutil.copy2(center_path, bak)

attach_path = TC / "poll_sender_bridge_attach.py"
attach_path.write_text(r'''#!/usr/bin/env python3
"""Default-OFF poll-path attach for owner-gated SenderBridge (arch-loop slice).

Enable only when OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH is truthy OR
_ops/TG-CENTER-SENDER-BRIDGE-ATTACH.flag exists. Even then, actual send is
refused by live_telegram_gate unless active writer-lock send_exceptions exist.
Never opens a network socket by itself.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

ENV = "OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH"
FLAG_NAME = "TG-CENTER-SENDER-BRIDGE-ATTACH.flag"


def _ops_root() -> Path:
    return Path(__file__).resolve().parents[1]


def attach_enabled(*, flag_path: Path | None = None) -> bool:
    env = str(os.environ.get(ENV, "")).strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    p = Path(flag_path) if flag_path is not None else (_ops_root() / FLAG_NAME)
    return p.is_file()


def maybe_run_after_poll(
    *,
    queue=None,
    send_fn: Callable[[dict], dict] | None = None,
    limit: int = 10,
    flag=None,
    lock=None,
    now=None,
    flag_path: Path | None = None,
) -> dict[str, Any]:
    """Call from center poll loop. Default: skip (attach off)."""
    if not attach_enabled(flag_path=flag_path):
        return {
            "ran": False,
            "skipped": True,
            "reason": "attach_default_off",
            "env": ENV,
        }
    if queue is None or send_fn is None:
        return {
            "ran": False,
            "skipped": False,
            "blocked": True,
            "reason": "missing_queue_or_send_fn",
        }
    import center_sender_bridge as csb

    bridge = csb.build_bridge(queue, send_fn)
    out = csb.run_once_if_allowed(bridge, limit=limit, flag=flag, lock=lock, now=now)
    out = dict(out)
    out["attach_enabled"] = True
    out["skipped"] = False
    return out
''', encoding="utf-8")

# Patch run_forever: after self.run_once() insert attach hook
src = center_path.read_text(encoding="utf-8", errors="replace")
needle = "        while not self.stopped():\n            self.run_once()\n"
insert = '''        while not self.stopped():
            self.run_once()
            # Arch-loop: default-OFF SenderBridge attach (env/flag). No-op unless enabled.
            try:
                import poll_sender_bridge_attach as _psba  # noqa: WPS433
                _psba.maybe_run_after_poll(
                    queue=getattr(self, "_sender_bridge_queue", None),
                    send_fn=getattr(self, "_sender_bridge_send_fn", None),
                )
            except Exception:  # noqa: BLE001 — attach must never kill poll
                pass
'''
if "poll_sender_bridge_attach" not in src:
    if needle not in src:
        raise SystemExit("run_forever needle not found")
    src = src.replace(needle, insert, 1)
    center_path.write_text(src, encoding="utf-8")
    print("CENTER_PATCHED")
else:
    print("CENTER_ALREADY_PATCHED")

test_path = OPS / "tests" / "test_poll_sender_bridge_attach_default_off.py"
test_path.write_text(r'''# -*- coding: utf-8 -*-
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
''', encoding="utf-8")

proc = subprocess.run([sys.executable, "-m", "pytest", str(test_path), "-q", "--tb=short"], cwd=str(OPS), capture_output=True, text=True)
print(proc.stdout)
print(proc.stderr)
print("RC", proc.returncode)

# verify default env not set in process / attach off against real ops flag absence for ENV
result = {
    "schema": "octopus-arch-evolution-center-bridge-attach-default-off/1",
    "stamp_local": stamp,
    "timezone": "Australia/Sydney",
    "status": "PASS" if proc.returncode == 0 else "FAIL",
    "constraints": {
        "no_live_send": True,
        "no_broad_unlock": True,
        "attach_default": "OFF",
        "no_secrets": True,
    },
    "enable": {
        "env": "OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH=1",
        "flag_file": "_ops/TG-CENTER-SENDER-BRIDGE-ATTACH.flag",
        "still_needs": "active writer-lock send_exceptions for send_allowed",
    },
    "changes": [
        {"path": str(attach_path), "action": "create"},
        {"path": str(center_path), "action": "patch_run_forever_after_run_once", "bak": str(bak)},
        {"path": str(test_path), "action": "create"},
    ],
    "pytest": {"rc": proc.returncode, "stdout_tail": (proc.stdout or "")[-1500:], "stderr_tail": (proc.stderr or "")[-1500:]},
    "compact": {
        "STATUS": "PASS" if proc.returncode == 0 else "FAIL",
        "EVIDENCE": str(EVID / "RESULT.json"),
        "NEXT": "owner may set queue/send_fn on center + env only under GO; keep attach OFF",
    },
}
(EVID / "RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("WROTE", EVID / "RESULT.json")
