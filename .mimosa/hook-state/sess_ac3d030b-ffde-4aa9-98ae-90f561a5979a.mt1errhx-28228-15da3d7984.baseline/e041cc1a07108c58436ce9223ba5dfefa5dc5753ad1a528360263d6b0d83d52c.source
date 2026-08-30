import json, re, subprocess, datetime
CAP = r"F:/backup/06-EVIDENCE/F1-191-20260818-2122"
KW1 = ["octopus","4d","heartbeat","bridge","telegram","emit_cycle","daemon","sensorium","feet","backup"]
KW2 = ["python","node","ssh","wireguard","tailscale","cloudflared"]
def load_ports(f):
    ports={}
    for line in open(f, encoding="utf-8", errors="replace"):
        m=re.match(r"\s*([\d\.:a-fA-F]+)\s+(\d+)\s+(\d+)", line)
        if m: ports.setdefault(int(m.group(3)),[]).append(f"{m.group(1)}:{m.group(2)}")
    return ports
tp=load_ports(f"{CAP}/01b-listen-tcp.txt"); up=load_ports(f"{CAP}/01c-listen-udp.txt")
procs=json.load(open(f"{CAP}/01-process-all.json", encoding="utf-8", errors="replace"))
if isinstance(procs,dict): procs=[procs]
now=datetime.datetime.now()
rows=[]
for p in procs:
    exe=(p.get("ExecutablePath") or ""); cmd=(p.get("CommandLine") or "")
    hay=(exe+" "+cmd).lower()
    tier=0
    if any(k in hay for k in KW1): tier=1
    elif any(k in hay for k in KW2): tier=2
    if not tier: continue
    if tier==2 and not any(k in hay for k in KW1) and "f:\backup" not in hay and "f:/backup" not in hay:
        tier=2
    cd=p.get("CreationDate"); up_str="UNKNOWN"
    if cd:
        try:
            if str(cd).startswith("/Date("):
                dt=datetime.datetime.fromtimestamp(int(str(cd)[6:-2])/1000)
            elif "/" in str(cd)[:3] or re.match(r"\d{14}", str(cd)):
                dt=datetime.datetime(year=int(cd[0:4]),month=int(cd[4:6]),day=int(cd[6:8]),hour=int(cd[8:10]),minute=int(cd[10:12]),second=int(cd[12:14]))
            else:
                dt=datetime.datetime.fromisoformat(str(cd).replace("Z","+00:00"))
            d=now-dt; up_str=f"{d.days}d{d.seconds//3600}h{(d.seconds%3600)//60}m"
        except Exception: up_str="PARSE_FAIL:"+str(cd)[:25]
    pid=p.get("ProcessId"); ports=",".join(tp.get(pid,[])+up.get(pid,[])) or "-"
    m=re.search(r'[A-Za-z]:[\/][^\s"]+\.(py|js|ts|json|yaml|md)', cmd)
    script=m.group(0) if m else "-"
    import os
    sexists="YES" if script!="-" and os.path.exists(script) else ("-" if script=="-" else "NO")
    rows.append((tier,pid,p.get("ParentProcessId"),exe,cmd[:160],up_str,ports,script,sexists))
rows.sort(key=lambda r:(r[0], -(r[2] or 0)))
with open(f"{CAP}/01d-process-filtered.tsv","w",encoding="utf-8") as f:
    f.write("tier\tpid\tppid\texe\tcmd(160)\tuptime\tports\tscript\tscript_exists\n")
    for r in rows: f.write("\t".join(str(x) for x in r)+"\n")
print(f"filtered_rows={len(rows)} tier1={sum(1 for r in rows if r[0]==1)} tier2={sum(1 for r in rows if r[0]==2)}")
