import os, json, time, hashlib, glob

needles = ["be612088", "fresh-e2e-canary-20260827B"]
out = {"host":"138", "now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "audit": [], "receipts": [], "verify_dispatch": None, "recent_processed": [], "related_processed": []}

# audit lines
ap = "/home/ari/octopus-mesh/audit/audit.jsonl"
if os.path.isfile(ap):
    with open(ap, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if any(n in line for n in needles):
                try:
                    out["audit"].append(json.loads(line))
                except Exception:
                    out["audit"].append({"_raw": line[:2000]})

# receipts matching
rp = "/home/ari/octopus-mesh/receipts"
if os.path.isdir(rp):
    for fn in os.listdir(rp):
        fp = os.path.join(rp, fn)
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
        except Exception:
            continue
        if any(n in txt or n in fn for n in needles):
            try:
                out["receipts"].append({"path": fp, "data": json.loads(txt)})
            except Exception:
                out["receipts"].append({"path": fp, "raw": txt[:4000]})

# verify dispatch
vdp = "/home/ari/octopus-mesh/state/verify_dispatch_state.json"
if os.path.isfile(vdp):
    try:
        with open(vdp, "r", encoding="utf-8") as f:
            vd = json.load(f)
        # extract matching keys/entries
        if isinstance(vd, dict):
            matched = {}
            # keep top-level scalars
            for k,v in vd.items():
                if not isinstance(v, (dict, list)):
                    matched[k] = v
            # search nested
            def hunt(obj, path="$"):
                found = []
                if isinstance(obj, dict):
                    blob = json.dumps(obj, default=str)
                    if any(n in blob for n in needles):
                        found.append((path, obj if len(blob)<8000 else {"_keys": list(obj.keys()), "_size": len(blob)}))
                    for k,v in obj.items():
                        found.extend(hunt(v, path+"."+str(k)))
                elif isinstance(obj, list):
                    for i,v in enumerate(obj):
                        found.extend(hunt(v, path+"[%d]"%i))
                elif isinstance(obj, str) and any(n in obj for n in needles):
                    found.append((path, obj))
                return found
            out["verify_dispatch"] = {"top": matched, "matches": hunt(vd)[:40], "keys": list(vd.keys())[:50]}
        else:
            out["verify_dispatch"] = vd
    except Exception as e:
        out["verify_dispatch"] = {"err": str(e)}

# recent processed last 20 by mtime + any content match
pp = "/home/ari/octopus-mesh/processed"
files = []
if os.path.isdir(pp):
    for fn in os.listdir(pp):
        fp = os.path.join(pp, fn)
        try:
            st = os.stat(fp)
        except OSError:
            continue
        files.append((st.st_mtime, fp, st.st_size))
files.sort(reverse=True)
for mt, fp, sz in files[:25]:
    rec = {"path": fp, "size": sz, "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mt))}
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read(8000)
        rec["has_needle"] = any(n in txt for n in needles)
        try:
            rec["data"] = json.loads(txt)
        except Exception:
            rec["raw"] = txt[:1500]
    except Exception as e:
        rec["err"] = str(e)
    out["recent_processed"].append(rec)

# all processed containing needles
for mt, fp, sz in files:
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read(20000)
    except Exception:
        continue
    if any(n in txt or n in os.path.basename(fp) for n in needles):
        try:
            data = json.loads(txt)
        except Exception:
            data = {"_raw": txt[:2000]}
        out["related_processed"].append({
            "path": fp,
            "size": sz,
            "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mt)),
            "data": data,
        })

# also check runtime, tasks, processing, quarantine
for extra in [
    "/home/ari/octopus-mesh/runtime",
    "/home/ari/octopus-mesh/processing",
    "/home/ari/octopus-mesh/quarantine",
    "/home/ari/octopus-mesh/rejected",
    "/home/ari/octopus-mesh/tasks",
]:
    if not os.path.isdir(extra):
        continue
    extra_hits = []
    for dirpath, dirnames, filenames in os.walk(extra):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 5000000:
                    continue
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read(200000)
            except Exception:
                continue
            if any(n in txt or n in fn for n in needles):
                extra_hits.append({"path": fp, "size": os.path.getsize(fp), "snippet": txt[:500]})
    out[extra] = extra_hits

dest = "/tmp/obs138_extract.json"
with open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)
print("WROTE", dest, "audit", len(out["audit"]), "receipts", len(out["receipts"]), "related", len(out["related_processed"]))