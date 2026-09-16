"""Recover the real cache dirs the B5 battery accidentally moved (isolation
leak: Path.home was pinned only at fixture build, not during the runs; the
handler's scan globbed the REAL ~/wt-*). Every moved item sits in a fixture
quarantine dir; original paths are recorded in each fixture proposal's
evidence/argv. Also lists the v1 CE run's rm -rf victims (regenerable caches
only, per the B5 whitelist itself)."""
import json
import pathlib
import shutil

home = pathlib.Path.home()
moved_back, missing, rmrf = [], [], []
for fxdir in sorted(pathlib.Path("/tmp").glob("b5-*")):
    props = list((fxdir / "state/proposals").glob("op-*.json"))
    for pr in props:
        try:
            doc = json.loads(pr.read_text(encoding="utf-8"))
        except Exception:
            continue
        art = doc.get("payload", {}).get("artifact", {}) or {}
        paths = art.get("paths") or []
        argvs = (art.get("argv")
                 or doc.get("payload", {}).get("artifact", {}).get("argv") or [])
        # command style tells mv (recoverable) from rm -rf (gone)
        kinds = set()
        for a in (argvs or []):
            if isinstance(a, list) and a:
                kinds.add(a[0])
        for p in paths:
            src = pathlib.Path(p)
            if "/tmp/" in p:
                continue  # fixture-internal
            if not src.exists():
                # search every quarantine dir for the basename
                base = src.name
                found = None
                for q in pathlib.Path("/tmp").glob("b5-*/state/b5-quarantine/*/*"):
                    if q.name == base:
                        found = q
                        break
                if found is not None:
                    src.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(found), str(src))
                    moved_back.append(str(src))
                else:
                    rmrf.append(p)
            else:
                missing.append(("still-there", p))
print("MOVED_BACK:", len(moved_back))
for x in moved_back:
    print("  restored:", x)
print("GONE (rm -rf by the v1 CE run; regenerable caches only):", len(rmrf))
for x in rmrf:
    print("  gone:", x)
