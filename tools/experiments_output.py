"""experiments_output — proposals from learning to a readable file."""
import json, sys
from pathlib import Path
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE)); sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib
SCHEMA = "octopus.experiments-output.v1"
OUTPUT = opslib.STATE_DIR / "proposals.jsonl"
def emit(proposals):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in proposals:
        entry = {"schema": SCHEMA, "at": opslib.now_iso(), **p}
        with OUTPUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        n += 1
    return n
def read_all():
    if not OUTPUT.exists(): return []
    return [json.loads(ln) for ln in OUTPUT.read_text(encoding="utf-8").splitlines() if ln.strip()]
