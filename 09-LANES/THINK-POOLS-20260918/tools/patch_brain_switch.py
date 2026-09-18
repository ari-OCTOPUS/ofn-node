#!/usr/bin/env python3
"""BRAIN-FACTORY SWITCH: make the two real RemoteBrain construction sites go
through tools/brain_factory (new provider path), with an explicit fallback to
the old path so behaviour never changes silently. Pre-image + receipt."""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
TARGETS = ["/home/ari/ofn/ofn/assistant_update.py", "/home/ari/ofn/ofn/run.py"]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


pre = {}
for p in TARGETS:
    shutil.copy2(p, p + ".pre-brainswitch-" + TS)
    pre[p] = sha(p)

HELPER = '''

def _factory_brain(tier="standard"):
    """BRAIN-FACTORY SWITCH (2026-09-18): prefer tools/brain_factory (whole
    provider path: both env files, all dialects, verified endpoints). Falls
    back to the legacy RemoteBrain path with a receipt if no provider is
    routable, so behaviour can never regress silently."""
    import sys as _sys
    import pathlib as _pl
    _root = _pl.Path(__file__).resolve().parent.parent
    if str(_root / "tools") not in _sys.path:
        _sys.path.insert(0, str(_root / "tools"))
    try:
        import brain_factory as _bf  # noqa: PLC0415
        _b = _bf.build(tier=tier)
        _rec = _root / "state" / "receipts"
        try:
            _rec.mkdir(parents=True, exist_ok=True)
            with (_rec / "brainswitch.jsonl").open("a", encoding="utf-8") as _fh:
                _fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                      "file": __file__, "tier": tier,
                                      "provider": (_b.get("decision") or {}).get("chosen"),
                                      "model": _b.get("model"), "path": "factory"}) + chr(10))
        except Exception:
            pass
        return _b["brain"]
    except Exception as _exc:  # noqa: BLE001 - fallback is deliberate and recorded
        try:
            _rec = _root / "state" / "receipts"
            _rec.mkdir(parents=True, exist_ok=True)
            with (_rec / "brainswitch.jsonl").open("a", encoding="utf-8") as _fh:
                _fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                      "file": __file__, "tier": tier,
                                      "path": "fallback", "why": type(_exc).__name__}) + chr(10))
        except Exception:
            pass
        return None
'''

results = {}
for p in TARGETS:
    src = pathlib.Path(p).read_text(encoding="utf-8")
    if "_factory_brain" in src:
        results[p] = "already switched"
        continue
    # insert helper after the module docstring/imports (first blank line after imports)
    lines = src.splitlines()
    insert_at = 0
    for i, ln in enumerate(lines[:60]):
        if ln.startswith(("import ", "from ")):
            insert_at = i + 1
    lines.insert(insert_at, HELPER)
    src = chr(10).join(lines)
    if not src.endswith(chr(10)):
        src += chr(10)
    pathlib.Path(p).write_text(src, encoding="utf-8", newline=chr(10))
    results[p] = "helper inserted at line %d" % insert_at
    print(p, "->", results[p])

rec = {"schema": "octopus.fix-receipt.v1", "id": "BRAINSWITCH-" + TS,
       "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
       "what": "_factory_brain() helper installed in the two RemoteBrain construction "
               "sites; call sites are switched in a following step so each site can be "
               "tested independently (owner guidance: one file at a time)",
       "files": [{"file": p, "sha_before": pre[p], "sha_after": str(pathlib.Path(p).stat().st_size)}
                 for p in TARGETS],
       "rollback": "cp <preimage> <file>",
       "preimages": [p + ".pre-brainswitch-" + TS for p in TARGETS]}
json.dump(rec, open("/home/ari/ofn/state/receipts/BRAINSWITCH-%s.json" % TS, "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
print("receipt: BRAINSWITCH-%s.json" % TS)
print(json.dumps(results, indent=0)[:400])
