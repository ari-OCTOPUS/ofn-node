"""SQLite connection policy for a machine somebody unplugs.

Every pragma here is chosen for one failure mode: the power goes out mid-write
and the box reboots. The defaults are tuned for servers on a UPS, which this
is not.

    journal_mode = WAL        a failed sync can only lose durability, not
                              corrupt the file — except during a checkpoint,
                              so we checkpoint rarely
    synchronous  = FULL       fsync on every commit. NOT `NORMAL`: SQLite's
                              own docs say that under WAL, `NORMAL` means
                              "transactions are no longer durable and might
                              roll back following a power failure". That is
                              precisely the property we are buying.
    busy_timeout = 5000       three legs share this file; block, don't fail

`synchronous=FULL` costs an fsync per commit. On eMMC that is roughly a
millisecond. The alternative costs the last few seconds of the ledger, which
is the one thing that cannot be reconstructed.

A warning worth writing down: consumer flash lies about fsync. These settings
are necessary and not sufficient — a supercapacitor or small UPS does more for
durability here than any pragma.
"""

from __future__ import annotations

import sqlite3
import threading
from typing import Iterable


PRAGMAS: tuple[tuple[str, object], ...] = (
    ("journal_mode", "WAL"),
    ("synchronous", "FULL"),
    ("busy_timeout", 5000),
    ("foreign_keys", "ON"),
    ("journal_size_limit", 4 * 1024 * 1024),
    ("temp_store", "MEMORY"),
)


def connect(path: str) -> sqlite3.Connection:
    """Open a connection with the durability policy applied.

    `isolation_level=None` puts us in explicit-transaction mode: nothing is
    implicitly wrapped, so a caller that means to commit says so. Implicit
    transactions are how a "read" ends up holding a write lock.

    `check_same_thread=False` because the HTTP server answers each request on
    its own thread while the stores are opened once at boot. Python's default
    would raise on the second thread to touch a store — which surfaces as the
    connection dropping mid-request, with no useful error anywhere.

    Relaxing that check makes correct locking OUR job, which is what `Guard`
    below is for. Every store wraps its connection in one; a bare connection
    shared across threads would interleave two explicit transactions on the
    same handle and commit half of each.
    """
    conn = sqlite3.connect(path, isolation_level=None, timeout=5.0,
                           check_same_thread=False)
    conn.row_factory = sqlite3.Row
    for name, value in PRAGMAS:
        conn.execute(f"PRAGMA {name} = {value}")
    return conn


def integrity_ok(conn: sqlite3.Connection, *, quick: bool = True) -> bool:
    """Structural check. `quick_check` on boot, full `integrity_check` nightly.

    quick_check skips index-vs-table cross-validation, which is the expensive
    part; on an SBC that difference is the whole reason boot is not slow.
    """
    pragma = "quick_check" if quick else "integrity_check"
    row = conn.execute(f"PRAGMA {pragma}").fetchone()
    return row is not None and row[0] == "ok"


def checkpoint(conn: sqlite3.Connection) -> None:
    """Fold the WAL back into the database file and truncate it.

    Called on clean shutdown and after restore — not on a timer. Checkpointing
    is the only moment in WAL mode when a failed sync can actually corrupt the
    file, so the correct frequency is 'as rarely as we can stand'.
    """
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def apply_schema(conn: sqlite3.Connection, statements: Iterable[str]) -> None:
    """Create tables idempotently, inside one transaction."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        for stmt in statements:
            conn.execute(stmt)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


class Pool:
    """One SQLite connection per thread, all pointing at the same file.

    The HTTP server answers each request on its own thread while the stores
    are opened once at boot. Sharing a single connection across those threads
    fails twice over: Python refuses it outright by default, and even with
    that check disabled two threads would interleave their explicit
    transactions on one handle and commit half of each.

    Handing every thread its own connection sidesteps both. Concurrency is
    then SQLite's problem, which it solves properly — WAL mode allows
    concurrent readers alongside one writer, and `busy_timeout` makes a
    writer wait rather than fail. This is the standard answer; per-method
    locking in Python would be a worse re-implementation of it.

    Cost: a few file handles. On a board with three legs and a handful of
    request threads, that is nothing.
    """

    __slots__ = ("_path", "_local", "_all", "_lock", "_closed")

    def __init__(self, path: str) -> None:
        self._path = path
        self._local = threading.local()
        self._all: list[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self._closed = False

    @property
    def conn(self) -> sqlite3.Connection:
        # A closed store must stay closed. Without this the thread-local
        # would simply mint a fresh connection on next use, so a shut-down
        # store would silently come back to life — and a health probe that
        # reads it would report a dead node as healthy.
        if self._closed:
            raise sqlite3.ProgrammingError("connection pool is closed")
        got = getattr(self._local, "conn", None)
        if got is None:
            got = connect(self._path)
            self._local.conn = got
            with self._lock:
                self._all.append(got)
        return got

    def close(self) -> None:
        """Close every connection this pool handed out.

        Called on shutdown from one thread, so it must reach connections
        created on others — hence the list alongside the thread-local.
        """
        with self._lock:
            for conn in self._all:
                try:
                    conn.close()
                except Exception:
                    pass
            self._all.clear()
            self._closed = True
        self._local = threading.local()
