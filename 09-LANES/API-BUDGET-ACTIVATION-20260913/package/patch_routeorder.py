#!/usr/bin/env python3
"""patch2 — make paid_call default to the health-aware deterministic route."""
import hashlib
import pathlib
import py_compile
import shutil
import sys

T = pathlib.Path("/home/ari/ofn/state/api-budget/api_budget.py")
B = pathlib.Path("/home/ari/ofn/state/api-budget/api_budget.py.pre-routeorder-20260913")
src = T.read_text(encoding="utf-8")
print("pre_image_sha256:", hashlib.sha256(src.encode()).hexdigest()[:24])

OLD = '''    if provider is None:
        provider = next((p for p in providers.provider_ids()
                         if providers.REGISTRY[p]["paid"] and providers.enabled(p)
                         and providers.key_present(p)), "")
'''
NEW = '''    if provider is None:
        # Health-aware, deterministic route rank (local -> cheapest live paid ->
        # stronger). A non-LIVE provider is skipped by name, never silently
        # failed over to.
        _cands = providers.candidates()
        provider = _cands[0] if _cands else ""
'''
if OLD not in src:
    print("ANCHOR_MISSING: default provider selection")
    sys.exit(3)
if not B.exists():
    shutil.copy2(T, B)
    print("backup written:", B.name)
src = src.replace(OLD, NEW, 1)
T.write_text(src, encoding="utf-8")
try:
    py_compile.compile(str(T), doraise=True)
except py_compile.PyCompileError as exc:
    print("PY_COMPILE_FAILED:", exc)
    shutil.copy2(B, T)
    sys.exit(4)
print("post_image_sha256:", hashlib.sha256(T.read_bytes()).hexdigest()[:24])
print("PATCH2_OK")
