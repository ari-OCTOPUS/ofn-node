import os, re
from pathlib import Path

roots = [
    Path(r'F:\backup\06-EVIDENCE'),
    Path(r'F:\backup\agent-prompts'),
    Path(r'F:\backup\continuity'),
    Path(r'F:\backup\nervous-system'),
    Path(r'F:\backup\architecture'),
    Path(r'F:\backup\04-SYSTEMS'),
    Path(r'F:\backup\03-GATES'),
    Path(r'F:\backup\_ops\budget'),
    Path(r'F:\backup\_ops\doctor'),
    Path(r'F:\backup\_ops\legs'),
    Path(r'F:\backup\_ops\organs'),
    Path(r'F:\backup\_ops\state\receipts'),
    Path(r'F:\backup\_ops\state\spine'),
    Path(r'F:\backup\_ops\state\export'),
    Path(r'F:\backup\_ops\state\owner-private'),
    Path(os.path.expanduser(r'~\.octopus-signing')),
    Path(r'F:\4d_system'),
]
pat = re.compile(r'root[-_]?v2|make[-_]?root[-_]?v2|CKPT.?348|seq\s*[=:]\s*348\b|checkpoint\s+(seq\s*)?348\b|unsigned\s+checkpoint', re.I)
name_pat = re.compile(r'root[-_]?v2|make[-_]?root|ckpt.?348', re.I)
skip = {'.mimosa','node_modules','__pycache__','.git','_Archive','untracked-source'}
exts = {'.py','.md','.ps1','.json','.txt','.yaml','.yml','.bat','.toml'}

name_hits=[]; content_hits=[]
for root in roots:
    if not root.exists():
        print('MISS', root); continue
    print('SCAN', root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith('.mimosa')]
        try:
            rel = Path(dirpath).relative_to(root)
        except Exception:
            continue
        # keep evidence scan shallow-ish
        maxdepth = 3 if '06-EVIDENCE' in str(root) else 4
        if len(rel.parts) > maxdepth:
            dirnames.clear(); continue
        for fn in filenames:
            p = Path(dirpath)/fn
            if name_pat.search(fn):
                name_hits.append(str(p))
            if p.suffix.lower() not in exts: continue
            try:
                sz = p.stat().st_size
                if sz > 1_500_000: continue
                text = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if pat.search(text):
                content_hits.append(str(p))

print('NAME_HITS', len(name_hits))
for h in name_hits[:40]: print('N', h)
print('CONTENT_HITS', len(content_hits))
for h in content_hits[:100]: print('C', h)
