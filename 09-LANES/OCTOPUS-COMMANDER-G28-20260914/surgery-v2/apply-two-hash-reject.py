"""Two-hash REJECT (owner decision 2026-09-14: «REJECT مبهم شود»).

Patches the W24 candidate binder: when a text carries TWO OR MORE hashes
that EACH resolve to a DIFFERENT pending card, the decision is
REJECT_AMBIGUOUS (owner must send a single-card message).
A text with multiple hashes that all resolve to the SAME card is fine.
"""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "TASK-W24-BINDER-SPOOL-006/go_b3_owner_bind.py")
PRE = P.parent / "go_b3_owner_bind.py.pre-twohash-20260914"

OLD = '''    hexes = sorted(set(h.lower() for h in hexes), key=len, reverse=True)
    for h in hexes:
        bound, st = resolve_hash(h, rows, expired)'''
NEW = '''    hexes = sorted(set(h.lower() for h in hexes), key=len, reverse=True)
    # owner decision 2026-09-14 «REJECT مبهم شود»: multiple DISTINCT valid
    # hashes = ambiguous intent; the owner must send a single-card message.
    _resolved = {}
    for h in hexes:
        _b, _s = resolve_hash(h, rows, expired)
        if _s == "OK" and _b:
            _resolved[_b] = h
    if len(_resolved) > 1:
        return emit_decision("REJECT_AMBIGUOUS", None, text,
                             {"reason": "multiple_distinct_valid_hashes",
                              "resolved_count": len(_resolved),
                              "owner_note": "send one card per message"})
    for h in hexes:
        bound, st = resolve_hash(h, rows, expired)'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "b9c504f8":
    sys.exit("not W24 candidate")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("preimage :", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("patched  :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
