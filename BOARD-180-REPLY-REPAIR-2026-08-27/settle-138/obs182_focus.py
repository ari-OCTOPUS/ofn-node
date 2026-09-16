import os, json, time, subprocess, glob
needles = ["04af67d5", "be612088", "fresh-e2e-canary-20260827B", "7ae7326a"]
mesh = "/root/octopus-mesh"
out = {"now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "host":"182"}

def exists(p):
    return os.path.isfile(p) or os.path.isdir(p)

inbox = os.path.join(mesh, "inbox")
names = sorted(os.listdir(inbox)) if os.path.isdir(inbox) else []
pos = None
for i,n in enumerate(names):
    if "04af67d5" in n:
        pos = i
        break
out["inbox_count"] = len(names)
out["inbox_pos_04af67d5"] = pos
out["inbox_name_04af67d5"] = names[pos] if pos is not None else None
out["still_in_inbox"] = pos is not None

# processed / receipts / outbox hits
out["processed_hits"] = []
for root in [os.path.join(mesh,"processed"), os.path.join(mesh,"receipts"), os.path.join(mesh,"outbox"), os.path.join(mesh,"state")]:
    if not os.path.isdir(root):
        continue
    for dp, dns, fns in os.walk(root):
        for fn in fns:
            if any(n in fn for n in needles):
                fp=os.path.join(dp,fn)
                try:
                    txt=open(fp,encoding="utf-8",errors="ignore").read(20000)
                    try:
                        data=json.loads(txt)
                    except Exception:
                        data={"raw":txt[:800]}
                    out["processed_hits"].append({"path":fp,"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(fp))), "data":data})
                except Exception as e:
                    out["processed_hits"].append({"path":fp,"err":str(e)})

# audit lines
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

# last witness cycle evidence
sw=os.path.join(mesh,"state","witness")
out["witness_state"]=[]
if os.path.isdir(sw):
    for fn in sorted(os.listdir(sw)):
        fp=os.path.join(sw,fn)
        try:
            st=os.stat(fp)
            rec={"name":fn,"size":st.st_size,"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))}
            if st.st_size < 8000 and os.path.isfile(fp):
                rec["txt"]=open(fp,encoding="utf-8",errors="ignore").read()
            out["witness_state"].append(rec)
        except Exception:
            pass

# recent receipts/outbox
def recent(p, n=6):
    if not os.path.isdir(p):
        return []
    items=[]
    for fn in os.listdir(p):
        fp=os.path.join(p,fn)
        try:
            st=os.stat(fp)
            items.append((st.st_mtime, fn, st.st_size))
        except OSError:
            pass
    items.sort(reverse=True)
    return [{"mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m)), "name":fn, "size":sz} for m,fn,sz in items[:n]]
out["recent_receipts"]=recent(os.path.join(mesh,"receipts"))
out["recent_outbox"]=recent(os.path.join(mesh,"outbox"))
out["recent_processed"]=recent(os.path.join(mesh,"processed"))

try:
    p=subprocess.run(["systemctl","show","octopus-witness-worker.timer","-p","ActiveState","-p","LastTriggerUSec","-p","NextElapseUSecRealtime"], capture_output=True, text=True, timeout=10)
    out["timer"]=p.stdout
    p=subprocess.run(["systemctl","is-active","octopus-witness-worker.service"], capture_output=True, text=True, timeout=10)
    out["service"]=p.stdout.strip()
    p=subprocess.run(["systemctl","show","octopus-witness-worker.service","-p","Result","-p","ExecMainStatus","-p","ActiveState","-p","InactiveExitTimestamp"], capture_output=True, text=True, timeout=10)
    out["service_show"]=p.stdout
except Exception as e:
    out["timer_err"]=str(e)

# journal last cycle
try:
    p=subprocess.run(["journalctl","-u","octopus-witness-worker.service","-n","40","--no-pager"], capture_output=True, text=True, timeout=15)
    out["journal"]=(p.stdout or "")[-4000:]
except Exception as e:
    out["journal"]=str(e)

dest="/tmp/obs182_focus.json"
with open(dest,"w",encoding="utf-8") as f:
    json.dump(out,f,indent=2,default=str)
print("WROTE", dest, "inbox", out["inbox_count"], "pos", out["inbox_pos_04af67d5"], "still", out["still_in_inbox"], "hits", len(out["processed_hits"]), "audit", len(out["audit"]), "now", out["now_utc"])