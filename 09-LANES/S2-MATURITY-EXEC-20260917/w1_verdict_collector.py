#!/usr/bin/env python3
"""W1 witness verdict collector (S2-MATURITY-EXEC, GOV V8/L2).

Runs on board138 at 2026-09-18 09:20Z (the 24h witness window on node 182 ended
09:11:20Z). Reads the two witness logs on 182 over SSH (read-only), applies the
charter's PASS/FAIL rule with no partial credit, and writes the verdict:

  138: /home/ari/ofn/state/evidence/W1-VERDICT-20260918.json
  laptop share (germline):  W1-VERDICT-20260918.json + W1-LANE-REPORT-APPEND-20260918.md
       -> finalize_w1_verdict.py on the laptop copies both into the vault.

PASS requires, in EVERY sample of BOTH files:
  * the four units' start timestamps frozen at 2026-09-17 07:18:32 (registry) /
    07:18:41 (checkpoint) UTC,
  * NRestarts = 0,
  * the .path units still active,
  * no apply_signed_inbound process,
  * sampling gaps <= 900s and the window covered to its planned end.

Anything else is FAIL, with the FIRST violation recorded verbatim. A file that
cannot be read makes the verdict UNVERIFIED — never a pass by absence.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

NODE = "root@192.168.0.182"
OBS = "/root/s1-maturity-w1-20260917/observations.jsonl"
FROZEN = "/var/lib/octopus/state/s1pa-attack/w1-frozen-window.jsonl"
PLANNED_END = "2026-09-18T09:11:20Z"
MAX_GAP_S = 900
EXPECTED_START = {
    "octopus-apply-checkpoint.service": "07:18:41",
    "octopus-apply-registry.service": "07:18:32",
}
PATH_UNITS = ["octopus-apply-checkpoint.path", "octopus-apply-registry.path"]
ALL_UNITS = PATH_UNITS + list(EXPECTED_START)

OUT_138 = Path("/home/ari/ofn/state/evidence/W1-VERDICT-20260918.json")
SHARE = Path("/mnt/octopus-germline")
OUT_SHARE = SHARE / "W1-VERDICT-20260918.json"
APPEND_SHARE = SHARE / "W1-LANE-REPORT-APPEND-20260918.md"


def sh(cmd: str) -> tuple[int, str]:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def grab(remote_path: str) -> tuple[str | None, str]:
    rc, out = sh("timeout 60 ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=no %s 'cat %s'"
                 % (NODE, remote_path))
    if rc != 0 or not out.strip():
        return None, "ssh_rc=%s" % rc
    return out, "ok"


def parse_ts(val: str):
    s = str(val or "").strip().replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def clock_of(val) -> str | None:
    """'Thu 2026-09-17 07:18:41 UTC' -> '07:18:41' (tolerant to formatting)."""
    m = re.search(r"\b(\d\d:\d\d:\d\d)\b", str(val or ""))
    return m.group(1) if m else None


def analyse(raw: str, label: str) -> dict:
    samples, malformed = [], 0
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if isinstance(d, dict) and d.get("units"):
            samples.append(d)
    stamps = [t for t in (parse_ts(s.get("ts")) for s in samples) if t]
    stamps.sort()
    gaps = [(stamps[i + 1] - stamps[i]).total_seconds() for i in range(len(stamps) - 1)]
    first_violation = None
    for s in samples:
        units = s.get("units") or {}
        for u in ALL_UNITS:
            state = units.get(u)
            if state is None:
                if first_violation is None:
                    first_violation = {"source": label, "ts": s.get("ts"), "unit": u,
                                       "why": "unit missing from sample"}
                continue
            txt = json.dumps(state, ensure_ascii=False)
            if u in EXPECTED_START:
                got = clock_of(txt)
                if got != EXPECTED_START[u] and first_violation is None:
                    first_violation = {"source": label, "ts": s.get("ts"), "unit": u,
                                       "why": "start timestamp moved",
                                       "expected": EXPECTED_START[u], "got": got,
                                       "raw": txt[:200]}
                nr = re.search(r"NRestarts['\"]?\s*:\s*['\"]?(\d+)", txt)
                if nr and int(nr.group(1)) != 0 and first_violation is None:
                    first_violation = {"source": label, "ts": s.get("ts"), "unit": u,
                                       "why": "NRestarts != 0", "got": nr.group(1)}
            elif u in PATH_UNITS:
                if '"ActiveState": "active"' not in txt.replace("'", '"') and first_violation is None:
                    first_violation = {"source": label, "ts": s.get("ts"), "unit": u,
                                       "why": "path unit not active", "raw": txt[:160]}
        procs = s.get("apply_signed_inbound") or s.get("procs") or s.get("processes")
        if procs and first_violation is None:
            first_violation = {"source": label, "ts": s.get("ts"),
                               "why": "apply_signed_inbound process present",
                               "raw": str(procs)[:160]}
    return {
        "path": label,
        "samples": len(samples),
        "malformed_lines": malformed,
        "first_ts": stamps[0].isoformat() if stamps else None,
        "last_ts": stamps[-1].isoformat() if stamps else None,
        "max_gap_seconds": int(max(gaps)) if gaps else None,
        "covers_planned_end": bool(stamps and parse_ts(PLANNED_END)
                                   and stamps[-1] >= parse_ts(PLANNED_END)),
        "first_violation": first_violation,
    }


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    notes, sources = [], {}
    for label, path in (("observations", OBS), ("frozen_window", FROZEN)):
        raw, why = grab(path)
        if raw is None:
            sources[label] = {"path": path, "status": "unreadable", "detail": why}
            notes.append("%s could not be read (%s)" % (path, why))
            continue
        sources[label] = analyse(raw, label)
        sources[label]["path"] = path
        sources[label]["status"] = "read"

    # bracket trick stops pgrep from matching its own command line; the grep also
    # drops the remote shell wrapper — a self-match once produced a false FAIL.
    rc, pg = sh("timeout 30 ssh -o BatchMode=yes -o ConnectTimeout=10 %s "
                "\"pgrep -fa '[a]pply_signed_inbound' || true\"" % NODE)
    live_procs = [l.strip() for l in (pg or "").splitlines()
                  if l.strip() and "pgrep" not in l and "bash -c" not in l]

    violations = [s["first_violation"] for s in sources.values()
                  if isinstance(s, dict) and s.get("first_violation")]
    unreadable = [k for k, s in sources.items() if s.get("status") != "read"]
    incomplete = [k for k, s in sources.items()
                  if s.get("status") == "read" and not s.get("covers_planned_end")]
    big_gap = [k for k, s in sources.items()
               if s.get("status") == "read" and (s.get("max_gap_seconds") or 0) > MAX_GAP_S]

    if unreadable:
        verdict = "UNVERIFIED"
    elif violations or live_procs or incomplete or big_gap:
        verdict = "FAIL"
    else:
        verdict = "PASS"

    verdict_doc = {
        "schema": "octopus.w1-witness-verdict.v1",
        "lane": "S2-MATURITY-EXEC-20260917",
        "collected_at": now,
        "node_witnessed": "182",
        "window": {"planned_start": "2026-09-17T09:11:20Z", "planned_end": PLANNED_END,
                   "sampling_interval_s": 300},
        "verdict": verdict,
        "sources": sources,
        "live_apply_signed_inbound_procs": live_procs[:5],
        "checks": {"max_gap_limit_s": MAX_GAP_S, "unreadable": unreadable,
                   "coverage_incomplete": incomplete, "gap_violations": big_gap,
                   "violations": violations},
        "first_violation": (violations[0] if violations else
                            ({"why": "live apply_signed_inbound process present",
                              "raw": live_procs[0][:160]} if live_procs else None)),
        "consequence_on_fail": ("S1-GAP-02A reverts to FAIL-OPEN-DEBUG per the S1-MATURITY charter"
                                if verdict == "FAIL" else None),
        "notes": notes,
    }
    OUT_138.parent.mkdir(parents=True, exist_ok=True)
    OUT_138.write_text(json.dumps(verdict_doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    md = ["", "## W1 witness verdict — %s (collected %sZ, node 182)" % (verdict, now),
          "<!-- written by octopus-w1-verdict on 138; collected read-only from 182 -->", ""]
    md.append("- planned window: 2026-09-17T09:11:20Z → %s (300s interval)" % PLANNED_END)
    for k, s in sources.items():
        if s.get("status") == "read":
            md.append("- `%s`: %d samples, %s → %s, max gap %ss, coverage_to_end=%s"
                      % (k, s["samples"], s["first_ts"], s["last_ts"],
                         s["max_gap_seconds"], s["covers_planned_end"]))
        else:
            md.append("- `%s`: UNREADABLE (%s)" % (k, s.get("detail")))
    md.append("- live apply_signed_inbound processes at collection: %d" % len(live_procs))
    if verdict == "FAIL":
        md.append("- **FIRST VIOLATION:** `%s`" % json.dumps(verdict_doc["first_violation"],
                                                             ensure_ascii=False)[:400])
        md.append("- Consequence: **S1-GAP-02A reverts to FAIL-OPEN-DEBUG** per charter. No partial credit.")
    elif verdict == "UNVERIFIED":
        md.append("- Consequence: verdict cannot be issued (data unreadable); treat GAP-02A as unproven.")
    text = "\n".join(md) + "\n"

    share_ok = False
    if SHARE.exists():
        try:
            OUT_SHARE.write_text(json.dumps(verdict_doc, indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")
            with APPEND_SHARE.open("a", encoding="utf-8") as fh:
                fh.write(text)
            share_ok = True
        except OSError as exc:
            notes.append("share write failed: %s" % type(exc).__name__)
    print(json.dumps({"verdict": verdict, "share_written": share_ok,
                      "obs_samples": sources.get("observations", {}).get("samples"),
                      "frozen_samples": sources.get("frozen_window", {}).get("samples"),
                      "first_violation": verdict_doc["first_violation"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
