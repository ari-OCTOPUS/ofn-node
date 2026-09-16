import os, json, time, glob, subprocess, hashlib

needles = ["be612088", "fresh-e2e-canary-20260827B"]
mesh = "/root/octopus-mesh"
out = {"now_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

def readp(p, n=200000):
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(n)
    except Exception as e:
        return "ERR:"+str(e)

# state tree
state = os.path.join(mesh, "state")
out["state_walk"] = []
if os.path.isdir(state):
    for dp, dns, fns in os.walk(state):
        for fn in fns:
            fp = os.path.join(dp, fn)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            rec = {"path": fp, "size": st.st_size, "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))}
            txt = readp(fp, 80000)
            rec["has_needle"] = any(n in txt or n in fn for n in needles)
            if rec["has_needle"] or st.st_size < 4000:
                rec["txt"] = txt[:2500]
            out["state_walk"].append(rec)

# receipts/control
rc = os.path.join(mesh, "receipts", "control")
out["receipts_control"] = []
if os.path.isdir(rc):
    for fn in os.listdir(rc):
        fp = os.path.join(rc, fn)
        try:
            st = os.stat(fp)
            txt = readp(fp, 20000)
        except Exception:
            continue
        out["receipts_control"].append({
            "name": fn, "size": st.st_size,
            "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
            "has_needle": any(n in txt or n in fn for n in needles),
            "txt": txt[:1500],
        })

# units
cmds = [
    ["systemctl", "list-units", "--all", "--no-pager", "--type=service"],
    ["systemctl", "list-units", "--all", "--no-pager", "--type=timer"],
    ["systemctl", "list-unit-files", "--no-pager"],
]
out["units"] = {}
for cmd in cmds:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        lines = []
        for line in (p.stdout or "").splitlines():
            low = line.lower()
            if any(x in low for x in ["octopus", "outbox", "reply", "worker", "mesh", "claim", "cognition", "afferent", "witness"]):
                lines.append(line)
        out["units"][" ".join(cmd)] = lines
    except Exception as e:
        out["units"][" ".join(cmd)] = [str(e)]

# bin listing
bn = os.path.join(mesh, "bin")
if os.path.isdir(bn):
    out["bin"] = sorted(os.listdir(bn))

# cognition dir
cog = os.path.join(mesh, "state", "cognition")
out["cognition"] = []
if os.path.isdir(cog):
    for fn in os.listdir(cog):
        fp = os.path.join(cog, fn)
        try:
            st = os.stat(fp)
        except OSError:
            continue
        txt = readp(fp, 50000)
        rec = {"name": fn, "size": st.st_size, "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)), "has_needle": any(n in txt or n in fn for n in needles)}
        if rec["has_needle"] or st.st_size < 3000:
            rec["txt"] = txt[:2000]
        out["cognition"].append(rec)

# replies state
rp = os.path.join(mesh, "state", "replies")
out["state_replies"] = []
if os.path.isdir(rp):
    for dp, dns, fns in os.walk(rp):
        for fn in fns:
            fp = os.path.join(dp, fn)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            txt = readp(fp, 80000)
            rec = {"path": fp, "size": st.st_size, "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)), "has_needle": any(n in txt or n in fn for n in needles)}
            if rec["has_needle"] or st.st_size < 4000:
                rec["txt"] = txt[:2500]
            out["state_replies"].append(rec)

# journal last lines mentioning needles if journalctl works
try:
    p = subprocess.run(["journalctl", "-n", "200", "--no-pager"], capture_output=True, text=True, timeout=20)
    lines = [ln for ln in (p.stdout or "").splitlines() if any(n in ln for n in needles)]
    out["journal_needles"] = lines[-50:]
except Exception as e:
    out["journal_needles"] = [str(e)]

# look for worker pid/logs
for pth in ["/var/log/octopus", "/root/octopus-mesh/logs", "/tmp"]:
    if not os.path.isdir(pth):
        continue
    hits = []
    for fn in os.listdir(pth)[:200]:
        if any(x in fn.lower() for x in ["octopus", "outbox", "reply", "mesh", "canary"]):
            fp = os.path.join(pth, fn)
            try:
                st = os.stat(fp)
                hits.append({"name": fn, "size": st.st_size, "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))})
            except OSError:
                pass
    out["logdir_"+pth] = hits

dest = "/tmp/obs180_deep.json"
with open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)
print("WROTE", dest)