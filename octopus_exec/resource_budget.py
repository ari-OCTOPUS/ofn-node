"""Resource ecology accounting only. No monetary conversion or external effects."""
import math
import os
from pathlib import Path
from .snapshot_reader import no_reparse
from shadow_homeostasis.canonical import finite_number


class ArtifactBudget:
    def __init__(self, root, cap_bytes=20 * 1024 * 1024):
        self.root = no_reparse(root).resolve()
        self.cap_bytes = cap_bytes

    def used(self):
        total = 0
        for directory, dirs, files in os.walk(self.root, followlinks=False):
            # Count link entries but never traverse them (pytest creates local current links).
            for name in list(dirs):
                path = Path(directory) / name
                stat = path.lstat()
                if path.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                    total += stat.st_size
                    dirs.remove(name)
            for name in files:
                total += (Path(directory) / name).lstat().st_size
        return total

    def require(self, additional):
        before = self.used()
        if additional < 0 or before + additional > self.cap_bytes:
            raise ValueError("artifact budget exhausted")
        return before


def assess_resources(observations, *, warning_pct=90.0):
    cpus = [o for o in observations if o["metric"] == "resource.cpu_pct" and o["quality"] == "VALID"]
    value = max((o["value"] for o in cpus), default=None)
    return {"state": "UNKNOWN" if value is None else "PRESSURE" if value >= warning_pct else "WITHIN_ENVELOPE",
            "measured_cpu_pct": value, "evidence_ids": sorted(o["observation_id"] for o in cpus),
            "warning_pct": warning_pct, "threshold_semantics": "local uncalibrated advisory; no gate change",
            "reason": "no eligible measurement" if value is None else "measured peak compared to advisory envelope",
            "executable": False}


def account_legs(legs):
    if not isinstance(legs, list) or len(legs) > 64:
        raise ValueError("leg budget")
    out, ids = [], set()
    for leg in legs:
        identity = (leg.get("leg_id"), leg.get("campaign_id"))
        if not all(isinstance(v, str) and v for v in identity) or identity in ids:
            raise ValueError("leg/campaign identity collision")
        ids.add(identity)
        amount, currency = leg.get("cost_amount"), leg.get("currency")
        evidence = leg.get("cost_evidence")
        if amount is not None and (not finite_number(amount) or amount < 0):
            raise ValueError("invalid cost")
        verified = (amount is not None and isinstance(currency, str) and bool(currency)
                    and isinstance(evidence, str) and bool(evidence))
        out.append({"leg_id": identity[0], "campaign_id": identity[1],
                    "inputs": leg.get("inputs", []), "outputs": leg.get("outputs", []),
                    "reported_cost_amount": amount, "cost_amount": amount if verified else None,
                    "currency": currency if verified else None, "cost_evidence": evidence,
                    "status": "ATTRIBUTED_NOT_AUTHENTICATED" if verified else "UNKNOWN",
                    "executable": False})
    return sorted(out, key=lambda l: (l["leg_id"], l["campaign_id"]))
