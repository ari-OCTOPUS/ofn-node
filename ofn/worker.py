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
from .kernel.quota import CONTROL_SCOPE
from .kernel.routing import RouteRequest, Rung, calibrate_latency
from .kernel.tenancy import TenantRegistry, TenantScope

MAX_ATTEMPTS = 3

# The owner's control scope is not a business leg and has no pack, but its
# jobs are legitimate queue citizens. Anything else outside the registry is
# a routing bug and gets parked, not run.
QUEUE_TENANTS = frozenset({CONTROL_SCOPE})

# A refusal carrying one of these code prefixes is a policy verdict, not a
# bad afternoon: the same request will be refused forever, so retrying only
# burns attempts against a metered brain. Everything else (provider errors,
# timeouts, exceptions) is treated as transient and retried with backoff.
NON_TRANSIENT_PREFIXES = ("quota:", "route:")

# Transient failures wait before their next attempt: 30s after the first,
# doubling, capped at ten minutes. Round 1 retried a deterministic denial
# three times inside one second; the floor here exists so that can never
# happen again, the cap so a flapping provider cannot retry forever.
BACKOFF_BASE_S = 30
BACKOFF_MAX_S = 600

OWNER_ASK_TASK = "owner:ask"


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
    # Earliest epoch second this job may run again after a transient
    # failure. Zero means ready now.
    not_before: int = 0


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

    def take_ready(self, now_epoch_s: int) -> Job | None:
        """FIFO first job whose backoff has elapsed. A waiting job keeps its
        place; nothing behind it may jump ahead of it."""
        with self._lock:
            for i, job in enumerate(self._items):
                if job.not_before <= now_epoch_s:
                    return self._items.pop(i)
            return None

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
        # The sink owns what happens to a *successful* answer. For owner
        # asks it scrubs, persists, and returns the metadata (response id,
        # hash, size) that THINK_DONE should commit to. False/None from the
        # sink means the answer never landed, so the job must not be marked
        # done; a bare True means "recorded elsewhere" — legacy tasks.
        result_sink: (Callable[[TenantScope, Job, RouterResult, int], object]
                      | None) = None,
        # Called on every refusal with the classification the worker used,
        # so the owner's store can mirror the job's real state.
        on_failure: Callable[..., None] | None = None,
        # Called the moment a job is picked up, before the brain runs.
        on_start: Callable[[TenantScope, Job], None] | None = None,
        backoff_base_s: int = BACKOFF_BASE_S,
    ) -> None:
        self._q = queue
        self._router = router
        self._registry = registry
        self._ledger = ledger
        self._now_s = now_epoch_s
        self._now_iso = now_iso
        self._on_result = on_result
        self._result_sink = result_sink
        self._on_failure = on_failure
        self._on_start = on_start
        self._backoff_base_s = max(0, int(backoff_base_s))
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
        """Process at most one ready job. Returns False when none is ready.

        One job per call rather than draining: it keeps the caller in control
        of pacing, and it means the stop flag is checked between jobs without
        this class needing to know about shutdown at all.
        """
        job = self._q.take_ready(self._now_s())
        if job is None:
            return False

        if job.tenant not in self._registry and job.tenant not in QUEUE_TENANTS:
            self.parked.append(job)
            return True
        if job.tenant in self._registry:
            scope = self._registry.scope(job.tenant)
        else:
            scope = TenantScope(TenantId(job.tenant))

        req = RouteRequest(
            task=job.task,
            interactive=False,          # never — that is the whole point
            estimated_tokens=job.estimated_tokens,
            owner_approved_deep=job.owner_approved_deep,
            max_rung=job.max_rung,
        )
        if self._on_start is not None:
            try:
                self._on_start(scope, job)
            except Exception:
                pass  # lifecycle mirroring must never stop the work

        started = time.monotonic()
        try:
            result = self._router.ask(TenantId(job.tenant), req, job.prompt,
                                      now_epoch_s=self._now_s())
        except Exception as exc:
            result = RouterResult("", None, refused=f"router raised: {exc}",
                                  refused_code="internal:exception")
        elapsed_ms = int((time.monotonic() - started) * 1000)

        # Replace the shipped estimate with what this board actually saw.
        # Only ever upward — see calibrate_latency for why.
        if result.rung is not None:
            calibrate_latency(result.rung, elapsed_ms)

        now = self._now_iso()
        if result.ok:
            # The answer is disposed of FIRST. If the sink cannot land it,
            # there is no THINK_DONE: a completion event pointing at an
            # answer nobody can read would be a polite lie.
            extra = True
            if self._result_sink is not None:
                try:
                    extra = self._result_sink(scope, job, result,
                                              elapsed_ms)
                except Exception:
                    extra = None
            if extra is None or extra is False:
                job.attempts += 1
                self.parked.append(job)
                self._q.forget(job)
                self._ledger.append(scope, "THINK_PARKED", {
                    "task": job.task, "idem": job.idem_key,
                    "attempts": job.attempts,
                    "reason": "answer could not be persisted",
                    "retryable": False,
                }, now)
                if self._on_failure is not None:
                    self._notify_failure(scope, job, "answer could not be "
                                         "persisted",
                                         "internal:persist-failed",
                                         retryable=False, next_not_before=0)
                return True

            done_payload = {
                "task": job.task, "idem": job.idem_key,
                "rung": result.rung.value if result.rung else None,
                "path": list(result.path), "billed_tokens": result.spend,
                "elapsed_ms": elapsed_ms,
                "scrubbed": dict(result.scrubbed.findings) if result.scrubbed else {},
            }
            if isinstance(extra, Mapping):
                done_payload.update(extra)
            self._ledger.append(scope, "THINK_DONE", done_payload, now)
            self._q.forget(job)
            if self._on_result is not None:
                self._on_result(scope, job, result)
            return True

        job.attempts += 1
        deterministic = result.refused_code.startswith(NON_TRANSIENT_PREFIXES)
        if deterministic or job.attempts >= MAX_ATTEMPTS:
            # Parked, not retried. A policy denial is forever; a repeatedly
            # failing job against a metered brain is a bill with no upper
            # limit. Either way, retrying is the wrong next move.
            self.parked.append(job)
            self._q.forget(job)
            self._ledger.append(scope, "THINK_PARKED", {
                "task": job.task, "idem": job.idem_key,
                "attempts": job.attempts, "reason": result.refused,
                "code": result.refused_code, "retryable": False,
                "path": list(result.path),
                **({"provider_model": result.provider_note}
                   if result.provider_note else {}),
            }, now)
            if self._on_failure is not None:
                self._notify_failure(scope, job,
                                     result.refused + (
                                         f" [{result.provider_note}]"
                                         if result.provider_note else ""),
                                     result.refused_code, retryable=False,
                                     next_not_before=0)
        else:
            delay = min(self._backoff_base_s * (2 ** (job.attempts - 1)),
                        BACKOFF_MAX_S)
            job.not_before = self._now_s() + delay
            self._q.requeue(job)
            self._ledger.append(scope, "THINK_RETRY", {
                "task": job.task, "idem": job.idem_key,
                "attempt": job.attempts, "reason": result.refused,
                "code": result.refused_code, "backoff_s": delay,
                "next_attempt_at": job.not_before,
                "path": list(result.path),
                **({"provider_model": result.provider_note}
                   if result.provider_note else {}),
            }, now)
            if self._on_failure is not None:
                self._notify_failure(scope, job, result.refused,
                                     result.refused_code, retryable=True,
                                     next_not_before=job.not_before)
        return True

    def _notify_failure(self, scope: TenantScope, job: Job, reason: str,
                        code: str, *, retryable: bool,
                        next_not_before: int) -> None:
        try:
            self._on_failure(scope, job, reason=reason, code=code,
                             retryable=retryable,
                             next_not_before=next_not_before,
                             attempts=job.attempts)
        except Exception:
            # The store mirroring the failure must never take the worker
            # down; the ledger rows above are the durable record either way.
            pass

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
