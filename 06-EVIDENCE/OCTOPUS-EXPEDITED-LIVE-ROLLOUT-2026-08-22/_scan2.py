from pathlib import Path
print(Path(r"F:/backup/_ops/loops/pass3_live.py").read_text(encoding="utf-8")[1:4500])
print("---URGENT OUTBOX TAIL---")
p = Path(r"F:/backup/_ops/state/telegram/urgent-outbox.jsonl")
if p.exists():
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    print("n_lines", len(lines))
    for l in lines[-3:]:
        # redact
        import json, hashlib
        try:
            d=json.loads(l)
            safe={k:(hashlib.sha256(str(v).encode()).hexdigest()[:12] if k.lower() in ("chat_id","token","text") else v) for k,v in d.items() if k.lower()!="text"}
            if "text" in d:
                safe["text_sha12"]=hashlib.sha256(str(d["text"]).encode()).hexdigest()[:12]
                safe["text_len"]=len(str(d["text"]))
            print(safe)
        except Exception as e:
            print("parse_err", type(e).__name__)
