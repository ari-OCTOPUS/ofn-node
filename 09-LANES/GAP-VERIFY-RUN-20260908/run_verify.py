"""Run the 29 unblocked GAP verifies on 138 — strictly read-only.

- Commands are pre-screened for write patterns; only 2>/dev/null stderr-discard allowed.
- pytest commands get -p no:cacheprovider; PYTHONDONTWRITEBYTECODE=1 exported.
- 'ssh 138 \"X\"' rows execute as X directly on 138 (we are already on 138; alias absent there).
- Script is piped via ssh stdin (bash -s): NO file is written on the node.
- Output: per-row JSON lines with actual_result (rc + captured stdout); honest ERRORs.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

LEDGER = Path(r"F:\ofn-node\ops\GAP-LEDGER.jsonl")
OUT = Path(r"F:\ofn-node\ops\GAP-VERIFY-RESULTS-20260908.jsonl")
LANE_MIRROR = Path(r"F:\backup\09-LANES\GAP-VERIFY-RUN-20260908\GAP-VERIFY-RESULTS-20260908.jsonl")

WRITE_PATTERNS = re.compile(
    r"(?<!2)>|>>|\btee\b|\brm\b|\bmv\b|\bcp\b|\bcurl\b|\bwget\b|\bgit push\b|\bpip\b|\bapt\b|\bsystemctl\b|--write\b")


def screen(cmd: str) -> str | None:
    cleaned = cmd.replace("2>/dev/null", "")
    m = WRITE_PATTERNS.search(cleaned)
    return f"write-pattern blocked: {m.group(0)!r}" if m else None


def main():
    rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    unblocked = [r for r in rows[1:] if r.get("blocked_by") is None and r.get("verify_command")]
    assert len(unblocked) == 29, f"expected 29, got {len(unblocked)}"

    blocks, meta = [], {}
    for r in unblocked:
        cmd = r["verify_command"]
        gid = r["gap_id"]
        block = {"gap_id": gid, "node": r["node"], "expect": r.get("expect"),
                 "verify_command": cmd, "class": r["class"]}
        reason = screen(cmd)
        if reason:
            block.update({"actual_result": "ERROR", "reason": reason})
            meta[gid] = block
            continue
        if cmd.startswith("ssh 138 "):
            cmd = cmd[len("ssh 138 "):].strip('"')
            adapted = "ssh-prefix stripped (executed directly on 138)"
        else:
            adapted = None
        if "pytest" in cmd:
            cmd = cmd + " -p no:cacheprovider"
            adapted = (adapted + "; " if adapted else "") + "pytest cache disabled"
        meta[gid] = {**block, "_cmd": cmd, "_adapted": adapted}

        b64 = __import__("base64").b64encode(cmd.encode()).decode()
        blocks.append(f"echo '=====ROW {gid}'\n"
                      f"o=$( {{ echo '{b64}' | base64 -d | timeout 60 bash; }} 2>&1 ); rc=$?\n"
                      f"echo \"RC=$rc\"\necho \"OUT=$o\"\n")

    script = "cd ~/ofn || { echo 'CD_FAIL'; exit 9; }\nexport PYTHONDONTWRITEBYTECODE=1\n" + "\n".join(blocks)
    # bytes on the wire: Windows text-mode would translate 
 to 
 and break remote bash
    p = subprocess.run(["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "board138", "bash -s"],
                       input=script.encode("utf-8"), capture_output=True, timeout=1800)
    p.stdout = p.stdout.decode("utf-8", errors="replace")
    p.stderr = p.stderr.decode("utf-8", errors="replace")
    p.returncode_rc = p.returncode
    if p.returncode != 0:
        print("ssh rc:", p.returncode, "stderr:", p.stderr[:300])

    # parse stream
    cur, results = None, {}
    for ln in p.stdout.splitlines():
        if ln.startswith("=====ROW "):
            cur = ln.split()[1]
            results[cur] = {"rc": None, "out": ""}
        elif cur and ln.startswith("RC="):
            results[cur]["rc"] = int(ln[3:])
        elif cur and ln.startswith("OUT="):
            results[cur]["out"] = ln[4:]
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out_rows = []
    for gid, m in meta.items():
        if "actual_result" in m:
            row = m
        else:
            rc, out = m.get("_cmd") and (results.get(gid, {}).get("rc"), results.get(gid, {}).get("out", ""))
            if rc is None:
                row = {**{k: v for k, v in m.items() if not k.startswith("_")},
                       "actual_result": "ERROR", "reason": "no output captured for row"}
            else:
                row = {**{k: v for k, v in m.items() if not k.startswith("_")},
                       "actual_result": "PASS" if rc == 0 else "FAIL" if rc in (1,) else "ERROR",
                       "rc": rc, "captured_output": out[:400]}
                if m.get("_adapted"):
                    row["adaptation"] = m["_adapted"]
        row["ran_at_utc"] = now
        row["vantage"] = "laptop ssh board138 (ari@192.168.0.138), repo ~/ofn"
        row["scope"] = "read-only verify per PROMPT-NEXT-1; zero node mutation"
        out_rows.append(row)

    for path in (OUT, LANE_MIRROR):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out_rows) + "\n",
                        encoding="utf-8")
    counts = {}
    for r in out_rows:
        counts[r["actual_result"]] = counts.get(r["actual_result"], 0) + 1
    print("verified:", len(out_rows), "| results:", counts)
    for r in out_rows:
        if r["actual_result"] != "ERROR":
            print(f"  {r['actual_result']:4s} {r['gap_id']} rc={r.get('rc')} out={str(r.get('captured_output'))[:100]!r}")


if __name__ == "__main__":
    main()
