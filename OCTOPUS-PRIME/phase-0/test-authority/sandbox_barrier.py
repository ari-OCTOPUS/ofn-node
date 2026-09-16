"""sandbox_barrier.py — multi-layer defensive barrier for the OCTOPUS test authority.

Activated via sitecustomize (run_sandbox_suite.py writes one that calls install())
BEFORE any production module is imported. It is a BACKSTOP: the primary isolation
is path redirection (REAL_VAULT=candidate, ORG_ROOT/OPS_DIR/...=sandbox) so no
live path is constructed in the first place; this barrier refuses+records any
write that nonetheless resolves under the LIVE vault.

Hardened per adversarial review (F-F): covers builtins.open + io.open, low-level
os.open (write flags), os move/link ops checking BOTH src AND dst, Path.open/
touch/write*/rename/replace, shutil copy/move/rmtree (dst), sqlite3.connect
(writable), network connects, and subprocess. Acceptance is on ATTEMPTS
(attempted_live_writes must be 0 in a real suite run — distinct from self-test
probes which deliberately attempt).
"""
from __future__ import annotations

import builtins
import io
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

FORBIDDEN_ROOT = Path(os.environ.get("BARRIER_FORBIDDEN_ROOT", r"F:\backup")).resolve()

attempted_live_writes: list[str] = []
network_attempts: list[str] = []          # EXTERNAL (blocked) only
localhost_connections: list[str] = []     # allowed loopback (in-process test servers)
subprocess_attempts: list[str] = []
_installed = False


def _under_forbidden(path) -> bool:
    try:
        if not isinstance(path, (str, bytes, os.PathLike, Path)):
            return False
        p = Path(os.fsdecode(path) if isinstance(path, bytes) else os.fspath(path))
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


def _refuse(api: str, tgt) -> None:
    attempted_live_writes.append(f"{api}({tgt})")
    raise LiveWriteBlocked(f"barrier: refused {api} under live vault: {tgt}")


