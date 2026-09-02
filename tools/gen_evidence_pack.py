#!/usr/bin/env python3
"""gen_evidence_pack.py — بستهٔ شواهد خام برای ناظر (SUPERVISION §7).

هر بخش = فرمان واقعی + خروجی واقعی + تاریخ UTC. هیچ چیز خلاصه/بازنویسی
نمی‌شود — «unverified» ها باید با خام بسته شوند.
"""
import datetime as _dt
import subprocess
import sys
from pathlib import Path

REPO = Path.home() / "ofn"
OUT = REPO / "docs/evidence/EVIDENCE-PACK-20260902.md"


def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, cwd=cwd or REPO,
                       capture_output=True, text=True, timeout=120)
    return (r.stdout + (("\n[stderr] " + r.stderr) if r.stderr.strip() else "")).strip()


def main() -> int:
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [f"# EVIDENCE PACK — raw outputs for supervision §7\n\n"
             f"generated: {now} (UTC) · host: {run('hostname')}\n"]
    parts.append("## 1) pytest raw — all three batteries\n```")
    parts.append(run("python3 -m pytest tests/test_hf.py tests/test_teeth.py "
                     "tests/test_lane_e_q.py -q"))
    parts.append("```\n## 2) rate card — command + output + active card\n```")
    parts.append("$ cd ~/ofn/ofn/agents && python3 rate_card_builder.py")
    parts.append(run("python3 rate_card_builder.py", cwd=REPO / "ofn/agents"))
    parts.append("```\nactive card (graded) — key fields:\n```json")
    parts.append(run('python3 -c "import json,os; d=json.load(open(os.path.'
                     'expanduser(\'~/.local/share/ofn/painting_rate_card.json\'))); '
                     'print(json.dumps({k:d[k] for k in (\'grade\',\'ocp_derived\','
                     '\'approval\')}, ensure_ascii=False, indent=1))"'))
    parts.append("```\n## 3) git show --stat\n```")
    for c in ("af4aba8b", "42122af1", "7a1f4e36"):
        parts.append(run(f"git show --stat --oneline {c} | head -10"))
        parts.append("")
    parts.append("```\n## 4) smoke.sh raw\n```")
    parts.append(run("bash tools/smoke.sh"))
    parts.append("```\n## 5) systemctl list-timers\n```")
    parts.append(run("systemctl list-timers --no-pager | grep octopus-"))
    parts.append("```\n## 6) reconcile raw\n```")
    parts.append(run("python3 tools/reconcile.py"))
    parts.append("```")
    parts.append("\n## 7) fingerprint store (production, post-cleanup)\n```")
    fp = Path.home() / "ofn/data/state/quote-fingerprints.jsonl"
    parts.append(fp.read_text() if fp.exists() else "(empty — no production quote sent yet)")
    parts.append("```\n---\nEnd of pack.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    print(f"written {OUT} ({len(parts)} sections)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
