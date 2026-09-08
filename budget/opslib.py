"""Import-boundary shim. Tools look here (`<repo>/budget`).

Live body is `ofn/budget/opslib.py` (pinned by tests/test_r0_spine_restore.py).
This file does not invent a second halt/alert implementation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_LIVE = Path(__file__).resolve().parent.parent / "ofn" / "budget" / "opslib.py"
_spec = importlib.util.spec_from_file_location("_ofn_live_opslib", _LIVE)
if _spec is None or _spec.loader is None:
    raise ImportError(f"live opslib missing: {_LIVE}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("_ofn_live_opslib", _mod)
_spec.loader.exec_module(_mod)

HOME = _mod.HOME
OFN_ROOT = _mod.OFN_ROOT
STATE_DIR = _mod.STATE_DIR
HALT_FLAG = _mod.HALT_FLAG
ALERTS_JSONL = _mod.ALERTS_JSONL
now_iso = _mod.now_iso
master_halted = _mod.master_halted
append_jsonl = _mod.append_jsonl
alert = _mod.alert

# #region agent log
try:
    import json as _json, time as _time
    open(r"F:\backup\debug-11f994.log", "a", encoding="utf-8").write(
        _json.dumps({"sessionId": "11f994", "runId": "post-fix",
                     "hypothesisId": "B", "location": "budget/opslib.py",
                     "message": "shim_loaded",
                     "data": {"live": str(_LIVE), "exists": _LIVE.is_file(),
                              "state_dir": str(STATE_DIR)},
                     "timestamp": int(_time.time() * 1000)}) + "\n")
except Exception:
    pass
# #endregion
