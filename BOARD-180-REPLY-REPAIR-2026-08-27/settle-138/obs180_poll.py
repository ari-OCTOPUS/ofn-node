import os, json, time, subprocess
needles = ["be612088", "fresh-e2e-canary-20260827B"]
mesh = "/root/octopus-mesh"
out = {"now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "host":"180"}

def ls(p, n=20):
    if not os.path.isdir(p):
        return {"exists": False, "path": p}
    items=[]
    names=os.listdir(p)
    for fn in names:
        fp=os.path.join(p,fn)
        try:
            st=os.stat(fp)
            items.append((st.st_mtime, fn, st.st_size, os.path.isdir(fp)))
        except OSError:
            pass
    items.sort(reverse=True)
    return {"exists": True, "count": len(names), "recent":[{"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m)), "name":fn, "size":sz, "is_dir":d} for m,fn,sz,d in items[:n]]}

def find_needles(root):
    hits=[]
    skip={".git","node_modules","__pycache__"}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in skip]
        for fn in fns:
            fp=os.path.join(dp,fn)
            try:
                sz=os.path.getsize(fp)
            except OSError:
                continue
            if sz>4000000:
                continue
            name_hit = any(n in fn for n in needles)
            txt=""
            try:
                with open(fp,"r",encoding="utf-8",errors="ignore") as f:
                    txt=f.read(250000)
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
                hits.append(rec)
    return hits

out["inbox"]=ls(os.path.join(mesh,"inbox"), 15)
out["processed"]=ls(os.path.join(mesh,"processed"), 15)
out["outbox"]=ls(os.path.join(mesh,"outbox"), 15)
out["receipts"]=ls(os.path.join(mesh,"receipts"), 15)
out["archive"]=ls(os.path.join(mesh,"processed","archive-already-processed-20260827T0231Z"), 20)
out["state"]=ls(os.path.join(mesh,"state"), 20)
out["state_replies"]=ls(os.path.join(mesh,"state","replies"), 20)
out["state_cognition"]=ls(os.path.join(mesh,"state","cognition"), 20)
out["hits"]=find_needles(mesh)
# units
try:
    p=subprocess.run(["systemctl","list-units","--all","--no-pager"], capture_output=True, text=True, timeout=15)
    lines=[ln for ln in (p.stdout or "").splitlines() if any(x in ln.lower() for x in ["octopus","outbox","reply","worker","mesh","cognition","afferent"])]
    out["units"]=lines
except Exception as e:
    out["units"]=[str(e)]
try:
    p=subprocess.run(["systemctl","list-timers","--all","--no-pager"], capture_output=True, text=True, timeout=15)
    lines=[ln for ln in (p.stdout or "").splitlines() if any(x in ln.lower() for x in ["octopus","outbox","reply","worker","mesh","cognition","afferent"])]
    out["timers"]=lines
except Exception as e:
    out["timers"]=[str(e)]
# bin
bn=os.path.join(mesh,"bin")
out["bin"]=sorted(os.listdir(bn)) if os.path.isdir(bn) else []
# outbox sha
op=os.path.join(mesh,"bin","octopus_reply_outbox.py")
if os.path.isfile(op):
    import hashlib
    h=hashlib.sha256()
    with open(op,"rb") as f:
        h.update(f.read())
    out["outbox_sha"]=h.hexdigest()
dest="/tmp/obs180_poll.json"
with open(dest,"w",encoding="utf-8") as f:
    json.dump(out,f,indent=2,default=str)
print("WROTE", dest, "hits", len(out["hits"]), "inbox", out["inbox"].get("count"), "now", out["now_utc"])