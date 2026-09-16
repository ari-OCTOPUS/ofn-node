import hashlib, json, os, sys, time, pathlib

LEDGER = pathlib.Path(os.environ.get("OCTOPUS_HOOK_LEDGER", ".cursor/hook-ledger.jsonl"))

def read_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}

def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()

def allow(**kw):
    emit({"permission": "allow", **kw}); sys.exit(0)

def deny(user_message, agent_message=None):
    emit({"permission": "deny", "user_message": user_message,
          "agent_message": agent_message or user_message})
    sys.exit(2)

def append_ledger(record):
    """Append-only hash chain. Each line links to the previous line's hash."""
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    prev = "0" * 64
    if LEDGER.exists():
        with LEDGER.open("rb") as fh:
            last = None
            for line in fh:
                if line.strip():
                    last = line
            if last:
                try:
                    prev = json.loads(last).get("this_hash", prev)
                except Exception:
                    pass
    record = dict(record)
    record["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    record["prev_hash"] = prev
    body = json.dumps(record, sort_keys=True, ensure_ascii=False)
    record["this_hash"] = hashlib.sha256((prev + body).encode("utf-8")).hexdigest()
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
