"""Repair literal 0x08 backspace bytes in the staged G8 V3 glass_runner.

The patch generator emitted JSON-escaped \\b which decoded to real backspace
bytes inside the r"..." pattern strings, so _HEX_PAT and _CONFIRM_PAT match
nothing at runtime. Replace each 0x08 byte with the two-character sequence
backslash + b, then recompile and print the new sha.
"""
import hashlib
import py_compile
from pathlib import Path

P = Path("/home/ari/ofn/state/coding-worker/stage/W24-G8-ROUTING-v3/glass_runner.py")

raw = P.read_bytes()
bs = b"\x08"                      # single backspace byte
seq = b"\\" + b"b"                # backslash + 'b', two bytes
n = raw.count(bs)
fixed = raw.replace(bs, seq)
P.write_bytes(fixed)
py_compile.compile(str(P), doraise=True)

after = P.read_bytes()
print(f"replaced={n} bs_before={n} bs_after={after.count(bs)}")
print("new_sha256=" + hashlib.sha256(after).hexdigest())
assert after.count(bs) == 0, "backspace bytes remain"
print("REPAIR_OK")
