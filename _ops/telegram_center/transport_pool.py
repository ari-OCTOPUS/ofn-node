#!/usr/bin/env python3
"""Bounded, circuit-protected Telegram transport.

Thread mode cannot kill a stuck resolver, so each worker owns its semaphore slot
until the thread actually exits.  A timed-out caller returns promptly, but no
replacement worker is spawned after the pool reaches its fixed bound.
Subprocess mode runs DNS+HTTP in a child that is killed by ``subprocess.run`` at
the hard deadline.  Circuits are isolated by one-way bot key; a 409 opens the
matching circuit immediately.
"""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import threading
import time
import urllib.error


class CircuitOpenError(RuntimeError):
    """The bot circuit is open or the bounded executor is saturated."""


class BotCircuit:
    def __init__(self, bot_key: str, *, fail_threshold: int = 3,
                 cooldown_s: float = 60.0, clock=None):
        self._bot = bot_key
        self._threshold = max(1, int(fail_threshold))
        self._cooldown = max(0.0, float(cooldown_s))
        self._clock = clock or time.time
        self._lock = threading.Lock()
        self._failures = 0
        self._open_until = 0.0

    @property
    def open(self) -> bool:
        with self._lock:
            return self._clock() < self._open_until

    def check(self) -> None:
        if self.open:
            raise CircuitOpenError(
                f"circuit OPEN for bot {self._bot} (cooldown "
                f"{max(0.0, self._open_until - self._clock()):.1f}s)"
            )

    def record(self, *, ok: bool, is_409: bool = False) -> None:
        with self._lock:
            now = self._clock()
            if ok:
                self._failures = 0
                self._open_until = 0.0
            elif is_409:
                self._failures = self._threshold
                self._open_until = now + self._cooldown
            else:
                self._failures += 1
                if self._failures >= self._threshold:
                    self._open_until = now + self._cooldown

    def stats(self) -> dict:
        with self._lock:
            return {
                "bot": self._bot,
                "consecutive_failures": self._failures,
                "open": self._clock() < self._open_until,
                "cooldown_remaining_s": round(max(0.0, self._open_until - self._clock()), 3),
            }


class TransportPool:
    """Fixed-size transport executor with per-bot circuit breakers."""

    def __init__(self, *, max_concurrent: int = 4, fail_threshold: int = 3,
                 cooldown_s: float = 60.0, subprocess_fn=None, clock=None,
                 deadline_margin: float = 5.0):
        self._max = max(1, int(max_concurrent))
        self._fail_threshold = max(1, int(fail_threshold))
        self._cooldown = max(0.0, float(cooldown_s))
        self._margin = max(0.0, float(deadline_margin))
        self._sem = threading.BoundedSemaphore(self._max)
        self._lock = threading.Lock()
        self._active = 0
        self._active_bots: set[str] = set()
        self._total_stalls = 0
        self._total_calls = 0
        self._total_saturated = 0
        self._total_circuit_blocks = 0
        self._circuits: dict[str, BotCircuit] = {}
        self._subprocess_fn = subprocess_fn
        self._clock = clock or time.time

    def _circuit(self, bot_key: str) -> BotCircuit:
        with self._lock:
            circuit = self._circuits.get(bot_key)
            if circuit is None:
                circuit = BotCircuit(
                    bot_key, fail_threshold=self._fail_threshold,
                    cooldown_s=self._cooldown, clock=self._clock,
                )
                self._circuits[bot_key] = circuit
            return circuit

    def _acquire_slot(self, bot_key: str, circuit: BotCircuit) -> None:
        try:
            circuit.check()
        except CircuitOpenError:
            with self._lock:
                self._total_circuit_blocks += 1
            raise
        with self._lock:
            if bot_key in self._active_bots:
                self._total_saturated += 1
                raise CircuitOpenError(
                    "bot already has an active transport request")
            self._active_bots.add(bot_key)
        if not self._sem.acquire(blocking=False):
            with self._lock:
                self._active_bots.discard(bot_key)
                self._total_saturated += 1
            raise CircuitOpenError("transport pool saturated (no worker spawned)")
        with self._lock:
            self._active += 1
            self._total_calls += 1

    def _release_slot(self, bot_key: str) -> None:
        with self._lock:
            self._active -= 1
            self._active_bots.discard(bot_key)
        self._sem.release()

    def _call_thread(self, bot_key: str, fn, deadline_s: float):
        import queue
        box: queue.Queue = queue.Queue(maxsize=1)

        def worker() -> None:
            try:
                value = fn()
            except Exception as exc:  # noqa: BLE001
                value = exc
            try:
                box.put_nowait(value)
            except queue.Full:
                pass
            finally:
                self._release_slot(bot_key)

        try:
            threading.Thread(target=worker, daemon=True).start()
        except Exception:
            self._release_slot(bot_key)
            raise
        try:
            result = box.get(timeout=max(0.0, float(deadline_s)))
        except queue.Empty:
            return None
        if isinstance(result, Exception):
            raise result
        return result

    def call(self, bot_key: str, url: str, timeout_s: float, *,
             data: bytes | None = None, headers: dict | None = None,
             fn=None) -> bytes | None:
        """Perform one call without exceeding the fixed worker/process bound."""
        circuit = self._circuit(bot_key)
        self._acquire_slot(bot_key, circuit)
        deadline = max(0.0, float(timeout_s)) + self._margin
        if fn is not None:
            return self._call_thread(
                bot_key, lambda: fn(url, timeout_s, data, headers), deadline)
        if self._subprocess_fn is None:
            return self._call_thread(
                bot_key,
                lambda: self._http_bytes(url, timeout_s, data, headers),
                deadline,
            )
        try:
            return self._subprocess_fn(
                url, timeout_s, data=data, headers=headers)
        finally:
            self._release_slot(bot_key)

    @staticmethod
    def _http_bytes(url: str, timeout_s: float, data: bytes | None,
                    headers: dict | None) -> bytes:
        import urllib.request
        request = urllib.request.Request(url, data=data, headers=headers or {})
        with urllib.request.urlopen(request, timeout=float(timeout_s)) as response:  # noqa: S310
            return response.read()

    def record_result(self, bot_key: str, *, ok: bool, is_409: bool = False) -> None:
        self._circuit(bot_key).record(ok=ok, is_409=is_409)

    def stats(self) -> dict:
        with self._lock:
            return {
                "active": self._active,
                "max_concurrent": self._max,
                "total_calls": self._total_calls,
                "total_stalls": self._total_stalls,
                "total_saturated": self._total_saturated,
                "total_circuit_blocks": self._total_circuit_blocks,
                "circuits": {key: circuit.stats() for key, circuit in self._circuits.items()},
            }


