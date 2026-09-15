"""Inspect the retirefix hunk vs TRIO changes around it."""
import difflib
from pathlib import Path

BASE = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py.baseline-109e68c0").read_text().splitlines()
ART = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py").read_text().splitlines()
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py").read_text().splitlines()

rl = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in
      difflib.SequenceMatcher(None, BASE, LIVE, autojunk=False).get_opcodes() if tag != "equal"]
tl = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in
      difflib.SequenceMatcher(None, BASE, ART, autojunk=False).get_opcodes() if tag != "equal"]

print("RETREFIX ops (base->live):", rl)
print("nearest TRIO ops:", [t for t in tl if abs(t[0] - rl[0][0]) < 40])
i1, i2, j1, j2 = rl[0]
print("\n--- BASE lines", i1 - 2, "..", i2 + 1)
for n in range(max(0, i1 - 2), min(len(BASE), i2 + 2)):
    print(f"B{n:4}", BASE[n])
print("\n--- LIVE lines", j1 - 2, "..", j2 + 1)
for n in range(max(0, j1 - 2), min(len(LIVE), j2 + 2)):
    print(f"L{n:4}", LIVE[n])
