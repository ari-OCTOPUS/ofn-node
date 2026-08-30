import os, json, time, subprocess
needles = ["be612088", "fresh-e2e-canary-20260827B"]
mesh = "/root/octopus-mesh"
out = {"now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "host":"182"}

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

out["inbox"]=ls(os.path.join(mesh,"inbox"))
out["processed"]=ls(os.path.join(mesh,"processed"))
out["outbox"]=ls(os.path.join(mesh,"outbox"))
out["receipts"]=ls(os.path.join(mesh,"receipts"))
out["hits"]=[]
skip={".git","__pycache__"}
for dp, dns, fns in os.walk(mesh):
    dns[:] = [d for d in dns if d not in skip]
    for fn in fns:
        fp=os.path.join(dp,fn)
        try:
            sz=os.path.getsize(fp)
        except OSError:
            continue
        if sz>4000000:
            continue
        name_hit=any(n in fn for n in needles)
        try:
            txt=open(fp,encoding="utf-8",errors="ignore").read(250000)
        except Exception:
            continue
        if name_hit or any(n in txt for n in needles):
            rec={"path":fp,"size":sz,"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(fp)))}
            try:
                rec["data"]=json.loads(txt)
            except Exception:
                i=-1
                for n in needles:
                    j=txt.find(n)
                    if j>=0 and (i<0 or j<i):
                        i=j
                rec["snippet"]=txt[max(0,i-80):i+300]
            out["hits"].append(rec)
# leftover check
out["leftover_c3f085a8_inbox"]=os.path.isfile(os.path.join(mesh,"inbox","2026-08-27T01-52-35.817302Z__c3f085a8-0a65-4849-9432-29deeaf1b652.json"))
try:
    p=subprocess.run(["systemctl","show","octopus-witness-worker.timer","-p","ActiveState","-p","LastTriggerUSec","-p","NextElapseUSecRealtime"], capture_output=True, text=True, timeout=10)
    out["timer"]=p.stdout
    p=subprocess.run(["systemctl","is-active","octopus-witness-worker.service"], capture_output=True, text=True, timeout=10)
    out["service"]=p.stdout.strip()
except Exception as e:
    out["timer_err"]=str(e)
# max_n in worker
wp="/root/octopus-mesh/bin/octopus_witness_worker.py"
out["max_n_mentions"]=[]
if os.path.isfile(wp):
    txt=open(wp,encoding="utf-8",errors="ignore").read()
    for i,line in enumerate(txt.splitlines(),1):
        if "max_n" in line or "MAX_N" in line or "max-n" in line:
            out["max_n_mentions"].append({"line":i,"txt":line.strip()[:200]})
dest="/tmp/obs182_poll.json"
with open(dest,"w",encoding="utf-8") as f:
    json.dump(out,f,indent=2,default=str)
print("WROTE", dest, "hits", len(out["hits"]), "leftover_c3", out["leftover_c3f085a8_inbox"], "now", out["now_utc"])