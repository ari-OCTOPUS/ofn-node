import os, json, time
needles = ["be612088", "fresh-e2e-canary-20260827B"]
roots = ["/home/ari/octopus-mesh"]
hits = []
skip_names = {".git", "node_modules", "__pycache__", "venv", ".venv"}
for root in roots:
    if not os.path.isdir(root):
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_names]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                continue
            if sz > 8000000:
                continue
            name_hit = any(n.lower() in fn.lower() for n in needles)
            content_hit = False
            if not name_hit:
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read(250000)
                    content_hit = any(n in txt for n in needles)
                except Exception:
                    continue
            if name_hit or content_hit:
                hits.append({
                    "path": fp,
                    "size": sz,
                    "mtime": os.path.getmtime(fp),
                    "name_hit": name_hit,
                })
print(json.dumps({"host": "138", "count": len(hits), "hits": hits}, indent=2))