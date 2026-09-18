"""Execute NEXT-TO-ALIVE as far as AGENTS.md allows. Read-only. No send. No flag enable."""
from __future__ import annotations

import json
import socket
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
OUT = LANE / "PLAN-EXECUTE-RECEIPT.json"
REMOTE = "ari@192.168.0.138"
GATES = "/home/ari/octopus-mesh/state/season/season5-gates-final.json"
SEASON_NOTE = "/home/ari/octopus-mesh/state/season/SEASON-5-2026-09-04.md"
FORWARDS = (
    (18791, 8791, "ziman"),
    (18792, 8792, "lead"),
    (18793, 8793, "studio"),
    (18794, 8794, "owner"),
    (18796, 8796, "bridge"),
)
INTERESTING = (
    "HOLD_EXTERNAL",
    "hold_external",
    "telegram",
    "Telegram",
    "live_of",
    "paid_ads",
    "ads",
    "painting",
    "ziman",
    "studio",
    "gates",
)


def _now() -> tuple[str, str]:
    local = datetime.now().astimezone().isoformat(timespec="seconds")
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return local, utc


def _tcp(host: str, port: int, timeout: float = 0.4) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def _healthz(port: int) -> dict:
    url = f"http://127.0.0.1:{port}/healthz"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            body = r.read().decode("utf-8", "replace")
            parsed = None
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = None
            ok = bool(parsed.get("ok")) if isinstance(parsed, dict) else ("ok" in body.lower())
            return {
                "url": url,
                "http": r.status,
                "ok": ok,
                "n": len(body),
                "err": None,
            }
    except Exception as e:
        return {"url": url, "http": None, "ok": False, "n": 0, "err": type(e).__name__}


def _ssh(remote_cmd: str, timeout: int = 20) -> dict:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        REMOTE,
        remote_cmd,
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "exit": p.returncode,
            "stdout": (p.stdout or "")[-8000:],
            "stderr": (p.stderr or "")[-2000:],
        }
    except Exception as e:
        return {"exit": None, "stdout": "", "stderr": f"{type(e).__name__}: {e}"}


def _pick(d: object) -> dict:
    if not isinstance(d, dict):
        return {"_type": type(d).__name__, "_len": (len(d) if hasattr(d, "__len__") else None)}
    out = {"_keys": sorted(str(k) for k in d.keys())}
    for k in INTERESTING:
        if k in d:
            v = d[k]
            if isinstance(v, (dict, list)):
                out[k] = v
            else:
                out[k] = v
    return out


