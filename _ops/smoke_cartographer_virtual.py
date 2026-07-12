#!/usr/bin/env python3
"""smoke_cartographer_virtual.py — فعال‌سازیِ «کاملاً مجازی» پای نقشه‌بردار.

مجازی یعنی: فلگ فقط در همین پروسه ست می‌شود (ephemeral)؛ هیچ تغییرِ live —
نه ویرایشِ PAPER_FULL_FLAGS، نه organismِ زنده، نه نوشتن در state/ORGANISM-STATE.json
یا state/events.jsonlِ واقعی. مسیرِ ledger با emitterِ ضبط‌کننده (in-memory) نشان داده می‌شود.

هدف: اثباتِ اینکه لیمب «فعال» درست رفتار می‌کند، بدونِ عبور از گیتِ deploy.
اجرا: python _ops/smoke_cartographer_virtual.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# چاپِ امنِ یونیکد روی ویندوز
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

_HERE = Path(__file__).resolve().parent          # _ops
for _p in (str(_HERE), str(_HERE / "legs"), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── فلگ فقط در همین پروسه (مجازی) ────────────────────────────────────────────
os.environ["OCTOPUS_WIRE_CARTOGRAPHER"] = "1"

import wiring                                     # noqa: E402
from cartographer_leg import CartographerLeg, default_packet  # noqa: E402


def _real_state_untouched() -> dict:
    """چک می‌کند که هیچ اثرِ live نگذاشتیم."""
    out = {"organism_state_has_cartographer": None, "events_vault_cartographer": None}
    try:
        import opslib
        sp = opslib.STATE_DIR / "ORGANISM-STATE.json"
        if sp.exists():
            d = json.loads(sp.read_text("utf-8"))
            out["organism_state_has_cartographer"] = "cartographer" in d
        ep = opslib.STATE_DIR / "events.jsonl"
        if ep.exists():
            out["events_vault_cartographer"] = sum(
                1 for ln in ep.read_text("utf-8").splitlines() if "vault-cartographer" in ln)
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)[:80]
    return out


def main() -> int:
    print("=== VIRTUAL ACTIVATION (flag set in THIS process only) ===")
    print("OCTOPUS_WIRE_CARTOGRAPHER =", os.environ.get("OCTOPUS_WIRE_CARTOGRAPHER"))
    print("in PAPER_FULL_FLAGS (live default)?:",
          "OCTOPUS_WIRE_CARTOGRAPHER" in wiring.PAPER_FULL_FLAGS, "(must be False)")
    print()

    # 1) مسیرِ organism، ولی standalone: build → beat → همان dictی که به ORGANISM-STATE می‌رفت
    leg = wiring.make_cartographer_leg()
    print("1) make_cartographer_leg():", "BUILT" if leg else None,
          "| money_link =", (leg.money_link if leg else "-"))
    beat = wiring.cartographer_beat(leg, beat=7)
    print("   cartographer_beat → ORGANISM-STATE['cartographer'] WOULD be:")
    print("  ", json.dumps(beat, ensure_ascii=False))
    print()

    # 2) مسیرِ ledger، کاملاً in-memory (emitterِ ضبط‌کننده — هیچ نوشتنِ واقعی)
    captured: list = []
    vleg = CartographerLeg(default_packet(), organ_table={},
                           emitter=lambda ev, ag, **kw: captured.append((ev, ag, kw)))
    prop = vleg.propose_refresh("virtual drill — map staleness sentinel",
                                map_updated_iso="2026-05-01")
    print("2) propose_refresh → Proposal:", prop.kind,
          "| publish =", prop.payload["publish"], "| no_mutation =", prop.payload["no_mutation"])
    if captured:
        ev, ag, kw = captured[0]
        blob = (kw.get("summary", "") + " " + kw.get("next_action", "")).lower()
        banned = [b for b in ("اونلی", "onlyfans", "صبا", "sk-", "api_key") if b in blob]
        print("   captured ledger event (IN-MEMORY, not written):", ev, "| agent =", ag,
              "| approval =", kw.get("approval_state"), "| content-free =", not banned)
    print()

    # 3) اثباتِ صفر اثرِ live
    chk = _real_state_untouched()
    print("3) LIVE side-effects check (must show none):")
    print("   ORGANISM-STATE.json has 'cartographer' key?:", chk["organism_state_has_cartographer"])
    print("   events.jsonl 'vault-cartographer' entries:", chk["events_vault_cartographer"])
    ok = (chk.get("organism_state_has_cartographer") in (False, None)
          and (chk.get("events_vault_cartographer") in (0, None)))
    print()
    print("RESULT:", "OK — fully virtual, zero live change." if ok
          else "⚠ unexpected live artifact — investigate.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
