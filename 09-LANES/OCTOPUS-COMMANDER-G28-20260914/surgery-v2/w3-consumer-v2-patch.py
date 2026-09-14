"""W3 consumer v2 (ROUND32): fix the NO_TASK permanent-loss counterexample.

The bug (measured by the reviewer with the REAL consume_decisions function
from TRIO 9e157b4d, in-memory filesystem, zero production contact):
  - a valid ACK_SEEN decision arrives BEFORE the task is registered
  - consumer logs DECISION_NO_TASK and marks the decision key as consumed
  - the task is registered later (with a valid created_at)
  - next tick: the decision key is already in the consumed set -> idle
  - the task stays in awaiting_ack FOREVER (the decision is permanently lost)

Fix: DECISION_NO_TASK is RETRYABLE — the decision key is NOT marked as
consumed; each tick re-evaluates unmatched decisions. A key only becomes
terminal (consumed) when it results in a task-affecting disposition:
DECISION_CONSUMED, DECISION_TASK_NOT_WAITING, DECISION_STALE, DECISION_IGNORED.
"""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v3d-9e157b4d"

OLD = '''        elif task is None:
            # the CARD was already consumed by the binder; no registered task
            # means nothing to resume - cards are NEVER re-pended
            _record_decision(cons_path, key, "DECISION_NO_TASK",
                             bound=str(bound)[:16])'''
NEW = '''        elif task is None:
            # no registered task MATCHES this decision. This is RETRYABLE:
            # the task may not have been registered yet (the registration
            # contract says durable task BEFORE card display, but the
            # consumer must tolerate a delayed registration). The decision
            # key is NOT consumed here - the next tick will re-evaluate it.
            # Cards themselves are consumed by the binder's one-use registry
            # and are NEVER re-pended.
            _record_decision(cons_path, key, "DECISION_NO_TASK_RETRYABLE",
                             bound=str(bound)[:16])'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "9e157b4d":
    sys.exit("not v3d")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v3d preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("W3v2        :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
