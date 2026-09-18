#!/usr/bin/env python3
"""Wire provider_failover into the broker (owner directive 2026-09-17).

Minimal hook: when NO provider is given, ask the failover picker first; if the
module is unavailable the previous behaviour is preserved verbatim (fail-open).
Preimage + exact anchors + compile + marker checks. No credential is printed.
"""
import hashlib
import py_compile
import shutil
import sys
from pathlib import Path

B = Path("/home/ari/ofn/state/api-budget/api_budget.py")
PRE = Path("/home/ari/ofn/state/api-budget/api_budget.py.pre-provider-failover-20260917")

EDITS = [
    # 1) c_model default
    (
        '''    if provider:
        m = providers.model(provider)
        if m:
            return m
    return (contract() or {}).get("model_allowlist", ["fugu"])[0]''',
        '''    if provider:
        m = providers.model(provider)
        if m:
            return m
    # provider_failover (owner 2026-09-17): health-aware default instead of a
    # hard sakana fallback, so one provider's limit never idles cognition.
    try:
        import provider_failover as _pf
        _pid = _pf.pick("standard")
        if _pid:
            _m = providers.model(_pid)
            if _m:
                return _m
    except Exception:
        pass
    return (contract() or {}).get("model_allowlist", ["fugu"])[0]''',
    ),
    # 2) load_key default
    (
        '''    if provider:
        return providers._key(provider)
    for pid in providers.provider_ids():''',
        '''    if provider:
        return providers._key(provider)
    try:
        import provider_failover as _pf
        _pid = _pf.pick("standard")
        if _pid:
            return providers._key(_pid)
    except Exception:
        pass
    for pid in providers.provider_ids():''',
    ),
    # 3) second-model critique pick
    (
        '    pid = providers.select("review") if providers.select("review") in cands else cands[0]',
        '''    pid = ""
    try:
        import provider_failover as _pf
        _c = _pf.pick("review")
        pid = _c if _c in cands else ""
    except Exception:
        pid = ""
    if not pid:
        pid = providers.select("review") if providers.select("review") in cands else cands[0]''',
    ),
]


def main() -> int:
    src = B.read_text(encoding="utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = src.count(old)
        if n != 1:
            print(f"ABORT: anchor E{i} count={n}")
            return 2
        src = src.replace(old, new)
    if not PRE.exists():
        shutil.copyfile(B, PRE)
        print("preimage_written")
    B.write_text(src, encoding="utf-8", newline="\n")
    py_compile.compile(str(B), doraise=True)
    checks = {
        "c_model_hook": src.count("_pf.pick(\"standard\")") == 2,
        "review_hook": "failover" in src and '_pf.pick("review")' in src,
        "fail_open": src.count("except Exception:") >= 3,
    }
    print("checks:", checks)
    if not all(checks.values()):
        B.write_bytes(PRE.read_bytes())
        print("REVERTED")
        return 3
    print("PATCH_OK sha=" + hashlib.sha256(B.read_bytes()).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
