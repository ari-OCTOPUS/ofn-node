"""Run the 29 unblocked GAP verifies on 138 — strictly read-only. (v2, clean rewrite)

- Commands pre-screened for write patterns (only 2>/dev/null stderr-discard allowed).
- pytest commands get -p no:cacheprovider; PYTHONDONTWRITEBYTECODE=1 exported on node.
- 'ssh 138 "X"' rows execute as X directly (we are already on 138).
- Script piped via ssh stdin as raw UTF-8 BYTES (no CRLF translation); no file written on node.
"""
import base64
import json
import re
import subprocess
import time
from pathlib import Path

LEDGER = Path(r"F:\ofn-node\ops\GAP-LEDGER.jsonl")
OUT = Path(r"F:\ofn-node\ops\GAP-VERIFY-RESULTS-20260908.jsonl")
LANE_MIRROR = Path(r"F:\backup\09-LANES\GAP-VERIFY-RUN-20260908\GAP-VERIFY-RESULTS-20260908.jsonl")

WRITE_PATTERNS = re.compile(
    r"(?<!2)>|>>|\btee\b|\brm\b|\bmv\b|\bcp\b|\bcurl\b|\bwget\b|\bgit push\b|\bpip\b|\bapt\b|\bsystemctl\b|--write\b")


def main():
    rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    unblocked = [r for r in rows[1:] if r.get("blocked_by") is None and r.get("verify_command")]
    assert len(unblocked) == 29, f"expected 29, got {len(unblocked)}"

    meta, blocks = {}, []
    for r in unblocked:
        cmd = r["verify_command"]
        gid = r["gap_id"]
        base = {"gap_id": gid, "node": r["node"], "expect": r.get("expect"),
                "verify_command": cmd, "class": r["class"]}
        m = WRITE_PATTERNS.search(cmd.replace("2>/dev/null", ""))
        if m:
            meta[gid] = {**base, "actual_result": "ERROR",
                         "reason": f"write-pattern blocked: {m.group(0)!r}"}
            continue
        adapted = []
        if cmd.startswith("ssh 138 "):
            cmd = cmd[len("ssh 138 "):].strip('"')
            adapted.append("ssh-prefix stripped (executed directly on 138)")
        if "pytest" in cmd:
            cmd += " -p no:cacheprovider"
            adapted.append("pytest cache disabled")
        if re.search(r"\bpython\b(?!3)", cmd):
            cmd = re.sub(r"\bpython\b(?!3)", "python3", cmd)
            adapted.append("python->python3 (DietPi has no 'python' alias)")
        if "tail -1" in cmd:
            cmd = cmd.replace("tail -1", "tail -n 1")
            adapted.append("tail -1 -> tail -n 1 (DietPi tail)")
        meta[gid] = {**base, "_cmd": cmd, "_adapted": "; ".join(adapted) or None}
        b64 = base64.b64encode(cmd.encode()).decode()
        blocks.append(f"echo '=====ROW {gid}'\n"
                      f"o=$( {{ echo '{b64}' | base64 -d | timeout 60 bash; }} 2>&1 ); rc=$?\n"
                      f"echo \"RC=$rc\"\necho \"OUT=$o\"\n")

    script = ("cd ~/ofn || { echo 'CD_FAIL'; exit 9; }\n"
              "export PYTHONDONTWRITEBYTECODE=1\n" + "\n".join(blocks))
    p = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "board138", "bash -s"],
        input=script.encode("utf-8"), capture_output=True, timeout=1800)
    stdout = p.stdout.decode("utf-8", errors="replace")
    if p.returncode != 0:
        print("ssh rc:", p.returncode,
              "stderr:", p.stderr.decode("utf-8", errors="replace")[:300])

    results, cur = {}, None
    for ln in stdout.splitlines():
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
            row = dict(m)
        else:
            got = results.get(gid) or {}
            rc, out = got.get("rc"), got.get("out", "")
            if rc is None:
                row = {**{k: v for k, v in m.items() if not k.startswith("_")},
                       "actual_result": "ERROR", "reason": "no output captured for row"}
            else:
                row = {**{k: v for k, v in m.items() if not k.startswith("_")},
                       "actual_result": "PASS" if rc == 0 else "FAIL" if rc == 1 else "ERROR",
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
            print(f"  {r['actual_result']:4s} {r['gap_id']} rc={r.get('rc')} "
                  f"out={str(r.get('captured_output'))[:110]!r}")
        elif "write-pattern" not in str(r.get("reason", "")):
            print(f"  ERR  {r['gap_id']} rc={r.get('rc')} out={str(r.get('captured_output'))[:90]!r}")


if __name__ == "__main__":
    main()
