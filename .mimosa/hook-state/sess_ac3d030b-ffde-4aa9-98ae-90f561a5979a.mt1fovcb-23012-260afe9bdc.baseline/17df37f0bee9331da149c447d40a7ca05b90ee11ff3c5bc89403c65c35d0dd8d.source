"""
Phase 9 -- data layer: connection pooling + chain-safe concurrent audit. OFFLINE.

  - pooling: N audit.append calls reuse ONE real connection (vs N unpooled)
  - .close() on a pooled connection is a no-op (connection stays usable)
  - hash-chain stays intact after pooled writes (verify_chain PASS)
  - concurrency: many threads appending in parallel never fork the chain
    (rowid-ordered read + append lock) -> verify_chain PASS, all entries present
"""
import os
import sys
import tempfile
import threading

_TMP_DB = tempfile.mkstemp(suffix="_brushline_p9.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = ""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import audit
from src.database import (init_db, get_connection, reset_pool, set_pool_enabled,
                          connection_count, reset_connection_count)


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


def _count_entries():
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM audit_entries").fetchone()["c"]
    finally:
        conn.close()


def main():
    init_db()

    # 1) POOLED: 10 appends reuse ONE real connection
    set_pool_enabled(True)
    reset_pool()
    reset_connection_count()
    for i in range(10):
        audit.append("BENCH_EVT", "e", {"i": i})
    pooled = connection_count()
    _check("pooled: 10 appends -> 1 real connection", pooled == 1)

    # UNPOOLED (legacy): each append opens its own connection
    set_pool_enabled(False)
    reset_connection_count()
    for i in range(10):
        audit.append("BENCH_EVT", "e", {"i": i})
    unpooled = connection_count()
    _check("unpooled: 10 appends -> 10 real connections", unpooled == 10)
    _check("pooling cuts connection churn", pooled < unpooled)
    set_pool_enabled(True)   # restore pooled mode

    # 2) no-op close: pooled connection stays usable after .close()
    reset_pool()
    reset_connection_count()
    conn = get_connection()
    conn.close()                       # no-op for a pooled connection
    conn2 = get_connection()
    conn2.execute("SELECT 1").fetchone()
    _check("close() is a no-op; connection reused (still 1 real)",
           connection_count() == 1)

    # 3) chain intact after pooled writes
    ok, msg = audit.verify_chain()
    _check("verify_chain PASS after pooled appends: " + msg, ok)

    # 4) CONCURRENCY: 5 threads x 10 appends must not fork the chain
    before = _count_entries()
    def worker(tid):
        for i in range(10):
            audit.append("CONC", "t" + str(tid), {"i": i})
    threads = [threading.Thread(target=worker, args=(k,)) for k in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    after = _count_entries()
    _check("all 50 concurrent appends persisted", after - before == 50)
    ok2, msg2 = audit.verify_chain()
    _check("verify_chain PASS after concurrent appends: " + msg2, ok2)

    print("\nALL DATA-LAYER (P9) CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        reset_pool()
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
