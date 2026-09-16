import os, json, time, hashlib, glob, subprocess

needles = ["be612088", "fresh-e2e-canary-20260827B", "inject_send_failure", "frozen_prediction"]
out = {
    "host": os.uname().nodename,
    "now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "tree": {},
    "hits": [],
    "outbox_py_sha": None,
    "key_files": {},
    "systemctl": {},
}

def sha256_file(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# find mesh root
roots = ["/root/octopus-mesh", "/home/ari/octopus-mesh", "/opt/octopus-mesh"]
mesh = None
for r in roots:
    if os.path.isdir(r):
        mesh = r
        break
out["mesh"] = mesh
if mesh:
    out["tree"]["root"] = sorted(os.listdir(mesh))[:80]
    for sub in ["pending", "outbox", "replies", "processed", "logs", "inbox", "receipts", "audit", "state", "runtime"]:
        p = os.path.join(mesh, sub)
        if not os.path.isdir(p):
            out["tree"][sub] = {"exists": False}
            continue
        items = []
        try:
            names = os.listdir(p)
        except OSError as e:
            out["tree"][sub] = {"exists": True, "err": str(e)}
            continue
        for fn in names:
            fp = os.path.join(p, fn)
            try:
                st = os.stat(fp)
                items.append((st.st_mtime, {"name": fn, "size": st.st_size, "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)), "is_dir": os.path.isdir(fp)}))
            except OSError:
                pass
        items.sort(reverse=True)
        out["tree"][sub] = {"exists": True, "count": len(names), "recent": [x[1] for x in items[:30]]}

    # walk for needles
    skip = {".git","node_modules","__pycache__","venv",".venv"}
    for dirpath, dirnames, filenames in os.walk(mesh):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                continue
            if sz > 8000000:
                continue
            name_hit = any(n.lower() in fn.lower() for n in needles)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read(400000)
            except Exception:
                continue
            if name_hit or any(n in txt for n in needles):
                rec = {"path": fp, "size": sz, "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(fp))), "name_hit": name_hit}
                try:
                    rec["data"] = json.loads(txt)
                except Exception:
                    # find snippet
                    idx = -1
                    for n in needles:
                        i = txt.find(n)
                        if i >= 0 and (idx < 0 or i < idx):
                            idx = i
                    rec["snippet"] = txt[max(0,idx-150):idx+400] if idx>=0 else txt[:400]
                out["hits"].append(rec)

    # outbox.py sha
    for cand in [
        os.path.join(mesh, "outbox.py"),
        os.path.join(mesh, "bin", "outbox.py"),
        os.path.join(mesh, "runtime", "outbox.py"),
    ]:
        if os.path.isfile(cand):
            out["outbox_py_candidates"] = out.get("outbox_py_candidates", [])
            out["outbox_py_candidates"].append({"path": cand, "sha256": sha256_file(cand)})
    # search for outbox.py
    found_outbox = []
    for dirpath, dirnames, filenames in os.walk(mesh):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if fn == "outbox.py" or "outbox" in fn.lower() and fn.endswith(".py"):
                fp = os.path.join(dirpath, fn)
                found_outbox.append({"path": fp, "sha256": sha256_file(fp), "size": os.path.getsize(fp)})
    out["outbox_py_all"] = found_outbox

# journal / logs mention
for cmd, key in [
    (["systemctl", "is-active", "octopus-mesh"], "mesh_active"),
    (["systemctl", "list-units", "--type=service", "--all", "--no-pager"], "units"),
]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        out["systemctl"][key] = (p.stdout or "")[:4000]
    except Exception as e:
        out["systemctl"][key] = str(e)

dest = "/tmp/obs180_extract.json"
with open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)
print("WROTE", dest, "hits", len(out["hits"]), "mesh", mesh)