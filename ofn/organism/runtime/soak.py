import json, os, time, urllib.request, urllib.error
from pathlib import Path

OUT = Path("/opt/octopus/lab/evidence/SOAK-RESULTS.json")
OUT.parent.mkdir(parents=True, exist_ok=True)
samples = []
abort = None
started = time.time()

def mem_avail():
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
    return -1

def temp():
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read())

def llama_rss():
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/cmdline", "rb") as fh:
                cmd = fh.read().replace(b"\0", b" ").decode(errors="replace")
        except Exception:
            continue
        if "llama-server" in cmd and (
            "-m " in cmd or "--model " in cmd
        ):
            with open(f"/proc/{name}/status") as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]), int(name)
    return -1, -1

def get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status
    except Exception:
        return 0

def post_tiny():
    body = json.dumps({
        "messages": [{"role": "user", "content": "Reply OK"}],
        "max_tokens": 4,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8081/v1/chat/completions",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return {"http": r.status, "ms": int((time.time() - t0) * 1000), "bytes": len(raw)}
    except urllib.error.HTTPError as e:
        return {"http": e.code, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"http": 0, "error": type(e).__name__, "ms": int((time.time() - t0) * 1000)}

def write():
    rsses = [s["llama_rss_kB"] for s in samples if s.get("llama_rss_kB", -1) > 0]
    mems = [s["mem_avail_kB"] for s in samples if s.get("mem_avail_kB", -1) > 0]
    temps = [s["temp_mC"] for s in samples if s.get("temp_mC", -1) > 0]
    payload = {
        "claim_level": "OBSERVED",
        "cap": "NONE_HOUR",
        "safety_stops": ["MemAvailable<350MiB", "thermal_margin<10C", "service_down_streak>=5"],
        "started_at": started,
        "age_seconds": int(time.time() - started),
        "samples": len(samples),
        "running": abort is None,
        "abort": abort,
        "peak_llama_rss_kB": max(rsses) if rsses else None,
        "min_mem_avail_kB": min(mems) if mems else None,
        "peak_temp_mC": max(temps) if temps else None,
        "last": samples[-1] if samples else None,
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(OUT)

down_streak = 0
i = 0
while abort is None:
    rss, pid = llama_rss()
    rec = {
        "t": time.time(),
        "mem_avail_kB": mem_avail(),
        "temp_mC": temp(),
        "llama_rss_kB": rss,
        "llama_pid": pid,
        "health": get("http://127.0.0.1:8081/health"),
        "organism": get("http://127.0.0.1:8090/api/v1/organism"),
    }
    if rec["health"] != 200 or rec["organism"] != 200:
        down_streak += 1
        rec["down_streak"] = down_streak
    else:
        down_streak = 0
    samples.append(rec)
    write()
    if i % 10 == 0:
        rec["tiny"] = post_tiny()
        write()
    if rec["mem_avail_kB"] >= 0 and rec["mem_avail_kB"] < 350 * 1024:
        abort = "mem_available"
    elif rec["temp_mC"] > 0 and (115000 - rec["temp_mC"]) < 10000:
        abort = "thermal"
    elif down_streak >= 5:
        abort = "service_down"
    if abort:
        write()
        break
    i += 1
    time.sleep(60)
