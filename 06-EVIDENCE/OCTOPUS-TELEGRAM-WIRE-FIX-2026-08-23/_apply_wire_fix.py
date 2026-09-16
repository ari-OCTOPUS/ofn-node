from pathlib import Path
import json, time, shutil, subprocess, sys

ROOT = Path(r"F:/backup")
OPS = ROOT / "_ops"
EVID = ROOT / "06-EVIDENCE" / "OCTOPUS-TELEGRAM-WIRE-FIX-2026-08-23"
EVID.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y-%m-%dT%H:%M:%S+10:00")

organ_path = OPS / "loops" / "telegram_organ.py"
bak = Path(str(organ_path) + ".bak-tg-wire-20260823")
if not bak.exists():
    shutil.copy2(organ_path, bak)

gate_path = OPS / "telegram_center" / "live_telegram_gate.py"
bridge_attach_path = OPS / "telegram_center" / "center_sender_bridge.py"
test_path = OPS / "tests" / "test_live_telegram_wire_20260823.py"

gate_path.write_text(r'''#!/usr/bin/env python3
"""Canonical LIVE-TELEGRAM.flag + writer-lock send gate.

Unlock (flag enabled) != send. Send only when an active send_exception
exists on the writer lock while respecting forbidden live sendMessage.
Reversible: delete this module / stop importing it.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

LIVE_FLAG_NAME = "LIVE-TELEGRAM.flag"
DEFAULT_LOCK = Path(__file__).resolve().parents[1] / "state" / "locks" / "octopus-writer.lock"


def ops_root() -> Path:
    return Path(__file__).resolve().parents[1]


def flag_path() -> Path:
    env = str(os.environ.get("OCTOPUS_LIVE_TELEGRAM_FLAG", "")).strip()
    if env:
        return Path(env)
    return ops_root() / LIVE_FLAG_NAME


def read_flag(path: Path | None = None) -> dict[str, Any]:
    p = Path(path) if path is not None else flag_path()
    if not p.is_file():
        return {"present": False, "enabled": False, "path": str(p), "raw_schema": None, "note": "missing"}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"present": True, "enabled": True, "path": str(p), "raw_schema": None, "note": "present_non_json_treated_as_enabled"}
    if not isinstance(raw, dict):
        return {"present": True, "enabled": True, "path": str(p), "raw_schema": None, "note": "present_non_object_treated_as_enabled"}
    enabled = bool(raw.get("enabled", True))
    return {"present": True, "enabled": enabled, "path": str(p), "raw_schema": raw.get("schema"), "note": raw.get("note"), "armed_at": raw.get("armed_at")}


def _read_lock(path: Path | None = None) -> dict[str, Any]:
    p = Path(path) if path is not None else Path(str(os.environ.get("OCTOPUS_WRITER_LOCK", "")).strip() or DEFAULT_LOCK)
    if not p.is_file():
        return {"present": False, "path": str(p), "data": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"present": True, "path": str(p), "data": {}, "corrupt": True}
    return {"present": True, "path": str(p), "data": data if isinstance(data, dict) else {}}


def _active_send_exceptions(lock_data: dict[str, Any], *, now: float | None = None) -> list[dict]:
    now = time.time() if now is None else float(now)
    ex = lock_data.get("send_exceptions") or []
    if not isinstance(ex, list):
        return []
    active = []
    for row in ex:
        if not isinstance(row, dict):
            continue
        exp = row.get("expires_at")
        if exp is not None:
            try:
                if float(exp) < now:
                    continue
            except (TypeError, ValueError):
                continue
        active.append(row)
    return active


def evaluate(*, flag: Path | None = None, lock: Path | None = None, now: float | None = None) -> dict[str, Any]:
    f = read_flag(flag)
    lk = _read_lock(lock)
    data = lk.get("data") or {}
    forbidden = list(data.get("forbidden_actions") or [])
    live_send_forbidden = "live sendMessage" in forbidden
    exceptions = _active_send_exceptions(data, now=now)
    live_mode_allowed = bool(f.get("enabled"))
    send_allowed = bool(live_mode_allowed and exceptions)
    return {
        "schema": "live-telegram-gate/1",
        "flag": f,
        "lock_path": lk.get("path"),
        "lock_present": bool(lk.get("present")),
        "live_sendMessage_forbidden": live_send_forbidden,
        "active_send_exceptions": len(exceptions),
        "live_mode_allowed": live_mode_allowed,
        "send_allowed": send_allowed,
        "reason": (
            "send_allowed_via_exception" if send_allowed else (
                "flag_disabled_or_missing" if not live_mode_allowed else "no_active_send_exception"
            )
        ),
    }


def live_mode_allowed(**kwargs) -> bool:
    return bool(evaluate(**kwargs).get("live_mode_allowed"))


def send_allowed(**kwargs) -> bool:
    return bool(evaluate(**kwargs).get("send_allowed"))
''', encoding='utf-8')

