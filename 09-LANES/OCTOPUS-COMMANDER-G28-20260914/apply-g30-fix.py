"""G30 fix: replace the 4 literal 0x08 (backspace) bytes in the G27 producer
artifact with the intended word-boundary escape sequence backslash-b, then scan
the whole file for any remaining control bytes. Byte-exact; preimage kept."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py")
PRE = P.parent / "glass_runner.py.pre-g30"

raw = P.read_bytes()
n = raw.count(b"\x08")
if n != 4:
    sys.exit("ABORT: expected exactly 4 backspace bytes, found %d" % n)
bad = [c for c in raw if c < 0x20 and c != 0x0a]
if any(c != 0x08 for c in bad):
    sys.exit("ABORT: unexpected control bytes: %r" % sorted(set(bad)))
shutil.copy2(P, PRE)
fixed = raw.replace(b"\x08", b"\\b")
ast.parse(fixed.decode("utf-8"))
P.write_bytes(fixed)
left = [c for c in P.read_bytes() if c < 0x20 and c != 0x0a]
print("preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("fixed   :", hashlib.sha256(P.read_bytes()).hexdigest()[:16],
      "remaining-control-bytes:", len(left))
