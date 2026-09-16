"""Acceptance suite for the repaired G8 V3 glass_runner routing."""
import importlib.util
import sys

for p in ("/home/ari/ofn/ofn/budget", "/home/ari/ofn/ofn/agents"):
    sys.path.insert(0, p)

spec = importlib.util.spec_from_file_location(
    "glass_v3", "/home/ari/ofn/state/coding-worker/stage/W24-G8-ROUTING-v3/glass_runner.py")
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except SystemExit:
    pass

KNOWN = ["aabbccdd11223344", "b3cafe42feed0000"]
cases = [
    # (text, expected_route) — hash identifies a registered card
    ("تایید کارت aabbccdd11223344", "B3"),
    ("confirm aabbccdd11223344", "B3"),
    ("b3cafe42feed0000 اوکیه", "B3"),
    # long payload hash (>= _LONG_HASH_MIN) without known match
    ("payload 5f3a1c9e2b7d4068af1c33e59d02b7a4cc88e190", "B3"),
    # bare money words, no hash -> money lane (gated downstream)
    ("بفرست", "MONEY"),
    ("hello there", "MONEY"),
    # empty
    ("", None),
    # hex too short (<8) -> not a token
    ("confirm abc123", "MONEY"),
]
results = []
for text, want in cases:
    r = m._route_owner_message(text, known=KNOWN)
    got = r["route"]
    ok = got == want
    results.append(ok)
    print(("PASS" if ok else "FAIL"), repr(text[:30]), "->", got, f"({r['reason']})", r.get("matched", []))

npass = sum(results)
print(f"ACCEPTANCE {npass}/{len(cases)}")
sys.exit(0 if npass == len(cases) else 1)
