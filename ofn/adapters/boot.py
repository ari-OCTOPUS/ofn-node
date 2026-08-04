"""Boot supervisor: decide whether this node is fit to act, before it acts.

Every check below answers one question — *can this node be trusted to make
decisions right now?* — and a failure of the critical ones does not stop the
node. It drops it into SAFE MODE: still running, still readable, still able to
answer a partner's screen from the ledger, but structurally unable to send
anything outward.

That distinction matters. A node that refuses to boot after a power cut is a
node nobody can diagnose remotely. A node that boots into a state where every
outbound path is closed is one you can log into, inspect, and repair — and
which cannot do damage while you get to it.

Order is deliberate: the clock is checked first because a wrong clock silently
invalidates signature freshness, quota windows, and TLS, and every check after
it would be reasoning from a bad premise.
"""

from __future__ import annotations

import enum
import os
import shutil
from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

from ..kernel.domain import TenantId
from ..kernel.tenancy import TenantScope
from . import audience_store as _audience
from . import consent_store as _consent
from . import facts as _facts
from . import ledger as _ledger
from . import outbox as _outbox
from . import products as _products
from . import studio_store as _studio
from .sqlite_base import (
    apply_schema, checkpoint, connect, integrity_ok, missing_columns,
)

# Keyed by the names `config.db_paths` uses: schema, then the migrations that
# bring an older file up to it. A store absent from this map is neither
# migrated nor checked, which is why the map lives next to the check rather
# than inside each adapter — forgetting to add a new store is visible from
# one screen.
SCHEMAS: Mapping[str, Sequence[str]] = {
    "ledger": _ledger.SCHEMA,
    "facts": _facts.SCHEMA,
    "outbox": _outbox.SCHEMA,
    "products": _products.SCHEMA,
    "consent": _consent.SCHEMA,
    "studio": _studio.SCHEMA,
    "audience": _audience.SCHEMA,
}

MIGRATIONS: Mapping[str, Sequence] = {
    "products": _products.MIGRATIONS,
    "studio": _studio.MIGRATIONS,
}

# A board with no battery-backed clock reports something near the epoch until
# NTP lands. Anything before this is definitely wrong, not merely surprising.
MIN_PLAUSIBLE_EPOCH = 1_767_225_600      # 2026-01-01
MIN_FREE_BYTES = 200 * 1024 * 1024
MIN_FREE_RAM_BYTES = 150 * 1024 * 1024


class Mode(enum.Enum):
    NORMAL = "normal"
    SAFE = "safe"


class Severity(enum.Enum):
    OK = "ok"
    WARN = "warn"          # note it, keep going
    CRITICAL = "critical"  # SAFE MODE


@dataclass(frozen=True)
class Check:
    name: str
    severity: Severity
    detail: str


@dataclass
class BootReport:
    checks: list[Check] = field(default_factory=list)
    mode: Mode = Mode.NORMAL
    recovered_outbox: int = 0

    def add(self, name: str, severity: Severity, detail: str) -> None:
        self.checks.append(Check(name, severity, detail))
        if severity is Severity.CRITICAL:
            self.mode = Mode.SAFE

    @property
    def ok(self) -> bool:
        return self.mode is Mode.NORMAL

    @property
    def failures(self) -> Sequence[Check]:
        return [c for c in self.checks if c.severity is not Severity.OK]

    def summary(self) -> str:
        bad = self.failures
        if not bad:
            return f"boot OK — {len(self.checks)} checks passed"
        head = f"boot {self.mode.value.upper()} — {len(bad)} of {len(self.checks)} checks raised"
        return head + ": " + "; ".join(f"{c.name}({c.severity.value})" for c in bad)


