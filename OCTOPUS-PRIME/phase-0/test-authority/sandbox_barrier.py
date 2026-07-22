"""sandbox_barrier.py — multi-layer defensive barrier for the OCTOPUS test authority.

Activated by importing this module (or auto via sitecustomize) BEFORE any
production module is imported. It does NOT weaken correctness — it makes the
sandbox contract enforceable and evidentiable:

  Layer B  write guard   : any write whose resolved path is under FORBIDDEN_ROOT
                           (the live vault) is refused AND recorded — even if it
                           would have failed anyway (tripwire counts ATTEMPTS).
  Layer C  subprocess    : subprocess spawning is refused by default.
  Layer D/E metrics      : attempted_live_writes / network_attempts / subprocess
                           attempts are recorded (paths only, never contents).
  network guard          : real socket connects are refused (fakes must be in-proc).

Acceptance is on ATTEMPTS, not just successes: attempted_live_writes must be 0.
"""
from __future__ import annotations

import builtins
import os
import socket
import subprocess
from pathlib import Path

FORBIDDEN_ROOT = Path(os.environ.get("BARRIER_FORBIDDEN_ROOT", r"F:\backup")).resolve()

# evidence (paths / summaries only — never file contents or secret values)
attempted_live_writes: list[str] = []
network_attempts: list[str] = []
subprocess_attempts: list[str] = []

_READ_MODES = ("r", "rb", "rt")


def _under_forbidden(path) -> bool:
    try:
        p = Path(os.fspath(path))
        p = p if p.is_absolute() else Path.cwd() / p
        rp = p.resolve()
        return rp == FORBIDDEN_ROOT or FORBIDDEN_ROOT in rp.parents
    except Exception:
        return False


class LiveWriteBlocked(RuntimeError):
    pass


class NetworkBlocked(RuntimeError):
    pass


class SubprocessBlocked(RuntimeError):
    pass


def install() -> None:
    _orig_open = builtins.open

    def _guard_open(file, mode="r", *a, **k):
        writing = any(c in mode for c in ("w", "a", "x", "+")) and not (
            mode in _READ_MODES)
        if writing and _under_forbidden(file):
            attempted_live_writes.append(f"open({os.fspath(file)}, {mode!r})")
            raise LiveWriteBlocked(f"barrier: refused write under live vault: {file}")
        return _orig_open(file, mode, *a, **k)

    builtins.open = _guard_open  # type: ignore[assignment]

    # os-level mutators
    def _wrap_os(name, argidx=0):
        orig = getattr(os, name, None)
        if orig is None:
            return

        def w(*a, **k):
            tgt = a[argidx] if len(a) > argidx else None
            if tgt is not None and _under_forbidden(tgt):
                attempted_live_writes.append(f"os.{name}({tgt})")
                raise LiveWriteBlocked(f"barrier: refused os.{name} under live vault: {tgt}")
            return orig(*a, **k)

        setattr(os, name, w)

    for nm in ("remove", "unlink", "rmdir", "mkdir", "makedirs", "rename", "replace"):
        _wrap_os(nm)

    # pathlib writers
    for meth in ("write_text", "write_bytes", "unlink", "mkdir", "rmdir"):
        orig = getattr(Path, meth, None)
        if orig is None:
            continue

        def mk(orig, meth):
            def w(self, *a, **k):
                if _under_forbidden(self):
                    attempted_live_writes.append(f"Path.{meth}({self})")
                    raise LiveWriteBlocked(f"barrier: refused Path.{meth} under live vault: {self}")
                return orig(self, *a, **k)
            return w

        setattr(Path, meth, mk(orig, meth))

    # network: refuse real connects
    _orig_conn = socket.socket.connect
    _orig_conn_ex = socket.socket.connect_ex
    _orig_create = socket.create_connection

    def _blk_connect(self, address, *a, **k):
        network_attempts.append(str(address))
        raise NetworkBlocked(f"barrier: network blocked: {address}")

    def _blk_connect_ex(self, address, *a, **k):
        network_attempts.append(str(address))
        raise NetworkBlocked(f"barrier: network blocked: {address}")

    def _blk_create(address, *a, **k):
        network_attempts.append(str(address))
        raise NetworkBlocked(f"barrier: network blocked: {address}")

    socket.socket.connect = _blk_connect  # type: ignore[assignment]
    socket.socket.connect_ex = _blk_connect_ex  # type: ignore[assignment]
    socket.create_connection = _blk_create  # type: ignore[assignment]

    # subprocess: refuse by default
    _orig_popen = subprocess.Popen

    class _BlkPopen(_orig_popen):  # type: ignore[misc]
        def __init__(self, *a, **k):
            subprocess_attempts.append(str(a[0] if a else k.get("args")))
            raise SubprocessBlocked("barrier: subprocess spawning refused in sandbox")

    subprocess.Popen = _BlkPopen  # type: ignore[assignment]

    # scrub obvious secret env vars (fakes replace them)
    for k in list(os.environ):
        if any(t in k.upper() for t in ("TOKEN", "SECRET", "API_KEY", "APIKEY",
                                        "PASSWORD", "_KEY", "POCKETSMITH")):
            os.environ[k] = "FAKE-REDACTED-FOR-TEST"


def summary() -> dict:
    return {
        "forbidden_root": str(FORBIDDEN_ROOT),
        "attempted_live_writes": len(attempted_live_writes),
        "attempted_live_writes_samples": attempted_live_writes[:20],
        "network_attempts": len(network_attempts),
        "network_attempts_samples": network_attempts[:20],
        "subprocess_attempts": len(subprocess_attempts),
    }
