"""Background thinker: the only place a slow brain is allowed to run.

The hosted brain takes between seven seconds and several minutes per call.
Nothing a partner is waiting on can go through it — the HTTP layer is
structurally forbidden from even importing the router for that reason. So the
thinking happens here instead: a loop that picks work off a queue, spends real
time on it, and writes the result back into the ledger where the interactive
path can read it instantly.

The shape that follows from that latency:

    partner taps a button
        → written to the ledger in single-digit milliseconds
        → "recorded ✓" on screen immediately
    ... minutes later, on this loop ...
        → brain thinks
        → proposal lands in the owner's queue
        → owner decides

Two properties this loop must have, and both are about the owner waking up to
a system that behaved:

**It must be interruptible.** A long call cannot be allowed to hold the
process open through a shutdown, so the stop flag is checked between every
job and the loop never blocks on anything longer than one call.

**It must never run away.** A task that fails is retried a bounded number of
times and then parked for a human, because a task that fails forever on a
quota-metered brain is a bill with no upper limit.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

from .adapters.ledger import Ledger
from .adapters.router import ModelRouter, RouterResult
from .kernel.domain import TenantId
from .kernel.routing import RouteRequest, Rung, calibrate_latency
from .kernel.tenancy import TenantRegistry, TenantScope

MAX_ATTEMPTS = 3


@dataclass
class Job:
    """One unit of thinking. Deliberately small and serialisable."""

    tenant: str
    task: str
    prompt: str
    idem_key: str
    max_rung: Rung = Rung.REMOTE
    estimated_tokens: int = 2000
    attempts: int = 0
    owner_approved_deep: bool = False


@dataclass
class WorkQueue:
    """In-memory queue with a durable shadow in the ledger.

    Jobs are recorded to the ledger on submission, so a restart mid-queue
    leaves a trace of what was pending even though the queue itself is lost.
    Rebuilding from that trace is deliberately *not* automatic: re-running
    thinking that may already have produced a proposal would double-charge
    the quota and could duplicate a queued decision. A human decides.
    """

    _items: list[Job] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _seen: set = field(default_factory=set)

    def submit(self, job: Job) -> bool:
        """Add a job. Returns False if this idem_key is already queued."""
        with self._lock:
            key = (job.tenant, job.idem_key)
            if key in self._seen:
                return False
            self._seen.add(key)
            self._items.append(job)
            return True

    def take(self) -> Job | None:
        with self._lock:
            return self._items.pop(0) if self._items else None

    def requeue(self, job: Job) -> None:
        """Put a failed job back at the tail, so one bad job cannot starve
        the rest by being retried at the head forever."""
        with self._lock:
            self._items.append(job)

    def forget(self, job: Job) -> None:
        with self._lock:
            self._seen.discard((job.tenant, job.idem_key))

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


class Worker:
    """Drains the queue through the router, writing every outcome to the ledger."""

    def __init__(
        self,
        queue: WorkQueue,
        router: ModelRouter,
        registry: TenantRegistry,
        ledger: Ledger,
        *,
        now_epoch_s: Callable[[], int],
        now_iso: Callable[[], str],
        on_result: Callable[[TenantScope, Job, RouterResult], None] | None = None,
    ) -> None:
        self._q = queue
        self._router = router
        self._registry = registry
        self._ledger = ledger
        self._now_s = now_epoch_s
        self._now_iso = now_iso
        self._on_result = on_result
        self.parked: list[Job] = []

    def submit(self, scope: TenantScope, job: Job) -> bool:
        """Queue a job and record the intent."""
        accepted = self._q.submit(job)
        if accepted:
            self._ledger.append(scope, "THINK_QUEUED", {
                "task": job.task, "idem": job.idem_key,
                "max_rung": job.max_rung.value,
            }, self._now_iso())
        return accepted

    def step(self) -> bool:
        """Process at most one job. Returns False when the queue is empty.

        One job per call rather than draining: it keeps the caller in control
        of pacing, and it means the stop flag is checked between jobs without
        this class needing to know about shutdown at all.
        """
        job = self._q.take()
        if job is None:
            return False

        if job.tenant not in self._registry:
            self.parked.append(job)
            return True
        scope = self._registry.scope(job.tenant)

        req = RouteRequest(
            task=job.task,
            interactive=False,          # never — that is the whole point
            estimated_tokens=job.estimated_tokens,
            owner_approved_deep=job.owner_approved_deep,
            max_rung=job.max_rung,
        )

        started = time.monotonic()
        try:
            result = self._router.ask(TenantId(job.tenant), req, job.prompt,
                                      now_epoch_s=self._now_s())
        except Exception as exc:
            result = RouterResult("", None, refused=f"router raised: {exc}")
        elapsed_ms = int((time.monotonic() - started) * 1000)

        # Replace the shipped estimate with what this board actually saw.
        # Only ever upward — see calibrate_latency for why.
        if result.rung is not None:
            calibrate_latency(result.rung, elapsed_ms)

        now = self._now_iso()
        if result.ok:
            self._ledger.append(scope, "THINK_DONE", {
                "task": job.task, "idem": job.idem_key,
                "rung": result.rung.value if result.rung else None,
                "path": list(result.path), "billed_tokens": result.spend,
                "elapsed_ms": elapsed_ms,
                "scrubbed": dict(result.scrubbed.findings) if result.scrubbed else {},
            }, now)
            self._q.forget(job)
            if self._on_result is not None:
                self._on_result(scope, job, result)
            return True

        job.attempts += 1
        if job.attempts >= MAX_ATTEMPTS:
            # Parked, not retried forever. A job that keeps failing against a
            # metered brain is an unbounded bill, and the reason it fails is
            # almost never something another attempt fixes.
            self.parked.append(job)
            self._q.forget(job)
            self._ledger.append(scope, "THINK_PARKED", {
                "task": job.task, "idem": job.idem_key,
                "attempts": job.attempts, "reason": result.refused,
            }, now)
        else:
            self._q.requeue(job)
            self._ledger.append(scope, "THINK_RETRY", {
                "task": job.task, "idem": job.idem_key,
                "attempt": job.attempts, "reason": result.refused,
            }, now)
        return True

    def drain(self, stop: threading.Event | None = None, limit: int = 100) -> int:
        """Work until the queue empties, the limit is hit, or stop is set.

        `limit` is a safety rail rather than a tuning knob: without it, a job
        that requeues itself could keep this loop busy indefinitely and starve
        the shutdown check.
        """
        done = 0
        while done < limit:
            if stop is not None and stop.is_set():
                break
            if not self.step():
                break
            done += 1
        return done

    def status(self) -> Mapping[str, object]:
        return {"queued": len(self._q), "parked": len(self.parked)}


def loop(worker: Worker, stop: threading.Event, interval_s: float = 5.0) -> None:
    """Run until told to stop. Intended for a daemon thread.

    Sleeps on the stop event rather than on the clock, so shutdown is
    immediate rather than up to `interval_s` late — on a board that reboots
    for backups, that difference is the difference between a clean stop and a
    SIGKILL mid-call.
    """
    while not stop.is_set():
        try:
            worker.drain(stop=stop, limit=20)
        except Exception:
            # A worker that dies silently is worse than one that retries: the
            # queue would fill with nothing draining it and no signal anywhere.
            pass
        stop.wait(interval_s)
