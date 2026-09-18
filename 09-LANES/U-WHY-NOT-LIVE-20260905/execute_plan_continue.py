"""Continue NEXT-TO-ALIVE after gates probe. Read-only. No send. No 138 write."""
from __future__ import annotations

import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
OUT = LANE / "PLAN-EXECUTE-CONTINUE.json"
REMOTE = "ari@192.168.0.138"
REMOTE_PY = r"""
import json, os, glob
season_dir = "/home/ari/octopus-mesh/state/season"
print("SEASON_DIR", os.path.isdir(season_dir))
if os.path.isdir(season_dir):
    print("SEASON_FILES", ",".join(sorted(os.listdir(season_dir))[:40]))
note = os.path.join(season_dir, "SEASON-5-2026-09-04.md")
if os.path.isfile(note):
    txt = open(note, encoding="utf-8", errors="replace").read()
    print("NOTE_N", len(txt))
    print("NOTE_HAS_HOLD", "HOLD_EXTERNAL" in txt)
    print("NOTE_HAS_TELEGRAM", "Telegram" in txt or "telegram" in txt)
gates = os.path.join(season_dir, "season5-gates-final.json")
d = json.load(open(gates, encoding="utf-8"))
print("M5", d.get("m5_owner_release"))
print("ADS", d.get("ads_budget"))
print("PAINTING", d.get("painting"))
print("HAS_HOLD_KEY", "HOLD_EXTERNAL" in d or "hold_external" in d)

# HOLD string hits in season dir only (small)
hits = []
for dirpath, _, filenames in os.walk(season_dir):
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if "HOLD_EXTERNAL" in t or "hold_external" in t:
            hits.append(p)
print("HOLD_FILES_N", len(hits))
for p in hits[:20]:
    print("HOLD_FILE", p)

ledgers = [
    "/home/ari/ofn/data/state/legs/claims-ledger.jsonl",
    "/home/ari/ofn/09-LANES/ECONOMIC-LEARNING/runs/2026-09-02/economic-learning-ledger.jsonl",
]
for p in ledgers:
    if not os.path.isfile(p):
        print("LEDGER_MISSING", p)
        continue
    n = 0
    with open(p, encoding="utf-8", errors="replace") as f:
        for _ in f:
            n += 1
    print("LEDGER_LINES", p, n)

# ofn telegram/send module names only
ofn = "/home/ari/ofn"
mods = []
if os.path.isdir(ofn):
    for dirpath, dirnames, filenames in os.walk(ofn):
        dirnames[:] = [x for x in dirnames if x not in (".git", "__pycache__", ".venv", "node_modules")]
        for fn in filenames:
            low = fn.lower()
            if low.endswith((".py", ".md", ".json")) and any(s in low for s in ("telegram", "hold_ext", "outbound", "wire")):
                mods.append(os.path.join(dirpath, fn))
            if len(mods) > 30:
                break
        if len(mods) > 30:
            break
print("MOD_N", len(mods))
for p in mods[:30]:
    print("MOD", p)
"""


def _now() -> tuple[str, str]:
    local = datetime.now().astimezone().isoformat(timespec="seconds")
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return local, utc


def _ssh_py(code: str) -> dict:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        REMOTE,
        "python3",
        "-c",
        code,
    ]
    p = subprocess.run(
        cmd,
        capture_output=True,
        timeout=45,
    )
    def dec(b: bytes) -> str:
        return (b or b"").decode("utf-8", "replace")[-8000:]

    return {"exit": p.returncode, "stdout": dec(p.stdout), "stderr": dec(p.stderr)}


def _get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            body = r.read().decode("utf-8", "replace")
            return {"url": url, "http": r.status, "n": len(body), "err": None}
    except Exception as e:
        return {"url": url, "http": None, "n": 0, "err": f"{type(e).__name__}"}


def main() -> int:
    local, utc = _now()
    probe = _ssh_py(REMOTE_PY)
    # GET-only status-ish paths on owner/ziman — no POST
    gets = [
        _get("http://127.0.0.1:18791/"),
        _get("http://127.0.0.1:18791/healthz"),
        _get("http://127.0.0.1:18794/"),
        _get("http://127.0.0.1:18794/healthz"),
        _get("http://127.0.0.1:18796/"),
        _get("http://127.0.0.1:18796/healthz"),
    ]
    out = {
        "schema": "octopus.next-to-alive-continue.v1",
        "measured_at": local,
        "measured_at_utc": utc,
        "lane": "U-WHY-NOT-LIVE-20260905",
        "send": False,
        "138_written": False,
        "live_organism_claim": False,
        "ssh_py": probe,
        "get_only": gets,
        "not_executed": [
            "POST",
            "Telegram send",
            "rewrite season5-gates-final.json",
            "enable wires",
        ],
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)
    print("ssh_exit", probe["exit"])
    print(probe["stdout"][-2500:])
    if probe["stderr"]:
        print("STDERR", probe["stderr"][-800:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
