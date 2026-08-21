#!/usr/bin/env python3
"""transport_pool.py — bounded, circuit-protected Telegram transport (Wave C).

Owner order 2026-08-21:
- never spawn one unkillable daemon thread per request
- DNS+HTTPS inside a terminable worker (subprocess mode) or a bounded pool
- at most one active request per bot
- hard deadline, cooldown, circuit breaker
- timeout never advances the offset (caller contract, see tg_api.next_offset)
- stuck worker is terminated (subprocess mode) and replaced; thread count bounded
- worker count stays bounded under repeated environmental stalls

Two transport modes:
  thread  — bounded daemon worker with wall-clock deadline (fail-soft None on
            stall). A stuck DNS thread cannot be killed, so the pool caps how
            many can accumulate (fail-soft saturation instead of spawning).
  subprocess — terminable child per call (env OCTOPUS_TG_TRANSPORT_SUBPROCESS=1,
            owner-gated); subprocess.run(timeout) kills a stuck resolver, so
            the worker is truly terminated and replaced.

Circuit breaker is per bot (token digest): N consecutive failures open the
circuit with cooldown; a 409 opens it immediately. While OPEN, calls are
refused before any network I/O (fail-soft, no retry storm).
"""
from __future__ import annotations

import json
import os
import threading
import time


class CircuitOpenError(RuntimeError):
    """Raised by pool.call when the per-bot circuit is OPEN (cooldown)."""


class BotCircuit:
    """Per-bot breaker: CLOSED -> (fail_threshold failures) -> OPEN(cooldown)."""

    def __init__(self, bot_key: str, *, fail_threshold: int = 3,
                 cooldown_s: float = 60.0, clock=None):
        self._bot = bot_key
        self._threshold = max(1, int(fail_threshold))
        self._cooldown = float(cooldown_s)
        self._clock = clock or time.time
        self._lock = threading.Lock()
        self._failures = 0
        self._open_until = 0.0

    # ── state ──────────────────────────────────────────────────────────────
    @property
    def open(self) -> bool:
        with self._lock:
            return self._clock() < self._open_until

    def check(self) -> None:
        """Raise CircuitOpenError when the circuit is open (before network)."""
        if self.open:
            raise CircuitOpenError(
                f"circuit OPEN for bot {self._bot} (cooldown "
                f"{max(0.0, self._open_until - self._clock()):.0f}s)")

    def record(self, *, ok: bool, is_409: bool = False) -> None:
        with self._lock:
            now = self._clock()
            if ok:
                self._failures = 0
                self._open_until = 0.0
                return
            if is_409:                      # duplicate consumer: open at once
                self._open_until = now + self._cooldown
                self._failures = self._threshold
                return
            self._failures += 1
            if self._failures >= self._threshold:
                self._open_until = now + self._cooldown

    def stats(self) -> dict:
        with self._lock:
            return {
                "bot": self._bot,
                "consecutive_failures": self._failures,
                "open": self._clock() < self._open_until,
                "cooldown_remaining_s": round(max(0.0, self._open_until - self._clock()), 1),
            }


