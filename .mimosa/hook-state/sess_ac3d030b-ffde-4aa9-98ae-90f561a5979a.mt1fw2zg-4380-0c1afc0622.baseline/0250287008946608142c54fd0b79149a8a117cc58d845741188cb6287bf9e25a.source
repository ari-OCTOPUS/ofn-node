# -*- coding: utf-8 -*-
"""Freedom KPIs — slogans become numbers. Observe-only in P0."""
from __future__ import annotations

from typing import Mapping


def freedom_metrics(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Compute measurable sovereignty. Missing fields → fail-closed zeros, not guesses."""
    local = int(snapshot.get("local_calls") or 0)
    cloud = int(snapshot.get("cloud_calls") or 0)
    total = local + cloud
    ratio = (local / total) if total else 0.0
    egress = int(snapshot.get("undocumented_external_egress") or 0)
    license_ok = str(snapshot.get("weight_license") or "") in ("Apache-2.0", "MIT")
    policy_author = str(snapshot.get("policy_author") or "")
    return {
        "local_execution_ratio": round(ratio, 4),
        "local_execution_ratio_pass": ratio >= 0.70 if total else False,
        "undocumented_external_egress": egress,
        "undocumented_external_egress_pass": egress == 0,
        "weight_license_ok": license_ok,
        "policy_author_is_owner": policy_author == "owner",
        "abliteration_of_brain": bool(snapshot.get("abliteration_of_brain")),
        "sovereign": (
            (ratio >= 0.70 if total else False)
            and egress == 0
            and license_ok
            and policy_author == "owner"
            and not bool(snapshot.get("abliteration_of_brain"))
        ),
    }
