import json, os, time, datetime
RAW = r"F:/backup/COUNCIL_REPORTS/2026-08-16-wave-01/A02_runtime_investigator/raw/heartbeat_obs.jsonl"
TARGETS = [
    r"F:/backup/_ops/state/ORGANISM-STATE.json",
    r"F:/backup/_ops/state/pulse/beat-state.json",
    r"F:/backup/_ops/state/pulse/arbiter-latest.json",
    r"F:/backup/_ops/state/chrono.db-wal",
    r"F:/backup/_ops/state/events.jsonl",
    r"F:/backup/_memory/HEARTBEAT.md",
]
def probe():
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "samples": {}}
    for t in TARGETS:
        try:
            st = os.stat(t)
            item = {"mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"), "size": st.st_size}
            if t.endswith("ORGANISM-STATE.json"):
                try:
                    d = json.load(open(t, encoding="utf-8"))
                    item["beat"] = d.get("beat")
                    item["keys"] = sorted(d.keys())[:40]
                    for k in ("coherence","identity_health","arbiter","pulse","profile"):
                        if k in d: item[k] = d[k] if not isinstance(d[k], dict) else {kk: d[k][kk] for kk in list(d[k])[:8]}
                except Exception as e:
                    item["err"] = str(e)[:80]
            rec["samples"][os.path.basename(t)] = item
        except FileNotFoundError:
            rec["samples"][os.path.basename(t)] = {"missing": True}
    return rec
with open(RAW, "a", encoding="utf-8") as f:
    for i in range(11):
        f.write(json.dumps(probe(), ensure_ascii=False) + "\n")
        f.flush()
        if i < 10: time.sleep(30)
print("sampler done")
