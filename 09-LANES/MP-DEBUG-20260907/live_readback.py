"""Read-only board138 probe; execute via stdin: ssh -o BatchMode=yes -o ConnectTimeout=20 -o ConnectionAttempts=1 board138 "timeout 20s python3 -B -".
No runtime module imports, file writes, arbitrary ledger dumps, or service changes.
Save stdout only on the laptop in the assigned debug lane.
"""
import ast,datetime,hashlib,json,os,socket,subprocess
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def st(x): return {"size_bytes":x.st_size,"inode":x.st_ino,"device":x.st_dev,"mtime_ns":x.st_mtime_ns}
def rev(path):
    p=subprocess.run(["git","-C",path,"rev-parse","HEAD"],capture_output=True,text=True,timeout=4)
    return p.stdout.strip() if p.returncode==0 else "UNKNOWN"
def parse_blob(blob):
    first=last=None
    count=errs=breaks=dups=0
    seen=set()
    target={}
    for n,line in enumerate(blob.splitlines(),1):
        try: row=json.loads(line)
        except Exception:
            errs+=1
            continue
        count+=1
        seq=row.get("seq") if isinstance(row,dict) else None
        if first is None: first=seq
        if not isinstance(seq,int) or isinstance(seq,bool): breaks+=1
        elif last is not None and seq!=last+1: breaks+=1
        if seq in seen: dups+=1
        seen.add(seq);last=seq
        if seq in (194298,194329):
            allowed=("event","reason","reason_code","seq","calib_tail")
            safe={k:row[k] for k in allowed if k in row}
            required=("loaded_source_revision","consumer_path","read_receipt_id","calib_tail","reason_code","mint_evidence")
            mint=row.get("mint_evidence")
            target[str(seq)]={"line":n,"safe_fields":safe,"fields_present":{k:k in row for k in required},"mint_evidence_calib_tail_present":isinstance(mint,dict) and "calib_tail" in mint,"raw_line_sha256":hashlib.sha256(line).hexdigest()}
    return {"line_count":len(blob.splitlines()),"record_count":count,"parse_errors":errs,"first_seq":first,"last_seq":last,"seq_non_increment_breaks":breaks,"seq_duplicates":dups,"ends_newline":blob.endswith(b"\n"),"target_records":target}
out={"schema":"read_only.audit_verification.v2","started_at_utc":now(),"hostname":socket.gethostname(),"loaded_process_revision":"UNKNOWN","runtime_imports":0,"remote_writes_requested":0}
out["repo_heads"]={p:rev(p) for p in ("/home/ari/octopus-mesh","/home/ari/ofn")}
out["service_probe_started_at_utc"]=now()
service=subprocess.run(["systemctl","show","ofn.service","--property=MainPID,WorkingDirectory,ActiveState,SubState,ExecMainStartTimestamp","--no-pager"],capture_output=True,text=True,timeout=4)
out["ofn_service"]={"exit_code":service.returncode,"properties":dict(line.split("=",1) for line in service.stdout.splitlines() if "=" in line),"loaded_source_revision":"UNKNOWN","observed_at_utc":now()}
path="/home/ari/octopus-mesh/audit/audit.jsonl"
read_start=now()
with open(path,"rb") as f:
    pre=os.fstat(f.fileno())
    blob=f.read(pre.st_size)
    post=os.fstat(f.fileno())
out["snapshot"]={"path":path,"read_started_at_utc":read_start,"read_ended_at_utc":now(),"fstat_before":st(pre),"fstat_after":st(post),"path_stat_after":st(os.stat(path)),"read_bytes":len(blob),"complete_initial_bound":len(blob)==pre.st_size,"sha256":hashlib.sha256(blob).hexdigest(),"checks":parse_blob(blob)}
n=30047320
prefix=blob[:n]
out["historical_prefix"]={"requested_bytes":n,"read_bytes":len(prefix),"expected_sha256":"029afbb112400a6b6eefd234c2efdc3b2dd1f9c267a138816f83a09fdc83009c","sha256":hashlib.sha256(prefix).hexdigest(),"checks":parse_blob(prefix)}
out["historical_prefix"]["matches_expected_sha256"]=out["historical_prefix"]["sha256"]==out["historical_prefix"]["expected_sha256"]
out["writer_source"]=[]
for path in ("/home/ari/octopus-mesh/bin/octopus_common.py","/home/ari/octopus-mesh/bin/octomesh_common.py"):
    rec={"path":path}
    if not os.path.isfile(path):
        rec["status"]="NOT_FOUND";out["writer_source"].append(rec);continue
    source=open(path,"rb").read()
    tree=ast.parse(source.decode("utf-8"))
    funcs=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=="audit_append":
            text=ast.get_source_segment(source.decode("utf-8"),node) or ""
            funcs.append({"name":node.name,"line":node.lineno,"end_line":node.end_lineno,"source_sha256":hashlib.sha256(text.encode()).hexdigest(),"contains_sha256":"sha256" in text,"contains_prev_hash":"prev_hash" in text,"contains_flock":"flock" in text,"contains_fsync":"fsync" in text,"contains_sort_keys":"sort_keys" in text})
    rec.update({"status":"READ_SOURCE_ONLY","file_sha256":hashlib.sha256(source).hexdigest(),"functions":funcs})
    out["writer_source"].append(rec)
out["interpretation"]={"historical_prefix_match":"unchanged relative to prior captured fingerprint only; not historic authenticity or tamperproof evidence","seq_continuity":"does not prove a cryptographic hash chain","service_status":"selected service properties only; source HEAD is not loaded process revision"}
out["ended_at_utc"]=now()
print(json.dumps(out,separators=(",",":"),ensure_ascii=True))
