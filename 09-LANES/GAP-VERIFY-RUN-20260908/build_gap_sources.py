"""Build ops/gap_sources.yaml from the canonical Downloads md (64-gap ledger twin).

Source of truth: C:/Users/Armin/Downloads/GAP-LEDGER — ۶۴ شکاف با معیار اجراپذیر.md
(pinned by L6 lane evidence + owner PROMPT-NEXT-1). Transcription is machine-parsed,
not hand-copied. Node mapping documented per section.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

MD = Path(r"C:\Users\Armin\Downloads") / "GAP-LEDGER — ۶۴ شکاف با معیار اجراپذیر.md"
OUT = Path(r"F:\ofn-node\ops\gap_sources.yaml")

rows = []


def parse_table(lines):
    """md table lines -> list of cell lists (| escaped as \\|). Skips header row."""
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        if re.match(r"^\|[\s:-]+\|", ln) and set(ln.replace("|", "").strip()) <= set("-: "):
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", ln)[1:-1]]
        out.append(cells)
    return out[1:]  # drop header row


text = MD.read_text(encoding="utf-8")
sections = re.split(r"^## ", text, flags=re.M)[1:]
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

for sec in sections:
    table = parse_table(sec.splitlines())
    if sec.startswith("شکاف‌های خودکدنویسی‌پذیر و بی‌blocker"):
        for c in table:
            gid, title, klass = c[0], c[1], c[2]
            verify_expect = c[3]
            parts = verify_expect.split(" → ", 1)
            verify = parts[0].strip().strip("`")
            expect = parts[1].strip().strip("`") if len(parts) > 1 else ""
            rows.append({
                "gap_id": gid.split()[0], "title": re.sub(r"🐙", "", title).strip(),
                "node": "138", "class": klass,
                "blocked_by": None,
                "verify_command": verify, "expect": expect,
                "canary": "🐙" in gid,
                "evidence": "canonical md twin (Downloads), machine-parsed",
                "updated_at_utc": now,
            })
    elif sec.startswith("شکاف‌های owner-only"):
        for c in table:
            gid, title, klass, blocked = c[0], c[1], c[2], c[3]
            rows.append({
                "gap_id": gid, "title": title, "node": "unassigned", "class": klass,
                "blocked_by": blocked, "verify_command": None, "expect": None,
                "canary": False,
                "evidence": "canonical md twin (Downloads), machine-parsed",
                "updated_at_utc": now,
            })
    elif sec.startswith("شکاف‌های خودکدنویسی‌پذیر ولی مسدود"):
        for c in table:
            gid, title, klass, blocked = c[0], c[1], c[2], c[3]
            rows.append({
                "gap_id": gid, "title": title, "node": "138", "class": klass,
                "blocked_by": blocked, "verify_command": None, "expect": None,
                "canary": False,
                "evidence": "canonical md twin (Downloads), machine-parsed",
                "updated_at_utc": now,
            })

ids = [r["gap_id"] for r in rows]
assert len(rows) == 64, f"expected 64 rows, got {len(rows)}"
assert len(set(ids)) == 64, "duplicate gap ids"
unblocked = [r for r in rows if r["blocked_by"] is None]
assert len(unblocked) == 29, f"expected 29 unblocked, got {len(unblocked)}"

meta = {
    "_meta": {
        "schema": "octopus.gap_sources.v1",
        "source_md": str(MD),
        "source_md_sha256": __import__("hashlib").sha256(MD.read_bytes()).hexdigest(),
        "node_mapping_note": "all 29 land verifies execute on 138's ~/ofn (live ofn checkout); mesh rows target 180 via --node flags; zero writes to any node",
        "generated_at_utc": now,
    }
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(yaml.safe_dump({**meta, "gaps": rows}, allow_unicode=True, sort_keys=False),
               encoding="utf-8")
print(f"wrote {OUT} — rows={len(rows)} unblocked={len(unblocked)} canaries=",
      [r["gap_id"] for r in rows if r.get("canary")])