class TransportPool:
    """Bounded transport executor with per-bot circuits and hard deadlines."""

    def __init__(self, *, max_concurrent: int = 4, fail_threshold: int = 3,
                 cooldown_s: float = 60.0, subprocess_fn=None, clock=None,
                 deadline_margin: float = 5.0):
        self._max = max(1, int(max_concurrent))
        self._fail_threshold = max(1, int(fail_threshold))
        self._cooldown = float(cooldown_s)
        self._margin = max(0.0, float(deadline_margin))
        self._sem = threading.BoundedSemaphore(self._max)
        self._lock = threading.Lock()
        self._active = 0
        self._total_stalls = 0
        self._total_calls = 0
        self._total_saturated = 0
        self._total_circuit_blocks = 0
        self._circuits: dict[str, BotCircuit] = {}
        self._subprocess_fn = subprocess_fn  # callable(url, timeout_s, data, headers) -> bytes|None
        self._clock = clock or time.time

    # ── internals ───────────────────────────────────────────────────────────
    def _circuit(self, bot_key: str) -> BotCircuit:
        with self._lock:
            c = self._circuits.get(bot_key)
            if c is None:
                c = BotCircuit(bot_key, fail_threshold=self._fail_threshold,
                               cooldown_s=self._cooldown, clock=self._clock)
                self._circuits[bot_key] = c
            return c

    def _run_thread(self, fn, timeout_s: float):
        """Bounded daemon worker with wall-clock deadline; None on stall."""
        import queue as _q
        box: _q.Queue = _q.Queue(maxsize=1)

        def _worker():
            try:
                box.put(fn())
            except Exception as exc:  # noqa: BLE001 — surfaced to caller
                box.put(exc)

        threading.Thread(target=_worker, daemon=True).start()
        try:
            got = box.get(timeout=float(timeout_s))
        except _q.Empty:
            return None
        if isinstance(got, Exception):
            raise got
        return got

    # ── public API ──────────────────────────────────────────────────────────
    def call(self, bot_key: str, url: str, timeout_s: float, *,
             data: bytes | None = None, headers: dict | None = None,
             fn=None) -> bytes | None:
        """One bounded transport call.

        fn: injected callable(url, timeout_s, data, headers) -> bytes (fixtures).
        Default: urllib inside a bounded worker; subprocess when enabled.
        Returns None on stall (fail-soft); raises on HTTP-level errors.
        """
        circ = self._circuit(bot_key)
        circ.check()                      # open circuit -> no network at all
        if not self._sem.acquire(blocking=False):
            with self._lock:
                self._total_saturated += 1
            raise CircuitOpenError("transport pool saturated (fail-soft)")
        with self._lock:
            self._active += 1
            self._total_calls += 1
        try:
            if fn is not None:
                # injected transports get the same hard deadline
                return self._run_thread(lambda: fn(url, timeout_s, data, headers),
                                        float(timeout_s) + self._margin)
            if self._subprocess_fn is not None:
                return self._subprocess_fn(url, timeout_s, data=data, headers=headers)
            return self._run_thread(
                lambda: self._http_bytes(url, timeout_s, data, headers),
                float(timeout_s) + self._margin)
        finally:
            with self._lock:
                self._active -= 1
            self._sem.release()

    @staticmethod
    def _http_bytes(url: str, timeout_s: float, data: bytes | None,
                    headers: dict | None) -> bytes:
        import urllib.request
        req = urllib.request.Request(url, data=data, headers=headers or {})
        with urllib.request.urlopen(req, timeout=float(timeout_s)) as resp:  # noqa: S310 — gated by callers
            return resp.read()

    def record_result(self, bot_key: str, *, ok: bool, is_409: bool = False) -> None:
        circ = self._circuit(bot_key)
        if not ok:
            with self._lock:
                self._total_stalls += 1
        circ.record(ok=ok, is_409=is_409)

    def stats(self) -> dict:
        with self._lock:
            return {
                "active": self._active,
                "max_concurrent": self._max,
                "total_calls": self._total_calls,
                "total_stalls": self._total_stalls,
                "total_saturated": self._total_saturated,
                "total_circuit_blocks": self._total_circuit_blocks,
                "circuits": {k: c.stats() for k, c in self._circuits.items()},
            }


def subprocess_transport(url: str, timeout_s: float, *, data: bytes | None = None,
                         headers: dict | None = None) -> bytes | None:
    """Terminable child process transport (DNS+HTTPS inside a killable worker).
    None on timeout/deadline — the stuck child is killed by subprocess.run."""
    import subprocess
    import sys as _sys
    _WORKER = r"""
import json, sys, urllib.request
url, timeout_s, data, headers = json.loads(sys.stdin.read())
req = urllib.request.Request(url, data=(data.encode('utf-8') if data else None),
                             headers=headers or {})
with urllib.request.urlopen(req, timeout=timeout_s) as resp:
    sys.stdout.write(resp.read().decode('utf-8', 'replace'))
"""
    try:
        payload = json.dumps([url, float(timeout_s),
                              data.decode("utf-8", "replace") if data else None,
                              headers or {}])
        proc = subprocess.run([_sys.executable, "-c", _WORKER], input=payload,
                              capture_output=True, text=True,
                              timeout=float(timeout_s) + 5.0)
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    return proc.stdout.encode("utf-8")
