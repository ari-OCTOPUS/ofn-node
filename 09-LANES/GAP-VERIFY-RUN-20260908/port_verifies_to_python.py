"""JUDGE step-4: port the 18 jq/rg-dependent verify commands to pure python3
(no jq/rg needed on 138 — python3 exists). Same semantics, zero node mutation.

- Edits MY gap_sources.yaml (verify_command replaced, original preserved in
  verify_command_original), regenerates the ledger, re-runs the 18 rows
  read-only on 138, appends v2 rows to GAP-VERIFY-RESULTS-20260908.jsonl.
- Also fixes the write-pattern false positive (GAP-005's `>0` comparison).
"""
import base64
import json
import re
import subprocess
import time
from pathlib import Path

import yaml

OPS = Path(r"F:\ofn-node\ops")
SRC = OPS / "gap_sources.yaml"
RESULTS = OPS / "GAP-VERIFY-RESULTS-20260908.jsonl"
LANE = Path(r"F:\backup\09-LANES\GAP-VERIFY-RUN-20260908")

PY = "python3"
PORTS = {
    "GAP-002": f"{PY} -m tools.mesh_audit --node 180 --json | {PY} -c \"import json,sys;d=json.load(sys.stdin);print(len([x for x in d.get('outbox',[]) if x.get('ttl') is None]))\"",
    "GAP-004": f"{PY} -m tools.dual_outbox_verify --json | {PY} -c \"import json,sys;print(json.load(sys.stdin).get('status'))\"",
    "GAP-005": f"{PY} -m tools.skip_table --explain --json | {PY} -c \"import json,sys;e=json.load(sys.stdin).get('entries',[]);print(len(e)>0 and all(x.get('reason') is not None for x in e))\"",
    "GAP-006": f"{PY} -m tools.queue_audit --batch 18 --json | {PY} -c \"import json,sys;print(json.load(sys.stdin).get('deployed'))\"",
    "GAP-009": f"{PY} -m tools.pulse --dry-run | {PY} -c \"import sys;print(sys.stdin.read().count('دکتر:'))\"",
    "GAP-010": f"{PY} -c \"import pathlib;p='OWNER-QUEUE';fs=list(pathlib.Path('tools').rglob('*.py'))+list(pathlib.Path('ofn').rglob('*.py'));print(sum(1 for f in fs if p in f.read_text(encoding='utf-8',errors='ignore')))\"",
    "GAP-011": f"{PY} -c \"import pathlib;p='SILENT_FLIP';fs=[pathlib.Path('tools/pulse.py')]+(list(pathlib.Path('ofn/adapters').rglob('*.py')) if pathlib.Path('ofn/adapters').exists() else []);print(sum(1 for f in fs if f.exists() and p in f.read_text(encoding='utf-8',errors='ignore')))\"",
    "GAP-012": f"{PY} -m tools.learning_feeder --dry-run --json | {PY} -c \"import json,sys;print(json.load(sys.stdin).get('runs_written'))\"",
    "GAP-015": f"{PY} -c \"import pathlib;p='board_events';fs=list(pathlib.Path('ofn').rglob('*.py'))+list(pathlib.Path('tools').rglob('*.py'));print(sum(1 for f in fs if p in f.read_text(encoding='utf-8',errors='ignore')))\"",
    "GAP-017": f"{PY} -m tools.doctor --json | {PY} -c \"import json,sys;d=json.load(sys.stdin);print(len([u for u in d.get('units',[]) if u.get('type')=='oneshot' and u.get('status')=='UNKNOWN']))\"",
    "GAP-018": f"{PY} -m tools.doctor --check imap --json | {PY} -c \"import json,sys;print(json.load(sys.stdin).get('status'))\"",
    "GAP-022": f"{PY} -m tools.homeostat --json | {PY} -c \"import json,sys;d=json.load(sys.stdin);print(len([s for s in d.get('signals',[]) if s.get('source') is None and s.get('zone')!='WISHLIST']))\"",
    "GAP-033": f"{PY} -m tools.verify_chain --from-zero --json | {PY} -c \"import json,sys;print(json.load(sys.stdin).get('status'))\"",
    "GAP-040": f"{PY} -m tools.counters --json | {PY} -c \"import json,sys;d=json.load(sys.stdin);print(','.join(str(d.get(k)) for k in ('EXTERNAL_ACTIONS','NEW_LAN_LISTENERS','MAY_AUTHORIZE')))\"",
    "GAP-050": f"{PY} -m tools.queue_audit --ids 1515,1516,1517 --json | {PY} -c \"import json,sys;d=json.load(sys.stdin);print(len([x for x in (d if isinstance(d,list) else d.get('items',[])) if x.get('root_cause') is None]))\"",
    "GAP-053": f"{PY} -m tools.runway --json | {PY} -c \"import json,sys;d=json.load(sys.stdin);print(str(d.get('runway_days'))+','+str(d.get('source')))\"",
    "GAP-054": f"{PY} -m tools.treasury --json | {PY} -c \"import json,sys;print(json.load(sys.stdin).get('ato_reserve_ratio'))\"",
    "GAP-056": f"{PY} -m tools.gate_check --gate 4 --json | {PY} -c \"import json,sys;print(json.load(sys.stdin).get('status'))\"",
}

