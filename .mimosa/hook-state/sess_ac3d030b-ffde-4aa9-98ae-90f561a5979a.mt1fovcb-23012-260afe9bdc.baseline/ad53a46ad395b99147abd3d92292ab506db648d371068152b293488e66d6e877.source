"""Watchdog notifier: tell the supervisor we are alive, but only if we are.

The whole value of a watchdog is in one design decision: what counts as
"alive". A heartbeat thread that pings unconditionally detects exactly one
failure — total process death — which the supervisor's restart policy already
handles. It is worse than nothing, because it produces confidence that a hung
service is healthy.

So the ping here is gated on a real liveness probe supplied by the caller: the
event loop has ticked recently, the database answers, the queue is being
drained. If that probe returns False, we simply do not ping, and the
supervisor kills and restarts us — which is the correct outcome for a process
that is running but not working.

Communicates over the notify socket directly with `socket`, so there is no
dependency on a systemd Python binding. When the socket is absent — running
under a test, or by hand in a terminal — every method is a no-op that returns
False rather than raising, because a watchdog that crashes the thing it is
watching is a poor watchdog.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from typing import Callable


@dataclass
class Notifier:
    """Thin wrapper over the supervisor's notify socket."""

    address: str = ""

    def __post_init__(self) -> None:
        if not self.address:
            self.address = os.environ.get("NOTIFY_SOCKET", "")

    @property
    def enabled(self) -> bool:
        return bool(self.address)

    def _send(self, message: str) -> bool:
        if not self.address:
            return False
        path = self.address
        if path.startswith("@"):        # abstract namespace
            path = "\0" + path[1:]
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            try:
                sock.connect(path)
                sock.sendall(message.encode("utf-8"))
            finally:
                sock.close()
            return True
        except OSError:
            return False

    def ready(self) -> bool:
        return self._send("READY=1")

    def ping(self) -> bool:
        return self._send("WATCHDOG=1")

    def stopping(self) -> bool:
        return self._send("STOPPING=1")

    def status(self, text: str) -> bool:
        """One line the operator sees in `systemctl status`. Never put a
        secret, a customer name, or raw model output here."""
        return self._send(f"STATUS={text[:200]}")


def watchdog_interval_s(default: float = 15.0) -> float:
    """Half the supervisor's timeout, which is the documented contract.

    Pinging at exactly the timeout races the supervisor and produces spurious
    restarts under any load at all.
    """
    raw = os.environ.get("WATCHDOG_USEC", "")
    try:
        usec = int(raw)
    except ValueError:
        return default
    if usec <= 0:
        return default
    return (usec / 1_000_000.0) / 2.0


class HealthGate:
    """Wraps a liveness probe and decides whether to ping.

    Records consecutive failures so a caller can distinguish a single blip
    from a service that has been wedged for a minute — the two want different
    responses, and only the second should end in a restart.
    """

    def __init__(self, probe: Callable[[], bool], *,
                 tolerate_failures: int = 2) -> None:
        self._probe = probe
        self._tolerate = max(0, tolerate_failures)
        self.consecutive_failures = 0
        self.last_healthy = True

    def check(self) -> bool:
        try:
            healthy = bool(self._probe())
        except Exception:
            # A probe that raises is a failing probe. Swallowing the exception
            # and pinging anyway would defeat the entire mechanism.
            healthy = False
        self.last_healthy = healthy
        if healthy:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
        return healthy

    def should_ping(self) -> bool:
        """Ping while inside the tolerance band; go silent past it."""
        self.check()
        return self.consecutive_failures <= self._tolerate


def beat(notifier: Notifier, gate: HealthGate) -> bool:
    """One watchdog cycle. Returns whether a ping was sent."""
    if gate.should_ping():
        return notifier.ping()
    notifier.status(f"unhealthy for {gate.consecutive_failures} checks — "
                    f"withholding watchdog ping")
    return False