bridge_attach_path.write_text(r'''#!/usr/bin/env python3
"""Optional center-facing SenderBridge attach (default-off).

Center may import this module. It does NOT auto-send. Callers must inject
queue + send_fn. run_once is refused unless live_telegram_gate.send_allowed().
"""
from __future__ import annotations

from typing import Any, Callable

from sender_bridge import SenderBridge
import live_telegram_gate as gate


def build_bridge(queue, send_fn: Callable[[dict], dict], **kwargs) -> SenderBridge:
    return SenderBridge(queue, send_fn, **kwargs)


def run_once_if_allowed(bridge: SenderBridge, *, limit: int = 10, flag=None, lock=None, now=None) -> dict[str, Any]:
    status = gate.evaluate(flag=flag, lock=lock, now=now)
    if not status.get("send_allowed"):
        return {"ran": False, "blocked": True, "gate": status, "sent": 0, "deferred": 0, "dlq": 0, "rate_blocked": 0, "due": 0}
    counts = dict(bridge.run_once(limit=limit))
    counts["ran"] = True
    counts["blocked"] = False
    counts["gate"] = status
    return counts
''', encoding='utf-8')

organ = organ_path.read_text(encoding='utf-8')
if 'def _flag_enabled' not in organ:
    old = 'LIVE_FLAG_NAME = "LIVE-TELEGRAM.flag"\nDEFAULT_RATE_S = 3600.0\nMAX_LOOPS_IN_DIGEST = 3\n'
    new = '''LIVE_FLAG_NAME = "LIVE-TELEGRAM.flag"
DEFAULT_RATE_S = 3600.0
MAX_LOOPS_IN_DIGEST = 3


def _canonical_live_flag_path() -> Path:
    """Prefer _ops/LIVE-TELEGRAM.flag (SoT unlock token), not state_dir."""
    try:
        return Path(__file__).resolve().parents[1] / LIVE_FLAG_NAME
    except Exception:  # noqa: BLE001
        return Path(LIVE_FLAG_NAME)


def _flag_enabled(state_dir: Path) -> bool:
    """True when canonical ops flag enabled, else legacy state_dir flag file."""
    try:
        import sys as _sys
        _tc = str(Path(__file__).resolve().parents[1] / "telegram_center")
        if _tc not in _sys.path:
            _sys.path.insert(0, _tc)
        import live_telegram_gate as _gate  # type: ignore
        return bool(_gate.live_mode_allowed())
    except Exception:
        pass
    if (Path(state_dir) / LIVE_FLAG_NAME).is_file():
        return True
    canon = _canonical_live_flag_path()
    if canon.is_file():
        try:
            raw = json.loads(canon.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return bool(raw.get("enabled", True))
        except (OSError, ValueError):
            return True
    return False
'''
    if old not in organ:
        raise SystemExit('organ anchor missing')
    organ = organ.replace(old, new, 1)
    organ = organ.replace(
        'self.live = bool(live) and (self.state_dir / LIVE_FLAG_NAME).is_file()',
        'self.live = bool(live) and _flag_enabled(self.state_dir)',
        1,
    )
    organ_path.write_text(organ, encoding='utf-8')

