#!/usr/bin/env python3
"""webapp_adapter — پلِ no-outbound برای ثبتِ تعاملات WebApp/local UI.

هیچ endpoint را live نمی‌کند. فقط یک helper برای ثبتِ request‌ها.
"""
from __future__ import annotations
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import intel_spine


def log_request(method: str, path: str, status_code: int = 200,
                actor: str = "", body_size: int = 0,
                is_mutating: bool = False) -> str | None:
    """یک WebApp request را ثبت کن (no body، no cookie، no auth)."""
    try:
        return intel_spine.log_interaction(
            source="webapp",
            direction="in",
            actor=actor or "anonymous",
            channel=path,
            text="",  # هیچ body ذخیره نمی‌شود
            kind=f"{method} {path}",
            status_code=status_code,
            body_size=body_size,
            is_mutating=is_mutating,
            d_level="D4" if is_mutating else "D0",
            safety_verdict="hold" if is_mutating else "allow",
        )
    except Exception:
        return None
