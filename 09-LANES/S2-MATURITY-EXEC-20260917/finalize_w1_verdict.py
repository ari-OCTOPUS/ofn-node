#!/usr/bin/env python
"""Finalize the W1 witness verdict into the vault (runs on the laptop).

The collector runs on board138 at 2026-09-18 09:20Z and writes its result to the
germline SMB share (E:\\germline on this machine). This script — registered as a
Windows Scheduled Task at 19:25 local (09:25Z) — copies that result into the
lane's evidence folder, appends the report section to the lane report, and
commits. It never invents a verdict: if the collector's JSON is absent it records
that fact and exits, leaving the verdict explicitly uncollected.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SHARE = Path(r"E:\germline")
LANE = Path(r"F:\backup\09-LANES\S2-MATURITY-EXEC-20260917")
EVIDENCE = LANE / "evidence" / "W1-VERDICT-20260918.json"
APPEND_SRC = SHARE / "W1-LANE-REPORT-APPEND-20260918.md"
REPORT = LANE / "LANE-REPORT.md"
STATUS = LANE / "evidence" / "W1-FINALIZE-STATUS.json"
SHARE_JSON = SHARE / "W1-VERDICT-20260918.json"


def git(*args):
    for exe in (shutil.which("git"), r"C:\Program Files\Git\cmd\git.exe",
                r"C:\Program Files\Git\bin\git.exe"):
        if exe:
            p = subprocess.run([exe, "-C", str(LANE.parent.parent)] + list(args),
                               capture_output=True, text=True)
            if p.returncode == 0 or "not a git repository" not in (p.stderr or ""):
                return p.returncode, (p.stdout or "") + (p.stderr or "")
    return -1, "git not found"


def main():
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    status = {"schema": "octopus.w1-finalize.v1", "at": now, "copied": False,
              "appended": False, "verdict": None, "committed": False}
    if not SHARE_JSON.exists():
        status["error"] = "collector output not found on shared drive (%s)" % SHARE_JSON
    else:
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SHARE_JSON, EVIDENCE)
        status["copied"] = True
        try:
            status["verdict"] = json.loads(EVIDENCE.read_text(encoding="utf-8")).get("verdict")
        except (OSError, ValueError):
            status["verdict"] = "UNREADABLE"
        if APPEND_SRC.exists():
            section = APPEND_SRC.read_text(encoding="utf-8")
            if "W1 witness verdict" not in REPORT.read_text(encoding="utf-8", errors="replace"):
                with REPORT.open("a", encoding="utf-8") as fh:
                    fh.write(section)
                status["appended"] = True
            else:
                status["appended"] = "already-present"
        rc, out = git("add", str(EVIDENCE), str(REPORT))
        rc2, out2 = git("commit", "-m",
                        "W1 witness verdict %s (collected on 138, finalized on laptop; "
                        "node 182 witness logs read-only)" % (status["verdict"],))
        status["committed"] = rc2 == 0
        status["git"] = (out + out2)[-300:]
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(status, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
