import re
from pathlib import Path
t = Path(r"F:\backup\_ops\tests\run_all.py").read_text(encoding="utf-8")
m = re.search(r"TESTS\s*=\s*\[(.*?)\]", t, re.S)
names = re.findall(r'"([^"]+\.py)"', m.group(1)) if m else []
print("n_tests", len(names))
print("first", names[:3])
print("last", names[-3:])
