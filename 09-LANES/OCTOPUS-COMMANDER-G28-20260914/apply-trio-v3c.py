"""TRIO v3c: _b5_measure must SEE permission errors - pathlib rglob swallows
PermissionError silently, so an unreadable dir measured as 0 bytes (not as
UNKNOWN) - exactly the false-VERIFIED vector the owner mission named. os.walk
with onerror=raise surfaces the error into the existing except-OSError path."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v3-b70f75b3"

OLD = '''            if _p.is_file():
                n = _p.stat().st_size
            elif _p.is_dir():
                for x in _p.rglob("*"):
                    if x.is_file() and not x.is_symlink():
                        n += x.stat().st_size
            per[str(p)] = {"bytes": n, "visible": True}'''
NEW = '''            if _p.is_file():
                n = _p.stat().st_size
            elif _p.is_dir():
                # os.walk+onerror: pathlib rglob SWALLOWS PermissionError, so
                # an unreadable dir would measure as 0 bytes instead of
                # UNKNOWN - that silence is how a read error could masquerade
                # as freed bytes
                def _raise(e):
                    raise e
                for _dp, _dns, _fns in os.walk(_p, onerror=_raise):
                    for _fn in _fns:
                        _fp = Path(_dp) / _fn
                        if _fp.is_file() and not _fp.is_symlink():
                            n += _fp.stat().st_size
            per[str(p)] = {"bytes": n, "visible": True}'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "b70f75b3":
    sys.exit("not v3")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v3 preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v3c        :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
