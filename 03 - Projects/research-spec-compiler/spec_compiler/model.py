"""
Canonical schema + IO for research specs.

The 11 canonical fields are exactly the compressed schema the project uses:

    idea, hypothesis, prediction, metric, experiment, failure_condition,
    architecture, api_contract, mvp, evaluation, decision_rule

A spec is just a dict with these keys. We keep it plain (no pydantic) so the
core runs anywhere with stdlib only.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

CANONICAL_FIELDS = [
    "idea",
    "hypothesis",
    "prediction",
    "metric",
    "experiment",
    "failure_condition",
    "architecture",
    "api_contract",
    "mvp",
    "evaluation",
    "decision_rule",
]


class SpecError(Exception):
    """Raised when a spec cannot be loaded or written."""


def _try_yaml():
    try:
        import yaml  # type: ignore
        return yaml
    except Exception:
        return None


def load_spec(path: str) -> Dict[str, Any]:
    """Load a spec from .yaml/.yml (needs PyYAML) or .json (stdlib)."""
    if not os.path.exists(path):
        raise SpecError(f"spec file not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if ext in (".yaml", ".yml"):
        yaml = _try_yaml()
        if yaml is None:
            raise SpecError(
                "PyYAML not installed. Either `pip install pyyaml` or use the "
                f".json mirror of {os.path.basename(path)}."
            )
        data = yaml.safe_load(text)
    elif ext == ".json":
        data = json.loads(text)
    else:
        raise SpecError(f"unsupported spec extension: {ext} (use .yaml or .json)")
    if not isinstance(data, dict):
        raise SpecError("top-level spec must be a mapping/object")
    return data


def dump_spec(spec: Dict[str, Any], path: str) -> None:
    """Write a spec to .yaml (if PyYAML present) or .json."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        yaml = _try_yaml()
        if yaml is None:
            raise SpecError("PyYAML not installed; write to a .json path instead.")
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(spec, fh, allow_unicode=True, sort_keys=False)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(spec, fh, ensure_ascii=False, indent=2)


def is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)
