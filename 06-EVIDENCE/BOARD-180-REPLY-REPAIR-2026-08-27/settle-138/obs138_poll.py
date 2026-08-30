import os, json, time
needles = ["be612088", "fresh-e2e-canary-20260827B"]
mesh = "/home/ari/octopus-mesh"
out = {"now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "host":"138"}

def ls(p, n=12):
    if not os.path.isdir(p):
        return {"exists": False}
    items=[]
    names=os.listdir(p)
    for fn in names:
        fp=os.path.join(p,fn)
        try:
            st=os.stat(fp)
            items.append((st.st_mtime, fn, st.st_size))
        except OSError:
            pass
    items.sort(reverse=True)
    return {"exists": True, "count": len(names), "recent":[{"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m)), "name":fn, "size":sz} for m,fn,sz in items[:n]]}

out["processed"]=ls(os.path.join(mesh,"processed"))
out["receipts"]=ls(os.path.join(mesh,"receipts"))
out["inbox"]=ls(os.path.join(mesh,"inbox"))
out["outbox"]=ls(os.path.join(mesh,"outbox"))
# audit matches
ap=os.path.join(mesh,"audit","audit.jsonl")
out["audit"]=[]
if os.path.isfile(ap):
    with open(ap,"r",encoding="utf-8",errors="ignore") as f:
        for line in f:
            if any(n in line for n in needles):
                try:
                    out["audit"].append(json.loads(line))
                except Exception:
                    out["audit"].append({"raw":line[:500]})
# receipts matching
out["receipt_hits"]=[]
rp=os.path.join(mesh,"receipts")
if os.path.isdir(rp):
    for fn in os.listdir(rp):
        fp=os.path.join(rp,fn)
        try:
            txt=open(fp,encoding="utf-8",errors="ignore").read()
        except Exception:
            continue
        if any(n in txt or n in fn for n in needles):
            try:
                out["receipt_hits"].append({"path":fp,"data":json.loads(txt)})
            except Exception:
                out["receipt_hits"].append({"path":fp,"raw":txt[:800]})
# processed matching
out["processed_hits"]=[]
pp=os.path.join(mesh,"processed")
if os.path.isdir(pp):
    for fn in os.listdir(pp):
        if any(n in fn for n in needles):
            fp=os.path.join(pp,fn)
            try:
                out["processed_hits"].append({"path":fp,"data":json.load(open(fp,encoding="utf-8"))})
            except Exception as e:
                out["processed_hits"].append({"path":fp,"err":str(e)})
        else:
            fp=os.path.join(pp,fn)
            try:
                txt=open(fp,encoding="utf-8",errors="ignore").read(20000)
            except Exception:
                continue
            if any(n in txt for n in needles):
                try:
                    out["processed_hits"].append({"path":fp,"data":json.loads(txt)})
                except Exception:
                    out["processed_hits"].append({"path":fp,"raw":txt[:800]})
# verify dispatch key
vdp=os.path.join(mesh,"state","verify_dispatch_state.json")
out["verify_has_run"]=False
out["verify_match"]=None
if os.path.isfile(vdp):
    try:
        vd=json.load(open(vdp,encoding="utf-8"))
        blob=json.dumps(vd,default=str)
        out["verify_has_run"]=any(n in blob for n in needles)
        if isinstance(vd, dict):
            for k,v in vd.items():
                s=json.dumps(v,default=str) if not isinstance(v,str) else v
                if any(n in k or n in s for n in needles):
                    out["verify_match"]={k: v if (not isinstance(v,str) or len(v)<4000) else v[:4000]}
                    break
    except Exception as e:
        out["verify_err"]=str(e)
dest="/tmp/obs138_poll.json"
with open(dest,"w",encoding="utf-8") as f:
    json.dump(out,f,indent=2,default=str)
print("WROTE", dest, "audit", len(out["audit"]), "proc_hits", len(out["processed_hits"]), "receipts", len(out["receipt_hits"]), "verify", out["verify_has_run"], "now", out["now_utc"])