def main() -> int:
    local, utc = _now()
    receipt: dict = {
        "schema": "octopus.next-to-alive-execute.v1",
        "measured_at": local,
        "measured_at_utc": utc,
        "lane": "U-WHY-NOT-LIVE-20260905",
        "owner_quote_fa": "پلن بپین همرو انجام بده متوقف نشو",
        "plan": "09-LANES/U-WHY-NOT-LIVE-20260905/NEXT-TO-ALIVE.md",
        "live_organism_claim": False,
        "send": False,
        "flags_enabled": False,
        "138_written": False,
        "arbiter": {
            "node_id": "laptop-vault / DESKTOP-KA9RFN5",
            "vantage": "this_host plus ssh_ro_138",
            "scope": "this_host_only plus node138 via ssh_ro",
            "claim_type": "observation",
            "not_node180": True,
        },
        "hard_stop": {
            "AGENTS_md_section_4": "no message leaves the machine; no OCTOPUS_WIRE_*",
            "plan_step_2_send": "not_executed",
            "plan_step_1_rewrite_138_json": "not_executed_this_script_is_read_only",
        },
    }

    receipt["tunnels"] = {}
    all_ok = True
    for lp, rp, role in FORWARDS:
        listen = _tcp("127.0.0.1", lp)
        hz = _healthz(lp) if listen else {"http": None, "ok": False, "err": "not_listen"}
        receipt["tunnels"][role] = {
            "local": lp,
            "remote": rp,
            "listen": listen,
            **hz,
        }
        if not (listen and hz.get("http") == 200 and hz.get("ok")):
            all_ok = False
    receipt["all_five_healthz_200_ok"] = all_ok

    iden = _ssh("hostname; ip -4 -br addr show eth0; test -f %s && echo GATES=1 || echo GATES=0; test -f %s && echo SEASON_NOTE=1 || echo SEASON_NOTE=0" % (GATES, SEASON_NOTE))
    receipt["ssh_identity"] = iden

    dump = _ssh(
        "python3 - <<'PY'\n"
        "import json, os\n"
        f"p={GATES!r}\n"
        "print('exists', os.path.isfile(p))\n"
        "if os.path.isfile(p):\n"
        "    d=json.load(open(p, encoding='utf-8'))\n"
        "    print('TYPE', type(d).__name__)\n"
        "    if isinstance(d, dict):\n"
        "        print('KEYS', ','.join(sorted(map(str, d.keys()))))\n"
        "        for k in sorted(d):\n"
        "            v=d[k]\n"
        "            if isinstance(v, (str, int, float, bool)) or v is None:\n"
        "                print('KV', k, '=', v)\n"
        "            elif isinstance(v, dict):\n"
        "                print('DICT', k, 'subkeys', ','.join(sorted(map(str, v.keys()))[:40]))\n"
        "            elif isinstance(v, list):\n"
        "                print('LIST', k, 'n', len(v))\n"
        "PY"
    )
    receipt["gates_probe"] = dump

    hold_grep = _ssh(
        "rg -n -i 'HOLD_EXTERNAL|hold_external|telegram' /home/ari/octopus-mesh/state/season /home/ari/ofn --glob '!*.pyc' --max-count 40 || "
        "grep -R -n -i -E 'HOLD_EXTERNAL|hold_external' /home/ari/octopus-mesh/state/season /home/ari/ofn 2>/dev/null | head -n 40"
    )
    receipt["hold_grep"] = {
        "exit": hold_grep["exit"],
        "stdout": hold_grep["stdout"][-4000:],
        "stderr": hold_grep["stderr"][-500:],
    }

    # Ledger look: names only, do not copy revenue/sent/booking values into this vault.
    ledger = _ssh(
        "python3 - <<'PY'\n"
        "import os\n"
        "cands=[\n"
        " '/home/ari/ofn',\n"
        " '/home/ari/octopus-mesh',\n"
        " '/home/ari/octopus-mesh/state',\n"
        "]\n"
        "hits=[]\n"
        "for root in cands:\n"
        "    if not os.path.isdir(root):\n"
        "        continue\n"
        "    for dirpath, dirnames, filenames in os.walk(root):\n"
        "        dirnames[:] = [d for d in dirnames if d not in ('.git','__pycache__','node_modules')]\n"
        "        base=os.path.basename(dirpath).lower()\n"
        "        if 'ledger' in base:\n"
        "            hits.append('DIR '+dirpath)\n"
        "        for fn in filenames:\n"
        "            low=fn.lower()\n"
        "            if 'ledger' in low and low.endswith(('.json','.jsonl','.md')):\n"
        "                hits.append('FILE '+os.path.join(dirpath, fn))\n"
        "        if len(hits)>40:\n"
        "            break\n"
        "    if len(hits)>40:\n"
        "        break\n"
        "print('n', len(hits))\n"
        "print('\\n'.join(hits[:40]))\n"
        "PY"
    )
    receipt["ledger_paths_only"] = {
        "exit": ledger["exit"],
        "stdout": ledger["stdout"][-3000:],
        "note": "paths only; values not copied",
    }

    receipt["executed"] = [
        "reuse/verify five tunnel /healthz GET",
        "ssh BatchMode identity + gates file probe",
        "HOLD_EXTERNAL grep on 138 season/ofn",
        "ledger path census (names only)",
    ]
    receipt["not_executed"] = [
        "rewrite season5-gates-final.json",
        "Telegram send",
        "live OF publish",
        "paid ads spend",
        "enable OCTOPUS_WIRE_*",
        "source OCTOPUS-flags.cmd",
        "write revenue/sent/booking in this vault",
        "new SSH to 180",
        "138-to-180 tunnel",
        "invent 138 JSON schema",
    ]
    receipt["alive"] = False
    receipt["why_not_alive"] = "step_2_first_effect_row_not_fired; AGENTS.md section 4"

    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)
    print("all_five_healthz_200_ok", receipt["all_five_healthz_200_ok"])
    print("ssh_exit", iden.get("exit"))
    print("gates_exit", dump.get("exit"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
