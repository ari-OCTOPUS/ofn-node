import os, json, time
needles = ["04af67d5", "be612088", "fresh-e2e-canary-20260827B", "7ae7326a"]
mesh = "/home/ari/octopus-mesh"
out = {"now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "host":"138"}
ap=os.path.join(mesh,"audit","audit.jsonl")
out["audit"]=[]
if os.path.isfile(ap):
    with open(ap,encoding="utf-8",errors="ignore") as f:
        for line in f:
            if any(n in line for n in needles):
                try:
                    out["audit"].append(json.loads(line))
                except Exception:
                    out["audit"].append({"raw":line[:400]})
out["processed_hits"]=[]
pp=os.path.join(mesh,"processed")
if os.path.isdir(pp):
    for fn in os.listdir(pp):
        fp=os.path.join(pp,fn)
        try:
            txt=open(fp,encoding="utf-8",errors="ignore").read(30000)
        except Exception:
            continue
        if any(n in fn or n in txt for n in needles):
            try:
                data=json.loads(txt)
            except Exception:
                data={"raw":txt[:600]}
            out["processed_hits"].append({"path":fp,"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(fp))), "message_type": data.get("message_type") if isinstance(data,dict) else None, "message_id": data.get("message_id") if isinstance(data,dict) else None, "sender": data.get("sender_node") if isinstance(data,dict) else None, "data": data})
out["receipt_hits"]=[]
rp=os.path.join(mesh,"receipts")
if os.path.isdir(rp):
    for fn in os.listdir(rp):
        if any(n in fn for n in needles):
            fp=os.path.join(rp,fn)
            try:
                out["receipt_hits"].append({"path":fp,"data":json.load(open(fp,encoding="utf-8"))})
            except Exception as e:
                out["receipt_hits"].append({"path":fp,"err":str(e)})
vdp=os.path.join(mesh,"state","verify_dispatch_state.json")
out["verify"]=None
if os.path.isfile(vdp):
    try:
        vd=json.load(open(vdp,encoding="utf-8"))
        out["verify"]=vd.get("be612088-7154-45ea-a96b-0d777c7689ff")
    except Exception as e:
        out["verify_err"]=str(e)
dest="/tmp/obs138_focus.json"
with open(dest,"w",encoding="utf-8") as f:
    json.dump(out,f,indent=2,default=str)
print("WROTE", dest, "audit", len(out["audit"]), "proc", len(out["processed_hits"]), "receipts", len(out["receipt_hits"]), "now", out["now_utc"])