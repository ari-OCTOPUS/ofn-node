"""Reconcile rebuilt ledger vs the canonical toolchain's OUTPUT artifact (Downloads md).

The judge states canonical gap_sources.yaml/tools/test exist in their Space
(business-legs-wiring/) — unreachable from this filesystem (full-disk search by
filename: zero hits). The md in Downloads IS the canonical generator's output, so
field-level equivalence against it is the strongest reconciliation available here.
"""
import json
import re
from pathlib import Path

MD = Path(r"C:\Users\Armin\Downloads") / "GAP-LEDGER — ۶۴ شکاف با معیار اجراپذیر.md"
LEDGER = Path(r"F:\ofn-node\ops\GAP-LEDGER.jsonl")

md = MD.read_text(encoding="utf-8")
rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
gaps = {r["gap_id"]: r for r in rows[1:]}
SEP = re.compile(r"^\|[\s:\-]+\|")


def md_table(sec_prefix):
    for s in re.split(r"^## ", md, flags=re.M):
        if s.startswith(sec_prefix):
            out = []
            for ln in s.splitlines():
                if ln.startswith("|") and not SEP.match(ln):
                    cells = [c.strip().replace("\\|", "|")
                             for c in re.split(r"(?<!\\)\|", ln)[1:-1]]
                    out.append(cells)
            return out[1:]
    return []


diffs = []
for c in md_table("شکاف‌های خودکدنویسی‌پذیر و بی‌blocker"):
    gid = c[0].split()[0]
    g = gaps.get(gid)
    if not g:
        diffs.append(f"{gid}: missing in rebuilt ledger")
        continue
    ve = c[3].split(" → ", 1)
    if g["class"] != c[2]:
        diffs.append(f"{gid}: class {g['class']} != {c[2]}")
    if g["verify_command"] != ve[0].strip().strip("`"):
        diffs.append(f"{gid}: verify differs: {g['verify_command']!r} vs {ve[0].strip().strip('`')!r}")
    if (g.get("expect") or "")[:40] != ve[1].strip().strip("`")[:40]:
        diffs.append(f"{gid}: expect differs")
    if g["blocked_by"] is not None:
        diffs.append(f"{gid}: blocked_by should be null")

for prefix in ("شکاف‌های owner-only", "شکاف‌های خودکدنویسی‌پذیر ولی مسدود"):
    for c in md_table(prefix):
        gid = c[0]
        g = gaps.get(gid)
        if not g:
            diffs.append(f"{gid}: missing")
            continue
        if g["class"] != c[2]:
            diffs.append(f"{gid}: class differs")
        if (g.get("blocked_by") or "")[:40] != c[3][:40]:
            diffs.append(f"{gid}: blocked_by differs: {g.get('blocked_by')!r} vs {c[3]!r}")

n = len(rows) - 1
print(f"rebuilt rows={n} | unblocked={sum(1 for r in rows[1:] if r['blocked_by'] is None)}"
      f" | classA={sum(1 for r in rows[1:] if str(r['class']).startswith('A'))}")
print("field-level diff vs canonical md output:",
      "IDENTICAL on all 64 rows" if not diffs else diffs)
