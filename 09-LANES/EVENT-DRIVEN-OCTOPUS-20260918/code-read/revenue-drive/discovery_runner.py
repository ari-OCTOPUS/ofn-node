#!/usr/bin/env python3
"""Discovery runner (owner 2026-09-18): grow the lead bank without being asked.
harvest -> enrich, then report. Fail-closed: missing module = receipt, not silence."""
import json, pathlib, subprocess, time
RD = pathlib.Path(__file__).resolve().parent
ROOT = RD.parent.parent
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
def rcp(kind, **kw):
    with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"schema": "octopus.discovery.v1", "at": NOW, "kind": kind, **kw},
                            ensure_ascii=False, sort_keys=True, default=str) + chr(10))
def run(script, args=()):
    p = ROOT / script
    if not p.exists():
        return None, "MISSING_%s" % script
    r = subprocess.run(["python3", str(p), *args], capture_output=True, text=True, timeout=900, cwd=str(ROOT))
    return r.returncode, ((r.stdout or "")[-300:] + "|" + (r.stderr or "")[-200:])
def main():
    if (RD / "SEND-PAUSED").exists():
        rcp("DISCOVERY_SKIPPED", why="paused"); return
    rc1, out1 = run("tools/harvest_b2b_accounts.py", ("--max-candidates", "60"))
    rcp("DISCOVERY_HARVEST", rc=rc1, out=out1)
    rc2, out2 = run("state/revenue-drive/lead_enrich.py")
    rcp("DISCOVERY_ENRICH", rc=rc2, out=out2)
    try:
        n = sum(1 for _ in (RD / "lead-emails.jsonl").open(encoding="utf-8"))
    except Exception:
        n = -1
    rcp("DISCOVERY_SUMMARY", harvest_rc=rc1, enrich_rc=rc2, lead_emails_rows=n)
    print(json.dumps({"at": NOW, "harvest": rc1, "enrich": rc2, "emails": n}))
if __name__ == "__main__":
    main()
