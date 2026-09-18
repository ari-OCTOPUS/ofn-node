"""Apply the G29 bounded fix: deterministic dependency-file resolution in
handle_spool_category (absolute path -> this spool -> executed/ by name).
Preimage: ops_agent.py.pre-g29-20260914. Anchor-count asserted == 1."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
PRE = P.parent / "ops_agent.py.pre-g29-20260914"

OLD = """            for _dep in _deps:
                _dp = Path(_dep) if str(_dep).endswith(".json") else (spool / str(_dep))
                try:
                    _dr = load_json(_dp) or {}
                except OSError:
                    _dr = {}
"""
NEW = """            for _dep in _deps:
                # G29 FIX 2026-09-14: resolve dependency files deterministically:
                # absolute path first, then this spool, then executed/ by name (a
                # retired predecessor). The old CWD-relative resolution could
                # never find a sibling request after it retired to executed/.
                _dp = None
                _cands = ([Path(str(_dep))] if str(_dep).startswith("/")
                          else [spool / str(_dep), _exec / Path(str(_dep)).name])
                for _c in _cands:
                    if _c.exists():
                        _dp = _c
                        break
                if _dp is None:
                    _dr = {}
                else:
                    try:
                        _dr = load_json(_dp) or {}
                    except OSError:
                        _dr = {}
"""

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
if old.count(OLD) != 1:
    sys.exit("ABORT: anchor count = %d" % old.count(OLD))
if "G29 FIX" in old:
    sys.exit("ABORT: fix already present")
shutil.copy2(P, PRE)
new = old.replace(OLD, NEW)
ast.parse(new)
P.write_bytes(new.encode("utf-8"))
print("preimage sha256:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("new sha256:", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