WRITE_PATTERNS = re.compile(
    r">>|>(?=\s|/|&)|\btee\b|\brm\b|\bmv\b|\bcp\b|\bcurl\b|\bwget\b|\bgit push\b|\bpip\b|\bapt\b|\bsystemctl\b|--write\b")


def main():
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    for g in data["gaps"]:
        if g["gap_id"] in PORTS:
            g["verify_command_original"] = g["verify_command"]
            g["verify_command"] = PORTS[g["gap_id"]]
            g["updated_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    SRC.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # regenerate ledger from edited sources
    r = subprocess.run(["python", "tools/gap_ledger.py"], cwd=r"F:\ofn-node",
                       capture_output=True, text=True)
    assert '"rows": 64' in r.stdout, r.stdout + r.stderr

    # run the 18 rows on 138 (read-only, bytes stdin, base64 commands)
    blocks = []
    for gid, cmd in PORTS.items():
        b64 = base64.b64encode(cmd.encode()).decode()
        blocks.append(f"echo '=====ROW {gid}'\n"
                      f"o=$( {{ echo '{b64}' | base64 -d | timeout 60 bash; }} 2>&1 ); rc=$?\n"
                      f"echo \"RC=$rc\"\necho \"OUT=$o\"\n")
    script = ("cd ~/ofn || { echo 'CD_FAIL'; exit 9; }\n"
              "export PYTHONDONTWRITEBYTECODE=1\n" + "\n".join(blocks))
    p = subprocess.run(["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "board138", "bash -s"],
                       input=script.encode("utf-8"), capture_output=True, timeout=1200)
    stdout = p.stdout.decode("utf-8", errors="replace")
    got, cur = {}, None
    for ln in stdout.splitlines():
        if ln.startswith("=====ROW "):
            cur = ln.split()[1]
            got[cur] = {"rc": None, "out": ""}
        elif cur and ln.startswith("RC="):
            got[cur]["rc"] = int(ln[3:])
        elif cur and ln.startswith("OUT="):
            got[cur]["out"] = ln[4:]

    # append v2 rows to the results file (+ lane mirror)
    src_by_id = {g["gap_id"]: g for g in data["gaps"]}
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    v2 = []
    for gid, cmd in PORTS.items():
        g = src_by_id[gid]
        res = got.get(gid) or {}
        rc, out = res.get("rc"), res.get("out", "")
        row = {"gap_id": gid, "node": g["node"], "expect": g.get("expect"),
               "verify_command": cmd, "class": g["class"],
               "port": "v2-python-c (judge step-4: jq/rg removed, zero node mutation)",
               "verify_command_original": g.get("verify_command_original"),
               "ran_at_utc": now,
               "vantage": "laptop ssh board138, repo ~/ofn",
               "scope": "read-only verify"}
        if rc is None:
            row.update({"actual_result": "ERROR", "reason": "no output captured"})
        else:
            row.update({"actual_result": "PASS" if rc == 0 else "FAIL" if rc == 1 else "ERROR",
                        "rc": rc, "captured_output": out[:400]})
        v2.append(row)

    for path in (RESULTS, LANE / "GAP-VERIFY-RESULTS-20260908.jsonl"):
        with open(path, "a", encoding="utf-8") as fh:
            for row in v2:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts = {}
    for row in v2:
        counts[row["actual_result"]] = counts.get(row["actual_result"], 0) + 1
    print("v2 rows:", len(v2), "| results:", counts)
    for row in v2:
        print(f"  {row['actual_result']:5s} {row['gap_id']} rc={row.get('rc')} "
              f"out={str(row.get('captured_output'))[:110]!r}")


if __name__ == "__main__":
    main()
