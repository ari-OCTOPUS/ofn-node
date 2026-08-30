import os, json, time
mesh="/home/ari/octopus-mesh"
needles=["577b0e22","04af67d5","be612088","cycle_settler","auto_settle","settled"]
out={"now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
out["audit"]=[]
ap=os.path.join(mesh,"audit","audit.jsonl")
if os.path.isfile(ap):
    with open(ap,encoding="utf-8",errors="ignore") as f:
        for line in f:
            if any(n in line for n in needles):
                try:
                    out["audit"].append(json.loads(line))
                except Exception:
                    out["audit"].append({"raw":line[:400]})
# last 8 audit
out["audit_tail"]=out["audit"][-15:]
rp=os.path.join(mesh,"receipts","577b0e22-0904-4ef7-b98b-72b491cb132f.claim.json")
out["receipt_577"]=None
if os.path.isfile(rp):
    out["receipt_577"]=json.load(open(rp,encoding="utf-8"))
# settler state
st=os.path.join(mesh,"state")
out["state_hits"]=[]
if os.path.isdir(st):
    for dp,dns,fns in os.walk(st):
        for fn in fns:
            fp=os.path.join(dp,fn)
            try:
                if os.path.getsize(fp)>3000000:
                    continue
                txt=open(fp,encoding="utf-8",errors="ignore").read(200000)
            except Exception:
                continue
            if any(n in txt or n in fn for n in ["577b0e22","be612088-7154","04af67d5"]):
                rec={"path":fp,"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(fp)))}
                try:
                    rec["data"]=json.loads(txt)
                except Exception:
                    rec["snippet"]=txt[:800]
                out["state_hits"].append(rec)
dest="/tmp/obs138_settle.json"
json.dump(out, open(dest,"w",encoding="utf-8"), indent=2, default=str)
print("WROTE", dest, "audit", len(out["audit"]), "receipt", bool(out["receipt_577"]), "state_hits", len(out["state_hits"]))