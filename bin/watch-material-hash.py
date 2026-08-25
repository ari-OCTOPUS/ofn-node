#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

PUBLIC = Path("/opt/octopus/lab/state/ORGANISM-PUBLIC.json")
LAN = Path("/opt/octopus/lab/state/LAN-WATCH.json")
SOAK = Path("/opt/octopus/lab/evidence/SOAK-RESULTS.json")
LETTERS = Path("/opt/octopus/lab/state/LETTERS.jsonl")


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def material() -> dict:
    public = load(PUBLIC)
    lan = load(LAN)
    soak = load(SOAK)
    letters = ""
    if LETTERS.is_file():
        letters = LETTERS.read_text(encoding="utf-8", errors="replace")
    hosts = {}
    for item in lan.get("hosts") or []:
        hosts[item.get("id")] = item.get("status")
    return {
        "health_state": public.get("health_state"),
        "autonomy_state": public.get("autonomy_state"),
        "identity_chain_valid": public.get("identity_chain_valid"),
        "alert": public.get("alert"),
        "letter": public.get("letter"),
        "llama_health": public.get("llama_health"),
        "soak_running": (public.get("soak") or {}).get("running"),
        "unknowns": public.get("unknowns") or [],
        "lan_hosts": hosts,
        "lan_letters": lan.get("letters_this_tick") or [],
        "telegram": lan.get("telegram"),
        "soak_abort": soak.get("abort"),
        "letters": letters,
        "last_utterance": public.get("last_utterance"),
        "last_utterance_kind": public.get("last_utterance_kind"),
        "last_habit": public.get("last_habit"),
    }


def main() -> int:
    body = json.dumps(material(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    print(hashlib.sha256(body.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
