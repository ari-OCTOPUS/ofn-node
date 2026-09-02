import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, allow, deny, append_ledger

BLOCK = [
    (re.compile(r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b"), "Recursive force delete is forbidden. Archive to 99-ARCHIVE/ instead."),
    (re.compile(r"\bgit\s+(reset\s+--hard|clean\s+-[a-zA-Z]*f|push\s+--force|filter-branch)"), "Destructive git operation is forbidden."),
    (re.compile(r"\b(mkfs|dd\s+if=|shred|truncate\s+-s\s*0)\b"), "Disk-destructive command is forbidden."),
    (re.compile(r"\bchmod\s+777\b"), "World-writable permissions are forbidden."),
    (re.compile(r"(DROP|TRUNCATE)\s+(TABLE|DATABASE)", re.I), "Destructive SQL is forbidden."),
    (re.compile(r"\bpytest\b.*\b(-p\s+no:cacheprovider)?.*--no-header.*-q\s*$"), None),
]

cmd = (read_input().get("command") or "")
for rx, msg in BLOCK:
    if msg and rx.search(cmd):
        append_ledger({"kind": "destructive_denied", "command": cmd[:400], "reason": msg})
        from _common import deny as d
        d(msg, msg)
allow()
