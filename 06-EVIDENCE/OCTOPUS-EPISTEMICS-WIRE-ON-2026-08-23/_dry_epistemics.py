import json, os, sys
from pathlib import Path
OPS = Path(r"F:\backup\_ops")
os.chdir(OPS)
sys.path.insert(0, str(OPS))
# load .env lines for OCTOPUS_* only into environ if missing (idempotent like typical loaders)
env_path = Path(r"F:\backup\.env")
for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k, _, v = s.partition("=")
    k = k.strip()
    v = v.strip().strip('"').strip("'")
    if k.startswith("OCTOPUS_") and k not in os.environ:
        os.environ[k] = v
# also honor flags.cmd style already in env via explicit set
os.environ["OCTOPUS_WIRE_EPISTEMICS"] = os.environ.get("OCTOPUS_WIRE_EPISTEMICS") or "1"
import wiring
from epistemics import run_offloop
results = run_offloop.compute_all()
beat_ret = wiring.epistemics_beat(live_loop=None, beat=720)
fl = json.loads((OPS / "state" / "flags-loaded-organism.json").read_text(encoding="utf-8"))
out = {
    "OCTOPUS_WIRE_EPISTEMICS_environ": os.environ.get("OCTOPUS_WIRE_EPISTEMICS"),
    "wiring_flag": wiring.flag("OCTOPUS_WIRE_EPISTEMICS"),
    "flags_loaded_pid": fl.get("pid"),
    "flags_loaded_value": (fl.get("flags") or {}).get("OCTOPUS_WIRE_EPISTEMICS"),
    "epistemics_beat_return": beat_ret,
    "offloop_metric_names": [r.get("metric") for r in results],
    "live_tg_send": False,
    "emit": False,
    "note": "dry/advisory; live_loop=None; no emit; no TG",
}
print(json.dumps(out, ensure_ascii=False, indent=2))
Path(r"F:\backup\06-EVIDENCE\OCTOPUS-EPISTEMICS-WIRE-ON-2026-08-23\EPISTEMICS-DRY.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
