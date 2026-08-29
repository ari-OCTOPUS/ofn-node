from __future__ import annotations

from pathlib import Path

SCHEMA_ROOT = Path(__file__).resolve().parent


def schema_path(*parts: str) -> Path:
    return SCHEMA_ROOT.joinpath(*parts)
