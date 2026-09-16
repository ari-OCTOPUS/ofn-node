import os, re
from pathlib import Path

roots = [
    Path(r'F:\backup\_ops\owner-runbook'),
    Path(r'F:\backup\_ops\owner-signing'),
    Path(r'F:\backup\_ops\tools'),
    Path(r'F:\backup\_ops\now_moves'),
    Path(r'F:\backup\_ops\runtime'),
    Path(r'F:\backup\_ops\containment'),
    Path(r'F:\backup\_ops\memory'),
    Path(r'F:\backup\_ops\octopus_v3'),
    Path(r'F:\backup\01-TRUTH'),
    Path(r'F:\backup\02-DECISIONS'),
    Path(r'F:\backup\07-HANDOFF'),
    Path(r'F:\backup\00-INDEX'),
    Path(r'F:\backup\docs'),
    Path(r'F:\backup\08-PLANS'),
    Path(r'F:\backup\06-EVIDENCE\OCTOPUS-INDEPENDENT-VERIFIER-KIT-2026-08-21'),
    Path(r'F:\backup\06-EVIDENCE\OCTOPUS-NEXT-AGENT-HANDOFF-2026-08-21-v2'),
    Path(r'F:\backup\06-EVIDENCE\OCTOPUS-WAVE-B-HANDOFF-2026-08-21'),
    Path(r'F:\backup\06-EVIDENCE\OCTOPUS-PRESERVATION-2026-08-21T2138'),
    Path(r'F:\backup\06-EVIDENCE\OCTOPUS-WAVE-A-2026-08-21'),
]
pat = re.compile(r'root[-_]?v2|make[-_]?root[-_]?v2|CKPT.?348|seq\s*[=:]\s*348|checkpoint\s*[=:]?\s*348|unsigned\s+checkpoint', re.I)
name_pat = re.compile(r'root[-_]?v2|make[-_]?root|ckpt.?348|unsigned', re.I)
skip = {'.mimosa','node_modules','__pycache__','.git','_Archive'}
exts = {'.py','.md','.ps1','.json','.txt','.yaml','.yml','.bat','.toml','.cfg','.ini'}

name_hits=[]; content_hits=[]
for root in roots:
    if not root.exists():
        print('MISS', root); continue
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith('.mimosa')]
        rel = Path(dirpath).relative_to(root)
        if len(rel.parts) > 5:
            dirnames.clear(); continue
        for fn in filenames:
            p = Path(dirpath)/fn
            if name_pat.search(fn):
                name_hits.append(str(p))
            if p.suffix.lower() not in exts: continue
            try:
                if p.stat().st_size > 2_000_000: continue
                text = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if pat.search(text):
                content_hits.append(str(p))

print('NAME_HITS', len(name_hits))
for h in name_hits[:50]: print('N', h)
print('CONTENT_HITS', len(content_hits))
for h in content_hits[:80]: print('C', h)
