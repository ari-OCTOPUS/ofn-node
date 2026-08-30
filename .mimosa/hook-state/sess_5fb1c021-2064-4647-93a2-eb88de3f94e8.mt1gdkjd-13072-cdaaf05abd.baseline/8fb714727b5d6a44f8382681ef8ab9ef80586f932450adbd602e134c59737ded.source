#!/usr/bin/env python3
"""test_blocker_fixes_2026_07_22.py — the 3 LEAD-SAFETY BLOCKERs (owner-review branch).

Covers, hermetically (all opslib path constants monkeypatched to a tmp dir —
NO live file is touched; fakes stand in for the ledger/gate/guard):

  * BLOCKER-1 (§3.8): human-append guard is now fail-CLOSED — a guard EXCEPTION
    downgrades is_human to False (was: left True = fail-open). Flag-off is
    unchanged. `chrono.on_human_judgment`.
  * BLOCKER-2 (§3.7b): an approval that names a specific effect_id releases ONLY
    that effect via the id-bound `release_one` (was: every money-kind pending
    batch-released on one append). Approval without an effect_id still uses the
    batch allowlist — a documented residual whose full close is the proposal_id
    column (TH-K-3).
  * BLOCKER-3 (split-brain STOP): `watchdog.STOP_FLAGS` now points at the
    canonical `opslib.STOP_ARCHITECT` ("04 - Architect System/STOP"), not the
    dead repo-root `STOP`.

Run: python -X utf8 test_blocker_fixes_2026_07_22.py   (or via pytest)
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
import types

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "budget", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib  # noqa: E402


def _isolate(d: pathlib.Path) -> None:
    """Redirect every STOP/HALT flag to tmp — no live file is touched."""
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "04 - Architect System" / "STOP"
    opslib.STOP_ORGANISM = d / "STOP-ORGANISM"


_SANDBOX = pathlib.Path(tempfile.mkdtemp(prefix="blocker-fixes-"))
_isolate(_SANDBOX)

# import AFTER isolation so watchdog.STOP_FLAGS captures the tmp STOP_ARCHITECT
import chrono     # noqa: E402
import watchdog   # noqa: E402


class _FakeLedger:
    def __init__(self):
        self.last = {}

    def append(self, event_type, judgment, actor, is_human):
        self.last = {"actor": actor, "is_human": is_human, "hash": "H"}
        return self.last


class _FakeGate:
    def __init__(self):
        self.calls = []

    def release_one(self, effect_id, entry):
        self.calls.append(("one", effect_id))
        return True

    def release_gated_effects(self, entry):
        self.calls.append(("batch", None))
        return 0


# ─── BLOCKER 1 ────────────────────────────────────────────────────────────────
def test_blocker1_guard_exception_is_fail_closed(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", "1")
    fake_guard = types.ModuleType("human_append_guard")

    class _G:
        def authorize(self, *a, **k):
            raise RuntimeError("guard blew up")

    fake_guard.default_guard = lambda: _G()
    monkeypatch.setitem(sys.modules, "human_append_guard", fake_guard)
    monkeypatch.setattr(chrono.opslib, "alert", lambda *a, **k: None)

    lg = _FakeLedger()
    chrono.on_human_judgment({"effect_id": "e1"}, gate=None, ledger=lg)
    assert lg.last["is_human"] is False   # fail-closed, not fail-open
    assert lg.last["actor"] == "system"


def test_blocker1_flag_off_is_unchanged(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", "0")
    lg = _FakeLedger()
    chrono.on_human_judgment({"x": 1}, gate=None, ledger=lg)
    assert lg.last["is_human"] is True    # guard disabled → prior behavior


# ─── BLOCKER 2 ────────────────────────────────────────────────────────────────
def test_blocker2_named_effect_is_id_bound(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", "0")
    gate = _FakeGate()
    chrono.on_human_judgment({"effect_id": "E42"}, gate=gate, ledger=_FakeLedger())
    assert gate.calls == [("one", "E42")]   # only that effect, via release_one


def test_blocker2_no_effect_id_uses_batch(monkeypatch):
    monkeypatch.setenv("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", "0")
    gate = _FakeGate()
    chrono.on_human_judgment({"note": "generic"}, gate=gate, ledger=_FakeLedger())
    assert gate.calls == [("batch", None)]  # documented residual (see TH-K-3)


# ─── BLOCKER 1 (full path): authorized==False ⇒ released==0 ⇒ settled==0 ──────
def _install_fake_guard(mp, *, raises=False, allow=True, reason="ok"):
    fake = types.ModuleType("human_append_guard")

    class _G:
        def authorize(self, *a, **k):
            if raises:
                raise RuntimeError("guard blew up")
            return (allow, reason)

    fake.default_guard = lambda: _G()
    mp.setitem(sys.modules, "human_append_guard", fake)
    mp.setenv("OCTOPUS_WIRE_HUMAN_APPEND_GUARD", "1")
    mp.setattr(chrono.opslib, "alert", lambda *a, **k: None)


def test_b_guard_exception_releases_zero(monkeypatch):
    _install_fake_guard(monkeypatch, raises=True)
    gate = _FakeGate()
    chrono.on_human_judgment({"effect_id": "e1"}, gate=gate, ledger=_FakeLedger())
    assert gate.calls == []   # invariant: unauthorized ⇒ zero release


def test_b_guard_denies_releases_zero(monkeypatch):
    # wrong-token / expired / replay / wrong-approval-id / wrong-content-hash
    # all surface as authorize()->(False, reason); every one must release nothing.
    for reason in ("wrong-token", "expired-token", "replay-token",
                   "approval-id-mismatch", "content-hash-mismatch"):
        mp = monkeypatch
        _install_fake_guard(mp, allow=False, reason=reason)
        gate = _FakeGate()
        lg = _FakeLedger()
        chrono.on_human_judgment({"effect_id": "e1"}, gate=gate, ledger=lg)
        assert gate.calls == [], f"released on deny reason={reason}"
        assert lg.last["is_human"] is False and lg.last["actor"] == "system"


def test_b_authorized_releases_only_named_effect(monkeypatch):
    _install_fake_guard(monkeypatch, allow=True, reason="ok")
    gate = _FakeGate()
    chrono.on_human_judgment({"effect_id": "E7"}, gate=gate, ledger=_FakeLedger())
    assert gate.calls == [("one", "E7")]   # authorized ⇒ only the named effect


def test_b_alert_failure_never_fail_open(monkeypatch):
    _install_fake_guard(monkeypatch, allow=False, reason="wrong-token")
    monkeypatch.setattr(chrono.opslib, "alert",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("alert down")))
    gate = _FakeGate()
    try:
        chrono.on_human_judgment({"effect_id": "e1"}, gate=gate, ledger=_FakeLedger())
    except Exception:
        pass   # a crash is fail-CLOSED; what matters is no effect was released
    assert gate.calls == []


# ─── BLOCKER 3 ────────────────────────────────────────────────────────────────
def test_blocker3_watchdog_uses_canonical_architect_stop():
    assert opslib.STOP_ARCHITECT in watchdog.STOP_FLAGS
    assert opslib.STOP_ARCHITECT.parent.name == "04 - Architect System"
    dead_root = watchdog._HERE.parent / "STOP"
    assert dead_root not in watchdog.STOP_FLAGS


def test_blocker3_should_revive_yields_on_architect_stop(tmp_path):
    stop = tmp_path / "STOP"
    stop.write_text("stop")
    should, reason = watchdog.should_revive(
        port_alive=False, stop_flags=[stop], state_exists=True)
    assert should is False
    assert "STOP" in reason


if __name__ == "__main__":  # runnable without pytest (their convention)
    import traceback

    class _MP:  # minimal monkeypatch shim for script mode
        def __init__(self): self._undo = []
        def setenv(self, k, v):
            import os
            self._undo.append(("env", k, os.environ.get(k)))
            os.environ[k] = v
        def setitem(self, d, k, v):
            self._undo.append(("item", d, k, d.get(k)))
            d[k] = v
        def setattr(self, obj, name, v):
            self._undo.append(("attr", obj, name, getattr(obj, name)))
            setattr(obj, name, v)
        def undo(self):
            import os
            for u in reversed(self._undo):
                if u[0] == "env":
                    if u[2] is None: os.environ.pop(u[1], None)
                    else: os.environ[u[1]] = u[2]
                elif u[0] == "item": u[1][u[2]] = u[3]
                elif u[0] == "attr": setattr(u[1], u[2], u[3])
            self._undo.clear()

    tests = [
        (test_blocker1_guard_exception_is_fail_closed, True),
        (test_blocker1_flag_off_is_unchanged, True),
        (test_blocker2_named_effect_is_id_bound, True),
        (test_blocker2_no_effect_id_uses_batch, True),
        (test_b_guard_exception_releases_zero, True),
        (test_b_guard_denies_releases_zero, True),
        (test_b_authorized_releases_only_named_effect, True),
        (test_b_alert_failure_never_fail_open, True),
        (test_blocker3_watchdog_uses_canonical_architect_stop, False),
        (test_blocker3_should_revive_yields_on_architect_stop, "tmp"),
    ]
    ok = 0
    for fn, arg in tests:
        mp = _MP()
        try:
            if arg is True:
                fn(mp)
            elif arg == "tmp":
                fn(pathlib.Path(tempfile.mkdtemp(prefix="wt-")))
            else:
                fn()
            print(f"[PASS] {fn.__name__}")
            ok += 1
        except Exception:
            print(f"[FAIL] {fn.__name__}")
            traceback.print_exc()
        finally:
            mp.undo()
    print(f"\n=== {ok}/{len(tests)} passed ===")
    sys.exit(0 if ok == len(tests) else 1)
