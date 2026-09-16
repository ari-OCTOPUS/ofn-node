#!/usr/bin/env python3
"""Collaborator daily model-cap contract: default 20, explicit override bounded >=1."""
from __future__ import annotations
import os
import sys
from pathlib import Path

OPS = Path(__file__).resolve().parents[2]
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))
from owner_console import collab_model_adapter as adapter  # noqa: E402


def _with(value):
    old = os.environ.get(adapter.COLLAB_DAILY_CAP_ENV)
    if value is None:
        os.environ.pop(adapter.COLLAB_DAILY_CAP_ENV, None)
    else:
        os.environ[adapter.COLLAB_DAILY_CAP_ENV] = value
    try:
        return adapter.daily_cap()
    finally:
        if old is None:
            os.environ.pop(adapter.COLLAB_DAILY_CAP_ENV, None)
        else:
            os.environ[adapter.COLLAB_DAILY_CAP_ENV] = old


def t_default_is_owner_cap_20():
    assert adapter.COLLAB_DAILY_CAP_DEFAULT == 20
    assert _with(None) == 20


def t_invalid_override_falls_back_to_20():
    assert _with("not-a-number") == 20


def t_explicit_override_is_honored_but_never_below_one():
    assert _with("7") == 7
    assert _with("0") == 1


if __name__ == "__main__":
    ts = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    [t() for t in ts]
    print(f"OK test_collab_model_cap: {len(ts)}/{len(ts)}")
