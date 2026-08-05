"""Platform adapters package.

Each module here is one outside service. The package is imported lazily by
the node; nothing here runs at import time, and nothing here publishes for
real until the OwnerRelease switch is wired (M5) and the relevant WIRE
flag is on — which the project's hard rules keep off by default.

`available_platforms()` is what lets the UI tell the truth about the
difference between *policy* and *wiring*: the platform matrix may know about
eleven platforms as policy, but only the adapters that exist as code here
are ones the node could ever publish to, and only the ones actually built
into the node are armed. A partner reading "11 platforms" without that
split would reasonably believe eleven live outputs exist when none do.
"""

from __future__ import annotations

import importlib
import pkgutil


def available_platforms() -> tuple[str, ...]:
    """The platforms this node has adapter *code* for, sorted.

    Discovery is by module presence, not by instantiation: an adapter that
    ships as dry-run still counts as available, because the code path exists
    and could be armed. This is the set between "policy knows about it" and
    "it is actually wired to send" — the middle number a partner needs to not
    be misled.

    Returns the empty tuple if no adapters are present, which is also the
    honest answer. Never raises: a broken adapter module does not inflate the
    count, it is simply skipped (availability is a structural fact, not a
    health check).
    """
    names: list[str] = []
    for mod_info in pkgutil.iter_modules(__path__):
        name = mod_info.name
        if name in ("base", "__init__"):
            continue
        try:
            mod = importlib.import_module(f"{__name__}.{name}")
        except Exception:
            continue
        platform = getattr(mod, "__all_platform__", None)
        if platform is None:
            # Walk the module's attributes for a class declaring `platform`.
            for attr in vars(mod).values():
                plat = getattr(attr, "platform", None)
                if isinstance(plat, str) and plat:
                    platform = plat
                    break
        if isinstance(platform, str) and platform:
            names.append(platform)
    return tuple(sorted(set(names)))

