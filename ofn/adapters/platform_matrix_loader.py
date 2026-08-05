"""Load the platform matrix from data, into the kernel's shape.

The kernel's `PlatformMatrix` ships empty — it must not know brand names.
This module is the bridge: it reads `data/platform_matrix.json` (where
brand names and marker vocabularies are allowed) and builds a populated
`PlatformMatrix` for the rest of the system to use.

This is an adapter, not kernel: it does file I/O, it reads JSON, and it
is allowed to mention brand names because it is not subject to the kernel
purity test. The kernel decides the *shape* of a rule; this supplies the
*content*.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from ofn.kernel.platform_matrix import PlatformMatrix, PlatformRule


def _as_tuple(v: object) -> tuple[str, ...]:
    return tuple(str(x) for x in v) if v else ()


def load_matrix(path: str | Path) -> PlatformMatrix:
    """Build a PlatformMatrix from a data file.

    Raises if the file is missing or malformed — a missing policy file is
    not "permissive", it is a configuration error, and the safest answer
    to a configuration error is to refuse to start rather than to guess.
    """
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    platforms = raw.get("platforms")
    if not isinstance(platforms, dict) or not platforms:
        raise ValueError(f"{path}: no 'platforms' mapping — refusing to "
                         f"build an empty policy from a file that should "
                         f"define one")

    rules: dict[str, PlatformRule] = {}
    for key, spec in platforms.items():
        if not isinstance(spec, Mapping):
            raise ValueError(f"{path}: platform {key!r} is not a mapping")
        rules[key] = PlatformRule(
            name=spec.get("display_name", key),
            layer=spec.get("layer", "?"),
            risk=spec.get("risk", "RED"),
            adult_policy=spec.get("adult_policy", "sexual_content_prohibited"),
            direct_adult_link_allowed=spec.get(
                "direct_adult_link_allowed", False),
            caption_max=spec.get("caption_max"),
            allowed_framing=_as_tuple(spec.get("allowed_framing")),
            blocked_framing=_as_tuple(spec.get("blocked_framing")),
            adult_link_markers=_as_tuple(spec.get("adult_link_markers")),
            solicitation_markers=_as_tuple(spec.get("solicitation_markers")),
        )
    return PlatformMatrix(rules)


def default_matrix_path() -> Path:
    """The conventional location of the policy file, relative to the repo.

    Layout:  ~/ofn/ofn/adapters/platform_matrix_loader.py  (this file)
             ~/ofn/data/platform_matrix.json                (the data)
    So: up from adapters/, up from ofn/, into data/.
    """
    return Path(__file__).resolve().parent.parent.parent / "data" / "platform_matrix.json"
