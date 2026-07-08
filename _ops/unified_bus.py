#!/usr/bin/env python3
"""unified_bus.py — Phase 5 · S-3: پلِ همگراییِ additive به یک ارگانیسمِ واحد.

UnifiedArchitecture L0: «one substrate, two views» — business events + causal ledger.
genome ledger (LANGAR) = substrate ابدی (append-only، hash-chain، age_tick).
chrono.db = runtime state (پایا در طولِ اجرا، reconstructable از ledger).
این دو رقیب نیستند — دو نما از یک سابستریت‌اند (همان تصمیمِ UnifiedArchitecture).

این پل:
  publish(event_type, payload, actor, is_human) → یک رویداد هم‌زمان به:
    ۱) genome ledger (LANGAR — ماندگار، age_tick در صورتِ is_human)
    ۲) chrono checkpoint (runtime — سریع، قابلِ replay)
  برعکسِ دو نویسندهٔ مستقل، این یک نویسندهٔ یکپارچه است = همگرایی بدونِ delete.

age_tick = فلشِ مشترک: همهٔ legs/doctor/telegram از همین publish می‌گذرند. راه‌های
قدیمی (ledger.append مستقیم در ماژول‌های قدیمی) deprecated نه deleted — additive.

NON-DESTRUCTIVE (طبقِ قانون): هیچ رقیبی حذف نمی‌شود. genome/agents/doctor.py قدیمی
باقی می‌ماند. این پل فقط یک مسیرِ توصیه‌شدهٔ جدید اضافه می‌کند. مهاجرتِ تدریجی،
نه big-bang.

additive؛ stdlib-only؛ $0 آفلاین. ledger/chrono قابل‌تزریق (تست).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent              # _ops
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402


class UnifiedBus:
    """پلِ همگرایی: publish → genome ledger (LANGAR) + chrono checkpoint.
    یک نویسنده، دو نما. additive — مسیرهای قدیمی دست‌نخورده.

   genome ledger = source of truth (ابدی). chrono = runtime cache (reconstructable).
    اگر ledger نباشد → fail-closed (هیچ publish). اگر chrono نباشد → ledger-only (fail-soft)."""

    def __init__(self, ledger=None, db=None, note_fn=None):
        self._ledger = ledger                          # genome Ledger instance
        self._db = db                                  # chrono ChronoDB instance
        # note_fn قابل‌تزریق (opslib.ledger_note) برای audit log جدا
        self._note = note_fn or _default_note

    def _lg(self):
        return self._ledger or opslib.genome_ledger()

    def publish(self, event_type: str, payload: dict, actor: str = "system",
                is_human: bool = False, beat: bool = False) -> dict:
        """یک رویداد را هم‌زمان به genome ledger + chrono checkpoint بفرست.
        is_human=True → age_tick +۱ (human-append، TINV-3).
        beat=True → heartbeat age_tick (heart-driven، v0.4.6).
        خروجی: entry از ledger (شامل hash، age_tick).
        fail-closed: اگر ledger بنویسد ولی chrono نه → باز هم entry برمی‌گردد (chrono = cache)."""
        if not isinstance(payload, dict):
            raise TypeError("payload must be dict")
        lg = self._lg()
        # ۱) genome ledger = source of truth (اولین، همیشه)
        entry = lg.append(event_type, payload, actor=actor,
                          is_human=is_human, beat=beat)
        # ۲) chrono checkpoint (runtime، fail-soft)
        if self._db is not None:
            try:
                self._checkpoint(entry)
            except Exception:  # noqa: BLE001 — chrono نباید publish را بکشد
                pass
        # ۳) audit log
        try:
            self._note("UNIFIED_PUBLISH", {"event_type": event_type, "actor": actor,
                                            "is_human": is_human,
                                            "hash": entry.get("hash", "") if isinstance(entry, dict) else ""})
        except Exception:  # noqa: BLE001
            pass
        return entry

    def _checkpoint(self, entry: dict) -> None:
        """checkpointِ سبک در chrono.db. entry باید dict با hash باشد."""
        if not isinstance(entry, dict):
            return
        # استفاده از جدولِ checkpoint موجود (chrono.py DDL) اگر db باشد
        # اینجا فقط یک note در جدولِ duration_marker می‌زنیم (additive، بدونِ schema change)
        import json
        h = entry.get("hash", "")
        etype = entry.get("type", event_type if 'event_type' in dir() else "UNKNOWN")
        try:
            import time as _t
            self._db.ex(
                "INSERT OR REPLACE INTO duration_marker(event_id, hlc_phys, hlc_logical, "
                "wall_ts, label) VALUES (?,?,?,?,?)",
                (f"unified-{h[:16]}", 0, 0, int(_t.time() * 1000),
                 json.dumps({"type": etype, "is_human": entry.get("is_human", 0)})))
        except Exception:  # noqa: BLE001 — chrono checkpoint fail-soft
            pass

    def replay(self, from_hash: str = "", to_hash: str = "",
               event_type: str | None = None) -> list[dict]:
        """بازپخشِ رویدادها از ledger (source of truth). chrono.db = cache فقط.
        اگر from/to باشند، بازه؛ اگر event_type باشد، فیلتر.
        این S-4 replay است — همیشه از ledger می‌آید، نه از chrono (reconstructable)."""
        lg = self._lg()
        out = []
        in_range = (not from_hash)
        for rec in lg.filter(event_type=event_type):
            h = rec.get("hash", "")
            if from_hash and h == from_hash:
                in_range = True
            if in_range:
                out.append(rec)
            if to_hash and h == to_hash:
                break
        return out


def _default_note(subtype: str, payload: dict, actor: str = "unified-bus") -> None:
    try:
        opslib.ledger_note(subtype, payload, actor=actor)
    except Exception:  # noqa: BLE001
        pass
