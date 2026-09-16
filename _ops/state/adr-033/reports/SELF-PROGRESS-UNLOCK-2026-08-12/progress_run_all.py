from pathlib import Path
import re
t = Path(r"C:\Users\Armin\.cursor\projects\f-backup\terminals\70531.txt").read_text(encoding="utf-8", errors="replace")
blocks = re.findall(r"test_[a-z0-9_]+\.py", t)
print("py mentions", len(set(blocks)), "unique of", len(blocks))
print("FAIL lines", sum(1 for l in t.splitlines() if "FAIL" in l and "test_" in l))
print("tail:")
print("\n".join(t.splitlines()[-15:]))
print("has_exit", "exit_code:" in t)