_WORKER = r"""
import base64, json, sys, urllib.error, urllib.request
request = json.loads(sys.stdin.read())
data = base64.b64decode(request['data_b64']) if request.get('data_b64') is not None else None
req = urllib.request.Request(request['url'], data=data, headers=request.get('headers') or {})
try:
    with urllib.request.urlopen(req, timeout=float(request['timeout_s'])) as response:
        envelope = {
            'kind': 'ok',
            'body_b64': base64.b64encode(response.read()).decode('ascii'),
        }
except urllib.error.HTTPError as exc:
    envelope = {
        'kind': 'http_error',
        'code': int(exc.code),
        'reason': str(exc.reason or ''),
        'headers': dict(exc.headers.items()) if exc.headers else {},
        'body_b64': base64.b64encode(exc.read(2 * 1024 * 1024)).decode('ascii'),
    }
sys.stdout.write(json.dumps(envelope, separators=(',', ':')))
"""


def _subprocess_deadline(timeout_s: float) -> float:
    timeout = max(0.0, float(timeout_s))
    return timeout + min(5.0, max(0.25, timeout * 0.2))


def subprocess_transport(url: str, timeout_s: float, *, data: bytes | None = None,
                         headers: dict | None = None) -> bytes | None:
    """Execute DNS+HTTP in a child and preserve request/response bytes exactly."""
    payload = json.dumps(
        {
            "url": str(url),
            "timeout_s": max(0.0, float(timeout_s)),
            "data_b64": base64.b64encode(data).decode("ascii") if data is not None else None,
            "headers": headers or {},
        },
        separators=(",", ":"),
    )
    try:
        process = subprocess.run(
            [sys.executable, "-c", _WORKER], input=payload,
            capture_output=True, text=True,
            timeout=_subprocess_deadline(timeout_s),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if process.returncode != 0 or not process.stdout:
        return None
    try:
        envelope = json.loads(process.stdout)
        body = base64.b64decode(
            str(envelope.get("body_b64") or ""), validate=True)
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if envelope.get("kind") == "ok":
        return body
    if envelope.get("kind") == "http_error":
        raise urllib.error.HTTPError(
            str(url), int(envelope.get("code") or 0),
            str(envelope.get("reason") or ""),
            envelope.get("headers") or {}, io.BytesIO(body),
        )
    return None
