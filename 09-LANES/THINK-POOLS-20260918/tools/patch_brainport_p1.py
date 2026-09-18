#!/usr/bin/env python3
"""Patch brainport.py to resolve its provider through the registry router.

PERFUSION P1. Fail-safe by design: if the router module is missing, raises, or
returns no usable token, the configured BRAIN_PROVIDER is kept exactly as before.
So the worst case of this patch is the previous behaviour.

Steps: preimage -> anchored patch (assert exactly one match) -> py_compile ->
report hashes. Nothing is executed here.
"""
import hashlib
import pathlib
import shutil
import subprocess
import time

TARGET = pathlib.Path("/home/ari/ofn/ofn/helpers/brainport.py")
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

src = TARGET.read_text(encoding="utf-8")
before_sha = hashlib.sha256(src.encode()).hexdigest()

ANCHOR = '        self.provider = os.environ.get("BRAIN_PROVIDER", "fugu").strip().lower()\n'
assert src.count(ANCHOR) == 1, f"anchor count = {src.count(ANCHOR)}"

REPLACEMENT = (
    '        self.provider = os.environ.get("BRAIN_PROVIDER", "fugu").strip().lower()\n'
    '        self.routing_reason = "PIN"\n'
    '        # PERFUSION P1 (2026-09-18): never call a provider we know is out of\n'
    '        # credit. The pin still wins while it is routable; otherwise the\n'
    '        # registry order decides. Any failure here keeps the pin (fail-safe).\n'
    '        try:\n'
    '            import sys as _sys\n'
    '            _tools = "/home/ari/ofn/tools"\n'
    '            if _tools not in _sys.path:\n'
    '                _sys.path.insert(0, _tools)\n'
    '            import provider_routing as _pr\n'
    '            _d = _pr.decide_brainport(_pr.env_pin())\n'
    '            if _d.get("token"):\n'
    '                self.provider = _d["token"]\n'
    '                self.routing_reason = _d.get("reason", "ROUTED")\n'
    '            _pr.record(_d)\n'
    '        except Exception:\n'
    '            pass\n'
)

preimage = TARGET.with_suffix(f".py.pre-perfusion-p1-{STAMP}")
shutil.copy2(TARGET, preimage)
TARGET.write_text(src.replace(ANCHOR, REPLACEMENT, 1), encoding="utf-8")

after = TARGET.read_text(encoding="utf-8")
compile_ok = subprocess.run(["python3", "-m", "py_compile", str(TARGET)],
                            capture_output=True, text=True)
print(f"preimage   : {preimage}")
print(f"sha_before : {before_sha[:16]}")
print(f"sha_after  : {hashlib.sha256(after.encode()).hexdigest()[:16]}")
print(f"py_compile : {'OK' if compile_ok.returncode == 0 else 'FAILED ' + compile_ok.stderr[:200]}")
print(f"anchor_left: {after.count(ANCHOR)} (1 = the original line is still there as the fallback)")

# Prove the resolved provider without printing any credential.
probe = subprocess.run(
    ["python3", "-c",
     "import sys; sys.path.insert(0,'/home/ari/ofn'); "
     "from ofn.helpers.brainport import BrainPort; "
     "b=BrainPort(); print('resolved_provider=%s reason=%s' % (b.provider, b.routing_reason))"],
    capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "BRAIN_PROVIDER": "fugu",
                                         "HOME": "/home/ari"})
print("live resolve:", (probe.stdout or probe.stderr).strip()[:200])
