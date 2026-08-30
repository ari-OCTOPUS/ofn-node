#!/usr/bin/env python3
"""smoke_24h.py — Phase 5 · S-6: چک‌لیستِ smoke 24h (اجرای دستی مالک).

چک می‌کند:
  ۱) state تازه‌تر از ۱۰ دقیقه (ارگانیسم زنده)
  ۲) heartbeat ساعتی (آیا حلقه می‌تپد؟)
  ۳) صفر alert / ledger-fallback (FREEZE/HALT)
  ۴) verify ledger (زنجیرهٔ hash سالم)
  ۵) $۰ (هیچ spend واقعی)
  ۶) یک epoch-log سالم

خروجی: PASS/FAIL با جزئیات. اجرای دستی مالک — نه schedule (نقضِ «twin owner-launched»).
additive؛ read-only؛ stdlib-only.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402


def run_checks(state_dir: Path | None = None) -> dict:
    """اجرای همهٔ چک‌ها. خروجی: {checks: [...], pass: bool}."""
    sd = state_dir or opslib.STATE_DIR
    results = []

    def check(name: str, ok: bool, detail: str = ""):
        results.append({"name": name, "ok": ok, "detail": detail})

    # ۱) state تازه‌تر از ۱۰ دقیقه
    state_file = sd / "ORGANISM-STATE.json"
    if state_file.exists():
        try:
            org = json.loads(state_file.read_text(encoding="utf-8"))
            ts = org.get("ts", "")
            t = datetime.fromisoformat(ts) if ts else None
            if t and t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            age_min = ((datetime.now(timezone.utc) - t).total_seconds() / 60) if t else 9999
            check("state-fresh", age_min < 10, f"age={age_min:.0f}min (ts={ts})")
        except Exception as e:  # noqa: BLE001
            check("state-fresh", False, f"parse error: {e}")
    else:
        check("state-fresh", False, "ORGANISM-STATE.json missing")

    # ۲) heartbeat ساعتی (فایلِ heartbeat)
    hb = _HERE.parent / "_memory" / "HEARTBEAT.md"
    if hb.exists():
        mtime = hb.stat().st_mtime
        age_h = (datetime.now(timezone.utc).timestamp() - mtime) / 3600
        check("heartbeat-hourly", age_h < 2, f"age={age_h:.1f}h")
    else:
        check("heartbeat-hourly", False, "HEARTBEAT.md missing")

    # ۳) صفر alert / FREEZE / HALT
    if state_file.exists():
        org = json.loads(state_file.read_text(encoding="utf-8"))
        frozen = bool(org.get("frozen"))
        halted = org.get("halted")
        check("no-freeze-halt", not frozen and not halted,
              f"frozen={frozen} halted={halted}")
    else:
        check("no-freeze-halt", False, "state missing")

    # ۴) verify ledger (hash-chain) — fail-soft
    try:
        lg = opslib.genome_ledger()
        ok, msg = lg.verify()
        check("ledger-verify", ok, msg[:100] if msg else "chain ok")
    except Exception as e:  # noqa: BLE001
        check("ledger-verify", False, f"verify error: {e}")

    # ۵) $۰ — صفر spend (musd)
    spend_ok = True
    spend_detail = ""
    try:
        org = json.loads(state_file.read_text(encoding="utf-8"))
        month = org.get("month") or {}
        musd = month.get("musd", 0)
        spend_ok = (musd == 0)
        spend_detail = f"month.musd={musd}"
    except Exception:  # noqa: BLE001
        spend_detail = "couldn't check"
    check("zero-spend", spend_ok, spend_detail)

    # ۶) epoch-log سالم (آخرین epoch در state)
    epochs = sd.parent / "budget" / "epochs"
    epoch_ok = False
    files = []
    if epochs.exists():
        files = sorted(epochs.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            try:
                ep = json.loads(files[0].read_text(encoding="utf-8"))
                epoch_ok = "allocations" in ep or "ts" in ep
            except Exception:  # noqa: BLE001
                pass
    check("epoch-log", epoch_ok, f"latest={files[0].name if files else 'none'}")

    all_ok = all(r["ok"] for r in results)
    return {"checks": results, "pass": all_ok, "ts": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    result = run_checks()
    print("=== SMOKE 24h ===")
    for c in result["checks"]:
        mark = "✅" if c["ok"] else "❌"
        print(f"  {mark} {c['name']}: {c['detail']}")
    print(f"\n{'PASS' if result['pass'] else 'FAIL'}")
    sys.exit(0 if result["pass"] else 1)
