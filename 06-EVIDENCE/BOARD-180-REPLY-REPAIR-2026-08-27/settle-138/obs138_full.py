import os, json, time, glob, hashlib, subprocess

needles = ["be612088", "fresh-e2e-canary-20260827B", "AUTOWAKE-PROBE-FRESH-EVENT"]
skip_names = {".git", "node_modules", "__pycache__", "venv", ".venv"}

def walk_hits(root, extra_needles=None):
    ns = list(needles)
    if extra_needles:
        ns.extend(extra_needles)
    hits = []
    if not os.path.isdir(root):
        return [{"error": "missing_root", "root": root}]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_names]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(fp)
                mt = os.path.getmtime(fp)
            except OSError:
                continue
            if sz > 12000000:
                continue
            name_hit = any(n.lower() in fn.lower() for n in ns)
            content_hit = False
            snippet = ""
            if sz < 4000000:
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read(400000)
                    content_hit = any(n in txt for n in ns)
                    if content_hit or name_hit:
                        # keep a short snippet around first needle
                        idx = -1
                        for n in ns:
                            i = txt.find(n)
                            if i >= 0 and (idx < 0 or i < idx):
                                idx = i
                        if idx >= 0:
                            snippet = txt[max(0, idx-120):idx+220]
                except Exception:
                    pass
            if name_hit or content_hit:
                hits.append({
                    "path": fp,
                    "size": sz,
                    "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mt)),
                    "name_hit": name_hit,
                    "content_hit": content_hit,
                    "snippet": snippet[:400],
                })
    return hits

def listdir_brief(path, limit=80):
    if not os.path.isdir(path):
        return {"exists": False, "path": path}
    items = []
    try:
        names = sorted(os.listdir(path))
    except OSError as e:
        return {"exists": True, "path": path, "error": str(e)}
    for name in names[-limit:]:
        fp = os.path.join(path, name)
        try:
            st = os.stat(fp)
            items.append({
                "name": name,
                "is_dir": os.path.isdir(fp),
                "size": st.st_size,
                "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
            })
        except OSError:
            items.append({"name": name, "error": "stat"})
    return {"exists": True, "path": path, "count": len(names), "items": items}

def read_json_if(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return {"_raw": f.read(20000), "_err": str(e)}
        except Exception as e2:
            return {"_err": str(e2)}

def sha256_file(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

out = {
    "host": os.uname().nodename if hasattr(os, "uname") else "?",
    "now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "tree": {},
    "hits": [],
    "key_files": {},
    "sha": {},
}

# 138 layout
roots = [
    "/home/ari/octopus-mesh",
    "/home/ari/octopus-mesh/processed",
    "/home/ari/octopus-mesh/receipts",
    "/home/ari/octopus-mesh/audit",
    "/home/ari/octopus-mesh/inbox",
    "/home/ari/octopus-mesh/outbox",
    "/home/ari/octopus-mesh/pending",
    "/home/ari/octopus-mesh/replies",
    "/home/ari/octopus-mesh/logs",
]
for r in [
    "/home/ari/octopus-mesh",
]:
    if os.path.isdir(r):
        out["tree"][r] = sorted(os.listdir(r))[:80]

for r in [
    "/home/ari/octopus-mesh/processed",
    "/home/ari/octopus-mesh/receipts",
    "/home/ari/octopus-mesh/audit",
    "/home/ari/octopus-mesh/inbox",
    "/home/ari/octopus-mesh/outbox",
    "/home/ari/octopus-mesh/pending",
    "/home/ari/octopus-mesh/replies",
    "/home/ari/octopus-mesh/logs",
    "/home/ari/octopus-mesh/state",
]:
    out["tree"][r] = listdir_brief(r, 40)

out["hits"] = walk_hits("/home/ari/octopus-mesh")

# also list known processed file
known = "/home/ari/octopus-mesh/processed/2026-08-27T02-27-28.246898Z__be612088-7154-45ea-a96b-0d777c7689ff.json"
out["key_files"][known] = read_json_if(known)

print(json.dumps(out, indent=2, default=str))