center_path = OPS / 'telegram_center' / 'center.py'
center_bak = Path(str(center_path) + '.bak-tg-wire-20260823')
if not center_bak.exists():
    shutil.copy2(center_path, center_bak)
center = center_path.read_text(encoding='utf-8', errors='replace')
if 'def owner_gated_sender_bridge_run_once(' not in center:
    hook = '''

def owner_gated_sender_bridge_run_once(queue, send_fn, *, limit: int = 10, **kwargs):
    """Optional SenderBridge drain — refused unless LIVE-TELEGRAM gate send_allowed.

    Default-off path for C03: center can import/call this without auto-wiring
    the poll loop. No network unless caller-injected send_fn does I/O AND gate allows.
    """
    try:
        import center_sender_bridge as _csb
    except Exception as exc:  # noqa: BLE001
        return {"ran": False, "blocked": True, "error": type(exc).__name__}
    bridge = _csb.build_bridge(queue, send_fn)
    return _csb.run_once_if_allowed(bridge, limit=limit, **kwargs)
'''
    center_path.write_text(center.rstrip() + '\n' + hook + '\n', encoding='utf-8')

test_path.write_text(r'''# -*- coding: utf-8 -*-
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
''', encoding='utf-8')

proc = subprocess.run([sys.executable, '-m', 'pytest', str(test_path), '-q', '--tb=short'], cwd=str(OPS), capture_output=True, text=True)
print(proc.stdout)
print(proc.stderr)
print('RC', proc.returncode)

result = {
    'schema': 'octopus-telegram-wire-fix/1',
    'stamp_local': stamp,
    'timezone': 'Australia/Sydney',
    'status': 'PASS' if proc.returncode == 0 else 'FAIL',
    'constraints': {'no_live_sendMessage': True, 'no_broad_unlock': True, 'no_secrets': True, 'no_invent': True, 'reversible': True},
    'addresses': ['C02', 'C03', 'C05-partial'],
    'changes': [
        {'path': str(gate_path), 'action': 'create'},
        {'path': str(bridge_attach_path), 'action': 'create'},
        {'path': str(organ_path), 'action': 'patch', 'bak': str(bak)},
        {'path': str(center_path), 'action': 'append_helper', 'bak': str(center_bak)},
        {'path': str(test_path), 'action': 'create'},
    ],
    'behavior': {
        'live_mode_allowed': 'LIVE-TELEGRAM.flag enabled=true (canonical _ops path / OCTOPUS_LIVE_TELEGRAM_FLAG)',
        'send_allowed': 'live_mode_allowed AND active writer-lock send_exceptions only',
        'TelegramOrgan.live': 'caller live=True AND flag enabled; live=False stays dry_run',
        'SenderBridge': 'center.owner_gated_sender_bridge_run_once default-off; refused without exception',
        'C05': 'canary sqlite remains non-SoT; durable loop/outbox remains organism SoT — no merge',
    },
    'pytest': {'rc': proc.returncode, 'stdout_tail': (proc.stdout or '')[-2000:], 'stderr_tail': (proc.stderr or '')[-2000:]},
    'miniapp_docs': {
        'status': 'PASS_PRIOR',
        'evidence': 'F:/backup/06-EVIDENCE/OCTOPUS-MINIAPP-DOC-RECONCILE-2026-08-23/RESULT.json',
        'true_url_state': 'LIVE localhost 127.0.0.1:8774 PID 12220; public URL NOT_PUBLISHED',
    },
    'compact': {
        'STATUS': 'PASS' if proc.returncode == 0 else 'FAIL',
        'EVIDENCE': str(EVID / 'RESULT.json'),
        'NEXT': 'optional: wire poll-loop to owner_gated_sender_bridge_run_once still default-off',
    },
}
(EVID / 'RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('WROTE', EVID / 'RESULT.json')
