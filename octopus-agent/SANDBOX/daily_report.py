#!/usr/bin/env python3
"""P6 daily advisory report generator — REPORT-ONLY by construction.

Runs under octopus-miniscientist-daily.service. Reads board state, verifies
authority hashes against the last-known-stable values, samples sensorium I/O,
appends one hash-chained CHANGELOG entry, and writes one report file inside
/opt/octopus-agent/REPORTS/daily/. It performs no other action of any kind:
no service calls, no network, no production writes. If an authority hash
differs, the report carries ALERT and the exit code is non-zero (fail-closed).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
from pathlib import Path

AGENT = Path("/opt/octopus-agent")
EXPECTED = {
    "/var/lib/octopus/state/OWNER_REVIEW_DECISION.json":
        "6fdf4f54c9a4a460d25eda416079d3646e55c4162e2f75a2721a12dd617be271",
    "/var/lib/octopus/state/wave_baseline_accepted.json":
        "a313fd777ea21641e17771df436e1cffb37c21957144ba75369e057ff541d728",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    now = datetime.datetime.now(datetime.timezone.utc)
    date = now.strftime("%Y-%m-%d")
    lines: list[str] = [f"# Mini Scientist daily advisory — {date}",
                        f"generated: {now.isoformat(timespec='seconds')}",
                        f"boot_id: {Path('/proc/sys/kernel/random/boot_id').read_text().strip()}", ""]

    lines.append("## Authority check")
    alerts = 0
    for path, expected in EXPECTED.items():
        try:
            actual = sha256(Path(path))
            status = "STABLE" if actual == expected else "ALERT-CHANGED"
            if status != "STABLE":
                alerts += 1
            lines.append(f"- {Path(path).name}: {status} ({actual[:16]}…)")
        except OSError as exc:
            alerts += 1
            lines.append(f"- {Path(path).name}: ALERT-UNREADABLE ({exc})")
    lines.append("")

    lines.append("## Phase status")
    phase_file = (AGENT / "CURRENT-PHASE.yaml").read_text().splitlines()
    for line in phase_file[:6]:
        if line.strip() and not line.startswith("#"):
            lines.append(f"    {line}")
    lines.append("")

    lines.append("## Sensorium process I/O sample (5 s)")
    try:
        pid_out = subprocess.run(
            ["systemctl", "show", "-p", "MainPID", "--value", "octopus-sensorium"],
            capture_output=True, text=True, timeout=10).stdout.strip()
        pid = int(pid_out)
        def io() -> dict[str, int]:
            out = {}
            for line in Path(f"/proc/{pid}/io").read_text().splitlines():
                k, _, v = line.partition(":")
                out[k.strip()] = int(v)
            return out
        import time
        a = io(); time.sleep(5); b = io()
        lines.append(f"- pid {pid}: write_bytes Δ {b['write_bytes']-a['write_bytes']:,} B / 5 s "
                     f"({(b['write_bytes']-a['write_bytes'])/5:,.0f} B/s), syscw Δ {b['syscw']-a['syscw']}")
    except Exception as exc:  # noqa: BLE001 — advisory report must never crash the unit
        lines.append(f"- sample unavailable: {exc}")
    lines.append("")

    lines.append("## Changelog tail")
    tail = (AGENT / "CHANGELOG.jsonl").read_text().splitlines()[-3:]
    for entry in tail:
        ev = json.loads(entry)
        lines.append(f"- seq{ev['seq']} {ev['phase']} {ev['type']} result={ev['payload'].get('result', ev['payload'].get('event', ''))}")
    lines.append("")

    outcome = "OK" if alerts == 0 else f"ALERTS={alerts}"
    lines.append(f"## Outcome: {outcome}")
    lines.append("Report-only run. No deploy, no restart, no network, no promotion.")

    out_dir = AGENT / "REPORTS" / "daily"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{date}.md").write_text("\n".join(lines) + "\n")

    cl = AGENT / "CHANGELOG.jsonl"
    entries = [l for l in cl.read_text().splitlines() if l.strip()]
    prev = json.loads(entries[-1])["hash"]
    ev = {"seq": len(entries), "run_id": f"daily-{date}", "ts": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
          "actor": "mini_scientist", "phase": "P6_DAILY_ADVISORY", "type": "REPORT_WRITTEN",
          "payload": {"outcome": outcome, "report": f"REPORTS/daily/{date}.md"},
          "evidence_refs": [f"REPORTS/daily/{date}.md"], "may_authorize": False, "prev_hash": prev}
    ev["hash"] = "sha256:" + hashlib.sha256(json.dumps(ev, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with cl.open("a") as fh:
        fh.write(json.dumps(ev, sort_keys=True) + "\n")

    return 0 if alerts == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
