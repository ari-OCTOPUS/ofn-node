"""G31 fix: the hex-token pattern \\b([a-f0-9]{8,64})\\b can NEVER match a hex
run longer than 64 chars (the trailing word boundary is unreachable inside the
{8,64} cap), so a hash-bearing text with one extra hex char routed to MONEY
(not_b3_shaped) and the B3 bind was silently missed. Fix: keep the LEADING
boundary (no tokens inside words) and drop the trailing one, so a >64 run
yields its 64-char prefix (registry-prefix match or fail-closed long-hash B3).
Byte-exact replace on the staged v2 artifact; preimage kept."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py")
PRE = P.parent / "glass_runner.py.pre-g31"

OLD = '_HEX_PAT = re.compile(r"\\b([a-f0-9]{8,64})\\b", re.I)'
NEW = ('# G31 2026-09-14: no trailing boundary - a hex run longer than 64 chars\n'
       '# must still yield its bounded prefix instead of silently not matching\n'
       '_HEX_PAT = re.compile(r"\\b([a-f0-9]{8,64})", re.I)')

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch")
if old.count(OLD) != 1:
    sys.exit("ABORT: anchor count = %d" % old.count(OLD))
shutil.copy2(P, PRE)
new = old.replace(OLD, NEW)
ast.parse(new)
P.write_bytes(new.encode("utf-8"))
print("preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("fixed   :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
bad = [c for c in P.read_bytes() if c < 0x20 and c != 0x0a]
print("control-bytes:", len(bad))