def install() -> None:
    global _installed
    if _installed:
        return
    _installed = True

    _WRITE = ("w", "a", "x", "+")

    # ---- builtins.open + io.open ----
    _orig_open = builtins.open

    def _guard_open(file, mode="r", *a, **k):
        if any(c in str(mode) for c in _WRITE) and _under_forbidden(file):
            _refuse("open", file)
        return _orig_open(file, mode, *a, **k)

    builtins.open = _guard_open       # type: ignore[assignment]
    io.open = _guard_open             # type: ignore[assignment]

    # ---- os path mutators: check EVERY positional path arg (dst included) ----
    def _wrap_os(name, nargs):
        orig = getattr(os, name, None)
        if orig is None:
            return

        def w(*a, **k):
            for tgt in a[:nargs]:
                if _under_forbidden(tgt):
                    _refuse(f"os.{name}", tgt)
            return orig(*a, **k)

        setattr(os, name, w)

    for nm in ("remove", "unlink", "rmdir", "mkdir", "makedirs"):
        _wrap_os(nm, 1)
    for nm in ("rename", "replace", "link", "symlink"):      # src AND dst
        _wrap_os(nm, 2)

    # ---- low-level os.open with write/create flags ----
    _orig_osopen = os.open

    def _guard_osopen(path, flags, *a, **k):
        wflags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
        if (flags & wflags) and _under_forbidden(path):
            _refuse("os.open", path)
        return _orig_osopen(path, flags, *a, **k)

    os.open = _guard_osopen           # type: ignore[assignment]

    # ---- pathlib writers ----
    def _wrap_path(meth, write_modes=False):
        orig = getattr(Path, meth, None)
        if orig is None:
            return

        def w(self, *a, **k):
            if write_modes:
                mode = a[0] if a else k.get("mode", "r")
                if not any(c in str(mode) for c in _WRITE):
                    return orig(self, *a, **k)
            if _under_forbidden(self):
                _refuse(f"Path.{meth}", self)
            return orig(self, *a, **k)

        setattr(Path, meth, w)

    for m in ("write_text", "write_bytes", "unlink", "mkdir", "rmdir", "touch"):
        _wrap_path(m)
    _wrap_path("open", write_modes=True)
    # Path.rename/replace destination
    for m in ("rename", "replace"):
        orig = getattr(Path, m, None)
        if orig:
            def mk(orig, m):
                def w(self, target, *a, **k):
                    if _under_forbidden(self) or _under_forbidden(target):
                        _refuse(f"Path.{m}", target)
                    return orig(self, target, *a, **k)
                return w
            setattr(Path, m, mk(orig, m))

    # ---- shutil (destination is arg[1]; rmtree target is arg[0]) ----
    def _wrap_shutil(name, dst_is_second):
        orig = getattr(shutil, name, None)
        if orig is None:
            return

        def w(*a, **k):
            idxs = (0, 1) if dst_is_second else (0,)
            for i in idxs:
                if len(a) > i and _under_forbidden(a[i]):
                    _refuse(f"shutil.{name}", a[i])
            return orig(*a, **k)

        setattr(shutil, name, w)

    for nm in ("copyfile", "copy", "copy2", "copytree", "move"):
        _wrap_shutil(nm, True)
    _wrap_shutil("rmtree", False)

    # ---- sqlite3.connect to a writable live db ----
    _orig_connect = sqlite3.connect

    def _guard_connect(database, *a, **k):
        if str(database) != ":memory:" and _under_forbidden(database):
            _refuse("sqlite3.connect", database)
        return _orig_connect(database, *a, **k)

    sqlite3.connect = _guard_connect  # type: ignore[assignment]

    # ---- network: block EXTERNAL; allow loopback (in-process test servers)
    #      except paid/model ports (LiteLLM 4000, Ollama 11434) ----
    _LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}
    # Only PAID gateways are denied on loopback. LiteLLM (4000) fronts paid
    # providers → deny. Ollama (11434) is free+local → it is loopback, NOT
    # external and NOT paid; allow it (runner points OLLAMA_BASE_URL at a dead
    # port for determinism so no real local inference runs in the suite).
    _PAID_PORTS = {4000}

    def _net_ok(address) -> bool:
        try:
            return str(address[0]) in _LOOPBACK and int(address[1]) not in _PAID_PORTS
        except Exception:
            return False

    def _net_guard(orig, addr_idx):
        def w(*a, **k):
            address = a[addr_idx] if len(a) > addr_idx else None
            if _net_ok(address):
                localhost_connections.append(str(address))
                return orig(*a, **k)
            network_attempts.append(str(address))
            raise NetworkBlocked(f"barrier: external network blocked: {address}")
        return w

    socket.socket.connect = _net_guard(socket.socket.connect, 1)        # type: ignore[assignment]
    socket.socket.connect_ex = _net_guard(socket.socket.connect_ex, 1)  # type: ignore[assignment]
    socket.create_connection = _net_guard(socket.create_connection, 0)  # type: ignore[assignment]

    # ---- subprocess: allow python (sandbox-bound; child inherits this barrier via
    #      PYTHONPATH sitecustomize); block cmd/.bat/.ps1/powershell launchers ----
    _orig_popen = subprocess.Popen
    _py = os.path.basename(sys.executable).lower()

    class _GuardPopen(_orig_popen):  # type: ignore[misc]
        def __init__(self, args, *a, **k):
            try:
                exe = str(args[0] if isinstance(args, (list, tuple)) else args).lower()
            except Exception:
                exe = ""
            subprocess_attempts.append(str(args)[:200])
            dangerous = any(x in exe for x in ("cmd", ".bat", ".ps1", "powershell", "startfile"))
            is_python = (_py in exe) or exe.endswith("python") or "python" in exe
            if dangerous or not is_python:
                raise SubprocessBlocked(f"barrier: non-python subprocess refused: {exe[:80]}")
            super().__init__(args, *a, **k)

    subprocess.Popen = _GuardPopen   # type: ignore[assignment]

    # ---- scrub secret-looking env (fakes replace) ----
    for kk in list(os.environ):
        if any(t in kk.upper() for t in ("TOKEN", "SECRET", "API_KEY", "APIKEY",
                                         "PASSWORD", "POCKETSMITH")) and "WIRE" not in kk.upper():
            os.environ[kk] = "FAKE-REDACTED-FOR-TEST"


def summary() -> dict:
    return {
        "forbidden_root": str(FORBIDDEN_ROOT),
        "attempted_live_writes": len(attempted_live_writes),
        "attempted_live_writes_samples": attempted_live_writes[:20],
        "network_attempts": len(network_attempts),
        "network_attempts_samples": network_attempts[:20],
        "localhost_connections": len(localhost_connections),
        "subprocess_attempts": len(subprocess_attempts),
    }