class BootSupervisor:
    """Runs the pre-flight sequence and reports what it found."""

    def __init__(
        self,
        *,
        db_paths: Mapping[str, str],
        tenants: Sequence[TenantId],
        now_epoch_s: Callable[[], int],
        state_dir: str,
        free_ram_bytes: Callable[[], int] | None = None,
    ) -> None:
        self._dbs = dict(db_paths)
        self._tenants = list(tenants)
        self._now = now_epoch_s
        self._state_dir = state_dir
        self._free_ram = free_ram_bytes or _read_available_ram

    def run(self, *, ledger=None, outbox=None, now_iso: str = "") -> BootReport:
        rep = BootReport()
        self._check_clock(rep)
        self._check_disk(rep)
        self._check_ram(rep)
        self._check_databases(rep)
        if ledger is not None:
            self._check_chains(rep, ledger)
        if outbox is not None:
            self._recover_outbox(rep, outbox, now_iso)
        return rep

    # ── individual checks ─────────────────────────────────────────────────
    def _check_clock(self, rep: BootReport) -> None:
        """A wrong clock invalidates everything downstream, silently.

        This board has no RTC, so until NTP lands the clock reads as some
        moment near the epoch. Signature freshness would reject every valid
        request, and quota windows would land in the wrong week — both failing
        in ways that look like other bugs.
        """
        now = self._now()
        if now < MIN_PLAUSIBLE_EPOCH:
            rep.add("clock", Severity.CRITICAL,
                    f"clock reads {now}, before the earliest plausible time — "
                    f"NTP has not synced; signature and quota windows cannot be "
                    f"trusted")
        else:
            rep.add("clock", Severity.OK, "clock plausible")

    def _check_disk(self, rep: BootReport) -> None:
        try:
            usage = shutil.disk_usage(self._state_dir)
        except OSError as exc:
            rep.add("disk", Severity.CRITICAL, f"state directory unreadable: {exc}")
            return
        if usage.free < MIN_FREE_BYTES:
            rep.add("disk", Severity.CRITICAL,
                    f"only {usage.free // 1024 // 1024} MB free — a full disk "
                    f"corrupts SQLite writes rather than failing them cleanly")
        else:
            rep.add("disk", Severity.OK, f"{usage.free // 1024 // 1024} MB free")

    def _check_ram(self, rep: BootReport) -> None:
        """4 GB is the whole budget. Starting without headroom means the OOM
        killer chooses for us, and it does not choose well."""
        free = self._free_ram()
        if free < 0:
            rep.add("ram", Severity.WARN, "could not read available memory")
        elif free < MIN_FREE_RAM_BYTES:
            rep.add("ram", Severity.WARN,
                    f"only {free // 1024 // 1024} MB available — expect the OOM "
                    f"killer if a model loads")
        else:
            rep.add("ram", Severity.OK, f"{free // 1024 // 1024} MB available")

    def _check_databases(self, rep: BootReport) -> None:
        """`quick_check` on boot, not `integrity_check`.

        quick_check skips index-vs-table cross validation, which is the
        expensive part. The thorough check runs nightly against the backup
        copy, where its cost is nobody's problem.
        """
        for name, path in sorted(self._dbs.items()):
            if not os.path.exists(path):
                rep.add(f"db:{name}", Severity.OK, "not yet created")
                continue
            try:
                conn = connect(path)
            except Exception as exc:
                rep.add(f"db:{name}", Severity.CRITICAL, f"cannot open: {exc}")
                continue
            try:
                if integrity_ok(conn, quick=True):
                    checkpoint(conn)          # fold the WAL back in cleanly
                    rep.add(f"db:{name}", Severity.OK, "integrity ok, WAL folded")
                else:
                    rep.add(f"db:{name}", Severity.CRITICAL,
                            "quick_check failed — restore from backup before use")
                self._check_shape(rep, name, conn)
            finally:
                conn.close()

    def _check_shape(self, rep: BootReport, name: str, conn) -> None:
        """Bring this file up to the current schema, then say whether it got
        there.

        `quick_check` above answers "is this file structurally sound", which
        is a different question from "is this file the shape this build
        expects". A file can be perfectly intact and still be one schema edit
        behind, because `CREATE TABLE IF NOT EXISTS` never revisits a table it
        finds.

        This check writes, which a check normally should not. It does so
        because of ordering: the stores migrate themselves when the node
        opens them, and pre-flight runs in a separate process *before* that.
        Checking first would report every pending migration as a fault and
        drop a healthy node into SAFE MODE for a condition it was about to
        fix by itself. So the migrations run here, and what is left over is
        the real answer.

        Residual drift is CRITICAL rather than a warning, and the reason is
        who pays. The alternative to failing here is failing later, in a
        partner's hand, as a request that dies with no response — which is
        exactly how this check came to be written. SAFE MODE keeps the node
        inspectable and closes the outbound paths, which is the correct
        posture for a node whose store does not match its code.
        """
        schema = SCHEMAS.get(name)
        if schema is None:
            return
        try:
            apply_schema(conn, schema, MIGRATIONS.get(name, ()))
            drift = missing_columns(conn, schema)
        except Exception as exc:
            rep.add(f"schema:{name}", Severity.CRITICAL,
                    f"could not bring the file to the current schema: {exc}")
            return
        if drift:
            gaps = "; ".join(f"{t} missing {', '.join(c)}"
                             for t, c in sorted(drift.items()))
            rep.add(f"schema:{name}", Severity.CRITICAL,
                    f"{gaps} — the file predates a schema change and no "
                    f"migration brings it forward")
        else:
            rep.add(f"schema:{name}", Severity.OK, "shape matches code")

    def _check_chains(self, rep: BootReport, ledger) -> None:
        """A broken chain means history was edited. Never act on it."""
        for tenant in self._tenants:
            ok, why = ledger.verify(TenantScope(tenant))
            if ok:
                rep.add(f"chain:{tenant.value}", Severity.OK, why)
            else:
                rep.add(f"chain:{tenant.value}", Severity.CRITICAL, why)

    def _recover_outbox(self, rep: BootReport, outbox, now_iso: str) -> None:
        """Anything in flight when the lights went out gets held, not resent.

        Held items are a WARN, not a CRITICAL: the node is healthy, but a
        human has messages waiting on a decision only they can make.
        """
        moved = outbox.recover_stale(now_iso, resend=False)
        rep.recovered_outbox = moved
        if moved:
            rep.add("outbox", Severity.WARN,
                    f"{moved} item(s) were in flight at shutdown — held for a "
                    f"human decision, not resent")
        else:
            rep.add("outbox", Severity.OK, "no interrupted sends")


def _read_available_ram() -> int:
    """MemAvailable in bytes, or -1 if unreadable (non-Linux, sandbox, etc.)."""
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return -1


def closed_gates_for(report: BootReport, base: Sequence[str] = ()) -> tuple[str, ...]:
    """Gates that must be treated as shut given this boot outcome.

    SAFE MODE adds a synthetic gate rather than setting a flag somewhere: the
    risk engine already escalates everything a pack is gated on, so expressing
    degradation as a closed gate means no new code path has to remember to
    check a mode variable.
    """
    gates = list(base)
    if report.mode is Mode.SAFE and "safe_mode" not in gates:
        gates.append("safe_mode")
    return tuple(gates)
