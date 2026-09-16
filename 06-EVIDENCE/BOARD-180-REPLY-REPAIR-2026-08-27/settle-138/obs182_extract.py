import os, json, time, hashlib, subprocess

needles = ["be612088", "fresh-e2e-canary-20260827B", "c3f085a8"]
out = {
    "host": os.uname().nodename,
    "now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "tree": {},
    "hits": [],
    "timer": {},
}

def sha256_file(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

roots = ["/root/octopus-mesh", "/home/ari/octopus-mesh", "/opt/octopus-mesh"]
mesh = None
for r in roots:
    if os.path.isdir(r):
        mesh = r
        break
out["mesh"] = mesh
if mesh:
    out["tree"]["root"] = sorted(os.listdir(mesh))[:80]
    for sub in ["inbox", "processed", "outbox", "pending", "replies", "logs", "receipts", "audit", "state", "runtime"]:
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
                    idx = -1
                    for n in needles:
                        i = txt.find(n)
                        if i >= 0 and (idx < 0 or i < idx):
                            idx = i
                    rec["snippet"] = txt[max(0,idx-150):idx+400] if idx>=0 else txt[:400]
                out["hits"].append(rec)

# witness timer
for cmd, key in [
    (["systemctl", "show", "octopus-witness-worker.timer", "-p", "Id", "-p", "ActiveState", "-p", "Unit", "-p", "Triggers", "-p", "LastTriggerUSec", "-p", "NextElapseUSecRealtime", "-p", "FragmentPath"], "timer_show"),
    (["systemctl", "cat", "octopus-witness-worker.timer"], "timer_cat"),
    (["systemctl", "is-active", "octopus-witness-worker.timer"], "timer_active"),
    (["systemctl", "is-active", "octopus-witness-worker.service"], "service_active"),
    (["systemctl", "show", "octopus-witness-worker.service", "-p", "Id", "-p", "ActiveState", "-p", "FragmentPath", "-p", "ExecStart"], "service_show"),
]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        out["timer"][key] = {"rc": p.returncode, "out": (p.stdout or "")[:5000], "err": (p.stderr or "")[:1000]}
    except Exception as e:
        out["timer"][key] = {"err": str(e)}

# look for max_n in unit files
for path in [
    "/etc/systemd/system/octopus-witness-worker.timer",
    "/etc/systemd/system/octopus-witness-worker.service",
    "/lib/systemd/system/octopus-witness-worker.timer",
    "/lib/systemd/system/octopus-witness-worker.service",
]:
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            out["timer"][path] = f.read()[:4000]

dest = "/tmp/obs182_extract.json"
with open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)
print("WROTE", dest, "hits", len(out["hits"]), "mesh", mesh)